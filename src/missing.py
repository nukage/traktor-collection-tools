"""Missing file scanner for Traktor collection."""

import os
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from parser import Track
from config import Config, SearchRoot
from everything import EverythingClient, get_client, is_everything_available


MISSING_CATEGORIES = ["all", "missing", "found_single", "found_multiple", "network_offline"]

SEARCH_TIMEOUT_PER_FILE = 30  # seconds per file search
EXISTS_TIMEOUT = 5  # seconds for existence check


@dataclass
class MissingFileInfo:
    track: Track
    original_path: str
    status: str = "missing"
    found_paths: list[str] = field(default_factory=list)
    found_sizes: list[int] = field(default_factory=list)
    best_size_match_index: int = -1

    @property
    def full_path(self) -> str:
        parts = [p for p in [self.track.volume, self.track.file_path] if p]
        result = "/".join(parts).replace("//", "/")
        if result.startswith("/"):
            result = result[1:]
        return result


def _build_full_path(track: Track) -> str:
    """Build full path from track volume and file_path."""
    volume = track.volume
    file_path = track.file_path

    if not volume or not file_path:
        return ""

    if volume.endswith(":") or volume.endswith(":"):
        sep = "\\"
    else:
        sep = "/"

    if volume.startswith("\\\\"):
        full = volume + file_path
    elif volume.endswith(":"):
        full = volume + sep + file_path
    else:
        full = volume + sep + file_path

    return full


def _path_exists_with_timeout(path_str: str, timeout: int = EXISTS_TIMEOUT) -> bool:
    """Check if a path exists with a timeout."""
    def _check():
        return os.path.exists(path_str)

    try:
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(_check)
            return future.result(timeout=timeout)
    except (FuturesTimeoutError, Exception):
        return False


def _get_file_size(path_str: str) -> Optional[int]:
    """Get file size with timeout."""
    try:
        return os.path.getsize(path_str)
    except (OSError, FileNotFoundError):
        return None


def _is_network_path(path_str: str) -> bool:
    """Check if a path is a network path (UNC or mapped network drive)."""
    if path_str.startswith("\\\\"):
        return True
    if len(path_str) >= 3 and path_str[1] == ':' and path_str[2] == '\\':
        drive_letter = path_str[0].upper()
        if drive_letter in ('Y', 'Z'):
            return True
    return False


def _should_scan_path(path_str: str, config: Config) -> bool:
    """Determine if a path should be scanned based on config settings."""
    if not _is_network_path(path_str):
        return True
    if not config.network_enabled:
        return False
    for folder in config.network_scan_folders:
        if path_str.startswith(folder):
            return True
    return False


def _is_drive_accessible(path_str: str) -> bool:
    r"""Check if a drive letter path (e.g. Z:\) is currently accessible."""
    if len(path_str) >= 3 and path_str[1] == ':' and path_str[2] == '\\':
        drive = path_str[0].upper() + ":\\"
        try:
            return os.path.exists(drive)
        except (OSError, ValueError):
            return False
    return True


def _search_for_file(filename: str, search_root: SearchRoot, config: Config = None, timeout: int = SEARCH_TIMEOUT_PER_FILE) -> list[tuple[str, int]]:
    """Search for a file by exact filename match within a search root. Returns list of (path, size)."""
    root_path = Path(search_root.path)
    max_depth = search_root.max_depth
    filename_lower = filename.lower()
    found = []

    if not root_path.exists():
        return []

    if config and not _should_scan_path(search_root.path, config):
        return []

    def _search():
        try:
            for dirpath, dirnames, filenames in os.walk(root_path):
                try:
                    rel_path = Path(dirpath).relative_to(root_path)
                    depth = len(rel_path.parts)
                    if depth > max_depth:
                        dirnames.clear()
                        continue
                except ValueError:
                    dirnames.clear()
                    continue

                for fname in filenames:
                    if fname.lower() == filename_lower:
                        full_path = os.path.join(dirpath, fname)
                        try:
                            size = os.path.getsize(full_path)
                            found.append((full_path, size))
                        except OSError:
                            found.append((full_path, 0))
        except (OSError, PermissionError):
            pass
        except Exception:
            pass

    try:
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(_search)
            future.result(timeout=timeout)
    except FuturesTimeoutError:
        pass
    except Exception:
        pass

    return found


def _matches_by_size(original_size: Optional[int], found_size: Optional[int], tolerance: float = 0.02) -> bool:
    """Check if sizes match within tolerance (default ±2%)."""
    if original_size is None or found_size is None:
        return False
    if original_size == 0:
        return False
    ratio = abs(found_size - original_size) / original_size
    return ratio <= tolerance


def _best_size_match(original_size: Optional[int], found_sizes: list[int]) -> tuple[bool, int]:
    """Find if any size matches within tolerance. Returns (has_match, best_index)."""
    if original_size is None or not found_sizes:
        return False, -1
    for i, size in enumerate(found_sizes):
        if _matches_by_size(original_size, size):
            return True, i
    return False, -1


def _strip_track_number(title: str) -> str:
    """Strip common track number patterns from title."""
    import re
    patterns = [
        r'^\d{1,2}\s*[-_.:]\s*',
        r'^\d{2}:\d{2}\s*-\s*',
        r'^track\s*\d+\s*[-_.:]\s*',
        r'^\d+\s+',
    ]
    result = title
    for pattern in patterns:
        result = re.sub(pattern, '', result, flags=re.IGNORECASE)
    return result.strip()


def fuzzy_match_filename(track: Track, search_roots: list[SearchRoot], timeout: int = 10) -> list[tuple[str, int]]:
    """Try fuzzy matching when exact filename fails. Returns list of (path, size)."""
    import re
    filename = Path(track.file_path).name
    name_without_ext = Path(track.file_path).stem
    extension = Path(track.file_path).suffix

    stripped_title = _strip_track_number(name_without_ext)
    if stripped_title == name_without_ext:
        return []

    stripped_filename = stripped_title + extension

    found = []
    for sr in search_roots:
        root_path = Path(sr.path)
        if not root_path.exists() or _is_network_path(sr.path):
            continue

        def _search():
            try:
                for dirpath, dirnames, filenames in os.walk(root_path):
                    try:
                        rel_path = Path(dirpath).relative_to(root_path)
                        depth = len(rel_path.parts)
                        if depth > sr.max_depth:
                            dirnames.clear()
                            continue
                    except ValueError:
                        dirnames.clear()
                        continue

                    for fname in filenames:
                        fname_lower = fname.lower()
                        if fname_lower == stripped_filename.lower() or fname_lower == (stripped_title + ".*").lower():
                            full_path = os.path.join(dirpath, fname)
                            try:
                                size = os.path.getsize(full_path)
                                found.append((full_path, size))
                            except OSError:
                                found.append((full_path, 0))
            except (OSError, PermissionError):
                pass
            except Exception:
                pass

        try:
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(_search)
                future.result(timeout=timeout)
        except FuturesTimeoutError:
            pass
        except Exception:
            pass

    return found


def find_missing_files(tracks: list[Track], config: Config) -> list[MissingFileInfo]:
    """Find missing files from track list and search for them."""
    results = []
    use_ev = config.use_everything and is_everything_available()
    ev_client = get_client() if use_ev else None

    for track in tracks:
        full_path = _build_full_path(track)
        if not full_path:
            continue

        original_size = _get_file_size(full_path)

        if full_path.startswith("\\\\") and not _is_drive_accessible(full_path):
            status = "network_offline"
            found_paths = []
            found_sizes = []
        elif _path_exists_with_timeout(full_path):
            status = "found_single"
            found_paths = [full_path]
            found_sizes = [original_size] if original_size else []
        else:
            found_paths = []
            found_sizes = []

            if use_ev and ev_client:
                try:
                    ev_results = ev_client.search_files_by_name(Path(track.file_path).name, max_results=20)
                    for r in ev_results:
                        if r.name.lower() == Path(track.file_path).name.lower():
                            if r.size is not None:
                                found_paths.append(r.path)
                                found_sizes.append(r.size)
                except Exception:
                    pass

            if not found_paths and not _is_network_path(full_path):
                for sr in config.search_roots:
                    matches = _search_for_file(Path(track.file_path).name, sr, config)
                    for path, size in matches:
                        found_paths.append(path)
                        found_sizes.append(size)

            if not found_paths and not _is_network_path(full_path):
                fuzzy_results = fuzzy_match_filename(track, config.search_roots)
                for path, size in fuzzy_results:
                    found_paths.append(path)
                    found_sizes.append(size)

            has_match, best_idx = _best_size_match(original_size, found_sizes)
            if has_match:
                best_size_match_index = best_idx
            elif len(found_paths) > 1:
                best_size_match_index = -1

            if len(found_paths) == 1:
                status = "found_single"
            elif len(found_paths) > 1:
                status = "found_multiple"
            elif _is_network_path(full_path) and not _is_drive_accessible(full_path):
                status = "network_offline"
            else:
                status = "missing"

        info = MissingFileInfo(
            track=track,
            original_path=full_path,
            status=status,
            found_paths=found_paths,
            found_sizes=found_sizes,
            best_size_match_index=best_size_match_index
        )
        results.append(info)

    return results


def categorize_missing(info: MissingFileInfo, config: Config) -> MissingFileInfo:
    """Update status of MissingFileInfo based on found paths."""
    if info.original_path.startswith("\\\\") and not _is_drive_accessible(info.original_path):
        info.status = "network_offline"
    elif len(info.found_paths) == 1:
        info.status = "found_single"
    elif len(info.found_paths) > 1:
        info.status = "found_multiple"
    else:
        info.status = "missing"

    return info


def filter_missing_by_category(
    missing_info: list[MissingFileInfo],
    category: str = "all"
) -> list[MissingFileInfo]:
    """Filter missing file info by category."""
    if category == "all":
        return missing_info

    return [m for m in missing_info if m.status == category]


def filter_by_size_match(missing_info: list[MissingFileInfo]) -> list[MissingFileInfo]:
    """Filter to items where found file size matches original size."""
    result = []
    for m in missing_info:
        if m.status == "missing" and len(m.found_paths) > 0:
            original_size = _get_file_size(m.original_path)
            for fs in m.found_sizes:
                if _matches_by_size(original_size, fs):
                    result.append(m)
                    break
        else:
            result.append(m)
    return result


def format_missing_info(info: MissingFileInfo, index: int = 0) -> str:
    """Format MissingFileInfo for display."""
    artist = info.track.artist[:20].ljust(20)
    title = info.track.title[:35].ljust(35)
    status = info.status

    if status == "missing":
        return f"{index:4d}  [MISSING]    {artist} | {title}"
    elif status == "found_single":
        found = info.found_paths[0][:50] if info.found_paths else ""
        return f"{index:4d}  [FOUND]      {artist} | {title} -> {found}"
    elif status == "found_multiple":
        return f"{index:4d}  [MULTIPLE]   {artist} | {title} -> {len(info.found_paths)} matches"
    elif status == "network_offline":
        return f"{index:4d}  [NETWORK]    {artist} | {title} -> {info.original_path[:50]}"
    else:
        return f"{index:4d}  [{status:12}] {artist} | {title}"
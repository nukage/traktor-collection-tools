"""Missing file scanner for Traktor collection."""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from parser import Track
from config import Config, SearchRoot


MISSING_CATEGORIES = ["all", "missing", "found_single", "found_multiple", "network_offline"]


@dataclass
class MissingFileInfo:
    track: Track
    original_path: str
    status: str = "missing"
    found_paths: list[str] = field(default_factory=list)

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


def _search_for_file(filename: str, search_root: SearchRoot) -> list[str]:
    """Search for a file by exact filename match within a search root."""
    root_path = Path(search_root.path)
    max_depth = search_root.max_depth

    if not root_path.exists():
        return []

    filename_lower = filename.lower()
    found = []

    for path in root_path.rglob(filename_lower):
        if path.is_file():
            try:
                rel_depth = len(path.relative_to(root_path).parts)
                if rel_depth <= max_depth:
                    found.append(str(path))
            except ValueError:
                continue

    return found


def find_missing_files(tracks: list[Track], config: Config) -> list[MissingFileInfo]:
    """Find missing files from track list and search for them."""
    results = []

    for track in tracks:
        full_path = _build_full_path(track)
        if not full_path:
            continue

        if full_path.startswith("\\\\"):
            status = "network_offline"
            found_paths = []
        elif os.path.exists(full_path):
            status = "found_single"
            found_paths = [full_path]
        else:
            found_paths = []
            for sr in config.search_roots:
                matches = _search_for_file(Path(track.file_path).name, sr)
                found_paths.extend(matches)

            if len(found_paths) == 1:
                status = "found_single"
            elif len(found_paths) > 1:
                status = "found_multiple"
            else:
                status = "missing"

        info = MissingFileInfo(
            track=track,
            original_path=full_path,
            status=status,
            found_paths=found_paths
        )
        results.append(info)

    return results


def categorize_missing(info: MissingFileInfo, config: Config) -> MissingFileInfo:
    """Update status of MissingFileInfo based on found paths."""
    if info.original_path.startswith("\\\\"):
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

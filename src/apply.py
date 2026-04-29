"""Apply selection changes from preview HTML export to NML file."""

import json
import re
import shutil
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from parser import Track


@dataclass
class SelectionData:
    created: str
    missing: list
    duplicates: list
    excluded: list


def load_selection(path: str) -> SelectionData:
    """Load selection data from a JSON file."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return SelectionData(
        created=data.get("created", ""),
        missing=data.get("missing", []),
        duplicates=data.get("duplicates", []),
        excluded=data.get("excluded", []),
    )


def split_path_for_nml(full_path: str) -> tuple[str, str]:
    """Split a filesystem path into NML VOLUME and FILE components.

    Examples:
        E:\\Music\\Artist\\Track.mp3 -> ("E:", "Music\\Artist\\Track.mp3")
        \\\\NAS\\Music\\Track.mp3    -> ("\\\\NAS\\Music", "Track.mp3")
    """
    if not full_path:
        return "", ""

    full_path = full_path.replace("/", "\\")

    if full_path.startswith("\\\\"):
        parts = full_path.split("\\")
        if len(parts) >= 4:
            volume = "\\\\" + parts[2] + "\\" + parts[3]
            file_path = "\\".join(parts[4:]) if len(parts) > 4 else ""
            return volume, file_path
        return full_path, ""

    match = re.match(r"^([A-Z]:)[\\/](.*)$", full_path, re.IGNORECASE)
    if match:
        return match.group(1), match.group(2)

    return "", full_path


def apply_selection(
    nml_path: str,
    selection: SelectionData,
    track_lookup: dict = None,
    backup: bool = True,
    dry_run: bool = False
) -> dict:
    """Apply selection to NML file.

    Args:
        nml_path: Path to NML file
        selection: Selection data from preview export
        track_lookup: Optional dict mapping audio_id to track info for dedupe
        backup: Whether to create backup
        dry_run: Whether to just preview

    Returns dict with stats:
        - rebased: count of tracks with rebased paths
        - removed: count of tracks removed
        - merged: count of duplicate groups merged
    """
    import xml.etree.ElementTree as ET
    from duplicates import find_duplicates, merge_tracks
    from parser import parse_nml

    if backup and not dry_run:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"{nml_path}.backup_{timestamp}"
        shutil.copy2(nml_path, backup_path)

    tree = ET.parse(nml_path)
    root = tree.getroot()

    collection = root.find("COLLECTION")
    if collection is None:
        return {"error": "No COLLECTION found in NML"}

    stats = {"rebased": 0, "removed": 0, "merged": 0}

    audio_id_to_entry = {}
    audio_id_to_track = {}
    for entry in collection.findall("ENTRY"):
        audio_id = entry.get("AUDIO_ID", "")
        if audio_id:
            audio_id_to_entry[audio_id] = entry
            # Build minimal track object for duplicate detection
            audio_id_to_track[audio_id] = Track(
                title=entry.get("TITLE", ""),
                artist=entry.get("ARTIST", ""),
                audio_id=audio_id,
                file_path=entry.find("LOCATION").get("FILE") if entry.find("LOCATION") is not None else "",
                volume=entry.find("LOCATION").get("VOLUME") if entry.find("LOCATION") is not None else "",
                volume_id=entry.find("LOCATION").get("VOLUMEID") if entry.find("LOCATION") is not None else "",
            )

    # Handle missing files
    for m in selection.missing:
        audio_id = m.get("audio_id", "")
        action = m.get("action", "")

        if action == "rebase":
            new_path = m.get("new_path", "")
            if audio_id in audio_id_to_entry and new_path:
                entry = audio_id_to_entry[audio_id]
                volume, file_path = split_path_for_nml(new_path)
                location = entry.find("LOCATION")
                if location is not None:
                    if not dry_run:
                        file_parts = file_path.replace("/", "\\").split("\\")
                        nml_dir = "/:" + "/:".join(file_parts[:-1]) + "/:" if len(file_parts) > 1 else "/:"
                        location.set("FILE", file_parts[-1])
                        location.set("VOLUME", volume)
                        location.set("DIR", nml_dir)
                        location.set("VOLUMEID", "")
                    stats["rebased"] += 1

        elif action == "delete":
            if audio_id in audio_id_to_entry:
                if not dry_run:
                    collection.remove(audio_id_to_entry[audio_id])
                stats["removed"] += 1

    # Handle excluded
    for excl in selection.excluded:
        excl_id = excl if isinstance(excl, str) else excl.get("audio_id", "")
        if excl_id and excl_id in audio_id_to_entry:
            if not dry_run:
                collection.remove(audio_id_to_entry[excl_id])
            stats["removed"] += 1

    # Handle duplicates
    # Re-derive duplicate groups from current collection
    all_tracks = list(audio_id_to_track.values())
    duplicate_groups = find_duplicates(all_tracks)

    # Build audio_id -> group_id mapping for current collection
    audio_id_to_group_id = {}
    for gid, group in enumerate(duplicate_groups):
        for t in group.tracks:
            audio_id_to_group_id[t.audio_id] = gid

    for d in selection.duplicates:
        group_id = d.get("group_id", -1)
        action = d.get("action", "")
        winner_id = d.get("winner_id")

        if group_id < 0 or group_id >= len(duplicate_groups):
            continue

        group = duplicate_groups[group_id]

        if action == "ignore":
            continue

        elif action == "keep_both":
            continue

        elif action == "merge":
            # Find the group containing winner_id - this is more robust than using group_id
            # because rebuilt groups may have different indices with minimal Track objects
            target_group = None
            if winner_id and winner_id in audio_id_to_entry:
                actual_winner = winner_id
                for g in duplicate_groups:
                    if any(t.audio_id == winner_id for t in g.tracks):
                        target_group = g
                        break
            elif group.winner and group.winner.audio_id in audio_id_to_entry:
                actual_winner = group.winner.audio_id
                target_group = group
            elif group.tracks and group.tracks[0].audio_id in audio_id_to_entry:
                actual_winner = group.tracks[0].audio_id
                target_group = group
            else:
                continue

            if target_group is None:
                continue

            # Remove all non-winners from target group
            for track in target_group.tracks:
                if track.audio_id != actual_winner and track.audio_id in audio_id_to_entry:
                    if not dry_run:
                        collection.remove(audio_id_to_entry[track.audio_id])
                    stats["removed"] += 1

            # If winner changed, update metadata from new winner source
            if winner_id and winner_id != group.winner.audio_id:
                new_winner_track = None
                for t in group.tracks:
                    if t.audio_id == winner_id:
                        new_winner_track = t
                        break

                if new_winner_track and new_winner_track in audio_id_to_track:
                    # Update winner metadata in NML entry
                    winner_entry = audio_id_to_entry[winner_id]
                    # Merge metadata from all variants
                    merged, _ = merge_tracks(new_winner_track, [t for t in group.tracks if t.audio_id != winner_id], group.same_file)
                    # Apply merged metadata
                    if not dry_run:
                        winner_entry.set("TITLE", merged.title)
                        winner_entry.set("ARTIST", merged.artist)

                        tempo = winner_entry.find("TEMPO")
                        if tempo is not None:
                            tempo.set("BPM", str(merged.bpm))
                            tempo.set("BPM_QUALITY", str(merged.bpm_quality))

                        info = winner_entry.find("INFO")
                        if info is not None:
                            info.set("KEY", str(merged.musical_key))
                            info.set("PLAYCOUNT", str(merged.playcount))

            stats["merged"] += 1

    # Update entries count
    if not dry_run:
        entries_count = len([e for e in collection.findall("ENTRY")])
        collection.set("ENTRIES", str(entries_count))

        xml_declaration = '<?xml version="1.0" encoding="UTF-8" standalone="no" ?>\n'
        nml_str = ET.tostring(root, encoding="unicode")

        with open(nml_path, "w", encoding="utf-8") as f:
            f.write(xml_declaration + nml_str)

    return stats


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python apply.py <selection.json> [nml_path]")
        print("  selection.json: Selection file from preview export")
        print("  nml_path: Optional NML path (uses config if not provided)")
        sys.exit(1)

    selection_file = sys.argv[1]
    nml_path = sys.argv[2] if len(sys.argv) > 2 else None

    if not nml_path:
        from config import load_config
        config = load_config()
        nml_path = config.traktor_nml

    print(f"Loading selection from {selection_file}")
    selection = load_selection(selection_file)
    print(f"  Missing: {len(selection.missing)}")
    print(f"  Duplicates: {len(selection.duplicates)}")
    print(f"  Excluded: {len(selection.excluded)}")

    print(f"\nApplying to {nml_path}")
    result = apply_selection(nml_path, selection, backup=True, dry_run=True)

    print(f"\nDry run results:")
    print(f"  Would rebase: {result.get('rebased', 0)} tracks")
    print(f"  Would remove: {result.get('removed', 0)} tracks")
    print(f"  Would merge: {result.get('merged', 0)} duplicate groups")

    if input("\nApply for real? (y/N): ").lower() == 'y':
        result = apply_selection(nml_path, selection, backup=True, dry_run=False)
        print(f"\nApplied:")
        print(f"  Rebased: {result.get('rebased', 0)} tracks")
        print(f"  Removed: {result.get('removed', 0)} tracks")
        print(f"  Merged: {result.get('merged', 0)} duplicate groups")

"""Apply selection changes from preview HTML export to NML file."""

import json
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
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


def apply_selection(nml_path: str, selection: SelectionData, backup: bool = True, dry_run: bool = False) -> dict:
    """Apply selection to NML file. Returns dict with stats."""
    import xml.etree.ElementTree as ET

    if backup and not dry_run:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"{nml_path}.backup_{timestamp}"
        shutil.copy2(nml_path, backup_path)

    tree = ET.parse(nml_path)
    root = tree.getroot()

    collection = root.find("COLLECTION")
    if collection is None:
        return {"error": "No COLLECTION found in NML"}

    stats = {"removed": 0, "rebased": 0, "merged": 0}

    audio_id_to_entry = {entry.get("AUDIO_ID", ""): entry for entry in collection.findall("ENTRY")}
    audio_id_to_track = {t.audio_id: t for t in [parse_track_from_entry(e) for e in collection.findall("ENTRY")]}
    audio_id_to_track = {k: v for k, v in audio_id_to_track.items() if v is not None}

    missing_audio_ids = set()
    for m in selection.missing:
        audio_id = m.get("audio_id", "")
        action = m.get("action", "")

        if action == "rebase":
            new_path = m.get("new_path", "")
            if audio_id in audio_id_to_entry and new_path:
                entry = audio_id_to_entry[audio_id]
                location = entry.find("LOCATION")
                if location is not None:
                    if not dry_run:
                        location.set("FILE", new_path)
                        location.set("VOLUME", "")
                    stats["rebased"] += 1
        elif action == "ignore":
            missing_audio_ids.add(audio_id)

    duplicate_group_ids = set()
    for d in selection.duplicates:
        group_id = d.get("group_id", "")
        action = d.get("action", "")

        if action == "merge":
            duplicate_group_ids.add(group_id)
        elif action == "ignore":
            duplicate_group_ids.add(group_id)

    tracks_to_remove = set(missing_audio_ids)
    for d in selection.duplicates:
        group_id = d.get("group_id", "")
        action = d.get("action", "")

        if action == "merge":
            winner_id = d.get("winner_id")
            if winner_id:
                for entry in collection.findall("ENTRY"):
                    entry_id = entry.get("AUDIO_ID", "")
                    if entry_id in audio_id_to_track:
                        track = audio_id_to_track[entry_id]
                        if track and hasattr(track, 'audio_id'):
                            pass
            stats["merged"] += 1

    if selection.excluded:
        for excl in selection.excluded:
            excl_id = excl.get("audio_id", "") or excl.get("group_id", "")
            if excl_id:
                tracks_to_remove.add(str(excl_id))

    entries_to_keep = []
    for entry in collection.findall("ENTRY"):
        audio_id = entry.get("AUDIO_ID", "")
        if audio_id in tracks_to_remove:
            if not dry_run:
                collection.remove(entry)
            stats["removed"] += 1
        else:
            entries_to_keep.append(entry)

    if not dry_run:
        collection.set("ENTRIES", str(len(entries_to_keep)))

        xml_declaration = '<?xml version="1.0" encoding="UTF-8" standalone="no" ?>\n'
        nml_str = ET.tostring(root, encoding="unicode")

        with open(nml_path, "w", encoding="utf-8") as f:
            f.write(xml_declaration + nml_str)

    return stats


def parse_track_from_entry(entry_el) -> Optional[Track]:
    """Parse a Track from an NML ENTRY element."""
    try:
        title = entry_el.get("TITLE", "")
        artist = entry_el.get("ARTIST", "")
        audio_id = entry_el.get("AUDIO_ID", "")

        location = entry_el.find("LOCATION")
        file_path = ""
        volume = ""
        volume_id = ""
        if location is not None:
            file_path = location.get("FILE", "")
            volume = location.get("VOLUME", "")
            volume_id = location.get("VOLUMEID", "")

        album_el = entry_el.find("ALBUM")
        album = album_el.get("TITLE", "") if album_el is not None else ""

        info = entry_el.find("INFO")
        playtime = 0.0
        playcount = 0
        if info is not None:
            playtime = float(info.get("PLAYTIME", 0) or 0)
            playcount = int(info.get("PLAYCOUNT", 0) or 0)

        tempo = entry_el.find("TEMPO")
        bpm = 0.0
        bpm_quality = 0.0
        if tempo is not None:
            bpm = float(tempo.get("BPM", 0) or 0)
            bpm_quality = float(tempo.get("BPM_QUALITY", 0) or 0)

        return Track(
            title=title,
            artist=artist,
            file_path=file_path,
            volume=volume,
            volume_id=volume_id,
            album=album,
            bpm=bpm,
            bpm_quality=bpm_quality,
            playtime=playtime,
            playcount=playcount,
            audio_id=audio_id,
        )
    except Exception:
        return None

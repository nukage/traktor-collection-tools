"""Duplicate track detection and merging for Traktor collections."""

import re
import json
from dataclasses import dataclass, field
from typing import Optional
from collections import defaultdict

from parser import Track, Cue


@dataclass
class DuplicateGroup:
    normalized_key: str
    tracks: list[Track]
    winner: Optional[Track] = None
    merged_track: Optional[Track] = None
    same_file: bool = False
    merge_actions: list = field(default_factory=list)


@dataclass
class MergeAction:
    field: str
    from_track: Track
    old_value: any
    new_value: any


def normalize(text: str) -> str:
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'\(feat\.[^)]+\)', '', text)
    text = re.sub(r'\(featuring[^)]+\)', '', text)
    text = re.sub(r'\(feat[^)]+\)', '', text)
    text = re.sub(r'\s+feat\.?\s+', ' ', text)
    text = re.sub(r'\s+featuring\s+', ' ', text)
    text = re.sub(r'\s+vs\.?\s+', ' ', text)
    text = re.sub(r'\s+ft\.?\s+', ' ', text)
    text = re.sub(r'\s+&\s+', ' ', text)
    text = re.sub(r'\s*[,/]\s*', ' ', text)
    text = re.sub(r'\s*-\s*', ' - ', text)
    text = re.sub(r'\([^)]*\)', '', text)
    text = re.sub(r'\s+', ' ', text)
    text = text.strip(' -')
    return text


def get_grouping_key(track: Track) -> str:
    artist = normalize(track.artist)
    title = normalize(track.title)
    return f"{artist} | {title}"


def score_track(track: Track) -> float:
    score = 0.0
    score += min(track.file_size / 10_000_000, 10) if track.file_size > 0 else 0
    score += min(track.bitrate / 320_000, 5) if track.bitrate > 0 else 0
    score += track.playtime / 600 if track.playtime > 0 else 0
    score += track.playcount * 0.5
    if track.bpm > 0:
        score += 0.5
    if track.stems:
        score += 2
    if track.import_date:
        try:
            year = int(track.import_date[:4])
            if year >= 2020:
                score += 1
        except:
            pass
    return score


def playtime_matches(t1: Track, t2: Track, tolerance: float = 1.0) -> bool:
    if t1.playtime <= 0 or t2.playtime <= 0:
        return False
    return abs(t1.playtime - t2.playtime) <= tolerance


def find_duplicates(tracks: list[Track], min_group_size: int = 2) -> list[DuplicateGroup]:
    groups = defaultdict(list)
    for track in tracks:
        key = get_grouping_key(track)
        if key:
            groups[key].append(track)

    duplicate_groups = []
    for key, group_tracks in groups.items():
        if len(group_tracks) < min_group_size:
            continue

        group_tracks.sort(key=score_track, reverse=True)
        winner = group_tracks[0]

        same_file = all(playtime_matches(winner, t) for t in group_tracks[1:])

        duplicate_groups.append(DuplicateGroup(
            normalized_key=key,
            tracks=group_tracks,
            winner=winner,
            same_file=same_file
        ))

    return duplicate_groups


def merge_tracks(winner: Track, duplicates: list[Track], same_file: bool) -> tuple[Track, list[MergeAction]]:
    merged = Track(
        title=winner.title,
        artist=winner.artist,
        file_path=winner.file_path,
        volume=winner.volume,
        volume_id=winner.volume_id,
        album=winner.album,
        bpm=winner.bpm,
        bpm_quality=winner.bpm_quality,
        musical_key=winner.musical_key,
        playtime=winner.playtime,
        playcount=winner.playcount,
        import_date=winner.import_date,
        last_played=winner.last_played,
        bitrate=winner.bitrate,
        file_size=winner.file_size,
        peak_db=winner.peak_db,
        perceived_db=winner.perceived_db,
        analyzed_db=winner.analyzed_db,
        audio_id=winner.audio_id,
        cues=list(winner.cues),
        stems=winner.stems
    )

    merge_actions = []

    for dup in duplicates:
        if dup.bpm > 0 and merged.bpm <= 0:
            merge_actions.append(MergeAction("bpm", dup, 0, dup.bpm))
            merged.bpm = dup.bpm
            merged.bpm_quality = dup.bpm_quality

        if dup.musical_key > 0 and merged.musical_key <= 0:
            merge_actions.append(MergeAction("musical_key", dup, 0, dup.musical_key))
            merged.musical_key = dup.musical_key

        if not merged.album and dup.album:
            merge_actions.append(MergeAction("album", dup, "", dup.album))
            merged.album = dup.album

        if len(dup.title) > len(merged.title):
            merge_actions.append(MergeAction("title", dup, merged.title, dup.title))
            merged.title = dup.title

        merged.playcount += dup.playcount

        if same_file and playtime_matches(winner, dup):
            existing_hotcue_indices = {c.hotcue for c in merged.cues if c.hotcue >= 0}
            for cue in dup.cues:
                if cue.hotcue < 0:
                    continue
                new_cue = Cue(
                    name=cue.name,
                    type=cue.type,
                    start=cue.start,
                    length=cue.length,
                    repeats=cue.repeats,
                    hotcue=cue.hotcue,
                    color=cue.color
                )
                if new_cue.hotcue in existing_hotcue_indices:
                    max_existing = max(existing_hotcue_indices)
                    new_cue = Cue(
                        name=cue.name,
                        type=cue.type,
                        start=cue.start,
                        length=cue.length,
                        repeats=cue.repeats,
                        hotcue=max_existing + 1,
                        color=cue.color
                    )
                merged.cues.append(new_cue)
                existing_hotcue_indices.add(new_cue.hotcue)
                merge_actions.append(MergeAction("cue", dup, len(merged.cues) - 1, new_cue.hotcue))

    return merged, merge_actions


def format_duplicate_group(group: DuplicateGroup, index: int = 0) -> str:
    winner = group.winner
    other_count = len(group.tracks) - 1

    same_file_str = "SAME" if group.same_file else "DIFF"
    cues_info = f"{len(winner.cues)} cues" if winner.cues else "no cues"

    lines = [
        f"{index+1}. {winner.artist} - {winner.title}",
        f"   Winner: {winner.bpm:.1f} BPM | {winner.playtime:.0f}s | {winner.file_size / 1_000_000:.1f}MB | {cues_info}",
        f"   + {other_count} duplicate(s) | Playtime match: {same_file_str}",
    ]

    if group.merge_actions:
        merged_fields = list(set(a.field for a in group.merge_actions))
        lines.append(f"   Merged: {', '.join(merged_fields)}")

    dup_details = []
    for t in group.tracks[1:]:
        dup_details.append(f"     - {t.artist} | {t.title} | {t.bpm:.1f} BPM | {t.playtime:.0f}s | {t.file_size / 1_000_000:.1f}MB")

    lines.extend(dup_details)

    return "\n".join(lines)


def generate_duplicate_report(groups: list[DuplicateGroup]) -> dict:
    report = {
        "total_groups": len(groups),
        "same_file_count": sum(1 for g in groups if g.same_file),
        "alternate_version_count": sum(1 for g in groups if not g.same_file),
        "total_tracks_affected": sum(len(g.tracks) for g in groups),
        "groups": []
    }

    for i, group in enumerate(groups):
        group_report = {
            "index": i,
            "normalized_key": group.normalized_key,
            "winner": {
                "title": group.winner.title,
                "artist": group.winner.artist,
                "bpm": group.winner.bpm,
                "playtime": group.winner.playtime,
                "file_size": group.winner.file_size,
                "cue_count": len(group.winner.cues),
            },
            "same_file": group.same_file,
            "duplicate_count": len(group.tracks) - 1,
            "duplicates": [
                {
                    "title": t.title,
                    "artist": t.artist,
                    "bpm": t.bpm,
                    "playtime": t.playtime,
                    "file_size": t.file_size,
                    "cue_count": len(t.cues),
                }
                for t in group.tracks[1:]
            ],
            "merge_actions": [
                {"field": a.field, "from_artist": a.from_track.artist, "old": a.old_value, "new": a.new_value}
                for a in group.merge_actions
            ]
        }
        report["groups"].append(group_report)

    return report


def generate_nml_patch(groups: list[DuplicateGroup], original_nml_path: str, output_path: str) -> dict:
    """Generate an NML patch file with duplicates removed and winners updated with merged metadata."""
    import xml.etree.ElementTree as ET

    tree = ET.parse(original_nml_path)
    root = tree.getroot()

    collection = root.find("COLLECTION")
    if collection is None:
        return {"error": "No COLLECTION found in NML"}

    tracks_to_remove = set()
    merge_map = {}

    for group in groups:
        for dup in group.tracks[1:]:
            tracks_to_remove.add(dup.audio_id)

        merged, actions = merge_tracks(group.winner, group.tracks[1:], group.same_file)
        merge_map[group.winner.audio_id] = merged

    entries_to_keep = []
    entries_removed = 0

    for entry in collection.findall("ENTRY"):
        audio_id = entry.get("AUDIO_ID", "")
        if audio_id in tracks_to_remove:
            entries_removed += 1
            continue

        if audio_id in merge_map:
            merged = merge_map[audio_id]
            entry.set("TITLE", merged.title)
            entry.set("ARTIST", merged.artist)

            tempo = entry.find("TEMPO")
            if tempo is not None:
                tempo.set("BPM", str(merged.bpm))
                tempo.set("BPM_QUALITY", str(merged.bpm_quality))

            info = entry.find("INFO")
            if info is not None:
                info.set("KEY", str(merged.musical_key))
                info.set("PLAYCOUNT", str(merged.playcount))

            for existing_cue in entry.findall("CUE_V2"):
                entry.remove(existing_cue)

            for cue in merged.cues:
                cue_el = ET.SubElement(entry, "CUE_V2")
                cue_el.set("NAME", cue.name)
                cue_el.set("DISPL_ORDER", "0")
                cue_el.set("TYPE", str(cue.type))
                cue_el.set("START", str(cue.start))
                cue_el.set("LEN", str(cue.length))
                cue_el.set("REPEATS", str(cue.repeats))
                cue_el.set("HOTCUE", str(cue.hotcue))
                cue_el.set("COLOR", cue.color)

        entries_to_keep.append(entry)

    for existing_entry in list(collection):
        if existing_entry.tag == "ENTRY":
            collection.remove(existing_entry)

    for entry in entries_to_keep:
        collection.append(entry)

    collection.set("ENTRIES", str(len(entries_to_keep)))

    xml_declaration = '<?xml version="1.0" encoding="UTF-8" standalone="no" ?>\n'
    nml_str = ET.tostring(root, encoding="unicode")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(xml_declaration + nml_str)

    return {
        "output_path": output_path,
        "entries_removed": entries_removed,
        "entries_kept": len(entries_to_keep),
        "groups_processed": len(groups),
    }
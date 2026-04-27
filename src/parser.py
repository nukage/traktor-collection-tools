"""Parse Traktor NML collection files."""

import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
import json


@dataclass
class Track:
    title: str
    artist: str
    file_path: str
    volume: str
    volume_id: str
    album: str = ""
    bpm: float = 0.0
    bpm_quality: float = 0.0
    musical_key: int = 0
    playtime: float = 0.0
    playcount: int = 0
    import_date: str = ""
    last_played: str = ""
    bitrate: int = 0
    file_size: int = 0
    peak_db: float = 0.0
    perceived_db: float = 0.0
    analyzed_db: float = 0.0
    audio_id: str = ""
    cues: list = field(default_factory=list)
    stems: Optional[dict] = None

    @property
    def full_path(self) -> str:
        parts = [p for p in [self.volume, self.file_path] if p]
        return "/".join(parts).replace("//", "/")


@dataclass
class Cue:
    name: str
    type: int
    start: float
    length: float
    repeats: int
    hotcue: int
    color: str = "#FFFFFF"


class NMLParser:
    NAMESPACE = ""

    ENTRY_TAGS = [
        "COLLECTION", "PLAYLISTS"
    ]

    def __init__(self, nml_path: str):
        self.nml_path = Path(nml_path)
        self.tracks: list[Track] = []
        self._stats = {}

    def parse(self) -> list[Track]:
        tree = ET.parse(self.nml_path)
        root = tree.getroot()

        for child in root:
            tag = child.tag.replace(self.NAMESPACE, "")
            if tag == "COLLECTION":
                self._parse_collection(child)
            elif tag == "PLAYLISTS":
                self._parse_playlists(child)

        return self.tracks

    def _parse_collection(self, collection_el) -> None:
        for entry in collection_el.findall("ENTRY"):
            track = self._parse_entry(entry)
            if track:
                self.tracks.append(track)

    def _parse_entry(self, entry_el) -> Optional[Track]:
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
            bitrate = 0
            musical_key = 0
            playtime = 0.0
            playcount = 0
            import_date = ""
            last_played = ""
            file_size = 0
            if info is not None:
                bitrate = int(info.get("BITRATE", 0))
                musical_key = int(info.get("KEY", 0))
                playtime = float(info.get("PLAYTIME_FLOAT", 0))
                playcount = int(info.get("PLAYCOUNT", 0))
                import_date = info.get("IMPORT_DATE", "")
                last_played = info.get("LAST_PLAYED", "")
                file_size = int(info.get("FILESIZE", 0))

            tempo = entry_el.find("TEMPO")
            bpm = 0.0
            bpm_quality = 0.0
            if tempo is not None:
                bpm = float(tempo.get("BPM", 0))
                bpm_quality = float(tempo.get("BPM_QUALITY", 0))

            loudness = entry_el.find("LOUDNESS")
            peak_db = 0.0
            perceived_db = 0.0
            analyzed_db = 0.0
            if loudness is not None:
                peak_db = float(loudness.get("PEAK_DB", 0))
                perceived_db = float(loudness.get("PERCEIVED_DB", 0))
                analyzed_db = float(loudness.get("ANALYZED_DB", 0))

            cues = []
            for cue_el in entry_el.findall("CUE_V2"):
                cue = Cue(
                    name=cue_el.get("NAME", ""),
                    type=int(cue_el.get("TYPE", 0)),
                    start=float(cue_el.get("START", 0)),
                    length=float(cue_el.get("LEN", 0)),
                    repeats=int(cue_el.get("REPEATS", -1)),
                    hotcue=int(cue_el.get("HOTCUE", -1)),
                    color=cue_el.get("COLOR", "#FFFFFF")
                )
                cues.append(cue)

            stems = None
            stems_el = entry_el.find("STEMS")
            if stems_el is not None:
                stems_json = stems_el.get("STEMS", "")
                try:
                    stems = json.loads(stems_json)
                except json.JSONDecodeError:
                    pass

            modified = entry_el.get("MODIFIED_DATE", "")

            return Track(
                title=title,
                artist=artist,
                file_path=file_path,
                volume=volume,
                volume_id=volume_id,
                album=album,
                bpm=bpm,
                bpm_quality=bpm_quality,
                musical_key=musical_key,
                playtime=playtime,
                playcount=playcount,
                import_date=import_date,
                last_played=last_played,
                bitrate=bitrate,
                file_size=file_size,
                peak_db=peak_db,
                perceived_db=perceived_db,
                analyzed_db=analyzed_db,
                audio_id=audio_id,
                cues=cues,
                stems=stems
            )
        except Exception as e:
            return None

    def _parse_playlists(self, playlists_el) -> None:
        pass

    def get_stats(self) -> dict:
        if not self.tracks:
            return {}

        bpm_values = [t.bpm for t in self.tracks if t.bpm > 0]
        playtime_values = [t.playtime for t in self.tracks if t.playtime > 0]
        import_years = [t.import_date[:4] for t in self.tracks if t.import_date and len(t.import_date) >= 4]

        albums = {}
        for t in self.tracks:
            if t.album:
                albums[t.album] = albums.get(t.album, 0) + 1

        return {
            "total_tracks": len(self.tracks),
            "tracks_with_bpm": len(bpm_values),
            "bpm_min": min(bpm_values) if bpm_values else 0,
            "bpm_max": max(bpm_values) if bpm_values else 0,
            "bpm_avg": sum(bpm_values) / len(bpm_values) if bpm_values else 0,
            "total_playtime_seconds": sum(playtime_values),
            "unique_albums": len(albums),
            "top_albums": sorted(albums.items(), key=lambda x: -x[1])[:20],
            "import_years": dict(sorted(
                {y: import_years.count(y) for y in set(import_years)}.items()
            )),
        }


def parse_nml(nml_path: str) -> tuple[list[Track], dict]:
    parser = NMLParser(nml_path)
    tracks = parser.parse()
    stats = parser.get_stats()
    return tracks, stats
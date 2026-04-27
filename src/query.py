"""Query engine for Traktor collection."""

import sys
sys.path.insert(0, 'src')
from parser import parse_nml, Track
from dataclasses import dataclass, field
from typing import Optional
from collections import defaultdict


@dataclass
class Query:
    bpm_min: Optional[float] = None
    bpm_max: Optional[float] = None
    artist: Optional[str] = None
    album: Optional[str] = None
    title_contains: Optional[str] = None
    import_after: Optional[str] = None
    import_before: Optional[str] = None
    key: Optional[int] = None
    limit: int = 50
    sort_by: str = "bpm"
    sort_desc: bool = True
    exclude_artist: Optional[str] = None
    file_extension: Optional[str] = None
    has_hotcues: bool = False
    year: Optional[int] = None
    min_playtime: Optional[float] = None
    max_playtime: Optional[float] = None


class Collection:
    def __init__(self, tracks: list[Track]):
        self.tracks = tracks
        self._artist_cache = None
        self._album_cache = None

    def search(self, q: Query) -> list[Track]:
        results = []
        for t in self.tracks:
            if not self._match_track(t, q):
                continue
            results.append(t)
        return self._sort(results, q)

    def _match_track(self, t: Track, q: Query) -> bool:
        if q.bpm_min is not None and (t.bpm <= 0 or t.bpm < q.bpm_min):
            return False
        if q.bpm_max is not None and (t.bpm <= 0 or t.bpm > q.bpm_max):
            return False
        if q.artist and q.artist.lower() not in t.artist.lower():
            return False
        if q.exclude_artist and q.exclude_artist.lower() in t.artist.lower():
            return False
        if q.album and q.album.lower() not in t.album.lower():
            return False
        if q.title_contains and q.title_contains.lower() not in t.title.lower():
            return False
        if q.key is not None and t.musical_key != q.key:
            return False
        if q.file_extension:
            ext = t.file_path.split(".")[-1].lower() if "." in t.file_path else ""
            if ext != q.file_extension.lower():
                return False
        if q.has_hotcues:
            if not any(c.type == 0 and c.hotcue >= 0 for c in t.cues):
                return False
        if q.import_after:
            year = int(q.import_after[:4]) if len(q.import_after) >= 4 else 0
            track_year = int(t.import_date[:4]) if len(t.import_date) >= 4 else 0
            if track_year < year:
                return False
        if q.import_before:
            year = int(q.import_before[:4]) if len(q.import_before) >= 4 else 9999
            track_year = int(t.import_date[:4]) if len(t.import_date) >= 4 else 0
            if track_year > year:
                return False
        if q.year:
            track_year = int(t.import_date[:4]) if len(t.import_date) >= 4 else 0
            if track_year != q.year:
                return False
        if q.min_playtime is not None and t.playtime < q.min_playtime:
            return False
        if q.max_playtime is not None and t.playtime > q.max_playtime:
            return False
        return True

    def _sort(self, tracks: list[Track], q: Query) -> list[Track]:
        if q.sort_by == "bpm":
            tracks.sort(key=lambda t: t.bpm if t.bpm > 0 else 0, reverse=q.sort_desc)
        elif q.sort_by == "title":
            tracks.sort(key=lambda t: t.title.lower(), reverse=q.sort_desc)
        elif q.sort_by == "artist":
            tracks.sort(key=lambda t: t.artist.lower(), reverse=q.sort_desc)
        elif q.sort_by == "playtime":
            tracks.sort(key=lambda t: t.playtime, reverse=q.sort_desc)
        elif q.sort_by == "import_date":
            tracks.sort(key=lambda t: t.import_date, reverse=q.sort_desc)
        return tracks[:q.limit]

    def by_artist(self, artist_name: str) -> list[Track]:
        q = Query(artist=artist_name, limit=200)
        return self.search(q)

    def by_bpm_range(self, min_bpm: float, max_bpm: float, limit: int = 50) -> list[Track]:
        q = Query(bpm_min=min_bpm, bpm_max=max_bpm, limit=limit)
        return self.search(q)

    def similar_to(self, track: Track, bpm_tolerance: float = 5, limit: int = 20) -> list[Track]:
        results = []
        for t in self.tracks:
            if t.title == track.title and t.artist == track.artist:
                continue
            if t.bpm <= 0:
                continue
            if abs(t.bpm - track.bpm) <= bpm_tolerance:
                results.append(t)
        results.sort(key=lambda t: abs(t.bpm - track.bpm))
        return results[:limit]

    def get_artists(self) -> dict[str, int]:
        artists = defaultdict(int)
        for t in self.tracks:
            if t.artist:
                artists[t.artist] += 1
        return dict(sorted(artists.items(), key=lambda x: -x[1]))

    def get_albums(self) -> dict[str, int]:
        albums = defaultdict(int)
        for t in self.tracks:
            if t.album:
                albums[t.album] += 1
        return dict(sorted(albums.items(), key=lambda x: -x[1]))


KEY_NAMES = {
    0: "C", 1: "C#", 2: "D", 3: "D#", 4: "E", 5: "F",
    6: "F#", 7: "G", 8: "G#", 9: "A", 10: "A#", 11: "B",
    12: "Cm", 13: "C#m", 14: "Dm", 15: "D#m", 16: "Em", 17: "Fm",
    18: "F#m", 19: "Gm", 20: "G#m", 21: "Am", 22: "A#m", 23: "Bm"
}

MUSICAL_KEY_TO_CAMELOT = {
    0: "8B", 1: "3B", 2: "10B", 3: "5B", 4: "12B", 5: "7B",
    6: "2B", 7: "9B", 8: "4B", 9: "11B", 10: "6B", 11: "1B",
    12: "8A", 13: "3A", 14: "10A", 15: "5A", 16: "12A", 17: "7A",
    18: "2A", 19: "9A", 20: "4A", 21: "11A", 22: "6A", 23: "1A"
}


def format_track(t: Track, index: int = 0) -> str:
    key_name = KEY_NAMES.get(t.musical_key, f"K{t.musical_key}")
    camelot = MUSICAL_KEY_TO_CAMELOT.get(t.musical_key, "?")
    cues = len([c for c in t.cues if c.type == 0 and c.hotcue >= 0])
    long_flag = "LIKELY MIX" if t.playtime > 600 else ""
    return (f"{index+1:3}. {t.artist[:25]:25} | {t.title[:35]:35} | "
            f"{t.bpm:6.1f} | {key_name}({camelot}) | {t.album[:30]:30} | {cues} cues | {long_flag}")


def format_track_simple(t: Track) -> str:
    return f"{t.artist} - {t.title} ({t.bpm:.1f} BPM)"


def load_collection(nml_path: str) -> Collection:
    tracks, _ = parse_nml(nml_path)
    return Collection(tracks)
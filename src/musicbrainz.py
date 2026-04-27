"""MusicBrainz API integration for metadata lookup."""

import os
import time
import sys
from dataclasses import dataclass
from typing import Optional

try:
    import musicbrainzngs
    HAS_MUSICBRAINZNGs = True
except ImportError:
    HAS_MUSICBRAINZNGs = False

from parser import Track


@dataclass
class MetadataResult:
    track: Track
    found: bool
    album: str = ""
    year: int = 0
    artist_normalized: str = ""
    release_id: str = ""
    score: float = 0.0
    error: Optional[str] = None


class MusicBrainzLookup:
    APP_NAME = "TraktorCollectionTools"
    APP_VERSION = "1.0"
    APP_CONTACT = ""

    def __init__(self, user_agent: str = None):
        if not HAS_MUSICBRAINZNGs:
            raise ImportError("musicbrainzngs not installed. Run: pip install musicbrainzngs")

        ua = user_agent or f"{self.APP_NAME}/{self.APP_VERSION} (contact@{self.APP_CONTACT})"
        musicbrainzngs.set_useragent(self.APP_NAME, self.APP_VERSION, self.APP_CONTACT)
        self.rate_limit_delay = 1.0

    def _rate_limit(self):
        time.sleep(self.rate_limit_delay)

    def search_recording(self, artist: str, title: str, limit: int = 5) -> Optional[dict]:
        self._rate_limit()
        try:
            result = musicbrainzngs.search_recordings(
                recording=title,
                artist=artist,
                limit=limit
            )
            if result.get('recording-list'):
                return result
            return None
        except musicbrainzngs.WebServiceError as e:
            return None

    def lookup_recording(self, recording_id: str) -> Optional[dict]:
        self._rate_limit()
        try:
            return musicbrainzngs.get_recording_by_id(
                recording_id,
                includes=["artists", "releases", "isrcs"]
            )
        except musicbrainzngs.WebServiceError:
            return None

    def get_release_info(self, release_id: str) -> Optional[dict]:
        self._rate_limit()
        try:
            return musicbrainzngs.get_release_by_id(
                release_id,
                includes=["artist-credits"]
            )
        except musicbrainzngs.WebServiceError:
            return None

    def find_best_match(self, artist: str, title: str, playtime: float = 0) -> Optional[dict]:
        results = self.search_recording(artist, title)
        if not results or not results.get('recording-list'):
            return None

        for rec in results['recording-list']:
            score = int(rec.get('ext:score', 0))
            if score < 80:
                continue

            if playtime > 0 and rec.get('length'):
                rec_ms = int(rec['length'])
                rec_secs = rec_ms / 1000
                if abs(rec_secs - playtime) > 10:
                    continue

            return rec

        return results['recording-list'][0] if results['recording-list'] else None

    def extract_metadata(self, recording: dict) -> tuple[str, int]:
        album = ""
        year = 0

        release_list = recording.get('release-list', [])
        if release_list:
            primary = release_list[0]
            album = primary.get('title', '')

            date_str = primary.get('date', '')
            if date_str:
                year = int(date_str[:4]) if len(date_str) >= 4 else 0

        return album, year

    def lookup_track(self, track: Track) -> MetadataResult:
        if not track.artist or not track.title:
            return MetadataResult(track=track, found=False, error="Missing artist or title")

        match = self.find_best_match(track.artist, track.title, track.playtime)

        if not match:
            return MetadataResult(track=track, found=False, error="No match found")

        album, year = self.extract_metadata(match)

        return MetadataResult(
            track=track,
            found=True,
            album=album,
            year=year,
            artist_normalized=track.artist,
            release_id=match.get('id', ''),
            score=float(match.get('ext:score', 0))
        )

    def lookup_tracks(self, tracks: list[Track], progress_callback=None) -> list[MetadataResult]:
        results = []
        total = len(tracks)

        for i, track in enumerate(tracks):
            result = self.lookup_track(track)
            results.append(result)

            if progress_callback:
                pct = ((i + 1) / total) * 100
                bar = "#" * int(pct // 2) + " " * (50 - int(pct // 2))
                safe_title = track.title[:40].encode('ascii', 'replace').decode('ascii')
                print(f"\r[{bar}] {pct:5.1f}% ({i+1}/{total}) | {safe_title:40}", end="", flush=True)

        if progress_callback:
            print()

        return results


def find_tracks_missing_metadata(tracks: list[Track]) -> list[Track]:
    missing = []
    for t in tracks:
        if not t.album or t.import_date[:4] == "1900":
            missing.append(t)
    return missing


if __name__ == "__main__":
    from parser import parse_nml

    nml_path = r"C:\Users\nukag\Documents\Native Instruments\Traktor 4.1.0\collection.nml"
    tracks, _ = parse_nml(nml_path)

    missing = find_tracks_missing_metadata(tracks)
    print(f"Tracks missing metadata: {len(missing)}")

    if missing:
        mb = MusicBrainzLookup()
        print(f"Looking up first 5...")
        results = mb.lookup_tracks(missing[:5])
        print("\nResults:")
        for r in results:
            status = "FOUND" if r.found else "NOT FOUND"
            print(f"  {r.track.artist[:20]:20} | {r.track.title[:30]:30} | {status} | {r.album[:20] if r.album else '-':20} | {r.year}")
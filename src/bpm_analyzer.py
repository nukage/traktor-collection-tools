"""BPM detection from audio files using librosa."""

import os
import sys
import json
import librosa
import numpy as np
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Callable

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from parser import Track


@dataclass
class BPMResult:
    track: Track
    detected_bpm: float
    confidence: float
    method: str
    error: Optional[str] = None


class BPMAnalyzer:
    SUPPORTED_FORMATS = {".mp3", ".wav", ".flac", ".m4a", ".ogg", ".aif", ".aiff"}

    def __init__(self, collection_path: str):
        self.collection_path = collection_path
        self.results: list[BPMResult] = []

    def analyze_track(self, track: Track, progress_callback: Optional[Callable] = None) -> BPMResult:
        file_path = self._get_full_path(track)
        if not file_path or not os.path.exists(file_path):
            return BPMResult(
                track=track,
                detected_bpm=0.0,
                confidence=0.0,
                method="none",
                error="File not found"
            )

        try:
            y, sr = librosa.load(file_path, sr=None, duration=120)
            if len(y) < sr:
                return BPMResult(
                    track=track,
                    detected_bpm=0.0,
                    confidence=0.0,
                    method="none",
                    error="File too short"
                )

            onset_env = librosa.onset.onset_strength(y=y, sr=sr)
            tempo, beats = librosa.beat.beat_track(onset_envelope=onset_env, sr=sr)
            confidence = self._calculate_confidence(beats, onset_env)

            if tempo < 50:
                tempo *= 2
            if tempo > 200:
                tempo /= 2

            return BPMResult(
                track=track,
                detected_bpm=float(tempo),
                confidence=float(confidence),
                method="librosa_beat"
            )
        except Exception as e:
            return BPMResult(
                track=track,
                detected_bpm=0.0,
                confidence=0.0,
                method="none",
                error=str(e)
            )

    def _get_full_path(self, track: Track) -> str:
        if track.volume and track.file_path:
            if track.volume.endswith(":"):
                return f"{track.volume}\\{track.file_path}"
            return track.file_path
        return track.file_path

    def _calculate_confidence(self, beats: np.ndarray, onset_env: np.ndarray) -> float:
        if len(beats) < 2:
            return 0.0
        beat_intervals = np.diff(beats)
        if len(beat_intervals) == 0:
            return 0.0
        std = np.std(beat_intervals)
        mean = np.mean(beat_intervals)
        if mean == 0:
            return 0.0
        cv = std / mean
        confidence = max(0.0, 1.0 - cv)
        return confidence

    def analyze_tracks(self, tracks: list[Track], progress_callback: Optional[Callable] = None) -> list[BPMResult]:
        results = []
        total = len(tracks)
        for i, track in enumerate(tracks):
            result = self.analyze_track(track, progress_callback)
            results.append(result)
            if progress_callback:
                progress_callback(i + 1, total, track.title)
        return results

    def save_results(self, results: list[BPMResult], output_path: str):
        data = []
        for r in results:
            data.append({
                "title": r.track.title,
                "artist": r.track.artist,
                "original_bpm": r.track.bpm,
                "detected_bpm": r.detected_bpm,
                "confidence": r.confidence,
                "method": r.method,
                "error": r.error,
                "file_path": r.track.file_path,
            })
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)


def analyze_missing_bpm(tracks: list[Track], progress_callback: Optional[Callable] = None) -> list[BPMResult]:
    missing_bpm = [t for t in tracks if t.bpm <= 0 or t.bpm_quality < 50]
    analyzer = BPMAnalyzer("")
    return analyzer.analyze_tracks(missing_bpm, progress_callback)


def print_progress(current: int, total: int, track_title: str):
    pct = (current / total) * 100
    bar = "#" * int(pct // 2) + " " * (50 - int(pct // 2))
    print(f"\r[{bar}] {pct:5.1f}% ({current}/{total}) | {track_title[:40]:40}", end="", flush=True)


if __name__ == "__main__":
    from parser import parse_nml

    nml_path = r"\\UNRAIDTOWER\Storage\Temp\collection.nml"
    tracks, _ = parse_nml(nml_path)

    missing_bpm = [t for t in tracks if t.bpm <= 0]
    print(f"Tracks missing BPM: {len(missing_bpm)}")

    if missing_bpm:
        print(f"Analyzing first 5 missing BPM tracks...")
        results = analyze_missing_bpm(missing_bpm[:5], print_progress)
        print("\n\nResults:")
        for r in results:
            status = "OK" if r.error is None else f"ERR: {r.error}"
            print(f"  {r.track.title[:40]:40} | BPM: {r.detected_bpm:6.1f} | Conf: {r.confidence:.2f} | {status}")
    else:
        print("All tracks have BPM!")
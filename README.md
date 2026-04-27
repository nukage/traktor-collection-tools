# Traktor Collection Tools

AI-assisted system for curating, cleaning, and extending a Traktor DJ collection via natural language queries.

**Source of truth:** Traktor NML collection file (no MediaMonkey bridge needed)

## What This Does

Parses Traktor's NML collection files and provides tools to:
- **Query** your collection with natural language-style commands
- **Analyze** tracks for BPM (using librosa audio analysis)
- **Detect** and merge duplicate tracks (preserving cue points)
- **Export** playlists to M3U, NML, or plain text

## Setup

```bash
pip install librosa soundfile numpy
python src/cli.py help
```

**Requirements:** Python 3.10+

## Quick Start

```bash
# Analyze collection stats
python src/cli.py stats

# Find tracks
python src/cli.py list "drum and bass 170-180"
python src/cli.py find "Au5"
python src/cli.py similar "Interstellar"

# List all artists
python src/cli.py artists -n 30

# Analyze tracks missing BPM (requires accessible file paths)
python src/cli.py analyze --limit 20

# Find and merge duplicates
python src/cli.py duplicates -n 20
python src/cli.py duplicates -n 20 -p cleaned.nml  # generate NML patch
```

## Commands

| Command | Description | Example |
|---------|-------------|---------|
| `list` | Search tracks by BPM, artist, year | `list drum and bass 170-180` |
| `find` | Find tracks by title | `find Au5` |
| `similar` | Find tracks similar to given title | `similar Interstellar` |
| `artists` | List all artists | `artists -n 30` |
| `albums` | List all albums | `albums -n 20` |
| `stats` | Collection statistics | `stats` |
| `analyze` | BPM detection for tracks missing it | `analyze --limit 20` |
| `duplicates` | Find and merge duplicate tracks | `duplicates -n 20 -p cleaned.nml` |
| `export` | Export playlist to M3U/NML/TXT | `export set.m3u "techno 130-145"` |

## NML File Location

On Windows: `%APPDATA%\Native Instruments\Traktor\<version>\`

Example network path: `\\UNRAIDTOWER\Storage\Temp\collection.nml`

Specify with `--nml` flag:
```bash
python src/cli.py list --nml "\\UNRAIDTOWER\Storage\Temp\collection.nml" "drum and bass"
```

## Duplicate Detection

The system finds tracks that are the same song but imported multiple times:

1. **Normalizes** artist + title (strips feat./featuring/vs./&, parentheticals)
2. **Groups** by normalized key
3. **Scores** each variant (file size, bitrate, playtime, plays, recency)
4. **Merges** metadata into winner (BPM, key, cues from matching-length variants)
5. **Outputs** NML patch file for manual review

**Cue point rule:** Only merged when playtime matches within ±1 second (same file = safe to merge cues).

## File Structure

```
src/
  parser.py       - NML XML parser (Track, Cue dataclasses)
  query.py        - Collection search engine (Query filters, BPM/artist/album)
  bpm_analyzer.py - librosa-based BPM detection from audio files
  duplicates.py   - Duplicate detection engine + NML patch generator
  cli.py          - All CLI commands
```

## Next Steps

- MusicBrainz/Discogs API for metadata lookup
- Web UI for visual collection management
- Beatport/SoundCloud discovery agent
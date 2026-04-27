# DJ Collection Manager — Status

## What Was Built

### Core Infrastructure

| Component | File | Status |
|-----------|------|--------|
| NML Parser | `src/parser.py` | Done |
| Collection Query Engine | `src/query.py` | Done |
| CLI | `src/cli.py` | Done |
| BPM Analyzer | `src/bpm_analyzer.py` | Done |
| Duplicate Detection | `src/duplicates.py` | Done |

### CLI Commands

```
list <query>     # Search tracks by BPM/artist/year
find <title>     # Find tracks by title
similar <title>  # Find similar tracks
artists          # List all artists
albums           # List all albums
stats            # Collection statistics
analyze          # BPM detection for tracks missing it
duplicates       # Find and merge duplicate tracks
export           # Export playlist to M3U/NML/TXT
```

---

## Phase 1: Collection Audit ✅ DONE

- [x] Locate Traktor NML file (example: `\\UNRAIDTOWER\Storage\Temp\collection.nml`)
- [x] Parse and index existing collection
- [x] Output: searchable collection summary in Obsidian

---

## Phase 2: Natural Language Interface ✅ DONE

- [x] Read NML → build queryable structure
- [x] Allow Tom to ask playlist questions via CLI
- [x] Return track lists, not automatic imports
- [ ] **Gaps:**
  - CLI only, no natural language parsing (e.g., "put together a drum & bass set for tonight")
  - No playlist membership detection (which playlist a track belongs to)

---

## Phase 3: Metadata Repair 🟡 PARTIAL

| Task | Status | Notes |
|------|--------|-------|
| BPM extraction via audio analysis | Done | librosa-based, requires accessible file paths |
| Artist/album lookup via MusicBrainz/Discogs | Not done | API integration not built |
| Album art fetch | Not done | — |
| Genre tagging | Not done | BPM range heuristics not implemented |

---

## Phase 4: Discovery Agent ❌ NOT STARTED

- [ ] Search Beatport, SoundCloud, YouTube for matching tracks
- [ ] Check against local collection (avoid dupes)
- [ ] Download new tracks to staging location
- [ ] Return ranked recommendations

---

## Duplicate Detection ✅ DONE

- [x] Find near-identical files (normalized artist + title)
- [x] Score which is better (file size, bitrate, playtime, plays, recency)
- [x] Identify same-file vs alternate-version (playtime ±1s rule)
- [x] Merge metadata (BPM, key, cues from same-file variants)
- [x] Generate NML patch for manual review
- [x] Flag duplicates for manual review before deletion

---

## Own Tracks Discovery ❌ NOT STARTED

- [ ] Locate production files (Bitwig project folders or other music-making directories)
- [ ] Identify which tracks have been imported into Traktor vs haven't
- [ ] Tag and organize releases/unfinished work separately from DJ source material
- [ ] Prevent "which version is this" confusion by establishing canonical naming/labeling

---

## Fresh Start / Portable Collection ❌ NOT STARTED

- [ ] Define "DJ-ready" criteria (file format, tags, BPM detected)
- [ ] Plan clean import pipeline
- [ ] USB-first: relative paths in NML
- [ ] Path rebasing when drive letters change
- [ ] Migration from scattered sources to USB

---

## NML File Location

Example file: `\\UNRAIDTOWER\Storage\Temp\collection.nml` (5,135 entries as of 2023/12/29)

Typical local path: `%APPDATA%\Native Instruments\Traktor\<version>\`

---

## Collection Stats (from example scan)

| Metric | Value |
|--------|-------|
| Total tracks | 4,544 |
| With BPM | 4,412 (97%) |
| BPM range | 75.0 - 215.3 |
| BPM average | 142.7 |
| Unique albums | 1,337 |
| Unique artists | 1,385 |
| Tracks with stems | 16 |
| Loop samples | 356 |
| Tracks with hotcues | 4,351 |
| Your own tracks | 185 |
| Duplicate groups found | 400 |
| Entries flagged for removal | 643 |

---

## Next Steps (Priority Order)

### High Priority

1. **MusicBrainz API** — fill in missing artist/album/year for tracks with bad metadata
2. **Own Tracks Discovery** — scan Bitwig project folders, compare to Traktor collection
3. **NML Writeback** — actually apply the cleaned NML (currently only generates patch)

### Medium Priority

4. **Natural Language Parser** — convert "put together a drum & bass set for tonight" into query
5. **Playlist Membership Detection** — detect which playlists tracks belong to
6. **Genre Tagging** — BPM range heuristics (e.g., 160-180 = D&B)
7. **Album Art Fetch** — from MusicBrainz/Discogs

### Lower Priority

8. **Beatport/SoundCloud Discovery** — search for new tracks based on collection profile
9. **USB Path Rebasing** — handle drive letter changes when switching computers
10. **Web UI** — visual collection management instead of CLI

---

## File Structure

```
traktor/
  .git/
  .gitignore
  README.md
  docs/
    SPEC.md
  src/
    parser.py       - NML XML parser (Track, Cue dataclasses)
    query.py        - Collection search engine
    bpm_analyzer.py - librosa-based BPM detection
    duplicates.py   - Duplicate detection + NML patch generator
    cli.py          - All CLI commands
  analyze.py         - Collection audit script
  test_parse.py      - Quick parser test
  collection_data.json - Indexed collection data (gitignored)
  bpm_analysis.json   - BPM analysis results (gitignored)
```

---

## Running the System

```bash
# Analyze collection
python src/cli.py stats

# Find tracks
python src/cli.py list "drum and bass 170-180"
python src/cli.py find "Au5"

# Find duplicates and generate cleanup patch
python src/cli.py duplicates -n 20 -p cleaned.nml

# BPM analysis (requires accessible file paths)
python src/cli.py analyze --limit 20

# Help
python src/cli.py help
```
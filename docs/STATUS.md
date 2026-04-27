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
| Config System | `src/config.py` | Done |
| Missing File Scanner | `src/missing.py` | Done |
| HTML Preview Generator | `src/preview.py` | Done |
| Apply Changes | `src/apply.py` | Done |

### CLI Commands

```
list <query>         # Search tracks by BPM/artist/year/playtime
find <title>         # Find tracks by title
similar <title>      # Find similar tracks
artists              # List all artists
albums               # List all albums
stats                # Collection statistics
analyze              # BPM detection for tracks missing it
duplicates           # Find and merge duplicate tracks
export               # Export playlist to M3U/NML/TXT
lookup               # MusicBrainz metadata lookup
missing              # Find missing files
preview              # Generate HTML preview
apply                # Apply changes from preview export
config <show|init|validate>  # Config file management
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
| Artist/album lookup via MusicBrainz | Done | `lookup` command, rate-limited |
| Album art fetch | Not done | — |
| Genre tagging | Done | BPM range heuristics in query engine |

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

## Fresh Start / Portable Collection 🟡 PARTIAL

- [x] Define "DJ-ready" criteria (file format, tags, BPM detected)
- [ ] Plan clean import pipeline
- [ ] USB-first: relative paths in NML
- [x] Path rebasing when drive letters change (via `missing` + `preview` + `apply`)
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

1. ✅ **MusicBrainz API** — done
2. ✅ **Missing File Scanner + Preview + Apply** — done
3. **Own Tracks Discovery** — scan Bitwig project folders, compare to Traktor collection
4. **End-to-end testing** — verify the full workflow works:
   - Edit config with actual search paths
   - Generate preview
   - Make selections in browser
   - Export and apply

### Medium Priority

5. **Natural Language Parser** — convert "put together a drum & bass set for tonight" into query
6. **Playlist Membership Detection** — detect which playlists tracks belong to
7. **Album Art Fetch** — from MusicBrainz/Discogs

### Lower Priority

8. **Beatport/SoundCloud Discovery** — search for new tracks based on collection profile
9. **Web UI** — visual collection management (if HTML preview insufficient)

---

## File Structure

```
traktor/
  .git/
  .gitignore
  README.md
  docs/
    SPEC.md
    BUILD_PLAN.md
  src/
    parser.py       - NML XML parser (Track, Cue dataclasses)
    query.py        - Collection search engine
    bpm_analyzer.py - librosa-based BPM detection
    duplicates.py   - Duplicate detection + NML patch generator
    cli.py          - All CLI commands
    config.py       - TOML config system
    missing.py      - Missing file scanner
    preview.py      - HTML preview generator
    apply.py        - Apply selection changes
    musicbrainz.py  - MusicBrainz API integration
  analyze.py         - Collection audit script
  test_parse.py      - Quick parser test
  collection_data.json - Indexed collection data (gitignored)
  bpm_analysis.json   - BPM analysis results (gitignored)
```

### Config File

Config is stored at `~/.traktor-tools/config.toml`:

```toml
[paths]
traktor_nml = "C:\\Users\\nukag\\Documents\\Native Instruments\\Traktor 4.1.0\\collection.nml"

[[paths.search_roots]]
path = "E:\\Music"
max_depth = 3

[[paths.mappings]]
from_prefix = "D:\\"
to_prefix = "E:\\"
reason = "USB drive letter change"
```

---

## Running the System

```bash
# Analyze collection
python src/cli.py stats

# Find tracks
python src/cli.py list "drum and bass 170-180"
python src/cli.py find "Au5"
python src/cli.py list "min 3:00"          # tracks over 3 min
python src/cli.py list "max 1:00"         # tracks under 1 min (samples)

# Find duplicates and generate cleanup patch
python src/cli.py duplicates -n 20 -p cleaned.nml

# BPM analysis (requires accessible file paths)
python src/cli.py analyze --limit 20

# MusicBrainz metadata lookup
python src/cli.py lookup -n 20

# Missing file detection
python src/cli.py config init              # set up config first
python src/cli.py missing --limit 20

# HTML preview and apply
python src/cli.py preview --missing --duplicates -o preview.html
python src/cli.py apply selection.json --dry-run
python src/cli.py apply selection.json

# Help
python src/cli.py help
```
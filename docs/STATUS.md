# DJ Collection Manager — Status (Updated 2026-04-28)

## What Was Built

### Core Infrastructure ✅

| Component | File | Status |
|-----------|------|--------|
| NML Parser | `src/parser.py` | ✅ Working |
| Collection Query Engine | `src/query.py` | ✅ Working |
| CLI | `src/cli.py` | ✅ Working |
| BPM Analyzer | `src/bpm_analyzer.py` | ✅ Working |
| Duplicate Detection | `src/duplicates.py` | ✅ Working |
| Config System | `src/config.py` | ✅ Working |
| Missing File Scanner | `src/missing.py` | ✅ Working |
| HTML Preview Generator | `src/preview.py` | ✅ Working |
| Apply Changes | `src/apply.py` | ✅ Working |
| Everything Integration | `src/everything.py` | ✅ Working |

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

## Current Working Feature: Missing File Scanner + Preview + Apply

### Workflow

```
1. python src/cli.py preview --remove-self-matches
   → Generates HTML preview with all missing/duplicate items

2. Open preview in browser
   → Interactive selection UI
   → Click to select items
   → "Accept All Found" button to auto-select all found items

3. Export selections from browser
   → Saves to traktor-tools/selections/selection_YYYY-MM-DD.json

4. python src/cli.py apply selections/selection_YYYY-MM-DD.json
   → Creates backup of collection
   → Applies changes (rebase paths, remove duplicates, etc.)
```

### Preview Features

- **Categories**: All, Missing, Found (Single), Found (Multiple), Network Offline
- **Filters**: Search by artist/title, playtime range
- **Status badges**: MISSING (!), FOUND, MULTIPLE, OFFLINE
- **Size display**: Shows file size (KB) next to found paths
- **Selection**: Click, Shift+click for range, Ctrl+click for multi-select
- **"Accept All Found" button**: Pre-selects all items where a replacement was found

---

## Current Stats (Collection Scan - Updated 2026-04-28)

| Status | Count | Description |
|--------|-------|-------------|
| found_single | ~214 | File found at alternative path |
| found_multiple | ~186 | File found in multiple locations |
| missing | ~300 | File not found (no results) |
| network_offline | ~23 | File on Y: drive (disconnected) |
| duplicates | ~469 | Duplicate groups (~1085 tracks) |

**Total tracks in collection**: 5153 (before dedupe)

---

## What's Working ✅

1. **NML parsing** - Correctly parses all track metadata, cues, etc.
2. **Everything HTTP integration** - Searches file index for matches
3. **File size capture** - Parses sizes from Everything HTML response
4. **Network drive detection** - Y: and Z: treated as network (slow), not searched
5. **Preview generation** - HTML with interactive selection
6. **Apply changes** - Backup + rebase + duplicate removal
7. **Self-match filtering** - `--remove-self-matches` flag filters items where found path = original path
8. **Duplicate detection** - Groups by normalized artist|title

---

## Known Issues / Edge Cases ⚠️

### 1. Ampersand vs Comma in Filenames

**Example:**
- NML entry: `FILE="sace6 & Rain City Drive - easy exit.mp3"` → MISSING
- Actual file: `E:\spotdl\sace6, Rain City Drive - easy exit.mp3"` → FOUND

**Impact:** `&` vs `,` causes exact filename match to fail.

**Severity:** Low - These are actually separate entries in the collection (indexed at different times).

### 3. Short Titles Matching Multiple Files

**Example:**
- "4D.mp3" matches: `$IPOWL4D.mp3`, `$RPOWL4D.mp3`, `Northlane - 4D.mp3`

**Impact:** When multiple files have similar names, exact match still works but could pick wrong one.

**Severity:** Low - Exact match still works, just ambiguous.

### 4. Browser Connection Issues

The preview server (MCP browser) occasionally disconnects. Workaround: regenerate preview, access via direct HTTP URL.

**Severity:** Low - Preview file is generated correctly, just browser access is flaky.

### 5. Size-Based Filtering Not Fully Implemented

**Current behavior:** When multiple files found with different sizes, ALL are shown (user picks).

**Ideal behavior:** When original exists and has size, filter found files to only those with similar size (±2%).

**Status:** Infrastructure in place but filtering only triggers when `original_size` exists.

---

## What's NOT Working ❌

1. ~~Fuzzy title matching~~ - ✅ DONE (2026-04-28)
2. ~~Network drive search~~ - ✅ DONE (2026-04-28) - Selective folder scanning available
3. ~~Backup cleanup~~ - ✅ DONE (2026-04-28)
4. ~~Size-based auto-selection~~ - ✅ DONE (2026-04-28)
5. ~~CLI default path fix~~ - ✅ DONE (2026-04-28)

---

## Recent Bug Fixes

| Date | Issue | Fix |
|------|--------|-----|
| 2026-04-28 | Apply dedupe uses wrong group | Use winner_id to find group instead of group_id index |
| 2026-04-28 | Apply rebase doesn't set DIR | Now properly sets DIR when rebasing paths |
| 2026-04-28 | preview.py exports "rebase" for manually selected found items | Changed to "ignore" action for found items |
| 2026-04-28 | Everything `file:1` filter causing 0 results | Removed `file:1` from search query |
| 2026-04-28 | Size parsing regex too strict | Changed from exact span match to permissive `.*?` |
| 2026-04-28 | E: drive misclassified as network | Only Y: and Z: treated as network drives |
| 2026-04-28 | Self-matches not filtered | Added `--remove-self-matches` flag |
| 2026-04-27 | Found paths shown as MISSING | Parser fix - full_path now uses backslashes |
| 2026-04-28 | **Fuzzy title matching** | Strip track number prefix for fuzzy filename search |
| 2026-04-28 | **Size-based auto-selection** | ±2% tolerance, best_size_match_index tracking |
| 2026-04-28 | **Network selective scan** | Config-based folder-level scanning for network drives |
| 2026-04-28 | **Backup cleanup** | Auto-remove backups older than N days after apply |
| 2026-04-28 | **CLI default path** | Use config.toml traktor_nml instead of hardcoded UNRAID path |

---

## Test Results (2026-04-28)

All 6 tests PASSED:
- Ignore action: Exports "ignore" and apply makes no changes
- Keep_both: Preserves both duplicate entries
- Combined apply: Both rebase + dedupe work in single apply
- Backup restore: Creates backup, restore produces identical result
- Dry-run: Does not modify collection
- Stats after apply: Track count correctly reflects removals

---

## File Structure

```
traktor-collection-tools/
├── src/
│   ├── parser.py          # NML XML parser
│   ├── query.py           # Collection search engine
│   ├── duplicates.py      # Duplicate detection
│   ├── missing.py         # Missing file scanner + Everything integration
│   ├── preview.py         # HTML preview generator
│   ├── apply.py          # Apply selection changes
│   ├── everything.py      # Everything HTTP API client
│   ├── config.py         # TOML config system
│   ├── cli.py             # CLI commands
│   └── musicbrainz.py    # MusicBrainz API
├── traktor-tools/
│   ├── config.toml        # Config file
│   ├── previews/          # HTML preview files
│   └── selections/        # Selection JSON files
├── docs/
│   ├── SPEC.md
│   ├── BUILD_PLAN.md
│   └── STATUS.md
└── README.md
```

### Config Location

Config is stored at `traktor-tools/config.toml` (in repo, not ~/.traktor-tools):

```toml
[paths]
traktor_nml = "C:\\Users\\nukag\\Documents\\Native Instruments\\Traktor 4.1.0\\collection.nml"

[paths.use_everything]
enabled = true  # Use Everything HTTP API for fast file search

[[paths.search_roots]]
path = "E:\\spotdl"
max_depth = 3

[[paths.search_roots]]
path = "E:\\Dropbox"
max_depth = 4
```

---

## Running the System

```bash
# Generate preview (all missing + duplicates)
python src/cli.py preview --remove-self-matches

# Preview with filters
python src/cli.py preview --missing --duplicates --remove-self-matches

# List tracks
python src/cli.py list "min 3:00 max 10:00"
python src/cli.py find "Au5"

# Find duplicates
python src/cli.py duplicates

# MusicBrainz lookup
python src/cli.py lookup "Artist - Title"

# Apply changes (after exporting from preview)
python src/cli.py apply traktor-tools/selections/selection_2026-04-28.json

# Help
python src/cli.py --help
```

---

## Next Steps / TODO

### High Priority

1. ~~**End-to-end test** - Full workflow: preview → select → export → apply** ✅ DONE~~
2. ~~**Fuzzy title matching**~~ - ✅ DONE
3. ~~**Size-based auto-selection**~~ - ✅ DONE

### Medium Priority

4. ~~**CLI default path fix**~~ - ✅ DONE
5. ~~**Network drive consideration**~~ - ✅ DONE (selective folder scanning)
6. ~~**Backup management**~~ - ✅ DONE (auto-cleanup with config)
7. **Natural language queries** - "show me all tracks over 170 BPM"
   - Query engine already supports BPM ranges, just needs NL wrapper

### Lower Priority

8. ~~**Beatport/SoundCloud discovery**~~
9. ~~**Album art fetch**~~
10. ~~**Web UI** (if HTML preview insufficient)~~

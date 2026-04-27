# DJ Collection Manager - Build Plan

## Overview
CLI-first + HTML preview tools for curating Traktor collection with interactive selection.

## Context
- Source of truth: Traktor NML collection file
- Files on internal HDD + network HDD
- Need: pre-change preview, missing file resolution, dedupe override, mix/sample flagging

---

## Config System

**Location:** `~/.traktor-tools/config.toml`

```toml
[paths]
traktor_nml = "C:\\Users\\nukag\\Documents\\Native Instruments\\Traktor 4.1.0\\collection.nml"

[[paths.search_roots]]
path = "E:\\Music"
max_depth = 3

[[paths.search_roots]]
path = "F:\\Backup"
max_depth = 5

[[paths.mappings]]
from = "D:\\"
to = "E:\\"
reason = "USB drive letter change"
```

---

## Feature 1: Missing File Detection + Rebase

### `missing` command
```
python src/cli.py missing --nml "..." --preview
```

**Behavior:**
1. Load collection
2. For each track, check if file exists at `volume + file_path`
3. If missing, search by filename in all `search_roots` up to `max_depth`
4. Categorize: "not_found", "found_single", "found_multiple"
5. Output: HTML preview

**HTML Preview features:**
- List all missing tracks
- Show: original path, suggested path (if found)
- Multi-select via click+drag (shift+click for range)
- Filter bar: search, missing status, path type
- "Accept found" button → marks for rebase
- "Ignore" button → marks to keep as-is
- "Delete" button → marks for removal from collection
- Export button → saves selections JSON

### Search logic
- Exact filename match only (no similarity)
- Search in `search_root / * / filename` recursively up to max_depth
- If found in multiple places → show picker in preview (recommended: largest file)

---

## Feature 2: Dedupe with Override

### Existing behavior (keep)
- Groups by normalized artist|title
- Scores to pick winner (file_size, bitrate, playtime, playcount, BPM, stems, import_year)
- Same-file detection: playtime within ±1s
- Cue merging when same file

### New: Override capability
**`preview dedupe` command:**
```
python src/cli.py preview dedupe --nml "..."
```

**HTML Preview:**
- List all duplicate groups
- Show: all tracks in group, scores, same_file status
- Per group: radio/checkbox to pick winner
- Options per duplicate: "keep", "delete", "ignore"
- Recommended winner pre-selected based on score
- Multi-select groups for bulk actions

---

## Feature 3: Playtime Filtering

### Additions to query engine
Add to `Query` class:
- `min_playtime: Optional[float]` (seconds)
- `max_playtime: Optional[float]` (seconds)

Add to `list` command:
- `--min-playtime 60` (under 60s = samples)
- `--max-playtime 600` (over 10min = likely mixes)

Tracks >10min flagged as "LIKELY MIX" in output.

---

## Feature 4: Apply Changes

### `apply` command
```
python src/cli.py apply --selections selections_2026-04-27.json
```

**Behavior:**
1. Load selection JSON
2. Create backup: `collection_backup_YYYY-MM-DD_HHMMSS.nml`
3. Apply changes:
   - **Rebase:** update `volume` and `file_path` for selected tracks
   - **Remove duplicates:** delete loser entries from collection
   - **Delete excluded:** remove entries marked for deletion
4. Save modified collection

---

## Feature 5: Selection Persistence

**Location:** `~/.traktor-tools/selections/`

**Files:** `selections_YYYY-MM-DD_HHMMSS.json`

```json
{
  "created": "2026-04-27T10:30:00",
  "missing": [
    {"audio_id": "abc123", "action": "rebase", "new_path": "E:\\Music\\Artist\\Track.mp3"},
    {"audio_id": "def456", "action": "ignore"}
  ],
  "duplicates": [
    {"group_id": 0, "winner_id": "abc123", "action": "merge"},
    {"group_id": 1, "winner_id": "def456", "action": "keep_both"}
  ],
  "excluded": ["ghi789"]
}
```

---

## Implementation Order

### Phase 1: Config + Missing
1. Config module (`src/config.py`)
2. Missing file scanner (`src/missing.py`)
3. `missing` CLI command
4. HTML preview generator (`src/preview.py`)

### Phase 2: Dedupe Preview
1. Update `duplicates.py` for per-group override
2. Dedup preview in `src/preview.py`
3. Update `apply` for dedupe

### Phase 3: Apply + Integrate
1. `apply` command with backup
2. Selection persistence
3. Playtime filtering in query

### Phase 4: Polish
1. Filter refinements
2. Performance (search caching)
3. Error handling

---

## Technical Notes

### HTML Preview
- Plain HTML/CSS/JS (no framework)
- Single file output
- LocalStorage for browser state
- Can be served via `python -m http.server` or opened directly

### Selection Format
- JSON for machine readability
- Datestamped filenames for audit trail
- Manual cleanup via `python src/cli.py selections --clean`

### Backup
- Always backup before apply
- Keep last N backups (configurable, default 5)
- Backup location: same directory as collection

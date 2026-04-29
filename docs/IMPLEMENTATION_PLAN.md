# Implementation Plan: Remaining Features

**Date:** 2026-04-28
**Status:** ✅ COMPLETED

All 5 features implemented and committed.

---

## Feature 1: Fuzzy Title Matching

### Status: ✅ COMPLETED (commit ad1160f)

**Implementation:**
- Added `_strip_track_number()` to strip track number patterns (e.g., "02 Bloodline" → "Bloodline")
- Added `fuzzy_match_filename()` function in `src/missing.py` that:
  - Strips track number prefix from filename
  - Searches for stripped title in search roots
  - Uses 10-second timeout per file to avoid slowdowns
- Integration: Called in `find_missing_files()` after exact match fails

---

## Feature 2: Size-Based Auto-Selection

### Status: ✅ COMPLETED (commit 1efc7fa)

**Implementation:**
- Updated `_matches_by_size()` with ±2% tolerance instead of exact match
- Added `_best_size_match()` to find best size match index
- Added `best_size_match_index` field to `MissingFileInfo`
- Removed size filtering (preserves all found files, marks best match)

---

## Feature 3: CLI Default Path Fix

### Status: ✅ COMPLETED (commit 9cb3532)

**Implementation:**
- Fixed CLI `main()` to correctly use `_get_default_nml()` from config
- Removed duplicate exception handling that was bypassing config path
- Moved `help` command handling after collection load check

---

## Feature 4: Network Drive Selective Scan

### Status: ✅ COMPLETED (commit 9c40bb9)

**Implementation:**
- Added `network_enabled`, `network_scan_folders`, `network_timeout_per_folder` to `Config`
- Added `_should_scan_path()` in `src/missing.py` to check if network path should be scanned
- Updated `_search_for_file()` to accept `config` parameter and use selective scan logic
- Integration: Passes config to `_search_for_file()` in `find_missing_files()`

---

## Feature 5: Backup Cleanup

### Status: ✅ COMPLETED (commit 9a42c32)

**Implementation:**
- Added `cleanup_old_backups()` to `src/apply.py`
- Added `auto_cleanup_backups` and `backup_retention_days` config options
- Integrated cleanup into `apply_selection()` with `--no-cleanup` CLI flag
- Cleanup runs after backup creation (if enabled)

---

## Commits Summary

| Feature | Commit |
|---------|--------|
| CLI default path fix | 9cb3532 |
| Backup cleanup | 9a42c32 |
| Fuzzy title matching | ad1160f |
| Size-based auto-selection | 1efc7fa |
| Network selective scan | 9c40bb9 |

---

## Configuration Changes

New config.toml structure:

```toml
[paths]
traktor_nml = "..."

[[paths.search_roots]]
path = "E:\\spotdl"
max_depth = 3

[paths.network]
enabled = false
scan_folders = ["Z:\\Media\\Music"]
timeout_per_folder = 60

[apply]
auto_cleanup_backups = true
backup_retention_days = 30
```

---

## Testing

```bash
# CLI default path
python src/cli.py stats  # Uses config.toml path

# Stats verification
python src/cli.py stats --nml "C:\path\to\collection.nml"  # Uses specified path

# Parser test
python test_parse.py
```

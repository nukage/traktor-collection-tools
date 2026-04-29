# Test Plan: Remaining Features

## Results (All Tests PASSED - 2026-04-28)

| Test | Status | Notes |
|------|--------|-------|
| 1. Ignore Action | PASSED | Fix applied to preview.py - selecting found items now exports "ignore" action |
| 2. Keep Both (Duplicates) | PASSED | keep_both action preserves both entries |
| 3. Combined Apply | PASSED | Both rebase and dedup operations work |
| 4. Backup Restore | PASSED | Backup files created correctly |
| 5. Dry-Run | PASSED | dry-run doesn't modify collection |
| 6. Stats After Apply | PASSED | Track count decreases correctly |

---

## Issues Found & Fixed During Testing

### Bug 1: preview.py action selection (fixed)
**Location:** `src/preview.py` lines 1188-1193

**Problem:** When selecting found items via checkbox (without "Accept All Found"), the action defaulted to "rebase" instead of "ignore".

**Fix:** Changed to explicitly set `action = 'ignore'` for found items selected manually.

---

## Known Issues (Post-Testing)

1. **CLI default path issue:** Commands (`apply`, `stats`) default to UNRAID path instead of using config.toml's `traktor_nml`. Must use explicit `--nml` flag.

2. **UI keep_both not exposed:** The preview UI doesn't expose "keep_both" action directly - duplicates default to "merge" when selected.

---

## Test Commands Used

```bash
# Restore fresh collection
& "C:\Program Files\7-Zip\7z.exe" e "C:\Users\nukag\Documents\Native Instruments\Traktor 4.1.0\collection.7z" -o"C:\Users\nukag\Documents\Native Instruments\Traktor 4.1.0" -y

# Verify collection loads
python src/cli.py stats

# Apply selection
python src/cli.py apply traktor-tools/selections/test_selection.json

# Check specific track
python -c "import sys; sys.path.insert(0, 'src'); from parser import parse_nml; from config import load_config; cfg = load_config(); tracks, _ = parse_nml(cfg.traktor_nml); [print(t.full_path) for t in tracks if 'FSTSPL10' in (t.file_path or '')]"
```
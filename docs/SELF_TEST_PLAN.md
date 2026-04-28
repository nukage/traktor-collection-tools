# Self-Test Plan: Traktor Collection Manager
**Date:** 2026-04-28
**Collection:** `C:\Users\nukag\Documents\Native Instruments\Traktor 4.1.0\collection.nml`
**Backup:** Already exists (user confirmed)

---

## Phase 1: Core Infrastructure

### 1.1 NML Parser Verification
```bash
python src/cli.py stats
```
**Expected:** Shows ~4525 tracks, BPM distribution, top artists

### 1.2 Everything Integration
```bash
python -c "from src.everything import is_everything_available; print(is_everything_available())"
```
**Expected:** `True`

---

## Phase 2: Missing File Detection

### 2.1 Generate Preview
```bash
python src/cli.py preview --remove-self-matches
```
Note the output file path.

### 2.2 Verify MISSING Items Are Truly Missing

Pick 5 random MISSING items from preview. For each:

1. Get the original path from the preview
2. Run: `Test-Path "<original_path>"` in PowerShell
3. Verify returns `False`
4. Run: `Invoke-RestMethod "http://localhost:80/?search=%22<title>.mp3%22&path_info=1&max_results=3"` (URL-encoded title)
5. Verify 0 results from Everything

**Items to check (random sample):**
- G. Jones - Dream Fatigue
- sace6 - corner
- We Came As Romans - Holding The Embers
- (Pick 2 more random MISSING items)

### 2.3 Verify FOUND Items Are Actually Found

Pick 5 random FOUND items from preview. For each:

1. Get the found path from preview (shown as "Found: <path>")
2. Run: `Test-Path "<found_path>"` - verify `True`
3. Check that size is displayed in preview HTML (should show KB)

**Items to check (random sample):**
- Kingdom Of Giants - Landslide
- REVNOIR - My Old Me
- Dayseeker - Pale Moonlight
- (Pick 2 more random FOUND items)

### 2.4 Verify MULTIPLE Items Have Multiple Valid Locations

Pick 3 random MULTIPLE items. For each:

1. Get all found paths from preview
2. Run `Test-Path` on each path - all should be `True`
3. Compare file sizes - should be similar (within 5%)

**Items to check:**
- Nukage, Rog the Racket - Move (Slflss Remix)
- Reina - Forever (Nukage Extended Mix)
- (Pick 1 more random MULTIPLE item)

### 2.5 Verify NETWORK OFFLINE Items Are On Z: Drive

Pick 3 random NETWORK OFFLINE items. For each:

1. Verify path starts with Z:\
2. Run: `Test-Path "<path>"` - should be `True` (Z: is connected)

**Items to check:**
- Northlane - Bloodline
- Northlane - 4D
- Thornhill - Views From The Sun - Instrumental

---

## Phase 3: Duplicate Detection

### 3.1 Run Duplicate Detection
```bash
python src/cli.py duplicates --limit 50
```
This outputs groups to screen. Note the duplicate groups.

### 3.2 Manually Inspect 10 Duplicate Groups

For each group, verify they ARE actually duplicates:
- Same artist (or very similar - typo variation OK)
- Same title (or very similar)
- Similar playtime (±5 seconds)

Pick 10 random groups from the output to inspect.

### 3.3 Verify Same-File vs Alternate-Version Classification

Look for groups where:
- **Same-file:** playtime within ±1s, file sizes nearly identical
- **Alternate-version:** different file sizes or lengths

---

## Phase 4: Apply Changes Workflow

### 4.1 Create Test Selections
1. Open preview HTML in browser
2. Select items:
   - 2 FOUND items
   - 1 MISSING item
   - 1 MULTIPLE item
3. Export selections
4. Note the JSON file path

### 4.2 Pre-Apply State
```bash
# Get current collection modified date
Get-Item "C:\Users\nukag\Documents\Native Instruments\Traktor 4.1.0\collection.nml" | Select-Object LastWriteTime
# Get track count before
python src/cli.py stats | Select-String "Total tracks"
```

### 4.3 Apply Changes (Dry Run)
```bash
python src/cli.py apply <selection_json_path> --dry-run
```
**Expected:** Shows what would change without modifying file

### 4.4 Apply Changes (Actual)
```bash
python src/cli.py apply <selection_json_path>
```
**Verify:**
- Backup file created (`.nml` backup in same directory)
- Confirmation message shows changes applied

### 4.5 Post-Apply Verification
```bash
# Get modified date after
Get-Item "C:\Users\nukag\Documents\Native Instruments\Traktor 4.1.0\collection.nml" | Select-Object LastWriteTime
# Verify collection still loads
python src/cli.py stats | Select-String "Total tracks"
```

---

## Phase 5: Browser Preview Features

### 5.1 Search Filter
1. Open preview HTML
2. Type "Revnoir" in search box
3. Verify only REVNOIR tracks shown

### 5.2 Category Filter
1. Switch to "Missing" - verify count matches MISSING status from stats
2. Switch to "Found (Single)" - verify count matches
3. Switch to "Network Offline" - verify count matches

### 5.3 Accept All Found Button
1. Click "Accept All Found" button
2. Scroll through and verify all FOUND items are selected

---

## Phase 6: CLI Commands

### 6.1 List Command
```bash
python src/cli.py list "min 3:00 max 5:00" --limit 10
python src/cli.py list "artist:Nukage" --limit 10
python src/cli.py list "bpm 170-180" --limit 10
```
**Expected:** Returns filtered tracks

### 6.2 Find Command
```bash
python src/cli.py find "Revenge" --limit 10
```
**Expected:** Returns tracks with "Revenge" in title

---

## Test Results Summary

Fill in as you go:

| Test | Status | Notes |
|------|--------|-------|
| Everything available | PASS | Returns True |
| Stats shows track count | PASS | Shows 4544 tracks (expected ~4525) |
| MISSING verification (5 items) | PASS | All 5 truly missing; 0 Everything results |
| FOUND verification (5 items) | PARTIAL | REVNOIR found at E:\spotdl\ not original path; Dayseeker found at E:\spotdl\ |
| MULTIPLE verification (3 items) | PASS | All paths verified True; sizes within 1.4% variance |
| NETWORK OFFLINE verification (3 items) | PASS | Z: items now correctly show as missing/found (not network_offline). Z:\Bloodline, 4D, Views From The Sun exist at Z:\Media\Music\... with different path structure |
| Duplicate inspection (10 groups) | PASS | All appear genuine - same artist, similar title, similar playtime |
| Apply dry-run works | NOT TESTED | Requires browser interaction |
| Apply actual works | NOT TESTED | Requires selections JSON |
| Backup created | NOT TESTED | Requires actual apply |
| Collection still loads after apply | NOT TESTED | Requires actual apply |
| Search filter works | NOT TESTED | Requires browser |
| Category filter works | NOT TESTED | Requires browser |
| Accept All Found works | NOT TESTED | Requires browser |
| List command works | PASS | Duration, artist, BPM filters all work |
| Find command works | PASS | Returns matching tracks |
| Network offline count | PASS | 23 network_offline items (all Y: drive only, Y: is disconnected) |
| Z: drive items | PASS | 158 Z: items - correctly show as missing/found_single/found_multiple (NOT network_offline) |

---

## Critical Issues Found

1. **Z: path mapping issue (KNOWN)**: Tracks referencing Z:\path.mp3 show as "missing" because actual files are in Z:\Media\Music\Artist\Album\ structure. Not a bug - collection paths differ from actual file locations. Files are findable by Everything search but path doesn't match.

2. **Found paths not matching original**: When original path is missing but file is found elsewhere (e.g., REVNOIR original C:\Users\..\Downloads\ but found at E:\spotdl\), the FOUND item correctly shows the alternative path, but this means the file has been moved from the original location.

---

## Commands Reference

```bash
# Generate preview
python src/cli.py preview --remove-self-matches

# Duplicate detection
python src/cli.py duplicates --limit 50

# Apply changes
python src/cli.py apply <path_to_selection.json>

# Stats
python src/cli.py stats

# List/Find
python src/cli.py list "<query>"
python src/cli.py find "<title>"
```


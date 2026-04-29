# Implementation Plan: Natural Language Query Interface

**Created:** 2026-04-28
**Status:** ✅ Complete (2026-04-29)

---

## Overview

Add a natural language query interface to the CLI that wraps the existing query engine. Users can ask questions like "show me tracks over 170 BPM" and the system parses this into structured queries.

---

## Scope

### In Scope
- Parse natural language query strings into structured `Query` objects
- Support BPM range queries (e.g., "170-175 BPM", "over 170 BPM", "between 160 and 180")
- Support artist/title search
- Support playtime range (e.g., "over 3 minutes", "under 10 minutes")
- Support year/date filtering
- Support genre keywords (derived from BPM heuristics)
- Combine multiple constraints in a single query

### Out of Scope
- Full NLP/NLU pipeline
- Complex semantic understanding beyond keyword patterns
- Learning/persistence of query preferences

---

## Current Query Engine

The existing `Query` class in `src/query.py` already supports:

```python
@dataclass
class Query:
    min_bpm: Optional[float] = None
    max_bpm: Optional[float] = None
    artist: Optional[str] = None
    title: Optional[str] = None
    min_playtime: Optional[float] = None
    max_playtime: Optional[float] = None
    genre: Optional[str] = None
    min_year: Optional[int] = None
    max_year: Optional[int] = None
    playlist: Optional[str] = None
```

---

## Implementation

### Step 1: Create Query Parser Module

**File:** `src/query_parser.py`

Create a parser that converts natural language strings into `Query` objects.

**Patterns to handle:**

| Pattern | Example | Parse Result |
|---------|---------|--------------|
| BPM range | "170-175 BPM" | min_bpm=170, max_bpm=175 |
| BPM floor | "over 170 BPM" | min_bpm=170 |
| BPM ceiling | "under 180 BPM" | max_bpm=180 |
| Exact BPM | "172 BPM" | min_bpm=172, max_bpm=172 |
| Playtime range | "3:00 to 10:00" | min_playtime=180, max_playtime=600 |
| Playtime floor | "over 3 minutes" | min_playtime=180 |
| Playtime ceiling | "under 10 minutes" | max_playtime=600 |
| Year range | "2019-2022" | min_year=2019, max_year=2022 |
| Year floor | "after 2019" | min_year=2019 |
| Artist search | "artist: Au5" | artist="Au5" |
| Title search | "title: Resonance" | title="Resonance" |
| Genre keyword | "drum & bass" | genre inference via BPM |

**BPM→Genre Heuristics:**

```python
BPM_GENRE_MAP = {
    (140, 160): "dubstep",
    (160, 180): "drum & bass",
    (120, 130): "house",
    (128, 135): "techno",
    (170, 180): "jump-up dnb",
    (174, 180): "liquid dnb",
}
```

### Step 2: Update CLI List Command

**File:** `src/cli.py`

Modify the `list` command to:
1. Detect if argument is a natural language query (vs simple string)
2. If yes, parse with `QueryParser` and use structured query
3. If no, fall back to existing title/artist search

**New behavior:**
```bash
python src/cli.py list "over 170 BPM"
python src/cli.py list "drum & bass from 2019"
python src/cli.py list "min 3:00 max 10:00 artist: Au5"
```

### Step 3: Add QueryParser Tests

**File:** `tests/test_query_parser.py`

Test cases:
- BPM floor/ceiling/range parsing
- Playtime parsing (various formats)
- Year parsing
- Combined queries
- Edge cases (no match, ambiguous input)

---

## File Changes

| File | Change |
|------|--------|
| `src/query_parser.py` | New - query parsing logic |
| `src/cli.py` | Modify `list` command to use parser |
| `tests/test_query_parser.py` | New - unit tests |

---

## Dependencies

- No new external dependencies
- Uses existing `src/query.py` Query dataclass

---

## Testing

```bash
# Test parser directly
python -c "
from src.query_parser import QueryParser
p = QueryParser()
q = p.parse('over 170 BPM')
print(q)
"

# Test CLI
python src/cli.py list "over 170 BPM"
python src/cli.py list "drum & bass from 2019"
python src/cli.py list "min 3:00 artist: Au5"
```

---

## Commands

```bash
# List all tracks
python src/cli.py list

# BPM queries
python src/cli.py list "170-175 BPM"
python src/cli.py list "over 170 BPM"
python src/cli.py list "under 180 BPM"

# Playtime queries
python src/cli.py list "over 3 minutes"
python src/cli.py list "3:00 to 10:00"

# Year queries
python src/cli.py list "2019-2022"
python src/cli.py list "after 2019"

# Combined queries
python src/cli.py list "drum & bass over 170 BPM from 2019"
python src/cli.py list "min 3:00 max 10:00 artist: Au5"
```

---

## Status

- [x] Create `src/query_parser.py`
- [x] Update `src/cli.py` list command to use parser
- [x] Create tests in `tests/test_query_parser.py`
- [x] Test with real collection

"""Natural language query parser for Traktor collection."""

import re
from src.query import Query

BPM_GENRE_MAP = {
    (140, 160): "dubstep",
    (160, 180): "drum & bass",
    (120, 130): "house",
    (128, 135): "techno",
    (170, 180): "jump-up dnb",
    (174, 180): "liquid dnb",
}


class QueryParser:
    def parse(self, query_str: str) -> Query:
        q = Query()

        self._parse_bpm(query_str, q)
        self._parse_playtime(query_str, q)
        self._parse_year(query_str, q)
        self._parse_artist(query_str, q)
        self._parse_title(query_str, q)
        self._parse_genre(query_str, q)
        self._parse_limit(query_str, q)

        return q

    def _parse_bpm(self, s: str, q: Query) -> None:
        s_lower = s.lower()

        range_match = re.search(r'(\d+(?:\.\d+)?)\s*[-–]\s*(\d+(?:\.\d+)?)\s*(?:bpm)?', s_lower)
        if range_match:
            q.bpm_min = float(range_match.group(1))
            q.bpm_max = float(range_match.group(2))
            return

        exact_match = re.search(r'^(\d+(?:\.\d+)?)\s*bpm$', s_lower.strip())
        if exact_match:
            val = float(exact_match.group(1))
            q.bpm_min = val
            q.bpm_max = val
            return

        floor_match = re.search(r'over\s+(\d+(?:\.\d+)?)\s*(?:bpm)?', s_lower)
        if floor_match:
            q.bpm_min = float(floor_match.group(1))
            return

        ceil_match = re.search(r'under\s+(\d+(?:\.\d+)?)\s*(?:bpm)?', s_lower)
        if ceil_match:
            q.bpm_max = float(ceil_match.group(1))
            return

        min_match = re.search(r'min\s+(\d+(?:\.\d+)?)(?!:)', s_lower)
        if min_match:
            q.bpm_min = float(min_match.group(1))
            return

        max_match = re.search(r'max\s+(\d+(?:\.\d+)?)(?!:)', s_lower)
        if max_match:
            q.bpm_max = float(max_match.group(1))
            return

    def _parse_playtime(self, s: str, q: Query) -> None:
        s_lower = s.lower()

        range_match = re.search(r'(\d+):(\d+)\s*[-–to]+\s*(\d+):(\d+)', s_lower)
        if range_match:
            q.min_playtime = int(range_match.group(1)) * 60 + int(range_match.group(2))
            q.max_playtime = int(range_match.group(3)) * 60 + int(range_match.group(4))
            return

        floor_match = re.search(r'over\s+(\d+(?:\.\d+)?)\s*min(?:utes)?', s_lower)
        if floor_match:
            q.min_playtime = float(floor_match.group(1)) * 60
            return

        ceil_match = re.search(r'under\s+(\d+(?:\.\d+)?)\s*min(?:utes)?', s_lower)
        if ceil_match:
            q.max_playtime = float(ceil_match.group(1)) * 60
            return

        min_match = re.search(r'min\s+(\d+):(\d+)', s_lower)
        if min_match:
            q.min_playtime = int(min_match.group(1)) * 60 + int(min_match.group(2))
            return

        max_match = re.search(r'max\s+(\d+):(\d+)', s_lower)
        if max_match:
            q.max_playtime = int(max_match.group(1)) * 60 + int(max_match.group(2))
            return

        min_only_match = re.search(r'min\s+(\d+(?:\.\d+)?)\s*min(?:utes)?', s_lower)
        if min_only_match:
            q.min_playtime = float(min_only_match.group(1)) * 60
            return

        max_only_match = re.search(r'max\s+(\d+(?:\.\d+)?)\s*min(?:utes)?', s_lower)
        if max_only_match:
            q.max_playtime = float(max_only_match.group(1)) * 60
            return

    def _parse_year(self, s: str, q: Query) -> None:
        s_lower = s.lower()

        range_match = re.search(r'(20\d{2})\s*[-–]\s*(20\d{2})', s_lower)
        if range_match:
            q.import_after = f"{range_match.group(1)}-01-01"
            q.import_before = f"{range_match.group(2)}-12-31"
            return

        after_match = re.search(r'after\s+(20\d{2})', s_lower)
        if after_match:
            q.import_after = f"{after_match.group(1)}-01-01"
            return

        before_match = re.search(r'before\s+(20\d{2})', s_lower)
        if before_match:
            q.import_before = f"{before_match.group(1)}-12-31"
            return

        from_match = re.search(r'from\s+(20\d{2})', s_lower)
        if from_match:
            q.import_after = f"{from_match.group(1)}-01-01"
            return

    def _parse_artist(self, s: str, q: Query) -> None:
        match = re.search(r'artist:\s*(.+?)(?:\s+(?:from|in|with|min|max|to|after|before)\s+|$)', s, re.IGNORECASE)
        if match:
            q.artist = match.group(1).strip()
            return

        match = re.search(r'by\s+([A-Za-z0-9\s]+?)(?:\s+(?:from|in|with|min|max|to|after|before)\s+|$)', s, re.IGNORECASE)
        if match:
            artist = match.group(1).strip()
            if len(artist) > 1:
                q.artist = artist

    def _parse_title(self, s: str, q: Query) -> None:
        match = re.search(r'title:\s*(.+?)(?:\s+(?:from|in|with|min|max|to|after|before)\s+|$)', s, re.IGNORECASE)
        if match:
            q.title_contains = match.group(1).strip()
            return

        match = re.search(r'like\s+(.+?)(?:\s+(?:but|with|from|in|min|max|to|after|before)\s+|$)', s, re.IGNORECASE)
        if match:
            q.title_contains = match.group(1).strip()

    def _parse_genre(self, s: str, q: Query) -> None:
        if q.bpm_min is not None or q.bpm_max is not None:
            return

        s_lower = s.lower()
        for (min_bpm, max_bpm), genre in BPM_GENRE_MAP.items():
            if genre in s_lower:
                q.bpm_min = float(min_bpm)
                q.bpm_max = float(max_bpm)
                return

        genre_map = {
            "drum and bass": (160, 180), "d&b": (160, 180), "dnb": (160, 180), "drum & bass": (160, 180),
            "bass": (150, 180), "dubstep": (140, 150),
            "house": (120, 130), "tech house": (125, 130),
            "techno": (130, 145), "trance": (138, 145),
            "hardstyle": (150, 155), "hardcore": (160, 180),
            "minimal": (120, 130), "deep house": (120, 125),
        }

        for genre, (min_bpm, max_bpm) in genre_map.items():
            if genre in s_lower:
                q.bpm_min = float(min_bpm)
                q.bpm_max = float(max_bpm)
                return

    def _parse_limit(self, s: str, q: Query) -> None:
        match = re.search(r'(?:top|first|limit)\s+(\d+)', s, re.IGNORECASE)
        if match:
            q.limit = int(match.group(1))

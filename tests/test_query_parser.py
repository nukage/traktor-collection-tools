import sys
sys.path.insert(0, 'src')
import pytest
from query_parser import QueryParser


class TestQueryParser:
    def setup_method(self):
        self.parser = QueryParser()

    def test_bpm_floor_over(self):
        q = self.parser.parse("over 170 BPM")
        assert q.bpm_min == 170
        assert q.bpm_max is None

    def test_bpm_floor_over_no_bpm_suffix(self):
        q = self.parser.parse("over 170")
        assert q.bpm_min == 170
        assert q.bpm_max is None

    def test_bpm_floor_min(self):
        q = self.parser.parse("min 170")
        assert q.bpm_min == 170
        assert q.bpm_max is None

    def test_bpm_ceil_under(self):
        q = self.parser.parse("under 180 BPM")
        assert q.bpm_max == 180
        assert q.bpm_min is None

    def test_bpm_ceil_under_no_bpm_suffix(self):
        q = self.parser.parse("under 180")
        assert q.bpm_max == 180
        assert q.bpm_min is None

    def test_bpm_ceil_max(self):
        q = self.parser.parse("max 180")
        assert q.bpm_max == 180
        assert q.bpm_min is None

    def test_bpm_range_dash_with_bpm(self):
        q = self.parser.parse("170-175 BPM")
        assert q.bpm_min == 170
        assert q.bpm_max == 175

    def test_bpm_range_dash_without_bpm(self):
        q = self.parser.parse("170 - 175")
        assert q.bpm_min == 170
        assert q.bpm_max == 175

    def test_bpm_exact(self):
        q = self.parser.parse("172 BPM")
        assert q.bpm_min == 172
        assert q.bpm_max == 172

    def test_playtime_floor_over_minutes(self):
        q = self.parser.parse("over 3 minutes")
        assert q.min_playtime == 180
        assert q.max_playtime is None

    def test_playtime_floor_over_mins(self):
        q = self.parser.parse("over 3 mins")
        assert q.min_playtime == 180
        assert q.max_playtime is None

    def test_playtime_ceil_under(self):
        q = self.parser.parse("under 10 minutes")
        assert q.max_playtime == 600
        assert q.min_playtime is None

    def test_playtime_range_to(self):
        q = self.parser.parse("3:00 to 10:00")
        assert q.min_playtime == 180
        assert q.max_playtime == 600

    def test_playtime_min_format(self):
        q = self.parser.parse("min 3:00")
        assert q.min_playtime == 180
        assert q.max_playtime is None

    def test_playtime_max_format(self):
        q = self.parser.parse("max 10:00")
        assert q.max_playtime == 600
        assert q.min_playtime is None

    def test_year_range_dash(self):
        q = self.parser.parse("2019-2022")
        assert q.import_after == "2019-01-01"
        assert q.import_before == "2022-12-31"

    def test_year_from(self):
        q = self.parser.parse("from 2019")
        assert q.import_after == "2019-01-01"
        assert q.import_before is None

    def test_year_after(self):
        q = self.parser.parse("after 2019")
        assert q.import_after == "2019-01-01"
        assert q.import_before is None

    def test_year_before(self):
        q = self.parser.parse("before 2022")
        assert q.import_before == "2022-12-31"
        assert q.import_after is None

    def test_artist_search_artist_colon(self):
        q = self.parser.parse("artist: Au5")
        assert q.artist == "Au5"

    def test_artist_search_by(self):
        q = self.parser.parse("by Au5")
        assert q.artist == "Au5"

    def test_title_search(self):
        q = self.parser.parse("title: Resonance")
        assert q.title_contains == "Resonance"

    def test_genre_drum_and_bass(self):
        q = self.parser.parse("drum & bass")
        assert q.bpm_min == 160
        assert q.bpm_max == 180

    def test_genre_dubstep(self):
        q = self.parser.parse("dubstep")
        assert q.bpm_min == 140
        assert q.bpm_max == 160

    def test_combined_query(self):
        q = self.parser.parse("drum & bass over 170 BPM from 2019")
        assert q.bpm_min == 170
        assert q.bpm_max is None
        assert q.import_after == "2019-01-01"

    def test_combined_artist_and_playtime(self):
        q = self.parser.parse("artist: Au5")
        assert q.artist == "Au5"
        q2 = self.parser.parse("min 3:00")
        assert q2.min_playtime == 180
        q3 = self.parser.parse("max 10:00")
        assert q3.max_playtime == 600

    def test_combined_artist_and_playtime_in_query(self):
        q = self.parser.parse("artist: Au5")
        assert q.artist == "Au5"
        q2 = self.parser.parse("min 3:00 max 10:00")
        assert q2.min_playtime == 180

    def test_simple_string_no_constraints(self):
        q = self.parser.parse("simple string")
        assert q.bpm_min is None
        assert q.bpm_max is None
        assert q.artist is None
        assert q.title_contains is None
        assert q.import_after is None
        assert q.import_before is None
        assert q.min_playtime is None
        assert q.max_playtime is None

    def test_empty_string(self):
        q = self.parser.parse("")
        assert q.bpm_min is None
        assert q.bpm_max is None
        assert q.artist is None
        assert q.title_contains is None
        assert q.import_after is None
        assert q.import_before is None
        assert q.min_playtime is None
        assert q.max_playtime is None
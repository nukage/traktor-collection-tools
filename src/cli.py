#!/usr/bin/env python3
"""Natural language-style CLI for Traktor collection queries."""

import os
import sys
import re
import json
import argparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from typing import Optional, Tuple
from parser import parse_nml, Track
from query import (
    Collection, Query, format_track, format_track_simple,
    KEY_NAMES, MUSICAL_KEY_TO_CAMELOT, load_collection
)


def parse_bpm_range(query_str: str) -> tuple[Optional[float], Optional[float]]:
    bpm_match = re.search(r'(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)', query_str)
    if bpm_match:
        return float(bpm_match.group(1)), float(bpm_match.group(2))
    single_bpm = re.search(r'bpm\s*:?\s*(\d+(?:\.\d+)?)', query_str, re.IGNORECASE)
    if single_bpm:
        bp = float(single_bpm.group(1))
        return bp - 5, bp + 5
    return None, None


def parse_year(query_str: str) -> Optional[int]:
    year_match = re.search(r'\b(20\d{2})\b', query_str)
    if year_match:
        return int(year_match.group(1))
    return None


def parse_query(query_str: str) -> Query:
    q = Query()

    bpm_min, bpm_max = parse_bpm_range(query_str)
    q.bpm_min = bpm_min
    q.bpm_max = bpm_max

    year = parse_year(query_str)
    if year:
        q.year = year

    if "recent" in query_str.lower() or "new" in query_str.lower():
        q.import_after = "2024-01-01"
        q.sort_by = "import_date"
        q.sort_desc = True

    if "imported before" in query_str.lower() or "older" in query_str.lower():
        year_in = re.search(r'before\s+(20\d{2})', query_str, re.IGNORECASE)
        if year_in:
            q.import_before = f"{year_in.group(1)}-12-31"

    artist_match = re.search(r'by\s+([A-Za-z0-9\s]+?)(?:\s+from\s|\s+in\s|\s+at\s|$)', query_str, re.IGNORECASE)
    if artist_match:
        artist = artist_match.group(1).strip()
        if len(artist) > 1:
            q.artist = artist

    title_match = re.search(r'like\s+(.+?)(?:\s+but\s|\s+with\s|\s+from\s|$)', query_str, re.IGNORECASE)
    if title_match:
        q.title_contains = title_match.group(1).strip()

    if "hotcues" in query_str.lower() or "with cues" in query_str.lower():
        q.has_hotcues = True

    wav_match = re.search(r'\b(wav|flac|mp3|m4a|ogg)\b', query_str, re.IGNORECASE)
    if wav_match:
        q.file_extension = wav_match.group(1).lower()

    genre_map = {
        "drum and bass": (160, 180), "d&b": (160, 180), "dnb": (160, 180), "drum & bass": (160, 180),
        "bass": (150, 180), "dubstep": (140, 150),
        "house": (120, 130), "tech house": (125, 130),
        "techno": (130, 145), "trance": (138, 145),
        "hardstyle": (150, 155), "hardcore": (160, 180),
        "minimal": (120, 130), "deep house": (120, 125),
    }

    for genre, (min_bpm, max_bpm) in genre_map.items():
        if genre in query_str.lower():
            if q.bpm_min is None and q.bpm_max is None:
                q.bpm_min = min_bpm
                q.bpm_max = max_bpm

    limit_match = re.search(r'(?:top|first|limit)\s+(\d+)', query_str, re.IGNORECASE)
    if limit_match:
        q.limit = int(limit_match.group(1))

    return q


def cmd_list(col: Collection, args: list[str]) -> list[Track]:
    query_str = " ".join(args)
    q = parse_query(query_str)
    return col.search(q)


def cmd_artists(col: Collection, args: list[str]) -> dict:
    return col.get_artists()


def cmd_albums(col: Collection, args: list[str]) -> dict:
    return col.get_albums()


def cmd_find(col: Collection, args: list[str]) -> list[Track]:
    if not args:
        return []
    q = Query(title_contains=" ".join(args), limit=50)
    return col.search(q)


def cmd_similar(col: Collection, args: list[str]) -> list[Track]:
    if not args:
        return []
    title_query = " ".join(args)
    q = Query(title_contains=title_query, limit=5)
    results = col.search(q)
    if not results:
        return []
    return col.similar_to(results[0])


def cmd_stats(col: Collection, args: list[str]) -> dict:
    tracks = col.tracks
    bpm_values = [t.bpm for t in tracks if t.bpm > 0]
    import_years = {}
    for t in tracks:
        if t.import_date and len(t.import_date) >= 4:
            y = t.import_date[:4]
            import_years[y] = import_years.get(y, 0) + 1

    return {
        "total": len(tracks),
        "with_bpm": len(bpm_values),
        "bpm_range": (min(bpm_values), max(bpm_values)) if bpm_values else (0, 0),
        "import_years": import_years,
        "top_artists": list(col.get_artists().items())[:10],
    }


from pathlib import Path
from bpm_analyzer import BPMAnalyzer
from duplicates import (
    find_duplicates, merge_tracks, format_duplicate_group,
    generate_duplicate_report, generate_nml_patch
)
from musicbrainz import MusicBrainzLookup, find_tracks_missing_metadata


def cmd_lookup(col: Collection, args: list[str], nml_path: str = None, outer_args=None) -> None:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-n", "--limit", type=int, default=20)
    parser.add_argument("--output", "-o", default="metadata_lookup.json")
    parsed, unknown = parser.parse_known_args(args)

    outer_limit = getattr(outer_args, 'limit', None) if outer_args else None

    # Use subcommand --limit if provided, otherwise outer -n, otherwise default 20
    limit = parsed.limit if parsed.limit != 20 else (outer_limit if outer_limit and outer_limit != 20 else 20)

    missing = find_tracks_missing_metadata(col.tracks)
    print(f"Tracks missing metadata: {len(missing)}")

    if not missing:
        print("All tracks have metadata!")
        return

    tracks_to_lookup = missing[:limit]

    mb = MusicBrainzLookup()
    print(f"Looking up {limit} tracks (rate limited, ~{limit}s)...")
    results = mb.lookup_tracks(tracks_to_lookup)

    found_count = sum(1 for r in results if r.found)
    print(f"\nFound: {found_count}/{len(results)}")

    if parsed.output:
        output_data = []
        for r in results:
            output_data.append({
                "artist": r.track.artist,
                "title": r.track.title,
                "found": r.found,
                "album": r.album,
                "year": r.year,
                "score": r.score,
                "error": r.error,
            })
        with open(parsed.output, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        print(f"Saved to {parsed.output}")

    print("\nSample results:")
    for r in results[:10]:
        status = "FOUND" if r.found else "MISSING"
        album_str = r.album[:30] if r.album else "-"
        print(f"  [{status:6}] {r.track.artist[:20]:20} | {r.track.title[:30]:30} | {album_str:30} | {r.year or 0}")


def cmd_analyze_bpm(col: Collection, args: list[str]) -> list:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", "-n", type=int, default=20)
    parser.add_argument("--output", "-o", default="bpm_analysis.json")
    parsed, unknown = parser.parse_known_args(args)

    missing_bpm = [t for t in col.tracks if t.bpm <= 0]
    print(f"Tracks missing BPM: {len(missing_bpm)}")

    if not missing_bpm:
        print("All tracks have BPM!")
        return []

    limit = min(parsed.limit, len(missing_bpm))
    tracks_to_analyze = missing_bpm[:limit]

    analyzer = BPMAnalyzer(args.nml if hasattr(args, 'nml') else "")

    def progress(current, total, title):
        pct = (current / total) * 100
        bar = "#" * int(pct // 2) + " " * (50 - int(pct // 2))
        safe_title = title[:40].encode('ascii', 'replace').decode('ascii')
        print(f"\r[{bar}] {pct:5.1f}% ({current}/{total}) | {safe_title:40}", end="", flush=True)

    print(f"Analyzing {limit} tracks...")
    results = analyzer.analyze_tracks(tracks_to_analyze, progress)
    print("\n\nResults:")
    for r in results:
        status = "OK" if r.error is None else f"ERR: {r.error}"
        bpm_str = f"{r.detected_bpm:6.1f}" if r.detected_bpm > 0 else "   N/A"
        safe_title = r.track.title[:40].encode('ascii', 'replace').decode('ascii')
        print(f"  {safe_title:40} | BPM: {bpm_str} | Conf: {r.confidence:.2f} | {status}")

    analyzer.save_results(results, parsed.output)
    print(f"\nSaved to {parsed.output}")
    return None


def cmd_duplicates(col: Collection, args: list[str], nml_path: str = None) -> None:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-n", type=int, default=20)
    parser.add_argument("--output", "-o", default=None)
    parser.add_argument("--same-file", action="store_true", help="Show only same-file duplicates (safe to merge)")
    parser.add_argument("--all", action="store_true", help="Show all duplicate groups including alternate versions")
    parser.add_argument("--patch", "-p", metavar="FILE", help="Generate NML patch file with duplicates removed")
    parsed, unknown = parser.parse_known_args(args)

    groups = find_duplicates(col.tracks)

    if parsed.same_file:
        groups = [g for g in groups if g.same_file]
    elif not parsed.all:
        groups = [g for g in groups if g.same_file]

    if not groups:
        print("No duplicate groups found.")
        return

    print(f"\nFound {len(groups)} duplicate group(s)")
    print("=" * 80)

    for i, group in enumerate(groups[:parsed.n or 20]):
        merged_track, actions = merge_tracks(group.winner, group.tracks[1:], group.same_file)
        group.merged_track = merged_track
        group.merge_actions = actions

        safe_artist = group.winner.artist[:30].encode('ascii', 'replace').decode('ascii')
        safe_title = group.winner.title[:35].encode('ascii', 'replace').decode('ascii')
        winner_cues = len(group.winner.cues)

        status = "SAME FILE" if group.same_file else "DIFF LENGTH"
        print(f"\n{i+1}. {safe_artist} | {safe_title}")
        print(f"   Winner: {group.winner.bpm:.1f} BPM | {group.winner.playtime:.0f}s | {winner_cues} cues | {group.winner.file_size/1_000_000:.1f}MB")
        print(f"   + {len(group.tracks)-1} duplicate(s) | {status}")

        if actions:
            merged_fields = list(set(a.field for a in actions))
            print(f"   -> Merged: {', '.join(merged_fields)}")

        for dup in group.tracks[1:]:
            safe_dup_artist = dup.artist[:20].encode('ascii', 'replace').decode('ascii')
            safe_dup_title = dup.title[:25].encode('ascii', 'replace').decode('ascii')
            print(f"     - {safe_dup_artist} | {safe_dup_title} | {dup.bpm:.1f} BPM | {dup.playtime:.0f}s")

    print("\n" + "=" * 80)

    if parsed.output:
        report = generate_duplicate_report(groups)
        with open(parsed.output, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"Report saved to {parsed.output}")

    if parsed.patch:
        if not nml_path:
            print("Error: --patch requires --nml to be set")
            return
        print(f"\nGenerating NML patch: {parsed.patch}")
        result = generate_nml_patch(groups, nml_path, parsed.patch)
        print(f"  Entries removed: {result.get('entries_removed', 0)}")
        print(f"  Entries kept: {result.get('entries_kept', 0)}")
        print(f"  Groups processed: {result.get('groups_processed', 0)}")
        print(f"  Patch saved to: {parsed.patch}")
        print(f"\n  --> Review the patch file before applying to your collection!")


def cmd_export(col: Collection, args: list[str]) -> None:
    if not args:
        print("Usage: export <filename> [query]")
        return

    filename = args[0]
    query_str = " ".join(args[1:]) if len(args) > 1 else ""

    if query_str:
        q = parse_query(query_str)
        tracks = col.search(q)
    else:
        tracks = []

    if filename.endswith(".m3u"):
        with open(filename, "w", encoding="utf-8") as f:
            f.write("#EXTM3U\n")
            for t in tracks:
                duration = int(t.playtime) if t.playtime > 0 else 0
                f.write(f"#EXTINF:{duration},{t.artist} - {t.title}\n")
                f.write(f"{t.full_path}\n")
        print(f"Exported {len(tracks)} tracks to {filename}")
    elif filename.endswith(".txt"):
        with open(filename, "w", encoding="utf-8") as f:
            for t in tracks:
                f.write(f"{t.full_path}\n")
        print(f"Exported {len(tracks)} paths to {filename}")
    elif filename.endswith(".nml"):
        nml_template = f'''<?xml version="1.0" encoding="UTF-8"?>
<NML VERSION="20">
<HEAD COMPANY="www.native-instruments.com" PROGRAM="Traktor Collection Query"></HEAD>
<PLAYLISTS>
  <NODE TYPE="FOLDER" NAME="Exports">
    <PLAYLIST NAME="{Path(filename).stem}" ENTRIES="{len(tracks)}">
'''
        for t in tracks:
            escaped_title = t.title.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
            escaped_artist = t.artist.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
            nml_template += f'''      <ENTRY TITLE="{escaped_title}" ARTIST="{escaped_artist}">
        <LOCATION DIR="/:Music/:" FILE="{t.file_path}" VOLUME="{t.volume}" VOLUMEID="{t.volume_id}"/>
        <TEMPO BPM="{t.bpm}"/>
        <INFO PLAYTIME="{int(t.playtime)}"/>
      </ENTRY>
'''
        nml_template += '''    </PLAYLIST>
  </NODE>
</PLAYLISTS>
</NML>'''
        with open(filename, "w", encoding="utf-8") as f:
            f.write(nml_template)
        print(f"Exported {len(tracks)} tracks to {filename}")
    else:
        print(f"Unsupported format: {filename}")
        print("Supported: .m3u, .txt, .nml")


COMMANDS = {
    "list": cmd_list,
    "l": cmd_list,
    "find": cmd_find,
    "f": cmd_find,
    "similar": cmd_similar,
    "sim": cmd_similar,
    "artists": cmd_artists,
    "albums": cmd_albums,
    "stats": cmd_stats,
    "export": cmd_export,
    "analyze": cmd_analyze_bpm,
    "duplicates": cmd_duplicates,
    "dup": cmd_duplicates,
    "lookup": cmd_lookup,
}


def main():
    parser = argparse.ArgumentParser(description="Traktor Collection Query CLI")
    parser.add_argument("command", nargs="?", default="list")
    parser.add_argument("args", nargs="*", default=[])
    parser.add_argument("--nml", default=r"\\UNRAIDTOWER\Storage\Temp\collection.nml",
                        help="Path to NML collection file")
    parser.add_argument("--limit", "-n", type=int, default=20)

    args = parser.parse_args()

    if args.command == "help":
        print("Available commands:")
        print("  list <query>     - Search tracks (e.g., 'list drum and bass 170-180')")
        print("  find <title>     - Find tracks by title")
        print("  similar <title>  - Find tracks similar to given title")
        print("  artists          - List all artists")
        print("  albums           - List all albums")
        print("  stats            - Collection statistics")
        print("  analyze          - Analyze tracks missing BPM")
        print("  lookup           - Lookup missing metadata via MusicBrainz")
        print("  duplicates       - Find duplicate tracks (alias: dup)")
        print("\nQuery examples:")
        print("  list drum and bass 170-180 recent")
        print("  list techno 130-140 from 2022")
        print("  list house with hotcues limit 50")
        print("  find shadow")
        print("  similar carbon decay")
        print("  analyze --limit 10 --output results.json")
        print("  lookup -n 20 --output metadata.json  # lookup missing metadata")
        print("  duplicates -n 20 -p cleaned.nml  # generate NML patch file")
        return

    nml_path = args.nml
    try:
        col = load_collection(nml_path)
    except Exception as e:
        print(f"Error loading collection: {e}")
        return

    if args.command == "duplicates" or args.command == "dup":
        cmd_duplicates(col, args.args, nml_path=args.nml)
    elif args.command == "lookup":
        cmd_lookup(col, args.args, nml_path=args.nml, outer_args=args)
    elif args.command in COMMANDS:
        cmd = COMMANDS[args.command]
        results = cmd(col, args.args)

        if results is None:
            return

        if isinstance(results, dict):
            if args.command == "artists":
                for artist, count in list(results.items())[:args.limit or 30]:
                    print(f"{count:4d}  {artist}")
            elif args.command == "albums":
                for album, count in list(results.items())[:args.limit or 30]:
                    print(f"{count:4d}  {album}")
            elif args.command == "stats":
                for k, v in results.items():
                    print(f"{k}: {v}")
        elif isinstance(results, list):
            if args.command in ("similar", "sim") and results:
                ref = results[0]
                print(f"Similar to: {ref.artist} - {ref.title} ({ref.bpm:.1f} BPM)")
                print("-" * 100)
            for i, t in enumerate(results[:args.limit or 50]):
                print(format_track(t, i))
        else:
            print(results)
    else:
        q = parse_query(args.command + " " + " ".join(args.args))
        q.limit = args.limit or 50
        results = col.search(q)
        for i, t in enumerate(results):
            print(format_track(t, i))


if __name__ == "__main__":
    main()
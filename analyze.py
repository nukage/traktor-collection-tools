import sys
sys.path.insert(0, 'src')
from parser import parse_nml, Track
from collections import defaultdict
import json

nml_path = r"\\UNRAIDTOWER\Storage\Temp\collection.nml"
tracks, basic_stats = parse_nml(nml_path)

bpm_buckets = defaultdict(int)
for t in tracks:
    if t.bpm > 0:
        bucket = int(t.bpm // 10) * 10
        bpm_buckets[bucket] += 1

bpm_ranges = {
    "70-90 (Deep/Low)": 0,
    "90-120 (House/Tech)": 0,
    "120-130 (Minimal/House)": 0,
    "130-140 (Techno/Trance)": 0,
    "140-150 (Prog House/Hardstyle)": 0,
    "150-160 (Drum&Bass/Bounce)": 0,
    "160-180 (Drum&Bass)": 0,
    "180+ (Hardstyle/Gabber)": 0,
}
for t in tracks:
    if t.bpm <= 0:
        continue
    bpm = t.bpm
    if bpm < 90:
        bpm_ranges["70-90 (Deep/Low)"] += 1
    elif bpm < 120:
        bpm_ranges["90-120 (House/Tech)"] += 1
    elif bpm < 130:
        bpm_ranges["120-130 (Minimal/House)"] += 1
    elif bpm < 140:
        bpm_ranges["130-140 (Techno/Trance)"] += 1
    elif bpm < 150:
        bpm_ranges["140-150 (Prog House/Hardstyle)"] += 1
    elif bpm < 160:
        bpm_ranges["150-160 (Drum&Bass/Bounce)"] += 1
    elif bpm < 180:
        bpm_ranges["160-180 (Drum&Bass)"] += 1
    else:
        bpm_ranges["180+ (Hardstyle/Gabber)"] += 1

artists = defaultdict(int)
for t in tracks:
    if t.artist:
        artists[t.artist] += 1

top_artists = sorted(artists.items(), key=lambda x: -x[1])[:30]

file_types = defaultdict(int)
for t in tracks:
    ext = t.file_path.split(".")[-1].lower() if "." in t.file_path else "unknown"
    file_types[ext] += 1

stems_count = sum(1 for t in tracks if t.stems)
loops_count = sum(1 for t in tracks if t.album and "Step Sequencer" in t.album)

hotcue_tracks = sum(1 for t in tracks if any(c.type == 0 and c.hotcue >= 0 for c in t.cues))
grid_tracks = sum(1 for t in tracks if any(c.type == 4 for c in t.cues))

print("=" * 60)
print("COLLECTION AUDIT REPORT")
print("=" * 60)
print(f"\nSource: {nml_path}")
print(f"\n## Overview")
print(f"  Total tracks:           {basic_stats['total_tracks']:,}")
print(f"  Tracks with BPM:         {basic_stats['tracks_with_bpm']:,}")
print(f"  BPM range:              {basic_stats['bpm_min']:.1f} - {basic_stats['bpm_max']:.1f}")
print(f"  BPM average:            {basic_stats['bpm_avg']:.1f}")
print(f"  Unique albums:          {basic_stats['unique_albums']:,}")
print(f"  Unique artists:         {len(artists):,}")

print(f"\n## File Types")
for ext, count in sorted(file_types.items(), key=lambda x: -x[1]):
    print(f"  {ext:12} {count:5,}")

print(f"\n## BPM Distribution (by 10s)")
for bucket in sorted(bpm_buckets.keys()):
    bar = "#" * (bpm_buckets[bucket] // 50)
    print(f"  {int(bucket):3d}-{int(bucket+9):3d}: {bpm_buckets[bucket]:5,} {bar}")

print(f"\n## BPM Range Breakdown")
for label, count in bpm_ranges.items():
    if count > 0:
        bar = "#" * (count // 50)
        print(f"  {label:30} {count:5,} {bar}")

print(f"\n## Collection Integrity")
print(f"  Tracks with stems:       {stems_count:,}")
print(f"  Loop samples:           {loops_count:,}")
print(f"  Tracks with hotcues:    {hotcue_tracks:,}")
print(f"  Tracks with grid:       {grid_tracks:,}")

print(f"\n## Play Stats")
total_plays = sum(t.playcount for t in tracks)
total_playtime_hours = basic_stats['total_playtime_seconds'] / 3600
print(f"  Total playcount:        {total_plays:,}")
print(f"  Total playtime:        {total_playtime_hours:.1f} hours ({total_playtime_hours/24:.1f} days)")

print(f"\n## Top 20 Artists")
for artist, count in top_artists[:20]:
    print(f"  {count:4d} - {artist}")

print(f"\n## Import Timeline")
for year, count in sorted(basic_stats['import_years'].items()):
    bar = "#" * (count // 30)
    print(f"  {year}: {count:5,} {bar}")

last_played = defaultdict(int)
for t in tracks:
    if t.last_played:
        year = t.last_played[:4]
        last_played[year] += 1
print(f"\n## Last Played (by year)")
for year in sorted(last_played.keys(), reverse=True)[:10]:
    count = last_played[year]
    bar = "#" * (count // 10)
    print(f"  {year}: {count:5,} {bar}")

with open("collection_data.json", "w", encoding="utf-8") as f:
    json.dump({
        "stats": basic_stats,
        "bpm_ranges": dict(bpm_ranges),
        "file_types": dict(file_types),
        "top_artists": dict(top_artists[:50]),
        "last_played": dict(last_played),
    }, f, indent=2, ensure_ascii=False)

print("\n" + "=" * 60)
print("Data saved to collection_data.json")
import sys
sys.path.insert(0, 'src')
from parser import parse_nml

nml_path = r"\\UNRAIDTOWER\Storage\Temp\collection.nml"
tracks, stats = parse_nml(nml_path)

print(f"Total tracks: {stats['total_tracks']}")
print(f"With BPM: {stats['tracks_with_bpm']}")
print(f"BPM range: {stats['bpm_min']:.1f} - {stats['bpm_max']:.1f}")
print(f"BPM avg: {stats['bpm_avg']:.1f}")
print(f"Unique albums: {stats['unique_albums']}")
print(f"Import years: {stats['import_years']}")
print()
print("Top 10 albums:")
for album, count in stats['top_albums'][:10]:
    print(f"  {count:4d} - {album}")
"""View detection results."""
import json

with open('output/detections.json') as f:
    d = json.load(f)

print("=== DETECTION RESULTS ===")
print(f"Frames: {d['metadata']['total_frames']}")
print(f"Total Tracks: {d['track_summary']['total_tracks']}")
print(f"Confirmed Tracks: {d['track_summary']['confirmed_tracks']}")
print(f"Classes Detected: {d['track_summary']['classes_tracked']}")
print()
print("=== CONFIRMED TRACKS ===")
for t in d['tracks'][:20]:
    print(f"  Track {t['track_id']}: {t['class_name']} ({t['duration_frames']} frames)")

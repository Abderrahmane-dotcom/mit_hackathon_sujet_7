"""
Visualization Script - Person 1: Ingest + Detection
Creates annotated frames showing detections and tracks.
"""

import json
import cv2
from pathlib import Path
import numpy as np

# Load detection results
with open('output/detections.json') as f:
    data = json.load(f)

print(f"Loaded {len(data['frame_detections'])} frame results")
print(f"Classes detected: {data['track_summary']['classes_tracked']}")

# Color map for different classes
COLORS = {
    'person': (0, 255, 0),
    'motorcycle': (255, 0, 0),
    'car': (0, 0, 255),
    'truck': (255, 255, 0),
    'chair': (255, 0, 255),
    'suitcase': (0, 255, 255),
    'default': (128, 128, 128)
}

def get_color(class_name):
    return COLORS.get(class_name, COLORS['default'])

# Create output directory
output_dir = Path('output/visualized')
output_dir.mkdir(parents=True, exist_ok=True)

# Visualize key frames (every 10th frame)
key_frames = [0, 30, 60, 90, 120, 150, 180]
key_frames = [f for f in key_frames if f < len(data['frame_detections'])]

print(f"\nVisualizing {len(key_frames)} key frames...")

for frame_idx in key_frames:
    frame_data = data['frame_detections'][frame_idx]
    frame_path = frame_data['frame_path']
    
    # Load image
    img = cv2.imread(frame_path)
    if img is None:
        print(f"Failed to load {frame_path}")
        continue
    
    # Draw detections
    for i, (box, score, class_name, track_id) in enumerate(zip(
        frame_data['boxes'],
        frame_data['scores'],
        frame_data['class_names'],
        frame_data['track_ids']
    )):
        x1, y1, x2, y2 = [int(c) for c in box]
        color = get_color(class_name)
        
        # Draw box
        cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
        
        # Draw label
        label = f"#{track_id} {class_name} {score:.2f}"
        label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)[0]
        cv2.rectangle(img, (x1, y1 - label_size[1] - 10), (x1 + label_size[0], y1), color, -1)
        cv2.putText(img, label, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
    
    # Add frame info
    info = f"Frame {frame_idx} | {len(frame_data['boxes'])} detections | t={frame_data['timestamp']:.2f}s"
    cv2.putText(img, info, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    
    # Save
    output_path = output_dir / f"frame_{frame_idx:04d}_annotated.jpg"
    cv2.imwrite(str(output_path), img)
    print(f"  Saved: {output_path.name}")

print(f"\n=== Visualization Complete ===")
print(f"Output directory: {output_dir}")

# Summary stats
print(f"\n=== Track Summary ===")
for track in data['tracks']:
    start_frame = track['frame_indices'][0]
    end_frame = track['frame_indices'][-1]
    print(f"Track {track['track_id']}: {track['class_name']} (frames {start_frame}-{end_frame}, {track['duration_frames']} total)")

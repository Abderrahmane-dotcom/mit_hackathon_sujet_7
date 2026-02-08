"""
Create Annotated Video - Person 1: Ingest + Detection
Combines all frames with detection annotations into a video file.
"""

import json
import cv2
from pathlib import Path

# Load detection results
with open('output/detections.json') as f:
    data = json.load(f)

print(f"Creating annotated video from {len(data['frame_detections'])} frames...")

# Color map for different classes
COLORS = {
    'person': (0, 255, 0),
    'motorcycle': (255, 0, 0),
    'car': (0, 0, 255),
    'truck': (255, 255, 0),
    'chair': (255, 0, 255),
    'suitcase': (0, 255, 255),
    'umbrella': (128, 0, 128),
    'default': (128, 128, 128)
}

def get_color(class_name):
    return COLORS.get(class_name, COLORS['default'])

# Get first frame to determine video size
first_frame = cv2.imread(data['frame_detections'][0]['frame_path'])
height, width = first_frame.shape[:2]
fps = 30

# Create video writer
output_path = 'output/annotated_video.mp4'
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
video_writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

# Process all frames
for frame_idx, frame_data in enumerate(data['frame_detections']):
    frame_path = frame_data['frame_path']
    
    # Load image
    img = cv2.imread(frame_path)
    if img is None:
        print(f"Failed to load {frame_path}")
        continue
    
    # Draw detections
    for box, score, class_name, track_id in zip(
        frame_data['boxes'],
        frame_data['scores'],
        frame_data['class_names'],
        frame_data['track_ids']
    ):
        x1, y1, x2, y2 = [int(c) for c in box]
        color = get_color(class_name)
        
        # Draw box with thicker lines
        cv2.rectangle(img, (x1, y1), (x2, y2), color, 3)
        
        # Draw label with background
        label = f"#{track_id} {class_name} {score:.2f}"
        label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
        cv2.rectangle(img, (x1, y1 - label_size[1] - 10), (x1 + label_size[0] + 5, y1), color, -1)
        cv2.putText(img, label, (x1 + 2, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    
    # Add frame info
    info = f"Frame {frame_idx} | {len(frame_data['boxes'])} detections | t={frame_data['timestamp']:.2f}s"
    # Add black background for text
    cv2.rectangle(img, (5, 5), (450, 40), (0, 0, 0), -1)
    cv2.putText(img, info, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    
    # Write frame
    video_writer.write(img)
    
    # Progress
    if (frame_idx + 1) % 30 == 0:
        print(f"  Processed {frame_idx + 1}/{len(data['frame_detections'])} frames...")

video_writer.release()
print(f"\n=== Video Created ===")
print(f"Output: {output_path}")
print(f"Duration: {len(data['frame_detections']) / fps:.2f}s at {fps} fps")

# World2Data Hackathon - Person 1: Ingest + Detection

## 🎯 Overview

This pipeline converts raw video into structured ground truth data for humanoid robot training. It implements **Person 1's** tasks from the hackathon requirements:

- ✅ Video loading with frame extraction and timestamps
- ✅ YOLOv8 object detection
- ✅ ByteTrack multi-object tracking

---

## 📁 Project Structure

```
hack4mit/
├── src/
│   ├── ingest/
│   │   ├── __init__.py
│   │   └── video_loader.py      # Load video/frames with timestamps
│   └── detection/
│       ├── __init__.py
│       ├── yolo_detector.py     # YOLOv8 object detection wrapper
│       └── bytetrack_tracker.py # ByteTrack tracking (supervision lib)
│
├── configs/
│   └── model.yaml               # Detector & tracker settings
│
├── frames/                      # Extracted video frames (181 @ 30fps)
├── output/
│   ├── detections.json          # Full detection & tracking results
│   ├── annotated_video.mp4      # Video with bounding boxes
│   └── visualized/              # Annotated key frames
│
├── run_pipeline.py              # Main pipeline runner
├── create_video.py              # Generate annotated video
├── view_results.py              # View detection summary
└── README.md                    # This file
```

---

## 🔧 Components

### 1. Video Loader (`src/ingest/video_loader.py`)

Handles video ingestion with two modes:

```python
# Load from video file
from src.ingest import VideoLoader
loader = VideoLoader("video.mp4")
for frame_idx, timestamp, frame in loader.frame_iterator():
    # Process frame

# Load from pre-extracted frames
from src.ingest import frame_iterator
for frame_idx, timestamp, frame in frame_iterator("frames/"):
    # Process frame
```

**Features:**
- Frame iteration with timestamps
- Video metadata (fps, duration, resolution)
- Extract frames to directory

---

### 2. YOLO Detector (`src/detection/yolo_detector.py`)

Wraps YOLOv8 for object detection:

```python
from src.detection import YOLODetector

detector = YOLODetector(
    model_path="yolov8n.pt",
    confidence_threshold=0.36
)

result = detector.detect(frame)
# Returns: {boxes, scores, class_ids, class_names}
```

**Navigation-relevant classes detected:**
- Person, vehicles (car, truck, motorcycle)
- Furniture (chair, couch, table)
- Appliances (refrigerator, sink, oven)
- Objects (suitcase, umbrella, backpack)

---

### 3. ByteTrack Tracker (`src/detection/bytetrack_tracker.py`)

Uses `supervision` library's ByteTrack for multi-object tracking:

```python
from src.detection import ByteTracker

tracker = ByteTracker(
    track_activation_threshold=0.36,
    lost_track_buffer=30,
    frame_rate=30
)

tracked = tracker.update(detections, frame_idx=0, timestamp=0.0)
# Returns: {boxes, scores, class_ids, class_names, track_ids}
```

**Features:**
- Consistent object IDs across frames
- Track history with bounding boxes and timestamps
- Track summary statistics

---

## 🚀 Usage

### Run Full Pipeline

```bash
# Extract frames from video (if not done)
ffmpeg -ss 00:00:31 -to 00:00:37 -i video.mp4 -vf "fps=30" frames/frame_%04d.jpg

# Run detection + tracking
python run_pipeline.py frames output/detections.json

# Create annotated video
python create_video.py

# View results summary
python view_results.py
```

### Output Format (`detections.json`)

```json
{
  "metadata": {
    "pipeline": "World2Data - Person 1: Ingest + Detection",
    "components": {
      "ingest": "src/ingest/video_loader.py",
      "detector": "src/detection/yolo_detector.py",
      "tracker": "src/detection/bytetrack_tracker.py"
    },
    "total_frames": 181,
    "fps": 30,
    "confidence_threshold": 0.36
  },
  "track_summary": {
    "total_tracks": 21,
    "confirmed_tracks": 12,
    "classes_tracked": ["person", "truck", "chair", ...]
  },
  "tracks": [...],
  "frame_detections": [...]
}
```

---

## 📊 Results (0:31-0:37 segment)

| Metric | Value |
|--------|-------|
| Frames processed | 181 |
| FPS | 30 |
| Duration | 6.03s |
| Resolution | 1280x720 |
| Total tracks | 21 |
| Confirmed tracks | 12 |
| Detection threshold | 0.36 |

**Classes detected:** person, truck, motorcycle, chair, tv, umbrella, sink

---

## 📦 Dependencies

```bash
pip install ultralytics opencv-python-headless supervision
```

---

## 🔗 Integration with Other Persons

| Person | Task | Integration Point |
|--------|------|-------------------|
| Person 2 | Interaction + State Tracking | Uses `frame_detections` from output |
| Person 3 | Semantic + Segmentation | Uses detected bounding boxes |
| Person 4 | Logging + App + Eval | Uses full JSON output |

---

## 📝 Configuration (`configs/model.yaml`)

```yaml
detector:
  model: "yolov8n.pt"
  confidence: 0.36
  iou: 0.45

tracker:
  iou_threshold: 0.3
  max_age: 30
  min_hits: 3

video:
  fps: 30
```

---

*World2Data Hackathon - MIT 2026*

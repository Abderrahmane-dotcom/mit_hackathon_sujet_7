"""
Main Detection Pipeline - Person 1: Ingest + Detection
Runs the full detection and tracking pipeline on video frames.

Uses:
- src/ingest/video_loader.py (load video, frame iterator, timestamps)
- src/detection/yolo_detector.py (wrap YOLOv8 inference)
- src/detection/bytetrack_tracker.py (track IDs across frames - uses supervision ByteTrack)
- configs/model.yaml (detector and tracker settings)
"""

import sys
import json
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

# Import from our modules
from src.ingest.video_loader import get_frame_paths, get_video_info
from src.detection.yolo_detector import YOLODetector
from src.detection.bytetrack_tracker import ByteTracker


def run_detection_pipeline(
    frames_dir: str,
    output_path: str = "output/detections.json",
    model: str = "yolov8n.pt",
    confidence: float = 0.36,
    fps: float = 30.0
):
    """
    Run detection and tracking on extracted frames.
    
    Pipeline:
    1. Load frames using src/ingest/video_loader.py
    2. Detect objects using src/detection/yolo_detector.py (YOLOv8)
    3. Track objects using src/detection/bytetrack_tracker.py (ByteTrack)
    4. Output structured JSON with detections and tracks
    
    Args:
        frames_dir: Directory containing frame images
        output_path: Output JSON file path
        model: YOLO model to use
        confidence: Detection confidence threshold
        fps: Video FPS for timestamp calculation
    """
    # === INGEST: Use video_loader.py ===
    frame_paths = get_frame_paths(frames_dir)
    video_info = get_video_info(frames_dir, fps)
    
    if not frame_paths:
        print(f"Error: No frames found in {frames_dir}")
        return None
    
    print(f"=== Video Info ===")
    print(f"  Frames: {video_info['frame_count']}")
    print(f"  Resolution: {video_info['width']}x{video_info['height']}")
    print(f"  Duration: {video_info['duration_seconds']:.2f}s at {fps}fps")
    
    # === DETECTION: Use yolo_detector.py ===
    print(f"\n=== Initializing Detector ===")
    print(f"  Model: {model}")
    print(f"  Confidence threshold: {confidence}")
    detector = YOLODetector(model_path=model, confidence_threshold=confidence)
    
    # === TRACKING: Use bytetrack_tracker.py (supervision ByteTrack) ===
    print(f"\n=== Initializing Tracker ===")
    print(f"  Algorithm: ByteTrack (supervision library)")
    tracker = ByteTracker(
        track_activation_threshold=confidence,
        lost_track_buffer=30,
        minimum_matching_threshold=0.8,
        frame_rate=int(fps)
    )
    
    # === PROCESS FRAMES ===
    all_frame_results = []
    
    print(f"\n=== Processing {len(frame_paths)} frames ===")
    for i, frame_path in enumerate(frame_paths):
        timestamp = i / fps
        
        # Detect objects (yolo_detector.py)
        detections = detector.detect(frame_path)
        
        # Track objects (bytetrack_tracker.py)
        tracked = tracker.update(detections, frame_idx=i, timestamp=timestamp)
        tracked["frame_path"] = frame_path
        
        all_frame_results.append(tracked)
        
        # Progress indicator
        if (i + 1) % 30 == 0 or i == 0:
            n_dets = len(detections["boxes"])
            print(f"  Frame {i+1}/{len(frame_paths)}: {n_dets} detections")
    
    # Get final track summary
    track_summary = tracker.get_track_summary()
    all_tracks = tracker.get_tracks(min_hits=3)
    
    # Build output
    output = {
        "metadata": {
            "pipeline": "World2Data - Person 1: Ingest + Detection",
            "video_segment": "0:31-0:37",
            "components": {
                "ingest": "src/ingest/video_loader.py",
                "detector": "src/detection/yolo_detector.py (YOLOv8)",
                "tracker": "src/detection/bytetrack_tracker.py (ByteTrack via supervision)"
            },
            "config": "configs/model.yaml",
            "total_frames": len(frame_paths),
            "fps": fps,
            "model": model,
            "confidence_threshold": confidence,
            "processed_at": datetime.now().isoformat()
        },
        "video_info": video_info,
        "track_summary": track_summary,
        "tracks": all_tracks,
        "frame_detections": all_frame_results
    }
    
    # Save output
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\n=== Pipeline Complete ===")
    print(f"Total frames: {len(frame_paths)}")
    print(f"Total tracks: {track_summary['total_tracks']}")
    print(f"Confirmed tracks: {track_summary['confirmed_tracks']}")
    print(f"Classes detected: {track_summary['classes_tracked']}")
    print(f"Output saved to: {output_file}")
    
    return output


if __name__ == "__main__":
    frames_dir = sys.argv[1] if len(sys.argv) > 1 else "frames"
    output_path = sys.argv[2] if len(sys.argv) > 2 else "output/detections.json"
    
    run_detection_pipeline(
        frames_dir=frames_dir,
        output_path=output_path,
        model="yolov8n.pt",
        confidence=0.36,
        fps=30.0
    )

"""
ByteTrack Tracker Module - Person 1: Ingest + Detection
Uses the supervision library's ByteTrack implementation for object tracking.
"""

from typing import List, Dict, Optional
import numpy as np

try:
    import supervision as sv
    SUPERVISION_AVAILABLE = True
except ImportError:
    SUPERVISION_AVAILABLE = False
    print("Warning: supervision not installed. Run: pip install supervision")


class ByteTracker:
    """
    ByteTrack tracker using supervision library.
    Tracks object IDs across frames using the ByteTrack algorithm.
    """
    
    def __init__(
        self,
        track_activation_threshold: float = 0.25,
        lost_track_buffer: int = 30,
        minimum_matching_threshold: float = 0.8,
        frame_rate: int = 30
    ):
        """
        Initialize ByteTrack tracker.
        
        Args:
            track_activation_threshold: Detection confidence threshold to consider
            lost_track_buffer: Number of frames to keep lost tracks
            minimum_matching_threshold: Minimum IoU for matching
            frame_rate: Video frame rate
        """
        if not SUPERVISION_AVAILABLE:
            raise ImportError("supervision library required: pip install supervision")
        
        self.tracker = sv.ByteTrack(
            track_activation_threshold=track_activation_threshold,
            lost_track_buffer=lost_track_buffer,
            minimum_matching_threshold=minimum_matching_threshold,
            frame_rate=frame_rate
        )
        
        self.track_history: Dict[int, Dict] = {}
        self.current_frame = 0
    
    def update(
        self, 
        detections: Dict,
        frame_idx: int,
        timestamp: float = 0.0
    ) -> Dict:
        """
        Update tracker with new detections from YOLO.
        
        Args:
            detections: Dict from YOLODetector.detect() with boxes, scores, class_ids, class_names
            frame_idx: Current frame index
            timestamp: Current timestamp in seconds
            
        Returns:
            Dict with tracked detections including track_ids
        """
        self.current_frame = frame_idx
        
        boxes = detections.get("boxes", [])
        scores = detections.get("scores", [])
        class_ids = detections.get("class_ids", [])
        class_names = detections.get("class_names", [])
        
        if not boxes:
            return {
                "boxes": [],
                "scores": [],
                "class_ids": [],
                "class_names": [],
                "track_ids": [],
                "frame_idx": frame_idx,
                "timestamp": timestamp
            }
        
        # Convert to supervision Detections format
        xyxy = np.array(boxes)
        confidence = np.array(scores)
        class_id = np.array(class_ids)
        
        sv_detections = sv.Detections(
            xyxy=xyxy,
            confidence=confidence,
            class_id=class_id
        )
        
        # Run ByteTrack
        tracked_detections = self.tracker.update_with_detections(sv_detections)
        
        # Extract track IDs
        if tracked_detections.tracker_id is not None:
            track_ids = tracked_detections.tracker_id.tolist()
        else:
            track_ids = [None] * len(boxes)
        
        # Update track history
        for i, track_id in enumerate(track_ids):
            if track_id is not None:
                if track_id not in self.track_history:
                    self.track_history[track_id] = {
                        "track_id": track_id,
                        "class_id": int(class_ids[i]) if i < len(class_ids) else -1,
                        "class_name": class_names[i] if i < len(class_names) else "unknown",
                        "boxes": [],
                        "scores": [],
                        "frame_indices": [],
                        "timestamps": []
                    }
                
                self.track_history[track_id]["boxes"].append(boxes[i])
                self.track_history[track_id]["scores"].append(scores[i])
                self.track_history[track_id]["frame_indices"].append(frame_idx)
                self.track_history[track_id]["timestamps"].append(timestamp)
        
        # Return results aligned with original detection order
        result_track_ids = []
        for i, box in enumerate(boxes):
            # Find matching track by box
            matched_id = None
            for j, tracked_box in enumerate(tracked_detections.xyxy):
                if np.allclose(box, tracked_box, atol=1):
                    if tracked_detections.tracker_id is not None:
                        matched_id = int(tracked_detections.tracker_id[j])
                    break
            result_track_ids.append(matched_id)
        
        return {
            "boxes": boxes,
            "scores": scores,
            "class_ids": class_ids,
            "class_names": class_names,
            "track_ids": result_track_ids,
            "frame_idx": frame_idx,
            "timestamp": timestamp
        }
    
    def get_tracks(self, min_hits: int = 3) -> List[Dict]:
        """Get all tracks with at least min_hits detections."""
        tracks = []
        for track_id, track_data in self.track_history.items():
            if len(track_data["frame_indices"]) >= min_hits:
                track_data["duration_frames"] = len(track_data["frame_indices"])
                tracks.append(track_data)
        return tracks
    
    def get_track_summary(self) -> Dict:
        """Get summary statistics of tracking."""
        confirmed_tracks = [t for t in self.track_history.values() if len(t["frame_indices"]) >= 3]
        classes = list(set(t["class_name"] for t in self.track_history.values()))
        
        return {
            "total_tracks": len(self.track_history),
            "confirmed_tracks": len(confirmed_tracks),
            "classes_tracked": classes,
            "frames_processed": self.current_frame + 1
        }
    
    def reset(self):
        """Reset the tracker state."""
        self.tracker.reset()
        self.track_history = {}
        self.current_frame = 0


def create_tracker(**kwargs) -> ByteTracker:
    """Convenience function to create a ByteTracker."""
    return ByteTracker(**kwargs)


# Keep Track dataclass for compatibility
from dataclasses import dataclass, field

@dataclass
class Track:
    """Represents a tracked object across frames."""
    track_id: int
    class_id: int
    class_name: str
    boxes: List[List[float]] = field(default_factory=list)
    scores: List[float] = field(default_factory=list)
    frame_indices: List[int] = field(default_factory=list)
    timestamps: List[float] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            "track_id": self.track_id,
            "class_id": self.class_id,
            "class_name": self.class_name,
            "boxes": self.boxes,
            "scores": self.scores,
            "frame_indices": self.frame_indices,
            "timestamps": self.timestamps,
            "duration_frames": len(self.frame_indices)
        }


if __name__ == "__main__":
    print(f"Supervision available: {SUPERVISION_AVAILABLE}")
    
    if SUPERVISION_AVAILABLE:
        # Test tracker
        tracker = ByteTracker()
        
        # Simulated detections
        test_dets = {
            "boxes": [[100, 100, 200, 200], [300, 300, 400, 400]],
            "scores": [0.9, 0.8],
            "class_ids": [0, 0],
            "class_names": ["person", "person"]
        }
        
        result = tracker.update(test_dets, frame_idx=0, timestamp=0.0)
        print(f"Frame 0 tracks: {result['track_ids']}")
        
        # Move boxes slightly
        test_dets["boxes"] = [[105, 102, 205, 202], [305, 302, 405, 402]]
        result = tracker.update(test_dets, frame_idx=1, timestamp=0.033)
        print(f"Frame 1 tracks: {result['track_ids']}")
        
        print(f"\nTrack summary: {tracker.get_track_summary()}")

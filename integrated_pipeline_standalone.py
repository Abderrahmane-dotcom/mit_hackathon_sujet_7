"""
Integrated World2Data Pipeline - Standalone Version
Combines Person 1 (Detection + Tracking) with Person 2 (Interaction + State)
Uses direct imports to avoid package issues.
"""

import sys
import json
import glob
import cv2
import numpy as np
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
from collections import deque

# === PERSON 1: VIDEO LOADER (inline) ===
def get_frame_paths(frames_dir: str, pattern: str = "*.jpg") -> List[str]:
    frames_path = Path(frames_dir)
    return sorted(glob.glob(str(frames_path / pattern)))

def get_video_info(frames_dir: str, fps: float = 30.0) -> Dict:
    frame_paths = get_frame_paths(frames_dir)
    if not frame_paths:
        return {"error": "No frames found"}
    first_frame = cv2.imread(frame_paths[0])
    height, width = first_frame.shape[:2] if first_frame is not None else (0, 0)
    return {
        "frames_dir": frames_dir,
        "frame_count": len(frame_paths),
        "fps": fps,
        "width": width,
        "height": height,
        "duration_seconds": len(frame_paths) / fps
    }

# === PERSON 1: YOLO DETECTOR (use ultralytics directly) ===
try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False

NAVIGATION_CLASSES = {
    0: "person", 1: "bicycle", 2: "car", 3: "motorcycle", 5: "bus", 7: "truck",
    56: "chair", 57: "couch", 58: "potted plant", 59: "bed", 60: "dining table",
    61: "toilet", 62: "tv", 63: "laptop", 24: "backpack", 25: "umbrella",
    26: "handbag", 28: "suitcase", 68: "microwave", 71: "sink", 72: "refrigerator"
}

class YOLODetector:
    def __init__(self, model_path: str = "yolov8n.pt", confidence_threshold: float = 0.36):
        self.model = YOLO(model_path)
        self.confidence_threshold = confidence_threshold
        self.target_classes = list(NAVIGATION_CLASSES.keys())
    
    def detect(self, image):
        results = self.model(image, conf=self.confidence_threshold, 
                            classes=self.target_classes, verbose=False)[0]
        boxes = results.boxes.xyxy.cpu().numpy().tolist() if len(results.boxes) > 0 else []
        scores = results.boxes.conf.cpu().numpy().tolist() if len(results.boxes) > 0 else []
        class_ids = results.boxes.cls.cpu().numpy().astype(int).tolist() if len(results.boxes) > 0 else []
        class_names = [NAVIGATION_CLASSES.get(cid, "unknown") for cid in class_ids]
        return {"boxes": boxes, "scores": scores, "class_ids": class_ids, "class_names": class_names}

# === PERSON 1: BYTETRACK (use supervision) ===
try:
    import supervision as sv
    SUPERVISION_AVAILABLE = True
except ImportError:
    SUPERVISION_AVAILABLE = False

class ByteTracker:
    def __init__(self, confidence: float = 0.36, frame_rate: int = 30):
        self.tracker = sv.ByteTrack(track_activation_threshold=confidence, 
                                     lost_track_buffer=30, frame_rate=frame_rate)
        self.track_history = {}
        self.current_frame = 0
    
    def update(self, detections: Dict, frame_idx: int, timestamp: float = 0.0) -> Dict:
        self.current_frame = frame_idx
        boxes = detections.get("boxes", [])
        scores = detections.get("scores", [])
        class_ids = detections.get("class_ids", [])
        class_names = detections.get("class_names", [])
        
        if not boxes:
            return {"boxes": [], "scores": [], "class_ids": [], "class_names": [],
                    "track_ids": [], "frame_idx": frame_idx, "timestamp": timestamp}
        
        sv_detections = sv.Detections(xyxy=np.array(boxes), confidence=np.array(scores),
                                       class_id=np.array(class_ids))
        tracked = self.tracker.update_with_detections(sv_detections)
        track_ids = tracked.tracker_id.tolist() if tracked.tracker_id is not None else [None] * len(boxes)
        
        # Update history
        for i, tid in enumerate(track_ids):
            if tid is not None:
                if tid not in self.track_history:
                    self.track_history[tid] = {"class_name": class_names[i] if i < len(class_names) else "unknown",
                                                "frames": []}
                self.track_history[tid]["frames"].append(frame_idx)
        
        return {"boxes": boxes, "scores": scores, "class_ids": class_ids, "class_names": class_names,
                "track_ids": track_ids, "frame_idx": frame_idx, "timestamp": timestamp}
    
    def get_track_summary(self) -> Dict:
        confirmed = [t for t in self.track_history.values() if len(t["frames"]) >= 3]
        classes = list(set(t["class_name"] for t in self.track_history.values()))
        return {"total_tracks": len(self.track_history), "confirmed_tracks": len(confirmed),
                "classes_tracked": classes, "frames_processed": self.current_frame + 1}

# === PERSON 2: IoU TRIGGER (inline) ===
def iou(box_a, box_b) -> float:
    ax1, ay1, ax2, ay2 = box_a
    bx1, by1, bx2, by2 = box_b
    inter_x1, inter_y1 = max(ax1, bx1), max(ay1, by1)
    inter_x2, inter_y2 = min(ax2, bx2), min(ay2, by2)
    inter_area = max(0, inter_x2 - inter_x1) * max(0, inter_y2 - inter_y1)
    area_a = max(0, ax2 - ax1) * max(0, ay2 - ay1)
    area_b = max(0, bx2 - bx1) * max(0, by2 - by1)
    union_area = area_a + area_b - inter_area
    return inter_area / union_area if union_area > 0 else 0.0

@dataclass
class TriggerStep:
    triggered: bool
    baseline: float
    delta: float

class RollingSpikeTrigger:
    def __init__(self, baseline_window: int = 8, spike_delta: float = 0.15,
                 min_iou: float = 0.05, cooldown_frames: int = 10):
        self.spike_delta = spike_delta
        self.min_iou = min_iou
        self.cooldown_frames = cooldown_frames
        self._history = deque(maxlen=baseline_window)
        self._last_trigger_frame = -1000
    
    def step(self, frame_idx: int, iou_value: float) -> TriggerStep:
        baseline = sum(self._history) / len(self._history) if self._history else 0.0
        can_trigger = (frame_idx - self._last_trigger_frame) >= self.cooldown_frames
        spike = (iou_value - baseline) >= self.spike_delta and iou_value >= self.min_iou
        triggered = can_trigger and spike
        if triggered:
            self._last_trigger_frame = frame_idx
        self._history.append(iou_value)
        return TriggerStep(triggered=triggered, baseline=baseline, delta=iou_value - baseline)

# === PERSON 2: STATE MEMORY (inline) ===
@dataclass
class StateTransition:
    object_id: str
    frame_idx: int
    before: str
    after: str
    reason: str

class StateMemory:
    def __init__(self):
        self._states: Dict[str, str] = {}
        self._history: List[StateTransition] = []
    
    def get_state(self, object_id: str) -> str:
        return self._states.get(object_id, "unknown")
    
    def update_state(self, object_id: str, new_state: str, frame_idx: int, reason: str) -> bool:
        prev = self.get_state(object_id)
        if prev == new_state:
            return False
        self._states[object_id] = new_state
        self._history.append(StateTransition(object_id, frame_idx, prev, new_state, reason))
        return True
    
    @property
    def history(self) -> List:
        return list(self._history)

# === INTEGRATED PIPELINE ===
AGENT_CLASSES = {"person"}
OBJECT_CLASSES = {"chair", "couch", "truck", "car", "motorcycle", "refrigerator", 
                  "tv", "sink", "toilet", "bed", "dining table", "suitcase", "umbrella"}

def run_integrated_pipeline(frames_dir: str, output_path: str = "output/integrated_results.json",
                           confidence: float = 0.36, fps: float = 30.0):
    print("=" * 60)
    print("WORLD2DATA INTEGRATED PIPELINE")
    print("=" * 60)
    
    # Load frames
    frame_paths = get_frame_paths(frames_dir)
    video_info = get_video_info(frames_dir, fps)
    print(f"\n[INGEST] Loaded {len(frame_paths)} frames")
    
    # Initialize
    detector = YOLODetector(confidence_threshold=confidence)
    tracker = ByteTracker(confidence=confidence, frame_rate=int(fps))
    triggers: Dict[Tuple[str, str], RollingSpikeTrigger] = {}
    state_memory = StateMemory()
    
    all_frame_results = []
    all_interactions = []
    
    print(f"\n[PROCESSING] {len(frame_paths)} frames...")
    
    for i, frame_path in enumerate(frame_paths):
        timestamp = i / fps
        
        # Detect & Track
        detections = detector.detect(frame_path)
        tracked = tracker.update(detections, frame_idx=i, timestamp=timestamp)
        
        # Classify agents vs objects
        agents, objects = {}, {}
        for j, (box, class_name, track_id) in enumerate(zip(
            tracked["boxes"], tracked["class_names"], tracked["track_ids"])):
            if track_id is None:
                continue
            obj_id = f"{class_name}_{track_id}"
            if class_name in AGENT_CLASSES:
                agents[obj_id] = tuple(box)
            elif class_name in OBJECT_CLASSES:
                objects[obj_id] = tuple(box)
        
        # Check interactions
        frame_interactions = []
        for agent_id, agent_box in agents.items():
            for object_id, object_box in objects.items():
                key = (agent_id, object_id)
                if key not in triggers:
                    triggers[key] = RollingSpikeTrigger()
                
                iou_val = iou(agent_box, object_box)
                result = triggers[key].step(i, iou_val)
                
                if result.triggered:
                    interaction = {
                        "frame_idx": i, "timestamp": timestamp,
                        "agent_id": agent_id, "object_id": object_id,
                        "iou_value": round(iou_val, 4)
                    }
                    frame_interactions.append(interaction)
                    all_interactions.append(interaction)
                    
                    # Update state
                    curr = state_memory.get_state(object_id)
                    new = "open" if curr != "open" else "closed"
                    state_memory.update_state(object_id, new, i, f"interaction with {agent_id}")
        
        # Store result
        all_frame_results.append({
            "frame_idx": i, "timestamp": timestamp, "frame_path": frame_path,
            "detections": {"boxes": tracked["boxes"], "scores": tracked["scores"],
                          "class_names": tracked["class_names"], "track_ids": tracked["track_ids"]},
            "agents": list(agents.keys()), "objects": list(objects.keys()),
            "interactions": frame_interactions
        })
        
        if (i + 1) % 30 == 0 or i == 0:
            print(f"  Frame {i+1}/{len(frame_paths)}: {len(agents)} agents, {len(objects)} objects")
    
    # Build output
    track_summary = tracker.get_track_summary()
    state_history = [{"object_id": t.object_id, "frame_idx": t.frame_idx,
                      "before": t.before, "after": t.after, "reason": t.reason}
                     for t in state_memory.history]
    
    output = {
        "metadata": {
            "pipeline": "World2Data Integrated Pipeline",
            "total_frames": len(frame_paths),
            "fps": fps,
            "processed_at": datetime.now().isoformat()
        },
        "video_info": video_info,
        "track_summary": track_summary,
        "interaction_summary": {"total_interactions": len(all_interactions)},
        "state_transitions": state_history,
        "interactions": all_interactions,
        "frame_data": all_frame_results
    }
    
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\n{'=' * 60}")
    print("PIPELINE COMPLETE")
    print(f"Frames: {len(frame_paths)} | Tracks: {track_summary['total_tracks']}")
    print(f"Interactions: {len(all_interactions)} | State transitions: {len(state_history)}")
    print(f"Output: {output_path}")
    
    return output

if __name__ == "__main__":
    frames_dir = sys.argv[1] if len(sys.argv) > 1 else "frames"
    output_path = sys.argv[2] if len(sys.argv) > 2 else "output/integrated_results.json"
    run_integrated_pipeline(frames_dir, output_path)

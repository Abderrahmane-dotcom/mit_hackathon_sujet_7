"""
Integrated World2Data Pipeline
Combines Person 1 (Detection + Tracking) with Person 2 (Interaction + State)

Pipeline Flow:
1. Load frames (Person 1: video_loader)
2. Detect objects (Person 1: yolo_detector)
3. Track objects (Person 1: bytetrack_tracker)
4. Detect interactions (Person 2: iou_trigger)
5. Track state changes (Person 2: state_memory)
6. Output structured JSON with all data
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

# Add paths - use current working directory
cwd = Path.cwd()
sys.path.insert(0, str(cwd))

# Person 1 imports
from src.ingest.video_loader import get_frame_paths, get_video_info
from src.detection.yolo_detector import YOLODetector
from src.detection.bytetrack_tracker import ByteTracker

# Person 2 imports (now in src/)
from src.interaction.iou_trigger import RollingSpikeTrigger, iou
from src.interaction.state_memory import StateMemory, StateTransition


# Agent classes (persons interacting)
AGENT_CLASSES = {"person"}

# Object classes (things that can be interacted with)
OBJECT_CLASSES = {"chair", "couch", "truck", "car", "motorcycle", "refrigerator", 
                  "tv", "sink", "toilet", "bed", "dining table", "suitcase", "umbrella"}


def classify_detections(tracked_result: Dict) -> Tuple[Dict, Dict]:
    """
    Separate detections into agents and objects for Person 2's pipeline.
    
    Returns:
        (agents_dict, objects_dict) where each is {id: (x1,y1,x2,y2)}
    """
    agents = {}
    objects = {}
    
    boxes = tracked_result.get("boxes", [])
    class_names = tracked_result.get("class_names", [])
    track_ids = tracked_result.get("track_ids", [])
    
    for i, (box, class_name, track_id) in enumerate(zip(boxes, class_names, track_ids)):
        if track_id is None:
            continue
            
        obj_id = f"{class_name}_{track_id}"
        box_tuple = tuple(box)
        
        if class_name in AGENT_CLASSES:
            agents[obj_id] = box_tuple
        elif class_name in OBJECT_CLASSES:
            objects[obj_id] = box_tuple
    
    return agents, objects


def run_integrated_pipeline(
    frames_dir: str,
    output_path: str = "output/integrated_results.json",
    confidence: float = 0.36,
    fps: float = 30.0
) -> Dict:
    """
    Run the complete integrated pipeline.
    
    Person 1: Detection + Tracking
    Person 2: Interaction + State
    """
    
    print("=" * 60)
    print("WORLD2DATA INTEGRATED PIPELINE")
    print("=" * 60)
    
    # === PERSON 1: INGEST ===
    frame_paths = get_frame_paths(frames_dir)
    video_info = get_video_info(frames_dir, fps)
    
    print(f"\n[INGEST] Loaded {len(frame_paths)} frames")
    print(f"  Resolution: {video_info['width']}x{video_info['height']}")
    print(f"  Duration: {video_info['duration_seconds']:.2f}s")
    
    # === PERSON 1: DETECTION ===
    print(f"\n[DETECTION] Initializing YOLOv8 (confidence={confidence})")
    detector = YOLODetector(model_path="yolov8n.pt", confidence_threshold=confidence)
    
    # === PERSON 1: TRACKING ===
    print("[TRACKING] Initializing ByteTrack")
    tracker = ByteTracker(
        track_activation_threshold=confidence,
        lost_track_buffer=30,
        frame_rate=int(fps)
    )
    
    # === PERSON 2: INTERACTION ===
    print("[INTERACTION] Initializing IoU triggers")
    triggers: Dict[Tuple[str, str], RollingSpikeTrigger] = {}
    
    # === PERSON 2: STATE ===
    print("[STATE] Initializing state memory")
    state_memory = StateMemory()
    
    # === PROCESS FRAMES ===
    all_frame_results = []
    all_interactions = []
    
    print(f"\n[PROCESSING] Running on {len(frame_paths)} frames...")
    
    for i, frame_path in enumerate(frame_paths):
        timestamp = i / fps
        
        # Person 1: Detect
        detections = detector.detect(frame_path)
        
        # Person 1: Track
        tracked = tracker.update(detections, frame_idx=i, timestamp=timestamp)
        
        # Classify into agents and objects
        agents, objects = classify_detections(tracked)
        
        # Person 2: Check for interactions
        frame_interactions = []
        
        for agent_id, agent_box in agents.items():
            for object_id, object_box in objects.items():
                key = (agent_id, object_id)
                
                # Create trigger if new pair
                if key not in triggers:
                    triggers[key] = RollingSpikeTrigger(
                        baseline_window=8,
                        spike_delta=0.15,
                        min_iou=0.05,
                        cooldown_frames=10,
                        event_window=15
                    )
                
                # Calculate IoU
                iou_value = iou(agent_box, object_box)
                
                # Check for trigger
                trigger_result = triggers[key].step(i, iou_value)
                
                if trigger_result.triggered:
                    # Interaction detected!
                    interaction = {
                        "frame_idx": i,
                        "timestamp": timestamp,
                        "agent_id": agent_id,
                        "object_id": object_id,
                        "iou_value": round(iou_value, 4),
                        "baseline": round(trigger_result.baseline, 4),
                        "delta": round(trigger_result.delta, 4)
                    }
                    frame_interactions.append(interaction)
                    all_interactions.append(interaction)
                    
                    # Update state (simple: interaction means state change)
                    current_state = state_memory.get_state(object_id)
                    new_state = "open" if current_state != "open" else "closed"
                    state_memory.update_state(
                        object_id=object_id,
                        new_state=new_state,
                        frame_idx=i,
                        reason=f"interaction with {agent_id}"
                    )
        
        # Store frame result
        frame_result = {
            "frame_idx": i,
            "timestamp": timestamp,
            "frame_path": frame_path,
            "detections": {
                "boxes": tracked["boxes"],
                "scores": tracked["scores"],
                "class_names": tracked["class_names"],
                "track_ids": tracked["track_ids"]
            },
            "agents": list(agents.keys()),
            "objects": list(objects.keys()),
            "interactions": frame_interactions
        }
        all_frame_results.append(frame_result)
        
        # Progress
        if (i + 1) % 30 == 0 or i == 0:
            n_agents = len(agents)
            n_objects = len(objects)
            print(f"  Frame {i+1}/{len(frame_paths)}: {n_agents} agents, {n_objects} objects")
    
    # Get summaries
    track_summary = tracker.get_track_summary()
    state_history = [
        {
            "object_id": t.object_id,
            "frame_idx": t.frame_idx,
            "before": t.before,
            "after": t.after,
            "reason": t.reason
        }
        for t in state_memory.history
    ]
    
    # Build output
    output = {
        "metadata": {
            "pipeline": "World2Data Integrated Pipeline",
            "components": {
                "person1_ingest": "src/ingest/video_loader.py",
                "person1_detection": "src/detection/yolo_detector.py",
                "person1_tracking": "src/detection/bytetrack_tracker.py",
                "person2_interaction": "src/interaction/iou_trigger.py",
                "person2_state": "src/interaction/state_memory.py"
            },
            "total_frames": len(frame_paths),
            "fps": fps,
            "processed_at": datetime.now().isoformat()
        },
        "video_info": video_info,
        "track_summary": track_summary,
        "interaction_summary": {
            "total_interactions": len(all_interactions),
            "unique_agent_object_pairs": len(triggers)
        },
        "state_transitions": state_history,
        "interactions": all_interactions,
        "frame_data": all_frame_results
    }
    
    # Save
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\n{'=' * 60}")
    print("PIPELINE COMPLETE")
    print(f"{'=' * 60}")
    print(f"Frames processed: {len(frame_paths)}")
    print(f"Tracks: {track_summary['total_tracks']} ({track_summary['confirmed_tracks']} confirmed)")
    print(f"Interactions detected: {len(all_interactions)}")
    print(f"State transitions: {len(state_history)}")
    print(f"Output: {output_file}")
    
    return output


if __name__ == "__main__":
    frames_dir = sys.argv[1] if len(sys.argv) > 1 else "frames"
    output_path = sys.argv[2] if len(sys.argv) > 2 else "output/integrated_results.json"
    
    run_integrated_pipeline(
        frames_dir=frames_dir,
        output_path=output_path,
        confidence=0.36,
        fps=30.0
    )

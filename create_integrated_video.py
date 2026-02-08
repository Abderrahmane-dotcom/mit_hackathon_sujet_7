"""
Create Integrated Annotated Video
Shows: Detections + Tracks + Interactions + State Changes
"""

import sys
import json
import cv2
from pathlib import Path

# Color map
COLORS = {
    'person': (0, 255, 0),       # Green - agents
    'motorcycle': (255, 165, 0),  # Orange
    'car': (0, 0, 255),          # Red
    'truck': (255, 255, 0),      # Cyan
    'chair': (255, 0, 255),      # Magenta
    'suitcase': (0, 255, 255),   # Yellow
    'umbrella': (128, 0, 255),   # Purple
    'tv': (255, 128, 0),         # Blue-ish
    'refrigerator': (128, 255, 0),
    'sink': (0, 128, 255),
    'default': (128, 128, 128)
}

INTERACTION_COLOR = (0, 0, 255)   # Red for interactions
STATE_COLOR = (255, 255, 0)       # Cyan for state info


def get_color(class_name):
    return COLORS.get(class_name, COLORS['default'])


def create_annotated_video(
    results_path: str = "output/integrated_results.json",
    output_path: str = "output/integrated_annotated_video.mp4",
):
    """Generate an annotated video from integrated pipeline results."""
    results_file = Path(results_path)
    if not results_file.exists():
        print(f"Error: Results file not found: {results_file}")
        print("Run the integrated pipeline first to generate results.")
        return

    with open(results_file) as f:
        data = json.load(f)

    print(f"Creating annotated video from {len(data['frame_data'])} frames...")
    print(f"Interactions to show: {len(data['interactions'])}")
    print(f"State transitions: {len(data['state_transitions'])}")

    # Build interaction lookup
    interaction_frames = {}
    for interaction in data['interactions']:
        frame_idx = interaction['frame_idx']
        if frame_idx not in interaction_frames:
            interaction_frames[frame_idx] = []
        interaction_frames[frame_idx].append(interaction)

    # Build state lookup (current state at each frame)
    state_at_frame = {}
    current_states = {}
    for transition in data['state_transitions']:
        frame_idx = transition['frame_idx']
        obj_id = transition['object_id']
        current_states[obj_id] = transition['after']
        state_at_frame[frame_idx] = dict(current_states)

    # Get first frame for dimensions
    first_frame_path = data['frame_data'][0]['frame_path']
    first_frame = cv2.imread(first_frame_path)
    if first_frame is None:
        print(f"Error: Cannot read first frame: {first_frame_path}")
        print("Make sure the frames directory still exists with the original images.")
        return
    height, width = first_frame.shape[:2]
    fps = data.get("metadata", {}).get("fps", 30)

    # Create video writer
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    video_writer = cv2.VideoWriter(output_path, fourcc, int(fps), (width, height))

    # Track which frames had recent interactions (for highlighting)
    recent_interaction_frames = set()
    for interaction in data['interactions']:
        start = interaction['frame_idx']
        for f in range(start, min(start + 15, len(data['frame_data']))):
            recent_interaction_frames.add(f)

    # Process all frames
    for frame_data in data['frame_data']:
        frame_idx = frame_data['frame_idx']
        frame_path = frame_data['frame_path']
        timestamp = frame_data['timestamp']

        img = cv2.imread(frame_path)
        if img is None:
            continue

        # Draw detections
        detections = frame_data['detections']
        for box, score, class_name, track_id in zip(
            detections['boxes'],
            detections['scores'],
            detections['class_names'],
            detections['track_ids']
        ):
            if track_id is None:
                continue

            x1, y1, x2, y2 = [int(c) for c in box]

            is_agent = class_name in {'person'}
            color = get_color(class_name)
            thickness = 3 if is_agent else 2

            # Draw box
            cv2.rectangle(img, (x1, y1), (x2, y2), color, thickness)

            # Draw label
            label = f"#{track_id} {class_name} {score:.2f}"
            label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)[0]
            cv2.rectangle(img, (x1, y1 - label_size[1] - 10), (x1 + label_size[0] + 5, y1), color, -1)
            cv2.putText(img, label, (x1 + 2, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

        # Highlight interactions
        if frame_idx in interaction_frames:
            for interaction in interaction_frames[frame_idx]:
                text = f"INTERACTION: {interaction['agent_id']} -> {interaction['object_id']}"
                cv2.rectangle(img, (10, height - 80), (width - 10, height - 40), INTERACTION_COLOR, -1)
                cv2.putText(img, text, (20, height - 50), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        # Draw interaction indicator (red border during interaction windows)
        if frame_idx in recent_interaction_frames:
            cv2.rectangle(img, (5, 5), (width - 5, height - 5), INTERACTION_COLOR, 4)

        # Show current states in corner
        y_offset = 80
        if state_at_frame:
            recent_states = {}
            for f in range(frame_idx, -1, -1):
                if f in state_at_frame:
                    recent_states = state_at_frame[f]
                    break

            if recent_states:
                cv2.rectangle(img, (width - 280, 50), (width - 10, 50 + len(recent_states) * 25 + 10), (0, 0, 0), -1)
                cv2.putText(img, "OBJECT STATES:", (width - 270, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.5, STATE_COLOR, 1)

                for obj_id, state in recent_states.items():
                    short_id = obj_id.split('_')[0][:10]
                    state_text = f"{short_id}: {state.upper()}"
                    cv2.putText(img, state_text, (width - 270, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                    y_offset += 22

        # Frame info header
        info = f"Frame {frame_idx} | t={timestamp:.2f}s | Agents: {len(frame_data['agents'])} | Objects: {len(frame_data['objects'])}"
        cv2.rectangle(img, (5, 5), (550, 40), (0, 0, 0), -1)
        cv2.putText(img, info, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        video_writer.write(img)

        if (frame_idx + 1) % 30 == 0:
            print(f"  Processed {frame_idx + 1}/{len(data['frame_data'])} frames...")

    video_writer.release()

    print(f"\n{'=' * 50}")
    print("INTEGRATED VIDEO CREATED")
    print(f"{'=' * 50}")
    print(f"Output: {output_path}")
    print(f"Duration: {len(data['frame_data']) / fps:.2f}s at {fps} fps")
    print("Features shown:")
    print("  - Object detections with track IDs")
    print("  - Agent/Object classification")
    print("  - Interaction events (red border + banner)")
    print("  - Object state panel (top-right corner)")


if __name__ == "__main__":
    results = sys.argv[1] if len(sys.argv) > 1 else "output/integrated_results.json"
    output = sys.argv[2] if len(sys.argv) > 2 else "output/integrated_annotated_video.mp4"
    create_annotated_video(results, output)

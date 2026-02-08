"""Streamlit app for visualizing World2Data pipeline results."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

import streamlit as st
from PIL import Image, ImageDraw

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.logging.schema import ensure_action_log
from src.logging.json_logger import write_action_log


COLORS = {
    "person": (0, 255, 0),
    "motorcycle": (255, 165, 0),
    "car": (0, 0, 255),
    "truck": (255, 255, 0),
    "chair": (255, 0, 255),
    "suitcase": (0, 255, 255),
    "umbrella": (128, 0, 255),
    "tv": (255, 128, 0),
    "refrigerator": (128, 255, 0),
    "sink": (0, 128, 255),
    "default": (160, 160, 160),
}


def resolve_frame_path(frame_path: str, video_info: Dict[str, Any]) -> Path:
    if not frame_path:
        return Path()

    raw_path = Path(frame_path)
    if raw_path.is_absolute() and raw_path.exists():
        return raw_path

    candidate = PROJECT_ROOT / raw_path
    if candidate.exists():
        return candidate

    frames_dir = video_info.get("frames_dir")
    if frames_dir:
        candidate = PROJECT_ROOT / frames_dir / raw_path.name
        if candidate.exists():
            return candidate

    return PROJECT_ROOT / raw_path


def get_color(class_name: str) -> Tuple[int, int, int]:
    return COLORS.get(class_name, COLORS["default"])


def draw_overlays(
    image: Image.Image,
    frame_data: Dict[str, Any],
    show_untracked: bool,
    show_labels: bool,
    highlight_interactions: bool,
) -> Image.Image:
    img = image.copy()
    draw = ImageDraw.Draw(img)

    detections = frame_data.get("detections", {})
    boxes = detections.get("boxes", [])
    scores = detections.get("scores", [])
    class_names = detections.get("class_names", [])
    track_ids = detections.get("track_ids", [])

    for box, score, class_name, track_id in zip(boxes, scores, class_names, track_ids):
        if track_id is None and not show_untracked:
            continue

        x1, y1, x2, y2 = [int(c) for c in box]
        color = get_color(class_name)
        draw.rectangle([x1, y1, x2, y2], outline=color, width=2)

        if show_labels:
            track_text = "?" if track_id is None else str(track_id)
            label = f"#{track_text} {class_name} {score:.2f}"
            text_pos = (x1 + 2, max(0, y1 - 14))
            draw.text(text_pos, label, fill=color)

    if highlight_interactions and frame_data.get("interactions"):
        banner = "INTERACTION DETECTED"
        draw.rectangle([10, 10, 10 + 300, 36], fill=(255, 0, 0))
        draw.text((16, 14), banner, fill=(255, 255, 255))

    return img


def load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def select_frame(frames: List[Dict[str, Any]]) -> Dict[str, Any]:
    frame_idx = st.slider("Frame index", 0, max(0, len(frames) - 1), 0)
    return frames[frame_idx]


def render_summary(action_log: Dict[str, Any]) -> None:
    video_info = action_log.get("video_info", {})
    track_summary = action_log.get("track_summary", {})
    interaction_summary = action_log.get("interaction_summary", {})
    state_transitions = action_log.get("state_transitions", [])

    st.subheader("Summary")
    st.write(
        {
            "frames": video_info.get("frame_count"),
            "fps": video_info.get("fps"),
            "resolution": f"{video_info.get('width')}x{video_info.get('height')}",
            "tracks": track_summary.get("total_tracks"),
            "confirmed_tracks": track_summary.get("confirmed_tracks"),
            "interactions": interaction_summary.get("total_interactions"),
            "state_transitions": len(state_transitions),
        }
    )


def run_pipeline(frames_dir: str, output_path: str, confidence: float, fps: float) -> Dict[str, Any]:
    try:
        from integrated_pipeline import run_integrated_pipeline
    except Exception as exc:
        raise RuntimeError(
            "Failed to import integrated_pipeline. Ensure dependencies are installed."
        ) from exc

    return run_integrated_pipeline(
        frames_dir=frames_dir,
        output_path=output_path,
        confidence=confidence,
        fps=fps,
    )


st.set_page_config(page_title="World2Data Viewer", layout="wide")

st.title("World2Data Streamlit Viewer")

with st.sidebar:
    st.header("Data")
    mode = st.radio("Mode", ["Load results", "Run pipeline"], index=0)

    results_path = st.text_input(
        "Results JSON",
        value=str(PROJECT_ROOT / "output" / "integrated_results.json"),
    )

    frames_dir = st.text_input("Frames directory", value=str(PROJECT_ROOT / "frames"))
    confidence = st.slider("Confidence", 0.1, 0.9, 0.36, 0.01)
    fps = st.number_input("FPS", min_value=1.0, max_value=120.0, value=30.0, step=1.0)

    save_action_log = st.checkbox("Write action log", value=True)
    action_log_path = st.text_input(
        "Action log output",
        value=str(PROJECT_ROOT / "output" / "action_log.json"),
    )

    run_clicked = st.button("Run")

    st.header("Media")
    show_video = st.checkbox("Show annotated video", value=True)
    video_path = st.text_input(
        "Annotated video path",
        value=str(PROJECT_ROOT / "output" / "integrated_annotated_video.mp4"),
    )

    st.header("Overlay")
    show_labels = st.checkbox("Show labels", value=True)
    show_untracked = st.checkbox("Show untracked boxes", value=False)
    highlight_interactions = st.checkbox("Highlight interactions", value=True)


data: Dict[str, Any] | None = None

if run_clicked and mode == "Run pipeline":
    with st.spinner("Running pipeline..."):
        try:
            data = run_pipeline(frames_dir, results_path, confidence, fps)
        except Exception as exc:
            st.error(str(exc))
            st.stop()

if data is None:
    results_file = Path(results_path)
    if not results_file.exists():
        st.error("Results JSON not found. Run the pipeline or update the path.")
        st.stop()
    data = load_json(results_file)

action_log = ensure_action_log(data)
frames = action_log.get("frames", [])
if not frames:
    st.warning("No frames available in results.")
    st.stop()

if save_action_log:
    try:
        write_action_log(action_log, action_log_path)
    except Exception as exc:
        st.error(f"Failed to write action log: {exc}")

render_summary(action_log)

left, right = st.columns([2, 1])

with left:
    st.subheader("Frame viewer")
    frame = select_frame(frames)
    frame_path = resolve_frame_path(frame.get("frame_path"), action_log.get("video_info", {}))

    if not frame_path.exists():
        st.error(f"Frame not found: {frame_path}")
    else:
        image = Image.open(frame_path).convert("RGB")
        overlay = draw_overlays(
            image,
            frame,
            show_untracked=show_untracked,
            show_labels=show_labels,
            highlight_interactions=highlight_interactions,
        )
        st.image(overlay, use_container_width=True)

with right:
    st.subheader("Frame details")
    st.write(
        {
            "frame_idx": frame.get("frame_idx"),
            "timestamp": frame.get("timestamp"),
            "agents": frame.get("agents"),
            "objects": frame.get("objects"),
            "interaction_count": len(frame.get("interactions", [])),
        }
    )

    detections = frame.get("detections", {})
    if detections.get("boxes"):
        rows = []
        for box, score, class_name, track_id in zip(
            detections.get("boxes", []),
            detections.get("scores", []),
            detections.get("class_names", []),
            detections.get("track_ids", []),
        ):
            rows.append(
                {
                    "class": class_name,
                    "score": round(score, 3),
                    "track_id": track_id,
                    "box": [round(v, 1) for v in box],
                }
            )
        st.dataframe(rows, use_container_width=True, height=240)

st.subheader("Interactions")
interactions = action_log.get("interactions", [])
if interactions:
    st.dataframe(interactions, use_container_width=True, height=240)
else:
    st.info("No interactions detected.")

st.subheader("State transitions")
state_transitions = action_log.get("state_transitions", [])
if state_transitions:
    st.dataframe(state_transitions, use_container_width=True, height=240)
else:
    st.info("No state transitions recorded.")

if show_video:
    video_file = Path(video_path)
    if video_file.exists():
        st.subheader("Annotated video")
        st.video(str(video_file))
    else:
        st.info("Annotated video not found. Generate it to enable playback.")

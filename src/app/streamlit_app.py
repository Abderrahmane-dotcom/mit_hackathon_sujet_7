"""Streamlit app for visualizing World2Data pipeline results."""

from __future__ import annotations

import json
import sys
import cv2
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Tuple

import streamlit as st
from PIL import Image, ImageDraw

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.logging.schema import ensure_action_log
from src.logging.json_logger import write_action_log
from src.ingest.video_loader import VideoLoader, get_frame_paths


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


def extract_frames_from_video(
    video_file: Any,
    output_dir: str,
    fps: float = 1.0,
    max_frames: int = None
) -> Tuple[List[str], Dict[str, Any]]:
    """
    Extract frames from uploaded video file.
    
    Args:
        video_file: Streamlit UploadedFile object
        output_dir: Directory to save extracted frames
        fps: Frame extraction rate (1.0 = extract 1 frame per second)
        max_frames: Maximum number of frames to extract
    
    Returns:
        (list of frame paths, video metadata)
    """
    # Save uploaded file to temp location
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
        tmp.write(video_file.getbuffer())
        tmp_path = tmp.name
    
    try:
        # Load video
        loader = VideoLoader(tmp_path)
        info = loader.get_info()
        
        # Create output directory
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Calculate frame skip rate
        video_fps = info["fps"]
        frame_skip = max(1, int(video_fps / fps))
        
        # Extract frames
        saved_paths = []
        frame_count = 0
        
        for frame_num, timestamp, frame in loader.frame_iterator():
            if frame_num % frame_skip == 0:
                if max_frames and frame_count >= max_frames:
                    break
                
                # Save frame as JPG
                filename = f"frame_{frame_count:06d}.jpg"
                filepath = output_path / filename
                cv2.imwrite(str(filepath), frame)
                saved_paths.append(str(filepath))
                frame_count += 1
        
        return saved_paths, info
    
    finally:
        # Clean up temp file
        Path(tmp_path).unlink(missing_ok=True)


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

# Initialize session state for frames directory
if "frames_dir" not in st.session_state:
    st.session_state.frames_dir = str(PROJECT_ROOT / "frames")
if "video_uploaded" not in st.session_state:
    st.session_state.video_uploaded = False

with st.sidebar:
    st.header("📹 Video Input")
    
    # Drag and drop video upload
    uploaded_video = st.file_uploader(
        "Drag & drop your video here or click to browse",
        type=["mp4", "avi", "mov", "mkv", "flv"]
    )
    
    if uploaded_video is not None:
        st.success(f"✅ Video loaded: {uploaded_video.name}")
        
        col1, col2 = st.columns(2)
        with col1:
            extraction_fps = st.slider("Extract @ FPS", 0.5, 30.0, 1.0, 0.5)
        with col2:
            max_frames = st.number_input("Max frames", min_value=1, max_value=1000, value=100)
        
        if st.button("🎬 Extract Frames & Load", use_container_width=True):
            with st.spinner("Extracting frames from video..."):
                try:
                    # Create frames directory for this upload
                    frames_dir = str(PROJECT_ROOT / f"frames_uploaded_{uploaded_video.name.replace('.', '_')}")
                    
                    frame_paths, video_info = extract_frames_from_video(
                        uploaded_video,
                        frames_dir,
                        fps=extraction_fps,
                        max_frames=max_frames
                    )
                    
                    st.session_state.frames_dir = frames_dir
                    st.session_state.video_uploaded = True
                    st.session_state.video_info = video_info
                    st.session_state.extracted_frames = frame_paths
                    
                    st.success(f"✅ Extracted {len(frame_paths)} frames from video!")
                    st.info(
                        f"📊 Video Info:\n"
                        f"- Resolution: {video_info['width']}×{video_info['height']}\n"
                        f"- Original FPS: {video_info['fps']:.1f}\n"
                        f"- Duration: {video_info['duration_seconds']:.2f}s\n"
                        f"- Total frames in video: {video_info['frame_count']}"
                    )
                except Exception as e:
                    st.error(f"❌ Error extracting frames: {str(e)}")
    
    st.divider()
    st.header("Data")
    mode = st.radio("Mode", ["Load results", "Run pipeline"], index=0)

    if st.session_state.video_uploaded:
        results_path = st.text_input(
            "Results JSON",
            value=str(PROJECT_ROOT / "output" / "integrated_results.json"),
        )
        frames_dir = st.session_state.frames_dir
        st.info(f"📁 Using extracted frames from upload")
    else:
        results_path = st.text_input(
            "Results JSON",
            value=str(PROJECT_ROOT / "output" / "integrated_results.json"),
        )
        frames_dir = st.text_input("Frames directory", value=str(PROJECT_ROOT / "frames"))
        st.session_state.frames_dir = frames_dir
    
    confidence = st.slider("Confidence", 0.1, 0.9, 0.36, 0.01)
    fps_setting = st.number_input("FPS", min_value=1.0, max_value=120.0, value=30.0, step=1.0)

    save_action_log = st.checkbox("Write action log", value=True)
    action_log_path = st.text_input(
        "Action log output",
        value=str(PROJECT_ROOT / "output" / "action_log.json"),
    )

    run_clicked = st.button("▶️ Run Pipeline", use_container_width=True)

    st.header("Media")
    show_video = st.checkbox("Show annotated video", value=False)
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
            data = run_pipeline(st.session_state.frames_dir, results_path, confidence, fps_setting)
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

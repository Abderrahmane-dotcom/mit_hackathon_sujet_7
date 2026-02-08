"""
Streamlit app for SAM + LFM Video Analysis
Drag-and-drop video upload with automatic processing
"""

import os
import sys
import json
import tempfile
from pathlib import Path
from typing import Optional

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Configuration
VIDEO_DIR = PROJECT_ROOT / "video"
OUTPUT_DIR = PROJECT_ROOT / "output"

# Ensure directories exist
VIDEO_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def save_upload_to_video_folder(uploaded_file) -> Optional[str]:
    """
    Save uploaded file to the video folder.
    Returns: Path to the saved video file
    """
    if uploaded_file is None:
        return None
    
    # Save to video directory
    video_path = VIDEO_DIR / uploaded_file.name
    
    with open(video_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    return str(video_path)


def run_sam_lfm_pipeline(video_path: str) -> Optional[str]:
    """
    Run the SAM + LFM analysis pipeline.
    
    Returns:
        Path to the output JSON file, or None if error
    """
    try:
        # Import the processing script
        import sys
        sys.path.insert(0, str(PROJECT_ROOT))
        
        # Clear previous frames/crops
        import shutil
        for dir_path in [PROJECT_ROOT / "frames", 
                        PROJECT_ROOT / "crops", 
                        PROJECT_ROOT / "the_cropped_frames"]:
            if dir_path.exists():
                shutil.rmtree(dir_path)
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # Import the main script modules
        from video_1fps_sam_lfm_print_result import (
            reset_dir, extract_json, mask_to_bbox, mask_area,
            FRAMES_DIR, CROPS_DIR, ANNOTATED_DIR,
            NAVIGATION_PROMPT, get_video_path, save_results
        )
        
        import cv2
        import numpy as np
        from PIL import Image
        import torch
        from transformers import pipeline
        
        # Reset folders
        reset_dir(FRAMES_DIR)
        reset_dir(CROPS_DIR)
        reset_dir(ANNOTATED_DIR)
        
        st.write("✅ Folders reset")
        
        # Extract frames (1 FPS)
        status_text = st.empty()
        status_text.text("🎬 Extracting frames at 1 FPS...")
        os.system(f'ffmpeg -y -i "{video_path}" -vf fps=1 "{FRAMES_DIR}/frame_%04d.jpg" 2>/dev/null')
        status_text.text("✅ Frames extracted")
        
        # Load SAM
        status_text.text("🔄 Loading SAM model...")
        sam = pipeline(
            "mask-generation",
            model="facebook/sam-vit-base",
            device=0 if torch.cuda.is_available() else -1
        )
        
        # Load LFM
        status_text.text("🔄 Loading LFM model...")
        vlm = pipeline(
            "image-text-to-text",
            model="LiquidAI/LFM2.5-VL-1.6B",
            device=0 if torch.cuda.is_available() else -1
        )
        
        status_text.text("✅ SAM + LFM models loaded")
        
        # Process frames
        image_files = sorted(f for f in os.listdir(FRAMES_DIR) if f.endswith(".jpg"))
        results = []
        
        progress_bar = st.progress(0)
        frame_status = st.empty()
        
        for t, frame_name in enumerate(image_files):
            frame_path = os.path.join(FRAMES_DIR, frame_name)
            frame_bgr = cv2.imread(frame_path)
            frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
            frame_pil = Image.fromarray(frame_rgb)
            
            sam_output = sam(frame_pil)
            annotated = frame_bgr.copy()
            objects_in_frame = []
            
            for idx, mask in enumerate(sam_output["masks"]):
                if mask_area(mask) < 600:
                    continue
                
                bbox = mask_to_bbox(mask)
                if bbox is None:
                    continue
                
                x1, y1, x2, y2 = bbox
                crop = frame_rgb[y1:y2, x1:x2]
                if crop.size == 0:
                    continue
                
                crop_path = f"{CROPS_DIR}/t{t}_obj{idx}.jpg"
                cv2.imwrite(crop_path, cv2.cvtColor(crop, cv2.COLOR_RGB2BGR))
                
                messages = [{
                    "role": "user",
                    "content": [
                        {"type": "image", "url": crop_path},
                        {"type": "text", "text": NAVIGATION_PROMPT}
                    ]
                }]
                
                output = vlm(
                    text=messages,
                    max_new_tokens=120,
                    max_length=None,
                    do_sample=False,
                    temperature=0.0,
                    return_full_text=False
                )[0]["generated_text"]
                
                parsed = extract_json(output)
                if parsed is None:
                    continue
                
                cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(
                    annotated,
                    f"{parsed['type']} | {parsed['state']}",
                    (x1, max(y1 - 5, 15)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.4,
                    (0, 255, 0),
                    1
                )
                
                objects_in_frame.append({
                    "bbox": [x1, y1, x2, y2],
                    "type": parsed["type"],
                    "state": parsed["state"]
                })
            
            out_path = f"{ANNOTATED_DIR}/frame_{t:04d}.jpg"
            cv2.imwrite(out_path, annotated)
            
            frame_result = {
                "time_sec": t,
                "frame": frame_path,
                "objects": objects_in_frame
            }
            results.append(frame_result)
            
            # Update progress
            progress = (t + 1) / len(image_files)
            progress_bar.progress(progress)
            frame_status.text(f"⏳ Processing frame {t + 1}/{len(image_files)}")
        
        frame_status.text(f"✅ Processed {len(image_files)} frames")
        
        # Save results
        status_text.text("💾 Saving results to JSON...")
        output_file = save_results(results, video_path, str(OUTPUT_DIR))
        status_text.text("✅ Results saved successfully!")
        
        return output_file
        
    except Exception as e:
        st.error(f"❌ Error running pipeline: {str(e)}")
        import traceback
        st.error(traceback.format_exc())
        return None


def display_results(json_file: str):
    """Display the results from the JSON file."""
    try:
        with open(json_file, 'r') as f:
            results = json.load(f)
        
        st.subheader("📊 Analysis Results")
        
        # Summary
        total_frames = len(results)
        total_objects = sum(len(frame["objects"]) for frame in results)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Frames", total_frames)
        with col2:
            st.metric("Total Objects Detected", total_objects)
        with col3:
            st.metric("Avg Objects per Frame", f"{total_objects / max(1, total_frames):.2f}")
        
        st.divider()
        
        # Frame-by-frame results
        st.subheader("Frame-by-Frame Analysis")
        
        for frame_data in results:
            time_sec = frame_data["time_sec"]
            objects = frame_data["objects"]
            
            with st.expander(f"⏱️ Frame at {time_sec}s - {len(objects)} objects"):
                if objects:
                    for obj_idx, obj in enumerate(objects):
                        st.write(f"**Object {obj_idx + 1}:**")
                        st.json({
                            "Type": obj["type"],
                            "State": obj["state"],
                            "BBox": f"({obj['bbox'][0]}, {obj['bbox'][1]}) to ({obj['bbox'][2]}, {obj['bbox'][3]})"
                        })
                else:
                    st.info("No objects detected in this frame")
        
        # Download button
        st.divider()
        with open(json_file, 'r') as f:
            json_content = f.read()
        
        st.download_button(
            label="📥 Download Results JSON",
            data=json_content,
            file_name=Path(json_file).name,
            mime="application/json"
        )
        
    except Exception as e:
        st.error(f"❌ Error displaying results: {str(e)}")


# ============================================
# Streamlit App
# ============================================

st.set_page_config(page_title="SAM + LFM Video Analysis", layout="wide")

st.title("🎬 SAM + LFM Video Analysis")
st.write("Upload a video to analyze with Segment Anything Model (SAM) and LFM Vision Language Model")

# Initialize session state
if "video_uploaded" not in st.session_state:
    st.session_state.video_uploaded = False
if "processing" not in st.session_state:
    st.session_state.processing = False
if "output_file" not in st.session_state:
    st.session_state.output_file = None

# Sidebar
with st.sidebar:
    st.header("📹 Video Upload")
    
    uploaded_file = st.file_uploader(
        "Drag & drop your video here or click to browse",
        type=["mp4", "avi", "mov", "mkv", "flv"],
        help="Upload a video file to analyze. Supported formats: mp4, avi, mov, mkv, flv"
    )
    
    if uploaded_file is not None:
        st.success(f"✅ Video loaded: {uploaded_file.name}")
        st.session_state.video_uploaded = True
        
        if st.button("🚀 Run SAM + LFM Analysis", use_container_width=True):
            st.session_state.processing = True
            
            with st.spinner("Processing video..."):
                # Save to video folder
                st.write("💾 Saving video to folder...")
                video_path = save_upload_to_video_folder(uploaded_file)
                
                if video_path:
                    st.write(f"✅ Video saved to: {video_path}")
                    
                    # Run pipeline
                    output_file = run_sam_lfm_pipeline(video_path)
                    
                    if output_file:
                        st.session_state.output_file = output_file
                        st.success("✅ Analysis complete!")
                    else:
                        st.error("❌ Failed to run analysis pipeline")
                else:
                    st.error("❌ Failed to save video")
            
            st.session_state.processing = False
    else:
        st.info("👆 Upload a video to get started")
    
    st.divider()
    st.subheader("ℹ️ How it works")
    st.write("""
    1. **Upload** a video file
    2. **Extract** frames at 1 FPS
    3. **Detect** regions with SAM
    4. **Analyze** with LFM vision model
    5. **Get** JSON results with object types and states
    """)

# Main content
if st.session_state.output_file and Path(st.session_state.output_file).exists():
    display_results(st.session_state.output_file)
elif st.session_state.video_uploaded and not st.session_state.processing:
    st.info("👈 Click the 'Run Analysis' button to start processing")
else:
    st.info("👈 Upload a video in the sidebar to begin")

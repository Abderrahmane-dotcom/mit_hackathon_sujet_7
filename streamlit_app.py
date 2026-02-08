# =========================================
# STREAMLIT APP
# VIDEO → 1 FPS → SAM → CROPS → LFM → JSON
# =========================================

import os
import json
import re
import shutil
import subprocess
import cv2
import numpy as np
from PIL import Image
import torch
import streamlit as st
from transformers import pipeline

# --------------------
# Paths
# --------------------
VIDEO_DIR = "./video"
FRAMES_DIR = "./frames"
CROPS_DIR = "./crops"
ANNOTATED_DIR = "./the_cropped_frames"
RESULTS_DIR = "./results"

FINAL_JSON_PATH = os.path.join(RESULTS_DIR, "navigation_results.json")

# --------------------
# Utils
# --------------------
def reset_dir(path):
    if os.path.exists(path):
        shutil.rmtree(path)
    os.makedirs(path, exist_ok=True)

def extract_json(text):
    if not isinstance(text, str):
        return None
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return None
    try:
        return json.loads(match.group())
    except:
        return None

def mask_to_bbox(mask):
    ys, xs = np.where(mask)
    if len(xs) == 0 or len(ys) == 0:
        return None
    return int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())

def mask_area(mask):
    return int(mask.sum())

# --------------------
# Streamlit UI
# --------------------
st.set_page_config(layout="wide")
st.title("🎥 Video → SAM → LFM Navigation Analyzer")

uploaded_video = st.file_uploader(
    "Upload a navigation video",
    type=["mp4", "avi", "mov"]
)

start_btn = st.button("🚀 Start Processing", disabled=uploaded_video is None)

# --------------------
# Main processing
# --------------------
if start_btn:

    # Reset folders
    for d in [VIDEO_DIR, FRAMES_DIR, CROPS_DIR, ANNOTATED_DIR, RESULTS_DIR]:
        reset_dir(d)

    # Save uploaded video
    video_path = os.path.join(VIDEO_DIR, uploaded_video.name)
    with open(video_path, "wb") as f:
        f.write(uploaded_video.read())

    st.success("✅ Video uploaded")

    # Extract frames (1 FPS)
    st.info("⏳ Extracting frames...")
    subprocess.run(
        f'ffmpeg -y -i "{video_path}" -vf fps=1 "{FRAMES_DIR}/frame_%04d.jpg"',
        shell=True,
        check=True
    )
    st.success("✅ Frames extracted")

    # Load models (cached)
    @st.cache_resource
    def load_models():
        sam_model = pipeline(
            "mask-generation",
            model="facebook/sam-vit-base",
            device=0 if torch.cuda.is_available() else -1
        )
        vlm_model = pipeline(
            "image-text-to-text",
            model="LiquidAI/LFM2.5-VL-1.6B",
            device=0 if torch.cuda.is_available() else -1
        )
        return sam_model, vlm_model

    with st.spinner("🔄 Loading models..."):
        sam, vlm = load_models()

    st.success("✅ SAM + LFM loaded")

    NAVIGATION_PROMPT = """
You are analyzing a CROPPED REGION extracted from a larger navigation scene.

This image shows only PART of an object.

Identify:
- object type: door | handle | drawer | passage | obstacle | sign
- object state:
  - door: closed | slightly_open | open
  - handle: visible | reachable | grasped | turned
  - drawer: closed | partially_open | open
  - passage: free | potentially_blocked | forbidden
  - obstacle: blocking | partially_blocking | non_blocking
  - sign: forbidden_access

Rules:
- Output JSON ONLY
- No explanations
- No markdown

ANSWER_JSON:
{
  "type": "string",
  "state": "string"
}
"""

    image_files = sorted(f for f in os.listdir(FRAMES_DIR) if f.endswith(".jpg"))
    progress = st.progress(0)

    final_results = []

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

        final_results.append(frame_result)
        progress.progress((t + 1) / len(image_files))

    # Save final JSON
    with open(FINAL_JSON_PATH, "w") as f:
        json.dump(final_results, f, indent=2)

    st.success("✅ Processing complete")

    # Outputs
    st.subheader("📦 Final Result")
    st.json(final_results)

    with open(FINAL_JSON_PATH, "rb") as f:
        st.download_button(
            "⬇️ Download result JSON",
            f,
            file_name="navigation_results.json",
            mime="application/json"
        )

    st.subheader("🖼️ Annotated Frames")
    st.image(
        sorted(os.path.join(ANNOTATED_DIR, f) for f in os.listdir(ANNOTATED_DIR)),
        width=400
    )

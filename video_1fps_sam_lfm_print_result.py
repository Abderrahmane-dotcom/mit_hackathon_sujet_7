# =========================================
# VIDEO → 1 FPS → SAM → CROPS → LFM → JSON
# LOCAL VERSION (WORKING, LFM-COMPATIBLE)
# =========================================

import os
import json
import re
import shutil
import cv2
import numpy as np
from PIL import Image
import torch
from transformers import pipeline

# --------------------
# Paths
# --------------------
VIDEO_DIR = "./video"
FRAMES_DIR = "./frames"
CROPS_DIR = "./crops"
ANNOTATED_DIR = "./the_cropped_frames"

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
# Reset folders
# --------------------
reset_dir(FRAMES_DIR)
reset_dir(CROPS_DIR)
reset_dir(ANNOTATED_DIR)

print("✅ Folders reset")

# --------------------
# Locate video
# --------------------
videos = [f for f in os.listdir(VIDEO_DIR) if f.lower().endswith((".mp4", ".avi", ".mov"))]
assert len(videos) == 1, "❌ Put exactly ONE video in ./video"
video_path = os.path.join(VIDEO_DIR, videos[0])

# --------------------
# Extract frames (1 FPS)
# --------------------
os.system(f'ffmpeg -y -i "{video_path}" -vf fps=1 "{FRAMES_DIR}/frame_%04d.jpg"')
print("✅ Frames extracted")

# --------------------
# Load SAM
# --------------------
sam = pipeline(
    "mask-generation",
    model="facebook/sam-vit-base",
    device=0 if torch.cuda.is_available() else -1
)

# --------------------
# Load LFM (THE ONLY CORRECT WAY)
# --------------------
vlm = pipeline(
    "image-text-to-text",
    model="LiquidAI/LFM2.5-VL-1.6B",
    device=0 if torch.cuda.is_available() else -1
)

print("✅ SAM + LFM loaded")

# --------------------
# Prompt
# --------------------
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

# --------------------
# Process frames
# --------------------
image_files = sorted(f for f in os.listdir(FRAMES_DIR) if f.endswith(".jpg"))

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

    print(json.dumps({
        "time_sec": t,
        "frame": frame_path,
        "objects": objects_in_frame
    }, indent=2))
    print("-" * 80)

print("✅ Processing complete")

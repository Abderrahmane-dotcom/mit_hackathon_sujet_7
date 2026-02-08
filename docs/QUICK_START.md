# 🎯 Quick Start: Drag & Drop Video

## The Easiest Way to Process Videos

### 🚀 In 4 Simple Steps:

**1. Run the app:**
```bash
streamlit run src/app/streamlit_app.py
```

**2. Upload your video:**
- Drag & drop into the **📹 Video Input** section
- Or click to browse and select

**3. Configure & Extract:**
- Set **Extract @ FPS** (1 FPS recommended for quick testing)
- Set **Max frames** (50-100 for testing, more for full analysis)
- Click **🎬 Extract Frames & Load**

**4. Run & View:**
- Adjust detection confidence
- Click **▶️ Run Pipeline**
- View results, interactions, and state transitions

---

## 📊 What You Get

✅ Automatic frame extraction from any video
✅ Real-time video metadata display
✅ Frame-by-frame detection visualization
✅ Interaction detection and state tracking
✅ Complete analysis pipeline in seconds

---

## 🎬 Video Format Support

| Format | Extension | Status |
|--------|-----------|--------|
| MP4    | .mp4      | ✅ Supported |
| AVI    | .avi      | ✅ Supported |
| MOV    | .mov      | ✅ Supported |
| Matroska | .mkv    | ✅ Supported |
| Flash Video | .flv | ✅ Supported |

---

## ⚡ Performance Guide

| Scenario | FPS | Max Frames | Time |
|----------|-----|-----------|------|
| Quick Test | 1.0 | 50 | ~30 seconds |
| Standard | 5.0 | 100 | ~2 minutes |
| Detailed | 10.0 | 200 | ~5 minutes |
| Full | 30.0 | ∞ | Depends on video |

---

## 🔧 Advanced Features

### Manual Frame Extraction (if needed)
```python
from src.ingest.video_loader import VideoLoader

loader = VideoLoader("my_video.mp4")
paths = loader.extract_frames("output_dir", fps=1.0)
```

### Custom Pipeline Parameters
- **Confidence**: Lower = more detections (higher false positives)
- **FPS Setting**: For playback speed in output video

---

## 📝 Notes

- Frames are saved to `frames_uploaded_<filename>/`
- Supported video codecs: H.264, H.265, MPEG-4
- Max file size: Depends on available disk space
- Processing time scales with video length and complexity

---

**See [DRAG_DROP_GUIDE.md](DRAG_DROP_GUIDE.md) for detailed documentation**

# Drag & Drop Video Upload Guide

## Overview

The updated Streamlit interface now supports seamless **drag-and-drop video upload** with automatic frame extraction. No need to manually extract frames anymore!

## Features

### 1. **Drag & Drop Video Upload**
- Simply drag a video file onto the "Video Input" section in the sidebar
- Alternatively, click to browse and select from your computer
- Supported formats: `.mp4`, `.avi`, `.mov`, `.mkv`, `.flv`

### 2. **Automatic Frame Extraction**
- Once a video is uploaded, configure extraction parameters:
  - **Extract @ FPS**: How many frames per second to extract (default: 1 FPS)
  - **Max frames**: Maximum number of frames to extract (default: 100)
- Click "🎬 Extract Frames & Load" to process the video

### 3. **Real-time Video Information**
After extraction, see:
- Video resolution (width × height)
- Original FPS
- Video duration
- Total frame count

## Workflow

### Step 1: Upload Video
```
1. Open the Streamlit app
2. Go to the "📹 Video Input" section in the sidebar
3. Drag & drop your video file (or click to browse)
```

### Step 2: Configure Extraction
```
1. Set "Extract @ FPS" - e.g., 1 FPS for 1 frame per second
   - Lower FPS = fewer frames (faster processing)
   - Higher FPS = more frames (slower processing)
2. Set "Max frames" - limit total extraction
   - Useful for long videos or quick testing
```

### Step 3: Extract & Load
```
1. Click "🎬 Extract Frames & Load"
2. Wait for extraction to complete
3. See video information displayed
```

### Step 4: Run Pipeline
```
1. Adjust detection settings:
   - Confidence threshold (0.1 - 0.9)
   - FPS for processing
2. Click "▶️ Run Pipeline"
3. Pipeline processes extracted frames
```

### Step 5: View Results
```
1. Extracted frames are displayed in the interface
2. Slide through frames to see detections
3. View interactions and state transitions
4. Download annotated video if generated
```

## Technical Details

### Frame Extraction Function

The extraction happens in `src/app/streamlit_app.py`:

```python
def extract_frames_from_video(
    video_file,      # Streamlit UploadedFile
    output_dir,      # Where to save frames
    fps=1.0,         # Extraction rate
    max_frames=None  # Maximum frames to extract
) -> Tuple[List[str], Dict[str, Any]]:
    # Uses VideoLoader from src/ingest/video_loader.py
    # Extracts frames as JPG files
    # Returns frame paths and video metadata
```

### Frame Storage

Extracted frames are saved to:
```
frames_uploaded_<video_name>/
├── frame_000000.jpg
├── frame_000001.jpg
├── frame_000002.jpg
└── ...
```

### Session State Management

The app uses Streamlit session state to track:
- `frames_dir`: Directory containing extracted frames
- `video_uploaded`: Whether a video was just uploaded
- `video_info`: Metadata about the original video
- `extracted_frames`: List of frame paths

## Example Usage

### Quick Test (1 FPS, max 50 frames)
```
1. Upload a 5-minute video (300 seconds)
2. Set Extract @ FPS to 1.0
3. Set Max frames to 50
4. Extract → Get ~50 frames
5. Run pipeline on these 50 frames
6. Quick results in seconds
```

### Full Analysis (30 FPS, no limit)
```
1. Upload a 30-second video
2. Set Extract @ FPS to 30.0
3. Set Max frames to 1000 (or leave default)
4. Extract → Get all ~900 frames
5. Run full pipeline for complete analysis
```

## Troubleshooting

### Issue: "Failed to extract frames"
- Ensure video format is supported (mp4, avi, mov, mkv, flv)
- Check that OpenCV (cv2) is installed: `pip install opencv-python`
- Try a different video file

### Issue: "Frames directory not found"
- This shouldn't happen with drag-and-drop
- Frames are automatically saved to `frames_uploaded_<name>/`
- Check that write permissions exist in the project directory

### Issue: "No frames available in results"
- Ensure the pipeline ran successfully
- Check that extraction rate (FPS) wasn't too low
- Try increasing Max frames value

## Integration with Existing Code

The new drag-and-drop feature integrates seamlessly with:

1. **VideoLoader** (`src/ingest/video_loader.py`)
   - Handles video reading and frame extraction
   - Provides video metadata (fps, resolution, duration)

2. **Integrated Pipeline** (`integrated_pipeline.py`)
   - Processes extracted frames as usual
   - No changes needed to existing pipeline code

3. **JSON Logger** (`src/logging/json_logger.py`)
   - Logs results as before
   - Works with extracted frames automatically

## Performance Tips

1. **For Initial Testing**: Use 1 FPS with max 50 frames
2. **For Real Analysis**: Use 5-10 FPS depending on video content
3. **For Slow Computers**: Reduce max frames or decrease FPS
4. **For High Detail**: Use 30 FPS matching original video

## API Reference

### `extract_frames_from_video()`
```python
from src.app.streamlit_app import extract_frames_from_video

frame_paths, video_info = extract_frames_from_video(
    video_file=st.file_uploader(...),
    output_dir="frames_output",
    fps=1.0,
    max_frames=100
)

# Returns:
# - frame_paths: List[str] - paths to extracted JPG files
# - video_info: Dict with keys:
#   - fps: Original video FPS
#   - frame_count: Total frames in video
#   - width, height: Resolution
#   - duration_seconds: Video duration
```

### `run_pipeline()`
```python
from src.app.streamlit_app import run_pipeline

results = run_pipeline(
    frames_dir="frames_uploaded_video_mp4",
    output_path="output/results.json",
    confidence=0.36,
    fps=30.0
)

# Returns: Dict with detection, tracking, interaction results
```

## Advanced: Custom Frame Extraction

If you want to use the VideoLoader directly:

```python
from src.ingest.video_loader import VideoLoader

loader = VideoLoader("video.mp4")
info = loader.get_info()  # Get metadata

# Extract frames manually
frame_paths = loader.extract_frames(
    output_dir="my_frames",
    fps=1.0,  # Extract at 1 FPS
    format="jpg"
)

# Or iterate through frames
for frame_idx, timestamp, frame in loader.frame_iterator():
    # Process frame
    pass
```

## Summary

The new drag-and-drop interface makes it incredibly easy to:
- 🎯 Load any video file
- ⚡ Extract frames automatically
- 🎬 Run the full pipeline in seconds
- 📊 View results immediately

No manual frame extraction. No directory setup. Just drag, drop, and analyze!

# Architecture Update: Drag & Drop Video Integration

## Overview

The Streamlit interface has been enhanced with **drag-and-drop video upload and automatic frame extraction**, making the entire workflow seamless and user-friendly.

## Component Diagram

```
User Interface (Streamlit)
│
├─ 📹 Video Input Section
│  ├─ File uploader widget
│  ├─ Extraction parameters (fps, max_frames)
│  └─ Extract button
│
├─ extract_frames_from_video()
│  ├─ Save uploaded file to temp location
│  ├─ Initialize VideoLoader
│  └─ Iterate & save frames as JPG
│
├─ VideoLoader (src/ingest/video_loader.py)
│  ├─ Load video with OpenCV
│  ├─ Get video metadata (fps, resolution, duration)
│  ├─ Frame iterator with timestamps
│  └─ Extract frames with frame skipping
│
├─ Frame Storage
│  └─ frames_uploaded_<name>/
│     ├─ frame_000000.jpg
│     ├─ frame_000001.jpg
│     └─ ...
│
├─ Pipeline Execution
│  ├─ YOLO Detection (Person 1)
│  ├─ ByteTrack Tracking (Person 1)
│  ├─ Interaction Detection (Person 2)
│  └─ State Memory (Person 2)
│
└─ Results Visualization
   ├─ Frame slider
   ├─ Bounding boxes with labels
   ├─ Interaction summary
   └─ State transitions

```

## Data Flow

### Before (Manual)
```
1. User extracts frames manually
2. Puts them in frames/ directory
3. Updates path in Streamlit UI
4. Runs pipeline
5. Views results
```

### After (Automated)
```
1. User drags video into UI
2. App extracts frames automatically
3. Frames saved to frames_uploaded_*/
4. UI automatically configured
5. Runs pipeline
6. Views results
```

## New Functions

### `extract_frames_from_video()`
**Location**: `src/app/streamlit_app.py`

```python
def extract_frames_from_video(
    video_file: Any,           # Streamlit UploadedFile
    output_dir: str,           # Where to save frames
    fps: float = 1.0,          # Extraction rate
    max_frames: int = None     # Limit total extraction
) -> Tuple[List[str], Dict[str, Any]]:
    """
    Extract frames from video file.
    
    Returns:
        - List of saved frame paths
        - Video metadata dict
    """
```

**Process**:
1. Save uploaded file to temporary location
2. Initialize `VideoLoader` with video path
3. Get video info (fps, resolution, duration)
4. Calculate frame skip rate to achieve desired fps
5. Iterate through video frames, saving every Nth frame
6. Clean up temporary file
7. Return frame paths and metadata

## Modified Files

### `src/app/streamlit_app.py`

**Imports Added**:
- `cv2` - OpenCV for video processing
- `tempfile` - Handle temporary files
- `VideoLoader` - Load and extract from videos
- `get_frame_paths` - List extracted frames

**Session State**:
- `frames_dir` - Currently active frames directory
- `video_uploaded` - Track if video was uploaded
- `video_info` - Metadata from uploaded video
- `extracted_frames` - List of frame paths

**UI Sections**:
- **📹 Video Input** - Drag/drop upload area
- Extraction parameters (fps, max_frames)
- Extract button with progress spinner
- Video info display after extraction

**Logic**:
- Conditional UI based on `video_uploaded` state
- Auto-configure frames directory
- Pipeline runs on extracted frames

## Integration Points

### 1. VideoLoader (`src/ingest/video_loader.py`)
- ✅ Already supports frame extraction
- ✅ Returns metadata
- ✅ Handles frame iteration
- No changes needed

### 2. Integrated Pipeline (`integrated_pipeline.py`)
- ✅ Works with extracted frames
- ✅ No changes needed
- Accepts frames_dir parameter

### 3. JSON Logger (`src/logging/json_logger.py`)
- ✅ Logs results as before
- ✅ No changes needed

## Performance Optimizations

### Frame Skipping
- Instead of extracting every frame, skip frames
- Formula: `frame_skip = int(original_fps / desired_fps)`
- Example: 30 fps video @ 1 fps extraction → skip 30 frames
- Reduces disk I/O and file count

### Temp File Handling
- Uploaded file saved to temp location
- Processed in-memory when possible
- Temp file deleted after extraction
- Keeps disk space clean

### Max Frames Limit
- User can limit total frames extracted
- Useful for quick testing
- Prevents disk space issues with long videos

## Testing the Integration

### Test 1: Basic Upload
```python
# Simulate in browser:
# 1. Open Streamlit app
# 2. Drag any .mp4 file
# 3. Extract frames
# 4. Should see frame list and video info
```

### Test 2: Pipeline Execution
```python
# After extraction:
# 1. Run pipeline
# 2. Should process frames automatically
# 3. View results in interface
```

### Test 3: Extraction Parameters
```python
# Test different fps values:
# - fps=0.5 → extract every 60 frames
# - fps=1.0 → extract every 30 frames
# - fps=5.0 → extract every 6 frames
# Verify extracted frame count matches expectation
```

## File Structure Update

```
project/
├── src/app/
│   └── streamlit_app.py        # ✨ ENHANCED with drag-drop
├── src/ingest/
│   └── video_loader.py         # ✅ Used for extraction
├── frames_uploaded_*/           # 📁 NEW: Dynamic frame dirs
│   ├── frame_000000.jpg
│   ├── frame_000001.jpg
│   └── ...
└── output/
    ├── integrated_results.json
    └── action_log.json
```

## Future Enhancements

1. **Video Preview**: Show thumbnail before extraction
2. **Progress Bar**: Real-time extraction progress
3. **Multiple Videos**: Queue multiple videos
4. **Frame Selection**: Choose specific time ranges
5. **Codec Detection**: Auto-detect best extraction settings
6. **Result Caching**: Cache results for same video
7. **Batch Processing**: Process multiple videos sequentially

## Dependencies

### Existing (Already installed)
- `streamlit` - Web UI
- `opencv-python` (cv2) - Video processing
- `pillow` - Image handling
- `ultralytics` - YOLO detection

### No New Dependencies Added
All required packages already in `requirements.txt`

## Summary

The drag-and-drop video upload feature:

✅ **Simplifies workflow** - No manual frame extraction needed
✅ **Saves time** - Automated extraction in seconds
✅ **User-friendly** - Intuitive drag-drop interface
✅ **Flexible** - Configurable extraction parameters
✅ **Integrated** - Works seamlessly with existing pipeline
✅ **No breaking changes** - Backward compatible with manual frame directories

Users can now go from raw video to results in 4 simple steps!

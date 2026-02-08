# 🎬 Complete Workflow Diagram

## User Journey Map

```
╔════════════════════════════════════════════════════════════════════════════╗
║                    WORLD2DATA DRAG-AND-DROP INTERFACE                      ║
║                         Complete User Journey                              ║
╚════════════════════════════════════════════════════════════════════════════╝

┌─────────────────────────────────────────────────────────────────────────────┐
│  STEP 1: START APPLICATION                                                  │
│                                                                              │
│  $ streamlit run src/app/streamlit_app.py                                   │
│  ↓                                                                           │
│  Browser opens to http://localhost:8501                                     │
│  Interface loads with "📹 Video Input" section                              │
└─────────────────────────────────────────────────────────────────────────────┘

                              ⬇️

┌─────────────────────────────────────────────────────────────────────────────┐
│  STEP 2: UPLOAD VIDEO                                                       │
│                                                                              │
│  User Action: Drag & drop video.mp4 into upload area                        │
│  ↓                                                                           │
│  st.file_uploader() captures file                                           │
│  Displays: "✅ Video loaded: video.mp4"                                     │
│  Shows extraction parameters:                                               │
│    • Extract @ FPS: [slider] (default: 1.0)                                 │
│    • Max frames: [input] (default: 100)                                     │
└─────────────────────────────────────────────────────────────────────────────┘

                              ⬇️

┌─────────────────────────────────────────────────────────────────────────────┐
│  STEP 3: EXTRACT FRAMES                                                     │
│                                                                              │
│  User Action: Click "🎬 Extract Frames & Load"                              │
│  ↓                                                                           │
│  extract_frames_from_video() executes:                                      │
│    1. Save uploaded file to temp location                                   │
│    2. Initialize VideoLoader                                                │
│    3. Get video metadata (fps, resolution, etc.)                            │
│    4. Calculate frame_skip ratio                                            │
│    5. Loop through video frames                                             │
│    6. Save every Nth frame as JPG                                           │
│    7. Delete temp file                                                      │
│  ↓                                                                           │
│  Output: frames_uploaded_video_mp4/                                         │
│    ├── frame_000000.jpg                                                     │
│    ├── frame_000001.jpg                                                     │
│    ├── frame_000002.jpg                                                     │
│    └── ...                                                                  │
│  ↓                                                                           │
│  Displays:                                                                  │
│    ✅ Extracted 100 frames from video!                                      │
│    📊 Video Info:                                                           │
│       - Resolution: 1920×1080                                               │
│       - Original FPS: 30.0                                                  │
│       - Duration: 5.00s                                                     │
│       - Total frames in video: 150                                          │
│  ↓                                                                           │
│  Session State Updated:                                                     │
│    st.session_state.frames_dir = "frames_uploaded_video_mp4/"               │
│    st.session_state.video_uploaded = True                                   │
│    st.session_state.video_info = {...}                                     │
└─────────────────────────────────────────────────────────────────────────────┘

                              ⬇️

┌─────────────────────────────────────────────────────────────────────────────┐
│  STEP 4: CONFIGURE PIPELINE                                                 │
│                                                                              │
│  User sees automatic configuration:                                         │
│    • Frames directory: 📁 Using extracted frames from upload                 │
│    • Confidence threshold: [slider] (default: 0.36)                         │
│    • FPS setting: [input] (default: 30.0)                                   │
│    • Write action log: ☑️ (default: True)                                   │
│                                                                              │
│  User Action: Click "▶️ Run Pipeline"                                       │
└─────────────────────────────────────────────────────────────────────────────┘

                              ⬇️

┌─────────────────────────────────────────────────────────────────────────────┐
│  STEP 5: RUN INTEGRATED PIPELINE                                            │
│                                                                              │
│  run_integrated_pipeline() executes:                                        │
│                                                                              │
│  ┌─ PERSON 1: DETECTION & TRACKING                                          │
│  │  ├─ Load frames from frames_uploaded_video_mp4/                          │
│  │  ├─ Initialize YOLOv8 detector                                           │
│  │  │  └─ For each frame: detect objects (person, car, etc.)               │
│  │  │     │ Class names, confidence scores, bounding boxes                 │
│  │  │     └─ Store: detections                                             │
│  │  └─ Initialize ByteTrack tracker                                         │
│  │     └─ For each frame: track object IDs over time                       │
│  │        └─ Store: track_ids                                              │
│  │                                                                          │
│  ├─ PERSON 2: INTERACTION & STATE                                           │
│  │  ├─ Classify detections (agents vs objects)                              │
│  │  ├─ Detect interactions with RollingSpikeTrigger                         │
│  │  │  └─ Calculate IoU between agents and objects                          │
│  │  │     └─ If touching: interaction detected                             │
│  │  └─ Track state changes with StateMemory                                 │
│  │     └─ Monitor state transitions over time                              │
│  │                                                                          │
│  └─ Output JSON Results:                                                    │
│     ├─ video_info (fps, resolution, duration)                              │
│     ├─ frames[] (frame-by-frame data)                                      │
│     ├─ detections (boxes, scores, class names)                             │
│     ├─ track_ids (object tracking)                                         │
│     ├─ interactions (agent-object interactions)                            │
│     └─ state_transitions (state changes)                                   │
│                                                                              │
│  Output: output/integrated_results.json                                     │
└─────────────────────────────────────────────────────────────────────────────┘

                              ⬇️

┌─────────────────────────────────────────────────────────────────────────────┐
│  STEP 6: DISPLAY RESULTS                                                    │
│                                                                              │
│  Interface Updates:                                                         │
│    ├─ Summary Section                                                       │
│    │  ├─ Total frames                                                      │
│    │  ├─ FPS                                                               │
│    │  ├─ Resolution                                                        │
│    │  ├─ Number of tracks                                                 │
│    │  ├─ Interactions detected                                             │
│    │  └─ State transitions                                                │
│    │                                                                        │
│    ├─ Frame Viewer (Left Column)                                            │
│    │  ├─ Frame slider: Select frame 0-99                                   │
│    │  ├─ Image display                                                     │
│    │  ├─ Bounding boxes with labels                                        │
│    │  ├─ Color coding by class:                                            │
│    │  │  ├─ Green: Person                                                  │
│    │  │  ├─ Red: Car                                                       │
│    │  │  └─ etc.                                                           │
│    │  └─ Interaction banner (if detected)                                  │
│    │                                                                        │
│    ├─ Frame Details (Right Column)                                          │
│    │  ├─ Frame index                                                       │
│    │  ├─ Timestamp                                                         │
│    │  ├─ Agents count                                                      │
│    │  ├─ Objects count                                                     │
│    │  ├─ Interactions                                                      │
│    │  └─ Detections table                                                  │
│    │     ├─ Class name                                                     │
│    │     ├─ Confidence score                                               │
│    │     ├─ Track ID                                                       │
│    │     └─ Bounding box coordinates                                       │
│    │                                                                        │
│    ├─ Interactions Section                                                  │
│    │  └─ Table of all interactions detected                                │
│    │                                                                        │
│    └─ State Transitions Section                                             │
│       └─ Table of all state changes recorded                               │
│                                                                              │
│  User Action: Explore results                                               │
│    • Slide through frames                                                   │
│    • View detections for each frame                                         │
│    • Study interactions                                                     │
│    • Analyze state transitions                                              │
│    • Toggle labels, untracked boxes, interactions                           │
└─────────────────────────────────────────────────────────────────────────────┘

                              ⬇️

┌─────────────────────────────────────────────────────────────────────────────┐
│  STEP 7: EXPORT & SHARE                                                     │
│                                                                              │
│  Generated Files:                                                           │
│    ├─ output/integrated_results.json                                        │
│    │  └─ Complete detection, tracking, interaction data                    │
│    ├─ output/action_log.json                                                │
│    │  └─ Structured log with metadata                                      │
│    ├─ output/integrated_annotated_video.mp4 (optional)                      │
│    │  └─ Video with bounding boxes overlay                                 │
│    └─ frames_uploaded_video_mp4/                                            │
│       └─ 100 extracted JPG frames                                           │
│                                                                              │
│  User Action: Download or share results                                     │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Data Flow Diagram

```
                     ┌──────────────────┐
                     │  Video Upload    │
                     │  (mp4, avi, etc) │
                     └────────┬─────────┘
                              │
                              ▼
                    ┌──────────────────────┐
                    │ extract_frames_      │
                    │ from_video()         │
                    │                      │
                    │ • Save to temp       │
                    │ • Load with VideoLd  │
                    │ • Skip frames        │
                    │ • Save as JPG        │
                    └────────┬─────────────┘
                             │
                             ▼
                  ┌───────────────────────┐
                  │ Frames Directory      │
                  │ frames_uploaded_*/    │
                  │ ├─ frame_000000.jpg   │
                  │ ├─ frame_000001.jpg   │
                  │ └─ ...                │
                  └────────┬──────────────┘
                           │
                           ▼
                ┌──────────────────────────┐
                │ run_integrated_pipeline  │
                │                          │
                │ PERSON 1:                │
                │ ├─ YOLODetector          │
                │ │  └─ Detect objects     │
                │ └─ ByteTracker           │
                │    └─ Track IDs          │
                │                          │
                │ PERSON 2:                │
                │ ├─ RollingSpikeTrigger   │
                │ │  └─ Detect interactions│
                │ └─ StateMemory           │
                │    └─ Track states       │
                └────────┬─────────────────┘
                         │
                         ▼
                ┌──────────────────────────┐
                │ JSON Results             │
                │ ├─ video_info            │
                │ ├─ frames[]              │
                │ ├─ detections[]          │
                │ ├─ interactions[]        │
                │ └─ state_transitions[]   │
                └────────┬─────────────────┘
                         │
                         ▼
                ┌──────────────────────────┐
                │ Streamlit Display        │
                │                          │
                │ ├─ Summary stats         │
                │ ├─ Frame viewer          │
                │ ├─ Bounding boxes        │
                │ ├─ Interactions table    │
                │ └─ State transitions tbl │
                └──────────────────────────┘
```

---

## Component Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      STREAMLIT APPLICATION                       │
│  src/app/streamlit_app.py                                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─── VIDEO INPUT SECTION ───────────────────────────────────┐  │
│  │ • File uploader widget                                    │  │
│  │ • Extraction parameters (fps, max_frames)                 │  │
│  │ • Extract button                                          │  │
│  │ • Video info display                                      │  │
│  └────────────────────────────────────────────────────────────┘  │
│                           ▼                                      │
│  ┌─── EXTRACTION FUNCTION ────────────────────────────────────┐  │
│  │ def extract_frames_from_video():                           │  │
│  │   • Uses: VideoLoader from src/ingest/                    │  │
│  │   • Extracts frames with frame skipping                   │  │
│  │   • Saves JPG files to frames_uploaded_*/                 │  │
│  │   • Returns: (paths, metadata)                            │  │
│  └────────────────────────────────────────────────────────────┘  │
│                           ▼                                      │
│  ┌─── SESSION STATE ──────────────────────────────────────────┐  │
│  │ • frames_dir: Path to extracted frames                    │  │
│  │ • video_uploaded: Boolean flag                            │  │
│  │ • video_info: Metadata dict                               │  │
│  │ • extracted_frames: List of paths                         │  │
│  └────────────────────────────────────────────────────────────┘  │
│                           ▼                                      │
│  ┌─── DATA SECTION ───────────────────────────────────────────┐  │
│  │ • Mode: Load results or Run pipeline                      │  │
│  │ • Conditional paths based on upload status                │  │
│  │ • Confidence threshold                                    │  │
│  │ • FPS setting                                             │  │
│  │ • Action log settings                                     │  │
│  └────────────────────────────────────────────────────────────┘  │
│                           ▼                                      │
│  ┌─── PIPELINE EXECUTION ─────────────────────────────────────┐  │
│  │ run_pipeline() calls:                                     │  │
│  │   ↓                                                        │  │
│  │   integrated_pipeline.run_integrated_pipeline()           │  │
│  │   ↓                                                        │  │
│  │   Returns: JSON with all results                          │  │
│  └────────────────────────────────────────────────────────────┘  │
│                           ▼                                      │
│  ┌─── VISUALIZATION ──────────────────────────────────────────┐  │
│  │ • Frame viewer with slider                                │  │
│  │ • Bounding boxes overlay                                  │  │
│  │ • Detection tables                                        │  │
│  │ • Interaction summary                                     │  │
│  │ • State transitions table                                 │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘

                         ▼ Uses ▼

┌─────────────────────────────────────────────────────────────────┐
│               EXISTING PIPELINE COMPONENTS                       │
│                (No changes needed)                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  VideoLoader (src/ingest/video_loader.py)                       │
│    ├─ Load video from file                                      │
│    ├─ Get video metadata                                        │
│    ├─ Iterate frames                                            │
│    └─ Extract frames                                            │
│                                                                  │
│  YOLODetector (src/detection/yolo_detector.py)                  │
│    ├─ Load YOLOv8 model                                         │
│    ├─ Detect objects per frame                                  │
│    └─ Return boxes, scores, class names                         │
│                                                                  │
│  ByteTracker (src/detection/bytetrack_tracker.py)               │
│    ├─ Track object IDs                                          │
│    ├─ Associate detections                                      │
│    └─ Return track IDs                                          │
│                                                                  │
│  RollingSpikeTrigger (src/interaction/iou_trigger.py)           │
│    ├─ Calculate IoU between objects                             │
│    ├─ Detect interactions                                       │
│    └─ Return interaction list                                   │
│                                                                  │
│  StateMemory (src/interaction/state_memory.py)                  │
│    ├─ Track state changes                                       │
│    ├─ Record transitions                                        │
│    └─ Return state data                                         │
│                                                                  │
│  JSON Logger (src/logging/json_logger.py)                       │
│    ├─ Format results                                            │
│    ├─ Write to JSON                                             │
│    └─ Log actions                                               │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## State Transitions

```
User Opens App
    │
    ▼
video_uploaded = False
frames_dir = "frames/" (default)
    │
    ▼
User Uploads Video
    │
    ▼
uploaded_video ≠ None
    │
    ├─ Show extraction parameters
    │
    └─ Extract button appears
        │
        ▼
    User Clicks Extract
        │
        ▼
    extract_frames_from_video() runs
        │
        ├─ Success
        │   │
        │   ▼
        │   video_uploaded = True
        │   frames_dir = "frames_uploaded_*/"
        │   video_info = {...}
        │   extracted_frames = [...]
        │   │
        │   └─ Show success message
        │      Show video info
        │      UI updates
        │
        └─ Error
            │
            ▼
            Show error message
            Keep same state
            User can try again

    UI Adapts:
        if video_uploaded:
            ├─ Show "Using extracted frames from upload"
            ├─ Use frames_dir from session state
            └─ Pipeline ready to run
        else:
            ├─ Show frames directory text input
            ├─ Allow manual path specification
            └─ User can browse existing frames

    User Clicks "▶️ Run Pipeline"
        │
        ▼
    run_pipeline(frames_dir, ...) executes
        │
        ├─ Success
        │   │
        │   ▼
        │   Load results.json
        │   Display in interface
        │   Show all visualizations
        │
        └─ Error
            │
            ▼
            Show error message
            Ask to check paths

    User Explores Results
        │
        ├─ Slide through frames
        ├─ View detections
        ├─ Study interactions
        └─ Analyze state transitions
```

---

## Success Indicators

```
✅ Video Successfully Extracted
   ├─ "✅ Extracted N frames from video!"
   ├─ Video info displayed:
   │  ├─ Resolution: 1920×1080
   │  ├─ Original FPS: 30.0
   │  ├─ Duration: 5.00s
   │  └─ Total frames in video: 150
   └─ frames_uploaded_*/ directory created

✅ Pipeline Running
   ├─ "Running pipeline..." spinner shows
   ├─ YOLO detector initializing
   ├─ ByteTrack tracker running
   ├─ Interactions detected
   └─ State transitions recorded

✅ Results Displaying
   ├─ Summary stats shown
   ├─ Frame viewer working
   ├─ Bounding boxes displayed
   ├─ Interaction table populated
   └─ State transitions listed

✅ Ready for Analysis
   ├─ Frame slider functional
   ├─ Labels toggle working
   ├─ All visualizations active
   └─ User can explore results
```

---

## Complete Timeline

```
Time  |  Action                  |  Duration  |  Output
───────────────────────────────────────────────────────────────
0:00  │  Start app               │  ~1s       │  Interface loads
0:05  │  Upload video            │  <1s       │  "✅ Video loaded"
0:10  │  Click Extract button    │  ~5-10s    │  "✅ Extracted frames"
0:20  │  Click Run Pipeline      │  ~30-60s   │  "Running pipeline..."
1:20  │  Pipeline complete       │  <1s       │  Results display
1:25  │  Explore results         │  ∞         │  User can analyze

Total: ~1.5 minutes for quick test
       ~3-5 minutes for standard analysis
```

This is the complete workflow! Ready to use! 🚀

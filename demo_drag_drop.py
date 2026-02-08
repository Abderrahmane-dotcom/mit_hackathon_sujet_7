#!/usr/bin/env python3
"""
Demo script showing the drag-and-drop video functionality.
This demonstrates how the new extract_frames_from_video function works.
"""

import sys
from pathlib import Path

# Add project to path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

def demo_frame_extraction():
    """
    Demonstrates the frame extraction process without Streamlit.
    Useful for testing the VideoLoader functionality.
    """
    from src.ingest.video_loader import VideoLoader
    
    print("=" * 70)
    print("FRAME EXTRACTION DEMO")
    print("=" * 70)
    
    # Example: If you have a video file
    sample_video = project_root / "sample_video.mp4"
    
    if not sample_video.exists():
        print("\n⚠️  No sample video found at:", sample_video)
        print("\nTo test frame extraction:")
        print("1. Place a video file in the project root")
        print("2. Name it 'sample_video.mp4'")
        print("3. Run this script again")
        return
    
    try:
        print(f"\n📹 Loading video: {sample_video}")
        loader = VideoLoader(str(sample_video))
        
        # Get video info
        info = loader.get_info()
        print("\n📊 Video Information:")
        print(f"   Resolution: {info['width']}×{info['height']}")
        print(f"   FPS: {info['fps']}")
        print(f"   Frame count: {info['frame_count']}")
        print(f"   Duration: {info['duration_seconds']:.2f}s")
        
        # Extract frames
        output_dir = project_root / "demo_frames"
        print(f"\n🎬 Extracting frames to {output_dir}...")
        
        frame_paths = loader.extract_frames(
            str(output_dir),
            fps=1.0,  # Extract 1 frame per second
            format="jpg"
        )
        
        print(f"\n✅ Successfully extracted {len(frame_paths)} frames!")
        print(f"   Saved to: {output_dir}")
        print(f"   First frame: {frame_paths[0]}")
        print(f"   Last frame: {frame_paths[-1]}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")


def demo_streamlit_workflow():
    """
    Describes the Streamlit workflow.
    """
    print("\n" + "=" * 70)
    print("STREAMLIT DRAG-AND-DROP WORKFLOW")
    print("=" * 70)
    
    workflow = """
    
    📱 USER INTERFACE FLOW:
    
    1️⃣  UPLOAD VIDEO
        └─ Open Streamlit app: streamlit run src/app/streamlit_app.py
        └─ Go to "📹 Video Input" section
        └─ Drag & drop video file or click to browse
        └─ Select from: mp4, avi, mov, mkv, flv
    
    2️⃣  CONFIGURE EXTRACTION
        └─ Extract @ FPS: 1.0 (1 frame per second)
        └─ Max frames: 100 (limit total extraction)
        └─ See real-time video info displayed
    
    3️⃣  EXTRACT FRAMES
        └─ Click "🎬 Extract Frames & Load"
        └─ App shows progress and metadata
        └─ Frames saved to frames_uploaded_<name>/
    
    4️⃣  RUN PIPELINE
        └─ Adjust confidence threshold
        └─ Click "▶️ Run Pipeline"
        └─ Pipeline processes extracted frames
    
    5️⃣  VIEW RESULTS
        └─ Frame-by-frame detection visualization
        └─ Bounding boxes with labels
        └─ Interaction detection summary
        └─ State transition tracking
    
    
    🔧 BACKEND PROCESS:
    
    Video Upload
        ↓
    VideoLoader.extract_frames()
        ├─ Read video file
        ├─ Calculate frame skip rate
        ├─ Iterate through frames
        └─ Save as JPG files
        ↓
    Frames Directory
        ├─ frames_uploaded_video_mp4/
        ├─ frame_000000.jpg
        ├─ frame_000001.jpg
        └─ frame_000002.jpg
        ↓
    Integrated Pipeline
        ├─ YOLO Detection
        ├─ ByteTrack Tracking
        ├─ Interaction Detection
        └─ State Memory
        ↓
    JSON Results
        ├─ integrated_results.json
        ├─ action_log.json
        └─ visualized frames
        ↓
    Display Results
        ├─ Frame viewer
        ├─ Detection tables
        ├─ Interaction summary
        └─ State transitions
    """
    
    print(workflow)


def demo_code_example():
    """
    Shows how to use the new functions programmatically.
    """
    print("\n" + "=" * 70)
    print("CODE EXAMPLES")
    print("=" * 70)
    
    examples = """
    
    📝 EXAMPLE 1: Direct VideoLoader Usage
    ──────────────────────────────────────
    
    from src.ingest.video_loader import VideoLoader
    
    # Load video
    loader = VideoLoader("my_video.mp4")
    info = loader.get_info()
    
    # Extract frames at 1 FPS
    frame_paths = loader.extract_frames("output_frames", fps=1.0)
    
    # Or iterate through frames manually
    for frame_idx, timestamp, frame in loader.frame_iterator():
        print(f"Frame {frame_idx}: {timestamp}s")
        # Process frame...
        if frame_idx > 10:
            break
    
    
    📝 EXAMPLE 2: In Streamlit App
    ──────────────────────────────
    
    import streamlit as st
    from src.app.streamlit_app import extract_frames_from_video
    
    # Upload file
    video_file = st.file_uploader("Upload video", type=["mp4", "avi"])
    
    if video_file:
        # Extract frames
        paths, info = extract_frames_from_video(
            video_file,
            output_dir="my_frames",
            fps=1.0,
            max_frames=100
        )
        
        st.success(f"Extracted {len(paths)} frames!")
        st.info(f"Resolution: {info['width']}x{info['height']}")
    
    
    📝 EXAMPLE 3: Batch Processing
    ──────────────────────────────
    
    from pathlib import Path
    from src.ingest.video_loader import VideoLoader
    
    videos_dir = Path("videos")
    
    for video_file in videos_dir.glob("*.mp4"):
        print(f"Processing {video_file.name}...")
        
        loader = VideoLoader(str(video_file))
        output = Path("frames") / video_file.stem
        
        paths = loader.extract_frames(str(output), fps=5.0)
        print(f"  Extracted {len(paths)} frames")
    
    
    📝 EXAMPLE 4: Conditional Extraction
    ────────────────────────────────────
    
    from src.ingest.video_loader import VideoLoader
    
    loader = VideoLoader("my_video.mp4")
    info = loader.get_info()
    
    # Only extract if video is short enough
    if info['duration_seconds'] < 60:  # Less than 1 minute
        paths = loader.extract_frames("output", fps=10.0)
    else:
        print("Video too long!")
    """
    
    print(examples)


def main():
    """Run all demos."""
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 68 + "║")
    print("║" + " WORLD2DATA - DRAG & DROP VIDEO DEMO ".center(68) + "║")
    print("║" + " " * 68 + "║")
    print("╚" + "=" * 68 + "╝")
    
    demo_streamlit_workflow()
    demo_code_example()
    demo_frame_extraction()
    
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print("""
    ✨ The new drag-and-drop feature makes it easy to:
    
    1. Upload any video file (mp4, avi, mov, mkv, flv)
    2. Automatically extract frames at desired rate
    3. Run the full detection pipeline
    4. View results in a beautiful interface
    
    No manual frame extraction needed!
    No directory setup required!
    Just drag, drop, and analyze!
    
    📖 For more details, see:
       - docs/DRAG_DROP_GUIDE.md
       - docs/QUICK_START.md
       - docs/ARCHITECTURE_UPDATE.md
    """)
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()

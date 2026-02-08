"""
Video Loader Module - Person 1: Ingest + Detection
Handles loading frames from:
1. Video files (.mp4, .avi, etc.) - extracts frames on-the-fly
2. Frame directories (pre-extracted .jpg files)
"""

import glob
import cv2
from pathlib import Path
from typing import List, Dict, Iterator, Tuple, Optional


# ============================================
# VIDEO FILE LOADING (extract frames from .mp4)
# ============================================

class VideoLoader:
    """Load video file and iterate through frames with timestamps."""
    
    def __init__(self, video_path: str):
        self.video_path = Path(video_path)
        if not self.video_path.exists():
            raise FileNotFoundError(f"Video not found: {video_path}")
        
        self.cap = cv2.VideoCapture(str(self.video_path))
        if not self.cap.isOpened():
            raise RuntimeError(f"Failed to open video: {video_path}")
        
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.frame_count = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.duration = self.frame_count / self.fps if self.fps > 0 else 0
    
    def __del__(self):
        if hasattr(self, 'cap') and self.cap is not None:
            self.cap.release()
    
    def get_info(self) -> Dict:
        """Return video metadata."""
        return {
            "path": str(self.video_path),
            "fps": self.fps,
            "frame_count": self.frame_count,
            "width": self.width,
            "height": self.height,
            "duration_seconds": self.duration
        }
    
    def seek_to_time(self, seconds: float) -> bool:
        """Seek to a specific time in seconds."""
        frame_num = int(seconds * self.fps)
        return self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
    
    def frame_iterator(
        self,
        start_time: float = 0.0,
        end_time: Optional[float] = None
    ) -> Iterator[Tuple[int, float, any]]:
        """
        Iterate through video frames with index, timestamp, and image.
        
        Args:
            start_time: Start time in seconds
            end_time: End time in seconds (None = until end)
            
        Yields:
            (frame_index, timestamp_seconds, frame_bgr)
        """
        self.seek_to_time(start_time)
        
        start_frame = int(start_time * self.fps)
        end_frame = int(end_time * self.fps) if end_time else self.frame_count
        
        frame_num = start_frame
        while frame_num < end_frame:
            ret, frame = self.cap.read()
            if not ret:
                break
            
            timestamp = frame_num / self.fps
            yield frame_num, timestamp, frame
            frame_num += 1
    
    def extract_frames(
        self,
        output_dir: str,
        start_time: float = 0.0,
        end_time: Optional[float] = None,
        format: str = "jpg"
    ) -> List[str]:
        """
        Extract frames from video to a directory.
        
        Returns:
            List of saved frame file paths
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        saved_paths = []
        for frame_num, timestamp, frame in self.frame_iterator(start_time, end_time):
            filename = f"frame_{frame_num:06d}.{format}"
            filepath = output_path / filename
            cv2.imwrite(str(filepath), frame)
            saved_paths.append(str(filepath))
        
        return saved_paths


def load_video(video_path: str) -> VideoLoader:
    """Load a video file and return VideoLoader instance."""
    return VideoLoader(video_path)


# ============================================
# FRAME DIRECTORY LOADING (pre-extracted jpgs)
# ============================================

def get_frame_paths(frames_dir: str, pattern: str = "*.jpg") -> List[str]:
    """Get sorted list of frame paths from a directory."""
    frames_path = Path(frames_dir)
    return sorted(glob.glob(str(frames_path / pattern)))


def load_frame(frame_path: str):
    """Load a single frame as BGR numpy array."""
    return cv2.imread(frame_path)


def frame_iterator(
    frames_dir: str,
    fps: float = 30.0,
    pattern: str = "*.jpg"
) -> Iterator[Tuple[int, float, any]]:
    """
    Iterate through pre-extracted frames with index, timestamp, and image.
    
    Yields:
        (frame_index, timestamp_seconds, frame_bgr)
    """
    frame_paths = get_frame_paths(frames_dir, pattern)
    
    for i, frame_path in enumerate(frame_paths):
        timestamp = i / fps
        frame = load_frame(frame_path)
        if frame is not None:
            yield i, timestamp, frame


def get_video_info(frames_dir: str, fps: float = 30.0) -> Dict:
    """Get metadata about pre-extracted frames."""
    frame_paths = get_frame_paths(frames_dir)
    
    if not frame_paths:
        return {"error": "No frames found"}
    
    first_frame = load_frame(frame_paths[0])
    height, width = first_frame.shape[:2] if first_frame is not None else (0, 0)
    
    return {
        "frames_dir": frames_dir,
        "frame_count": len(frame_paths),
        "fps": fps,
        "width": width,
        "height": height,
        "duration_seconds": len(frame_paths) / fps
    }


if __name__ == "__main__":
    import sys
    
    path = sys.argv[1] if len(sys.argv) > 1 else "frames"
    
    # Check if it's a video file or directory
    if Path(path).is_file():
        print("=== Loading Video File ===")
        loader = load_video(path)
        print(f"Video Info: {loader.get_info()}")
        
        print("\nFirst 3 frames:")
        for i, ts, frame in loader.frame_iterator():
            print(f"  Frame {i}: t={ts:.3f}s, shape={frame.shape}")
            if i >= 2:
                break
    else:
        print("=== Loading Frame Directory ===")
        info = get_video_info(path)
        print(f"Info: {info}")
        
        print("\nFirst 3 frames:")
        for i, ts, frame in frame_iterator(path):
            print(f"  Frame {i}: t={ts:.3f}s, shape={frame.shape}")
            if i >= 2:
                break

"""
YOLO Detector Module - Person 1: Ingest + Detection
Wraps YOLOv8 inference for object detection.
"""

from pathlib import Path
from typing import List, Dict, Optional, Union
import numpy as np

try:
    from ultralytics import YOLO
except ImportError:
    raise ImportError("Please install ultralytics: pip install ultralytics")


class YOLODetector:
    """YOLOv8 object detector wrapper for navigation-relevant objects."""
    
    # Classes relevant for humanoid navigation (COCO dataset)
    # Note: COCO doesn't have "door" class - we detect door-like objects
    # For doors, consider fine-tuning or using segmentation
    NAVIGATION_CLASSES = {
        # People and vehicles (obstacles/agents)
        0: "person",
        1: "bicycle",
        2: "car", 
        3: "motorcycle",
        5: "bus",
        7: "truck",
        # Furniture (obstacles/interactables)
        56: "chair",
        57: "couch",
        58: "potted plant",
        59: "bed",
        60: "dining table",
        61: "toilet",
        # Electronics
        62: "tv",
        63: "laptop",
        67: "cell phone",
        # Objects that indicate doors/passages
        24: "backpack",      # Often near entries
        25: "umbrella",      # Outdoor indicator
        26: "handbag",
        28: "suitcase",      # Travel/entry areas
        # Kitchen/indoor navigation
        68: "microwave",
        69: "oven",
        70: "toaster",
        71: "sink",
        72: "refrigerator",
        73: "book",
        # Note: For actual door detection, recommend:
        # - SAM segmentation for door regions
        # - Fine-tuned model on door datasets
        # - VLM to identify "door" semantically
    }
    
    def __init__(
        self, 
        model_path: str = "yolov8n.pt",
        confidence_threshold: float = 0.36,  # Updated threshold
        iou_threshold: float = 0.45,
        device: Optional[str] = None
    ):
        """
        Initialize YOLO detector.
        
        Args:
            model_path: Path to YOLO model or model name (yolov8n, yolov8s, etc.)
            confidence_threshold: Minimum confidence for detections
            iou_threshold: IoU threshold for NMS
            device: Device to run on ('cuda', 'cpu', or None for auto)
        """
        self.model = YOLO(model_path)
        self.confidence_threshold = confidence_threshold
        self.iou_threshold = iou_threshold
        self.device = device
        
        # Get class names from model
        self.class_names = self.model.names
    
    def detect(
        self, 
        image: Union[np.ndarray, str, Path],
        classes: Optional[List[int]] = None
    ) -> Dict:
        """
        Run detection on a single image.
        
        Args:
            image: Image as numpy array (BGR), or path to image
            classes: Optional list of class IDs to filter
            
        Returns:
            Dict with detections:
            {
                "boxes": [[x1, y1, x2, y2], ...],
                "scores": [conf1, conf2, ...],
                "class_ids": [cls1, cls2, ...],
                "class_names": [name1, name2, ...]
            }
        """
        results = self.model(
            image,
            conf=self.confidence_threshold,
            iou=self.iou_threshold,
            device=self.device,
            classes=classes,
            verbose=False
        )[0]
        
        boxes = results.boxes
        
        if len(boxes) == 0:
            return {
                "boxes": [],
                "scores": [],
                "class_ids": [],
                "class_names": []
            }
        
        return {
            "boxes": boxes.xyxy.cpu().numpy().tolist(),
            "scores": boxes.conf.cpu().numpy().tolist(),
            "class_ids": boxes.cls.cpu().numpy().astype(int).tolist(),
            "class_names": [self.class_names[int(c)] for c in boxes.cls.cpu().numpy()]
        }
    
    def detect_batch(
        self, 
        images: List[Union[np.ndarray, str, Path]],
        classes: Optional[List[int]] = None
    ) -> List[Dict]:
        """Run detection on multiple images."""
        results = self.model(
            images,
            conf=self.confidence_threshold,
            iou=self.iou_threshold,
            device=self.device,
            classes=classes,
            verbose=False
        )
        
        detections = []
        for result in results:
            boxes = result.boxes
            if len(boxes) == 0:
                detections.append({
                    "boxes": [],
                    "scores": [],
                    "class_ids": [],
                    "class_names": []
                })
            else:
                detections.append({
                    "boxes": boxes.xyxy.cpu().numpy().tolist(),
                    "scores": boxes.conf.cpu().numpy().tolist(),
                    "class_ids": boxes.cls.cpu().numpy().astype(int).tolist(),
                    "class_names": [self.class_names[int(c)] for c in boxes.cls.cpu().numpy()]
                })
        
        return detections
    
    def detect_on_frames(
        self,
        frame_paths: List[str],
        classes: Optional[List[int]] = None
    ) -> List[Dict]:
        """
        Run detection on a list of frame file paths.
        
        Returns:
            List of detection dicts with frame metadata
        """
        all_detections = []
        
        for i, frame_path in enumerate(frame_paths):
            detection = self.detect(frame_path, classes)
            detection["frame_index"] = i
            detection["frame_path"] = frame_path
            all_detections.append(detection)
        
        return all_detections


def create_detector(model: str = "yolov8n.pt", **kwargs) -> YOLODetector:
    """Convenience function to create a YOLO detector."""
    return YOLODetector(model_path=model, **kwargs)


if __name__ == "__main__":
    import sys
    import glob
    
    # Test on extracted frames
    frames_dir = sys.argv[1] if len(sys.argv) > 1 else "frames"
    frame_paths = sorted(glob.glob(f"{frames_dir}/*.jpg"))[:5]
    
    if not frame_paths:
        print("No frames found!")
        sys.exit(1)
    
    print(f"Testing YOLO detector on {len(frame_paths)} frames...")
    detector = YOLODetector()
    
    for path in frame_paths:
        result = detector.detect(path)
        print(f"\n{Path(path).name}:")
        for i, (box, score, name) in enumerate(zip(
            result["boxes"], result["scores"], result["class_names"]
        )):
            print(f"  {name}: {score:.2f} at {[int(x) for x in box]}")

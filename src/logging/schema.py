"""Action log schema helpers."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from typing import Any, Dict, List

SCHEMA_VERSION = "1.0"


def is_action_log(data: Dict[str, Any]) -> bool:
    metadata = data.get("metadata", {}) if isinstance(data, dict) else {}
    return "schema_version" in metadata


def _normalize_frames(frame_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    frames = []
    for frame in frame_data:
        frames.append(
            {
                "frame_idx": frame.get("frame_idx"),
                "timestamp": frame.get("timestamp"),
                "frame_path": frame.get("frame_path"),
                "detections": frame.get("detections", {}),
                "agents": frame.get("agents", []),
                "objects": frame.get("objects", []),
                "interactions": frame.get("interactions", []),
            }
        )
    return frames


def ensure_action_log(data: Dict[str, Any]) -> Dict[str, Any]:
    if is_action_log(data):
        return data

    metadata = deepcopy(data.get("metadata", {}))
    now = datetime.now().isoformat()
    metadata.setdefault("schema_version", SCHEMA_VERSION)
    metadata.setdefault("generated_at", now)

    return {
        "metadata": metadata,
        "video_info": deepcopy(data.get("video_info", {})),
        "track_summary": deepcopy(data.get("track_summary", {})),
        "interaction_summary": deepcopy(data.get("interaction_summary", {})),
        "state_transitions": deepcopy(data.get("state_transitions", [])),
        "interactions": deepcopy(data.get("interactions", [])),
        "frames": _normalize_frames(data.get("frame_data", [])),
    }

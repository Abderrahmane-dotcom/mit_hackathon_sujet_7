"""IoU spike detection with rolling baseline."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple
from collections import deque

Box = Tuple[float, float, float, float]  # x1, y1, x2, y2


@dataclass(frozen=True)
class TriggerEvent:
    frame_idx: int
    iou_value: float
    baseline: float
    window_start: int
    window_end: int


@dataclass(frozen=True)
class TriggerStep:
    triggered: bool
    baseline: float
    delta: float
    in_window: bool


def iou(box_a: Box, box_b: Box) -> float:
    """Compute IoU for two axis-aligned boxes."""
    ax1, ay1, ax2, ay2 = box_a
    bx1, by1, bx2, by2 = box_b

    inter_x1 = max(ax1, bx1)
    inter_y1 = max(ay1, by1)
    inter_x2 = min(ax2, bx2)
    inter_y2 = min(ay2, by2)
    inter_w = max(0.0, inter_x2 - inter_x1)
    inter_h = max(0.0, inter_y2 - inter_y1)
    inter_area = inter_w * inter_h

    area_a = max(0.0, ax2 - ax1) * max(0.0, ay2 - ay1)
    area_b = max(0.0, bx2 - bx1) * max(0.0, by2 - by1)
    union_area = area_a + area_b - inter_area
    return inter_area / union_area if union_area > 0 else 0.0


class RollingSpikeTrigger:
    """Detect IoU spikes using a rolling baseline window."""

    def __init__(
        self,
        baseline_window: int = 8,
        spike_delta: float = 0.15,
        min_iou: float = 0.05,
        cooldown_frames: int = 6,
        event_window: int = 10,
    ) -> None:
        if baseline_window <= 0:
            raise ValueError("baseline_window must be positive")
        if event_window <= 0:
            raise ValueError("event_window must be positive")

        self.baseline_window = baseline_window
        self.spike_delta = spike_delta
        self.min_iou = min_iou
        self.cooldown_frames = cooldown_frames
        self.event_window = event_window

        self._history = deque(maxlen=baseline_window)
        self._last_trigger_frame = -10**9

    def reset(self) -> None:
        self._history.clear()
        self._last_trigger_frame = -10**9

    def step(self, frame_idx: int, iou_value: float) -> TriggerStep:
        baseline = sum(self._history) / len(self._history) if self._history else 0.0
        can_trigger = (frame_idx - self._last_trigger_frame) >= self.cooldown_frames
        spike = (iou_value - baseline) >= self.spike_delta and iou_value >= self.min_iou
        triggered = bool(can_trigger and spike)
        if triggered:
            self._last_trigger_frame = frame_idx
        self._history.append(iou_value)
        in_window = frame_idx < (self._last_trigger_frame + self.event_window)
        return TriggerStep(
            triggered=triggered,
            baseline=baseline,
            delta=iou_value - baseline,
            in_window=in_window,
        )

    def event_from_step(self, frame_idx: int, iou_value: float) -> TriggerEvent | None:
        step = self.step(frame_idx, iou_value)
        if not step.triggered:
            return None
        return TriggerEvent(
            frame_idx=frame_idx,
            iou_value=iou_value,
            baseline=step.baseline,
            window_start=frame_idx,
            window_end=frame_idx + self.event_window,
        )

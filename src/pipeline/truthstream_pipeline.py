"""Pipeline stub that operates on precomputed detections."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, Iterable, List, Tuple

from src.interaction.iou_trigger import Box, RollingSpikeTrigger, iou
from src.interaction.state_memory import StateMemory


@dataclass(frozen=True)
class FrameDetections:
    frame_idx: int
    agents: Dict[str, Box]
    objects: Dict[str, Box]


@dataclass(frozen=True)
class InteractionEvent:
    frame_idx: int
    agent_id: str
    object_id: str
    iou_value: float
    baseline: float
    window_start: int
    window_end: int


def run_pipeline(
    frames: Iterable[FrameDetections],
    state_memory: StateMemory | None = None,
    trigger_factory: Callable[[], RollingSpikeTrigger] | None = None,
    on_interaction: Callable[[InteractionEvent], str | None] | None = None,
) -> Tuple[List[InteractionEvent], List]:
    """Run the interaction stage using precomputed detections.

    This is a stub for integration with detection/tracking. It emits interaction
    events and optionally updates state using the provided callback.
    """

    state_memory = state_memory or StateMemory()
    trigger_factory = trigger_factory or RollingSpikeTrigger

    triggers: Dict[Tuple[str, str], RollingSpikeTrigger] = {}
    events: List[InteractionEvent] = []

    for frame in frames:
        for agent_id, agent_box in frame.agents.items():
            for object_id, object_box in frame.objects.items():
                key = (agent_id, object_id)
                trigger = triggers.setdefault(key, trigger_factory())
                value = iou(agent_box, object_box)
                step = trigger.step(frame.frame_idx, value)
                if not step.triggered:
                    continue
                event = InteractionEvent(
                    frame_idx=frame.frame_idx,
                    agent_id=agent_id,
                    object_id=object_id,
                    iou_value=value,
                    baseline=step.baseline,
                    window_start=frame.frame_idx,
                    window_end=frame.frame_idx + trigger.event_window,
                )
                events.append(event)

                if on_interaction:
                    new_state = on_interaction(event)
                    if new_state is not None:
                        state_memory.update_state(
                            object_id,
                            new_state,
                            frame.frame_idx,
                            reason="interaction_callback",
                        )

    return events, state_memory.history

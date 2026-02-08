"""Per-object state memory for interaction tracking."""

from dataclasses import dataclass
from typing import Dict, List


VALID_STATES = {"unknown", "closed", "open"}


@dataclass(frozen=True)
class StateTransition:
    object_id: str
    frame_idx: int
    before: str
    after: str
    reason: str


class StateMemory:
    """Store state per object and record transitions."""

    def __init__(self):
        self._states: Dict[str, str] = {}
        self._history: List[StateTransition] = []

    def get_state(self, object_id: str) -> str:
        return self._states.get(object_id, "unknown")

    def update_state(self, object_id: str, new_state: str, frame_idx: int, reason: str) -> bool:
        if new_state not in VALID_STATES:
            raise ValueError(f"Invalid state: {new_state}")
        prev_state = self.get_state(object_id)
        if prev_state == new_state:
            return False
        self._states[object_id] = new_state
        self._history.append(
            StateTransition(
                object_id=object_id,
                frame_idx=frame_idx,
                before=prev_state,
                after=new_state,
                reason=reason,
            )
        )
        return True

    def clear(self):
        self._states.clear()
        self._history.clear()

    @property
    def history(self) -> List[StateTransition]:
        return list(self._history)

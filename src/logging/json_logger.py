"""Action log JSON writer."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from .schema import ensure_action_log


class JsonLogger:
    def __init__(self, output_dir: str = "output") -> None:
        self.output_dir = Path(output_dir)

    def write(self, data: Dict[str, Any], filename: str = "action_log.json") -> Path:
        action_log = ensure_action_log(data)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        output_path = self.output_dir / filename
        with output_path.open("w", encoding="utf-8") as handle:
            json.dump(action_log, handle, indent=2)
        return output_path


def write_action_log(data: Dict[str, Any], output_path: str) -> Path:
    action_log = ensure_action_log(data)
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with output_file.open("w", encoding="utf-8") as handle:
        json.dump(action_log, handle, indent=2)
    return output_file

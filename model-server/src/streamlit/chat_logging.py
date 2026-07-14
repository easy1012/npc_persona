from __future__ import annotations

import json
from pathlib import Path


def build_interaction_log(user_message: str, response_text: str) -> dict[str, str]:
    return {
        "input": user_message,
        "output": response_text,
    }


def append_interaction_log(path: Path, record: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as log_file:
        log_file.write(json.dumps(record, ensure_ascii=False) + "\n")

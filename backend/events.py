from __future__ import annotations

import json
from pathlib import Path

from backend.config import BACKEND_DIR
from backend.schemas import GuideActionPayload, now_iso8601


EVENT_LOG_PATH = BACKEND_DIR / "logs" / "ai_events.jsonl"


def log_ai_event(
    *,
    session_id: str,
    message_type: str,
    guide_action: GuideActionPayload,
    context: dict | None = None,
) -> None:
    EVENT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "timestamp": now_iso8601(),
        "session_id": session_id,
        "message_type": message_type,
        "action_cmd": guide_action.action_cmd,
        "parameters": guide_action.parameters,
        "spoken_response": guide_action.spoken_response,
        "context": context or {},
    }
    with EVENT_LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")

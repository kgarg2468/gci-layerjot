from __future__ import annotations

import json
import logging
from time import perf_counter

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from pydantic import ValidationError

from backend.config import settings
from backend.orchestrator import run_agent
from backend.schemas import (
    AIRequestEnvelope,
    AIResponseEnvelope,
    DebugPayload,
    fallback_payload,
    now_iso8601,
)


logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
)
LOGGER = logging.getLogger("gci.backend")

app = FastAPI(title="GCI Mac MVP Backend", version="0.1.0")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    LOGGER.info("WebSocket client connected.")

    try:
        while True:
            raw = await websocket.receive_text()

            try:
                message = json.loads(raw)
            except json.JSONDecodeError:
                LOGGER.warning("Received malformed JSON.")
                await websocket.send_text(
                    json.dumps(
                        {
                            "type": "error",
                            "session_id": "unknown",
                            "timestamp": now_iso8601(),
                            "payload": {
                                "message": "Malformed JSON",
                            },
                        }
                    )
                )
                continue

            msg_type = message.get("type")

            if msg_type == "ping":
                await websocket.send_text(
                    json.dumps(
                        {
                            "type": "pong",
                            "session_id": message.get("session_id", "unknown"),
                            "timestamp": now_iso8601(),
                            "payload": {},
                        }
                    )
                )
                continue

            if msg_type != "ai_request":
                await websocket.send_text(
                    json.dumps(
                        {
                            "type": "error",
                            "session_id": message.get("session_id", "unknown"),
                            "timestamp": now_iso8601(),
                            "payload": {
                                "message": f"Unsupported message type: {msg_type}",
                            },
                        }
                    )
                )
                continue

            try:
                request = AIRequestEnvelope.model_validate(message)
            except ValidationError as exc:
                LOGGER.warning("Invalid ai_request payload: %s", exc)
                await websocket.send_text(
                    json.dumps(
                        {
                            "type": "error",
                            "session_id": message.get("session_id", "unknown"),
                            "timestamp": now_iso8601(),
                            "payload": {
                                "message": "Invalid ai_request payload",
                            },
                        }
                    )
                )
                continue

            start = perf_counter()
            payload = await run_agent(
                transcript=request.payload.transcript,
                context=request.payload.context.model_dump(),
            )
            latency_ms = int((perf_counter() - start) * 1000)

            if payload.debug is None:
                payload.debug = DebugPayload(latency_ms=latency_ms)
            else:
                payload.debug.latency_ms = latency_ms

            response = AIResponseEnvelope(
                type="ai_response",
                session_id=request.session_id,
                timestamp=now_iso8601(),
                payload=payload,
            )

            await websocket.send_text(response.model_dump_json())

    except WebSocketDisconnect:
        LOGGER.info("WebSocket client disconnected.")
    except Exception:
        LOGGER.exception("WebSocket server failure.")
        fallback = AIResponseEnvelope(
            type="ai_response",
            session_id="unknown",
            timestamp=now_iso8601(),
            payload=fallback_payload(),
        )
        try:
            await websocket.send_text(fallback.model_dump_json())
        except Exception:
            pass

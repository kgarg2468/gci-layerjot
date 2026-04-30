from __future__ import annotations

from contextlib import asynccontextmanager
import json
import logging
from time import perf_counter

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from pydantic import ValidationError

from backend.config import settings
from backend.action_contract import to_guide_action
from backend.events import log_ai_event
from backend.orchestrator import run_agent
from backend.procedure import build_procedure_summary, detect_procedure_alert
from backend.rag.ingest import ingest_docs, is_ingested
from backend.schemas import (
    AIRequestEnvelope,
    AIResponseEnvelope,
    AIResponsePayload,
    DebugPayload,
    GuideActionPayload,
    fallback_payload,
    now_iso8601,
)
from backend.vision import analyze_camera_frame


logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
)
LOGGER = logging.getLogger("gci.backend")


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        if not settings.openai_api_key:
            LOGGER.info("RAG ingest: skipped (no OPENAI_API_KEY set).")
        elif is_ingested():
            LOGGER.info("RAG ingest: skipped (chroma_db already populated).")
        else:
            LOGGER.info("RAG ingest: building vector store from backend/docs ...")
            ingest_docs()
            LOGGER.info("RAG ingest: built.")
    except Exception:
        LOGGER.exception("RAG ingest failed at startup — falling back to text search.")
    yield


app = FastAPI(title="GCI Mac MVP Backend", version="0.1.0", lifespan=lifespan)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


async def _send_ai_response(
    websocket: WebSocket,
    *,
    session_id: str,
    payload: AIResponsePayload,
    guide_action: GuideActionPayload,
    message_type: str,
    context: dict | None = None,
) -> None:
    response = AIResponseEnvelope(
        type="ai_response",
        session_id=session_id,
        timestamp=now_iso8601(),
        payload=payload,
        action_cmd=guide_action.action_cmd,
        parameters=guide_action.parameters,
        spoken_response=guide_action.spoken_response,
    )
    try:
        log_ai_event(
            session_id=session_id,
            message_type=message_type,
            guide_action=guide_action,
            context=context,
        )
    except Exception:
        LOGGER.exception("Failed to log AI event.")
    await websocket.send_text(response.model_dump_json())


def _payload_from_guide_action(guide_action: GuideActionPayload) -> AIResponsePayload:
    if guide_action.action_cmd in {"show_alert", "flag_breach"}:
        intent = "safety_block" if guide_action.action_cmd == "show_alert" else "clarify"
    elif guide_action.action_cmd == "end_procedure":
        intent = "clarify"
    else:
        intent = "rag"

    return AIResponsePayload(
        intent=intent,
        spoken_response=guide_action.spoken_response,
        action={
            "type": guide_action.action_cmd,
            "params": guide_action.parameters,
        },
    )


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

            if msg_type == "camera_frame":
                payload = message.get("payload") if isinstance(message.get("payload"), dict) else {}
                guide_action = analyze_camera_frame(payload)
                await _send_ai_response(
                    websocket,
                    session_id=message.get("session_id", "unknown"),
                    payload=_payload_from_guide_action(guide_action),
                    guide_action=guide_action,
                    message_type="camera_frame",
                    context=payload.get("context") if isinstance(payload.get("context"), dict) else {},
                )
                continue

            if msg_type == "procedure_complete":
                payload = message.get("payload") if isinstance(message.get("payload"), dict) else {}
                guide_action = build_procedure_summary(payload)
                await _send_ai_response(
                    websocket,
                    session_id=message.get("session_id", "unknown"),
                    payload=_payload_from_guide_action(guide_action),
                    guide_action=guide_action,
                    message_type="procedure_complete",
                    context=payload,
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
            context = request.payload.context.model_dump()
            guide_action = detect_procedure_alert(
                transcript=request.payload.transcript,
                context=context,
            )
            if guide_action is not None:
                payload = _payload_from_guide_action(guide_action)
            else:
                payload = await run_agent(
                    transcript=request.payload.transcript,
                    context=context,
                )
                sources = payload.debug.sources if payload.debug is not None else []
                guide_action = to_guide_action(payload, context=context, sources=sources)
            latency_ms = int((perf_counter() - start) * 1000)

            if payload.debug is None:
                payload.debug = DebugPayload(latency_ms=latency_ms)
            else:
                payload.debug.latency_ms = latency_ms

            await _send_ai_response(
                websocket,
                session_id=request.session_id,
                payload=payload,
                guide_action=guide_action,
                message_type="ai_request",
                context=context,
            )

    except WebSocketDisconnect:
        LOGGER.info("WebSocket client disconnected.")
    except Exception:
        LOGGER.exception("WebSocket server failure.")
        fb = fallback_payload()
        fb.debug = DebugPayload(latency_ms=0)
        fallback = AIResponseEnvelope(
            type="ai_response",
            session_id="unknown",
            timestamp=now_iso8601(),
            payload=fb,
            action_cmd="show_alert",
            parameters={"severity": "error", "message": fb.spoken_response},
            spoken_response=fb.spoken_response,
        )
        try:
            await websocket.send_text(fallback.model_dump_json())
        except Exception:
            pass

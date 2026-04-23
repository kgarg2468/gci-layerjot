from __future__ import annotations

from contextlib import asynccontextmanager
import json
import logging
from time import perf_counter

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from pydantic import ValidationError

from backend.config import settings
from backend.orchestrator import run_agent
from backend.rag.ingest import ingest_docs, is_ingested
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
        fb = fallback_payload()
        fb.debug = DebugPayload(latency_ms=0)
        fallback = AIResponseEnvelope(
            type="ai_response",
            session_id="unknown",
            timestamp=now_iso8601(),
            payload=fb,
        )
        try:
            await websocket.send_text(fallback.model_dump_json())
        except Exception:
            pass

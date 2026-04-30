from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


IntentType = Literal[
    "retrieve_data",
    "navigate",
    "rag",
    "clarify",
    "safety_block",
    "error",
]

ActionCommand = Literal[
    "next_step",
    "prev_step",
    "show_alert",
    "read_step",
    "flag_breach",
    "end_procedure",
    "navigate_home",
]


class ContextPayload(BaseModel):
    patient_id: Optional[str] = None
    current_screen: str = "home"
    current_step: Optional[int] = None
    procedure_active: bool = False
    session_id: str
    procedure_id: Optional[str] = None
    procedure_name: Optional[str] = None
    current_step_id: Optional[int] = None
    current_step_title: Optional[str] = None
    total_steps: Optional[int] = None
    completed_step_ids: List[int] = Field(default_factory=list)
    missed_step_ids: List[int] = Field(default_factory=list)
    started_at: Optional[str] = None


class AIRequestPayload(BaseModel):
    transcript: str
    context: ContextPayload


class AIRequestEnvelope(BaseModel):
    type: Literal["ai_request"]
    session_id: str
    timestamp: str
    payload: AIRequestPayload


class ActionPayload(BaseModel):
    type: str
    params: Dict[str, Any] = Field(default_factory=dict)


class DebugPayload(BaseModel):
    tool_called: Optional[str] = None
    tool_calls: List[str] = Field(default_factory=list)
    tool_inputs: List[Dict[str, Any]] = Field(default_factory=list)
    sources: List[str] = Field(default_factory=list)
    latency_ms: Optional[int] = None


class AIResponsePayload(BaseModel):
    intent: IntentType
    spoken_response: str
    action: Optional[ActionPayload] = None
    debug: Optional[DebugPayload] = None


class GuideActionPayload(BaseModel):
    action_cmd: ActionCommand
    parameters: Dict[str, Any] = Field(default_factory=dict)
    spoken_response: str


class AIResponseEnvelope(BaseModel):
    type: Literal["ai_response"]
    session_id: str
    timestamp: str
    payload: AIResponsePayload
    schema_version: str = "clabsi-ar.v1"
    action_cmd: Optional[ActionCommand] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)
    spoken_response: str = ""


class BasicEnvelope(BaseModel):
    type: str
    session_id: str
    timestamp: str
    payload: Dict[str, Any] = Field(default_factory=dict)


def now_iso8601() -> str:
    return datetime.now(timezone.utc).isoformat()


def fallback_payload(
    message: str = "I'm having trouble with that request. Please try again.",
) -> AIResponsePayload:
    return AIResponsePayload(intent="error", spoken_response=message, action=None)

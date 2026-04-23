from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional, TypedDict

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph

from backend.config import settings
from backend.prompts import ROUTER_SYSTEM_PROMPT, SYNTHESIS_SYSTEM_PROMPT
from backend.safety import safety_check
from backend.schemas import AIResponsePayload, ActionPayload, DebugPayload, fallback_payload
from backend.tools import TOOL_REGISTRY


LOGGER = logging.getLogger(__name__)


class AgentState(TypedDict, total=False):
    transcript: str
    context: dict
    messages: List[BaseMessage]
    tool_results: List[Dict[str, Any]]
    safety_violation: Optional[str]
    final_payload: Optional[AIResponsePayload]


def _build_router_llm() -> ChatOpenAI:
    llm = ChatOpenAI(
        model=settings.llm_model,
        temperature=settings.llm_temperature,
        api_key=settings.openai_api_key or None,
    )
    return llm.bind_tools(list(TOOL_REGISTRY.values()), tool_choice="auto")


def _build_synthesis_llm():
    llm = ChatOpenAI(
        model=settings.llm_model,
        temperature=settings.llm_temperature,
        api_key=settings.openai_api_key or None,
    )
    return llm.with_structured_output(AIResponsePayload)


async def _safety_node(state: AgentState) -> AgentState:
    violation = safety_check(state["transcript"], state["context"])
    if violation:
        state["safety_violation"] = violation
        state["final_payload"] = AIResponsePayload(
            intent="safety_block",
            spoken_response=violation,
            action=None,
        )
    return state


async def _router_node(state: AgentState) -> AgentState:
    router_llm = _build_router_llm()
    route_messages: List[BaseMessage] = [
        SystemMessage(content=ROUTER_SYSTEM_PROMPT),
        HumanMessage(
            content=(
                f"Transcript: {state['transcript']}\n"
                f"Context JSON:\n{json.dumps(state['context'], indent=2)}"
            )
        ),
    ]
    ai_message = await router_llm.ainvoke(route_messages)
    state["messages"] = route_messages + [ai_message]
    return state


async def _tool_executor_node(state: AgentState) -> AgentState:
    last = state["messages"][-1]
    tool_calls = list(getattr(last, "tool_calls", []) or [])
    results: List[Dict[str, Any]] = []
    new_messages: List[BaseMessage] = []

    for tool_call in tool_calls:
        tool_name = tool_call.get("name")
        tool_args = tool_call.get("args", {}) or {}

        tool = TOOL_REGISTRY.get(tool_name)
        if tool is None:
            tool_result = {"error": f"Unknown tool: {tool_name}"}
        else:
            try:
                tool_result = await tool.ainvoke(tool_args)
            except Exception as exc:  # pragma: no cover - defensive fallback
                LOGGER.exception("Tool execution failed: %s", tool_name)
                tool_result = {"error": f"Tool failed: {exc}"}

        results.append(
            {
                "name": tool_name,
                "args": tool_args,
                "result": tool_result,
            }
        )
        new_messages.append(
            ToolMessage(
                content=json.dumps(tool_result),
                tool_call_id=tool_call.get("id", tool_name),
                name=tool_name,
            )
        )

    state["messages"] = state["messages"] + new_messages
    state["tool_results"] = results
    return state


async def _synthesis_node(state: AgentState) -> AgentState:
    synthesis_llm = _build_synthesis_llm()
    tool_results = state.get("tool_results", [])
    synthesis_messages: List[BaseMessage] = [
        SystemMessage(content=SYNTHESIS_SYSTEM_PROMPT),
        HumanMessage(
            content=(
                f"Transcript: {state['transcript']}\n"
                f"Context:\n{json.dumps(state['context'], indent=2)}\n\n"
                f"Tool results (JSON):\n{json.dumps(tool_results, indent=2)}"
            )
        ),
    ]
    candidate_payload = await synthesis_llm.ainvoke(synthesis_messages)
    state["final_payload"] = _enforce_output_guards(candidate_payload, tool_results)
    return state


def _route_after_safety(state: AgentState) -> str:
    return END if state.get("safety_violation") else "router"


def _route_after_router(state: AgentState) -> str:
    last = state["messages"][-1]
    tool_calls = list(getattr(last, "tool_calls", []) or [])
    return "tool_executor" if tool_calls else "synthesis"


def _build_graph():
    graph = StateGraph(AgentState)
    graph.add_node("safety_gate", _safety_node)
    graph.add_node("router", _router_node)
    graph.add_node("tool_executor", _tool_executor_node)
    graph.add_node("synthesis", _synthesis_node)
    graph.add_edge(START, "safety_gate")
    graph.add_conditional_edges("safety_gate", _route_after_safety, {END: END, "router": "router"})
    graph.add_conditional_edges(
        "router",
        _route_after_router,
        {"tool_executor": "tool_executor", "synthesis": "synthesis"},
    )
    graph.add_edge("tool_executor", "synthesis")
    graph.add_edge("synthesis", END)
    return graph.compile()


_GRAPH = None


def _graph():
    global _GRAPH
    if _GRAPH is None:
        _GRAPH = _build_graph()
    return _GRAPH


def _heuristic_fallback(transcript: str, context: dict) -> AIResponsePayload:
    lowered = transcript.lower()

    if "open" in lowered and "checklist" in lowered:
        return AIResponsePayload(
            intent="navigate",
            spoken_response="Opening the central line checklist.",
            action=ActionPayload(
                type="open_screen",
                params={"screen": "central_line_checklist"},
            ),
        )

    if any(keyword in lowered for keyword in ["heart rate", "vitals", "blood pressure"]):
        patient_id = context.get("patient_id")
        if not patient_id:
            return AIResponsePayload(
                intent="safety_block",
                spoken_response="I don't have an active patient loaded. Please select a patient first.",
                action=None,
            )

        tool_result = TOOL_REGISTRY["get_patient_vitals"].invoke({"patient_id": patient_id})
        if isinstance(tool_result, dict) and "error" in tool_result:
            return AIResponsePayload(
                intent="error",
                spoken_response="I could not retrieve patient vitals right now.",
                action=None,
            )

        heart_rate = tool_result.get("heart_rate")
        return AIResponsePayload(
            intent="retrieve_data",
            spoken_response=f"The patient's heart rate is {heart_rate} beats per minute.",
            action=None,
        )

    if any(keyword in lowered for keyword in ["sterile", "protocol", "precaution"]):
        tool_result = TOOL_REGISTRY["query_protocol"].invoke({"query": transcript})
        snippets = tool_result.get("results", [])
        if not snippets:
            return AIResponsePayload(
                intent="rag",
                spoken_response="I could not find matching protocol guidance in the local documents.",
                action=None,
            )
        first = snippets[0]["content"][:220].strip()
        return AIResponsePayload(
            intent="rag",
            spoken_response=first,
            action=None,
        )

    return AIResponsePayload(
        intent="clarify",
        spoken_response="I did not catch the request. Please rephrase.",
        action=None,
    )


def _enforce_output_guards(
    candidate: AIResponsePayload,
    tool_results: List[Dict[str, Any]],
) -> AIResponsePayload:
    tool_names = [item["name"] for item in tool_results]

    # Never allow retrieve_data unless vitals tool was actually called.
    if candidate.intent == "retrieve_data" and "get_patient_vitals" not in tool_names:
        return AIResponsePayload(
            intent="clarify",
            spoken_response=(
                "I need to verify patient data first. Please ask again and confirm the active patient."
            ),
            action=None,
        )

    # Only open_screen actions are supported in this Mac MVP.
    if candidate.action and candidate.action.type != "open_screen":
        candidate.action = None

    # Normalize navigation actions from the actual tool result when the model omits screen details.
    if candidate.intent == "navigate":
        needs_screen = (
            candidate.action is None
            or candidate.action.type != "open_screen"
            or not candidate.action.params.get("screen")
        )
        if needs_screen:
            for result in tool_results:
                if result["name"] == "open_screen" and isinstance(result["result"], dict):
                    screen = result["result"].get("screen")
                    if screen:
                        candidate.action = ActionPayload(
                            type="open_screen",
                            params={"screen": screen},
                        )
                        break

    return candidate


async def run_agent(transcript: str, context: dict) -> AIResponsePayload:
    violation = safety_check(transcript, context)
    if violation:
        return AIResponsePayload(intent="safety_block", spoken_response=violation, action=None)

    if not settings.openai_api_key:
        LOGGER.warning("OPENAI_API_KEY not set — using heuristic fallback orchestrator.")
        payload = _heuristic_fallback(transcript, context)
        payload.debug = DebugPayload(tool_called=None, tool_calls=[], tool_inputs=[])
        return payload

    try:
        initial_state: AgentState = {
            "transcript": transcript,
            "context": context,
            "messages": [],
            "tool_results": [],
            "safety_violation": None,
            "final_payload": None,
        }
        final_state = await _graph().ainvoke(initial_state)
        payload = final_state["final_payload"]
        tool_results = final_state.get("tool_results") or []

        payload.debug = DebugPayload(
            tool_called=tool_results[0]["name"] if tool_results else None,
            tool_calls=[item["name"] for item in tool_results],
            tool_inputs=[item["args"] for item in tool_results],
        )
        return payload

    except Exception:  # pragma: no cover - network/runtime fallback
        LOGGER.exception("Agent execution failed.")
        return fallback_payload()

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from backend.config import settings
from backend.safety import safety_check
from backend.schemas import AIResponsePayload, ActionPayload, DebugPayload, fallback_payload
from backend.tools import TOOL_REGISTRY


LOGGER = logging.getLogger(__name__)


ROUTER_SYSTEM_PROMPT = """
You are GCI, an AI clinical assistant for CLABSI prevention procedures.
You are an execution engine, not a chatbot.

Decide whether to call tools before answering.
Use tools for real patient data and protocol data.
""".strip()


SYNTHESIS_SYSTEM_PROMPT = """
You are GCI, an AI clinical assistant for CLABSI prevention procedures.

Rules:
1. Keep spoken_response concise (1-2 sentences).
2. Never fabricate patient data. If patient data is needed, it must come from tool results.
3. Never make diagnosis or medication dosing recommendations.
4. If intent is unclear, return intent=clarify.
5. Return only schema fields from AIResponsePayload.

Allowed intents:
- retrieve_data
- navigate
- rag
- clarify
- safety_block
- error

Action policy for this MVP:
- Only open_screen action is supported.
- If no action is needed, set action to null.
""".strip()


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


async def _execute_tools(tool_calls: List[dict]) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []

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

    return results


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

    # If navigation intent but action is missing, derive from tool result when possible.
    if candidate.intent == "navigate" and candidate.action is None:
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
        payload = _heuristic_fallback(transcript, context)
        payload.debug = DebugPayload(tool_called=None, tool_calls=[], tool_inputs=[])
        return payload

    try:
        router_llm = _build_router_llm()
        synthesis_llm = _build_synthesis_llm()

        route_messages = [
            SystemMessage(content=ROUTER_SYSTEM_PROMPT),
            HumanMessage(
                content=(
                    f"Transcript: {transcript}\n"
                    f"Context JSON:\n{json.dumps(context, indent=2)}"
                )
            ),
        ]

        router_response = await router_llm.ainvoke(route_messages)
        tool_calls = list(getattr(router_response, "tool_calls", []) or [])
        tool_results = await _execute_tools(tool_calls)

        synthesis_messages = [
            SystemMessage(content=SYNTHESIS_SYSTEM_PROMPT),
            HumanMessage(
                content=(
                    f"Transcript: {transcript}\n"
                    f"Context:\n{json.dumps(context, indent=2)}\n\n"
                    f"Tool results (JSON):\n{json.dumps(tool_results, indent=2)}"
                )
            ),
        ]

        candidate_payload = await synthesis_llm.ainvoke(synthesis_messages)
        payload = _enforce_output_guards(candidate_payload, tool_results)

        payload.debug = DebugPayload(
            tool_called=tool_results[0]["name"] if tool_results else None,
            tool_calls=[item["name"] for item in tool_results],
            tool_inputs=[item["args"] for item in tool_results],
        )
        return payload

    except Exception:  # pragma: no cover - network/runtime fallback
        LOGGER.exception("Agent execution failed.")
        return fallback_payload()

from __future__ import annotations

from langchain_core.tools import tool

from backend.rag.pipeline import query_protocol_docs


@tool
def query_protocol(query: str) -> dict:
    """
    Search protocol docs for procedural information.
    Use when asked about sterile precautions or CLABSI protocol details.
    """
    results = query_protocol_docs(query)
    if not results:
        return {
            "query": query,
            "results": [],
            "note": "No matching protocol content found.",
        }

    return {
        "query": query,
        "results": results,
    }

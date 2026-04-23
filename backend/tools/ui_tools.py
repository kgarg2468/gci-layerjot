from __future__ import annotations

from langchain_core.tools import tool


VALID_SCREENS = {
    "home",
    "central_line_checklist",
    "patient_overview",
    "sterile_prep",
    "maintenance_protocol",
    "settings",
}


@tool
def open_screen(screen_name: str) -> dict:
    """
    Navigate to a supported screen.
    Use when the user asks to open or go to a specific screen.
    """
    if screen_name not in VALID_SCREENS:
        return {"error": f"Unknown screen: {screen_name}"}

    return {
        "action_type": "open_screen",
        "screen": screen_name,
        "status": "success",
    }

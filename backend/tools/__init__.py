from .patient_tools import get_patient_vitals
from .protocol_tools import query_protocol
from .ui_tools import open_screen

ALL_TOOLS = [
    get_patient_vitals,
    open_screen,
    query_protocol,
]

TOOL_REGISTRY = {tool.name: tool for tool in ALL_TOOLS}

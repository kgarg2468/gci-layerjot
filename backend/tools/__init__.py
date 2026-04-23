from .patient_tools import get_patient_vitals, query_patient_records
from .protocol_tools import query_protocol
from .ui_tools import open_screen

ALL_TOOLS = [
    get_patient_vitals,
    query_patient_records,
    open_screen,
    query_protocol,
]

TOOL_REGISTRY = {tool.name: tool for tool in ALL_TOOLS}

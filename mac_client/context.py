from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

from mac_client.config import settings


@dataclass
class ClientContext:
    patient_id: str | None
    current_screen: str
    current_step: int | None
    procedure_active: bool
    session_id: str

    @classmethod
    def create_default(cls) -> "ClientContext":
        return cls(
            patient_id=settings.default_patient_id,
            current_screen=settings.default_screen,
            current_step=None,
            procedure_active=False,
            session_id=str(uuid4()),
        )

    def to_payload(self) -> dict:
        return {
            "patient_id": self.patient_id,
            "current_screen": self.current_screen,
            "current_step": self.current_step,
            "procedure_active": self.procedure_active,
            "session_id": self.session_id,
        }

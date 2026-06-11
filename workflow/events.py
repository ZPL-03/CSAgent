"""工作流事件模型。"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class WorkflowEvent:
    """单条工作流审计事件。"""

    run_id: str
    event_type: str
    agent: str
    message: str
    stage: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=utc_now_iso)

    def to_record(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "event_type": self.event_type,
            "agent": self.agent,
            "message": self.message,
            "stage": self.stage,
            "payload": self.payload,
            "created_at": self.created_at,
        }

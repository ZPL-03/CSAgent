"""智能体基类。"""

from __future__ import annotations

from typing import Any, Callable, Dict, Optional

from core.logging_utils import get_logger


ProgressCallback = Optional[Callable[[str, str], None]]


class BaseAgent:
    """所有智能体统一继承的基类。"""

    agent_name = "BASE"

    def __init__(self, progress_callback: ProgressCallback = None) -> None:
        self.progress_callback = progress_callback
        self.logger = get_logger(self.agent_name)

    def emit(self, message: str) -> None:
        self.emit_event("info", message)

    def emit_event(self, event_type: str, message: str, payload: Dict[str, Any] | None = None) -> None:
        event_payload = payload or {}
        self.logger.info(f"[{event_type}] {message}")
        if not self.progress_callback:
            return

        try:
            self.progress_callback(
                self.agent_name,
                message,
                {
                    "agent": self.agent_name,
                    "event_type": event_type,
                    "message": message,
                    "payload": event_payload,
                },
            )
        except TypeError:
            self.progress_callback(self.agent_name, message)

    def run(self, input_data: Any) -> Any:
        raise NotImplementedError

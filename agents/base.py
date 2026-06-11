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

    def emit_llm_trace(self, llm_backend: Any, context: Dict[str, Any] | None = None) -> None:
        """把 LLM 后端调用轨迹写入智能体事件。"""

        trace = list(getattr(llm_backend, "last_call_trace", []) or [])
        if not trace:
            return
        successful = [item for item in trace if item.get("status") == "success"]
        selected = successful[-1] if successful else None
        fallback_used = bool(selected and trace and trace[0].get("backend") != selected.get("backend"))
        if selected:
            message = (
                f"LLM 调用完成：使用 {selected.get('backend')} / {selected.get('model')}，"
                f"后端尝试 {len(trace)} 次"
            )
        else:
            message = f"LLM 调用失败：后端尝试 {len(trace)} 次"
        self.emit_event(
            "llm_call_trace",
            message,
            {
                "context": context or {},
                "trace": trace,
                "selected_backend": selected.get("backend") if selected else None,
                "selected_model": selected.get("model") if selected else None,
                "fallback_used": fallback_used,
            },
        )

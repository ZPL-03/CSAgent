"""工作流工具注册与调用审计。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict


ToolCallable = Callable[[Dict[str, Any]], Dict[str, Any]]
ToolEventSink = Callable[[str, str, str, Dict[str, Any]], None]


@dataclass
class ToolSpec:
    """可审计工具定义。"""

    name: str
    agent: str
    description: str
    handler: ToolCallable
    input_schema: Dict[str, Any] = field(default_factory=dict)
    output_schema: Dict[str, Any] = field(default_factory=dict)


class ToolRegistry:
    """统一注册和调用工程工具。"""

    def __init__(self, event_sink: ToolEventSink | None = None) -> None:
        self._tools: Dict[str, ToolSpec] = {}
        self.event_sink = event_sink

    def register(self, spec: ToolSpec) -> None:
        if spec.name in self._tools:
            raise ValueError(f"工具已注册：{spec.name}")
        self._tools[spec.name] = spec

    def names(self) -> list[str]:
        return sorted(self._tools)

    def describe(self) -> list[Dict[str, Any]]:
        return [
            {
                "name": item.name,
                "agent": item.agent,
                "description": item.description,
                "input_schema": item.input_schema,
                "output_schema": item.output_schema,
            }
            for item in self._tools.values()
        ]

    def run(self, name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        if name not in self._tools:
            raise KeyError(f"未注册工具：{name}")
        spec = self._tools[name]
        if self.event_sink:
            self.event_sink("tool_started", spec.agent, f"开始调用工具 {name}", {"tool": name})
        try:
            result = spec.handler(payload)
        except Exception as exc:
            if self.event_sink:
                self.event_sink(
                    "tool_failed",
                    spec.agent,
                    f"工具 {name} 调用失败：{exc}",
                    {"tool": name, "error": str(exc)},
                )
            raise
        if self.event_sink:
            self.event_sink("tool_completed", spec.agent, f"工具 {name} 调用完成", {"tool": name})
        return result

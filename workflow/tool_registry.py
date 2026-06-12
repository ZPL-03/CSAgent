"""工作流工具注册与调用审计。"""

from __future__ import annotations

import time
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
        started_at = time.perf_counter()
        input_summary = _summarize_payload(payload)
        if self.event_sink:
            self.event_sink(
                "tool_started",
                spec.agent,
                f"开始调用工具 {name}",
                {
                    "tool": name,
                    "description": spec.description,
                    "input_schema": spec.input_schema,
                    "output_schema": spec.output_schema,
                    "input_summary": input_summary,
                },
            )
        try:
            result = spec.handler(payload)
        except Exception as exc:
            duration_ms = round((time.perf_counter() - started_at) * 1000.0, 3)
            if self.event_sink:
                self.event_sink(
                    "tool_failed",
                    spec.agent,
                    f"工具 {name} 调用失败：{exc}",
                    {
                        "tool": name,
                        "description": spec.description,
                        "error": str(exc),
                        "duration_ms": duration_ms,
                        "input_summary": input_summary,
                    },
                )
            raise
        duration_ms = round((time.perf_counter() - started_at) * 1000.0, 3)
        if self.event_sink:
            self.event_sink(
                "tool_completed",
                spec.agent,
                f"工具 {name} 调用完成",
                {
                    "tool": name,
                    "description": spec.description,
                    "duration_ms": duration_ms,
                    "input_summary": input_summary,
                    "output_summary": _summarize_payload(result),
                },
            )
        return result


def _summarize_payload(value: Any, depth: int = 0) -> Any:
    """生成适合写入事件表的轻量摘要，避免保存大字段全文。"""

    if depth >= 2:
        return _scalar_summary(value)
    if isinstance(value, dict):
        summary: Dict[str, Any] = {}
        for key, item in value.items():
            if key in {"content", "content_markdown", "content_plain", "error_log"}:
                summary[key] = {"type": type(item).__name__, "chars": len(str(item))}
            else:
                summary[str(key)] = _summarize_payload(item, depth + 1)
        return summary
    if isinstance(value, list):
        return {
            "type": "list",
            "count": len(value),
            "sample": [_summarize_payload(item, depth + 1) for item in value[:3]],
        }
    return _scalar_summary(value)


def _scalar_summary(value: Any) -> Any:
    if isinstance(value, (str, int, float, bool)) or value is None:
        text = str(value)
        if isinstance(value, str) and len(text) > 160:
            return text[:157] + "..."
        return value
    return {"type": type(value).__name__, "repr": str(value)[:160]}

"""任务配置与事实边界展示组件。"""

from __future__ import annotations

import json
from html import escape
from typing import Any

from PyQt6.QtWidgets import QTextBrowser

from core.task_contract import (
    describe_boundary_conditions,
    describe_load_conditions,
    task_payload_from_request,
)


class TaskConfigWidget(QTextBrowser):
    """展示结构化任务契约、用户事实和工程域参数边界。"""

    def __init__(self) -> None:
        super().__init__()
        self.setOpenExternalLinks(False)
        self.reset_view()

    def reset_view(self) -> None:
        self.setHtml(
            "<h3>任务配置</h3>"
            "<p>输入自然语言设计需求并完成任务解析后，这里会展示结构化任务契约、用户已给事实、"
            "几何参考、固定几何约束、候选生成控制参数和初筛控制参数。</p>"
        )

    def update_task(self, task: dict[str, Any] | None) -> None:
        if not task:
            self.reset_view()
            return

        payload = task_payload_from_request(task)
        material = payload.get("material_system") or {}
        generation = payload.get("candidate_generation_preferences") or {}
        screening = payload.get("screening_preferences") or {}
        targets = payload.get("design_targets") or {}
        facts = payload.get("user_input_facts") or {}
        envelope = payload.get("geometry_envelope") or {}
        reference_geometry = facts.get("geometry_reference") or {}
        fixed_geometry = facts.get("fixed_geometry") or {}

        html = (
            "<h3>任务配置</h3>"
            + self._section(
                "任务契约",
                [
                    ("任务编号", task.get("task_id") or "-"),
                    ("应用对象", payload.get("application") or "-"),
                    ("壳体类型", payload.get("hull_type") or "-"),
                    ("载荷工况", describe_load_conditions(payload.get("load_conditions") or {})),
                    ("边界条件", describe_boundary_conditions(payload.get("boundary_conditions") or {})),
                    ("材料体系", material.get("name") or "-"),
                ],
            )
            + self._section(
                "设计控制参数",
                [
                    ("候选池总数", generation.get("total_candidates")),
                    ("来源分配模式", generation.get("source_allocation_mode") or "-"),
                    ("LLM 指定数量", self._optional_count(generation.get("llm_candidates"))),
                    ("案例迁移指定数量", self._optional_count(generation.get("case_transfer_candidates"))),
                    ("DOE 指定数量", self._optional_count(generation.get("doe_candidates"))),
                    ("初筛保留数量", screening.get("top_k_candidates")),
                    ("极限压力目标", self._pressure_text(targets.get("ultimate_pressure_min_MPa"))),
                    ("优化目标", targets.get("primary_objective") or "-"),
                ],
            )
            + self._geometry_table("几何参数域", envelope)
            + self._dict_table("用户已给事实", facts)
            + self._dict_table("普通几何参考", reference_geometry)
            + self._dict_table("固定几何约束", fixed_geometry)
            + self._fact_boundary_note()
        )
        self.setHtml(html)

    def _section(self, title: str, rows: list[tuple[str, Any]]) -> str:
        body = "".join(
            f"<tr><th>{escape(str(label))}</th><td>{self._safe(value)}</td></tr>"
            for label, value in rows
        )
        return (
            f"<h4>{escape(title)}</h4>"
            "<table border='1' cellspacing='0' cellpadding='6'>"
            + body
            + "</table>"
        )

    def _geometry_table(self, title: str, geometry: dict[str, Any]) -> str:
        order = ["length_mm", "radius_mm", "thickness_mm", "alpha_deg", "beta_deg", "imperfection_ratio"]
        rows = []
        for key in order:
            value = geometry.get(key)
            if isinstance(value, list) and len(value) >= 2:
                text = f"{value[0]} - {value[1]}"
            else:
                text = value
            rows.append((key, text))
        return self._section(title, rows)

    def _dict_table(self, title: str, payload: dict[str, Any]) -> str:
        if not payload:
            return f"<h4>{escape(title)}</h4><p>无。</p>"
        rows = []
        for key, value in payload.items():
            rows.append((key, self._format_value(value)))
        return self._section(title, rows)

    def _format_value(self, value: Any) -> str:
        if isinstance(value, (dict, list)):
            return json.dumps(value, ensure_ascii=False, indent=2)
        return str(value)

    def _safe(self, value: Any) -> str:
        if value is None or value == "":
            return "-"
        return escape(str(value)).replace("\n", "<br>")

    def _optional_count(self, value: Any) -> str:
        return "未指定，按来源比例计算" if value is None else str(value)

    def _pressure_text(self, value: Any) -> str:
        return "-" if value is None or value == "" else f"{value} MPa"

    def _fact_boundary_note(self) -> str:
        return (
            "<h4>事实边界</h4>"
            "<ul>"
            "<li><code>user_input_facts</code> 只保存用户自然语言明确给出的事实。</li>"
            "<li><code>geometry_reference</code> 是设计中心和几何包络参考，不强制候选方案等于该数值。</li>"
            "<li><code>fixed_geometry</code> 是明确固定、限定或必须保持不变的几何约束，会覆盖候选对应参数。</li>"
            "<li>参数域、材料库、单位格式和有限元接口字段属于系统工程域约束，不作为用户事实发送给 LLM。</li>"
            "</ul>"
        )

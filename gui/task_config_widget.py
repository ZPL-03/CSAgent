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
from gui.i18n import DEFAULT_LANGUAGE


LABELS = {
    "zh": {
        "title": "任务配置",
        "empty": "输入自然语言设计需求并完成任务解析后，这里会展示结构化任务契约、用户已给事实、几何参考、固定几何约束、候选生成控制参数和初筛控制参数。",
        "contract": "任务契约",
        "task_id": "任务编号",
        "application": "应用对象",
        "hull_type": "壳体类型",
        "load": "载荷工况",
        "boundary": "边界条件",
        "material": "材料体系",
        "control": "设计控制参数",
        "total_candidates": "候选池总数",
        "source_mode": "来源分配模式",
        "llm_count": "LLM 指定数量",
        "case_count": "案例迁移指定数量",
        "doe_count": "DOE 指定数量",
        "top_k": "初筛保留数量",
        "target_pressure": "极限压力目标",
        "objective": "优化目标",
        "geometry_domain": "几何参数域",
        "facts": "用户已给事实",
        "reference_geometry": "普通几何参考",
        "fixed_geometry": "固定几何约束",
        "none": "无。",
        "unspecified": "未指定，按来源比例计算",
        "fact_title": "事实边界",
        "fact_note": (
            "<li><code>user_input_facts</code> 只保存用户自然语言明确给出的事实。</li>"
            "<li><code>geometry_reference</code> 是设计中心和几何包络参考，不强制候选方案等于该数值。</li>"
            "<li><code>fixed_geometry</code> 是明确固定、限定或必须保持不变的几何约束，会覆盖候选对应参数。</li>"
            "<li>参数域、材料库、单位格式和有限元接口字段属于系统工程域约束，不作为用户事实发送给 LLM。</li>"
        ),
    },
    "en": {
        "title": "Task Configuration",
        "empty": "After task parsing, this panel shows the structured task contract, user-provided facts, geometry references, fixed geometry constraints, candidate-generation controls, and screening controls.",
        "contract": "Task Contract",
        "task_id": "Task ID",
        "application": "Application",
        "hull_type": "Hull Type",
        "load": "Load Case",
        "boundary": "Boundary",
        "material": "Material System",
        "control": "Design Controls",
        "total_candidates": "Candidate Pool Size",
        "source_mode": "Source Allocation",
        "llm_count": "LLM Count",
        "case_count": "Case Transfer Count",
        "doe_count": "DOE Count",
        "top_k": "Screening Top-K",
        "target_pressure": "Ultimate Pressure Target",
        "objective": "Objective",
        "geometry_domain": "Geometry Domain",
        "facts": "User Facts",
        "reference_geometry": "Reference Geometry",
        "fixed_geometry": "Fixed Geometry",
        "none": "None.",
        "unspecified": "Not specified, calculated by source ratio",
        "fact_title": "Fact Boundary",
        "fact_note": (
            "<li><code>user_input_facts</code> stores only facts explicitly provided by the user.</li>"
            "<li><code>geometry_reference</code> is a design-center reference and does not force candidates to equal the value.</li>"
            "<li><code>fixed_geometry</code> stores explicit fixed/equal constraints and overrides candidate fields.</li>"
            "<li>Parameter ranges, material libraries, unit formats, and FEM interface fields are system constraints, not user facts sent to the LLM.</li>"
        ),
    },
}


class TaskConfigWidget(QTextBrowser):
    """展示结构化任务契约、用户事实和工程域参数边界。"""

    def __init__(self, language: str = DEFAULT_LANGUAGE) -> None:
        super().__init__()
        self.language = language
        self.task: dict[str, Any] | None = None
        self.setOpenExternalLinks(False)
        self.reset_view()

    def set_language(self, language: str) -> None:
        self.language = language if language in LABELS else DEFAULT_LANGUAGE
        self.update_task(self.task)

    def _label(self, key: str) -> str:
        return LABELS.get(self.language, LABELS[DEFAULT_LANGUAGE]).get(key, key)

    def reset_view(self) -> None:
        self.setHtml(
            f"<h3>{self._label('title')}</h3>"
            f"<p>{self._label('empty')}</p>"
        )

    def update_task(self, task: dict[str, Any] | None) -> None:
        self.task = task
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
            f"<h3>{self._label('title')}</h3>"
            + self._section(
                self._label("contract"),
                [
                    (self._label("task_id"), task.get("task_id") or "-"),
                    (self._label("application"), payload.get("application") or "-"),
                    (self._label("hull_type"), payload.get("hull_type") or "-"),
                    (self._label("load"), describe_load_conditions(payload.get("load_conditions") or {})),
                    (self._label("boundary"), describe_boundary_conditions(payload.get("boundary_conditions") or {})),
                    (self._label("material"), material.get("name") or "-"),
                ],
            )
            + self._section(
                self._label("control"),
                [
                    (self._label("total_candidates"), generation.get("total_candidates")),
                    (self._label("source_mode"), generation.get("source_allocation_mode") or "-"),
                    (self._label("llm_count"), self._optional_count(generation.get("llm_candidates"))),
                    (self._label("case_count"), self._optional_count(generation.get("case_transfer_candidates"))),
                    (self._label("doe_count"), self._optional_count(generation.get("doe_candidates"))),
                    (self._label("top_k"), screening.get("top_k_candidates")),
                    (self._label("target_pressure"), self._pressure_text(targets.get("ultimate_pressure_min_MPa"))),
                    (self._label("objective"), targets.get("primary_objective") or "-"),
                ],
            )
            + self._geometry_table(self._label("geometry_domain"), envelope)
            + self._dict_table(self._label("facts"), facts)
            + self._dict_table(self._label("reference_geometry"), reference_geometry)
            + self._dict_table(self._label("fixed_geometry"), fixed_geometry)
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
            return f"<h4>{escape(title)}</h4><p>{self._label('none')}</p>"
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
        return self._label("unspecified") if value is None else str(value)

    def _pressure_text(self, value: Any) -> str:
        return "-" if value is None or value == "" else f"{value} MPa"

    def _fact_boundary_note(self) -> str:
        return (
            f"<h4>{self._label('fact_title')}</h4>"
            "<ul>"
            f"{self._label('fact_note')}"
            "</ul>"
        )

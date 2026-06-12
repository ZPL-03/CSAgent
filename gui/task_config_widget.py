"""任务配置与事实边界展示组件。"""

from __future__ import annotations

import json
from typing import Any

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFrame,
    QGridLayout,
    QLabel,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

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
        "empty_fields": "等待解析字段",
        "none": "无",
        "unspecified": "未指定，按来源比例计算",
        "fact_title": "事实边界",
        "fact_short": "用户事实、几何参考和固定约束分层记录；参数域、材料库、单位格式和有限元接口属于系统工程约束。",
        "fact_user": "只保存用户自然语言明确给出的事实。",
        "fact_reference": "作为设计中心和几何包络参考，不强制候选方案等于该数值。",
        "fact_fixed": "明确固定、限定或必须保持不变的几何约束，会覆盖候选对应参数。",
        "fact_system": "参数域、材料库、单位格式和有限元接口字段不作为用户事实发送给 LLM。",
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
        "empty_fields": "Pending Parsed Fields",
        "none": "None",
        "unspecified": "Not specified, calculated by source ratio",
        "fact_title": "Fact Boundary",
        "fact_short": "User facts, geometry references, and fixed constraints are stored separately; parameter ranges, materials, units, and FEM fields are system constraints.",
        "fact_user": "Stores only facts explicitly provided by the user.",
        "fact_reference": "Defines the design-center reference and does not force candidate values.",
        "fact_fixed": "Stores explicit fixed/equal constraints and overrides candidate fields.",
        "fact_system": "System parameter ranges, materials, units, and FEM fields are not sent to the LLM as user facts.",
    },
}


class TaskConfigWidget(QWidget):
    """展示结构化任务契约、用户事实和工程域参数边界。"""

    def __init__(self, language: str = DEFAULT_LANGUAGE) -> None:
        super().__init__()
        self.language = language
        self.task: dict[str, Any] | None = None
        self._plain_text = ""

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        self.content = QWidget()
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(12, 12, 12, 12)
        self.content_layout.setSpacing(12)
        self.scroll_area.setWidget(self.content)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.scroll_area)
        self.reset_view()

    def set_language(self, language: str) -> None:
        self.language = language if language in LABELS else DEFAULT_LANGUAGE
        self.update_task(self.task)

    def toPlainText(self) -> str:
        return self._plain_text

    def _label(self, key: str) -> str:
        return LABELS.get(self.language, LABELS[DEFAULT_LANGUAGE]).get(key, key)

    def reset_view(self) -> None:
        self.task = None
        groups = [
            (self._label("facts"), [("user_input_facts", self._label("fact_user"))]),
            (self._label("reference_geometry"), [("geometry_reference", self._label("fact_reference"))]),
            (self._label("fixed_geometry"), [("fixed_geometry", self._label("fact_fixed"))]),
            (self._label("control"), [("candidate_generation / screening", self._label("unspecified"))]),
            (
                self._label("geometry_domain"),
                [("length / radius / thickness / alpha / beta / imperfection", self._label("fact_system"))],
            ),
        ]
        self._render(
            header=(self._label("title"), self._label("empty")),
            groups=groups,
            note=False,
            columns=2,
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

        groups = [
            (
                self._label("contract"),
                [
                    (self._label("task_id"), task.get("task_id") or "-"),
                    (self._label("application"), payload.get("application") or "-"),
                    (self._label("hull_type"), payload.get("hull_type") or "-"),
                    (self._label("load"), describe_load_conditions(payload.get("load_conditions") or {})),
                    (self._label("boundary"), describe_boundary_conditions(payload.get("boundary_conditions") or {})),
                    (self._label("material"), material.get("name") or "-"),
                ],
            ),
            (
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
            ),
            (self._label("geometry_domain"), self._geometry_rows(envelope)),
            (self._label("facts"), self._dict_rows(facts)),
            (self._label("reference_geometry"), self._dict_rows(reference_geometry)),
            (self._label("fixed_geometry"), self._dict_rows(fixed_geometry)),
        ]
        self._render(header=(self._label("title"), self._label("fact_short")), groups=groups, note=True)

    def _render(
        self,
        header: tuple[str, str],
        groups: list[tuple[str, list[tuple[str, Any]]]],
        note: bool,
        columns: int | None = None,
    ) -> None:
        self._clear_layout(self.content_layout)
        title, subtitle = header
        self.content_layout.addWidget(self._header_widget(title, subtitle))

        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(10)
        columns = columns or 2
        for index, (group_title, rows) in enumerate(groups):
            card = self._card_widget(group_title, rows)
            grid.addWidget(card, index // columns, index % columns)
        for column in range(columns):
            grid.setColumnStretch(column, 1)
        self.content_layout.addLayout(grid)

        if note:
            self.content_layout.addWidget(self._fact_boundary_widget())
        self._plain_text = self._compose_plain_text(title, subtitle, groups, note)

    def _header_widget(self, title: str, subtitle: str) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        title_label = QLabel(title)
        title_label.setObjectName("configTitle")
        subtitle_label = QLabel(subtitle)
        subtitle_label.setObjectName("configSubtitle")
        subtitle_label.setWordWrap(True)
        layout.addWidget(title_label)
        layout.addWidget(subtitle_label)
        return widget

    def _card_widget(self, title: str, rows: list[tuple[str, Any]]) -> QFrame:
        card = QFrame()
        card.setObjectName("configCard")
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(8)

        title_label = QLabel(title)
        title_label.setObjectName("configCardTitle")
        layout.addWidget(title_label)

        row_grid = QGridLayout()
        row_grid.setContentsMargins(0, 0, 0, 0)
        row_grid.setHorizontalSpacing(10)
        row_grid.setVerticalSpacing(6)
        for row, (label, value) in enumerate(rows):
            key_label = QLabel(str(label))
            key_label.setObjectName("configKey")
            key_label.setWordWrap(True)
            value_label = QLabel(self._safe(value))
            value_label.setObjectName("configValue")
            value_label.setWordWrap(True)
            value_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            row_grid.addWidget(key_label, row, 0, Qt.AlignmentFlag.AlignTop)
            row_grid.addWidget(value_label, row, 1, Qt.AlignmentFlag.AlignTop)
        row_grid.setColumnStretch(0, 0)
        row_grid.setColumnStretch(1, 1)
        layout.addLayout(row_grid)
        return card

    def _fact_boundary_widget(self) -> QFrame:
        rows = [
            ("user_input_facts", self._label("fact_user")),
            ("geometry_reference", self._label("fact_reference")),
            ("fixed_geometry", self._label("fact_fixed")),
            ("system_constraints", self._label("fact_system")),
        ]
        return self._card_widget(self._label("fact_title"), rows)

    def _geometry_rows(self, geometry: dict[str, Any]) -> list[tuple[str, Any]]:
        order = ["length_mm", "radius_mm", "thickness_mm", "alpha_deg", "beta_deg", "imperfection_ratio"]
        rows = []
        for key in order:
            value = geometry.get(key)
            if isinstance(value, list) and len(value) >= 2:
                text = f"{value[0]} - {value[1]}"
            else:
                text = value
            rows.append((key, text))
        return rows

    def _dict_rows(self, payload: dict[str, Any]) -> list[tuple[str, Any]]:
        if not payload:
            return [("-", self._label("none"))]
        return [(str(key), self._format_value(value)) for key, value in payload.items()]

    def _format_value(self, value: Any) -> str:
        if isinstance(value, (dict, list)):
            return json.dumps(value, ensure_ascii=False)
        return str(value)

    def _safe(self, value: Any) -> str:
        if value is None or value == "":
            return "-"
        return str(value)

    def _optional_count(self, value: Any) -> str:
        return self._label("unspecified") if value is None else str(value)

    def _pressure_text(self, value: Any) -> str:
        return "-" if value is None or value == "" else f"{value} MPa"

    def _compose_plain_text(
        self,
        title: str,
        subtitle: str,
        groups: list[tuple[str, list[tuple[str, Any]]]],
        note: bool,
    ) -> str:
        lines = [title, subtitle]
        for group_title, rows in groups:
            lines.append(group_title)
            for label, value in rows:
                lines.append(f"{label}: {self._safe(value)}")
        if note:
            lines.extend(
                [
                    self._label("fact_title"),
                    "user_input_facts: " + self._label("fact_user"),
                    "geometry_reference: " + self._label("fact_reference"),
                    "fixed_geometry: " + self._label("fact_fixed"),
                    "system_constraints: " + self._label("fact_system"),
                ]
            )
        return "\n".join(lines)

    @staticmethod
    def _clear_layout(layout: QVBoxLayout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            child_layout = item.layout()
            if widget is not None:
                widget.deleteLater()
            elif child_layout is not None:
                TaskConfigWidget._clear_nested_layout(child_layout)

    @staticmethod
    def _clear_nested_layout(layout: Any) -> None:
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            child_layout = item.layout()
            if widget is not None:
                widget.deleteLater()
            elif child_layout is not None:
                TaskConfigWidget._clear_nested_layout(child_layout)

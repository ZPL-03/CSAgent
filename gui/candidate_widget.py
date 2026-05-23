"""候选方案展示组件。"""

from __future__ import annotations

from html import escape
from typing import Iterable

from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from gui.interactive_view import InteractivePlotWidget
from core.pressure_hull_profile import GEOMETRY_LABELS, TYPE_DISPLAY_NAMES
from core.task_contract import describe_boundary_conditions, describe_load_conditions


SOURCE_LABELS = {
    "LLM": "LLM 外部知识库/知识图谱增强",
    "CASE_TRANSFER": "历史案例迁移",
    "DOE": "DOE 参数采样",
}


def _format_generation_label(source: object) -> str:
    key = str(source or "UNKNOWN")
    return SOURCE_LABELS.get(key, key)


def _format_number(value: object, digits: int = 3) -> str:
    if value is None or value == "":
        return "-"
    try:
        return f"{float(value):.{digits}f}"
    except Exception:
        return str(value)


def _layup_sequence(layup: dict) -> list[object]:
    angles = layup.get("angles_deg")
    if isinstance(angles, list) and angles:
        return angles
    return []


class CandidateWidget(QWidget):
    """展示候选方案表格、设计细节与交互式几何视图。"""

    HEADERS = ["样本", "来源", "预测极限压力", "预测面密度", "排序分数", "FEM极限压力", "状态", "结论"]

    def __init__(self) -> None:
        super().__init__()
        self.candidates: list[dict] = []
        self.results_by_session_id: dict[str, dict] = {}

        self.table = QTableWidget(0, len(self.HEADERS))
        self.table.setHorizontalHeaderLabels(self.HEADERS)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.itemSelectionChanged.connect(self._refresh_detail)

        self.summary_label = QLabel("当前还没有候选方案。")
        self.summary_label.setWordWrap(True)

        self.detail_browser = QTextBrowser()
        self.preview_widget = InteractivePlotWidget("选中候选方案后，这里会显示可旋转的三维几何视图。")

        right_layout = QVBoxLayout()
        right_layout.addWidget(self.summary_label)
        right_layout.addWidget(self.detail_browser, 2)
        right_layout.addWidget(self.preview_widget, 3)

        right_widget = QWidget()
        right_widget.setLayout(right_layout)

        splitter = QSplitter()
        splitter.addWidget(self.table)
        splitter.addWidget(right_widget)
        splitter.setSizes([720, 620])

        layout = QHBoxLayout(self)
        layout.addWidget(splitter)

    def _result_for_candidate(self, candidate: dict) -> dict | None:
        return self.results_by_session_id.get(candidate.get("candidate_id", ""))

    def update_candidates(self, candidates: Iterable[dict], results_by_session_id: dict[str, dict] | None = None) -> None:
        self.candidates = list(candidates)
        if results_by_session_id is not None:
            self.results_by_session_id = dict(results_by_session_id)

        self.table.setRowCount(len(self.candidates))
        source_counter: dict[str, int] = {}

        for row, candidate in enumerate(self.candidates):
            source = str(candidate.get("source", "UNKNOWN"))
            generation_label = _format_generation_label(source)
            source_counter[generation_label] = source_counter.get(generation_label, 0) + 1
            result = self._result_for_candidate(candidate)
            archive_id = candidate.get("persistent_candidate_id") or (result or {}).get("candidate_id", "-")
            values = [
                candidate.get("display_name", candidate.get("candidate_id", "")),
                generation_label,
                _format_number(candidate.get("surrogate_ultimate_pressure_MPa")),
                _format_number(candidate.get("surrogate_weight")),
                _format_number(candidate.get("rank_score"), 4),
                _format_number(result.get("ultimate_pressure_MPa") if result else None),
                result.get("status", "未校核") if result else "未校核",
                result.get("verdict", "-") if result else "-",
            ]
            for col, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                if col == 0:
                    item.setToolTip(f"会话编号: {candidate.get('candidate_id')} | 正式编号: {archive_id}")
                self.table.setItem(row, col, item)

        summary = " / ".join(f"{key}: {value}" for key, value in sorted(source_counter.items()))
        self.summary_label.setText(
            f"当前候选方案数：{len(self.candidates)} | 来源构成：{summary or '-'} | "
            "说明：候选阶段只使用临时编号，只有做过 ABAQUS 校核后才会分配正式 C 编号。"
        )

        if self.candidates:
            self.table.selectRow(0)
        else:
            self.detail_browser.setHtml("<p>暂无候选方案。</p>")
            self.preview_widget.clear_scene("暂无几何预览。")

    def reset_view(self) -> None:
        if hasattr(self, "detail_browser"):
            self.detail_browser.clear()
        self.preview_widget.reset_plotter()

    def selected_candidates(self) -> list[dict]:
        rows = sorted({index.row() for index in self.table.selectionModel().selectedRows()})
        return [self.candidates[row] for row in rows if 0 <= row < len(self.candidates)]

    def _refresh_detail(self) -> None:
        selected = self.selected_candidates()
        if not selected:
            self.detail_browser.setHtml("<p>请选择候选方案查看详细信息。</p>")
            self.preview_widget.clear_scene("请选择候选方案查看三维几何视图。")
            return

        candidate = selected[0]
        result = self._result_for_candidate(candidate)
        geometry = candidate.get("geometry", {})
        layup = candidate.get("layup", {})
        material = candidate.get("material_system", {})
        load_conditions = candidate.get("load_conditions", {})
        design_targets = candidate.get("design_targets", {})
        rule_check = candidate.get("rule_check", {})
        screening_summary = candidate.get("screening_summary") or "尚未完成代理模型初筛。"
        selection_reason = candidate.get("selection_reason") or "当前样本尚未进入优先校核队列。"

        ply_items = "".join(
            f"<li>第 {index + 1} 层：{angle}&deg;</li>"
            for index, angle in enumerate(_layup_sequence(layup))
        )
        geometry_items = "".join(
            f"<li>{GEOMETRY_LABELS.get(key, key)}: {_format_number(value)}</li>"
            for key, value in geometry.items()
        )
        material_items = "".join(f"<li>{key}: {value}</li>" for key, value in material.items())
        target_items = "".join(f"<li>{key}: {value}</li>" for key, value in design_targets.items())
        rule_errors = rule_check.get("errors") or ["无"]
        rule_suggestions = rule_check.get("suggestions") or ["无"]
        archive_id = candidate.get("persistent_candidate_id") or (result or {}).get("candidate_id", "-")
        llm_excerpt = str(candidate.get("llm_output_excerpt") or "").strip()
        llm_excerpt_html = ""
        if candidate.get("source") == "LLM" and llm_excerpt:
            llm_excerpt_html = (
                "<h4>LLM 回答片段</h4>"
                f"<p>{escape(llm_excerpt).replace(chr(10), '<br>')}</p>"
            )

        result_html = ""
        if result:
            result_html = (
                "<h4>真实 ABAQUS 结果</h4>"
                f"<p>正式样本编号：{archive_id}<br>"
                f"状态：{result.get('status')}<br>"
                f"极限压力：{_format_number(result.get('ultimate_pressure_MPa'))} MPa<br>"
                f"线性屈曲压力：{_format_number(result.get('linear_buckling_pressure_MPa'))} MPa<br>"
                f"极限压力依据：{result.get('ultimate_pressure_basis', '-')}<br>"
                f"面密度：{_format_number(result.get('weight_kg_per_m2'))} kg/m^2<br>"
                f"失效模式：{result.get('failure_mode', '-')}<br>"
                f"结论：{result.get('verdict', '-')}</p>"
            )

        htype = str(candidate.get("hull_type", "CYLINDRICAL"))
        stype_display = TYPE_DISPLAY_NAMES.get(htype, htype)

        html = (
            f"<h3>{candidate.get('display_name', candidate.get('candidate_id'))} | {_format_generation_label(candidate.get('source'))} | {stype_display}</h3>"
            f"<p><b>会话编号：</b>{candidate.get('candidate_id', '-')}<br>"
            f"<b>正式编号：</b>{archive_id}</p>"
            f"<p><b>生成说明：</b>{candidate.get('rationale', '-')}</p>"
            f"<p><b>来源补充：</b>{candidate.get('origin_summary') or '当前候选未附带额外来源说明。'}</p>"
            f"<p><b>代理预测：</b> 极限压力={_format_number(candidate.get('surrogate_ultimate_pressure_MPa'))} MPa，"
            f"线性屈曲Q(ASME RD-1172)={_format_number(candidate.get('asme_linear_buckling_pressure_MPa'))} MPa，"
            f"PBIPF公式={_format_number(candidate.get('surrogate_PBIPF_MPa'))} MPa，"
            f"面密度={_format_number(candidate.get('surrogate_weight'))} kg/m^2，"
            f"评分={_format_number(candidate.get('rank_score'), 4)}<br>"
            f"线性屈曲Q来源：{candidate.get('linear_buckling_source') or '-'}</p>"
            f"<p><b>代理模型初筛摘要：</b>{screening_summary}</p>"
            f"<p><b>优先校核原因：</b>{selection_reason}</p>"
            "<h4>几何设计参数</h4><ul>"
            f"{geometry_items}</ul>"
            "<h4>材料系统</h4><ul>"
            f"{material_items}</ul>"
            "<h4>载荷与边界</h4><ul>"
            f"<li>{describe_load_conditions(load_conditions)}</li>"
            f"<li>{describe_boundary_conditions(candidate.get('boundary_conditions', {}))}</li></ul>"
            "<h4>设计目标</h4><ul>"
            f"{target_items}</ul>"
            f"<h4>铺层定义</h4><p>铺层字符串：{layup.get('skin_layup', '-')}</p>"
            f"<p>比例：0°={_format_number(layup.get('skin_f0'))}，±45°={_format_number(layup.get('skin_f45'))}，90°={_format_number(layup.get('skin_f90'))}</p>"
            f"<ul>{ply_items or '<li>暂无铺层明细</li>'}</ul>"
            "<h4>规则检查</h4>"
            f"<p>是否通过校验：{rule_check.get('is_valid', False)}</p>"
            f"<p>问题：{'；'.join(rule_errors)}</p>"
            f"<p>建议：{'；'.join(rule_suggestions)}</p>"
            f"{llm_excerpt_html}"
            f"{result_html}"
        )
        self.detail_browser.setHtml(html)
        self.preview_widget.show_candidate(candidate)

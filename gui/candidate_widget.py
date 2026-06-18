"""候选方案展示组件。"""

from __future__ import annotations

from html import escape
from typing import Iterable

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QGridLayout,
    QHeaderView,
    QLabel,
    QSizePolicy,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from gui.i18n import DEFAULT_LANGUAGE, text as tr
from core.pressure_hull_profile import GEOMETRY_LABELS, TYPE_DISPLAY_NAMES
from core.task_contract import describe_boundary_conditions, describe_load_conditions


def _format_generation_label(source: object, language: str = DEFAULT_LANGUAGE) -> str:
    key = str(source or "UNKNOWN")
    source_keys = {
        "LLM": "candidate.source.llm",
        "CASE_TRANSFER": "candidate.source.case",
        "DOE": "candidate.source.doe",
        "UNKNOWN": "candidate.source.unknown",
    }
    return tr(source_keys.get(key, "candidate.source.unknown"), language=language) if key in source_keys else key


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


def _count_map_text(payload: dict | None) -> str:
    if not isinstance(payload, dict) or not payload:
        return "-"
    return " / ".join(f"{escape(str(key))}={escape(str(value))}" for key, value in payload.items())


class CandidateWidget(QWidget):
    """展示候选方案表格、设计细节与来源审计。"""

    COLUMN_COUNT = 8
    candidateSelected = pyqtSignal(dict)

    def __init__(self, language: str = DEFAULT_LANGUAGE) -> None:
        super().__init__()
        self.language = language
        self.candidates: list[dict] = []
        self.results_by_session_id: dict[str, dict] = {}

        self.table = QTableWidget(0, self.COLUMN_COUNT)
        self.table.setHorizontalHeaderLabels(self._headers())
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setCornerButtonEnabled(False)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.table.horizontalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        for column, width in enumerate([92, 104, 118, 100, 112, 118, 116, 98]):
            self.table.setColumnWidth(column, width)
        self.table.itemSelectionChanged.connect(self._refresh_detail)
        self.table.setMinimumWidth(280)
        self.table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self.summary_label = QLabel(tr("candidate.empty", language=self.language))
        self.summary_label.setWordWrap(True)

        self.total_metric = self._metric_label()
        self.llm_metric = self._metric_label()
        self.case_metric = self._metric_label()
        self.doe_metric = self._metric_label()
        self.evaluated_metric = self._metric_label()
        metric_layout = QGridLayout()
        metric_layout.setContentsMargins(0, 0, 0, 0)
        metric_layout.setHorizontalSpacing(8)
        metric_layout.setVerticalSpacing(8)
        metric_cards = [self.total_metric, self.llm_metric, self.case_metric, self.doe_metric, self.evaluated_metric]
        for index, card in enumerate(metric_cards):
            metric_layout.addWidget(card, 0, index)
            metric_layout.setColumnStretch(index, 1)
        self.metric_widget = QWidget()
        self.metric_widget.setLayout(metric_layout)
        self.metric_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.metric_widget.setMaximumHeight(64)

        self.detail_browser = QTextBrowser()
        self.audit_browser = QTextBrowser()
        self.detail_tabs = QTabWidget()
        self.detail_tabs.setObjectName("candidateDetailTabs")
        self.detail_tabs.setDocumentMode(True)
        self.detail_tabs.addTab(self.detail_browser, tr("candidate.tab.detail", language=self.language))
        self.detail_tabs.addTab(self.audit_browser, tr("candidate.tab.audit", language=self.language))
        self.detail_tabs.tabBar().setExpanding(True)
        self.detail_tabs.tabBar().setUsesScrollButtons(False)
        self.detail_tabs.setMinimumWidth(300)
        self.detail_tabs.setMaximumHeight(300)

        splitter = QSplitter()
        splitter.addWidget(self.table)
        splitter.addWidget(self.detail_tabs)
        splitter.setChildrenCollapsible(False)
        splitter.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([640, 640])
        self.splitter = splitter

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        layout.addWidget(self.metric_widget, 0)
        layout.addWidget(splitter, 1)
        self.update_candidates([])

    def _metric_label(self) -> QLabel:
        label = QLabel()
        label.setWordWrap(False)
        label.setMinimumWidth(92)
        label.setMinimumHeight(52)
        label.setMaximumHeight(52)
        label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        label.setProperty("role", "metricCard")
        return label

    def _headers(self) -> list[str]:
        return tr("candidate.headers", language=self.language).split("|")

    def set_language(self, language: str) -> None:
        self.language = language
        self.table.setHorizontalHeaderLabels(self._headers())
        self.detail_tabs.setTabText(0, tr("candidate.tab.detail", language=self.language))
        self.detail_tabs.setTabText(1, tr("candidate.tab.audit", language=self.language))
        self._update_metric_cards()
        if not self.candidates:
            self.summary_label.setText(tr("candidate.empty", language=self.language))
            self.detail_browser.setHtml(self._empty_detail_html())
            self.audit_browser.setHtml(self._generation_audit_html({}))

    def _source_counter(self) -> dict[str, int]:
        counter = {"LLM": 0, "CASE_TRANSFER": 0, "DOE": 0}
        for candidate in self.candidates:
            source = str(candidate.get("source", "UNKNOWN"))
            if source in counter:
                counter[source] += 1
        return counter

    def _update_metric_cards(self) -> None:
        counter = self._source_counter()
        evaluated_count = sum(1 for candidate in self.candidates if self._result_for_candidate(candidate))
        self.total_metric.setText(tr("candidate.metric.total", language=self.language, count=len(self.candidates)))
        self.llm_metric.setText(tr("candidate.metric.llm", language=self.language, count=counter.get("LLM", 0)))
        self.case_metric.setText(
            tr("candidate.metric.case", language=self.language, count=counter.get("CASE_TRANSFER", 0))
        )
        self.doe_metric.setText(tr("candidate.metric.doe", language=self.language, count=counter.get("DOE", 0)))
        self.evaluated_metric.setText(tr("candidate.metric.evaluated", language=self.language, count=evaluated_count))

    def _result_for_candidate(self, candidate: dict) -> dict | None:
        return self.results_by_session_id.get(candidate.get("candidate_id", ""))

    def _generation_audit_for_pool(self) -> dict:
        for candidate in self.candidates:
            audit = candidate.get("generation_audit")
            if isinstance(audit, dict) and audit:
                return audit
        return {}

    def _generation_audit_summary(self, audit: dict) -> str:
        if not audit:
            return "-"
        summary = str(audit.get("summary") or "").strip()
        if summary:
            return summary
        added = audit.get("added_counts") if isinstance(audit.get("added_counts"), dict) else {}
        duplicates = audit.get("duplicate_counts") if isinstance(audit.get("duplicate_counts"), dict) else {}
        return f"有效进入候选池：{_count_map_text(added)}；结构去重：{duplicates.get('total', 0) if isinstance(duplicates, dict) else 0}"

    def _generation_audit_html(self, audit: dict) -> str:
        if not audit:
            return "<h4>候选来源与去重审计</h4><p>当前候选未附带结构化生成审计。</p>"
        filter_reasons = audit.get("filter_reasons") if isinstance(audit.get("filter_reasons"), dict) else {}
        reason_items = []
        for source, reasons in filter_reasons.items():
            if not reasons:
                continue
            reason_items.append(f"<li>{escape(str(source))}: {escape('；'.join(str(item) for item in reasons))}</li>")
        reasons_html = "<ul>" + "".join(reason_items) + "</ul>" if reason_items else "<p>未记录规则过滤原因。</p>"
        return (
            "<h4>候选来源与去重审计</h4>"
            f"<p><b>摘要：</b>{escape(str(audit.get('summary') or '-'))}</p>"
            "<table border='1' cellspacing='0' cellpadding='5'>"
            "<tr><th>项目</th><th>LLM</th><th>案例迁移</th><th>DOE</th><th>合计</th></tr>"
            f"<tr><td>初始配额</td><td>{escape(str((audit.get('source_targets') or {}).get('LLM', '-')))}</td>"
            f"<td>{escape(str((audit.get('source_targets') or {}).get('CASE_TRANSFER', '-')))}</td>"
            f"<td>{escape(str((audit.get('source_targets') or {}).get('DOE', '-')))}</td>"
            f"<td>{escape(str((audit.get('source_targets') or {}).get('total', '-')))}</td></tr>"
            f"<tr><td>原始输出</td><td>{escape(str((audit.get('raw_counts') or {}).get('LLM', '-')))}</td>"
            f"<td>{escape(str((audit.get('raw_counts') or {}).get('CASE_TRANSFER', '-')))}</td>"
            f"<td>{escape(str((audit.get('raw_counts') or {}).get('DOE', '-')))}</td><td>-</td></tr>"
            f"<tr><td>规则有效</td><td>{escape(str((audit.get('valid_counts') or {}).get('LLM', '-')))}</td>"
            f"<td>{escape(str((audit.get('valid_counts') or {}).get('CASE_TRANSFER', '-')))}</td>"
            f"<td>{escape(str((audit.get('valid_counts') or {}).get('DOE', '-')))}</td><td>-</td></tr>"
            f"<tr><td>进入候选池</td><td>{escape(str((audit.get('added_counts') or {}).get('LLM', '-')))}</td>"
            f"<td>{escape(str((audit.get('added_counts') or {}).get('CASE_TRANSFER', '-')))}</td>"
            f"<td>{escape(str((audit.get('added_counts') or {}).get('DOE', '-')))}</td><td>-</td></tr>"
            f"<tr><td>结构去重</td><td>{escape(str((audit.get('duplicate_counts') or {}).get('LLM', '-')))}</td>"
            f"<td>{escape(str((audit.get('duplicate_counts') or {}).get('CASE_TRANSFER', '-')))}</td>"
            f"<td>{escape(str((audit.get('duplicate_counts') or {}).get('DOE', '-')))}</td>"
            f"<td>{escape(str((audit.get('duplicate_counts') or {}).get('total', '-')))}</td></tr>"
            "</table>"
            f"<p><b>DOE 补足：</b>{escape(str(audit.get('doe_fill_count', '-')))} 个，采样轮次 {escape(str(audit.get('doe_rounds', '-')))}。</p>"
            "<h4>规则过滤原因</h4>"
            f"{reasons_html}"
        )

    def _empty_detail_html(self) -> str:
        title = escape(tr("candidate.empty", language=self.language))
        body = escape(tr("candidate.empty_body", language=self.language))
        return f"<h4>{title}</h4><p>{body}</p>"

    def update_candidates(self, candidates: Iterable[dict], results_by_session_id: dict[str, dict] | None = None) -> None:
        self.candidates = list(candidates)
        if results_by_session_id is not None:
            self.results_by_session_id = dict(results_by_session_id)

        self.table.setRowCount(len(self.candidates))
        self.setMinimumHeight(260)
        self.setMaximumHeight(16777215)
        self.metric_widget.setVisible(True)
        self.table.setVisible(True)
        self.detail_tabs.setMaximumHeight(16777215)
        self.detail_tabs.setVisible(True)
        self.splitter.setSizes([640, 640])
        source_counter: dict[str, int] = {}

        for row, candidate in enumerate(self.candidates):
            source = str(candidate.get("source", "UNKNOWN"))
            generation_label = _format_generation_label(source, self.language)
            source_counter[generation_label] = source_counter.get(generation_label, 0) + 1
            result = self._result_for_candidate(candidate)
            archive_id = candidate.get("persistent_candidate_id") or (result or {}).get("candidate_id", "-")
            screening_selected = candidate.get("screening_selected")
            status_value = result.get("status", "未校核") if result else "未校核"
            if screening_selected is False and not result:
                status_value = "未入选Top-K"
            values = [
                candidate.get("display_name", candidate.get("candidate_id", "")),
                generation_label,
                _format_number(candidate.get("surrogate_ultimate_pressure_MPa")),
                _format_number(candidate.get("surrogate_weight")),
                _format_number(candidate.get("rank_score"), 4),
                _format_number(result.get("ultimate_pressure_MPa") if result else None),
                status_value,
                result.get("verdict", "-") if result else "-",
            ]
            for col, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if screening_selected is False and not result:
                    item.setForeground(QColor("#8796aa"))
                    item.setToolTip("未进入默认 Top-K 校核队列；仍可人工选择进入 FEM 校核。")
                if col == 0:
                    item.setToolTip(f"会话编号: {candidate.get('candidate_id')} | 正式编号: {archive_id}")
                self.table.setItem(row, col, item)

        self._update_metric_cards()
        summary = " / ".join(f"{key}: {value}" for key, value in sorted(source_counter.items()))
        pool_audit = self._generation_audit_for_pool()
        audit_summary = self._generation_audit_summary(pool_audit)
        self.audit_browser.setHtml(self._generation_audit_html(pool_audit))
        self.summary_label.setText(
            f"当前候选方案数：{len(self.candidates)} | 来源构成：{summary or '-'} | "
            f"来源审计：{audit_summary} | "
            "说明：候选阶段只使用临时编号，只有做过 ABAQUS 校核后才会分配正式 C 编号。"
        )

        if self.candidates:
            self.table.selectRow(0)
        else:
            self.detail_browser.setHtml(self._empty_detail_html())
            self.audit_browser.setHtml(self._generation_audit_html({}))
        self._sync_detail_tab_widths()

    def reset_view(self) -> None:
        if hasattr(self, "detail_browser"):
            self.detail_browser.setHtml(self._empty_detail_html())
        if hasattr(self, "audit_browser"):
            self.audit_browser.setHtml(self._generation_audit_html({}))

    def selected_candidates(self) -> list[dict]:
        rows = sorted({index.row() for index in self.table.selectionModel().selectedRows()})
        return [self.candidates[row] for row in rows if 0 <= row < len(self.candidates)]

    def _refresh_detail(self) -> None:
        selected = self.selected_candidates()
        if not selected:
            self.detail_browser.setHtml(f"<p>{tr('candidate.no_detail', language=self.language)}</p>")
            return

        candidate = selected[0]
        self.candidateSelected.emit(candidate)
        result = self._result_for_candidate(candidate)
        geometry = candidate.get("geometry", {})
        layup = candidate.get("layup", {})
        material = candidate.get("material_system", {})
        load_conditions = candidate.get("load_conditions", {})
        design_targets = candidate.get("design_targets", {})
        rule_check = candidate.get("rule_check", {})
        screening_summary = candidate.get("screening_summary") or "尚未完成代理模型初筛。"
        selection_reason = candidate.get("selection_reason") or "当前样本尚未进入优先校核队列。"
        generation_audit_html = self._generation_audit_html(candidate.get("generation_audit") or {})

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
                "<h4>LLM 回答原文</h4>"
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
            f"<h3>{candidate.get('display_name', candidate.get('candidate_id'))} | {_format_generation_label(candidate.get('source'), self.language)} | {stype_display}</h3>"
            f"<p><b>会话编号：</b>{candidate.get('candidate_id', '-')}<br>"
            f"<b>正式编号：</b>{archive_id}</p>"
            f"<p><b>生成说明：</b>{candidate.get('rationale', '-')}</p>"
            f"<p><b>来源补充：</b>{candidate.get('origin_summary') or '当前候选未附带额外来源说明。'}</p>"
            f"{generation_audit_html}"
            f"<p><b>代理预测：</b> 极限压力={_format_number(candidate.get('surrogate_ultimate_pressure_MPa'))} MPa，"
            f"ASME RD-1172线性屈曲压力={_format_number(candidate.get('asme_linear_buckling_pressure_MPa'))} MPa，"
            f"PBIPF 预测极限压力为 {_format_number(candidate.get('surrogate_PBIPF_MPa'))} MPa，"
            f"面密度={_format_number(candidate.get('surrogate_weight'))} kg/m^2，"
            f"评分={_format_number(candidate.get('rank_score'), 4)}<br>"
            f"线性屈曲压力来源：{candidate.get('linear_buckling_source') or '-'}</p>"
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

    def _sync_detail_tab_widths(self) -> None:
        if not hasattr(self, "detail_tabs"):
            return
        width = max(104, (max(220, self.detail_tabs.width()) - 8) // 2)
        self.detail_tabs.setStyleSheet(
            "QTabWidget#candidateDetailTabs QTabBar::tab {"
            f"min-width: {width}px; max-width: {width}px;"
            "}"
        )

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._sync_detail_tab_widths()

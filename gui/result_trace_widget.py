"""结果追踪与案例回流展示组件。"""

from __future__ import annotations

from html import escape
from typing import Iterable

from PyQt6.QtWidgets import QHBoxLayout, QLabel, QSplitter, QTableWidget, QTableWidgetItem, QTextBrowser, QVBoxLayout, QWidget


def _fmt(value: object, digits: int = 3) -> str:
    if value is None or value == "":
        return "-"
    try:
        return f"{float(value):.{digits}f}"
    except Exception:
        return str(value)


def _error_pct(predicted: object, actual: object) -> float | None:
    if predicted in (None, "") or actual in (None, ""):
        return None
    try:
        predicted_value = float(predicted)
        actual_value = float(actual)
    except Exception:
        return None
    if abs(actual_value) < 1e-9:
        return None
    return abs(predicted_value - actual_value) / abs(actual_value) * 100.0


class ResultTraceWidget(QWidget):
    """展示 TMP 候选、正式 C 编号、有限元、案例回流和报告之间的追踪关系。"""

    HEADERS = [
        "会话候选",
        "来源",
        "正式编号",
        "代理极限压力",
        "FEM极限压力",
        "代理误差%",
        "FEM结论",
        "案例编号",
        "回流状态",
        "报告状态",
    ]

    def __init__(self) -> None:
        super().__init__()
        self.rows: list[dict] = []

        self.table = QTableWidget(0, len(self.HEADERS))
        self.table.setHorizontalHeaderLabels(self.HEADERS)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.itemSelectionChanged.connect(self._refresh_detail)

        self.summary_label = QLabel("当前还没有可追踪的设计数据。")
        self.summary_label.setWordWrap(True)
        self.detail_browser = QTextBrowser()
        self.detail_browser.setHtml("<p>完成候选生成后，这里会显示端到端结果追踪。</p>")

        right_layout = QVBoxLayout()
        right_layout.addWidget(self.summary_label)
        right_layout.addWidget(self.detail_browser)
        right_widget = QWidget()
        right_widget.setLayout(right_layout)

        splitter = QSplitter()
        splitter.addWidget(self.table)
        splitter.addWidget(right_widget)
        splitter.setSizes([780, 560])

        layout = QHBoxLayout(self)
        layout.addWidget(splitter)

    def reset_view(self) -> None:
        self.update_trace([], {}, [], None)
        self.detail_browser.setHtml("<p>完成候选生成后，这里会显示端到端结果追踪。</p>")

    def update_trace(
        self,
        candidates: Iterable[dict],
        results_by_session_id: dict[str, dict] | None = None,
        knowledge_updates: Iterable[dict] | None = None,
        report: dict | None = None,
    ) -> None:
        candidates_list = list(candidates)
        result_map = dict(results_by_session_id or {})
        update_map = self._knowledge_update_map(list(knowledge_updates or []))
        self.rows = [
            self._build_trace_row(candidate, result_map, update_map, report)
            for candidate in candidates_list
        ]
        self._render_table()
        self._render_summary(report)
        if self.rows:
            self.table.selectRow(0)
        else:
            self.detail_browser.setHtml("<p>暂无候选、有限元或案例回流追踪数据。</p>")

    def _knowledge_update_map(self, updates: list[dict]) -> dict[str, dict]:
        mapping: dict[str, dict] = {}
        for update in updates:
            if not isinstance(update, dict):
                continue
            for key in [update.get("session_candidate_id"), update.get("candidate_id")]:
                if key:
                    mapping[str(key)] = update
        return mapping

    def _build_trace_row(
        self,
        candidate: dict,
        result_map: dict[str, dict],
        update_map: dict[str, dict],
        report: dict | None,
    ) -> dict:
        session_id = str(candidate.get("candidate_id") or "")
        result = result_map.get(session_id) or result_map.get(str(candidate.get("session_candidate_id") or ""))
        formal_id = str((result or {}).get("candidate_id") or candidate.get("persistent_candidate_id") or "-")
        update = update_map.get(session_id) or update_map.get(formal_id) or {}
        predicted = candidate.get("surrogate_ultimate_pressure_MPa")
        actual = (result or {}).get("ultimate_pressure_MPa")
        report_status = "未导出"
        if report:
            report_status = "已纳入报告" if result else "未纳入报告"
        return {
            "candidate": candidate,
            "result": result or {},
            "knowledge_update": update,
            "session_id": session_id or "-",
            "source": str(candidate.get("source") or "-"),
            "formal_id": formal_id,
            "predicted_pressure": predicted,
            "actual_pressure": actual,
            "error_pct": _error_pct(predicted, actual),
            "verdict": str((result or {}).get("verdict") or "-"),
            "case_id": str(update.get("case_id") or "-"),
            "knowledge_status": str(update.get("status") or ("未回流" if result else "-")),
            "report_status": report_status,
            "report": report or {},
        }

    def _render_table(self) -> None:
        self.table.setRowCount(len(self.rows))
        for row_index, row in enumerate(self.rows):
            values = [
                row["session_id"],
                row["source"],
                row["formal_id"],
                _fmt(row["predicted_pressure"]),
                _fmt(row["actual_pressure"]),
                _fmt(row["error_pct"], 2),
                row["verdict"],
                row["case_id"],
                row["knowledge_status"],
                row["report_status"],
            ]
            for col_index, value in enumerate(values):
                self.table.setItem(row_index, col_index, QTableWidgetItem(str(value)))

    def _render_summary(self, report: dict | None) -> None:
        total = len(self.rows)
        if total == 0:
            self.summary_label.setText("当前还没有可追踪的设计数据。")
            return
        evaluated = sum(1 for row in self.rows if row["result"])
        stored = sum(1 for row in self.rows if row["knowledge_status"] == "stored")
        failed_updates = sum(1 for row in self.rows if row["knowledge_status"] in {"failed", "missing_result"})
        report_status = "已导出" if report else "未导出"
        self.summary_label.setText(
            f"追踪样本 {total} 个 | 已完成 FEM {evaluated} 个 | "
            f"正式案例回流 {stored} 个 | 回流异常 {failed_updates} 个 | 报告 {report_status}"
        )

    def _refresh_detail(self) -> None:
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            self.detail_browser.setHtml("<p>请选择追踪记录查看详情。</p>")
            return
        row = self.rows[selected_rows[0].row()]
        candidate = row["candidate"]
        result = row["result"]
        update = row["knowledge_update"]
        report = row["report"]
        html = (
            f"<h3>{escape(row['session_id'])} -> {escape(row['formal_id'])}</h3>"
            "<h4>候选与代理预测</h4>"
            f"<p>来源：{escape(row['source'])}<br>"
            f"代理极限压力：{escape(_fmt(row['predicted_pressure']))} MPa<br>"
            f"ASME RD-1172 线性屈曲压力：{escape(_fmt(candidate.get('asme_linear_buckling_pressure_MPa')))} MPa<br>"
            f"PBIPF 公式：{escape(_fmt(candidate.get('surrogate_PBIPF_MPa')))} MPa<br>"
            f"排序分数：{escape(_fmt(candidate.get('rank_score'), 4))}</p>"
            "<h4>有限元结果</h4>"
            f"<p>状态：{escape(str(result.get('status') or '-'))}<br>"
            f"极限压力：{escape(_fmt(row['actual_pressure']))} MPa<br>"
            f"线性屈曲压力：{escape(_fmt(result.get('linear_buckling_pressure_MPa')))} MPa<br>"
            f"代理误差：{escape(_fmt(row['error_pct'], 2))} %<br>"
            f"结论：{escape(row['verdict'])}<br>"
            f"失效模式：{escape(str(result.get('failure_mode') or '-'))}</p>"
            "<h4>案例回流</h4>"
            f"<p>案例编号：{escape(row['case_id'])}<br>"
            f"回流状态：{escape(row['knowledge_status'])}<br>"
            f"校准触发：{escape(str(update.get('retrained') if update else '-'))}<br>"
            f"错误摘要：{escape(str(update.get('error') or '-'))}</p>"
            "<h4>报告范围</h4>"
            f"<p>报告状态：{escape(row['report_status'])}<br>"
            f"Markdown：{escape(str(report.get('markdown_path') or '-'))}<br>"
            f"PDF：{escape(str(report.get('pdf_path') or '-'))}</p>"
            "<h4>工件路径</h4>"
            f"<p>模态数据：{escape(str(result.get('visualization_json') or '-'))}<br>"
            f"工件目录：{escape(str(result.get('artifact_dir') or '-'))}</p>"
        )
        self.detail_browser.setHtml(html)

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication

from gui.result_trace_widget import ResultTraceWidget


def _app() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_result_trace_widget_renders_end_to_end_mapping() -> None:
    app = _app()
    widget = ResultTraceWidget()
    candidates = [
        {
            "candidate_id": "TMP_1",
            "display_name": "TMP_1",
            "source": "DOE",
            "surrogate_ultimate_pressure_MPa": 50.0,
            "asme_linear_buckling_pressure_MPa": 42.0,
            "surrogate_PBIPF_MPa": 50.0,
            "rank_score": 45.0,
        },
        {
            "candidate_id": "TMP_2",
            "display_name": "TMP_2",
            "source": "LLM",
            "surrogate_ultimate_pressure_MPa": 35.0,
        },
    ]
    results = {
        "TMP_1": {
            "candidate_id": "C1",
            "session_candidate_id": "TMP_1",
            "status": "success",
            "ultimate_pressure_MPa": 40.0,
            "linear_buckling_pressure_MPa": 38.0,
            "verdict": "通过",
            "failure_mode": "非线性后屈曲极限点",
            "visualization_json": "data/abaqus_runs/C1/C1_mode.json",
            "artifact_dir": "data/abaqus_runs/C1",
        }
    }
    updates = [
        {
            "status": "stored",
            "case_id": "CASE_1",
            "candidate_id": "C1",
            "session_candidate_id": "TMP_1",
            "retrained": False,
        }
    ]
    report = {"markdown_path": "data/results/latest_report.md", "pdf_path": "data/results/latest_report.pdf"}
    try:
        widget.update_trace(candidates, results, updates, report)

        assert widget.table.rowCount() == 2
        assert widget.table.item(0, 0).text() == "TMP_1"
        assert widget.table.item(0, 2).text() == "C1"
        assert widget.table.item(0, 5).text() == "25.00"
        assert widget.table.item(0, 7).text() == "CASE_1"
        assert widget.table.item(0, 8).text() == "stored"
        assert widget.table.item(0, 9).text() == "已纳入报告"
        assert widget.table.item(1, 2).text() == "-"
        assert widget.table.item(1, 8).text() == "-"
        assert "追踪样本 2 个" in widget.summary_label.text()
        assert "已完成 FEM 1 个" in widget.summary_label.text()

        widget.table.selectRow(0)
        detail = widget.detail_browser.toPlainText()
        assert "TMP_1 -> C1" in detail
        assert "CASE_1" in detail
        assert "latest_report.md" in detail
        assert "代理误差：25.00 %" in detail
    finally:
        widget.close()
        app.processEvents()


def test_result_trace_widget_resets_to_empty_state() -> None:
    app = _app()
    widget = ResultTraceWidget()
    try:
        widget.update_trace([{"candidate_id": "TMP_1"}], {}, [], None)
        widget.reset_view()

        assert widget.table.rowCount() == 0
        assert "当前还没有可追踪的设计数据" in widget.summary_label.text()
        assert "完成候选生成后" in widget.detail_browser.toPlainText()
    finally:
        widget.close()
        app.processEvents()

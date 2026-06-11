import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication

from core.task_parser import TaskParser
from gui.main_window import MainWindow


def _app() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def _candidate(candidate_id: str) -> dict:
    return {
        "candidate_id": candidate_id,
        "display_name": candidate_id,
        "source": "DOE",
        "geometry": {},
        "layup": {},
        "material_system": {},
    }


def test_report_button_allows_partial_evaluated_results(monkeypatch) -> None:
    monkeypatch.setenv("CSDM_cph_DISABLE_LLM_AUTO", "1")
    app = _app()
    window = MainWindow()
    try:
        window.session.task = TaskParser().parse_instruction("生成 6 个候选，初筛保留 3 个候选")
        window.session.evaluated_candidates = [_candidate("TMP_1"), _candidate("TMP_2")]
        window.session.results_by_session_id = {"TMP_1": {"candidate_id": "C1", "session_candidate_id": "TMP_1"}}

        window._update_button_states()

        assert window.report_button.isEnabled() is True
        assert [item["candidate_id"] for item in window._report_candidate_set()] == ["TMP_1"]

        captured = {}
        window._run_action = lambda action, payload, status_text: captured.update(
            {"action": action, "payload": payload, "status_text": status_text}
        )
        window._start_report()

        assert captured["action"] == "report"
        assert [item["candidate_id"] for item in captured["payload"]["candidates"]] == ["TMP_1"]
        assert [item["candidate_id"] for item in captured["payload"]["results"]] == ["C1"]
        assert window.tabs.currentWidget() is window.report_widget
    finally:
        window.close()
        app.processEvents()


def test_report_completion_updates_preview_tab(monkeypatch) -> None:
    monkeypatch.setenv("CSDM_cph_DISABLE_LLM_AUTO", "1")
    app = _app()
    window = MainWindow()
    try:
        report = {
            "markdown_path": "data/results/latest_report.md",
            "pdf_path": None,
            "content": "# 报告\n\n预览内容。",
            "llm_explanation_used": False,
        }

        window._handle_finished("report", {"report": report})

        assert window.session.report == report
        assert window.tabs.currentWidget() is window.report_widget
        assert "预览内容" in window.report_widget.preview_browser.toPlainText()
        assert "LLM 工程解释：否" in window.report_widget.summary_label.text()
    finally:
        window.close()
        app.processEvents()


def test_loaded_example_keeps_geometry_as_candidate_variables(monkeypatch) -> None:
    monkeypatch.setenv("CSDM_cph_DISABLE_LLM_AUTO", "1")
    app = _app()
    window = MainWindow()
    try:
        window._load_example_prompt()
        text = window.input_line.text()

        assert "外压 30 MPa" in text
        assert "生成 12 个候选" in text
        assert "初筛保留 5 个候选" in text
        assert "长度" not in text
        assert "半径" not in text
        assert "厚度" not in text
        assert "初始缺陷" not in text
    finally:
        window.close()
        app.processEvents()

from __future__ import annotations

import csv
import json
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication

from core.task_parser import TaskParser
from gui.main_window import MainWindow
from workflow.event_store import WorkflowEventStore
from workflow.simulation_queue import SimulationJobQueue


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


class FakeKnowledge:
    def status(self) -> dict:
        return {"ready": True}

    def retrieve(self, task: dict, top_k: int | None = None, kg_top_k: int | None = None) -> dict:
        return {"query": "restore", "chunks": [], "relations": []}

    def retrieve_by_query(self, query: str, top_k: int | None = None, kg_top_k: int | None = None) -> dict:
        return {"query": query, "chunks": [], "relations": []}


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


def test_session_data_export_writes_json_and_trace_csv(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("CSDM_cph_DISABLE_LLM_AUTO", "1")
    monkeypatch.setattr("gui.main_window.RESULTS_DIR", tmp_path)
    app = _app()
    window = MainWindow()
    try:
        window.session.workflow_run_id = "RUN_EXPORT"
        window.session.instruction = "导出测试需求"
        window.session.task = TaskParser().parse_instruction("外压 30 MPa，生成 2 个候选，初筛保留 1 个候选")
        candidate = {
            **_candidate("TMP_1"),
            "source": "LLM",
            "surrogate_ultimate_pressure_MPa": 45.5,
            "asme_linear_buckling_pressure_MPa": 30.1,
            "surrogate_PBIPF_MPa": 45.5,
            "rank_score": 41.2,
        }
        window.session.candidates = [candidate]
        window.session.evaluated_candidates = [candidate]
        window.session.results_by_session_id = {
            "TMP_1": {
                "candidate_id": "C1",
                "session_candidate_id": "TMP_1",
                "ultimate_pressure_MPa": 43.2,
                "linear_buckling_pressure_MPa": 32.0,
                "status": "success",
                "verdict": "通过",
            }
        }
        window.session.knowledge_updates = [
            {"candidate_id": "C1", "session_candidate_id": "TMP_1", "case_id": "CASE_1", "status": "stored"}
        ]
        window.session.report = {"markdown_path": "data/results/latest_report.md"}

        window._update_button_states()
        assert window.export_data_button.isEnabled() is True

        json_path, csv_path = window._write_session_export()

        payload = json.loads(json_path.read_text(encoding="utf-8"))
        assert payload["workflow_run_id"] == "RUN_EXPORT"
        assert payload["instruction"] == "导出测试需求"
        assert payload["results"][0]["candidate_id"] == "C1"

        with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
            rows = list(csv.DictReader(handle))
        assert rows[0]["session_candidate_id"] == "TMP_1"
        assert rows[0]["formal_candidate_id"] == "C1"
        assert rows[0]["case_id"] == "CASE_1"
        assert rows[0]["fem_ultimate_pressure_MPa"] == "43.2"
    finally:
        window.close()
        app.processEvents()


def test_session_data_export_button_disabled_for_empty_session(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("CSDM_cph_DISABLE_LLM_AUTO", "1")
    monkeypatch.setattr("gui.main_window.RESULTS_DIR", tmp_path)
    app = _app()
    window = MainWindow()
    try:
        window._update_button_states()
        assert window.export_data_button.isEnabled() is False
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


def test_monitor_page_contains_workflow_audit_widget(monkeypatch) -> None:
    monkeypatch.setenv("CSDM_cph_DISABLE_LLM_AUTO", "1")
    app = _app()
    window = MainWindow()
    try:
        window._switch_workspace_page(3)
        assert window.stack.currentWidget() is window.monitor_page
        assert window.workflow_widget.parent() is not None
        assert window.workflow_widget.isHidden() is False
        assert window.workflow_widget.health_button.isHidden() is False
        assert window.workflow_widget.audit_button.isHidden() is False
    finally:
        window.close()
        app.processEvents()


def test_main_window_restores_workflow_snapshot(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("CSDM_cph_DISABLE_LLM_AUTO", "1")
    monkeypatch.setattr("gui.knowledge_widget.DomainKnowledgeBase", FakeKnowledge)
    app = _app()
    store = WorkflowEventStore(tmp_path / "workflow.sqlite3")
    task = TaskParser().parse_instruction(
        "请为复合材料外压圆柱耐压壳设计方案，外压 30 MPa，极限压力不低于 35 MPa，生成 6 个候选，初筛保留 3 个候选"
    )
    candidate = _candidate("TMP_1")
    snapshot = {
        "run_id": "RUN_RESTORE",
        "instruction": "恢复测试需求",
        "task": task,
        "candidates": [candidate],
        "screened_candidates": [candidate],
        "evaluated_candidates": [candidate],
        "results": [{"candidate_id": "C1", "session_candidate_id": "TMP_1", "verdict": "通过"}],
        "knowledge_updates": [{"status": "stored", "case_id": "CASE_1", "candidate_id": "C1", "session_candidate_id": "TMP_1"}],
        "report": {"markdown_path": "data/results/latest_report.md", "content": "# 报告"},
        "stage": "awaiting_report_confirmation",
        "pending_confirmation": "export_report",
        "screen_skipped": False,
    }
    store.create_run("RUN_RESTORE", snapshot["instruction"])
    store.save_snapshot("RUN_RESTORE", snapshot)

    window = MainWindow()
    try:
        window.workflow_event_store = store
        window.workflow_widget.event_store = store
        window.workflow_widget.simulation_queue = SimulationJobQueue(store.db_path)
        window._refresh_run_selector()

        assert window.run_selector.currentData() == "RUN_RESTORE"

        window._restore_selected_run()

        assert window.session.workflow_run_id == "RUN_RESTORE"
        assert window.session.instruction == "恢复测试需求"
        assert window.session.pending_confirmation == "export_report"
        assert window.session.results_by_session_id["TMP_1"]["candidate_id"] == "C1"
        assert window.session.knowledge_updates[0]["case_id"] == "CASE_1"
        assert window.tabs.indexOf(window.result_trace_widget) >= 0
        assert "CASE_1" in window.result_trace_widget.table.item(0, 7).text()
        assert window.tabs.currentWidget() is window.result_trace_widget
        assert "RUN_RESTORE" in window.status_label.text()
        assert window.confirm_yes_button.isEnabled() is True
    finally:
        window.close()
        app.processEvents()

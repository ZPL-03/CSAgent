from __future__ import annotations

import copy
import csv
import json
import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import yaml
from PyQt6.QtGui import QFont, QFontMetrics
from PyQt6.QtWidgets import QApplication, QComboBox, QFrame, QLabel, QLineEdit, QPushButton

import gui.main_window as main_window_module
from core.task_parser import TaskParser
from gui.candidate_widget import CandidateWidget
from gui.chat_widget import ChatWidget
from gui.knowledge_widget import KnowledgeWidget
from gui.main_window import MainWindow
from gui.theme import application_stylesheet
from gui.workbench_widgets import AgentStatusCard, FlowDagWidget, StatusPill
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


def _config_loader(payload: dict):
    def loader() -> dict:
        return copy.deepcopy(payload)

    loader.cache_clear = lambda: None
    return loader


class FakeKnowledge:
    def status(self) -> dict:
        return {"ready": True}

    def retrieve(self, task: dict, top_k: int | None = None, kg_top_k: int | None = None) -> dict:
        return {"query": "restore", "chunks": [], "relations": []}

    def retrieve_by_query(self, query: str, top_k: int | None = None, kg_top_k: int | None = None) -> dict:
        return {"query": query, "chunks": [], "relations": []}


class FakeBatchEvaluateOrchestrator:
    def __init__(self, progress_callback=None) -> None:
        self.progress_callback = progress_callback

    def prepare_candidates_for_fem(self, task, candidates):
        return [
            {
                **candidate,
                "candidate_id": f"C{16 + index}",
                "display_name": f"C{16 + index}",
                "session_candidate_id": candidate["candidate_id"],
            }
            for index, candidate in enumerate(candidates)
        ]

    def evaluate_prepared_candidate(self, task, candidate):
        return {
            "candidate_id": candidate["candidate_id"],
            "session_candidate_id": candidate["session_candidate_id"],
            "status": "success",
            "ultimate_pressure_MPa": 45.0,
            "verdict": "通过",
        }

    def persist_knowledge_records(self, task, designs, results):
        return [
            {
                "status": "stored",
                "case_id": f"CASE_{16 + index}",
                "candidate_id": design["candidate_id"],
                "session_candidate_id": design["session_candidate_id"],
            }
            for index, design in enumerate(designs)
        ]


def test_confirmation_controls_share_input_action_row(monkeypatch) -> None:
    monkeypatch.setenv("CSDM_cph_DISABLE_LLM_AUTO", "1")
    app = _app()
    window = MainWindow()
    try:
        row_widgets = [window.input_action_layout.itemAt(index).widget() for index in range(window.input_action_layout.count())]
        assert row_widgets == [
            window.example_button,
            window.input_line,
            window.generate_button,
            window.confirm_yes_button,
            window.confirm_no_button,
        ]
        assert window.input_line.sizePolicy().horizontalPolicy().name == "Expanding"
        for button in [window.generate_button, window.confirm_yes_button, window.confirm_no_button]:
            text_width = button.fontMetrics().horizontalAdvance(button.text())
            assert text_width <= max(0, button.width() - 18)
    finally:
        window.close()
        app.processEvents()


def test_report_button_allows_partial_evaluated_results(monkeypatch) -> None:
    monkeypatch.setenv("CSDM_cph_DISABLE_LLM_AUTO", "1")
    app = _app()
    window = MainWindow()
    try:
        window.session.task = TaskParser().parse_instruction("外压 30 MPa，生成 6 个候选，初筛保留 3 个候选")
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
    finally:
        window.close()
        app.processEvents()


def test_live_visual_toggle_keeps_fem_result_available(monkeypatch) -> None:
    monkeypatch.setenv("CSDM_cph_DISABLE_LLM_AUTO", "1")
    app = _app()
    window = MainWindow()
    try:
        calls: list[tuple[str, str]] = []

        def record_candidate(candidate: dict) -> None:
            calls.append(("candidate", str(candidate.get("candidate_id"))))

        def record_result(result: dict) -> None:
            calls.append(("fem", str(result.get("candidate_id"))))

        monkeypatch.setattr(window.live_result_view, "show_candidate", record_candidate)
        monkeypatch.setattr(window.live_result_view, "show_mode_shape", record_result)

        candidate = _candidate("TMP_1")
        result = {"candidate_id": "C1", "session_candidate_id": "TMP_1", "status": "success"}
        window.session.candidates = [candidate]
        window.session.results_by_session_id = {"TMP_1": result}
        window._live_visual_mode = "fem"

        window._show_live_visual()
        assert calls[-1] == ("fem", "C1")

        window._queue_candidate_preview(candidate)
        window._flush_candidate_preview()
        assert calls[-1] == ("candidate", "TMP_1")
        assert window.live_visual_toggle_button.text() == "FE"

        window._toggle_live_visual_mode()
        assert calls[-1] == ("fem", "C1")
        assert window.live_visual_toggle_button.text() == "3D"
    finally:
        window.close()
        app.processEvents()


def test_live_visual_toggle_prefers_selected_candidate_result(monkeypatch) -> None:
    monkeypatch.setenv("CSDM_cph_DISABLE_LLM_AUTO", "1")
    app = _app()
    window = MainWindow()
    try:
        calls: list[tuple[str, str]] = []

        monkeypatch.setattr(window.live_result_view, "show_candidate", lambda candidate: None)
        monkeypatch.setattr(
            window.live_result_view,
            "show_mode_shape",
            lambda result: calls.append(("fem", str(result.get("candidate_id")))),
        )

        first = _candidate("TMP_1")
        second = _candidate("TMP_2")
        window.session.candidates = [first, second]
        window.session.results_by_session_id = {
            "TMP_1": {"candidate_id": "C1", "session_candidate_id": "TMP_1", "status": "success"},
            "TMP_2": {"candidate_id": "C2", "session_candidate_id": "TMP_2", "status": "success"},
        }
        window._selected_live_candidate = first
        window._live_visual_mode = "fem"

        window._show_live_visual()

        assert calls[-1] == ("fem", "C1")
    finally:
        window.close()
        app.processEvents()


def test_design_solution_report_uses_candidates_before_fem(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("CSDM_cph_DISABLE_LLM_AUTO", "1")
    app = _app()
    window = MainWindow()
    try:
        window.session.task = TaskParser().parse_instruction("外压 30 MPa，生成 6 个候选，初筛保留 3 个候选")
        window.session.candidates = [_candidate("TMP_1"), _candidate("TMP_2")]
        window.session.screened_candidates = [_candidate("TMP_2")]
        window.report_output_dir = tmp_path
        index = window.report_type_selector.findData("design_solution")
        window.report_type_selector.setCurrentIndex(index)

        window._update_button_states()
        assert window.report_button.isEnabled() is True

        captured = {}
        window._run_action = lambda action, payload, status_text: captured.update(
            {"action": action, "payload": payload, "status_text": status_text}
        )
        window._start_report()

        assert captured["action"] == "report"
        assert captured["payload"]["report_kind"] == "design_solution"
        assert captured["payload"]["output_dir"] == str(tmp_path)
        assert [item["candidate_id"] for item in captured["payload"]["candidates"]] == ["TMP_2"]
        assert captured["payload"]["results"] == []
    finally:
        window.close()
        app.processEvents()


def test_fem_report_uses_output_dir_and_evaluated_results(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("CSDM_cph_DISABLE_LLM_AUTO", "1")
    app = _app()
    window = MainWindow()
    try:
        window.session.task = TaskParser().parse_instruction("外压 30 MPa，生成 6 个候选，初筛保留 3 个候选")
        window.session.candidates = [_candidate("TMP_1"), _candidate("TMP_2")]
        window.session.results_by_session_id = {"TMP_1": {"candidate_id": "C1", "session_candidate_id": "TMP_1"}}
        window.report_output_dir = tmp_path
        index = window.report_type_selector.findData("fem")
        window.report_type_selector.setCurrentIndex(index)

        window._update_button_states()
        assert window.report_button.isEnabled() is True

        captured = {}
        window._run_action = lambda action, payload, status_text: captured.update(
            {"action": action, "payload": payload, "status_text": status_text}
        )
        window._start_report()

        assert captured["action"] == "report"
        assert captured["payload"]["report_kind"] == "fem"
        assert captured["payload"]["output_dir"] == str(tmp_path)
        assert [item["candidate_id"] for item in captured["payload"]["candidates"]] == ["TMP_1"]
        assert [item["candidate_id"] for item in captured["payload"]["results"]] == ["C1"]
    finally:
        window.close()
        app.processEvents()


def test_report_completion_updates_session_and_open_button(monkeypatch) -> None:
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
        assert window.open_report_button.isEnabled() is True
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


def test_workbench_non_destructive_buttons_execute_connected_actions(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("CSDM_cph_DISABLE_LLM_AUTO", "1")
    monkeypatch.setattr("gui.main_window.RESULTS_DIR", tmp_path)
    app = _app()
    window = MainWindow()
    try:
        window.example_button.click()
        assert "外压 30 MPa" in window.input_line.text()
        assert "生成 12 个候选" in window.input_line.text()

        approvals: list[bool] = []
        window._respond_confirmation = lambda approved: approvals.append(approved)
        window.confirm_yes_button.setEnabled(True)
        window.confirm_no_button.setEnabled(True)
        window.confirm_yes_button.click()
        window.confirm_no_button.click()
        assert approvals == [True, False]

        window.reset_view_button.click()
        window.fit_view_button.click()

        window.trace_button.click()
        app.processEvents()
        assert window.stack.currentWidget() is window.monitor_page

        window.session.workflow_run_id = "RUN_CLICK"
        window.session.instruction = "按钮点击导出测试"
        window.session.task = TaskParser().parse_instruction("外压 30 MPa，生成 2 个候选，初筛保留 1 个候选")
        candidate = _candidate("TMP_1")
        window.session.candidates = [candidate]
        window.session.results_by_session_id = {
            "TMP_1": {
                "candidate_id": "C1",
                "session_candidate_id": "TMP_1",
                "ultimate_pressure_MPa": 42.0,
                "linear_buckling_pressure_MPa": 31.5,
                "status": "success",
                "verdict": "通过",
            }
        }
        window._update_button_states()
        assert window.export_data_button.isEnabled() is True

        window.export_data_button.click()
        app.processEvents()

        assert (tmp_path / "session_export_RUN_CLICK.json").exists()
        assert (tmp_path / "session_trace_RUN_CLICK.csv").exists()
        assert "数据导出完成" in window.log_widget.toPlainText()
    finally:
        window.close()
        app.processEvents()


def test_primary_workflow_buttons_click_through_to_pipeline(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("CSDM_cph_DISABLE_LLM_AUTO", "1")
    app = _app()
    window = MainWindow()
    calls: list[tuple[str, dict, str]] = []

    def fake_run_action(action: str, payload: dict, status_text: str) -> None:
        calls.append((action, payload, status_text))

    try:
        window._run_action = fake_run_action
        instruction = "请为复合材料外压圆柱耐压壳设计方案，外压 30 MPa，极限压力不低于 35 MPa，生成 6 个候选，初筛保留 3 个候选"
        window.input_line.setText(instruction)
        window.generate_button.click()
        assert calls[-1][0] == "conversation_start"
        assert calls[-1][1]["instruction"] == instruction
        assert window.input_line.text() == ""

        task = TaskParser().parse_instruction(instruction)
        candidates = [_candidate("TMP_1"), _candidate("TMP_2")]
        window.session.task = task
        window.session.candidates = candidates
        window.session.stage = "candidate_pool"
        window.session.pending_confirmation = None
        window.workbench_candidate_widget.update_candidates(candidates)
        window._update_button_states()

        window.screen_button.click()
        assert calls[-1][0] == "screen"
        assert calls[-1][1]["candidates"] == candidates

        monkeypatch.setattr(window, "_selected_candidates_for_evaluation", lambda: [candidates[0]])
        window._update_button_states()
        window.evaluate_selected_button.click()
        assert calls[-1][0] == "evaluate"
        assert [item["candidate_id"] for item in calls[-1][1]["candidates"]] == ["TMP_1"]

        window.evaluate_all_button.click()
        assert calls[-1][0] == "evaluate"
        assert [item["candidate_id"] for item in calls[-1][1]["candidates"]] == ["TMP_1", "TMP_2"]

        window.session.results_by_session_id = {
            "TMP_1": {
                "candidate_id": "C1",
                "session_candidate_id": "TMP_1",
                "ultimate_pressure_MPa": 41.2,
                "status": "success",
                "verdict": "通过",
            }
        }
        window.report_output_dir = tmp_path
        report_index = window.report_type_selector.findData("fem")
        if report_index >= 0:
            window.report_type_selector.setCurrentIndex(report_index)
        window._update_button_states()
        window.report_button.click()
        assert calls[-1][0] == "report"
        assert calls[-1][1]["report_kind"] == "fem"
        assert calls[-1][1]["output_dir"] == str(tmp_path)
        assert calls[-1][1]["results"][0]["candidate_id"] == "C1"
    finally:
        window.close()
        app.processEvents()


def test_utility_and_sidebar_buttons_click_through(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("CSDM_cph_DISABLE_LLM_AUTO", "1")
    monkeypatch.setattr("gui.knowledge_widget.DomainKnowledgeBase", FakeKnowledge)
    monkeypatch.setattr(
        main_window_module.QFileDialog,
        "getExistingDirectory",
        lambda *args, **kwargs: str(tmp_path),
    )
    opened_paths: list[str] = []
    monkeypatch.setattr(
        main_window_module.QDesktopServices,
        "openUrl",
        lambda url: opened_paths.append(url.toLocalFile()) or True,
    )
    app = _app()
    store = WorkflowEventStore(tmp_path / "workflow.sqlite3")
    task = TaskParser().parse_instruction("外压 30 MPa，生成 6 个候选，初筛保留 3 个候选")
    snapshot = {
        "run_id": "RUN_BUTTONS",
        "instruction": "restore button coverage",
        "task": task,
        "candidates": [_candidate("TMP_1")],
        "screened_candidates": [_candidate("TMP_1")],
        "evaluated_candidates": [],
        "results": [],
        "knowledge_updates": [],
        "report": None,
        "stage": "awaiting_fem_confirmation",
        "pending_confirmation": "fem_evaluation",
        "screen_skipped": False,
    }
    store.create_run("RUN_BUTTONS", snapshot["instruction"])
    store.save_snapshot("RUN_BUTTONS", snapshot)
    report_path = tmp_path / "latest_report.md"
    report_path.write_text("# report", encoding="utf-8")

    window = MainWindow()
    maintenance_calls: list[str] = []
    try:
        window.workflow_event_store = store
        window.workflow_widget.event_store = store
        window.workflow_widget.simulation_queue = SimulationJobQueue(store.db_path)
        window.knowledge_widget._run_maintenance = lambda action: maintenance_calls.append(action)

        window.report_dir_button.click()
        assert window.report_output_dir == tmp_path

        window.session.report = {"markdown_path": str(report_path)}
        window._update_button_states()
        assert window.open_report_button.isEnabled() is True
        window.open_report_button.click()
        assert len(opened_paths) == 1
        assert Path(opened_paths[0]) == report_path

        window.knowledge_right_rebuild_button.click()
        window.knowledge_right_snapshot_button.click()
        assert maintenance_calls == ["rebuild", "export"]

        window._refresh_run_selector()
        assert window.run_selector.currentData() == "RUN_BUTTONS"
        window.restore_run_button.click()
        assert window.session.workflow_run_id == "RUN_BUTTONS"
        assert window.session.pending_confirmation == "fem_evaluation"

        window.reset_button.click()
        assert window.session.task is None
        assert window.session.candidates == []
        assert window.input_line.text() == ""
    finally:
        window.close()
        app.processEvents()


def test_remaining_workbench_and_workflow_buttons_click_through(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("CSDM_cph_DISABLE_LLM_AUTO", "1")
    monkeypatch.setattr("gui.knowledge_widget.DomainKnowledgeBase", FakeKnowledge)
    health_calls: list[int] = []

    def fake_probe(timeout_seconds=12):
        health_calls.append(timeout_seconds)
        return [
            {
                "role": "primary",
                "name": "domain_finetuned_primary",
                "model": "csllm",
                "base_url_configured": True,
                "api_key_configured": True,
                "available_for_call": True,
                "health_status": "success",
                "health_message": "可用",
                "latency_ms": 1.0,
                "error": "",
            }
        ]

    audit_calls: list[str] = []

    def fake_write_run_audit(event_store, simulation_queue, workflow_run_id, output_dir):
        audit_calls.append(workflow_run_id)
        path = tmp_path / f"run_audit_{workflow_run_id}.md"
        path.write_text("# audit", encoding="utf-8")
        return path

    monkeypatch.setattr("gui.workflow_widget.probe_llm_backends", fake_probe)
    monkeypatch.setattr("gui.workflow_widget.write_run_audit", fake_write_run_audit)
    app = _app()
    store = WorkflowEventStore(tmp_path / "workflow.sqlite3")
    task = TaskParser().parse_instruction("外压 30 MPa，生成 6 个候选，初筛保留 3 个候选")
    store.create_run("RUN_CONTROLS", "button controls")
    store.save_snapshot(
        "RUN_CONTROLS",
        {
            "run_id": "RUN_CONTROLS",
            "instruction": "button controls",
            "task": task,
            "stage": "awaiting_fem_confirmation",
            "pending_confirmation": "fem_evaluation",
            "candidates": [_candidate("TMP_1")],
            "screened_candidates": [_candidate("TMP_1")],
            "results": [],
            "knowledge_updates": [],
            "report": None,
        },
    )
    window = MainWindow()
    knowledge_refresh_calls: list[tuple[bool, bool, int]] = []
    visual_calls: list[tuple[str, str]] = []
    try:
        window.workflow_event_store = store
        window.workflow_widget.event_store = store
        window.workflow_widget.simulation_queue = SimulationJobQueue(store.db_path)
        window._queue_knowledge_refresh = (
            lambda task, load_evidence=False, force=False, delay_ms=0: knowledge_refresh_calls.append(
                (load_evidence, force, delay_ms)
            )
        )
        window.live_result_view.show_mode_shape = lambda result: visual_calls.append(
            ("fem", str(result.get("candidate_id") or ""))
        )
        window.live_result_view.show_candidate = lambda candidate: visual_calls.append(
            ("geometry", str(candidate.get("candidate_id") or ""))
        )

        window.refresh_button.click()
        assert knowledge_refresh_calls == [(True, True, 0)]

        window._refresh_run_selector()
        window.refresh_runs_button.click()
        assert window.run_selector.currentData() == "RUN_CONTROLS"

        window.workflow_widget.refresh("RUN_CONTROLS", "awaiting_fem_confirmation", "fem_evaluation")
        assert window.workflow_widget.audit_button.isEnabled() is True
        window.workflow_widget.health_button.click()
        assert health_calls == [12]
        assert window.workflow_widget.llm_health_results[0]["model"] == "csllm"
        window.workflow_widget.audit_button.click()
        assert audit_calls == ["RUN_CONTROLS"]
        assert (tmp_path / "run_audit_RUN_CONTROLS.md").exists()

        candidate = _candidate("TMP_1")
        result = {
            "candidate_id": "C1",
            "session_candidate_id": "TMP_1",
            "mode_shape": {"nodes": [], "elements": [], "values": []},
        }
        window.session.task = task
        window.session.candidates = [candidate]
        window.session.results_by_session_id = {"TMP_1": result}
        window._selected_live_candidate = candidate
        window._show_live_visual()
        assert visual_calls[-1] == ("fem", "C1")
        assert window.live_visual_toggle_button.text() == "3D"

        window.live_visual_toggle_button.click()
        assert visual_calls[-1] == ("geometry", "TMP_1")
        assert window.live_visual_toggle_button.text() == "FE"

        window.live_visual_toggle_button.click()
        assert visual_calls[-1] == ("fem", "C1")
        assert window.live_visual_toggle_button.text() == "3D"
    finally:
        window.close()
        app.processEvents()


def test_pipeline_worker_evaluate_action_keeps_batch_candidate_identity(monkeypatch) -> None:
    monkeypatch.setenv("CSDM_cph_DISABLE_LLM_AUTO", "1")
    monkeypatch.setattr(main_window_module, "OrchestratorAgent", FakeBatchEvaluateOrchestrator)
    app = _app()
    task = TaskParser().parse_instruction("外压 30 MPa，生成 6 个候选，初筛保留 3 个候选")
    worker = main_window_module.PipelineWorker(
        "evaluate",
        {
            "task": task,
            "candidates": [_candidate("TMP_10"), _candidate("TMP_4"), _candidate("TMP_9")],
        },
    )
    captured: dict = {}
    errors: list[str] = []
    worker.finished.connect(lambda action, payload: captured.update({"action": action, "payload": payload}))
    worker.failed.connect(errors.append)

    worker.run()
    app.processEvents()

    assert errors == []
    assert captured["action"] == "evaluate"
    payload = captured["payload"]
    assert [item["candidate_id"] for item in payload["fem_designs"]] == ["C16", "C17", "C18"]
    assert [item["session_candidate_id"] for item in payload["fem_designs"]] == ["TMP_10", "TMP_4", "TMP_9"]
    assert [item["candidate_id"] for item in payload["results"]] == ["C16", "C17", "C18"]
    assert [item["session_candidate_id"] for item in payload["knowledge_updates"]] == ["TMP_10", "TMP_4", "TMP_9"]


def test_pipeline_worker_evaluate_action_emits_realtime_fem_events(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("CSDM_cph_DISABLE_LLM_AUTO", "1")
    monkeypatch.setattr(main_window_module, "OrchestratorAgent", FakeBatchEvaluateOrchestrator)
    app = _app()
    task = TaskParser().parse_instruction("外压 30 MPa，生成 3 个候选，初筛保留 2 个候选")
    workflow_db_path = tmp_path / "workflow.sqlite3"
    worker = main_window_module.PipelineWorker(
        "evaluate",
        {
            "task": task,
            "workflow_run_id": "RUN_TEST_FEM",
            "workflow_db_path": workflow_db_path,
            "candidates": [_candidate("TMP_10"), _candidate("TMP_4")],
        },
    )
    messages: list[tuple[str, str, object]] = []
    captured: dict = {}
    errors: list[str] = []
    worker.message.connect(lambda sender, message, event: messages.append((sender, message, event)))
    worker.finished.connect(lambda action, payload: captured.update({"action": action, "payload": payload}))
    worker.failed.connect(errors.append)

    worker.run()
    app.processEvents()

    assert errors == []
    runtime_events = [
        event
        for _, _, event in messages
        if isinstance(event, dict) and event.get("event_type") == "workflow_runtime_event"
    ]
    assert [event["payload"]["runtime_event_type"] for event in runtime_events] == [
        "simulation_job_queued",
        "simulation_job_started",
        "simulation_job_completed",
        "simulation_job_queued",
        "simulation_job_started",
        "simulation_job_completed",
    ]
    assert [event["payload"]["candidate_id"] for event in runtime_events if event["payload"]["runtime_event_type"] == "simulation_job_completed"] == [
        "C16",
        "C17",
    ]
    partial_results = [
        event["payload"]["result"]
        for _, _, event in messages
        if isinstance(event, dict) and event.get("event_type") == "fem_partial_result"
    ]
    assert [result["candidate_id"] for result in partial_results] == ["C16", "C17"]
    assert captured["action"] == "evaluate"

    store = WorkflowEventStore(workflow_db_path)
    assert store.has_run("RUN_TEST_FEM")
    persisted_events = store.list_events("RUN_TEST_FEM")
    assert [event["event_type"] for event in persisted_events] == [
        "simulation_job_queued",
        "simulation_job_started",
        "simulation_job_completed",
        "simulation_job_queued",
        "simulation_job_started",
        "simulation_job_completed",
    ]
    assert [
        event["payload"]["candidate_id"]
        for event in persisted_events
        if event["event_type"] == "simulation_job_completed"
    ] == ["C16", "C17"]


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
        window._switch_workspace_page(2)
        assert window.stack.currentWidget() is window.monitor_page
        assert window.monitor_dashboard_widget.parent() is not None
        assert window.workflow_widget.parent() is not None
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
        assert "RUN_RESTORE" in window.status_label.text()
        assert window.confirm_yes_button.isEnabled() is True
    finally:
        window.close()
        app.processEvents()


def test_main_window_routes_runtime_events_to_logs_and_actionable_chat(monkeypatch) -> None:
    monkeypatch.setenv("CSDM_cph_DISABLE_LLM_AUTO", "1")
    app = _app()
    window = MainWindow()
    try:
        before_chat = window.chat_widget.toPlainText()
        event = {
            "event_type": "workflow_runtime_event",
            "payload": {
                "runtime_event_type": "node_started",
                "runtime_agent": "parse_task",
                "runtime_stage": "parse_task",
            },
        }

        window._handle_message("FLOW", "节点开始：parse_task", event)

        assert "node_started @ parse_task" in window.log_widget.toPlainText()
        assert "节点开始：parse_task" not in window.chat_widget.toPlainText()
        assert window.chat_widget.toPlainText() == before_chat
        assert window.runtime_agent_states["ORCHESTRATOR"] == "active"
        assert window.flow_dag_widget.agent_states["ORCHESTRATOR"] == "active"

        event["payload"]["runtime_event_type"] = "node_completed"
        window._handle_message("FLOW", "节点完成：parse_task", event)

        assert window.runtime_agent_states["ORCHESTRATOR"] == "done"
        assert window.flow_dag_widget.agent_states["ORCHESTRATOR"] == "done"

        simulation_event = {
            "event_type": "workflow_runtime_event",
            "payload": {
                "runtime_event_type": "simulation_job_started",
                "runtime_agent": "FEM_AGENT",
                "runtime_stage": "evaluate_candidates",
                "record": {"run_id": "RUN_CHAT"},
            },
        }
        window._handle_message("FLOW", "有限元作业开始：RUN_CHAT:TMP_1", simulation_event)

        assert "simulation_job_started @ evaluate_candidates" in window.log_widget.toPlainText()
        assert "FEM_AGENT: 有限元作业开始：RUN_CHAT:TMP_1" in window.chat_widget.toPlainText()
    finally:
        window.close()
        app.processEvents()


def test_main_window_shell_layout_keeps_reference_workbench_structure(monkeypatch) -> None:
    monkeypatch.setenv("CSDM_cph_DISABLE_LLM_AUTO", "1")
    app = _app()
    window = MainWindow()
    try:
        window.resize(1280, 960)
        window.locale.set_theme("dark")
        window._apply_styles()
        window._update_overview_cards()
        window.show()
        app.processEvents()

        assert window.logo_label.property("mode") == "image"
        assert not window.logo_label.pixmap().isNull()
        assert window.app_title_label.text() == "CSAgent"
        assert window.model_status_label.isVisible() is True
        assert window.reset_view_button.isVisible() is True
        assert window.fit_view_button.isVisible() is True
        assert "#e5edf7" in window.stage_card.text()
        assert window.queue_progress.isVisible() is False

        for index, button in enumerate(window.nav_buttons):
            window._switch_workspace_page(index)
            app.processEvents()
            assert button.isChecked() is True
            assert window.stack.currentIndex() == index
            assert window.left_stack.currentIndex() == index
            assert window.right_stack.currentIndex() == index
    finally:
        window.close()
        app.processEvents()


def test_main_window_initial_geometry_fits_available_work_area(monkeypatch) -> None:
    monkeypatch.setenv("CSDM_cph_DISABLE_LLM_AUTO", "1")
    app = _app()
    window = MainWindow()
    try:
        available = app.primaryScreen().availableGeometry()
        target = window._target_window_size()

        assert target.width() <= available.width()
        assert target.height() <= available.height()
        assert window.width() <= available.width()
        assert window.height() <= available.height()
    finally:
        window.close()
        app.processEvents()


def test_main_window_default_theme_is_dark(monkeypatch) -> None:
    monkeypatch.setenv("CSDM_cph_DISABLE_LLM_AUTO", "1")
    app = _app()
    window = MainWindow()
    try:
        assert window.locale.theme == "dark"
        assert window.theme_selector.currentData() == "dark"
    finally:
        window.close()
        app.processEvents()


def test_restored_oversized_window_geometry_is_clamped(monkeypatch) -> None:
    monkeypatch.setenv("CSDM_cph_DISABLE_LLM_AUTO", "1")
    app = _app()
    window = MainWindow()
    try:
        target = window._target_window_size()
        window.resize(target.width() * 2, target.height())
        window._ensure_window_within_work_area(clamp_to_target=True)
        app.processEvents()

        assert window.width() <= target.width()
        assert window.height() <= target.height()
        assert window.width() / max(1, window.height()) <= 1.72
    finally:
        window.close()
        app.processEvents()


def test_main_window_requested_width_is_not_expanded_by_hidden_pages(monkeypatch) -> None:
    monkeypatch.setenv("CSDM_cph_DISABLE_LLM_AUTO", "1")
    app = _app()
    window = MainWindow()
    try:
        requested_width = 1280
        for index in range(len(window.nav_buttons)):
            window._switch_workspace_page(index)
            window.resize(requested_width, 960)
            window.show()
            app.processEvents()

            assert window.stack.minimumSizeHint().width() <= 600
            assert window.main_splitter.minimumSizeHint().width() <= requested_width
            assert window.width() <= requested_width
    finally:
        window.close()
        app.processEvents()


def test_workbench_right_rail_fits_non_maximized_viewport(monkeypatch) -> None:
    monkeypatch.setenv("CSDM_cph_DISABLE_LLM_AUTO", "1")
    app = _app()
    window = MainWindow()
    try:
        window.locale.set_theme("dark")
        window._apply_styles()
        window.resize(1280, 960)
        window._sync_main_splitter_sizes()
        window.show()
        app.processEvents()

        margins = window.workbench_right_content.layout().contentsMargins()
        assert margins.left() == margins.right()
        assert window.workbench_right_scroll.viewport().width() >= window.workbench_right_content.width() - 1
        assert window.right_stack.width() >= 350
    finally:
        window.close()
        app.processEvents()


def test_candidate_pool_empty_and_runtime_use_same_splitter_balance() -> None:
    app = _app()
    widget = CandidateWidget()
    try:
        widget.resize(760, 280)
        widget.show()
        app.processEvents()
        empty_sizes = widget.splitter.sizes()

        widget.update_candidates([_candidate(f"C{index}") for index in range(1, 7)])
        app.processEvents()
        runtime_sizes = widget.splitter.sizes()

        for sizes in [empty_sizes, runtime_sizes]:
            table_width, detail_width = sizes
            assert table_width >= 260
            assert detail_width >= 280
            assert 0.8 <= table_width / max(1, detail_width) <= 1.25
        assert abs(empty_sizes[0] - runtime_sizes[0]) <= 32
    finally:
        widget.close()
        app.processEvents()


def test_status_pill_centers_status_dot_and_text_group() -> None:
    app = _app()
    _ = app
    pill = StatusPill("领域主模型", "success")
    pill.resize(164, 34)
    font = QFont(pill.font())
    font.setPointSize(10)

    dot_center, text_rect, display_text = pill._content_geometry(font)
    metrics = QFontMetrics(font)
    content_left = dot_center.x() - 5.5
    content_right = text_rect.left() + metrics.horizontalAdvance(display_text)
    content_center = (content_left + content_right) / 2.0

    assert abs(dot_center.y() - pill.height() / 2.0) < 0.1
    assert abs(text_rect.center().y() - pill.height() / 2.0) < 0.1
    assert abs(content_center - pill.width() / 2.0) < 1.5


def test_flow_dag_merges_requirement_parsing_into_orchestrator() -> None:
    app = _app()
    _ = app
    names = [node.name for node in FlowDagWidget.MAIN_NODES]
    assert names == ["ORCHESTRATOR", "CANDIDATE_GEN", "SCREENER", "FEM_AGENT", "REPORT_GEN"]
    assert FlowDagWidget.MAIN_NODES[0].subtitle == "需求解析 / 编排"
    assert FlowDagWidget.KNOWLEDGE_NODE.agent == "KNOWLEDGE_AGENT"
    widget = FlowDagWidget()
    assert widget._node_status_text(FlowDagWidget.MAIN_NODES[0], "waiting") == "需求解析 / 编排 · 等待"
    assert widget._node_status_text(FlowDagWidget.MAIN_NODES[0], "active") == "需求解析 / 编排 · 运行中"
    assert widget._node_status_text(FlowDagWidget.KNOWLEDGE_NODE, "active", "rag") == "检索证据 / RAG-KG"


def test_visible_workbench_buttons_keep_text_inside_layout(monkeypatch) -> None:
    monkeypatch.setenv("CSDM_cph_DISABLE_LLM_AUTO", "1")
    app = _app()
    window = MainWindow()
    try:
        window.resize(1280, 960)
        window.show()
        app.processEvents()

        checked_buttons: set[int] = set()
        for index in range(len(window.nav_buttons)):
            window._switch_workspace_page(index)
            app.processEvents()
            visible_buttons = [
                button
                for button in window.findChildren(QPushButton)
                if button.isVisible() and button.text().strip()
            ]
            assert visible_buttons
            for button in visible_buttons:
                checked_buttons.add(id(button))
                text_width = button.fontMetrics().horizontalAdvance(button.text())
                assert text_width <= max(0, button.width() - 18), (
                    button.text(),
                    button.width(),
                    text_width,
                    index,
                )

        assert id(window.knowledge_widget.batch_button) in checked_buttons
        assert id(window.knowledge_widget.rebuild_button) in checked_buttons
        assert id(window.knowledge_widget.export_snapshot_button) in checked_buttons
    finally:
        window.close()
        app.processEvents()


def test_main_splitter_widths_do_not_expand_past_window(monkeypatch) -> None:
    monkeypatch.setenv("CSDM_cph_DISABLE_LLM_AUTO", "1")
    app = _app()
    window = MainWindow()
    try:
        for width, height in [(1180, 860), (1280, 900), (1360, 960), (1680, 1050)]:
            window.resize(width, height)
            window.show()
            app.processEvents()
            window._sync_main_splitter_sizes()
            app.processEvents()
            sizes = window.main_splitter.sizes()
            assert sum(sizes) <= window.main_splitter.width() + 4
            assert window.left_stack.width() <= 286
            assert 318 <= window.right_stack.width() <= 370
            right_edge = window.right_stack.mapTo(window, window.right_stack.rect().bottomRight()).x()
            assert right_edge <= window.rect().right() + 2
    finally:
        window.close()
        app.processEvents()


def test_main_window_critical_buttons_have_connected_actions(monkeypatch) -> None:
    monkeypatch.setenv("CSDM_cph_DISABLE_LLM_AUTO", "1")
    app = _app()
    window = MainWindow()

    def receiver_count(button: QPushButton) -> int:
        total = 0
        for signal_name in ("clicked", "toggled"):
            signal = getattr(button, signal_name, None)
            if signal is None:
                continue
            try:
                total += button.receivers(signal)
            except TypeError:
                continue
        return total

    try:
        window.show()
        app.processEvents()
        assert window.nav_group.receivers(window.nav_group.idClicked) > 0
        for name, button in zip(
            ["nav_workbench", "nav_knowledge", "nav_monitor", "nav_settings"],
            window.nav_buttons,
        ):
            assert isinstance(button, QPushButton), name
            assert button.text().strip(), name

        button_specs = [
            ("generate", window.generate_button),
            ("confirm_yes", window.confirm_yes_button),
            ("confirm_no", window.confirm_no_button),
            ("example", window.example_button),
            ("trace", window.trace_button),
            ("refresh_knowledge", window.refresh_button),
            ("report_dir", window.report_dir_button),
            ("open_report", window.open_report_button),
            ("export_data", window.export_data_button),
            ("live_visual_mode", window.live_visual_toggle_button),
            ("reset_view", window.reset_view_button),
            ("fit_view", window.fit_view_button),
            ("refresh_runs", window.refresh_runs_button),
            ("restore_run", window.restore_run_button),
            ("screen", window.screen_button),
            ("evaluate_selected", window.evaluate_selected_button),
            ("evaluate_all", window.evaluate_all_button),
            ("report", window.report_button),
            ("reset_session", window.reset_button),
            ("settings_save", window.settings_save_button),
            ("settings_reload", window.settings_reload_button),
            ("knowledge_search", window.knowledge_widget.search_button),
            ("knowledge_upload", window.knowledge_widget.upload_button),
            ("knowledge_batch", window.knowledge_widget.batch_button),
            ("knowledge_rebuild", window.knowledge_widget.rebuild_button),
            ("knowledge_export_snapshot", window.knowledge_widget.export_snapshot_button),
            ("knowledge_refresh", window.knowledge_widget.refresh_button),
            ("knowledge_graph_reset", window.knowledge_widget.graph_reset_button),
            ("knowledge_graph_zoom_in", window.knowledge_widget.graph_zoom_in_button),
            ("knowledge_graph_zoom_out", window.knowledge_widget.graph_zoom_out_button),
            ("knowledge_graph_label_toggle", window.knowledge_widget.graph_label_button),
            ("knowledge_graph_relation_toggle", window.knowledge_widget.graph_relation_button),
            ("knowledge_right_rebuild", window.knowledge_right_rebuild_button),
            ("knowledge_right_snapshot", window.knowledge_right_snapshot_button),
        ]

        for name, button in button_specs:
            assert isinstance(button, QPushButton), name
            assert button.text().strip() or button.toolTip().strip(), name
            assert receiver_count(button) > 0, name
    finally:
        window.close()
        app.processEvents()


def test_main_window_controls_survive_page_theme_language_switches(monkeypatch) -> None:
    monkeypatch.setenv("CSDM_cph_DISABLE_LLM_AUTO", "1")
    app = _app()
    calls: list[tuple[str, object | None]] = []

    def record(name: str):
        def _recorder(_self, *args, **_kwargs) -> None:
            calls.append((name, args[0] if args else None))

        return _recorder

    def record_knowledge(name: str):
        def _recorder(_self, *args, **_kwargs) -> None:
            calls.append((name, args[0] if args else None))

        return _recorder

    patched_main_window_methods = {
        "_start_conversation": "start",
        "_respond_confirmation": "confirm",
        "_load_example_prompt": "example",
        "_refresh_knowledge_view": "refresh_knowledge",
        "_open_latest_report": "open_report",
        "_export_session_data": "export_data",
        "_choose_report_output_dir": "report_dir",
        "_refresh_run_selector": "refresh_runs",
        "_restore_selected_run": "restore_run",
        "_start_screen": "screen",
        "_start_evaluate_selected": "evaluate_selected",
        "_start_evaluate_all": "evaluate_all",
        "_start_report": "report",
        "_reset_session": "reset_session",
        "_save_settings_from_page": "settings_save",
        "_reload_settings_page": "settings_reload",
    }
    for method_name, call_name in patched_main_window_methods.items():
        monkeypatch.setattr(MainWindow, method_name, record(call_name))

    for method_name, call_name in {
        "_search_from_input": "knowledge_search",
        "_select_and_ingest_file": "knowledge_upload",
        "_select_and_ingest_files": "knowledge_batch",
        "_run_maintenance": "knowledge_maintenance",
    }.items():
        monkeypatch.setattr(KnowledgeWidget, method_name, record_knowledge(call_name))

    window = MainWindow()
    try:
        window.resize(1280, 960)
        window.show()
        app.processEvents()

        for index, button in enumerate(window.nav_buttons):
            button.click()
            app.processEvents()
            assert window.stack.currentIndex() == index
            assert button.isChecked()

        for selector in [window.language_selector, window.theme_selector]:
            assert isinstance(selector, QComboBox)
            original_index = selector.currentIndex()
            if selector.count() > 1:
                selector.setCurrentIndex((original_index + 1) % selector.count())
                app.processEvents()
                selector.setCurrentIndex(original_index)
                app.processEvents()

        buttons_to_click = [
            window.generate_button,
            window.confirm_yes_button,
            window.confirm_no_button,
            window.example_button,
            window.trace_button,
            window.refresh_button,
            window.open_report_button,
            window.export_data_button,
            window.report_dir_button,
            window.live_visual_toggle_button,
            window.reset_view_button,
            window.fit_view_button,
            window.refresh_runs_button,
            window.restore_run_button,
            window.screen_button,
            window.evaluate_selected_button,
            window.evaluate_all_button,
            window.report_button,
            window.reset_button,
            window.settings_save_button,
            window.settings_reload_button,
            window.knowledge_widget.search_button,
            window.knowledge_widget.upload_button,
            window.knowledge_widget.batch_button,
            window.knowledge_widget.rebuild_button,
            window.knowledge_widget.export_snapshot_button,
            window.knowledge_widget.refresh_button,
            window.knowledge_widget.graph_reset_button,
            window.knowledge_widget.graph_zoom_in_button,
            window.knowledge_widget.graph_zoom_out_button,
            window.knowledge_widget.graph_label_button,
            window.knowledge_widget.graph_relation_button,
            window.knowledge_right_rebuild_button,
            window.knowledge_right_snapshot_button,
        ]
        for button in buttons_to_click:
            button.setEnabled(True)
            button.click()
            app.processEvents()

        expected_calls = {
            "start",
            "confirm",
            "example",
            "refresh_knowledge",
            "open_report",
            "export_data",
            "report_dir",
            "refresh_runs",
            "restore_run",
            "screen",
            "evaluate_selected",
            "evaluate_all",
            "report",
            "reset_session",
            "settings_save",
            "settings_reload",
            "knowledge_search",
            "knowledge_upload",
            "knowledge_batch",
            "knowledge_maintenance",
        }
        assert expected_calls.issubset({name for name, _arg in calls})
        assert ("knowledge_maintenance", "rebuild") in calls
        assert ("knowledge_maintenance", "export") in calls
        assert window.stack.currentIndex() == 2
    finally:
        window.close()
        app.processEvents()


def test_workbench_input_actions_share_one_compact_row(monkeypatch) -> None:
    monkeypatch.setenv("CSDM_cph_DISABLE_LLM_AUTO", "1")
    app = _app()
    window = MainWindow()
    try:
        window.resize(1280, 960)
        window.show()
        app.processEvents()

        widgets = [
            window.input_line,
            window.generate_button,
            window.confirm_yes_button,
            window.confirm_no_button,
        ]
        centers = [widget.mapTo(window, widget.rect().center()).y() for widget in widgets]
        assert max(centers) - min(centers) <= 2
        assert window.input_line.width() > window.generate_button.width() * 4
        assert abs(window.confirm_yes_button.y() - window.generate_button.y()) <= 2
        assert abs(window.confirm_no_button.y() - window.generate_button.y()) <= 2
    finally:
        window.close()
        app.processEvents()


def test_shell_pages_keep_major_regions_inside_window_across_themes(monkeypatch) -> None:
    monkeypatch.setenv("CSDM_cph_DISABLE_LLM_AUTO", "1")
    app = _app()
    window = MainWindow()

    def assert_inside_window(widget) -> None:
        window_rect = window.rect().adjusted(-2, -2, 2, 2)
        top_left = widget.mapTo(window, widget.rect().topLeft())
        bottom_right = widget.mapTo(window, widget.rect().bottomRight())
        assert widget.width() > 0
        assert widget.height() > 0
        assert window_rect.contains(top_left), (widget.objectName(), top_left, window_rect)
        assert window_rect.contains(bottom_right), (widget.objectName(), bottom_right, window_rect)

    try:
        window.resize(1280, 960)
        window.show()
        app.processEvents()

        for theme in ["dark", "light"]:
            window.locale.set_theme(theme)
            window._apply_styles()
            for index in range(len(window.nav_buttons)):
                window._switch_workspace_page(index)
                app.processEvents()

                assert_inside_window(window.main_splitter)
                assert_inside_window(window.left_stack)
                assert_inside_window(window.stack)
                assert_inside_window(window.right_stack)
                assert_inside_window(window.model_status_label)
    finally:
        window.close()
        app.processEvents()


def test_flow_dag_knowledge_node_has_even_spacing_and_stays_inside_panel() -> None:
    app = _app()
    widget = FlowDagWidget()
    try:
        widget.resize(960, 218)
        widget.show()
        app.processEvents()

        geometry = widget.layout_rects(960, 218)
        outer = geometry["outer"]
        knowledge = geometry["knowledge_rect"]
        node_rects = geometry["node_rects"]

        assert outer.contains(knowledge)
        assert knowledge.height() >= 50
        assert knowledge.top() - node_rects[1].bottom() >= 12
        assert outer.bottom() - knowledge.bottom() >= 12
        assert knowledge.width() >= 220
        assert knowledge.width() <= 280
        assert abs(float(geometry["branch_x"]) - knowledge.center().x()) <= 1.0
        for previous, current in zip(node_rects, node_rects[1:]):
            assert previous.right() < current.left()
    finally:
        widget.close()
        app.processEvents()


def test_chat_short_messages_do_not_expand_to_panel_width() -> None:
    app = _app()
    widget = ChatWidget()
    try:
        widget.resize(1000, 420)
        widget.add_message("USER", "外压 30 MPa，生成 12 个候选。")
        widget.add_message("ORCHESTRATOR", "已解析任务。")
        widget.show()
        app.processEvents()

        bubbles = [item for item in widget.findChildren(QFrame) if item.objectName() == "chatBubble"]
        widths = sorted(bubble.width() for bubble in bubbles)
        assert len(widths) == 2
        assert widths[0] <= 260
        assert widths[1] <= 420
    finally:
        widget.close()
        app.processEvents()


def test_chat_bubble_width_tracks_rendered_text_width() -> None:
    app = _app()
    widget = ChatWidget()
    try:
        widget.resize(1120, 420)
        widget.show()
        app.processEvents()

        text = "请为复合材料外压圆柱耐压壳设计方案，外压 30 MPa，生成 12 个候选。"
        target_max, target_min = widget._responsive_width(920, 220)
        rendered_width = widget._text_metrics(13).horizontalAdvance(text)
        raw_width = rendered_width + 18
        expected_width = target_max if raw_width >= target_max else max(target_min, raw_width)

        assert widget._content_width(text, target_max, target_min) == expected_width
    finally:
        widget.close()
        app.processEvents()


def test_chat_short_runtime_bubbles_follow_text_width() -> None:
    app = _app()
    widget = ChatWidget()
    try:
        widget.resize(1120, 420)
        widget.show()
        app.processEvents()

        messages = [
            ("USER", "继续"),
            ("USER", "跳过/暂停"),
            ("ORCHESTRATOR", "start FEM TMP_11 -> C16"),
            ("FEM_AGENT", "C16 first ABAQUS solve"),
        ]
        for sender, message in messages:
            widget.add_message(sender, message)
            app.processEvents()

        bubbles = [item for item in widget.findChildren(QFrame) if item.objectName() == "chatBubble"]
        assert len(bubbles) == len(messages)
        for bubble, (_, message) in zip(bubbles, messages):
            text_width = widget._text_metrics(13).horizontalAdvance(message)
            assert bubble.width() - text_width <= 20
            assert bubble.width() <= 360
    finally:
        widget.close()
        app.processEvents()


def test_chat_dynamic_messages_scroll_to_latest_with_bottom_spacer() -> None:
    app = _app()
    widget = ChatWidget()
    try:
        widget.resize(980, 260)
        widget.show()
        app.processEvents()

        for index in range(12):
            widget.add_message("ORCHESTRATOR", f"第 {index + 1} 条运行事件：候选生成、代理初筛和状态更新。")
            app.processEvents()

        layout = widget.content_layout
        assert layout.count() == 13
        for index in range(12):
            assert layout.itemAt(index).widget() is not None
        assert layout.itemAt(layout.count() - 1).widget() is None
        assert widget.scroll_area.verticalScrollBar().value() == widget.scroll_area.verticalScrollBar().maximum()
    finally:
        widget.close()
        app.processEvents()


def test_light_theme_uses_light_log_and_sidebar_surfaces() -> None:
    stylesheet = application_stylesheet("Microsoft YaHei UI", "light")

    assert "background: #ffffff;" in stylesheet
    assert "color: #334155;" in stylesheet
    assert "background: #0b1220;" not in stylesheet
    assert "background: #141f31;" not in stylesheet
    assert "ui_workbench_light.png" not in (open("README.md", encoding="utf-8").read())


def test_agent_status_card_aligns_dot_and_labels_without_rich_text_blocks() -> None:
    app = _app()
    card = AgentStatusCard()
    try:
        card.resize(260, 72)
        card.set_theme("dark")
        card.set_content("ORCHESTRATOR", "active", "运行中", "任务编排与人工确认")
        card.show()
        app.processEvents()

        assert card.dot.width() == card.dot.height() == 9
        assert abs(card.dot.geometry().center().y() - card.title.geometry().center().y()) <= 5
        assert "background:transparent" in card.detail.styleSheet()
        assert card.title.text() == "ORCHESTRATOR"
    finally:
        card.close()
        app.processEvents()


def test_settings_page_exposes_editable_runtime_configuration(monkeypatch) -> None:
    monkeypatch.setenv("CSDM_cph_DISABLE_LLM_AUTO", "1")
    app = _app()
    window = MainWindow()
    try:
        window.resize(1280, 960)
        window.show()
        window._switch_workspace_page(3)
        app.processEvents()

        assert "llm.primary.model" in window.settings_fields
        assert "abaqus.command" in window.settings_fields
        assert "knowledge.chunk_token_size" in window.settings_fields
        assert "primary" in window.settings_health_labels
        assert "fallback" in window.settings_health_labels
        assert "knowledge" in window.settings_health_labels
        assert isinstance(window.settings_fields["llm.primary.model"], QLineEdit)
        assert "csllm" in window.settings_health_labels["primary"].text()
        assert window.settings_save_button.isVisible() is True
        assert window.settings_reload_button.isVisible() is True
        assert window.settings_status_label.text()
    finally:
        window.close()
        app.processEvents()


def test_settings_page_persists_editable_runtime_configuration(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("CSDM_cph_DISABLE_LLM_AUTO", "1")
    app_config = {
        "abaqus": {
            "command": "abaqus",
            "user_subroutine": "",
            "use_user_subroutine": False,
            "job_timeout_seconds": 3600,
            "max_retries": 3,
            "poll_interval_seconds": 5,
        },
        "pipeline": {
            "candidate_source_ratio": {"llm": 2, "case_transfer": 1, "doe": 1},
            "random_seed": 42,
        },
        "project_knowledge": {
            "top_k": 5,
            "kg_top_k": 8,
            "chunk_token_size": 512,
            "chunk_overlap_tokens": 64,
            "min_chunk_tokens": 80,
            "vector_enabled": True,
            "vector_collection_name": "csdm_cph_project_knowledge",
        },
        "conversation": {"confirmation_steps": ["screening", "fem"]},
    }
    llm_config = {
        "backends": [
            {
                "name": "domain_finetuned_primary",
                "model": "csllm",
                "base_url_env": "LLM_PRIMARY_URL",
                "model_env": "LLM_PRIMARY_MODEL_NAME",
                "temperature": 0.2,
                "max_tokens": 1800,
                "timeout_seconds": 180,
            },
            {
                "name": "fallback_openai_compatible",
                "base_url_env": "URL",
                "model_env": "MODEL_NAME",
                "temperature": 0.2,
                "max_tokens": 1800,
                "timeout_seconds": 180,
            },
        ]
    }
    monkeypatch.setattr(main_window_module, "CONFIG_DIR", tmp_path)
    monkeypatch.setattr(main_window_module, "load_app_config", _config_loader(app_config))
    monkeypatch.setattr(main_window_module, "load_llm_config", _config_loader(llm_config))
    app = _app()
    window = MainWindow()
    try:
        assert "csllm" in window.settings_health_labels["primary"].text()
        assert "API_KEY" not in window.settings_health_labels["fallback"].text()
        window.settings_fields["llm.primary.model"].setText("csllm-check")
        window.settings_fields["abaqus.command"].setText("D:/Abaqus/Commands/abaqus.bat")
        window.settings_fields["pipeline.ratio.llm"].setText("3")
        window.settings_fields["pipeline.ratio.case_transfer"].setText("2")
        window.settings_fields["pipeline.ratio.doe"].setText("1")
        window.settings_fields["knowledge.chunk_token_size"].setText("256")
        window.settings_fields["knowledge.chunk_overlap_tokens"].setText("32")
        window.settings_fields["knowledge.min_chunk_tokens"].setText("64")

        window.settings_save_button.click()

        saved_app = yaml.safe_load((tmp_path / "app_config.yaml").read_text(encoding="utf-8"))
        saved_llm = yaml.safe_load((tmp_path / "llm_config.yaml").read_text(encoding="utf-8"))
        assert saved_app["abaqus"]["command"] == "D:/Abaqus/Commands/abaqus.bat"
        assert saved_app["pipeline"]["candidate_source_ratio"] == {"llm": 3, "case_transfer": 2, "doe": 1}
        assert saved_app["project_knowledge"]["chunk_token_size"] == 256
        assert saved_app["project_knowledge"]["chunk_overlap_tokens"] == 32
        assert saved_app["project_knowledge"]["min_chunk_tokens"] == 64
        assert saved_llm["backends"][0]["model"] == "csllm-check"
        assert window.settings_status_label.text()

        window.settings_fields["llm.primary.model"].setText("temporary")
        window.settings_reload_button.click()
        assert window.settings_fields["llm.primary.model"].text() == "csllm"
    finally:
        window.close()
        app.processEvents()

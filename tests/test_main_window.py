from __future__ import annotations

import copy
import csv
import json
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import yaml
from PyQt6.QtGui import QFont, QFontMetrics
from PyQt6.QtWidgets import QApplication, QFrame, QLabel, QLineEdit, QPushButton

import gui.main_window as main_window_module
from core.task_parser import TaskParser
from gui.chat_widget import ChatWidget
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


def test_main_window_routes_runtime_events_to_logs_without_chat_noise(monkeypatch) -> None:
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
        expected_width = min(target_max, max(target_min, rendered_width + 28))

        assert widget._content_width(text, target_max, target_min) == expected_width
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

        window._save_settings_from_page()

        saved_app = yaml.safe_load((tmp_path / "app_config.yaml").read_text(encoding="utf-8"))
        saved_llm = yaml.safe_load((tmp_path / "llm_config.yaml").read_text(encoding="utf-8"))
        assert saved_app["abaqus"]["command"] == "D:/Abaqus/Commands/abaqus.bat"
        assert saved_app["pipeline"]["candidate_source_ratio"] == {"llm": 3, "case_transfer": 2, "doe": 1}
        assert saved_app["project_knowledge"]["chunk_token_size"] == 256
        assert saved_app["project_knowledge"]["chunk_overlap_tokens"] == 32
        assert saved_app["project_knowledge"]["min_chunk_tokens"] == 64
        assert saved_llm["backends"][0]["model"] == "csllm-check"
        assert window.settings_status_label.text()
    finally:
        window.close()
        app.processEvents()

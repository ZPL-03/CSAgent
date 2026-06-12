from __future__ import annotations

import csv
import json
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtGui import QFont, QFontMetrics
from PyQt6.QtWidgets import QApplication, QFrame, QLabel, QPushButton

from core.task_parser import TaskParser
from gui.chat_widget import ChatWidget
from gui.main_window import MainWindow
from gui.theme import application_stylesheet
from gui.workbench_widgets import AgentStatusCard
from gui.workbench_widgets import FlowDagWidget
from gui.workbench_widgets import StatusPill
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


def test_main_window_marks_failed_stage_and_agent(monkeypatch) -> None:
    monkeypatch.setenv("CSDM_cph_DISABLE_LLM_AUTO", "1")
    app = _app()
    window = MainWindow()
    try:
        window.session.stage = "screen_candidates_failed"
        assert window._agent_state_map()["SCREENER"] == "failed"
        assert window._agent_status_label("failed") == "失败"

        window._handle_failed("worker error")

        assert window.session.stage == "failed"
        assert window.session.pending_confirmation is None
        assert window._agent_state_map()["ORCHESTRATOR"] == "failed"
        assert "worker error" in window.status_label.text()
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


def test_main_window_updates_model_pill_for_primary_llm_trace(monkeypatch) -> None:
    monkeypatch.setenv("CSDM_cph_DISABLE_LLM_AUTO", "1")
    app = _app()
    window = MainWindow()
    try:
        event = {
            "event_type": "llm_call_trace",
            "payload": {
                "selected_backend": "domain_finetuned_primary",
                "selected_model": "csllm",
                "fallback_used": False,
                "trace": [{"backend": "domain_finetuned_primary", "status": "success"}],
            },
        }

        window._handle_message("CANDIDATE_GEN", "LLM call completed", event)

        assert window.model_status_label.status == "success"
        assert "csllm" in window.model_status_label.text
        assert "csllm" in window.log_widget.toPlainText()
        assert window.last_llm_trace_payload["selected_backend"] == "domain_finetuned_primary"
    finally:
        window.close()
        app.processEvents()


def test_main_window_updates_model_pill_for_fallback_llm_trace(monkeypatch) -> None:
    monkeypatch.setenv("CSDM_cph_DISABLE_LLM_AUTO", "1")
    app = _app()
    window = MainWindow()
    try:
        event = {
            "event_type": "llm_call_trace",
            "payload": {
                "selected_backend": "configured_fallback",
                "selected_model": "deepseek-v4-pro",
                "fallback_used": True,
                "trace": [
                    {"backend": "domain_finetuned_primary", "status": "failed"},
                    {"backend": "configured_fallback", "status": "success"},
                ],
            },
        }

        window._handle_message("CANDIDATE_GEN", "LLM call completed", event)

        assert window.model_status_label.status == "warning"
        assert "deepseek-v4-pro" in window.model_status_label.text
        assert "configured_fallback" in window.log_widget.toPlainText()
        assert window.last_llm_trace_payload["fallback_used"] is True
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
        assert window.flow_dag_widget.stage_text == "运行中 · parse_task"

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
        window.resize(1680, 980)
        window.main_splitter.setSizes([270, 1040, 370])
        window.workbench_splitter.setSizes([190, 760])
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
        assert not window.reset_view_button.icon().isNull()
        assert not window.fit_view_button.icon().isNull()
        assert window.reset_view_button.toolTip()
        assert window.fit_view_button.toolTip()
        assert "#e5edf7" in window.stage_card.text()
        assert window.queue_progress.isVisible() is False

        left_width, center_width, right_width = window.main_splitter.sizes()
        assert 240 <= left_width <= 310
        assert center_width >= 900
        assert 320 <= right_width <= 430

        dag_height, chat_height = window.workbench_splitter.sizes()
        assert 160 <= dag_height <= 230
        assert chat_height >= 520
        chat_bubbles = [item for item in window.chat_widget.findChildren(QFrame) if item.objectName() == "chatBubble"]
        widths = [bubble.width() for bubble in chat_bubbles]
        assert max(widths) <= int(window.chat_widget.width() * 0.82)
        assert len(set(widths)) > 1

        for index, button in enumerate(window.nav_buttons):
            window._switch_workspace_page(index)
            app.processEvents()
            assert button.isChecked() is True
            assert window.stack.currentIndex() == index
            assert window.left_stack.currentIndex() == index
            assert window.right_stack.currentIndex() == index
            assert window.stack.currentWidget().width() > 0
            assert window.left_stack.currentWidget().width() > 0
            assert window.right_stack.currentWidget().width() > 0
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
    names = [node.name for node in FlowDagWidget.MAIN_NODES]
    assert names == ["ORCHESTRATOR", "CANDIDATE_GEN", "SCREENER", "FEM_AGENT", "REPORT_GEN"]
    assert FlowDagWidget.MAIN_NODES[0].subtitle == "需求解析 / 编排"
    assert FlowDagWidget.KNOWLEDGE_NODE.agent == "KNOWLEDGE_AGENT"


def test_visible_workbench_buttons_keep_text_inside_layout(monkeypatch) -> None:
    monkeypatch.setenv("CSDM_cph_DISABLE_LLM_AUTO", "1")
    app = _app()
    window = MainWindow()
    try:
        window.resize(1680, 980)
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


def test_chat_empty_state_uses_adaptive_engineering_message_cards() -> None:
    app = _app()
    widget = ChatWidget()
    try:
        widget.resize(1120, 520)
        widget.set_empty_text("输入设计需求后，系统展示实时协作过程。")
        widget.set_empty_state(
            title="对话 · 等待设计任务",
            user_prompt="请为复合材料外压圆柱耐压壳设计方案，外压 30 MPa，极限压力不低于 35 MPa，生成 12 个候选，初筛保留 5 个候选",
            agent_title="ORCHESTRATOR",
            agent_body="收到任务后，系统会抽取用户已给事实，构建候选池和初筛目标，并在代理初筛、有限元校核、报告导出前请求人工确认。",
            tool_title="工具调用 · abaqus_solver",
            tool_body="有限元阶段会显示正式 C 编号、作业状态、线性屈曲、Static Riks 后屈曲、云图路径和诊断摘要。",
            evidence_a="RAG/KG 证据",
            evidence_b="候选来源审计",
        )
        widget.show()
        app.processEvents()

        bubbles = [item for item in widget.findChildren(QFrame) if item.objectName() == "chatBubble"]
        assert len(bubbles) >= 3
        widths = [bubble.width() for bubble in bubbles]
        assert max(widths) <= int(widget.width() * 0.72)
        assert min(widths) >= 220
        assert len(set(widths)) > 1
        assert any(label.text() == "U" for label in widget.findChildren(QLabel))
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
        assert widths[0] <= 240
        assert widths[1] <= 360
    finally:
        widget.close()
        app.processEvents()


def test_light_theme_uses_light_log_and_sidebar_surfaces() -> None:
    stylesheet = application_stylesheet("Microsoft YaHei UI", "light")

    assert 'background: #ffffff;' in stylesheet
    assert 'color: #334155;' in stylesheet
    assert 'background: #0b1220;' not in stylesheet
    assert 'background: #141f31;' not in stylesheet
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

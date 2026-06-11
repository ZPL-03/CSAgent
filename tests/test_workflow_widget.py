import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication

from gui.workflow_widget import WorkflowWidget
from workflow.event_store import WorkflowEventStore
from workflow.events import WorkflowEvent


def _app() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_workflow_widget_renders_runtime_events(tmp_path) -> None:
    app = _app()
    store = WorkflowEventStore(tmp_path / "workflow.sqlite3")
    store.create_run("RUN_TEST", "生成 2 个候选，初筛保留 1 个候选")
    store.append_event(
        WorkflowEvent(
            run_id="RUN_TEST",
            event_type="node_completed",
            agent="parse_task",
            message="节点完成：parse_task",
            stage="parse_task",
        )
    )
    store.append_event(
        WorkflowEvent(
            run_id="RUN_TEST",
            event_type="tool_completed",
            agent="RequirementAgent",
            message="工具 parse_task 调用完成",
            stage="parse_task",
        )
    )

    widget = WorkflowWidget(event_store=store)
    try:
        widget.refresh("RUN_TEST", "awaiting_screen_confirmation", "screen_candidates")
        html = widget.browser.toHtml()

        assert "智能体流程" in html
        assert "RUN_TEST" in html
        assert "任务解析" in html
        assert "完成" in html
        assert "screen_candidates" in html
        assert "工具 parse_task 调用完成" in html
    finally:
        widget.close()
        app.processEvents()

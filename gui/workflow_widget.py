"""多智能体工作流状态视图。"""

from __future__ import annotations

from PyQt6.QtWidgets import QTextBrowser, QVBoxLayout, QWidget

from workflow.event_store import WorkflowEventStore


class WorkflowWidget(QWidget):
    """展示工作流节点、人工确认点和事件审计。"""

    NODE_LABELS = [
        ("parse_task", "任务解析"),
        ("generate_candidates", "候选生成"),
        ("wait_screen", "初筛确认"),
        ("screen_candidates", "代理初筛"),
        ("wait_fem", "有限元确认"),
        ("evaluate_candidates", "有限元校核"),
        ("wait_report", "报告确认"),
        ("generate_report", "报告生成"),
    ]

    def __init__(self, event_store: WorkflowEventStore | None = None) -> None:
        super().__init__()
        self.event_store = event_store or WorkflowEventStore()
        self.browser = QTextBrowser()
        layout = QVBoxLayout()
        layout.addWidget(self.browser)
        self.setLayout(layout)
        self.reset_view()

    def reset_view(self) -> None:
        self.browser.setHtml(
            "<h3>智能体流程</h3>"
            "<p>启动对话式设计后，这里会显示 LangGraph 工作流节点、人工确认点和工具调用事件。</p>"
        )

    def refresh(self, workflow_run_id: str | None, stage: str = "", pending_confirmation: str | None = None) -> None:
        if not workflow_run_id:
            self.reset_view()
            return
        try:
            events = self.event_store.list_events(workflow_run_id)
        except Exception as exc:
            self.browser.setHtml(f"<h3>智能体流程</h3><p>读取工作流事件失败：{exc}</p>")
            return

        completed_nodes = {
            event["agent"]
            for event in events
            if event.get("event_type") == "node_completed"
        }
        failed_nodes = {
            event["agent"]
            for event in events
            if event.get("event_type") == "node_failed"
        }
        active_stage = stage or "-"
        pending_text = pending_confirmation or "-"

        node_rows = []
        for node_name, label in self.NODE_LABELS:
            if node_name in failed_nodes:
                status = "失败"
            elif node_name in completed_nodes:
                status = "完成"
            elif active_stage == node_name or active_stage.startswith(node_name):
                status = "当前"
            else:
                status = "等待"
            node_rows.append(f"<tr><td>{label}</td><td><code>{node_name}</code></td><td>{status}</td></tr>")

        event_items = []
        for event in events[-80:]:
            created_at = event.get("created_at", "")
            agent = event.get("agent", "")
            event_type = event.get("event_type", "")
            message = event.get("message", "")
            event_items.append(
                f"<li><code>{created_at}</code> [{agent}] <b>{event_type}</b>：{message}</li>"
            )

        self.browser.setHtml(
            "<h3>智能体流程</h3>"
            f"<p><b>运行编号：</b><code>{workflow_run_id}</code></p>"
            f"<p><b>当前阶段：</b>{active_stage}　<b>等待确认：</b>{pending_text}</p>"
            "<h4>节点状态</h4>"
            "<table border='1' cellspacing='0' cellpadding='6'>"
            "<tr><th>智能体节点</th><th>节点键</th><th>状态</th></tr>"
            + "".join(node_rows)
            + "</table>"
            "<h4>事件审计</h4>"
            "<ol>"
            + "".join(event_items)
            + "</ol>"
        )

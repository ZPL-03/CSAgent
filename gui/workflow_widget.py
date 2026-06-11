"""多智能体工作流状态视图。"""

from __future__ import annotations

from PyQt6.QtWidgets import QTextBrowser, QVBoxLayout, QWidget

from core.llm_status import configured_llm_backends
from workflow.event_store import WorkflowEventStore
from workflow.simulation_queue import SimulationJobQueue


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

    def __init__(
        self,
        event_store: WorkflowEventStore | None = None,
        simulation_queue: SimulationJobQueue | None = None,
    ) -> None:
        super().__init__()
        self.event_store = event_store or WorkflowEventStore()
        self.simulation_queue = simulation_queue or SimulationJobQueue(self.event_store.db_path)
        self.browser = QTextBrowser()
        layout = QVBoxLayout()
        layout.addWidget(self.browser)
        self.setLayout(layout)
        self.reset_view()

    def reset_view(self) -> None:
        self.browser.setHtml(
            "<h3>智能体流程</h3>"
            "<p>启动对话式设计后，这里会显示 LangGraph 工作流节点、人工确认点和工具调用事件。</p>"
            + self._llm_status_html()
        )

    def _llm_status_html(self) -> str:
        rows = []
        for backend in configured_llm_backends():
            rows.append(
                "<tr>"
                f"<td>{backend['role']}</td>"
                f"<td>{backend['name']}</td>"
                f"<td>{backend['model']}</td>"
                f"<td>{'是' if backend['base_url_configured'] else '否'}</td>"
                f"<td>{'是' if backend['api_key_configured'] else '否'}</td>"
                f"<td>{'可调用' if backend['available_for_call'] else '不可调用'}</td>"
                "</tr>"
            )
        return (
            "<h4>LLM 后端</h4>"
            "<table border='1' cellspacing='0' cellpadding='6'>"
            "<tr><th>角色</th><th>后端</th><th>模型</th><th>URL</th><th>密钥</th><th>状态</th></tr>"
            + "".join(rows)
            + "</table>"
        )

    def refresh(self, workflow_run_id: str | None, stage: str = "", pending_confirmation: str | None = None) -> None:
        if not workflow_run_id:
            self.reset_view()
            return
        try:
            events = self.event_store.list_events(workflow_run_id)
            jobs = self.simulation_queue.list_jobs(workflow_run_id)
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

        llm_rows = []
        for event in events:
            if event.get("event_type") != "llm_call_trace":
                continue
            payload = event.get("payload") or {}
            context = payload.get("context") or {}
            trace = payload.get("trace") or []
            attempts = []
            for item in trace:
                attempts.append(
                    f"{item.get('backend')} / {item.get('model')} / {item.get('status')}"
                )
            llm_rows.append(
                "<tr>"
                f"<td>{context.get('purpose') or '-'}</td>"
                f"<td>{payload.get('selected_backend') or '-'}</td>"
                f"<td>{payload.get('selected_model') or '-'}</td>"
                f"<td>{'是' if payload.get('fallback_used') else '否'}</td>"
                f"<td>{'<br/>'.join(attempts) if attempts else '-'}</td>"
                "</tr>"
            )
        llm_trace_html = (
            "<p>当前运行还没有 LLM 调用轨迹。</p>"
            if not llm_rows
            else (
                "<table border='1' cellspacing='0' cellpadding='6'>"
                "<tr><th>用途</th><th>选用后端</th><th>选用模型</th><th>使用回退</th><th>尝试链路</th></tr>"
                + "".join(llm_rows)
                + "</table>"
            )
        )

        job_rows = []
        for job in jobs:
            result = job.get("result") or {}
            ultimate = result.get("ultimate_pressure_MPa")
            ultimate_text = "-" if ultimate is None else str(ultimate)
            error = job.get("error_message") or "-"
            job_rows.append(
                "<tr>"
                f"<td><code>{job.get('job_id')}</code></td>"
                f"<td>{job.get('session_candidate_id') or '-'}</td>"
                f"<td>{job.get('formal_candidate_id') or '-'}</td>"
                f"<td>{job.get('status') or '-'}</td>"
                f"<td>{ultimate_text}</td>"
                f"<td>{error}</td>"
                "</tr>"
            )
        jobs_html = (
            "<p>当前运行还没有有限元作业。</p>"
            if not job_rows
            else (
                "<table border='1' cellspacing='0' cellpadding='6'>"
                "<tr><th>作业编号</th><th>会话候选</th><th>正式候选</th><th>状态</th><th>极限压力 MPa</th><th>错误</th></tr>"
                + "".join(job_rows)
                + "</table>"
            )
        )

        self.browser.setHtml(
            "<h3>智能体流程</h3>"
            f"<p><b>运行编号：</b><code>{workflow_run_id}</code></p>"
            f"<p><b>当前阶段：</b>{active_stage}　<b>等待确认：</b>{pending_text}</p>"
            + self._llm_status_html()
            + "<h4>节点状态</h4>"
            + "<table border='1' cellspacing='0' cellpadding='6'>"
            "<tr><th>智能体节点</th><th>节点键</th><th>状态</th></tr>"
            + "".join(node_rows)
            + "</table>"
            + "<h4>有限元队列</h4>"
            + jobs_html
            + "<h4>LLM 调用轨迹</h4>"
            + llm_trace_html
            + "<h4>事件审计</h4>"
            + "<ol>"
            + "".join(event_items)
            + "</ol>"
        )

"""多智能体工作流状态视图。"""

from __future__ import annotations

from html import escape
from typing import Any

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

    NODE_ARTIFACT_LABELS = {
        "parse_task": "任务契约",
        "generate_candidates": "候选池",
        "wait_screen": "人工确认",
        "screen_candidates": "代理初筛",
        "wait_fem": "人工确认",
        "evaluate_candidates": "有限元作业",
        "wait_report": "人工确认",
        "generate_report": "报告文件",
    }

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

    def _safe(self, value: Any) -> str:
        if value is None or value == "":
            return "-"
        return escape(str(value))

    def _load_snapshot(self, workflow_run_id: str) -> tuple[dict[str, Any], str]:
        try:
            return self.event_store.load_snapshot(workflow_run_id), ""
        except Exception as exc:
            return {}, str(exc)

    def _source_text(self, snapshot: dict[str, Any]) -> str:
        counter = dict(snapshot.get("source_counter") or {})
        if not counter:
            for candidate in snapshot.get("candidates") or []:
                source = str(candidate.get("source") or "UNKNOWN")
                counter[source] = counter.get(source, 0) + 1
        if not counter:
            return "-"
        return " / ".join(f"{self._safe(key)}={self._safe(value)}" for key, value in sorted(counter.items()))

    def _task_label(self, snapshot: dict[str, Any]) -> str:
        task = snapshot.get("task") or {}
        application = task.get("application") or "复合材料外压圆柱耐压壳"
        load = task.get("load_conditions") or {}
        pressure = load.get("external_pressure_MPa")
        target = (task.get("design_targets") or {}).get("ultimate_pressure_min_MPa")
        parts = [str(application)]
        if pressure is not None:
            parts.append(f"外压 {pressure} MPa")
        if target is not None:
            parts.append(f"极限压力目标 {target} MPa")
        return " | ".join(parts)

    def _snapshot_summary_html(
        self,
        workflow_run_id: str,
        snapshot: dict[str, Any],
        active_stage: str,
        pending_text: str,
        snapshot_error: str,
    ) -> str:
        report = snapshot.get("report") or {}
        results = snapshot.get("results") or []
        passed = sum(1 for result in results if str(result.get("verdict") or "").strip() in {"通过", "PASS", "pass"})
        rows = [
            ("运行编号", f"<code>{self._safe(workflow_run_id)}</code>"),
            ("当前阶段", self._safe(active_stage)),
            ("等待确认", self._safe(pending_text)),
            ("任务摘要", self._safe(self._task_label(snapshot))),
            ("候选总数", self._safe(len(snapshot.get("candidates") or []))),
            ("候选来源", self._source_text(snapshot)),
            ("初筛保留", self._safe(len(snapshot.get("screened_candidates") or []))),
            ("有限元结果", self._safe(len(results))),
            ("有限元通过", self._safe(passed)),
            ("报告 Markdown", self._safe(report.get("markdown_path"))),
            ("快照状态", self._safe(snapshot.get("stage") or ("读取失败" if snapshot_error else "-"))),
        ]
        if snapshot_error:
            rows.append(("快照诊断", self._safe(snapshot_error)))
        return (
            "<h4>运行摘要</h4>"
            "<table border='1' cellspacing='0' cellpadding='6'>"
            + "".join(f"<tr><th>{label}</th><td>{value}</td></tr>" for label, value in rows)
            + "</table>"
        )

    def _event_status_maps(self, events: list[dict[str, Any]]) -> tuple[dict[str, str], dict[str, str]]:
        status_by_node: dict[str, str] = {}
        latest_message_by_node: dict[str, str] = {}
        for event in events:
            event_type = event.get("event_type")
            agent = str(event.get("agent") or "")
            if event_type == "node_started":
                status_by_node[agent] = "运行中"
            elif event_type == "node_completed":
                status_by_node[agent] = "完成"
            elif event_type == "node_failed":
                status_by_node[agent] = "失败"
            if event_type in {"node_started", "node_completed", "node_failed"}:
                latest_message_by_node[agent] = str(event.get("message") or "")
        return status_by_node, latest_message_by_node

    def _node_artifact(self, node_name: str, snapshot: dict[str, Any], jobs: list[dict[str, Any]]) -> str:
        if node_name == "parse_task":
            task = snapshot.get("task") or {}
            return f"task_id={task.get('task_id') or '-'}"
        if node_name == "generate_candidates":
            return f"候选={len(snapshot.get('candidates') or [])}；来源={self._source_text(snapshot)}"
        if node_name == "wait_screen":
            return "等待代理初筛确认"
        if node_name == "screen_candidates":
            return f"初筛={len(snapshot.get('screened_candidates') or [])}"
        if node_name == "wait_fem":
            return "等待有限元校核确认"
        if node_name == "evaluate_candidates":
            return f"作业={len(jobs)}；结果={len(snapshot.get('results') or [])}"
        if node_name == "wait_report":
            return "等待报告输出确认"
        if node_name == "generate_report":
            report = snapshot.get("report") or {}
            return report.get("markdown_path") or "-"
        return "-"

    def _workflow_graph_html(
        self,
        events: list[dict[str, Any]],
        jobs: list[dict[str, Any]],
        snapshot: dict[str, Any],
        active_stage: str,
    ) -> str:
        status_by_node, latest_message_by_node = self._event_status_maps(events)
        rows = []
        for index, (node_name, label) in enumerate(self.NODE_LABELS, start=1):
            status = status_by_node.get(node_name, "等待")
            if status == "等待" and (active_stage == node_name or active_stage.startswith(node_name)):
                status = "当前"
            rows.append(
                "<tr>"
                f"<td>{index}</td>"
                f"<td>{self._safe(label)}<br><code>{self._safe(node_name)}</code></td>"
                f"<td>{self._safe(status)}</td>"
                f"<td>{self._safe(self.NODE_ARTIFACT_LABELS.get(node_name, '-'))}</td>"
                f"<td>{self._safe(self._node_artifact(node_name, snapshot, jobs))}</td>"
                f"<td>{self._safe(latest_message_by_node.get(node_name))}</td>"
                "</tr>"
            )
        return (
            "<h4>状态图</h4>"
            "<table border='1' cellspacing='0' cellpadding='6'>"
            "<tr><th>序号</th><th>智能体节点</th><th>状态</th><th>产物类型</th><th>当前产物</th><th>最近节点事件</th></tr>"
            + "".join(rows)
            + "</table>"
        )

    def _diagnostics_html(
        self,
        events: list[dict[str, Any]],
        jobs: list[dict[str, Any]],
        snapshot: dict[str, Any],
        snapshot_error: str,
    ) -> str:
        items: list[str] = []
        if snapshot_error:
            items.append(f"快照读取失败：{snapshot_error}")
        if snapshot.get("error"):
            items.append(f"当前状态错误：{snapshot.get('error')}")
        for event in events:
            if event.get("event_type") in {"node_failed", "tool_failed", "simulation_job_failed"}:
                items.append(str(event.get("message") or ""))
        for job in jobs:
            if str(job.get("status") or "") == "failed":
                items.append(f"有限元作业失败：{job.get('job_id')}，{job.get('error_message') or '-'}")
        for event in events:
            if event.get("event_type") != "llm_call_trace":
                continue
            payload = event.get("payload") or {}
            trace = payload.get("trace") or []
            if payload.get("fallback_used"):
                items.append(
                    f"LLM 已使用回退后端：{payload.get('selected_backend')} / {payload.get('selected_model')}"
                )
            elif trace and not any(item.get("status") == "success" for item in trace):
                purpose = (payload.get("context") or {}).get("purpose") or "-"
                items.append(f"LLM 调用未成功：{purpose}")
        if not items:
            return "<h4>诊断</h4><p>当前未记录阻断性诊断。</p>"
        return (
            "<h4>诊断</h4><ul>"
            + "".join(f"<li>{self._safe(item)}</li>" for item in items[-20:])
            + "</ul>"
        )

    def refresh(self, workflow_run_id: str | None, stage: str = "", pending_confirmation: str | None = None) -> None:
        if not workflow_run_id:
            self.reset_view()
            return
        try:
            events = self.event_store.list_events(workflow_run_id)
            jobs = self.simulation_queue.list_jobs(workflow_run_id)
        except Exception as exc:
            self.browser.setHtml(f"<h3>智能体流程</h3><p>读取工作流事件失败：{self._safe(exc)}</p>")
            return

        snapshot, snapshot_error = self._load_snapshot(workflow_run_id)
        active_stage = stage or "-"
        pending_text = pending_confirmation or "-"

        event_items = []
        for event in events[-80:]:
            created_at = event.get("created_at", "")
            agent = event.get("agent", "")
            event_type = event.get("event_type", "")
            message = event.get("message", "")
            event_items.append(
                f"<li><code>{self._safe(created_at)}</code> [{self._safe(agent)}] "
                f"<b>{self._safe(event_type)}</b>：{self._safe(message)}</li>"
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
                    f"{self._safe(item.get('backend'))} / {self._safe(item.get('model'))} / {self._safe(item.get('status'))}"
                )
            llm_rows.append(
                "<tr>"
                f"<td>{self._safe(context.get('purpose'))}</td>"
                f"<td>{self._safe(payload.get('selected_backend'))}</td>"
                f"<td>{self._safe(payload.get('selected_model'))}</td>"
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
                f"<td><code>{self._safe(job.get('job_id'))}</code></td>"
                f"<td>{self._safe(job.get('session_candidate_id'))}</td>"
                f"<td>{self._safe(job.get('formal_candidate_id'))}</td>"
                f"<td>{self._safe(job.get('status'))}</td>"
                f"<td>{self._safe(ultimate_text)}</td>"
                f"<td>{self._safe(error)}</td>"
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
            + self._snapshot_summary_html(workflow_run_id, snapshot, active_stage, pending_text, snapshot_error)
            + self._llm_status_html()
            + self._workflow_graph_html(events, jobs, snapshot, active_stage)
            + self._diagnostics_html(events, jobs, snapshot, snapshot_error)
            + "<h4>有限元队列</h4>"
            + jobs_html
            + "<h4>LLM 调用轨迹</h4>"
            + llm_trace_html
            + "<h4>事件审计</h4>"
            + "<ol>"
            + "".join(event_items)
            + "</ol>"
        )

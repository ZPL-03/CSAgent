"""多智能体工作流状态视图。"""

from __future__ import annotations

from html import escape
from pathlib import Path
from typing import Any

from PyQt6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QTextBrowser, QVBoxLayout, QWidget

from core.llm_status import configured_llm_backends, probe_llm_backends
from core.paths import RESULTS_DIR
from gui.theme import resolve_theme
from workflow.agent_contracts import list_agent_contracts
from workflow.event_store import WorkflowEventStore
from workflow.run_audit import write_run_audit
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
        ("persist_knowledge", "知识回流"),
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
        "persist_knowledge": "案例记忆",
        "wait_report": "人工确认",
        "generate_report": "报告文件",
    }

    def __init__(
        self,
        event_store: WorkflowEventStore | None = None,
        simulation_queue: SimulationJobQueue | None = None,
        audit_output_dir: Path | None = None,
    ) -> None:
        super().__init__()
        self.event_store = event_store or WorkflowEventStore()
        self.simulation_queue = simulation_queue or SimulationJobQueue(self.event_store.db_path)
        self.audit_output_dir = audit_output_dir or RESULTS_DIR
        self.theme = "dark"
        self.llm_health_results: list[dict[str, Any]] = []
        self._last_refresh_args: tuple[str | None, str, str | None] = (None, "", None)
        self.health_button = QPushButton("检测 LLM 后端")
        self.audit_button = QPushButton("导出运行审计")
        self.audit_button.setEnabled(False)
        self.audit_status_label = QLabel("")
        self.audit_status_label.setWordWrap(True)
        self.browser = QTextBrowser()
        layout = QVBoxLayout()
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.health_button)
        button_layout.addWidget(self.audit_button)
        layout.addWidget(self.browser)
        layout.addWidget(self.audit_status_label)
        layout.addLayout(button_layout)
        self.setLayout(layout)
        self.health_button.clicked.connect(self._run_llm_health_check)
        self.audit_button.clicked.connect(self._export_run_audit)
        self.reset_view()

    def set_controls_visible(self, visible: bool) -> None:
        self.health_button.setVisible(visible)
        self.audit_button.setVisible(visible)

    def set_theme(self, theme: str) -> None:
        """刷新工作流 HTML 视图主题。"""

        self.theme = theme
        workflow_run_id, stage, pending = self._last_refresh_args
        if workflow_run_id:
            self.refresh(workflow_run_id, stage, pending)
        else:
            self.reset_view()

    def reset_view(self) -> None:
        self._last_refresh_args = (None, "", None)
        self.audit_button.setEnabled(False)
        self.audit_status_label.setText("")
        self.browser.setHtml(
            self._page_html(
                self._initial_dag_html()
                + self._llm_status_html()
                + self._agent_contracts_html()
            )
        )

    def _run_llm_health_check(self) -> None:
        self.health_button.setEnabled(False)
        self.health_button.setText("正在检测 LLM 后端...")
        try:
            self.llm_health_results = probe_llm_backends(timeout_seconds=12)
            workflow_run_id, stage, pending = self._last_refresh_args
            if workflow_run_id:
                self.refresh(workflow_run_id, stage, pending)
            else:
                self.browser.setHtml(
                    self._page_html(
                        self._initial_dag_html()
                        + self._llm_status_html()
                        + self._agent_contracts_html()
                    )
                )
        finally:
            self.health_button.setText("检测 LLM 后端")
            self.health_button.setEnabled(True)

    def _export_run_audit(self) -> None:
        workflow_run_id, stage, pending = self._last_refresh_args
        if not workflow_run_id:
            self.audit_status_label.setText("当前没有可导出的运行快照。")
            return
        try:
            path = write_run_audit(
                self.event_store,
                self.simulation_queue,
                workflow_run_id,
                output_dir=self.audit_output_dir,
            )
        except Exception as exc:
            self.audit_status_label.setText(f"运行审计导出失败：{self._safe(exc)}")
            return
        self.refresh(workflow_run_id, stage, pending)
        self.audit_status_label.setText(f"运行审计已导出：{path}")
        self.browser.append(f"<p><b>运行审计已导出：</b>{self._safe(path)}</p>")

    def _llm_status_html(self) -> str:
        health_by_name = {str(item.get("name") or ""): item for item in self.llm_health_results}
        rows = []
        for backend in configured_llm_backends():
            health = health_by_name.get(str(backend.get("name") or ""), {})
            latency = health.get("latency_ms")
            latency_text = "-" if latency in (None, "") else f"{latency} ms"
            health_status = health.get("health_message") or "未检测"
            error = health.get("error") or "-"
            rows.append(
                "<tr>"
                f"<td>{self._safe(backend['role'])}</td>"
                f"<td>{self._safe(backend['name'])}</td>"
                f"<td>{self._safe(backend['model'])}</td>"
                f"<td>{'是' if backend['base_url_configured'] else '否'}</td>"
                f"<td>{'是' if backend['api_key_configured'] else '否'}</td>"
                f"<td>{'可调用' if backend['available_for_call'] else '不可调用'}</td>"
                f"<td>{self._safe(health_status)}</td>"
                f"<td>{self._safe(latency_text)}</td>"
                f"<td>{self._safe(error)}</td>"
                "</tr>"
            )
        return (
            "<h4>LLM 后端</h4>"
            "<table border='1' cellspacing='0' cellpadding='6'>"
            "<tr><th>角色</th><th>后端</th><th>模型</th><th>URL</th><th>密钥</th><th>配置状态</th><th>实时检测</th><th>耗时</th><th>错误摘要</th></tr>"
            + "".join(rows)
            + "</table>"
        )

    def _safe(self, value: Any) -> str:
        if value is None or value == "":
            return "-"
        return escape(str(value))

    def _html_palette(self) -> dict[str, str]:
        if resolve_theme(self.theme) == "light":
            return {
                "text": "#172033",
                "muted": "#64748b",
                "surface": "#ffffff",
                "surface_alt": "#f8fafc",
                "border": "#c8d2df",
                "head": "#e8eef7",
                "done": "#0f766e",
                "active": "#2563eb",
                "failed": "#dc2626",
                "wait": "#94a3b8",
                "active_bg": "#eff6ff",
                "failed_bg": "#fff1f2",
            }
        return {
            "text": "#dbe4ef",
            "muted": "#94a3b8",
            "surface": "#111c2e",
            "surface_alt": "#0f172a",
            "border": "#334155",
            "head": "#182337",
            "done": "#14b8a6",
            "active": "#38bdf8",
            "failed": "#fb7185",
            "wait": "#64748b",
            "active_bg": "#102a43",
            "failed_bg": "#3c1822",
        }

    def _page_html(self, body: str) -> str:
        color = self._html_palette()
        return (
            "<style>"
            f"body{{font-size:13px;color:{color['text']};}}"
            "h3{margin:0 0 8px 0;font-size:17px;}"
            f"h4{{margin:4px 0 8px 0;font-size:14px;color:{color['text']};}}"
            "table{border-collapse:collapse;width:100%;}"
            f"th{{background:{color['head']};text-align:left;}}"
            f"th,td{{border:1px solid {color['border']};padding:6px 8px;vertical-align:top;}}"
            ".cards{display:flex;gap:8px;margin:8px 0 14px 0;}"
            f".card{{border:1px solid {color['border']};border-left:4px solid {color['active']};background:{color['surface_alt']};padding:8px 10px;min-width:118px;}}"
            f".card .label{{color:{color['muted']};font-size:12px;}}"
            f".card .value{{font-size:17px;font-weight:700;color:{color['text']};margin-top:4px;}}"
            f".dot{{display:inline-block;width:8px;height:8px;border-radius:4px;margin:0 5px 0 14px;}}"
            f".dot.done{{background:{color['done']};border:0;}}"
            f".dot.active{{background:{color['active']};border:0;}}"
            f".dot.wait{{background:{color['wait']};border:0;}}"
            f".status-done{{color:{color['done']};font-weight:700;}}"
            f".status-active{{color:{color['active']};font-weight:700;}}"
            f".status-failed{{color:{color['failed']};font-weight:700;}}"
            f".status-wait{{color:{color['wait']};font-weight:700;}}"
            "</style>"
            + body
        )

    def _initial_dag_html(self) -> str:
        return (
            "<h3>运行审计</h3>"
            "<p>等待任务输入后，这里显示运行摘要、智能体状态、工具调用、有限元队列、LLM 调用链路和失败诊断。</p>"
            "<table border='1' cellspacing='0' cellpadding='6'>"
            "<tr><th>审计对象</th><th>当前状态</th><th>说明</th></tr>"
            "<tr><td>LangGraph 运行</td><td><span class='status-wait'>等待</span></td><td>未创建运行编号</td></tr>"
            "<tr><td>LLM 后端</td><td><span class='status-wait'>未检测</span></td><td>点击下方按钮执行实时健康检查</td></tr>"
            "<tr><td>有限元队列</td><td><span class='status-wait'>空闲</span></td><td>等待候选进入 FEM 校核阶段</td></tr>"
            "<tr><td>运行恢复</td><td><span class='status-wait'>待选择</span></td><td>从右侧运行记录选择可恢复状态</td></tr>"
            "</table>"
        )

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

    def _status_class(self, status: str) -> str:
        if status in {"完成"}:
            return "done"
        if status in {"运行中", "当前"}:
            return "active"
        if status in {"失败"}:
            return "failed"
        return "wait"

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
        if node_name == "persist_knowledge":
            updates = snapshot.get("knowledge_updates") or []
            stored = sum(1 for item in updates if str(item.get("status") or "") == "stored")
            failed = sum(1 for item in updates if str(item.get("status") or "") == "failed")
            return f"回流={len(updates)}；正式={stored}；失败={failed}"
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
            state_class = self._status_class(status)
            rows.append(
                "<tr>"
                f"<td>{index}</td>"
                f"<td>{self._safe(label)}<br><code>{self._safe(node_name)}</code></td>"
                f"<td><span class='status-{state_class}'>{self._safe(status)}</span></td>"
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

    def _dashboard_cards_html(
        self,
        snapshot: dict[str, Any],
        events: list[dict[str, Any]],
        jobs: list[dict[str, Any]],
        active_stage: str,
        pending_text: str,
    ) -> str:
        llm_calls = sum(1 for event in events if event.get("event_type") == "llm_call_trace")
        failed_jobs = sum(1 for job in jobs if str(job.get("status") or "") == "failed")
        cards = [
            ("当前阶段", active_stage or "-"),
            ("候选池", len(snapshot.get("candidates") or [])),
            ("有限元作业", f"{len(jobs)} / 失败 {failed_jobs}"),
            ("LLM 调用", llm_calls),
            ("等待确认", pending_text or "-"),
        ]
        return (
            "<div class='cards'>"
            + "".join(
                f"<div class='card'><div class='label'>{self._safe(label)}</div>"
                f"<div class='value'>{self._safe(value)}</div></div>"
                for label, value in cards
            )
            + "</div>"
        )

    def _agent_contracts_html(self) -> str:
        rows = []
        for contract in list_agent_contracts():
            rows.append(
                "<tr>"
                f"<td>{self._safe(contract.label)}<br><code>{self._safe(contract.node_name)}</code></td>"
                f"<td>{self._safe(contract.runtime_agent)}<br><code>{self._safe(contract.tool_name)}</code></td>"
                f"<td>{self._safe(contract.responsibility)}</td>"
                f"<td><b>LLM</b>：{self._safe(contract.llm_policy)}<br>"
                f"<b>失败</b>：{self._safe(contract.failure_policy)}</td>"
                "</tr>"
            )
        return (
            "<h4>智能体职责契约</h4>"
            "<table border='1' cellspacing='0' cellpadding='6'>"
            "<tr><th>节点</th><th>运行时智能体/工具</th><th>职责</th><th>边界策略</th></tr>"
            + "".join(rows)
            + "</table>"
        )

    def _tool_calls_html(self, events: list[dict[str, Any]]) -> str:
        rows = []
        for event in events:
            if event.get("event_type") not in {"tool_started", "tool_completed", "tool_failed"}:
                continue
            payload = event.get("payload") or {}
            rows.append(
                "<tr>"
                f"<td><code>{self._safe(payload.get('tool'))}</code><br>{self._safe(event.get('agent'))}</td>"
                f"<td>{self._safe(event.get('event_type'))}</td>"
                f"<td>{self._safe(payload.get('duration_ms'))}</td>"
                f"<td><pre>{self._safe(self._compact_json(payload.get('input_summary')))}</pre></td>"
                f"<td><pre>{self._safe(self._compact_json(payload.get('output_summary')))}</pre></td>"
                f"<td>{self._safe(payload.get('error'))}</td>"
                "</tr>"
            )
        if not rows:
            return "<h4>工具调用审计</h4><p>当前运行还没有工具调用事件。</p>"
        return (
            "<h4>工具调用审计</h4>"
            "<table border='1' cellspacing='0' cellpadding='6'>"
            "<tr><th>工具/智能体</th><th>状态</th><th>耗时 ms</th><th>输入摘要</th><th>输出摘要</th><th>错误</th></tr>"
            + "".join(rows[-80:])
            + "</table>"
        )

    def _compact_json(self, value: Any) -> str:
        if value in (None, ""):
            return "-"
        try:
            import json

            text = json.dumps(value, ensure_ascii=False, sort_keys=True)
        except Exception:
            text = str(value)
        return text if len(text) <= 900 else text[:897] + "..."

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
        self._last_refresh_args = (workflow_run_id, stage, pending_confirmation)
        if not workflow_run_id:
            self.reset_view()
            return
        self.audit_button.setEnabled(True)
        self.audit_status_label.setText("")
        try:
            events = self.event_store.list_events(workflow_run_id)
            jobs = self.simulation_queue.list_jobs(workflow_run_id)
        except Exception as exc:
            self.browser.setHtml(self._page_html(f"<h3>智能体流程</h3><p>读取工作流事件失败：{self._safe(exc)}</p>"))
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
            self._page_html(
            "<h3>智能体流程</h3>"
            + self._dashboard_cards_html(snapshot, events, jobs, active_stage, pending_text)
            + self._snapshot_summary_html(workflow_run_id, snapshot, active_stage, pending_text, snapshot_error)
            + self._llm_status_html()
            + self._workflow_graph_html(events, jobs, snapshot, active_stage)
            + self._agent_contracts_html()
            + self._diagnostics_html(events, jobs, snapshot, snapshot_error)
            + self._tool_calls_html(events)
            + "<h4>有限元队列</h4>"
            + jobs_html
            + "<h4>LLM 调用轨迹</h4>"
            + llm_trace_html
            + "<h4>事件审计</h4>"
            + "<ol>"
            + "".join(event_items)
            + "</ol>"
            )
        )

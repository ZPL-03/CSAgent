"""工作流运行审计报告导出。"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from core.paths import RESULTS_DIR
from core.task_contract import describe_boundary_conditions, describe_load_conditions, task_payload_from_request
from workflow.agent_contracts import list_agent_contracts
from workflow.event_store import WorkflowEventStore
from workflow.simulation_queue import SimulationJobQueue


def _text(value: Any) -> str:
    if value is None or value == "":
        return "-"
    return str(value).replace("\n", " ").strip()


def _num(value: Any, digits: int = 3) -> str:
    if value is None or value == "":
        return "-"
    try:
        return f"{float(value):.{digits}f}"
    except Exception:
        return _text(value)


def _slug(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_-]+", "_", value.strip())
    return cleaned or "RUN"


def _table(headers: list[str], rows: list[list[Any]]) -> str:
    header = "| " + " | ".join(headers) + " |"
    divider = "| " + " | ".join("---" for _ in headers) + " |"
    body = ["| " + " | ".join(_text(item).replace("|", "\\|") for item in row) + " |" for row in rows]
    return "\n".join([header, divider, *body]) if body else "\n".join([header, divider])


def _source_text(snapshot: dict[str, Any]) -> str:
    counter = dict(snapshot.get("source_counter") or {})
    if not counter:
        for candidate in snapshot.get("candidates") or []:
            source = str(candidate.get("source") or "UNKNOWN")
            counter[source] = counter.get(source, 0) + 1
    return " / ".join(f"{key}={value}" for key, value in sorted(counter.items())) if counter else "-"


def _result_map(results: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    mapping: dict[str, dict[str, Any]] = {}
    for result in results:
        for key in [result.get("session_candidate_id"), result.get("candidate_id")]:
            if key:
                mapping[str(key)] = result
    return mapping


def _knowledge_update_map(updates: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    mapping: dict[str, dict[str, Any]] = {}
    for update in updates:
        for key in [update.get("session_candidate_id"), update.get("candidate_id")]:
            if key:
                mapping[str(key)] = update
    return mapping


def _pressure_error(predicted: Any, actual: Any) -> str:
    if predicted in (None, "") or actual in (None, ""):
        return "-"
    try:
        predicted_value = float(predicted)
        actual_value = float(actual)
    except Exception:
        return "-"
    if abs(actual_value) < 1e-9:
        return "-"
    return f"{abs(predicted_value - actual_value) / abs(actual_value) * 100.0:.2f}"


def _compact_json(value: Any, limit: int = 360) -> str:
    if value in (None, ""):
        return "-"
    try:
        text = json.dumps(value, ensure_ascii=False, sort_keys=True)
    except Exception:
        text = str(value)
    text = text.replace("\n", " ")
    return text if len(text) <= limit else text[: limit - 3] + "..."


def build_run_audit_markdown(
    run_id: str,
    snapshot: dict[str, Any],
    events: list[dict[str, Any]],
    jobs: list[dict[str, Any]],
) -> str:
    """生成单次工作流运行的 Markdown 审计报告。"""

    task = task_payload_from_request(snapshot.get("task") or {})
    results = list(snapshot.get("results") or [])
    candidates = list(snapshot.get("candidates") or [])
    screened = list(snapshot.get("screened_candidates") or [])
    evaluated = list(snapshot.get("evaluated_candidates") or [])
    updates = list(snapshot.get("knowledge_updates") or [])
    report = snapshot.get("report") or {}
    result_by_key = _result_map(results)
    update_by_key = _knowledge_update_map(updates)

    passed_count = sum(1 for result in results if str(result.get("verdict") or "") == "通过")
    failed_events = [event for event in events if event.get("event_type") in {"node_failed", "tool_failed", "simulation_job_failed"}]
    failed_jobs = [job for job in jobs if str(job.get("status") or "") == "failed"]
    llm_events = [event for event in events if event.get("event_type") == "llm_call_trace"]
    tool_events = [
        event
        for event in events
        if event.get("event_type") in {"tool_started", "tool_completed", "tool_failed"}
    ]

    lines = [
        f"# CSAgent 运行审计报告",
        "",
        "## 运行摘要",
        "",
        _table(
            ["字段", "值"],
            [
                ["运行编号", run_id],
                ["阶段", snapshot.get("stage")],
                ["等待确认", snapshot.get("pending_confirmation")],
                ["任务", task.get("application")],
                ["载荷", describe_load_conditions(task.get("load_conditions") or {})],
                ["边界", describe_boundary_conditions(task.get("boundary_conditions") or {})],
                ["候选总数", len(candidates)],
                ["候选来源", _source_text(snapshot)],
                ["初筛数量", len(screened)],
                ["待/已校核候选", len(evaluated)],
                ["有限元结果", len(results)],
                ["有限元通过", passed_count],
                ["知识回流记录", len(updates)],
                ["报告 Markdown", report.get("markdown_path")],
                ["报告 PDF", report.get("pdf_path")],
            ],
        ),
        "",
        "## 智能体职责契约",
        "",
        _table(
            ["节点", "运行时智能体", "工具", "LLM 边界", "失败策略"],
            [
                [item.node_name, item.runtime_agent, item.tool_name, item.llm_policy, item.failure_policy]
                for item in list_agent_contracts()
            ],
        ),
        "",
        "## 候选-结果-案例追踪",
        "",
    ]

    trace_rows = []
    for candidate in candidates:
        session_id = str(candidate.get("candidate_id") or "-")
        result = result_by_key.get(session_id) or {}
        formal_id = str(result.get("candidate_id") or candidate.get("persistent_candidate_id") or "-")
        update = update_by_key.get(session_id) or update_by_key.get(formal_id) or {}
        trace_rows.append(
            [
                session_id,
                candidate.get("source"),
                formal_id,
                _num(candidate.get("surrogate_ultimate_pressure_MPa")),
                _num(result.get("ultimate_pressure_MPa")),
                _pressure_error(candidate.get("surrogate_ultimate_pressure_MPa"), result.get("ultimate_pressure_MPa")),
                result.get("verdict"),
                update.get("case_id"),
                update.get("status") or ("未回流" if result else "-"),
            ]
        )
    lines.extend(
        [
            _table(
                ["TMP", "来源", "C编号", "代理极限压力", "FEM极限压力", "代理误差%", "FEM结论", "CASE", "回流状态"],
                trace_rows,
            ),
            "",
            "## 有限元队列",
            "",
            _table(
                ["作业编号", "TMP", "C编号", "状态", "极限压力", "错误"],
                [
                    [
                        job.get("job_id"),
                        job.get("session_candidate_id"),
                        job.get("formal_candidate_id"),
                        job.get("status"),
                        _num((job.get("result") or {}).get("ultimate_pressure_MPa")),
                        job.get("error_message"),
                    ]
                    for job in jobs
                ],
            ),
            "",
            "## LLM 调用轨迹",
            "",
        ]
    )

    llm_rows = []
    for event in llm_events:
        payload = event.get("payload") or {}
        context = payload.get("context") or {}
        trace = payload.get("trace") or []
        attempts = "；".join(
            f"{item.get('backend')}/{item.get('model')}/{item.get('status')}"
            for item in trace
        )
        llm_rows.append(
            [
                event.get("created_at"),
                context.get("purpose"),
                payload.get("selected_backend"),
                payload.get("selected_model"),
                "是" if payload.get("fallback_used") else "否",
                attempts,
            ]
        )
    lines.extend(
        [
            _table(["时间", "用途", "选用后端", "选用模型", "使用回退", "尝试链路"], llm_rows),
            "",
            "## 工具调用审计",
            "",
            _table(
                ["时间", "工具", "智能体", "状态", "耗时ms", "输入摘要", "输出摘要", "错误"],
                [
                    [
                        event.get("created_at"),
                        (event.get("payload") or {}).get("tool"),
                        event.get("agent"),
                        event.get("event_type"),
                        (event.get("payload") or {}).get("duration_ms"),
                        _compact_json((event.get("payload") or {}).get("input_summary")),
                        _compact_json((event.get("payload") or {}).get("output_summary")),
                        (event.get("payload") or {}).get("error"),
                    ]
                    for event in tool_events
                ],
            ),
            "",
            "## 诊断",
            "",
        ]
    )

    if failed_events or failed_jobs or snapshot.get("error"):
        if snapshot.get("error"):
            lines.append(f"- 当前状态错误：{_text(snapshot.get('error'))}")
        for event in failed_events:
            lines.append(f"- [{_text(event.get('agent'))}] {_text(event.get('message'))}")
        for job in failed_jobs:
            lines.append(f"- 有限元作业失败：{_text(job.get('job_id'))}，{_text(job.get('error_message'))}")
    else:
        lines.append("当前运行未记录阻断性诊断。")

    lines.extend(
        [
            "",
            "## 事件审计",
            "",
            _table(
                ["时间", "阶段", "智能体", "事件", "消息"],
                [
                    [
                        event.get("created_at"),
                        event.get("stage"),
                        event.get("agent"),
                        event.get("event_type"),
                        event.get("message"),
                    ]
                    for event in events
                ],
            ),
            "",
        ]
    )
    return "\n".join(lines)


def write_run_audit(
    event_store: WorkflowEventStore,
    simulation_queue: SimulationJobQueue,
    run_id: str,
    output_dir: Path | None = None,
) -> Path:
    """读取运行库并导出 Markdown 审计报告。"""

    snapshot = event_store.load_snapshot(run_id)
    events = event_store.list_events(run_id)
    jobs = simulation_queue.list_jobs(run_id)
    target_dir = output_dir or RESULTS_DIR
    target_dir.mkdir(parents=True, exist_ok=True)
    output_path = target_dir / f"run_audit_{_slug(run_id)}.md"
    output_path.write_text(build_run_audit_markdown(run_id, snapshot, events, jobs), encoding="utf-8")
    return output_path

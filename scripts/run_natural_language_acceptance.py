"""多条自然语言输入的端到端工作流验收入口。"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.dont_write_bytecode = True
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

from agents.orchestrator import OrchestratorAgent
from core.conversation_flow import ConversationFlowController, ConversationState
from core.paths import RESULTS_DIR, RUNTIME_DIR
from core.task_contract import requested_candidate_pool_size, requested_screen_top_k, task_payload_from_request
from workflow.event_store import WorkflowEventStore


DEFAULT_INSTRUCTIONS = [
    "请为复合材料外压圆柱耐压壳设计方案，外压 30 MPa，极限压力不低于 35 MPa，生成 8 个候选，初筛保留 3 个候选",
    "请为深海潜器复合材料外压圆柱耐压壳设计方案，外压 28 MPa，极限压力不低于 36 MPa，生成 8 个候选，初筛保留 3 个候选，两端简支",
    "Design a composite external-pressure cylindrical pressure hull, external pressure 25 MPa, ultimate pressure at least 40 MPa, generate 8 candidates, keep 3 after screening, simply supported ends",
]


def _candidate_signature(candidate: dict[str, Any]) -> tuple[Any, ...]:
    geometry = candidate.get("geometry") or {}
    material = candidate.get("material_system") or {}
    layup = candidate.get("layup") or {}
    return (
        candidate.get("hull_type"),
        material.get("material_key") or material.get("name"),
        tuple(
            (key, round(float(value), 6 if key == "imperfection_ratio" else 3))
            for key, value in sorted(geometry.items())
            if value is not None
        ),
        layup.get("template_name"),
        layup.get("layup"),
    )


def _assert_unique_candidates(candidates: list[dict[str, Any]]) -> None:
    signatures = [_candidate_signature(candidate) for candidate in candidates]
    if len(signatures) != len(set(signatures)):
        raise AssertionError("候选池存在结构重复方案")


def _attach_deterministic_downstream(orchestrator: OrchestratorAgent, output_dir: Path) -> None:
    """把 FEM、知识回流和报告替换为可审计的快速验收适配器。"""

    output_dir.mkdir(parents=True, exist_ok=True)

    def prepare_candidate_for_fem(task: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
        next_index = len(getattr(prepare_candidate_for_fem, "_seen", [])) + 1
        seen = list(getattr(prepare_candidate_for_fem, "_seen", []))
        seen.append(candidate.get("candidate_id"))
        setattr(prepare_candidate_for_fem, "_seen", seen)
        formal_id = f"C_ACCEPT_{next_index}"
        prepared = dict(candidate)
        prepared.pop("persistent_candidate_id", None)
        prepared["candidate_id"] = formal_id
        prepared["display_name"] = formal_id
        prepared["session_candidate_id"] = candidate["candidate_id"]
        return prepared

    def evaluate_prepared_candidate(task: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
        predicted = float(candidate.get("surrogate_ultimate_pressure_MPa") or 45.0)
        result = {
            "candidate_id": candidate["candidate_id"],
            "display_name": candidate["display_name"],
            "session_candidate_id": candidate["session_candidate_id"],
            "status": "success",
            "verdict": "通过",
            "linear_buckling_pressure_MPa": round(float(candidate.get("asme_linear_buckling_pressure_MPa") or predicted), 3),
            "ultimate_pressure_MPa": round(max(predicted * 0.96, 45.0), 3),
            "failure_mode": "acceptance_adapter",
            "visualization_path": "",
            "odb_path": "",
        }
        (output_dir / f"result_{candidate['candidate_id']}.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return result

    def persist_knowledge_records(
        task: dict[str, Any],
        fem_designs: list[dict[str, Any]],
        results: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        updates = []
        for index, design in enumerate(fem_designs, start=1):
            updates.append(
                {
                    "status": "stored",
                    "case_id": f"CASE_ACCEPT_{index}",
                    "candidate_id": design.get("candidate_id"),
                    "session_candidate_id": design.get("session_candidate_id"),
                }
            )
        return updates

    def generate_report(
        task: dict[str, Any],
        results: list[dict[str, Any]],
        candidates: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        run_id = str(task.get("task_id") or "TASK_ACCEPT")
        markdown_path = output_dir / f"{run_id}_acceptance_report.md"
        pdf_path = output_dir / f"{run_id}_acceptance_report.pdf"
        task_payload = task_payload_from_request(task)
        lines = [
            "# CSAgent 耐压壳设计报告",
            "",
            f"- 外压：{task_payload['load_conditions'].get('external_pressure_MPa')} MPa",
            f"- 目标极限压力：{task_payload['design_targets'].get('ultimate_pressure_min_MPa')} MPa",
            f"- 候选数量：{len(candidates or [])}",
            f"- FEM 验收结果：{len(results)} 个",
        ]
        markdown_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        pdf_path.write_bytes(b"%PDF-1.4\n% CSAgent acceptance fixture\n")
        return {
            "markdown_path": str(markdown_path),
            "pdf_path": str(pdf_path),
            "content": markdown_path.read_text(encoding="utf-8"),
            "llm_explanation_used": False,
        }

    orchestrator.prepare_candidate_for_fem = prepare_candidate_for_fem  # type: ignore[method-assign]
    orchestrator.evaluate_prepared_candidate = evaluate_prepared_candidate  # type: ignore[method-assign]
    orchestrator.persist_knowledge_records = persist_knowledge_records  # type: ignore[method-assign]
    orchestrator.generate_report = generate_report  # type: ignore[method-assign]


def _validate_completed_state(state: ConversationState, instruction: str) -> dict[str, Any]:
    if state.stage != "completed":
        raise AssertionError(f"工作流未完成：{state.stage}")
    if state.task is None:
        raise AssertionError("工作流缺少任务契约")
    if not state.workflow_run_id:
        raise AssertionError("工作流缺少运行编号")
    if not state.candidates:
        raise AssertionError("工作流未生成候选")
    if not state.evaluated_candidates:
        raise AssertionError("工作流未完成初筛")
    if not state.results:
        raise AssertionError("工作流未生成 FEM 结果")
    if not state.knowledge_updates:
        raise AssertionError("工作流未完成知识回流")
    if not state.report:
        raise AssertionError("工作流未生成报告")

    _assert_unique_candidates(state.candidates)
    _assert_unique_candidates(state.evaluated_candidates)
    task_payload = task_payload_from_request(state.task)
    target_total = requested_candidate_pool_size(state.task)
    target_top_k = requested_screen_top_k(state.task)
    if len(state.candidates) != target_total:
        raise AssertionError(f"候选数量不符合任务契约：{len(state.candidates)} != {target_total}")
    if len(state.evaluated_candidates) != target_top_k:
        raise AssertionError(f"初筛数量不符合任务契约：{len(state.evaluated_candidates)} != {target_top_k}")

    generation_audit = dict(state.candidates[0].get("generation_audit") or {}) if state.candidates else {}
    return {
        "instruction": instruction,
        "run_id": state.workflow_run_id,
        "stage": state.stage,
        "candidate_count": len(state.candidates),
        "screened_count": len(state.evaluated_candidates),
        "result_count": len(state.results),
        "knowledge_update_count": len(state.knowledge_updates),
        "report_markdown": state.report.get("markdown_path"),
        "external_pressure_MPa": task_payload["load_conditions"].get("external_pressure_MPa"),
        "ultimate_pressure_min_MPa": task_payload["design_targets"].get("ultimate_pressure_min_MPa"),
        "source_counter": {
            source: sum(1 for candidate in state.candidates if candidate.get("source") == source)
            for source in sorted({str(candidate.get("source")) for candidate in state.candidates})
        },
        "generation_audit": generation_audit,
    }


def _run_case(instruction: str, output_dir: Path, use_real_fem: bool) -> dict[str, Any]:
    orchestrator = OrchestratorAgent()
    if not use_real_fem:
        _attach_deterministic_downstream(orchestrator, output_dir)
    events: list[tuple[str, str, dict[str, Any]]] = []
    store = WorkflowEventStore(output_dir / "workflow_acceptance.sqlite3")
    controller = ConversationFlowController(
        orchestrator,
        event_callback=lambda event_type, message, payload: events.append((event_type, message, payload)),
        event_store=store,
    )

    state = controller.start(instruction)
    state = controller.continue_after_confirmation(state, True)
    state = controller.continue_after_confirmation(state, True)
    state = controller.continue_after_confirmation(state, True)
    summary = _validate_completed_state(state, instruction)

    snapshot = store.load_snapshot(state.workflow_run_id)
    if snapshot.get("stage") != "completed":
        raise AssertionError("事件库快照未记录完成状态")
    runtime_event_types = {
        payload.get("runtime_event_type")
        for event_type, _message, payload in events
        if event_type == "workflow_runtime_event"
    }
    required_events = {"node_started", "tool_started", "tool_completed", "simulation_job_queued", "simulation_job_completed"}
    missing_events = sorted(required_events - runtime_event_types)
    if missing_events:
        raise AssertionError(f"运行事件缺失：{missing_events}")

    summary["runtime_event_count"] = len(events)
    summary["workflow_status"] = store.list_runs(limit=1)[0]["status"]
    return summary


def _load_instructions(path: Path | None) -> list[str]:
    if path is None:
        return list(DEFAULT_INSTRUCTIONS)
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, list):
        return [str(item).strip() for item in payload if str(item).strip()]
    if isinstance(payload, dict) and isinstance(payload.get("instructions"), list):
        return [str(item).strip() for item in payload["instructions"] if str(item).strip()]
    raise ValueError("自然语言验收输入文件必须是字符串数组，或包含 instructions 数组的 JSON 对象")


def main() -> int:
    parser = argparse.ArgumentParser(description="运行多条自然语言输入的 CSAgent 端到端验收。")
    parser.add_argument("--instructions", type=Path, help="JSON 输入文件，内容为字符串数组或 instructions 字段。")
    parser.add_argument("--disable-llm", action="store_true", help="关闭 LLM 自动调用，仅验证确定性候选闭合和工作流。")
    parser.add_argument("--real-fem", action="store_true", help="使用真实 Abaqus FEM 链路；默认使用快速验收适配器。")
    parser.add_argument("--verbose", action="store_true", help="在控制台输出智能体内部日志。")
    args = parser.parse_args()

    load_dotenv(ROOT / ".env", override=True)
    if not args.verbose:
        logging.disable(logging.CRITICAL)
    if args.disable_llm:
        os.environ["CSDM_cph_DISABLE_LLM_AUTO"] = "1"

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = RUNTIME_DIR / "acceptance" / f"RUN_ACCEPTANCE_{timestamp}"
    output_dir.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    summaries = []
    for instruction in _load_instructions(args.instructions):
        summaries.append(_run_case(instruction, output_dir, use_real_fem=args.real_fem))

    report = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "output_dir": str(output_dir),
        "llm_enabled": os.getenv("CSDM_cph_DISABLE_LLM_AUTO", "0").strip().lower() not in {"1", "true", "yes", "on"},
        "real_fem": bool(args.real_fem),
        "case_count": len(summaries),
        "cases": summaries,
    }
    summary_path = RESULTS_DIR / f"natural_language_acceptance_{timestamp}.json"
    summary_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    console_report = {
        "status": "passed",
        "summary_path": str(summary_path),
        "output_dir": str(output_dir),
        "llm_enabled": report["llm_enabled"],
        "real_fem": report["real_fem"],
        "case_count": report["case_count"],
        "cases": [
            {
                "run_id": case["run_id"],
                "stage": case["stage"],
                "candidate_count": case["candidate_count"],
                "screened_count": case["screened_count"],
                "result_count": case["result_count"],
                "knowledge_update_count": case["knowledge_update_count"],
            }
            for case in summaries
        ],
    }
    print(json.dumps(console_report, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

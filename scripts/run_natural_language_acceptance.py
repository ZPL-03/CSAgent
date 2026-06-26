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


DEFAULT_INSTRUCTION_CASES = [
    {
        "instruction": "请为复合材料外压圆柱耐压壳设计方案，外压 30 MPa，极限压力不低于 35 MPa，生成 8 个候选，初筛保留 3 个候选",
        "expected": {"external_pressure_MPa": 30.0, "ultimate_pressure_min_MPa": 35.0, "candidate_count": 8, "screened_count": 3},
    },
    {
        "instruction": "面向深海设备舱的复合材料圆柱耐压壳，外压 28 MPa，极限压力目标不低于 36 MPa，两端简支，生成 8 个候选，初筛保留 3 个候选",
        "expected": {"external_pressure_MPa": 28.0, "ultimate_pressure_min_MPa": 36.0, "candidate_count": 8, "screened_count": 3},
    },
    {
        "instruction": "Design a composite external-pressure cylindrical pressure hull for 25 MPa hydrostatic pressure, ultimate pressure at least 40 MPa, simply supported ends, generate 8 candidates and retain 3 screened candidates.",
        "expected": {"external_pressure_MPa": 25.0, "ultimate_pressure_min_MPa": 40.0, "candidate_count": 8, "screened_count": 3},
    },
    {
        "instruction": "复合材料外压圆柱壳耐压设计，外压 32 MPa，极限压力不低于 42 MPa，可参考长度 520 mm、半径 105 mm、厚度 11 mm，但候选参数允许优化，生成 8 个候选，初筛保留 3 个候选",
        "expected": {"external_pressure_MPa": 32.0, "ultimate_pressure_min_MPa": 42.0, "candidate_count": 8, "screened_count": 3},
    },
    {
        "instruction": "请生成无人潜航器用复合材料耐压圆柱壳方案，外压 22 MPa，极限压力不低于 33 MPa，生成 8 个候选，初筛保留 3 个候选",
        "expected": {"external_pressure_MPa": 22.0, "ultimate_pressure_min_MPa": 33.0, "candidate_count": 8, "screened_count": 3},
    },
    {
        "instruction": "复合材料外压圆柱耐压壳，目标工况外压 35 MPa，极限压力不少于 45 MPa，要求两端固支，生成 8 个候选，初筛保留 3 个候选",
        "expected": {"external_pressure_MPa": 35.0, "ultimate_pressure_min_MPa": 45.0, "candidate_count": 8, "screened_count": 3},
    },
    {
        "instruction": "为轻量化深海耐压舱设计复合材料圆柱壳，外压 18 MPa，极限压力不低于 30 MPa，生成 8 个候选，初筛保留 3 个候选",
        "expected": {"external_pressure_MPa": 18.0, "ultimate_pressure_min_MPa": 30.0, "candidate_count": 8, "screened_count": 3},
    },
    {
        "instruction": "Composite pressure hull preliminary design: external pressure 40 MPa, required ultimate pressure no less than 52 MPa, generate 8 candidate designs and retain 3 screened candidates.",
        "expected": {"external_pressure_MPa": 40.0, "ultimate_pressure_min_MPa": 52.0, "candidate_count": 8, "screened_count": 3},
    },
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
    """把 FEM 和知识回流替换为可审计的快速验收适配器，报告阶段仍使用正式报告智能体。"""

    output_dir.mkdir(parents=True, exist_ok=True)
    if hasattr(orchestrator, "candidate_gen") and hasattr(orchestrator.candidate_gen, "case_retriever"):
        orchestrator.candidate_gen.case_retriever.use_vector_index = False
        orchestrator.candidate_gen.case_retriever._case_memory_failed = True

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

    def prepare_candidates_for_fem(task: dict[str, Any], candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
        prepared: list[dict[str, Any]] = []
        setattr(prepare_candidate_for_fem, "_seen", [])
        for candidate in candidates:
            prepared.append(prepare_candidate_for_fem(task, candidate))
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

    orchestrator.prepare_candidate_for_fem = prepare_candidate_for_fem  # type: ignore[method-assign]
    orchestrator.prepare_candidates_for_fem = prepare_candidates_for_fem  # type: ignore[method-assign]
    orchestrator.evaluate_prepared_candidate = evaluate_prepared_candidate  # type: ignore[method-assign]
    orchestrator.persist_knowledge_records = persist_knowledge_records  # type: ignore[method-assign]


def _expected_float(expected: dict[str, Any], *keys: str) -> float | None:
    for key in keys:
        if expected.get(key) is not None:
            return float(expected[key])
    return None


def _expected_int(expected: dict[str, Any], *keys: str) -> int | None:
    for key in keys:
        if expected.get(key) is not None:
            return int(expected[key])
    return None


def _assert_close(name: str, actual: float | int | None, expected: float | None) -> None:
    if expected is None:
        return
    if actual is None or abs(float(actual) - expected) > 1e-6:
        raise AssertionError(f"{name} 解析不符合期望：{actual} != {expected}")


def _validate_expected_contract(summary: dict[str, Any], expected: dict[str, Any] | None) -> None:
    if not expected:
        return
    _assert_close(
        "外部静水压力",
        summary.get("external_pressure_MPa"),
        _expected_float(expected, "external_pressure_MPa", "pressure"),
    )
    _assert_close(
        "目标极限压力",
        summary.get("ultimate_pressure_min_MPa"),
        _expected_float(expected, "ultimate_pressure_min_MPa", "target"),
    )
    expected_candidates = _expected_int(expected, "candidate_count", "total_candidates", "total")
    if expected_candidates is not None and int(summary.get("candidate_count", -1)) != expected_candidates:
        raise AssertionError(f"候选数量不符合期望：{summary.get('candidate_count')} != {expected_candidates}")
    expected_screened = _expected_int(expected, "screened_count", "top_k_candidates", "top_k")
    if expected_screened is not None and int(summary.get("screened_count", -1)) != expected_screened:
        raise AssertionError(f"初筛数量不符合期望：{summary.get('screened_count')} != {expected_screened}")


def _validate_completed_state(
    state: ConversationState,
    instruction: str,
    expected: dict[str, Any] | None = None,
) -> dict[str, Any]:
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
    if not state.report.get("report_outputs"):
        raise AssertionError("工作流未生成 FEM/总体/推荐方案报告交付件")

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
    summary = {
        "instruction": instruction,
        "run_id": state.workflow_run_id,
        "stage": state.stage,
        "candidate_count": len(state.candidates),
        "screened_count": len(state.evaluated_candidates),
        "result_count": len(state.results),
        "knowledge_update_count": len(state.knowledge_updates),
        "report_markdown": state.report.get("markdown_path"),
        "report_pdf": state.report.get("pdf_path"),
        "report_outputs": state.report.get("report_outputs"),
        "external_pressure_MPa": task_payload["load_conditions"].get("external_pressure_MPa"),
        "ultimate_pressure_min_MPa": task_payload["design_targets"].get("ultimate_pressure_min_MPa"),
        "source_counter": {
            source: sum(1 for candidate in state.candidates if candidate.get("source") == source)
            for source in sorted({str(candidate.get("source")) for candidate in state.candidates})
        },
        "generation_audit": generation_audit,
    }
    _validate_expected_contract(summary, expected)
    if expected:
        summary["expected"] = expected
    return summary


def _run_case(case: dict[str, Any], output_dir: Path, use_real_fem: bool) -> dict[str, Any]:
    instruction = str(case["instruction"])
    expected = case.get("expected") if isinstance(case.get("expected"), dict) else None
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
    summary = _validate_completed_state(state, instruction, expected=expected)

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


def _normalize_instruction_case(item: Any) -> dict[str, Any] | None:
    if isinstance(item, str):
        instruction = item.strip()
        return {"instruction": instruction} if instruction else None
    if isinstance(item, dict):
        instruction = str(item.get("instruction") or item.get("text") or "").strip()
        if not instruction:
            return None
        expected = item.get("expected")
        return {"instruction": instruction, "expected": expected} if isinstance(expected, dict) else {"instruction": instruction}
    return None


def _load_instruction_cases(path: Path | None) -> list[dict[str, Any]]:
    if path is None:
        return [dict(case, expected=dict(case["expected"])) for case in DEFAULT_INSTRUCTION_CASES]
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    raw_items: list[Any]
    if isinstance(payload, list):
        raw_items = payload
    elif isinstance(payload, dict) and isinstance(payload.get("instructions"), list):
        raw_items = payload["instructions"]
    else:
        raise ValueError("自然语言验收输入文件必须是字符串数组、对象数组，或包含 instructions 数组的 JSON 对象")
    cases = [case for item in raw_items if (case := _normalize_instruction_case(item))]
    if not cases:
        raise ValueError("自然语言验收输入文件没有有效指令")
    return cases


def _select_instruction_cases(cases: list[dict[str, Any]], max_cases: int | None) -> list[dict[str, Any]]:
    if max_cases is None or max_cases == 0:
        return cases
    if max_cases < 0:
        raise ValueError("max-cases 必须大于等于 0")
    return cases[:max_cases]


def main() -> int:
    parser = argparse.ArgumentParser(description="运行多条自然语言输入的 CSAgent 端到端验收。")
    parser.add_argument("--instructions", type=Path, help="JSON 输入文件，内容为字符串数组或 instructions 字段。")
    parser.add_argument("--max-cases", type=int, default=0, help="最多运行前 N 条验收输入；0 表示运行全部输入。")
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
    for case in _select_instruction_cases(_load_instruction_cases(args.instructions), args.max_cases):
        summaries.append(_run_case(case, output_dir, use_real_fem=args.real_fem))

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
    exit_code = main()
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(exit_code)

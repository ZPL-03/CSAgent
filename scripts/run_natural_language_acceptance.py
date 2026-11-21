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

from dotenv import load_dotenv  # noqa: E402

from agents.orchestrator import OrchestratorAgent  # noqa: E402
from core.conversation_flow import ConversationFlowController, ConversationState  # noqa: E402
from core.paths import RESULTS_DIR, RUNTIME_DIR  # noqa: E402
from core.task_contract import requested_candidate_pool_size, requested_screen_top_k, task_payload_from_request  # noqa: E402
from workflow.event_store import WorkflowEventStore  # noqa: E402


DEFAULT_INSTRUCTION_CASES = [
    {
        "instruction": "请设计复合材料耐压圆柱壳，工作压力 30 MPa，长度 500 mm，半径 100 mm，生成 8 个候选，初筛保留 3 个候选",
        "expected": {
            "external_pressure_MPa": 30,
            "candidate_count": 8,
            "screened_count": 3
        }
    },
    {
        "instruction": "面向深海设备舱设计复合材料圆柱耐压壳，工作压力 28 MPa，长度 600 mm，半径 120 mm，两端简支，生成 8 个候选，初筛保留 3 个候选",
        "expected": {
            "external_pressure_MPa": 28,
            "candidate_count": 8,
            "screened_count": 3
        }
    },
    {
        "instruction": "Design a composite cylindrical pressure hull for 25 MPa hydrostatic pressure, length 500 mm, radius 100 mm, simply supported ends, generate 8 candidates and retain 3 screened candidates.",
        "expected": {
            "external_pressure_MPa": 25,
            "candidate_count": 8,
            "screened_count": 3
        }
    },
    {
        "instruction": "复合材料耐压圆柱壳，工作压力 32 MPa，可参考长度 520 mm、半径 105 mm、厚度 11 mm，生成 8 个候选，初筛保留 3 个候选",
        "expected": {
            "external_pressure_MPa": 32,
            "candidate_count": 8,
            "screened_count": 3
        }
    },
    {
        "instruction": "请设计无人潜航器用复合材料耐压圆柱壳，工作压力 22 MPa，长度 500 mm，半径 100 mm",
        "expected": {
            "external_pressure_MPa": 22,
            "candidate_count": 8,
            "screened_count": 3
        },
        "candidate_count_reply": "8",
        "screen_count_reply": "3"
    },
    {
        "instruction": "复合材料耐压圆柱壳，工作压力 35 MPa，要求两端固支，生成 8 个候选，初筛保留 3 个候选",
        "expected": {
            "external_pressure_MPa": 35,
            "candidate_count": 8,
            "screened_count": 3
        }
    },
    {
        "instruction": "为深海耐压舱设计轻量化复合材料圆柱壳，工作压力 18 MPa，长度 500 mm，半径 100 mm，生成 8 个候选",
        "expected": {
            "external_pressure_MPa": 18,
            "candidate_count": 8,
            "screened_count": 3
        },
        "screen_count_reply": "3"
    },
    {
        "instruction": "Composite cylindrical pressure hull design: working pressure 40 MPa, generate 8 candidate designs and retain 3 screened candidates.",
        "expected": {
            "external_pressure_MPa": 40,
            "candidate_count": 8,
            "screened_count": 3
        }
    }
]


def _candidate_signature(candidate: dict[str, Any]) -> tuple[Any, ...]:
    geometry = candidate.get("geometry") or {}
    material = candidate.get("material_system") or {}
    layup = candidate.get("layup") or {}
    return (
        candidate.get("hull_type"),
        material.get("material_key") or material.get("name"),
        tuple(
            (key, value if key == "radius_reference" else round(float(value), 6 if key == "imperfection_ratio" else 3))
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
    if set(state.report.get("report_outputs") or {}) != {"overall"}:
        raise AssertionError("工作流未生成总体设计方案报告")

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
        "source_counter": {
            source: sum(1 for candidate in state.candidates if candidate.get("source") == source)
            for source in sorted({str(candidate.get("source")) for candidate in state.candidates})
        },
        "generation_audit": generation_audit,
        "llm_explanation_used": bool(state.report.get("llm_explanation_used")),
        "llm_explanation_audit": state.report.get("llm_explanation_audit"),
    }
    _validate_expected_contract(summary, expected)
    if expected:
        summary["expected"] = expected
    return summary


def _run_case(case: dict[str, Any], output_dir: Path) -> dict[str, Any]:
    instruction = str(case["instruction"])
    expected = case.get("expected") if isinstance(case.get("expected"), dict) else None
    orchestrator = OrchestratorAgent()
    events: list[tuple[str, str, dict[str, Any]]] = []
    store = WorkflowEventStore(output_dir / "workflow_acceptance.sqlite3")
    controller = ConversationFlowController(
        orchestrator,
        event_callback=lambda event_type, message, payload: events.append((event_type, message, payload)),
        event_store=store,
    )

    state = controller.start(instruction)
    if state.pending_confirmation == "candidate_count":
        state = controller.provide_quantity(state, str(case.get("candidate_count_reply") or ""))
    if state.pending_confirmation == "screen_count":
        state = controller.provide_quantity(state, str(case.get("screen_count_reply") or ""))
    elif state.pending_confirmation == "screen_candidates":
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
        normalized = {"instruction": instruction, **({"expected": expected} if isinstance(expected, dict) else {})}
        for key in ("candidate_count_reply", "screen_count_reply"):
            if item.get(key) is not None:
                normalized[key] = item[key]
        return normalized
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
        summaries.append(_run_case(case, output_dir))

    report = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "output_dir": str(output_dir),
        "llm_enabled": os.getenv("CSDM_cph_DISABLE_LLM_AUTO", "0").strip().lower() not in {"1", "true", "yes", "on"},
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

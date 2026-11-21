"""在独立目录验证指定模型：运行真实全流程，或仅复用求解证据验证模型。"""

from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import datetime, timezone
import json
import hashlib
import os
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]


def assess_workflow(result: dict) -> dict:
    """候选来源只作诊断；工程流程与模型报告分别验收。"""
    from core.fem_result_semantics import complete_case_result_errors
    from core.rule_checker import RuleChecker

    candidates = result["candidates"]
    sources = {source: sum(item["source"] == source for item in candidates)
               for source in ("LLM", "CASE_TRANSFER", "DOE")}
    generation = candidates[0].get("generation_audit") if candidates else None
    flow_failures = []
    checker = RuleChecker()
    for item in candidates:
        flow_failures.extend(checker.run(item, task=result["task"])["errors"])
    if not candidates:
        flow_failures.append("缺少候选")
    for item in result["results"]:
        flow_failures.extend(complete_case_result_errors(item))
        if item.get("solved_design"):
            flow_failures.extend(checker.run(item["solved_design"], task=result["task"])["errors"])
        else:
            flow_failures.append("缺少实际求解设计")
    if not result["results"]:
        flow_failures.append("缺少真实求解结果")
    if not result["knowledge_updates"] or any(item.get("status") not in {"stored", "archived_only"} for item in result["knowledge_updates"]):
        flow_failures.append("案例未完整入库")
    if not result["report"].get("pdf_generated"):
        flow_failures.append("PDF 未生成")
    used = bool(result["report"].get("llm_explanation_used"))
    explanation_audit = result["report"].get("llm_explanation_audit") or {}
    model_failures = []
    if not used or explanation_audit.get("status") != "accepted":
        model_failures.append("模型报告事实选择未通过")
        if explanation_audit.get("error"):
            model_failures.append(explanation_audit["error"])
    failures = flow_failures + model_failures
    return {
        "status": "failed" if failures else "passed", "failures": failures,
        "flow_status": "failed" if flow_failures else "passed", "flow_failures": flow_failures,
        "model_report_status": "failed" if model_failures else "passed", "model_report_failures": model_failures,
        "source_counter": sources, "generation_audit": generation,
        "llm_candidate_branch": {"status": "adopted" if sources["LLM"] else "not_adopted",
                                 "accepted_count": sources["LLM"],
                                 "diagnostics": (generation or {}).get("llm_diagnostics", []),
                                 "filter_reasons": ((generation or {}).get("filter_reasons") or {}).get("LLM", [])},
        "llm_explanation_used": used, "llm_explanation_audit": explanation_audit,
    }


def replay_models(source_path: Path, backend, output: Path) -> dict:
    """候选重生成与历史求解证据分别保存；不创建求解器，不入库或重算代理公式。"""
    from agents.candidate_gen import CandidateGenAgent
    from agents.report_gen import ReportGenAgent
    from core.io_utils import write_json

    raw = source_path.read_bytes()
    source = json.loads(raw)
    source_audit = assess_workflow(source)
    if source_audit["flow_status"] != "passed":
        raise ValueError("源工程流程证据不完整：" + "；".join(source_audit["flow_failures"]))
    events = []
    def record_event(_agent, _message, event):
        events.append(event)
        write_json(output / "model_events.json", events)

    generator = CandidateGenAgent(record_event)
    generator.llm_backend = backend
    candidates = generator.run(source["task"])
    write_json(output / "candidate_replay.json", {"task": source["task"], "candidates": candidates,
                                                  "generation_audit": generator.last_generation_audit})
    reporter = ReportGenAgent(record_event)
    reporter.llm_backend = backend
    # 只有源运行的候选与原始结果关联；重生成候选没有 FEM 结论。
    selected = {item["candidate_id"]: item for item in source.get("top_candidates", [])}
    report_candidates = [selected.get(item["candidate_id"], item) for item in source["candidates"]]
    report_artifact = reporter.run({"task": source["task"], "results": source["results"],
                                    "candidates": report_candidates, "output_dir": output / "reports"})
    write_json(output / "report_replay.json", report_artifact)
    audit = assess_workflow({**source, "report": report_artifact})
    audit.update(mode="model_replay", flow_status="not_run", source_flow_status=source_audit["flow_status"],
                 solver_executed=False, source_workflow=str(source_path.resolve()),
                 source_workflow_sha256=hashlib.sha256(raw).hexdigest(),
                 generation_audit=generator.last_generation_audit,
                 source_counter={name: sum(row["source"] == name for row in candidates) for name in ("LLM", "CASE_TRANSFER", "DOE")})
    audit["llm_candidate_branch"] = {
        "status": "adopted" if audit["source_counter"]["LLM"] else "not_adopted",
        "accepted_count": audit["source_counter"]["LLM"],
        "diagnostics": generator.last_generation_audit.get("llm_diagnostics", []),
        "filter_reasons": generator.last_generation_audit.get("filter_reasons", {}).get("LLM", []),
    }
    return audit


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--backend", choices=("primary", "fallback"), required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--run-real-abaqus", action="store_true", help="明确允许真实 Abaqus 求解。")
    mode.add_argument("--replay-workflow", type=Path, help="复用 workflow.json，仅执行模型候选生成和报告，不运行 Abaqus。")
    parser.add_argument("--instruction", default="外压30MPa，长度500mm，半径100mm，缺陷比0.008，生成2个候选，初筛保留1个")
    args = parser.parse_args(argv)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    mode_name = "model_replay" if args.replay_workflow else "full_workflow"
    output = ROOT / "data/runtime/model_validation" / f"{stamp}_{args.backend}_{mode_name}"
    output.mkdir(parents=True, exist_ok=False)
    os.environ["CSDM_CPH_RUN_ROOT"] = str(output)
    os.environ["CSDM_cph_DISABLE_LLM_AUTO"] = "1"
    if os.getenv("CSDM_cph_USE_HASH_EMBEDDING") == "1":
        raise ValueError("真实模型验收不接受哈希嵌入")
    sys.path.insert(0, str(ROOT))

    # 路径隔离必须先于业务模块导入，所有台账、案例、向量库和报告写入该目录。
    from core.config_loader import embedding_device, load_llm_config
    from core.llm_backend import LLMBackend
    from core.io_utils import write_json

    report = {"status": "running", "backend": args.backend, "mode": mode_name,
              "solver_executed": False, "started_at": datetime.now(timezone.utc).isoformat(),
              "embedding_device": embedding_device(), "output_dir": str(output)}
    write_json(output / "validation.json", report)
    backend = None
    orchestrator = None
    try:
        config = deepcopy(load_llm_config())
        backend_name = {"primary": "domain_finetuned_primary", "fallback": "configured_fallback"}[args.backend]
        config["backends"] = [item for item in config["backends"] if item["name"] == backend_name]
        if len(config["backends"]) != 1:
            raise ValueError("缺少待验收模型配置")
        backend = LLMBackend(config)
        report["model"] = backend.model
        # 固定到同一指定后端，缺失主模型不能被外部 API 的成功替代。
        if args.replay_workflow:
            report.update(replay_models(args.replay_workflow, backend, output))
        else:
            from agents.orchestrator import OrchestratorAgent

            orchestrator = OrchestratorAgent()
            orchestrator.candidate_gen.llm_backend = backend
            orchestrator.report_gen.llm_backend = backend
            report["solver_executed"] = True
            result = orchestrator.run(args.instruction)
            write_json(output / "workflow.json", result)
            report.update(assess_workflow(result))
    except Exception as exc:
        report.update(status="failed", flow_status="not_run" if args.replay_workflow else "failed", model_report_status="not_completed",
                      error=backend._sanitize_trace_error(exc) if backend else type(exc).__name__)
        if orchestrator is not None:
            report["generation_audit"] = orchestrator.candidate_gen.last_generation_audit
    finally:
        report["finished_at"] = datetime.now(timezone.utc).isoformat()
        report["llm_calls"] = backend.call_history if backend else []
        write_json(output / "validation.json", report)
        if backend:
            for runtime in backend.backends:
                if runtime.client is not None:
                    runtime.client.close()
    print(json.dumps({"status": report["status"], "validation_path": str(output / "validation.json")}, ensure_ascii=False))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())

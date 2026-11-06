"""校验 CS_LLM FEM-ready 候选并通过正式仿真队列运行指定方案。"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.fem_candidate_transfer import (  # noqa: E402
    FEMCandidateTransferError,
    build_fem_ready_task_record,
    import_fem_ready_response,
)
from workflow.runtime import DesignWorkflowRuntime  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="运行 CS_LLM FEM-ready 候选的正式 Abaqus 校核。")
    parser.add_argument("input", type=Path, help="设计服务完整 JSON 响应文件")
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument("--candidate-id", action="append", dest="candidate_ids", help="待运行的 TMP 编号，可重复")
    selection.add_argument("--all", action="store_true", help="运行候选包中的全部方案")
    parser.add_argument("--run-id", help="显式工作流运行编号")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        imported = import_fem_ready_response(args.input)
        payload = imported["payload"]
        candidates = list(payload["candidates"])
        if not args.all:
            requested = list(dict.fromkeys(args.candidate_ids or []))
            by_id = {str(candidate.get("candidate_id")): candidate for candidate in candidates}
            missing = [candidate_id for candidate_id in requested if candidate_id not in by_id]
            if missing:
                raise FEMCandidateTransferError("候选包中不存在编号：" + ", ".join(missing))
            candidates = [by_id[candidate_id] for candidate_id in requested]
        task = build_fem_ready_task_record(payload)
        result = DesignWorkflowRuntime().evaluate_fem_ready_candidates(
            task,
            candidates,
            run_id=args.run_id,
        )
    except (OSError, json.JSONDecodeError, FEMCandidateTransferError, ValueError, RuntimeError) as exc:
        print(json.dumps({"status": "failed", "error": str(exc)}, ensure_ascii=False))
        return 1

    print(
        json.dumps(
            {
                "status": "completed",
                "run_id": result["run_id"],
                "candidate_count": len(candidates),
                "knowledge_updates": result["knowledge_updates"],
                "jobs": [
                    {
                        "candidate_id": item.get("candidate_id"),
                        "session_candidate_id": item.get("session_candidate_id"),
                        "design_revision_id": item.get("design_revision_id"),
                        "status": item.get("status"),
                        "verdict": item.get("verdict"),
                        "error_type": item.get("error_type"),
                    }
                    for item in result["results"]
                ],
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

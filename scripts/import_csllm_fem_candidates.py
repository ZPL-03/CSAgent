"""导入 CS_LLM 设计服务返回的 FEM-ready JSON 候选包。"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.fem_candidate_transfer import FEMCandidateTransferError, import_fem_ready_response  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="导入并验证 CS_LLM FEM-ready JSON 响应。")
    parser.add_argument("input", type=Path, help="设计服务完整 JSON 响应文件")
    parser.add_argument("--output", type=Path, help="已验证候选包输出路径")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        imported = import_fem_ready_response(args.input, args.output)
    except (OSError, json.JSONDecodeError, FEMCandidateTransferError) as exc:
        print(json.dumps({"status": "failed", "error": str(exc)}, ensure_ascii=False))
        return 1
    payload = imported["payload"]
    print(
        json.dumps(
            {
                "status": "validated",
                "path": imported["path"],
                "candidate_count": payload["candidate_count"],
                "design_fingerprint": payload["design_fingerprint"],
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

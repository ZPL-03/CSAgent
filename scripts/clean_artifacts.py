"""列出并清理 Python 缓存及明确指定的无案例引用求解工件。"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.paths import ABAQUS_DIR, ABAQUS_RUNS_DIR, CASES_DIR, DATA_DIR  # noqa: E402


IO_DIR = DATA_DIR / "io"


def candidate_artifact_paths(candidate_id: str) -> list[Path]:
    normalized = str(candidate_id)
    if not re.fullmatch(r"C[1-9][0-9]*", normalized):
        raise ValueError(f"无效求解编号：{candidate_id}")
    return [
        IO_DIR / f"input_{normalized}.json",
        IO_DIR / f"result_{normalized}.json",
        ABAQUS_RUNS_DIR / normalized,
        ABAQUS_DIR / f"{normalized}.inp",
        ABAQUS_DIR / f"{normalized}.odb",
        ABAQUS_DIR / f"{normalized}_mode1.json",
    ]


def unreferenced_candidate_paths(candidate_ids: list[str]) -> list[Path]:
    """拒绝案例引用和带有作业锁的候选。"""
    referenced = {json.loads(path.read_text(encoding="utf-8")).get("candidate_id")
                  for path in CASES_DIR.glob("CASE_*.json")}
    if referenced.intersection(candidate_ids):
        raise ValueError("求解工件仍被案例引用，不允许单独删除")
    paths = []
    for candidate_id in candidate_ids:
        candidate_paths = candidate_artifact_paths(candidate_id)
        if any((ABAQUS_RUNS_DIR / candidate_id).rglob("*.lck")) or (ABAQUS_DIR / f"{candidate_id}.lck").exists():
            raise ValueError(f"候选 {candidate_id} 存在作业锁，不能清理")
        paths.extend(candidate_paths)
    return paths


def remove_path(path: Path) -> None:
    """删除文件或目录，不存在时直接跳过。"""
    if not path.exists():
        return
    if path.is_symlink() or not path.resolve().is_relative_to(ROOT.resolve()) or path.resolve() == ROOT.resolve():
        raise ValueError(f"不允许清理越界路径：{path}")
    if path.is_dir():
        shutil.rmtree(path)
    else:
        path.unlink(missing_ok=True)


def python_cache_paths(root: Path | None = None) -> list[Path]:
    root = root or ROOT
    return [*root.rglob("__pycache__"), root / ".pytest_cache", root / ".ruff_cache", *root.rglob("*.pyc")]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate-id", action="append", default=[])
    parser.add_argument("--apply", action="store_true", help="执行清理；省略时只列出目标")
    args = parser.parse_args()
    paths = sorted(set(python_cache_paths() + unreferenced_candidate_paths(args.candidate_id)))
    targets = [path for path in paths if path.exists() and not any(parent in paths for parent in path.parents)]
    for path in targets:
        if path.is_symlink() or not path.resolve().is_relative_to(ROOT.resolve()) or path.resolve() == ROOT.resolve():
            raise ValueError(f"不允许清理越界路径：{path}")
    print(json.dumps({"apply": args.apply, "targets": [str(path) for path in targets]}, ensure_ascii=False))
    if args.apply:
        for path in targets:
            remove_path(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

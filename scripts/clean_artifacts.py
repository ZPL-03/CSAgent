"""清理 Python 缓存、Abaqus 会话残留和异常工件。"""

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

from core.paths import ABAQUS_DIR, ABAQUS_RUNS_DIR, CASES_DIR, DATA_DIR, RESULTS_DIR, RUNTIME_DIR


IO_DIR = DATA_DIR / "io"


def candidate_artifact_paths(candidate_id: str) -> list[Path]:
    normalized = str(candidate_id).strip()
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


def purge_business_records(candidate_ids: list[str]) -> None:
    """只清理没有案例引用的求解工件，避免破坏案例证据链。"""
    referenced = {json.loads(path.read_text(encoding="utf-8")).get("candidate_id")
                  for path in CASES_DIR.glob("CASE_*.json")}
    if referenced.intersection(candidate_ids):
        raise ValueError("求解工件仍被案例引用，不允许单独删除")
    for candidate_id in candidate_ids:
        for path in candidate_artifact_paths(candidate_id):
            remove_path(path)


def purge_problem_prefixes(prefixes: list[str]) -> None:
    candidate_ids = [item.strip() for item in prefixes]
    for candidate_id in candidate_ids:
        candidate_artifact_paths(candidate_id)
    purge_business_records(candidate_ids)

    for path in RESULTS_DIR.glob("batch_summary_*.json"):
        text = path.read_text(encoding="utf-8") if path.exists() else ""
        payload = json.loads(text)
        records = payload if isinstance(payload, list) else payload.get("records", [])
        if any(record.get("candidate_id") in candidate_ids for record in records):
            remove_path(path)




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


def clean_python_caches() -> None:
    """清理 Python 缓存目录。"""
    for path in ROOT.rglob("__pycache__"):
        remove_path(path)
    remove_path(ROOT / ".pytest_cache")
    for path in ROOT.rglob("*.pyc"):
        remove_path(path)


def clean_abaqus_session_files() -> None:
    """清理 Abaqus 会话文件和临时 build 脚本。"""
    for pattern in ("abaqus.rpy*", "abaqus*.rec"):
        for path in ABAQUS_DIR.glob(pattern):
            remove_path(path)
        for path in ABAQUS_RUNS_DIR.rglob(pattern):
            remove_path(path)

    for path in ABAQUS_DIR.glob("build_*.py"):
        remove_path(path)

    residual_patterns = (
        "*.lck",
        "*.023",
        "*.com",
        "*.jnl",
        "*.prt",
        "*.sim",
        "*.odb_f",
    )
    for pattern in residual_patterns:
        for path in ABAQUS_RUNS_DIR.rglob(pattern):
            remove_path(path)


def clean_gui_audit_artifacts() -> None:
    """清理 GUI 渲染审计保留的临时截图目录。"""
    remove_path(RUNTIME_DIR / "release_gui_audit")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--purge-prefix", action="append", default=[])
    parser.add_argument("--candidate-id", action="append", default=[])
    args = parser.parse_args()

    clean_python_caches()
    clean_abaqus_session_files()
    clean_gui_audit_artifacts()
    purge_business_records(args.candidate_id)
    purge_problem_prefixes(args.purge_prefix)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

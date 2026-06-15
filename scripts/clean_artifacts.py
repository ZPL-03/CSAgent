"""清理 Python 缓存、Abaqus 会话残留和异常工件。"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.paths import ABAQUS_DIR, ABAQUS_RUNS_DIR, CHROMA_DIR, DATA_DIR, RESULTS_DIR, RUNTIME_DIR


IO_DIR = DATA_DIR / "io"


def candidate_artifact_paths(candidate_id: str) -> list[Path]:
    normalized = str(candidate_id).strip()
    if not normalized:
        return []
    return [
        IO_DIR / f"input_{normalized}.json",
        IO_DIR / f"result_{normalized}.json",
        ABAQUS_RUNS_DIR / normalized,
        ABAQUS_DIR / f"{normalized}.inp",
        ABAQUS_DIR / f"{normalized}.odb",
        ABAQUS_DIR / f"{normalized}_mode1.json",
    ]


def purge_business_records(candidate_ids: list[str], case_ids: list[str]) -> None:
    """只清理候选求解工件，不删除正式案例记录，避免破坏连续编号。"""
    touched = False
    for candidate_id in candidate_ids:
        for path in candidate_artifact_paths(candidate_id):
            touched = touched or path.exists()
            remove_path(path)
    _ = case_ids
    if touched and CHROMA_DIR.exists():
        shutil.rmtree(CHROMA_DIR, ignore_errors=True)


def purge_problem_prefixes(prefixes: list[str]) -> None:
    candidate_ids = [item.strip() for item in prefixes if item.strip() and item.strip().startswith("C") and not item.strip().startswith("CASE_")]
    case_ids = [item.strip() for item in prefixes if item.strip().startswith("CASE_")]
    purge_business_records(candidate_ids, case_ids)

    for path in RESULTS_DIR.glob("batch_summary_*.json"):
        text = path.read_text(encoding="utf-8") if path.exists() else ""
        if any(prefix in text for prefix in prefixes):
            remove_path(path)

    if prefixes and not candidate_ids and not case_ids and CHROMA_DIR.exists():
        shutil.rmtree(CHROMA_DIR, ignore_errors=True)




def remove_path(path: Path) -> None:
    """删除文件或目录，不存在时直接跳过。"""
    if not path.exists():
        return
    if path.is_dir():
        shutil.rmtree(path, ignore_errors=True)
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

    for path in ABAQUS_RUNS_DIR.rglob("build_*.py"):
        remove_path(path)

    residual_patterns = (
        "*.lck",
        "*.023",
        "*.com",
        "*.jnl",
        "*.sta",
        "*.prt",
        "*.sim",
        "*.log",
        "*.env",
        "*.odb_f",
        "candidate_retry_*.json",
    )
    for pattern in residual_patterns:
        for path in ABAQUS_RUNS_DIR.rglob(pattern):
            remove_path(path)


def clean_contaminated_vector_index() -> None:
    """清理由测试临时目录污染的本地向量索引。"""
    if not CHROMA_DIR.exists():
        return
    temp_markers = (b"pytest-", b"pytest-of-")
    for path in CHROMA_DIR.rglob("*"):
        if not path.is_file():
            continue
        try:
            with path.open("rb") as handle:
                data = handle.read(2_000_000)
        except OSError:
            continue
        if any(marker in data for marker in temp_markers):
            remove_path(CHROMA_DIR)
            return


def clean_gui_audit_artifacts() -> None:
    """清理 GUI 渲染审计保留的临时截图目录。"""
    remove_path(RUNTIME_DIR / "release_gui_audit")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--purge-prefix", action="append", default=[])
    parser.add_argument("--candidate-id", action="append", default=[])
    parser.add_argument("--case-id", action="append", default=[], help="保留兼容参数；不会删除正式案例 JSON")
    args = parser.parse_args()

    clean_python_caches()
    clean_abaqus_session_files()
    clean_contaminated_vector_index()
    clean_gui_audit_artifacts()
    purge_business_records(args.candidate_id, args.case_id)
    purge_problem_prefixes(args.purge_prefix)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

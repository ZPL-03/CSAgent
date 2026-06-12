"""CSAgent 发布审计门禁。

该脚本检查项目是否满足可发布快照的基础契约，包括品牌残留、缓存残留、
案例编号、知识库运行时路径、UI 展示资产、报告标题和本地密钥忽略规则。
默认不访问网络；需要检查 LLM 连通性时使用 ``--with-llm-health``。
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.dont_write_bytecode = True
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.schema_validator import validate_or_raise


FORBIDDEN_TEXT = [
    "MechAgent",
    "mimo-v2.5-pro",
    "token-plan-cn",
    "tp-ct",
    "PBIPF 带 Q",
    "带Q公式",
    "专利",
    "knowledge/external",
    "external_knowledge",
    "avatarBadge",
    "VerｄDict",
    "VerdDict",
    "CSDM_cph 运行审计报告",
    "CSDM_cph 耐压壳设计报告",
]

TEXT_SUFFIXES = {
    ".py",
    ".md",
    ".json",
    ".yaml",
    ".yml",
    ".txt",
    ".csv",
    ".schema",
}

EXCLUDED_SCAN_DIRS = {
    ".git",
    "reference",
    "knowledge/chroma_db",
    "knowledge/runtime",
    "data/abaqus_runs",
    "data/runtime",
    "data/io",
    "data/tasks",
}

EXCLUDED_SCAN_FILES = {
    "scripts/release_audit.py",
}

REQUIRED_UI_ASSETS = [
    "docs/assets/ui_workbench_dark.png",
    "docs/assets/ui_workbench_light.png",
    "docs/assets/ui_knowledge_dark.png",
    "docs/assets/ui_monitor_dark.png",
    "docs/assets/ui_settings_dark.png",
]


@dataclass
class AuditItem:
    name: str
    passed: bool
    detail: str


class ReleaseAudit:
    def __init__(self, with_llm_health: bool = False) -> None:
        self.with_llm_health = with_llm_health
        self.items: list[AuditItem] = []

    def add(self, name: str, passed: bool, detail: str) -> None:
        self.items.append(AuditItem(name=name, passed=passed, detail=detail))

    def run(self) -> int:
        self.check_clean_residuals()
        self.check_cache_absent()
        self.check_env_ignored()
        self.check_runtime_knowledge_paths()
        self.check_ui_assets()
        self.check_cases()
        self.check_latest_report()
        if self.with_llm_health:
            self.check_llm_health()

        for item in self.items:
            status = "PASS" if item.passed else "FAIL"
            print(f"[{status}] {item.name}: {item.detail}")
        return 0 if all(item.passed for item in self.items) else 1

    def _iter_text_files(self) -> Iterable[Path]:
        for path in ROOT.rglob("*"):
            if not path.is_file():
                continue
            relative = path.relative_to(ROOT).as_posix()
            if relative in EXCLUDED_SCAN_FILES:
                continue
            if any(relative == excluded or relative.startswith(f"{excluded}/") for excluded in EXCLUDED_SCAN_DIRS):
                continue
            if path.suffix.lower() in TEXT_SUFFIXES or path.name == ".gitignore":
                yield path

    def check_clean_residuals(self) -> None:
        hits: list[str] = []
        for path in self._iter_text_files():
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            for pattern in FORBIDDEN_TEXT:
                if pattern in text:
                    hits.append(f"{path.relative_to(ROOT)}:{pattern}")
        self.add("旧残留关键词", not hits, "未发现旧品牌、旧模型、旧路径和异常文本残留" if not hits else "; ".join(hits[:12]))

    def check_cache_absent(self) -> None:
        caches = [path.relative_to(ROOT).as_posix() for path in ROOT.rglob("__pycache__")]
        pytest_cache = ROOT / ".pytest_cache"
        if pytest_cache.exists():
            caches.append(".pytest_cache")
        self.add("缓存目录", not caches, "无 __pycache__ / .pytest_cache" if not caches else ", ".join(caches[:12]))

    def _git_output(self, args: list[str]) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", *args],
            cwd=ROOT,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            check=False,
        )

    def check_env_ignored(self) -> None:
        tracked = self._git_output(["ls-files", ".env"])
        ignored = self._git_output(["check-ignore", "-q", ".env"])
        passed = tracked.stdout.strip() == "" and ignored.returncode == 0
        detail = ".env 未跟踪且被 .gitignore 忽略" if passed else f"tracked={tracked.stdout.strip()!r}, ignored_rc={ignored.returncode}"
        self.add("本地密钥文件", passed, detail)

    def check_runtime_knowledge_paths(self) -> None:
        config = yaml.safe_load((ROOT / "config/app_config.yaml").read_text(encoding="utf-8"))
        knowledge = dict((config or {}).get("project_knowledge", {}))
        required = {
            "base_dir": "knowledge/runtime",
            "upload_dir": "knowledge/runtime/uploads",
            "rag_chunks_path": "knowledge/runtime/rag/rag_chunks.jsonl",
            "vector_chroma_dir": "knowledge/chroma_db",
        }
        mismatches = [f"{key}={knowledge.get(key)!r}" for key, expected in required.items() if knowledge.get(key) != expected]
        external_exists = (ROOT / "knowledge/external").exists()
        passed = not mismatches and not external_exists
        detail = "知识库运行事实源为 knowledge/runtime + knowledge/chroma_db" if passed else "; ".join([*mismatches, f"knowledge/external exists={external_exists}"])
        self.add("知识库运行时路径", passed, detail)

    def check_ui_assets(self) -> None:
        missing = [asset for asset in REQUIRED_UI_ASSETS if not (ROOT / asset).is_file()]
        self.add("UI 展示资产", not missing, "主工作台、知识库、监控、设置截图齐全" if not missing else ", ".join(missing))

    def check_cases(self) -> None:
        case_dir = ROOT / "data/cases"
        paths = sorted(case_dir.glob("CASE_*.json"), key=lambda item: int(item.stem.split("_")[1]))
        if not paths:
            self.add("案例库编号", False, "data/cases 为空")
            return

        errors: list[str] = []
        for index, path in enumerate(paths, start=1):
            data = json.loads(path.read_text(encoding="utf-8"))
            try:
                validate_or_raise("case_record.schema.json", data)
                validate_or_raise("abaqus_result.schema.json", data.get("abaqus_results") or {})
            except Exception as exc:
                errors.append(f"{path.name}: {exc}")
                continue
            expected_case = f"CASE_{index}"
            expected_candidate = f"C{index}"
            design = data.get("design") or {}
            result = data.get("abaqus_results") or {}
            if data.get("case_id") != expected_case:
                errors.append(f"{path.name}: case_id={data.get('case_id')}")
            if data.get("candidate_id") != expected_candidate or data.get("display_name") != expected_candidate:
                errors.append(f"{path.name}: 顶层身份不一致")
            if design.get("candidate_id") != expected_candidate or design.get("display_name") != expected_candidate:
                errors.append(f"{path.name}: design 身份不一致")
            if result.get("candidate_id") != expected_candidate:
                errors.append(f"{path.name}: abaqus_results.candidate_id={result.get('candidate_id')}")
            if "????" in path.read_text(encoding="utf-8") or "\ufffd" in path.read_text(encoding="utf-8"):
                errors.append(f"{path.name}: 存在乱码占位符")

        self.add("案例库编号", not errors, f"{len(paths)} 条案例连续且身份一致" if not errors else "; ".join(errors[:12]))

    def check_latest_report(self) -> None:
        report_path = ROOT / "data/results/latest_report.md"
        if not report_path.exists():
            self.add("最新报告", True, "当前没有本地 latest_report.md；报告属于运行时输出")
            return
        text = report_path.read_text(encoding="utf-8")
        passed = text.startswith("# CSAgent 耐压壳设计报告") and "### 工程解释与制造建议" not in text
        detail = "报告标题和工程解释后处理正确" if passed else "报告标题或工程解释标题异常"
        self.add("最新报告", passed, detail)

    def check_llm_health(self) -> None:
        from dotenv import load_dotenv

        from core.llm_status import probe_llm_backends

        load_dotenv(ROOT / ".env")
        results = probe_llm_backends(timeout_seconds=20)
        fallback_ok = any(item.get("role") == "fallback" and item.get("health_status") == "success" for item in results)
        primary = next((item for item in results if item.get("role") == "primary"), {})
        fallback = next((item for item in results if item.get("role") == "fallback"), {})
        detail = (
            f"primary={primary.get('model')}:{primary.get('health_status')}；"
            f"fallback={fallback.get('model')}:{fallback.get('health_status')}"
        )
        self.add("LLM 后端健康", fallback_ok, detail)


def main() -> int:
    parser = argparse.ArgumentParser(description="CSAgent 发布审计门禁")
    parser.add_argument("--with-llm-health", action="store_true", help="同时检查 LLM 主/回退模型连通性")
    args = parser.parse_args()
    return ReleaseAudit(with_llm_health=args.with_llm_health).run()


if __name__ == "__main__":
    raise SystemExit(main())

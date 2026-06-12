"""CSAgent 交付一致性检查。

该脚本检查项目交付状态，包括产品命名一致性、本地运行产物隔离、
案例编号连续性、知识库运行时路径、UI 展示资产、报告标题和本地密钥忽略规则。
默认只读取本地文件；需要检测 LLM 连通性时使用 ``--with-llm-health``。
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


def _join(*parts: str) -> str:
    return "".join(parts)


FORBIDDEN_TEXT = [
    _join("Mech", "Agent"),
    _join("mimo", "-v2.5-pro"),
    _join("token", "-plan-cn"),
    _join("tp", "-ct"),
    _join("PBIPF ", "\u5e26 Q"),
    _join("\u5e26", "Q\u516c\u5f0f"),
    _join("\u4e13", "\u5229"),
    _join("knowledge", "/external"),
    _join("external", "_knowledge"),
    _join("avatar", "Badge"),
    _join("Ver", "\uff44", "Dict"),
    _join("Verd", "Dict"),
    _join("CSDM_cph ", "\u8fd0\u884c\u5ba1\u8ba1\u62a5\u544a"),
    _join("CSDM_cph ", "\u8010\u538b\u58f3\u8bbe\u8ba1\u62a5\u544a"),
    _join("Neo", "4j"),
    _join("\u5916\u90e8", "\u77e5\u8bc6\u5e93"),
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
]

UI_ASSET_SOURCES = [
    "assets/csagent_badge.png",
    "assets/csagent_logo.png",
    "gui/main_window.py",
    "gui/theme.py",
    "gui/workbench_widgets.py",
    "gui/chat_widget.py",
    "gui/knowledge_widget.py",
    "gui/render_utils.py",
    "gui/interactive_view.py",
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
        self.check_product_identity()
        self.check_agent_runtime_contract()
        self.check_runtime_knowledge_paths()
        self.check_runtime_knowledge_status_contract()
        self.check_knowledge_pipeline_contract()
        self.check_knowledge_file_type_contract()
        self.check_gui_workbench_contract()
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
        self.add("产品关键词", not hits, "产品命名、模型名称、运行路径和报告标题一致" if not hits else "; ".join(hits[:12]))

    def check_cache_absent(self) -> None:
        caches = [path.relative_to(ROOT).as_posix() for path in ROOT.rglob("__pycache__")]
        pytest_cache = ROOT / ".pytest_cache"
        if pytest_cache.exists():
            caches.append(".pytest_cache")
        self.add("本地运行产物", not caches, "无 Python 测试缓存目录" if not caches else ", ".join(caches[:12]))

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

    def check_product_identity(self) -> None:
        config = yaml.safe_load((ROOT / "config/app_config.yaml").read_text(encoding="utf-8"))
        project = dict((config or {}).get("project", {}))
        expected = {
            "name": "CSAgent",
            "display_name": "CSAgent 多智能体智能设计平台",
            "package_name": "CSDM_cph",
            "domain": "composite_pressure_hull",
        }
        mismatches = [f"{key}={project.get(key)!r}" for key, value in expected.items() if project.get(key) != value]
        passed = not mismatches
        detail = "产品显示名为 CSAgent，CSDM_cph 仅作为内部包名" if passed else "; ".join(mismatches)
        self.add("产品身份配置", passed, detail)

    def check_agent_runtime_contract(self) -> None:
        from workflow.agent_contracts import list_agent_contracts

        contracts = list_agent_contracts()
        expected_nodes = {
            "parse_task": "ORCHESTRATOR",
            "generate_candidates": "CANDIDATE_GEN",
            "screen_candidates": "SCREENER",
            "evaluate_candidates": "FEM_AGENT",
            "persist_knowledge": "KNOWLEDGE_AGENT",
            "generate_report": "REPORT_GEN",
        }
        by_node = {contract.node_name: contract for contract in contracts}
        errors: list[str] = []
        for node_name, agent_name in expected_nodes.items():
            contract = by_node.get(node_name)
            if contract is None:
                errors.append(f"缺少节点 {node_name}")
                continue
            if contract.runtime_agent != agent_name:
                errors.append(f"{node_name}.runtime_agent={contract.runtime_agent!r}")
        runtime_agents = {contract.runtime_agent for contract in contracts}
        expected_agents = set(expected_nodes.values())
        if runtime_agents != expected_agents:
            errors.append(f"runtime_agents={sorted(runtime_agents)!r}")

        no_llm_nodes = {"parse_task", "screen_candidates", "evaluate_candidates", "persist_knowledge"}
        for node_name in no_llm_nodes:
            policy = by_node.get(node_name).llm_policy if by_node.get(node_name) else ""
            if "不调用 LLM" not in policy:
                errors.append(f"{node_name}.llm_policy={policy!r}")
        candidate_policy = by_node.get("generate_candidates").llm_policy if by_node.get("generate_candidates") else ""
        if "主模型优先" not in candidate_policy or "回退" not in candidate_policy:
            errors.append("候选生成 LLM 策略缺少主模型或回退说明")
        report_policy = by_node.get("generate_report").llm_policy if by_node.get("generate_report") else ""
        if "工程解释" not in report_policy or "数值" not in report_policy:
            errors.append("报告生成 LLM 策略缺少工程解释或数值边界")

        runtime_text = (ROOT / "workflow/runtime.py").read_text(encoding="utf-8")
        event_store_text = (ROOT / "workflow/event_store.py").read_text(encoding="utf-8")
        simulation_queue_text = (ROOT / "workflow/simulation_queue.py").read_text(encoding="utf-8")
        runtime_tokens = [
            "wait_screen",
            "wait_fem",
            "wait_report",
            "resume",
            "continue_after_confirmation",
            "simulation_queue",
            "WorkflowEventStore",
            "ToolRegistry",
        ]
        for token in runtime_tokens:
            if token not in runtime_text:
                errors.append(f"workflow/runtime.py 缺少 {token}")
        if "workflow_events" not in event_store_text or "workflow_snapshots" not in event_store_text:
            errors.append("事件库缺少事件或快照表")
        if "simulation_jobs" not in simulation_queue_text:
            errors.append("仿真队列缺少作业表")

        detail = "六智能体契约、LLM 边界、人工确认、快照恢复、工具注册和仿真队列齐备" if not errors else "; ".join(errors[:12])
        self.add("多智能体运行契约", not errors, detail)

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
        external_runtime_path = _join("knowledge", "/external")
        external_exists = (ROOT / external_runtime_path).exists()
        passed = not mismatches and not external_exists
        detail = "知识库运行事实源为 knowledge/runtime + knowledge/chroma_db" if passed else "; ".join([*mismatches, f"{external_runtime_path} exists={external_exists}"])
        self.add("知识库运行时路径", passed, detail)

    def check_runtime_knowledge_status_contract(self) -> None:
        from core.knowledge_ingestion import (
            STEP_CHUNK,
            STEP_KG,
            STEP_PARSE,
            STEP_RETRIEVAL,
            STEP_VECTOR,
            KnowledgeIngestionService,
        )

        status = KnowledgeIngestionService().status()
        required_keys = {
            "store_type",
            "document_count",
            "rag_chunk_count",
            "vector_chunk_count",
            "vector_ready",
            "vector_status",
            "vector_message",
            "vector_detail",
            "vector_backend",
            "kg_entity_count",
            "kg_relation_count",
            "chunk_token_size",
            "chunk_overlap_tokens",
            "min_chunk_tokens",
            "dedupe_key",
            "pipeline",
        }
        missing = [key for key in sorted(required_keys) if key not in status]
        expected_steps = [STEP_PARSE, STEP_CHUNK, STEP_VECTOR, STEP_KG, STEP_RETRIEVAL]
        pipeline = status.get("pipeline") if isinstance(status.get("pipeline"), list) else []
        step_names = [str(step.get("name") or "") for step in pipeline if isinstance(step, dict)]
        errors = list(missing)
        if status.get("store_type") != "project_runtime_knowledge":
            errors.append(f"store_type={status.get('store_type')!r}")
        if status.get("dedupe_key") != "content_hash":
            errors.append(f"dedupe_key={status.get('dedupe_key')!r}")
        if step_names[:5] != expected_steps:
            errors.append(f"pipeline={step_names[:5]!r}")
        detail = "空库和已有库均暴露分块、去重、RAG/KG 计数和五阶段流水线状态" if not errors else "; ".join(errors[:12])
        self.add("知识库状态契约", not errors, detail)

    def check_knowledge_pipeline_contract(self) -> None:
        required_files = [
            ROOT / "core/knowledge_ingestion.py",
            ROOT / "gui/knowledge_widget.py",
            ROOT / "gui/workbench_widgets.py",
            ROOT / "docs/接口约定.md",
            ROOT / "docs/项目全流程梳理.md",
        ]
        missing: list[str] = []
        for path in required_files:
            text = path.read_text(encoding="utf-8")
            if "检索验证 / 证据引用" not in text:
                missing.append(path.relative_to(ROOT).as_posix())
        self.add(
            "知识流水线契约",
            not missing,
            "入库流水线包含解析、分块、向量、KG 和检索验证五阶段" if not missing else ", ".join(missing),
        )

    def check_knowledge_file_type_contract(self) -> None:
        from core.knowledge_ingestion import SUPPORTED_INGEST_SUFFIXES, SUPPORTED_QT_FILE_FILTER

        required_suffixes = {
            ".pdf",
            ".docx",
            ".pptx",
            ".md",
            ".txt",
            ".csv",
            ".tsv",
            ".xlsx",
            ".png",
            ".jpg",
            ".webp",
            ".inp",
            ".for",
            ".sta",
            ".odb",
            ".sim",
            ".cae",
        }
        missing_suffixes = sorted(required_suffixes - set(SUPPORTED_INGEST_SUFFIXES))
        missing_filter = sorted(suffix for suffix in required_suffixes if f"*{suffix}" not in SUPPORTED_QT_FILE_FILTER)
        ingestion_text = (ROOT / "core/knowledge_ingestion.py").read_text(encoding="utf-8")
        parser_tokens = [
            "_parse_with_mineru",
            "_parse_with_docling",
            "_parse_pdf_text",
            "_parse_docx_text",
            "_parse_pptx_text",
            "_parse_image_metadata",
            "_parse_engineering_binary_metadata",
            "_parse_csv_table",
            "_parse_xlsx_table",
        ]
        missing_parser_tokens = [token for token in parser_tokens if token not in ingestion_text]
        errors = [
            *(f"suffix:{suffix}" for suffix in missing_suffixes),
            *(f"filter:{suffix}" for suffix in missing_filter),
            *(f"parser:{token}" for token in missing_parser_tokens),
        ]
        detail = "上传入口覆盖文档、表格、图片、Abaqus 文本和工程二进制元数据解析契约" if not errors else "; ".join(errors[:12])
        self.add("知识库文件类型契约", not errors, detail)

    def check_gui_workbench_contract(self) -> None:
        files = {
            "main": (ROOT / "gui/main_window.py").read_text(encoding="utf-8"),
            "knowledge": (ROOT / "gui/knowledge_widget.py").read_text(encoding="utf-8"),
            "interactive": (ROOT / "gui/interactive_view.py").read_text(encoding="utf-8"),
            "i18n": (ROOT / "gui/i18n.py").read_text(encoding="utf-8"),
            "workbench": (ROOT / "gui/workbench_widgets.py").read_text(encoding="utf-8"),
            "chat": (ROOT / "gui/chat_widget.py").read_text(encoding="utf-8"),
        }
        required_tokens = {
            "main": [
                "QStackedWidget",
                "nav.workbench",
                "nav.project",
                "nav.knowledge",
                "nav.monitor",
                "nav.settings",
                "FlowDagWidget",
                "ChatWidget",
                "InteractivePlotWidget",
                "_build_settings_page",
                "settings_fields",
                "_save_settings_from_page",
                "_reload_settings_page",
                "report_button",
                "export_data_button",
                "open_report_button",
            ],
            "workbench": [
                "ORCHESTRATOR",
                "CANDIDATE_GEN",
                "SCREENER",
                "FEM_AGENT",
                "KNOWLEDGE_AGENT",
                "REPORT_GEN",
                "FlowDagWidget",
            ],
            "knowledge": [
                "graph_search_input",
                "graph_reset_button",
                "set_filter_text",
                "wheelEvent",
                "mousePressEvent",
                "mouseMoveEvent",
                "mouseDoubleClickEvent",
                "ingest_paths",
            ],
            "interactive": ["reset_view", "fit_view", "show_reference_hull", "show_candidate"],
            "i18n": ["nav.workbench", "nav.settings", "Workbench", "Settings"],
            "chat": ["ChatWidget", "ScrollBarAsNeeded", "fit_content"],
        }
        missing: list[str] = []
        for name, tokens in required_tokens.items():
            text = files[name]
            for token in tokens:
                if token not in text:
                    missing.append(f"{name}:{token}")
        detail = "五页导航、六智能体 DAG、对话区、实时视口、知识图谱交互和设置页配置入口齐备" if not missing else "; ".join(missing[:12])
        self.add("GUI 工作台契约", not missing, detail)

    def check_ui_assets(self) -> None:
        missing = [asset for asset in REQUIRED_UI_ASSETS if not (ROOT / asset).is_file()]
        if missing:
            self.add("UI 展示资产", False, ", ".join(missing))
            return
        asset_paths = [ROOT / asset for asset in REQUIRED_UI_ASSETS]
        source_paths = [ROOT / path for path in UI_ASSET_SOURCES]
        missing_sources = [path.relative_to(ROOT).as_posix() for path in source_paths if not path.exists()]
        invalid_assets: list[str] = []
        for path in asset_paths:
            data = path.read_bytes()
            if len(data) < 4096 or not data.startswith(b"\x89PNG\r\n\x1a\n"):
                invalid_assets.append(path.relative_to(ROOT).as_posix())
        errors = [*missing_sources, *invalid_assets]
        detail = "主工作台深色展示图和 UI 源文件齐备" if not errors else "; ".join(errors)
        self.add("UI 展示资产", not errors, detail)

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
        primary_ok = any(item.get("role") == "primary" and item.get("health_status") == "success" for item in results)
        fallback_ok = any(item.get("role") == "fallback" and item.get("health_status") == "success" for item in results)
        primary = next((item for item in results if item.get("role") == "primary"), {})
        fallback = next((item for item in results if item.get("role") == "fallback"), {})
        detail = (
            f"primary={primary.get('model')}:{primary.get('health_status')}；"
            f"fallback={fallback.get('model')}:{fallback.get('health_status')}"
        )
        self.add("LLM 后端健康", primary_ok and fallback_ok, detail)


def main() -> int:
    parser = argparse.ArgumentParser(description="CSAgent 交付一致性检查")
    parser.add_argument("--with-llm-health", action="store_true", help="同时检查 LLM 主/回退模型连通性")
    args = parser.parse_args()
    return ReleaseAudit(with_llm_health=args.with_llm_health).run()


if __name__ == "__main__":
    raise SystemExit(main())

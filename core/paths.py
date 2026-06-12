"""项目路径与目录工具。"""

from __future__ import annotations
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = ROOT_DIR / "config"
SCHEMA_DIR = ROOT_DIR / "schemas"
DATA_DIR = ROOT_DIR / "data"
ASSETS_DIR = ROOT_DIR / "assets"
IO_DIR = DATA_DIR / "io"
TASKS_DIR = DATA_DIR / "tasks"
RESULTS_DIR = DATA_DIR / "results"
CASES_DIR = DATA_DIR / "cases"
ABAQUS_RUNS_DIR = DATA_DIR / "abaqus_runs"
RUNTIME_DIR = DATA_DIR / "runtime"
KNOWLEDGE_DIR = ROOT_DIR / "knowledge"
RUNTIME_KNOWLEDGE_DIR = KNOWLEDGE_DIR / "runtime"
KNOWLEDGE_UPLOADS_DIR = RUNTIME_KNOWLEDGE_DIR / "uploads"
RUNTIME_KNOWLEDGE_RAG_DIR = RUNTIME_KNOWLEDGE_DIR / "rag"
RUNTIME_KNOWLEDGE_KG_DIR = RUNTIME_KNOWLEDGE_DIR / "kg"
RUNTIME_KNOWLEDGE_STRUCTURED_DIR = RUNTIME_KNOWLEDGE_DIR / "structured_text"
CHROMA_DIR = KNOWLEDGE_DIR / "chroma_db"
CASE_LIBRARY_DIR = KNOWLEDGE_DIR / "case_library"
MODELS_DIR = ROOT_DIR / "models"
DOCS_DIR = ROOT_DIR / "docs"
ABAQUS_DIR = ROOT_DIR / "abaqus"
ABAQUS_TEMPLATE_DIR = ABAQUS_DIR / "templates"


def ensure_project_dirs() -> None:
    """确保项目运行所需目录存在。"""
    for path in [
        DATA_DIR,
        ASSETS_DIR,
        IO_DIR,
        TASKS_DIR,
        RESULTS_DIR,
        CASES_DIR,
        ABAQUS_RUNS_DIR,
        RUNTIME_DIR,
        KNOWLEDGE_DIR,
        RUNTIME_KNOWLEDGE_DIR,
        KNOWLEDGE_UPLOADS_DIR,
        RUNTIME_KNOWLEDGE_RAG_DIR,
        RUNTIME_KNOWLEDGE_KG_DIR,
        RUNTIME_KNOWLEDGE_STRUCTURED_DIR,
        CHROMA_DIR,
        CASE_LIBRARY_DIR,
        MODELS_DIR,
        DOCS_DIR,
        ABAQUS_DIR,
        ABAQUS_TEMPLATE_DIR,
    ]:
        path.mkdir(parents=True, exist_ok=True)

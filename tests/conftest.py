from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def isolated_ui_settings(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    monkeypatch.setenv("CSDM_cph_UI_SETTINGS", str(tmp_path / "ui_settings.json"))
    monkeypatch.setenv("CSDM_cph_USE_HASH_EMBEDDING", "1")


@pytest.fixture(autouse=True)
def isolated_task_records(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    """受控测试不得把任务写入正式运行目录。"""
    import core.id_utils as ids
    import agents.orchestrator as orchestrator
    import agents.fem_agent as fem
    import agents.knowledge_agent as knowledge
    import core.case_retriever as retriever
    import core.rag_engine as rag
    import core.surrogate_model as surrogate
    from core.config_loader import load_app_config

    task_dir = tmp_path / "tasks"
    task_dir.mkdir()
    monkeypatch.setattr(ids, "TASKS_DIR", task_dir)
    monkeypatch.setattr(ids, "IO_DIR", tmp_path / "io")
    monkeypatch.setattr(ids, "ABAQUS_RUNS_DIR", tmp_path / "abaqus_runs")
    monkeypatch.setattr(orchestrator, "TASKS_DIR", task_dir)
    monkeypatch.setattr(orchestrator, "IO_DIR", tmp_path / "io")
    monkeypatch.setattr(fem, "IO_DIR", tmp_path / "io")
    monkeypatch.setattr(fem, "ABAQUS_RUNS_DIR", tmp_path / "abaqus_runs")
    for module in (ids, knowledge, retriever):
        monkeypatch.setattr(module, "CASES_DIR", tmp_path / "cases")
        monkeypatch.setattr(module, "CASE_LIBRARY_DIR", tmp_path / "library")
    monkeypatch.setattr(surrogate, "CASES_DIR", tmp_path / "cases")
    monkeypatch.setattr(surrogate, "MODELS_DIR", tmp_path / "models")
    monkeypatch.setattr(rag, "CHROMA_DIR", tmp_path / "chroma")
    monkeypatch.setitem(load_app_config()["project_knowledge"], "vector_chroma_dir", str(tmp_path / "chroma"))
    monkeypatch.setitem(load_app_config()["project_knowledge"], "builtin_dense_enabled", False)

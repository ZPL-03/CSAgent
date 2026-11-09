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

    task_dir = tmp_path / "tasks"
    task_dir.mkdir()
    monkeypatch.setattr(ids, "TASKS_DIR", task_dir)
    monkeypatch.setattr(orchestrator, "TASKS_DIR", task_dir)
    monkeypatch.setattr(orchestrator, "IO_DIR", tmp_path / "io")
    monkeypatch.setattr(fem, "IO_DIR", tmp_path / "io")

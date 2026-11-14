from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path
import os

import pytest


ROOT = Path(__file__).resolve().parent.parent


def _clean_test_caches() -> None:
    from scripts.clean_artifacts import python_cache_paths, remove_path

    for path in python_cache_paths():
        remove_path(path)


def test_release_audit_reports_caches_without_removing_them(monkeypatch, tmp_path):
    from scripts import release_audit

    paths = [tmp_path / "__pycache__", tmp_path / ".pytest_cache", tmp_path / ".ruff_cache"]
    for path in paths:
        path.mkdir()
    bytecode = tmp_path / "module.pyc"
    bytecode.write_bytes(b"cached")
    monkeypatch.setattr(release_audit, "ROOT", tmp_path)
    audit = release_audit.ReleaseAudit()
    audit.check_cache_absent()
    assert not audit.items[-1].passed
    assert all(path.exists() for path in [*paths, bytecode])
    assert "module.pyc" in audit.items[-1].detail


@pytest.mark.parametrize("create_directories", [False, True])
def test_release_audit_accepts_empty_case_store(monkeypatch, tmp_path, create_directories):
    from scripts import release_audit

    if create_directories:
        (tmp_path / "data/cases").mkdir(parents=True)
        (tmp_path / "knowledge/case_library").mkdir(parents=True)
    monkeypatch.setattr(release_audit, "ROOT", tmp_path)
    audit = release_audit.ReleaseAudit()
    audit.check_cases()
    assert audit.items[-1].passed
    assert "案例库为空" in audit.items[-1].detail


def test_release_audit_rejects_orphan_migration_case(monkeypatch, tmp_path):
    from scripts import release_audit

    library = tmp_path / "knowledge/case_library"
    library.mkdir(parents=True)
    (library / "CASE_1.json").write_text("{}", encoding="utf-8")
    monkeypatch.setattr(release_audit, "ROOT", tmp_path)
    audit = release_audit.ReleaseAudit()
    audit.check_cases()
    assert not audit.items[-1].passed


def test_release_audit_rejects_incomplete_case_record(monkeypatch, tmp_path):
    from scripts import release_audit

    cases = tmp_path / "data/cases"
    cases.mkdir(parents=True)
    (cases / "CASE_1.json").write_text("{}", encoding="utf-8")
    monkeypatch.setattr(release_audit, "ROOT", tmp_path)
    audit = release_audit.ReleaseAudit()
    audit.check_cases()
    assert not audit.items[-1].passed


def test_release_audit_passes_without_network() -> None:
    _clean_test_caches()
    result = subprocess.run(
        [sys.executable, "scripts/release_audit.py"],
        cwd=ROOT,
        env={**os.environ, "PYTHONIOENCODING": "utf-8"},
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "[PASS] 产品关键词" in result.stdout
    assert "[PASS] 本地运行产物" in result.stdout
    assert "[PASS] 产品身份配置" in result.stdout
    assert "[PASS] 多智能体运行契约" in result.stdout
    assert "[PASS] 知识库状态契约" in result.stdout
    assert "[PASS] 知识流水线契约" in result.stdout
    assert "[PASS] 知识库文件类型契约" in result.stdout
    assert "[PASS] GUI 工作台契约" in result.stdout
    assert "[PASS] 案例库编号" in result.stdout
    assert "[PASS] UI 展示资产" in result.stdout


def test_release_audit_gui_render_passes_without_artifacts() -> None:
    _clean_test_caches()
    screenshot_dir = ROOT / "data/runtime/release_gui_audit"
    if screenshot_dir.exists():
        shutil.rmtree(screenshot_dir)
    result = subprocess.run(
        [sys.executable, "scripts/release_audit.py", "--with-gui-render"],
        cwd=ROOT,
        env={**os.environ, "PYTHONIOENCODING": "utf-8"},
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "[PASS] GUI 渲染审计" in result.stdout
    assert not screenshot_dir.exists()

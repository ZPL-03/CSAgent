from __future__ import annotations

import json

import pytest

from scripts import clean_artifacts


def test_cleanup_rejects_invalid_candidate_paths():
    for value in ("../config", "CASE_1", "C1/..", "C1_suffix", "", "C0", " C7", "C7 "):
        with pytest.raises(ValueError):
            clean_artifacts.candidate_artifact_paths(value)


def test_cleanup_preserves_case_referenced_solver_artifacts(monkeypatch, tmp_path):
    cases = tmp_path / "cases"
    cases.mkdir()
    (cases / "CASE_1.json").write_text(json.dumps({"candidate_id": "C7"}), encoding="utf-8")
    monkeypatch.setattr(clean_artifacts, "CASES_DIR", cases)
    with pytest.raises(ValueError, match="仍被案例引用"):
        clean_artifacts.unreferenced_candidate_paths(["C7"])
    with pytest.raises(ValueError, match="无效求解编号"):
        clean_artifacts.unreferenced_candidate_paths([" C7 "])


def test_cleanup_rejects_project_root_and_outside_path(tmp_path):
    with pytest.raises(ValueError, match="越界"):
        clean_artifacts.remove_path(tmp_path)
    with pytest.raises(ValueError, match="越界"):
        clean_artifacts.remove_path(clean_artifacts.ROOT)


def test_cleanup_preserves_locked_solver_directory(monkeypatch, tmp_path):
    cases = tmp_path / "cases"
    cases.mkdir()
    runs = tmp_path / "runs"
    (runs / "C7").mkdir(parents=True)
    (runs / "C7/job.lck").touch()
    monkeypatch.setattr(clean_artifacts, "CASES_DIR", cases)
    monkeypatch.setattr(clean_artifacts, "ABAQUS_RUNS_DIR", runs)
    with pytest.raises(ValueError, match="作业锁"):
        clean_artifacts.unreferenced_candidate_paths(["C7"])
    assert (runs / "C7/job.lck").exists()


def test_cleanup_defaults_to_preview_and_never_sweeps_solver_files(monkeypatch, tmp_path):
    cache = tmp_path / ".pytest_cache"
    cache.mkdir()
    solver = tmp_path / "abaqus_runs/C1"
    solver.mkdir(parents=True)
    for name in ("job.lck", "job.prt", "job.sim", "abaqus.rpy", "build_model.py"):
        (solver / name).touch()
    monkeypatch.setattr(clean_artifacts, "ROOT", tmp_path)
    monkeypatch.setattr(clean_artifacts, "CASES_DIR", tmp_path / "cases")
    monkeypatch.setattr(clean_artifacts.sys, "argv", ["clean_artifacts.py"])
    assert clean_artifacts.main() == 0
    assert cache.exists()
    monkeypatch.setattr(clean_artifacts.sys, "argv", ["clean_artifacts.py", "--apply"])
    assert clean_artifacts.main() == 0
    assert not cache.exists()
    assert len(list(solver.iterdir())) == 5

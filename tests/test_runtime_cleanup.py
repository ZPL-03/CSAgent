from __future__ import annotations

import json

import pytest

from scripts import clean_artifacts


def test_cleanup_rejects_invalid_candidate_paths():
    for value in ("../config", "CASE_1", "C1/..", "C1_suffix", "", "C0"):
        with pytest.raises(ValueError):
            clean_artifacts.candidate_artifact_paths(value)


def test_cleanup_preserves_case_referenced_solver_artifacts(monkeypatch, tmp_path):
    cases = tmp_path / "cases"
    cases.mkdir()
    (cases / "CASE_1.json").write_text(json.dumps({"candidate_id": "C7"}), encoding="utf-8")
    monkeypatch.setattr(clean_artifacts, "CASES_DIR", cases)
    with pytest.raises(ValueError, match="仍被案例引用"):
        clean_artifacts.purge_business_records(["C7"])


def test_cleanup_rejects_project_root_and_outside_path(tmp_path):
    with pytest.raises(ValueError, match="越界"):
        clean_artifacts.remove_path(tmp_path)
    with pytest.raises(ValueError, match="越界"):
        clean_artifacts.remove_path(clean_artifacts.ROOT)

from __future__ import annotations

import json
import hashlib
import re
from pathlib import Path

from core.fem_result_semantics import complete_case_result_errors, required_fem_artifact_fields, result_semantic_errors, verified_capacity_pressure
from core.paths import CASES_DIR, resolve_project_path
from core.schema_validator import validate_or_raise
from gui.render_utils import mode_shape_payload_status


def _case_number(path: Path) -> int:
    match = re.fullmatch(r"CASE_([0-9]+)\.json", path.name)
    assert match is not None
    return int(match.group(1))


def _load_cases() -> list[tuple[Path, dict]]:
    paths = sorted(CASES_DIR.glob("CASE_*.json"), key=_case_number)
    assert paths, "正式案例库不能为空"
    return [(path, json.loads(path.read_text(encoding="utf-8"))) for path in paths]


def test_case_library_numbering_and_fem_artifacts_are_consistent() -> None:
    cases = _load_cases()
    expected_numbers = list(range(1, len(cases) + 1))
    assert [_case_number(path) for path, _ in cases] == expected_numbers

    for index, (path, case_record) in enumerate(cases, start=1):
        validate_or_raise("case_record.schema.json", case_record)
        result = case_record.get("abaqus_results") or {}
        validate_or_raise("abaqus_result.schema.json", result)

        case_id = f"CASE_{index}"
        candidate_id = case_record["candidate_id"]
        assert re.fullmatch(r"C[1-9][0-9]*", candidate_id)
        design = case_record.get("design") or {}
        assert case_record["case_id"] == case_id
        assert case_record.get("candidate_id") == candidate_id
        assert case_record.get("display_name") == candidate_id
        assert design.get("candidate_id") == candidate_id
        assert design.get("display_name") == candidate_id
        assert result.get("candidate_id") == candidate_id
        assert result.get("status") in {"success", "failed", "max_retries_exceeded"}
        assert not result_semantic_errors(result)
        assert not complete_case_result_errors(result)
        for field in ("run_id", "task_id", "session_candidate_id"):
            values = [item.get(field) for item in (case_record, design, result)]
            if any(values):
                assert all(values) and len(set(values)) == 1, (path.name, field)
        capacity_pressure = verified_capacity_pressure(result)
        if capacity_pressure is not None:
            assert capacity_pressure > 0
        assert isinstance(result.get("linear_buckling_pressure_MPa"), (int, float))
        assert result["linear_buckling_pressure_MPa"] > 0

        for key in required_fem_artifact_fields(result):
            artifact = result.get(key)
            assert artifact, f"{path.name} 缺少 {key}"
            artifact_path = resolve_project_path(artifact)
            assert artifact_path is not None
            assert artifact_path.exists(), f"{path.name} 的 {key} 文件不存在：{artifact_path}"
            assert artifact_path.is_file()
            assert artifact_path.stat().st_size > 0
        for path_field, hash_field in (("user_subroutine_path", "user_subroutine_sha256"),
                                       ("material_strength_include", "material_strength_sha256")):
            artifact_path = resolve_project_path(result[path_field])
            assert hashlib.sha256(artifact_path.read_bytes()).hexdigest() == result[hash_field]

        mode_status = mode_shape_payload_status(result)
        assert mode_status["available"] is True
        assert mode_status["points"] > 0
        assert mode_status["faces"] > 0


def test_case_library_contains_no_mojibake_placeholders() -> None:
    for path, _case_record in _load_cases():
        text = path.read_text(encoding="utf-8")
        assert "?" * 4 not in text
        assert "\ufffd" not in text

from copy import deepcopy
import hashlib
import json

import pytest

from core.fem_candidate_transfer import (
    FEMCandidateTransferError,
    FEM_SOURCE_TABLE_SHA256,
    build_fem_ready_task_record,
    validate_fem_ready_response,
    adapt_imported_candidate,
    import_fem_ready_response,
)
from core.fem_input_contract import attach_design_revision


def _candidate(index: int) -> dict:
    candidate = {
        "contract_version": "1",
        "candidate_id": f"TMP_{index}",
        "display_name": f"TMP_{index}",
        "source": "CASE_TRANSFER",
        "hull_type": "CYLINDRICAL",
        "geometry": {
            "length_mm": 600.0,
            "radius_mm": 150.0,
            "thickness_mm": 20.0,
            "alpha_deg": 25.0 + index,
            "beta_deg": 80.0,
            "imperfection_ratio": 0.008,
        },
        "layup": {
            "skin_layup": "explicit",
            "ply_count": 4,
            "ply_thickness_mm": 5.0,
            "angles_deg": [25.0 + index, -(25.0 + index), 80.0, -80.0],
            "balanced": True,
            "symmetric": False,
        },
        "load_conditions": {"type": "external_pressure", "external_pressure_MPa": 50.259081},
        "boundary_conditions": {"type": "FLANGE_CONSTRAINED"},
        "material_system": {
            "name": "M40J/TDE-85",
            "material_key": "M40J_TDE_85",
            "density_kg_per_m3": 1600.0,
            "E1_GPa": 218.0,
            "E2_GPa": 9.07,
            "G12_GPa": 6.35,
            "nu12": 0.3,
            "Xt_MPa": 2088.0,
            "Xc_MPa": 1212.0,
            "Yt_MPa": 22.5,
            "Yc_MPa": 196.0,
            "S_MPa": 61.1,
        },
        "design_targets": {"primary_objective": "最小壳体质量"},
        "analysis": {"analysis_type": "linear_buckling_plus_first_mode_imperfection_riks"},
        "provenance": {
            "source_sha256": FEM_SOURCE_TABLE_SHA256,
            "geometry_match": "exact",
            "historical_fem_reference": {
                "ultimate_pressure_MPa": 60.0,
                "status": "screening_reference_only_not_current_run",
            },
        },
        "screening": {
            "candidate_role": "historically_screened_baseline",
            "historical_reference_comparison": "at_or_above_target_for_same_geometry",
            "historical_reference_meets_target_at_source_geometry": True,
            "current_abaqus_status": "not_run",
            "current_design_verdict": "pending",
        },
    }
    return attach_design_revision(candidate)


def _response() -> dict:
    candidates = [_candidate(1), _candidate(2)]
    source_table = {"sha256": FEM_SOURCE_TABLE_SHA256, "row_count": 5857}
    request = {"schema_version": "2", "candidate_count": 2}
    seed = {"request": request, "source_table": source_table, "candidates": candidates}
    fingerprint = hashlib.sha256(
        json.dumps(seed, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return {
        "status": "passed",
        "contract_version": "1",
        "generation_mode": "fem_ready_cylindrical_shell",
        "result": {
            "schema_version": "2",
            "contract_version": "1",
            "generation_mode": "fem_ready_cylindrical_shell",
            "request": request,
            "source_table": source_table,
            "candidate_count": 2,
            "candidates": candidates,
            "design_fingerprint": fingerprint,
        },
    }


def test_valid_fem_ready_response_imports_without_markdown_parsing() -> None:
    candidates = validate_fem_ready_response(_response())

    assert [item["candidate_id"] for item in candidates] == ["TMP_1", "TMP_2"]
    assert len({item["design_revision_id"] for item in candidates}) == 2


def test_analysis_adaptation_preserves_source_and_invalidates_historical_equivalence():
    from core.config_loader import load_app_config
    from core.fem_input_contract import validate_fem_input

    source = _candidate(1)
    source["geometry"]["imperfection_ratio"] = 0.003
    source["analysis"]["use_user_subroutine"] = False
    source = attach_design_revision(source)
    original = deepcopy(source)
    adapted = adapt_imported_candidate(source)
    assert source == original
    assert adapted["geometry"]["imperfection_ratio"] == 0.008
    assert adapted["geometry"]["radius_reference"] == "inner"
    assert adapted["analysis"]["use_user_subroutine"] == load_app_config()["abaqus"]["use_user_subroutine"]
    assert adapted["parent_design_revision_id"] == source["design_revision_id"]
    assert adapted["design_revision_id"] != source["design_revision_id"]
    assert adapted["provenance"]["source_geometry"] == source["geometry"]
    assert adapted["provenance"]["historical_fem_reference"] == source["provenance"]["historical_fem_reference"]
    assert adapted["screening"]["candidate_role"] == "analysis_condition_transfer_exploration"
    assert validate_fem_input(adapted) == []


def test_import_separates_source_and_analysis_fingerprints(tmp_path):
    response = _response()
    path = tmp_path / "source.json"
    path.write_text(json.dumps(response), encoding="utf-8")
    imported = import_fem_ready_response(path, tmp_path / "imported.json")["payload"]
    assert imported["source_design_fingerprint"] == response["result"]["design_fingerprint"]
    assert imported["design_fingerprint"] != imported["source_design_fingerprint"]
    assert json.loads(path.read_text(encoding="utf-8")) == response


def test_import_uses_user_defect_and_keeps_historical_geometry(tmp_path, monkeypatch):
    import core.fem_candidate_transfer as transfer

    response = _response()
    first = response["result"]["candidates"][0]
    first["provenance"]["source_geometry"] = {"length_mm": 500, "radius_mm": 140, "imperfection_ratio": 0.002}
    result = response["result"]
    result["request"]["geometry"] = {"length_mm": 600, "radius_mm": 150}
    result["design_fingerprint"] = transfer._fingerprint({key: result[key] for key in ("request", "source_table", "candidates")})
    source = tmp_path / "source.json"
    source.write_text(json.dumps(response), encoding="utf-8")
    payload = import_fem_ready_response(source, tmp_path / "import.json", imperfection_ratio=0.005)["payload"]
    assert all(candidate["geometry"]["imperfection_ratio"] == 0.005 for candidate in payload["candidates"])
    adapted = payload["candidates"][0]
    assert adapted["provenance"]["source_geometry"] == first["provenance"]["source_geometry"]
    assert adapted["provenance"]["imported_geometry"] == first["geometry"]
    assert adapted["parent_design_revision_id"] == first["design_revision_id"]
    monkeypatch.setattr(transfer, "next_task_id", lambda: "TASK_IMPORT")
    task = build_fem_ready_task_record(payload)["task"]
    assert task["geometry_envelope"]["imperfection_ratio"] == [0.005, 0.005]
    assert task["user_input_facts"]["fixed_geometry"]["imperfection_ratio"] == 0.005
    assert json.loads(source.read_text(encoding="utf-8")) == response


def test_import_rejects_duplicates_created_by_fixed_analysis_conditions(tmp_path):
    import core.fem_candidate_transfer as transfer

    response = _response()
    first = response["result"]["candidates"][0]
    second = deepcopy(first)
    second.update(candidate_id="TMP_2", display_name="TMP_2")
    second["geometry"]["imperfection_ratio"] = 0.003
    response["result"]["candidates"][1] = attach_design_revision(second)
    result = response["result"]
    result["design_fingerprint"] = transfer._fingerprint({key: result[key] for key in ("request", "source_table", "candidates")})
    source, output = tmp_path / "source.json", tmp_path / "import.json"
    source.write_text(json.dumps(response), encoding="utf-8")
    with pytest.raises(FEMCandidateTransferError, match="适配后候选重复"):
        import_fem_ready_response(source, output)
    assert not output.exists()


@pytest.mark.parametrize("request_defect,override,expected,source_kind", [
    (None, None, 0.008, "default"), (0.004, None, 0.004, "user"),
    (0.004, 0.006, 0.006, "user"), (None, 0.008, 0.008, "user"),
])
def test_import_condition_priority_reaches_task(tmp_path, monkeypatch, request_defect, override, expected, source_kind):
    import core.fem_candidate_transfer as transfer

    response = _response()
    result = response["result"]
    result["request"]["geometry"] = {"length_mm": 600, "radius_mm": 150}
    if request_defect is not None:
        result["request"]["geometry"]["imperfection_ratio"] = request_defect
    result["design_fingerprint"] = transfer._fingerprint({key: result[key] for key in ("request", "source_table", "candidates")})
    path = tmp_path / "source.json"
    path.write_text(json.dumps(response), encoding="utf-8")
    payload = import_fem_ready_response(path, tmp_path / "imported.json", imperfection_ratio=override)["payload"]
    monkeypatch.setattr(transfer, "next_task_id", lambda: "TASK_IMPORT")
    task = build_fem_ready_task_record(payload)["task"]
    assert task["geometry_envelope"]["imperfection_ratio"] == [expected, expected]
    assert task["analysis_condition_sources"]["imperfection_ratio"] == source_kind
    assert all(candidate["geometry"]["imperfection_ratio"] == expected for candidate in payload["candidates"])


def test_task_builder_does_not_replace_request_condition_with_candidate_values(monkeypatch):
    import core.fem_candidate_transfer as transfer

    monkeypatch.setattr(transfer, "next_task_id", lambda: pytest.fail("条件冲突时不分配任务编号"))
    payload = _response()["result"]
    payload["request"]["geometry"] = {"imperfection_ratio": 0.003}
    with pytest.raises(FEMCandidateTransferError, match="缺陷比与导入分析条件不一致"):
        build_fem_ready_task_record(payload)


def test_validated_response_builds_machine_task_without_markdown_parsing(monkeypatch) -> None:
    import core.fem_candidate_transfer as transfer

    monkeypatch.setattr(transfer, "next_task_id", lambda: "TASK_FEM_READY")
    response = _response()
    response["result"]["request"] = {
        "schema_version": "2",
        "candidate_count": 2,
        "geometry": {"length_mm": 600.0, "radius_mm": 150.0},
        "load_conditions": {"type": "external_pressure", "external_pressure_MPa": 50.259081},
        "boundary_conditions": {"type": "FLANGE_CONSTRAINED"},
        "design_targets": {"primary_objective": "最小壳体质量"},
        "structure_form": "两端金属封头、中间复合材料圆柱壳",
    }
    seed = {
        "request": response["result"]["request"],
        "source_table": response["result"]["source_table"],
        "candidates": response["result"]["candidates"],
    }
    response["result"]["design_fingerprint"] = hashlib.sha256(
        json.dumps(seed, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    payload = {**response["result"], "status": "validated"}

    task = build_fem_ready_task_record(payload)

    assert task["source"] == "csllm_fem_ready"
    assert task["task"]["load_conditions"]["external_pressure_MPa"] == 50.259081
    assert task["task"]["geometry_envelope"]["length_mm"] == [600.0, 600.0]
    assert task["task"]["candidate_generation_preferences"]["total_candidates"] == 2
    assert task["task"]["layup_constraints"]["symmetric"] is True


@pytest.mark.parametrize("mutation", ["source", "revision", "fingerprint", "numbering", "screening"])
def test_fem_ready_response_rejects_tampering(mutation: str) -> None:
    response = deepcopy(_response())
    if mutation == "source":
        response["result"]["source_table"]["sha256"] = "0" * 64
    elif mutation == "revision":
        response["result"]["candidates"][0]["geometry"]["thickness_mm"] = 19.0
    elif mutation == "fingerprint":
        response["result"]["design_fingerprint"] = "0" * 64
    elif mutation == "numbering":
        response["result"]["candidates"][1]["candidate_id"] = "TMP_3"
    else:
        response["result"]["candidates"][0]["screening"]["current_design_verdict"] = "passed"

    with pytest.raises(FEMCandidateTransferError):
        validate_fem_ready_response(response)

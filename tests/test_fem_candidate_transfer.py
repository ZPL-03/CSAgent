from copy import deepcopy
import hashlib
import json

import pytest

from core.fem_candidate_transfer import (
    FEMCandidateTransferError,
    FEM_SOURCE_TABLE_SHA256,
    build_fem_ready_task_record,
    validate_fem_ready_response,
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
        "design_targets": {"ultimate_pressure_min_MPa": 50.259081},
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
        "design_targets": {"ultimate_pressure_min_MPa": 50.259081},
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

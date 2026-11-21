from __future__ import annotations

from copy import deepcopy

import pytest

from abaqus.cylindrical_geometry import radius_reference
from abaqus.runtime_build_pressure_hull import layup_angles, material_payload, validate_runtime_candidate
from agents.fem_agent import FEMAgent
from agents.orchestrator import OrchestratorAgent
from core.config_loader import load_material_db
from core.fem_input_contract import (
    FEMInputValidationError,
    attach_design_revision,
    compute_design_revision_id,
    validate_fem_input,
    validate_fem_input_or_raise,
)
from core.schema_validator import validate_or_raise
from core.task_contract import normalize_task_payload
from core.task_parser import TaskParser


def _generated_candidate() -> dict:
    """合同样本只依赖本项目材料库，逐层输入不依赖相邻项目的代码。"""
    angles = [90.0] * 4 + [25.0, -25.0, 80.0, -80.0] * 8 + [90.0] * 4
    text = "[" + "/".join(f"{angle:g}" for angle in angles) + "]"
    return attach_design_revision({
        "candidate_id": "TMP_1",
        "display_name": "TMP_1",
        "source": "CASE_TRANSFER",
        "hull_type": "CYLINDRICAL",
        "geometry": {
            "length_mm": 600.0, "radius_mm": 150.0, "radius_reference": "inner",
            "thickness_mm": 20.0, "alpha_deg": 25.0, "beta_deg": 80.0,
            "imperfection_ratio": 0.008,
        },
        "layup": {
            "template_name": "BASE_90_AB", "layup": text, "skin_layup": text,
            "angles_deg": angles, "ply_count": 40, "ply_thickness_mm": 0.5,
            "balanced": True, "symmetric": False,
        },
        "material_system": {
            **load_material_db()["M40J_TDE_85"],
            "name": "M40J/TDE-85", "material_key": "M40J_TDE_85",
        },
        "load_conditions": {"type": "external_pressure", "external_pressure_MPa": 50.259081},
        "boundary_conditions": {"type": "FLANGE_CONSTRAINED"},
        "design_targets": {"ultimate_pressure_min_MPa": 50.259081},
        "analysis": {"analysis_type": "linear_buckling_plus_first_mode_imperfection_riks"},
    })


def test_cylindrical_candidate_satisfies_schema_and_fem_contract() -> None:
    candidate = _generated_candidate()

    validate_or_raise("candidate.schema.json", candidate)
    assert validate_fem_input(candidate) == []
    assert candidate["design_revision_id"] == compute_design_revision_id(candidate)
    assert len(layup_angles(candidate)) == 40
    assert candidate["layup"]["balanced"] is True
    assert candidate["layup"]["symmetric"] is (
        candidate["layup"]["angles_deg"] == list(reversed(candidate["layup"]["angles_deg"]))
    )
    assert material_payload(candidate)["E1"] > 0
    assert validate_runtime_candidate(candidate)["length"] == 600


def _historical_task(candidate):
    """转交任务沿用候选半径基准，并允许历史提案中的非对称连续角度。"""
    return normalize_task_payload({
        "radius_reference": radius_reference(candidate["geometry"]),
        "load_conditions": candidate["load_conditions"],
        "boundary_conditions": candidate["boundary_conditions"],
        "design_targets": candidate["design_targets"],
        "layup_constraints": {"symmetric": False, "allowed_angles": [], "min_ratio_per_angle": 0},
    })


def test_orchestrator_rejects_task_radius_reference_mismatch(monkeypatch) -> None:
    import agents.orchestrator as module
    candidate = _generated_candidate()
    task = _historical_task(candidate)
    task["radius_reference"] = "middle_surface" if task["radius_reference"] == "inner" else "inner"
    monkeypatch.setattr(module, "reserve_candidate_ids", lambda *_: pytest.fail("半径基准不一致不能分配编号"))
    with pytest.raises(ValueError, match="半径基准"):
        object.__new__(OrchestratorAgent).prepare_candidate_for_fem(task, candidate)


def test_orchestrator_records_task_revision_without_changing_physical_design() -> None:
    candidate = _generated_candidate()
    task = _historical_task(candidate)
    orchestrator = object.__new__(OrchestratorAgent)

    promoted = orchestrator.prepare_candidate_for_fem(task, candidate)

    assert promoted["candidate_id"].startswith("C")
    assert promoted["session_candidate_id"] == "TMP_1"
    assert promoted["design_revision_id"] != candidate["design_revision_id"]
    assert promoted["parent_design_revision_id"] == candidate["design_revision_id"]
    for field in ("geometry", "layup", "material_system", "load_conditions", "boundary_conditions"):
        assert promoted[field] == candidate[field]
    assert promoted["task_constraints"]["layup_constraints"]["symmetric"] is False
    assert validate_fem_input(promoted) == []


def test_new_fem_candidates_require_fixed_defect_before_reserving_ids(monkeypatch) -> None:
    import agents.orchestrator as module
    candidate = _generated_candidate()
    candidate["geometry"]["imperfection_ratio"] = 0.003
    monkeypatch.setattr(module, "reserve_candidate_ids", lambda *_: pytest.fail("无效分析条件不能分配求解编号"))
    orchestrator = object.__new__(OrchestratorAgent)
    with pytest.raises(ValueError, match="0.008"):
        orchestrator.prepare_candidate_for_fem({}, candidate)
    with pytest.raises(ValueError, match="0.008"):
        orchestrator.prepare_candidates_for_fem({}, [candidate])


def test_result_annotation_preserves_actual_solver_design() -> None:
    candidate = _generated_candidate()
    agent = FEMAgent()
    result = agent._annotate_result(candidate, {"status": "failed"})
    assert result["solved_design"]["geometry"] == candidate["geometry"]
    assert result["solved_design"]["layup"] == candidate["layup"]
    assert result["solved_design"]["design_revision_id"] == candidate["design_revision_id"]


def test_missing_fem_fields_fail_closed_instead_of_using_defaults() -> None:
    candidate = _generated_candidate()
    missing_material = deepcopy(candidate)
    del missing_material["material_system"]["E1_GPa"]
    missing_material = attach_design_revision(missing_material)

    with pytest.raises(FEMInputValidationError, match="material_system.E1_GPa"):
        validate_fem_input_or_raise(missing_material)
    with pytest.raises(ValueError, match="material_system.E1_GPa"):
        material_payload(missing_material)

    missing_layup = deepcopy(candidate)
    del missing_layup["layup"]["angles_deg"]
    missing_layup = attach_design_revision(missing_layup)
    with pytest.raises(ValueError, match="layup.angles_deg"):
        layup_angles(missing_layup)


def test_false_layup_declaration_and_material_drift_fail_closed() -> None:
    candidate = _generated_candidate()

    false_symmetry = deepcopy(candidate)
    false_symmetry["layup"]["symmetric"] = not false_symmetry["layup"]["symmetric"]
    false_symmetry = attach_design_revision(false_symmetry)
    assert validate_fem_input(false_symmetry) == ["layup.symmetric"]

    material_drift = deepcopy(candidate)
    material_drift["material_system"]["E1_GPa"] += 1.0
    material_drift = attach_design_revision(material_drift)
    assert validate_fem_input(material_drift) == ["material_system.E1_GPa"]


def test_compact_layup_text_cannot_enter_fem_contract() -> None:
    candidate = _generated_candidate()
    candidate["layup"]["layup"] = "[90_4/(±25/±80)_8/90_4]"
    candidate = attach_design_revision(candidate)

    assert validate_fem_input(candidate) == ["layup.compact_notation"]


def test_orchestrator_expands_compact_layup_at_the_single_fem_boundary() -> None:
    candidate = _generated_candidate()
    candidate["candidate_id"] = "TMP_1"
    candidate["display_name"] = "TMP_1"
    candidate["layup"]["layup"] = "[90_4/(±25/±80)_8/90_4]"
    candidate["layup"]["skin_layup"] = candidate["layup"]["layup"]
    candidate = attach_design_revision(candidate)
    task = _historical_task(candidate)
    orchestrator = object.__new__(OrchestratorAgent)

    promoted = orchestrator.prepare_candidate_for_fem(task, candidate)

    assert validate_fem_input(promoted) == []
    assert "±" not in promoted["layup"]["layup"]
    assert "_4" not in promoted["layup"]["layup"]
    assert promoted["layup"]["ply_count"] == len(promoted["layup"]["angles_deg"])
    assert "90_4" in str(promoted["provenance"]["source_layup"])
    assert promoted["design_revision_id"] != candidate["design_revision_id"]
    assert promoted["parent_design_revision_id"] == candidate["design_revision_id"]


def test_ultimate_pressure_target_cannot_be_below_service_pressure() -> None:
    candidate = _generated_candidate()
    candidate["design_targets"]["ultimate_pressure_min_MPa"] = (
        candidate["load_conditions"]["external_pressure_MPa"] - 1.0
    )
    candidate = attach_design_revision(candidate)

    assert validate_fem_input(candidate) == ["design_targets.ultimate_pressure_min_MPa"]
    with pytest.raises(FEMInputValidationError, match="ultimate_pressure_min_MPa"):
        validate_fem_input_or_raise(candidate)


@pytest.mark.parametrize("failure", ["mesh_error", "geometry_issue", "convergence_fail", "pressure_negative", "process_crash"])
def test_solver_failure_preserves_submitted_design_without_resubmission(monkeypatch, failure) -> None:
    candidate = _generated_candidate()
    candidate["candidate_id"] = "C1"
    candidate["analysis"]["use_user_subroutine"] = False
    candidate = attach_design_revision(candidate)
    original = deepcopy(candidate)
    agent = FEMAgent()
    calls = []
    monkeypatch.setattr("agents.fem_agent.is_abaqus_available", lambda _: True)

    def solve(submitted, result_path):
        calls.append(deepcopy(submitted))
        return agent._empty_result_payload(submitted, "failed", failure)

    monkeypatch.setattr(agent, "_run_real", solve)
    result = agent.run(candidate)
    assert len(calls) == 1
    assert candidate == original
    assert result["status"] == "failed"
    assert result["retry_count"] == 0
    assert result["error_type"] == failure
    assert result["solved_design"]["geometry"] == original["geometry"]
    assert result["solved_design"]["layup"] == original["layup"]
    assert result["solved_design"]["analysis"] == calls[0]["analysis"]
    assert validate_fem_input(calls[0]) == []


def test_task_parser_converts_depth_and_uses_service_pressure_as_default_target() -> None:
    task = TaskParser().parse_instruction(
        "5000米水深复合材料圆柱耐压壳，长度600 mm，内半径150 mm，"
        "生成50个候选，初筛保留5个候选"
    )
    payload = task["task"]

    assert payload["load_conditions"]["service_depth_m"] == 5000
    assert payload["load_conditions"]["external_pressure_MPa"] == pytest.approx(50.259081)
    assert payload["load_conditions"]["pressure_basis"] == "rho_g_h_gauge_differential"
    assert payload["design_targets"]["ultimate_pressure_min_MPa"] == pytest.approx(50.259081)

from __future__ import annotations

import importlib.util
from copy import deepcopy
from pathlib import Path

import pytest

from abaqus.runtime_build_pressure_hull import layup_angles, material_payload, validate_runtime_candidate
from agents.fem_agent import FEMAgent
from agents.orchestrator import OrchestratorAgent
from core.fem_input_contract import (
    FEMInputValidationError,
    attach_design_revision,
    compute_design_revision_id,
    validate_fem_input,
    validate_fem_input_or_raise,
)
from core.schema_validator import validate_or_raise
from core.task_parser import TaskParser


CS_LLM_ENGINE = (
    Path(__file__).resolve().parents[2]
    / "CS_LLM"
    / "scripts"
    / "fem_ready_design_engine.py"
)


def _load_csllm_engine():
    spec = importlib.util.spec_from_file_location("csllm_fem_ready_design_engine", CS_LLM_ENGINE)
    if spec is None or spec.loader is None:
        raise RuntimeError("无法加载 CS_LLM FEM-ready 引擎。")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _generated_candidate() -> dict:
    engine = _load_csllm_engine()
    result = engine.generate_fem_ready_design(
        {
            "schema_version": "2",
            "generation_mode": "fem_ready_cylindrical_shell",
            "candidate_count": 1,
            "geometry": {"length_mm": 600, "radius_mm": 150},
            "load_conditions": {"service_depth_m": 5000},
            "boundary_conditions": {"type": "FLANGE_CONSTRAINED"},
        }
    )
    return result["candidates"][0]


def test_csllm_candidate_satisfies_csdm_schema_and_fem_contract() -> None:
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


def test_orchestrator_promotes_csllm_candidate_without_changing_design_revision() -> None:
    candidate = _generated_candidate()
    parser = TaskParser()
    task = parser.parse_instruction(
        "5000米水深复合材料圆柱耐压壳，长度600 mm，内半径150 mm，"
        "生成50个候选，初筛保留5个候选，端部法兰约束"
    )
    orchestrator = object.__new__(OrchestratorAgent)

    promoted = orchestrator.prepare_candidate_for_fem(task, candidate)

    assert promoted["candidate_id"].startswith("C")
    assert promoted["session_candidate_id"] == "TMP_1"
    assert promoted["design_revision_id"] == candidate["design_revision_id"]
    assert validate_fem_input(promoted) == []


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
    task = TaskParser().parse_instruction("外压 30 MPa，生成 1 个候选，初筛保留 1 个候选")
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


def test_retry_design_change_creates_child_revision() -> None:
    candidate = _generated_candidate()
    agent = FEMAgent()

    adjusted = agent.apply_adjustment(candidate, "convergence_fail", 0)

    assert adjusted["geometry"] != candidate["geometry"]
    assert adjusted["design_revision_id"] != candidate["design_revision_id"]
    assert adjusted["parent_design_revision_id"] == candidate["design_revision_id"]
    assert validate_fem_input(adjusted) == []


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

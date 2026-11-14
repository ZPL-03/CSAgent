from copy import deepcopy
import math

import pytest

from abaqus.cylindrical_geometry import shell_radii
from abaqus.runtime_build_pressure_hull import imperfection_amplitude_mm, validate_runtime_candidate
from core.fem_input_contract import attach_design_revision, validate_fem_input
from core.pressure_hull_profile import estimate_shell_mass_kg, normalize_geometry
from core.task_parser import TaskParser
from tests.test_fem_candidate_transfer import _candidate


@pytest.mark.parametrize("reference,radius", [("inner", 150), ("middle_surface", 160), ("outer", 170)])
def test_radius_representations_describe_same_shell(reference, radius):
    geometry = {"length_mm": 600, "radius_mm": radius, "radius_reference": reference,
                "thickness_mm": 20, "imperfection_ratio": 0.008}
    assert shell_radii(geometry) == {"inner": 150, "middle_surface": 160, "outer": 170}
    expected_mass = math.pi * (0.17**2 - 0.15**2) * 0.6 * 1600
    assert estimate_shell_mass_kg(geometry, {"density_kg_per_m3": 1600}) == pytest.approx(expected_mass)
    assert imperfection_amplitude_mm(geometry) == pytest.approx(1.28)
    assert normalize_geometry("CYLINDRICAL", geometry)["radius_reference"] == reference
    candidate = _candidate(1)
    candidate["geometry"].update(geometry)
    candidate = attach_design_revision(candidate)
    assert validate_fem_input(candidate) == []
    assert validate_runtime_candidate(candidate)["radius"] == 160


@pytest.mark.parametrize("updates", [
    {"radius_reference": "unknown"}, {"radius_reference": None},
    {"radius_reference": "outer", "radius_mm": 10}, {"radius_mm": float("inf")},
    {"thickness_mm": False}, {"radius_mm": -1},
])
def test_invalid_radius_contract_fails_before_solver(updates):
    candidate = _candidate(1)
    candidate["geometry"].update(updates)
    candidate = attach_design_revision(candidate)
    assert "geometry.radius_reference_or_dimensions" in validate_fem_input(candidate)
    with pytest.raises(ValueError):
        validate_runtime_candidate(candidate)


def test_radius_identity_changes_revision_without_mutating_source():
    source = _candidate(1)
    original = deepcopy(source)
    adapted = deepcopy(source)
    adapted["geometry"]["radius_reference"] = "inner"
    adapted = attach_design_revision(adapted)
    assert source == original
    assert adapted["parent_design_revision_id"] == source["design_revision_id"]
    assert adapted["design_revision_id"] != source["design_revision_id"]
    assert shell_radii(source["geometry"])["middle_surface"] == 150
    assert shell_radii(adapted["geometry"])["middle_surface"] == 160


@pytest.mark.parametrize("label,reference", [("内半径", "inner"), ("外半径", "outer"), ("中面半径", "middle_surface")])
def test_task_parser_preserves_user_radius_reference(label, reference):
    task = TaskParser().parse_instruction(f"外压50 MPa，长度600 mm，{label}150 mm，生成2个候选，初筛保留1个")
    assert task["task"]["radius_reference"] == reference
    assert task["task"]["geometry_envelope"]["radius_mm"] == [150, 150]


def test_surrogate_and_doe_preserve_physical_radius(tmp_path):
    from core.surrogate_model import SurrogateModelManager, candidate_to_features
    from core.doe_sampler import DOESampler

    manager = SurrogateModelManager(models_dir=tmp_path)
    predictions = []
    for reference, radius in (("inner", 150), ("middle_surface", 160), ("outer", 170)):
        candidate = _candidate(1)
        candidate["geometry"].update(radius_mm=radius, radius_reference=reference)
        predictions.append(manager.formula_prediction(candidate, apply_calibration=False).to_dict())
        assert manager.predict([candidate_to_features(candidate)])[0] == predictions[-1]["ultimate_pressure_MPa"]
    assert predictions[0] == predictions[1] == predictions[2]
    task = TaskParser().parse_instruction("外压30 MPa，内半径150 mm，长度600 mm，生成2个候选，初筛保留1个")
    candidates = DOESampler().sample_candidates(task, 2)
    assert len(candidates) == 2
    assert all(item["geometry"]["radius_reference"] == "inner" for item in candidates)

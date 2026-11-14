from copy import deepcopy

import pytest

from core.pressure_hull_profile import (
    expand_layup_for_fem, layup_pattern, normalize_layup, parse_layup_sequence,
)
from core.rule_checker import RuleChecker


@pytest.mark.parametrize("text,expected", [
    ("[±30/90]s", [30, -30, 90, 90, -30, 30]),
    ("[(±45/0)_2/90]_s", [45, -45, 0, 45, -45, 0, 90, 90, 0, -45, 45, 0, -45, 45]),
    ("[(30/-30)_s]", [30, -30, -30, 30]),
    ("[90_2/(+/-alpha/β)_2]", [90, 90, 40, -40, 70, 40, -40, 70]),
    ("[22.5/-22.5]", [22.5, -22.5]),
])
def test_layup_expansion_preserves_order_and_symmetry(text, expected):
    assert parse_layup_sequence(text) == expected


@pytest.mark.parametrize("text", [
    "", "invalid", "[±wrong/90]", "[45//90]", "[45/]", "[45", "45]", "[]",
    "[(45/90]", "[45_0]", "[45_-1]", "[45_1.5]", "[45]_s_extra", "[45_100000000]",
])
def test_invalid_layup_has_no_default_angles(text):
    with pytest.raises(ValueError):
        parse_layup_sequence(text)


def test_template_preserves_noninteger_angles():
    sequence = parse_layup_sequence(layup_pattern(22.5, 67.5))
    assert sequence[4:8] == [22.5, -22.5, 67.5, -67.5]
    assert len(sequence) == 40


def test_explicit_layer_array_is_not_replaced_with_a_template():
    raw = {"angles_deg": [30, -30, -30, 30]}
    geometry = {"alpha_deg": 40, "beta_deg": 70, "thickness_mm": 1}
    normalized = normalize_layup(raw, geometry)
    assert normalized["angles_deg"] == raw["angles_deg"]
    assert normalized["ply_count"] == 4
    assert expand_layup_for_fem(normalized, geometry)["angles_deg"] == raw["angles_deg"]
    with pytest.raises(ValueError, match="不一致"):
        normalize_layup({**raw, "layup": "[90/90/90/90]"}, geometry)
    with pytest.raises(ValueError, match="不一致"):
        expand_layup_for_fem({**raw, "balanced": False}, geometry)
    with pytest.raises(ValueError, match="不一致"):
        expand_layup_for_fem({**raw, "layup": "[30/-30/-30/30]", "skin_layup": "[90/90/90/90]"}, geometry)


def test_rule_checker_counts_both_signs_instead_of_only_their_presence():
    candidate = {"hull_type": "CYLINDRICAL", "geometry": {
        "length_mm": 500, "radius_mm": 100, "thickness_mm": 10,
        "alpha_deg": 40, "beta_deg": 70, "imperfection_ratio": 0.008,
    }, "layup": {"layup": "[40_12/-40_4]"}}
    original = deepcopy(candidate)
    result = RuleChecker().run(candidate)
    assert not result["is_valid"]
    assert not result["details"]["balanced"]
    assert candidate == original


def test_schema_dependency_is_required(monkeypatch):
    import core.schema_validator as validator

    validator.get_validator.cache_clear()
    monkeypatch.setattr(validator, "_JSONSCHEMA_AVAILABLE", False)
    with pytest.raises(validator.SchemaValidationError, match="jsonschema"):
        validator.validate_or_raise("candidate.schema.json", {})


def test_missing_layup_is_not_a_training_feature_default():
    from core.surrogate_model import record_to_training_sample

    with pytest.raises(ValueError, match="缺少铺层"):
        record_to_training_sample({"design": {}, "abaqus_results": {"status": "success", "ultimate_pressure_MPa": 80}})


def test_candidate_normalization_does_not_repair_a_rejected_proposal(monkeypatch):
    from agents.candidate_gen import CandidateGenAgent
    from core.task_parser import TaskParser

    monkeypatch.setenv("CSDM_cph_DISABLE_LLM_AUTO", "1")
    task = TaskParser().parse_instruction("外压 10 MPa，生成4个候选，预筛1个")
    agent = CandidateGenAgent()
    raw = agent.doe_sampler.sample_candidates(task, 1, strict_solver_window=True)[0]
    raw["layup"] = {"layup": "[40_12/-40_4]"}
    candidate = agent._normalize_candidate(task, raw, 1, "LLM")
    assert candidate["layup"]["angles_deg"] == [40] * 12 + [-40] * 4
    assert not candidate["rule_check"]["is_valid"]


def test_stiffness_keeps_zero_and_signed_coupling_without_regularization():
    from core.pressure_hull_profile import compute_laminate_stiffness

    material = {"E1_GPa": 100, "E2_GPa": 10, "G12_GPa": 5, "nu12": 0.3}
    symmetric = compute_laminate_stiffness({"layup": "[45/-45/-45/45]"}, material, 1.2)
    assert symmetric["B23"] == pytest.approx(0, abs=1e-10)
    forward = compute_laminate_stiffness({"layup": "[45/-45/45/-45]"}, material, 1.2)
    reverse = compute_laminate_stiffness({"layup": "[-45/45/-45/45]"}, material, 1.2)
    assert forward["B23"] < 0
    assert reverse["B23"] == pytest.approx(-forward["B23"])
    assert "B23_raw" not in forward


@pytest.mark.parametrize("material", [{}, {"E1_GPa": 100, "E2_GPa": 10, "G12_GPa": 5, "nu12": 4}])
def test_stiffness_does_not_substitute_missing_or_unphysical_material(material):
    from core.pressure_hull_profile import compute_laminate_stiffness

    with pytest.raises(ValueError):
        compute_laminate_stiffness({"layup": "[45/-45]"}, material, 1)

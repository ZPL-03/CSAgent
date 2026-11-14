import json

import pytest

from agents.screener import ScreenerAgent
from core import surrogate_model as surrogate
from core.pressure_hull_profile import compute_laminate_stiffness
from tests.test_fem_candidate_transfer import _candidate


def _descriptors(**overrides):
    values = dict(q_value=100.0, length_mm=600.0, radius_mm=150.0, thickness_mm=10.0,
                  imperfection_ratio=0.008, a22=1_000_000.0,
                  d12=2_000_000.0, d22=50_000_000.0, d33=6_000_000.0)
    values.update(overrides)
    return surrogate._pbipf_descriptors({"imperfection_ratio_to_permille": 1000}, **values)


@pytest.mark.parametrize("field,value", [
    ("q_value", 0), ("q_value", -2), ("length_mm", None), ("radius_mm", 0),
    ("thickness_mm", False), ("imperfection_ratio", -0.008),
    ("imperfection_ratio", None), ("a22", float("nan")), ("d22", float("inf")),
    ("d12", float("nan")), ("d33", 2_000_000.0),
    ("d33", 2_000_000.0000001),
])
def test_invalid_descriptor_input_is_not_replaced(field, value):
    with pytest.raises(ValueError):
        _descriptors(**{field: value})


def test_perfect_geometry_and_signed_stiffness_are_preserved():
    assert _descriptors(imperfection_ratio=0)["D3"] == 0
    assert _descriptors(d12=-2_000_000.0)["D2"] == 625.0
    assert _descriptors(d12=10_000_000.0)["D2"] == -1250.0
    stiffness = compute_laminate_stiffness(
        {"angles_deg": [0, 0], "layup": "[0/0]"},
        {"E1_GPa": 10, "E2_GPa": 10, "G12_GPa": 5, "nu12": -0.2}, 2.0)
    assert stiffness["D12"] == stiffness["D"][0][1] < 0


@pytest.mark.parametrize("coefficient,value", [("d1", float("inf")), ("d2", True)])
def test_invalid_formula_coefficient_is_rejected(coefficient, value):
    coefficients = dict(d0=1.0, d1=0.0, d2=0.0, d3=0.0)
    coefficients[coefficient] = value
    with pytest.raises(ValueError):
        surrogate._evaluate_pbipf(coefficients, _descriptors())


@pytest.mark.parametrize("pressure", [-1.0, 0.0])
def test_nonpositive_formula_result_is_preserved(pressure):
    assert surrogate._evaluate_pbipf(dict(d0=pressure, d1=0.0, d2=0.0, d3=0.0), _descriptors()) == pressure


def test_batch_and_single_inference_reject_missing_values(tmp_path):
    manager = surrogate.SurrogateModelManager(models_dir=tmp_path)
    candidate = _candidate(1)
    row = surrogate.candidate_to_features(candidate)
    assert manager.predict([row])[0] == manager.formula_prediction(candidate).ultimate_pressure_MPa
    for invalid in ([], row[:-1], [*row, 1], [float("nan"), *row[1:]]):
        with pytest.raises(ValueError):
            manager.predict([invalid])
    del candidate["geometry"]["imperfection_ratio"]
    with pytest.raises(ValueError, match="imperfection_ratio"):
        manager.formula_prediction(candidate)
    with pytest.raises(ValueError, match="未知代理模型特征"):
        surrogate.candidate_to_features(_candidate(1), feature_order=["unsupported"])


@pytest.mark.parametrize("payload", ["not json", "[]", '{"calibration_status":"invalid"}'])
def test_invalid_calibration_is_not_silently_ignored(tmp_path, payload):
    manager = surrogate.SurrogateModelManager(models_dir=tmp_path)
    manager.calibration_path.write_text(payload, encoding="utf-8")
    with pytest.raises(ValueError):
        manager._load_calibration()


def test_accepted_calibration_is_bound_to_formula_and_coefficients(tmp_path, monkeypatch):
    manager = surrogate.SurrogateModelManager(models_dir=tmp_path)
    payload = dict(calibration_status="accepted", scale=1.5, bias_MPa=0.0, uncertainty_MPa=1.0,
                   formula_fingerprint=surrogate._formula_fingerprint())
    manager.calibration_path.write_text(json.dumps(payload), encoding="utf-8")
    assert manager._load_calibration()["scale"] == 1.5
    monkeypatch.setattr(surrogate, "_coefficients", lambda: {"PBIPF": {"d1": 999}})
    with pytest.raises(ValueError, match="系数不一致"):
        manager._load_calibration()


@pytest.mark.parametrize("field,value", [("scale", 0), ("scale", float("inf")),
                                        ("bias_MPa", None), ("bias_MPa", 1.0), ("uncertainty_MPa", -1)])
def test_accepted_calibration_requires_valid_values(tmp_path, field, value):
    manager = surrogate.SurrogateModelManager(models_dir=tmp_path)
    payload = dict(calibration_status="accepted", scale=1.5, bias_MPa=0.0, uncertainty_MPa=1.0,
                   formula_fingerprint=surrogate._formula_fingerprint())
    payload[field] = value
    manager.calibration_path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError):
        manager._load_calibration()


@pytest.mark.parametrize("predictions,targets", [([], []), ([1], [1, 2]), ([0], [1]), ([-1], [2]), ([1], [float("nan")])])
def test_invalid_calibration_pairs_have_no_default_scale(predictions, targets):
    with pytest.raises(ValueError):
        surrogate._fit_positive_scale(predictions, targets)


def test_prediction_without_validation_keeps_error_unknown(tmp_path):
    manager = surrogate.SurrogateModelManager(models_dir=tmp_path)
    assert manager.formula_prediction(_candidate(1)).uncertainty_MPa is None
    assert manager.formula_prediction(_candidate(1), apply_calibration=False).uncertainty_MPa is None


@pytest.mark.parametrize("field,value", [("d1", 999.0), ("model_type", "unknown"), ("training_q_source", "ASME_RD_1172"),
                                        ("descriptor_radius_reference", "middle_surface"), ("q_method", "FEA"), ("imperfection_ratio_to_permille", 1)])
def test_runtime_regression_parameters_are_bound_to_validation(field, value):
    parameters = dict(surrogate._coefficients()["PBIPF"])
    parameters[field] = value
    with pytest.raises(ValueError):
        surrogate._validate_regression_report(parameters)


def test_validation_report_survives_lf_checkout_and_rejects_changed_code(tmp_path, monkeypatch):
    from pathlib import Path

    root = Path(surrogate.__file__).resolve().parents[1]
    parameters = dict(surrogate._coefficients()["PBIPF"])
    report = surrogate._validate_regression_report(parameters)
    paths = set(report["code_hashes"]) | set(report["data_hashes"]) | {parameters["validation_report"]}
    for relative in paths:
        destination = tmp_path / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text((root / relative).read_text(encoding="utf-8-sig"), encoding="utf-8", newline="\n")
    monkeypatch.setattr(surrogate, "__file__", str(tmp_path / "core/surrogate_model.py"))
    assert surrogate._validate_regression_report(parameters) == report
    changed = tmp_path / "core/pressure_regression.py"
    changed.write_text(changed.read_text(encoding="utf-8") + "\n# 校验测试\n", encoding="utf-8")
    with pytest.raises(ValueError, match="计算代码"):
        surrogate._validate_regression_report(parameters)


def test_runtime_pressure_matches_fem_trained_linear_regression(tmp_path):
    import numpy as np
    from core.pressure_regression import PressureRegression
    from core.surrogate_dataset import load_dataset, row_to_candidate, runtime_features

    frame, _ = load_dataset()
    low_pressure = frame.sort_values("ultimate_pressure_MPa").head(3)
    features, _, _ = runtime_features(low_pressure)
    manager = surrogate.SurrogateModelManager(models_dir=tmp_path)
    parameters = manager.validation_report["model"]
    model = PressureRegression(tuple(parameters["coefficients"]), parameters["intercept_MPa"])
    predicted = np.array([manager.formula_prediction(row_to_candidate(row)).ultimate_pressure_MPa for _, row in low_pressure.iterrows()])
    assert np.any(predicted < 0)
    assert predicted == pytest.approx(model.predict(features))
    validation = manager.formula_prediction(_candidate(1)).model_validation
    assert validation["model_type"] == "linear"
    assert validation["training_q_source"] == "finite_element_eigenvalue"
    assert validation["prediction_q_source"] == "ASME_RD_1172"
    candidate = row_to_candidate(low_pressure.iloc[0])
    assert manager.predict([surrogate.candidate_to_features(candidate)])[0] == pytest.approx(manager.formula_prediction(candidate).ultimate_pressure_MPa)


def test_nonpositive_estimate_is_audited_and_not_selected(tmp_path):
    from core.surrogate_dataset import load_dataset, row_to_candidate

    frame, _ = load_dataset()
    invalid = row_to_candidate(frame.sort_values("ultimate_pressure_MPa").iloc[0])
    invalid["candidate_id"] = "TMP_2"
    invalid["material_system"]["density_kg_per_m3"] = _candidate(1)["material_system"]["density_kg_per_m3"]
    agent = ScreenerAgent()
    agent.model_manager = surrogate.SurrogateModelManager(models_dir=tmp_path)
    task = {"screening_preferences": {"top_k_candidates": 2}}
    ranked = agent.rank_candidates(task, [invalid, _candidate(1)])
    rejected = next(candidate for candidate in ranked if candidate["candidate_id"] == "TMP_2")
    assert rejected["surrogate_ultimate_pressure_MPa"] < 0
    assert rejected["surrogate_prediction_status"] == "nonpositive"
    assert rejected["rank_score"] is None and rejected["screening_rank"] is None
    assert rejected["screening_selected"] is False
    assert len([candidate for candidate in ranked if candidate["screening_selected"]]) == 1
    assert agent.run({"task": {"screening_preferences": {"top_k_candidates": 1}}, "candidates": [invalid]}) == []


def test_prediction_uses_accepted_validation_error_without_historical_floor(tmp_path):
    manager = surrogate.SurrogateModelManager(models_dir=tmp_path)
    payload = dict(calibration_status="accepted", scale=1.5, bias_MPa=0.0, uncertainty_MPa=0.125,
                   formula_fingerprint=surrogate._formula_fingerprint())
    manager.calibration_path.write_text(json.dumps(payload), encoding="utf-8")
    assert manager.formula_prediction(_candidate(1)).uncertainty_MPa == 0.125


@pytest.mark.parametrize("validation_error", [None, 0.0, 6.5])
def test_screening_rank_does_not_use_global_validation_error(tmp_path, monkeypatch, validation_error):
    agent = ScreenerAgent()
    agent.model_manager = surrogate.SurrogateModelManager(models_dir=tmp_path)
    candidate = _candidate(1)
    prediction = agent.model_manager.predict_candidate_payload(candidate)
    prediction["uncertainty_MPa"] = validation_error
    monkeypatch.setattr(agent.model_manager, "predict_candidate_payload", lambda _: prediction)
    task = {"screening_preferences": {"top_k_candidates": 1}}
    result = agent.rank_candidates(task, [candidate])[0]
    assert result["surrogate_uncertainty_MPa"] == validation_error
    assert result["rank_score"] == round(
        agent.pressure_weight * result["surrogate_ultimate_pressure_MPa"]
        - agent.weight_penalty * result["surrogate_weight"], 4)
    assert "uncertainty_component" not in result["screening_breakdown"]

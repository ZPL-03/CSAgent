import copy
import json

import numpy as np
import pytest

from core.pressure_regression import PressureRegression, fit_pressure_regression
from core.surrogate_dataset import DATA, STIFFNESS_COMPONENTS, design_group, load_dataset, row_to_candidate, runtime_features
from scripts.fit_pressure_surrogate import cross_validate, metrics, split_design_groups


def regression_data():
    rng = np.random.default_rng(7)
    features = rng.normal(size=(120, 3)) * [0.1, 2000, 0.2] + [0.2, 3000, 0.1]
    return features


def test_positive_link_is_fitted_in_engineering_units():
    features = regression_data()
    expected = PressureRegression((185.7, 0.0046, -29.3), -0.04, "softplus", 3.6)
    target = expected.predict(features)
    fitted = fit_pressure_regression(features, target, "softplus")
    assert fitted.predict(features) == pytest.approx(target, rel=1e-7)
    assert fitted.coefficients == pytest.approx(expected.coefficients, rel=1e-6)
    assert fitted.link_scale_MPa == pytest.approx(3.6, rel=1e-6)
    assert fitted.intercept_MPa == pytest.approx(-0.04, abs=1e-6)


def test_linear_fit_and_negative_predictions_are_not_clipped():
    features = regression_data()
    expected = PressureRegression((10, 0.001, -2), 20, "identity")
    target = expected.predict(features)
    fitted = fit_pressure_regression(features, target, "identity")
    assert fitted.predict(features) == pytest.approx(target)
    result = metrics(np.array([1.0, 3.0]), np.array([-1.0, 4.0]))
    assert result["nonpositive_count"] == 1
    assert result["rmse_MPa"] == pytest.approx(np.sqrt(2.5))


def test_stable_positive_link_has_no_fixed_pressure_floor():
    model = PressureRegression((1, 0, 0), 0, "softplus", 1)
    x = np.array([[-20, 0, 0], [-10, 0, 0], [0, 0, 0], [1000, 0, 0]])
    values = model.predict(x)
    assert 0 < values[0] < values[1] < values[2] < values[3]
    assert values[3] == 1000
    with pytest.raises(ValueError, match="下溢"):
        model.predict(np.array([[-1000, 0, 0]]))


@pytest.mark.parametrize("target,prediction", [([], []), ([1, 2], [1]),
                         ([1, float("nan")], [1, 2]), ([1, 2], [1, float("inf")]), ([1, 0], [1, 2])])
def test_invalid_metric_data_fails_explicitly(target, prediction):
    with pytest.raises(ValueError):
        metrics(np.array(target), np.array(prediction))


@pytest.mark.parametrize("link,scale", [("unknown", None), ("softplus", None), ("softplus", -1), ("softplus", float("inf"))])
def test_invalid_link_is_rejected(link, scale):
    with pytest.raises(ValueError):
        PressureRegression((1, 2, 3), 1, link, scale).predict(np.ones((1, 3)))


def test_degenerate_regression_fails():
    with pytest.raises(ValueError, match="方差"):
        fit_pressure_regression(np.ones((10, 3)), np.arange(1, 11), "softplus")
    with pytest.raises(ValueError, match="目标必须为正"):
        fit_pressure_regression(regression_data(), np.zeros(120), "softplus")


def test_dataset_contract_and_group_separation():
    frame, metadata = load_dataset()
    assert len(frame) == metadata["sample_count"] == 5857
    assert frame.source_flag.notna().all()
    assert set(frame.source_id) == {"complete_source_results"}
    assert "split" not in frame.columns
    candidate = row_to_candidate(frame.iloc[0])
    assert candidate["geometry"]["length_mm"] == 300
    assert candidate["geometry"]["radius_mm"] == 160
    assert candidate["geometry"]["thickness_mm"] == 19
    assert candidate["material_system"]["G12_GPa"] == 3.35
    assert candidate["material_system"]["nu12"] == 0.16
    assert len(candidate["layup"]["angles_deg"]) == 40
    changed = copy.deepcopy(candidate)
    changed["geometry"]["imperfection_ratio"] = 0.008
    assert design_group(candidate) == design_group(changed)
    _, groups, audit = runtime_features(frame)
    training, testing = split_design_groups(groups)
    assert not set(groups[training]) & set(groups[testing])
    assert sorted([*training, *testing]) == list(range(len(frame)))
    repeat_training, repeat_testing = split_design_groups(groups)
    np.testing.assert_array_equal(training, repeat_training)
    np.testing.assert_array_equal(testing, repeat_testing)
    assert audit["stiffness_max_abs_error"] <= 0.051


@pytest.mark.parametrize("component", STIFFNESS_COMPONENTS)
def test_missing_source_stiffness_is_rejected(component):
    frame, _ = load_dataset()
    with pytest.raises(ValueError, match="16 个"):
        runtime_features(frame.head(1).drop(columns=[component]))


def test_dataset_fingerprint_is_required(tmp_path):
    (tmp_path / "dataset_metadata.json").write_text((DATA / "dataset_metadata.json").read_text(encoding="utf-8"), encoding="utf-8")
    (tmp_path / "design_dataset.csv").write_text("invalid", encoding="utf-8")
    with pytest.raises(ValueError, match="指纹"):
        load_dataset(tmp_path)


def test_group_cross_validation_keeps_repeated_designs_together():
    features = regression_data()
    target = PressureRegression((185.7, 0.0046, -29.3), -0.04, "softplus", 3.6).predict(features)
    groups = np.repeat([f"design-{index}" for index in range(40)], 3)
    report, rows = cross_validate(features, target, groups)
    assert report["group_overlap_count"] == 0
    assert rows.groupby("design_group").fold.nunique().max() == 1
    assert report["metrics"]["softplus"]["nonpositive_count"] == 0
    assert json.dumps(report, allow_nan=False)

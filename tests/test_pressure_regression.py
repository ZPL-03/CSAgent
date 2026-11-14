import copy
import json

import numpy as np
import pytest
from sklearn.linear_model import LinearRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import PolynomialFeatures, StandardScaler

from core.pressure_regression import PressureRegression, fit_pressure_regression
from core.surrogate_dataset import (
    DATA, DESCRIPTORS, STIFFNESS_COMPONENTS, design_group, digest, load_dataset,
    load_regression_dataset, row_to_candidate, runtime_features,
)
from scripts.fit_pressure_surrogate import metrics, split_regression_rows


def test_text_fingerprint_is_portable_and_detects_content_changes(tmp_path):
    lf, crlf = tmp_path / "lf.csv", tmp_path / "crlf.csv"
    lf.write_text("Q,P\n1,2\n", encoding="utf-8", newline="\n")
    crlf.write_text("Q,P\n1,2\n", encoding="utf-8-sig", newline="\r\n")
    assert digest(lf) == digest(crlf)
    crlf.write_text("Q,P\n1,3\n", encoding="utf-8", newline="\r\n")
    assert digest(lf) != digest(crlf)


def regression_data():
    rng = np.random.default_rng(7)
    return rng.normal(size=(120, 3)) * [0.1, 2000, 0.2] + [0.2, 3000, 0.1]


def test_linear_fit_is_equivalent_to_standardized_pipeline():
    frame, _ = load_regression_dataset()
    x, y = frame[DESCRIPTORS].to_numpy(), frame.maxP.to_numpy()
    training, testing = split_regression_rows(len(frame))
    pipeline = make_pipeline(PolynomialFeatures(degree=1), StandardScaler(), LinearRegression()).fit(x[training], y[training])
    model = fit_pressure_regression(x[training], y[training])
    assert model.predict(x) == pytest.approx(pipeline.predict(x), abs=1e-11)
    assert model.coefficients == pytest.approx((185.77317089347588, 0.004656012009242322, -29.312096583263948))
    assert model.intercept_MPa == pytest.approx(-0.04158270972381217, abs=1e-11)
    assert np.sum(model.predict(x) <= 0) == 32
    assert metrics(y[testing], model.predict(x[testing]))["nonpositive_count"] == 11
    assert len(training) == 3201 and len(testing) == 1068
    assert not set(training) & set(testing)
    repeated = split_regression_rows(len(frame))
    np.testing.assert_array_equal(training, repeated[0])
    np.testing.assert_array_equal(testing, repeated[1])


def test_training_descriptors_use_finite_element_q(monkeypatch):
    from core import surrogate_dataset

    def reject_asme(*args, **kwargs):
        raise AssertionError("线性拟合不能调用 ASME 估算 Q")

    monkeypatch.setattr(surrogate_dataset, "estimate_linear_buckling_feature_q", reject_asme)
    frame, metadata = load_regression_dataset()
    row = frame.iloc[0]
    assert metadata["q_source"] == "finite_element_eigenvalue"
    assert row.Q == 199.61
    assert row.D1 == pytest.approx(np.log10(row.Q) * row.t / row.R, abs=5.1e-10)


def test_linear_fit_and_negative_predictions_are_not_clipped():
    features = regression_data()
    expected = PressureRegression((10, 0.001, -2), 20)
    fitted = fit_pressure_regression(features, expected.predict(features))
    assert fitted.predict(features) == pytest.approx(expected.predict(features))
    assert PressureRegression((1, 0, 0), 0).predict(np.array([[-1, 0, 0], [0, 0, 0]])).tolist() == [-1, 0]
    result = metrics(np.array([1.0, 3.0]), np.array([-1.0, 4.0]))
    assert result["nonpositive_count"] == 1
    assert result["rmse_MPa"] == pytest.approx(np.sqrt(2.5))


@pytest.mark.parametrize("target,prediction", [([], []), ([1, 2], [1]),
                         ([1, float("nan")], [1, 2]), ([1, 2], [1, float("inf")]), ([1, 0], [1, 2])])
def test_invalid_metric_data_fails_explicitly(target, prediction):
    with pytest.raises(ValueError):
        metrics(np.array(target), np.array(prediction))


@pytest.mark.parametrize("coefficients,intercept", [((1, 2), 0), ((1, 2, float("nan")), 0), ((1, 2, 3), float("inf"))])
def test_invalid_coefficients_are_rejected(coefficients, intercept):
    with pytest.raises(ValueError):
        PressureRegression(coefficients, intercept).predict(np.ones((1, 3)))


def test_degenerate_regression_fails():
    with pytest.raises(ValueError, match="方差"):
        fit_pressure_regression(np.ones((10, 3)), np.arange(1, 11))
    with pytest.raises(ValueError, match="目标必须为正"):
        fit_pressure_regression(regression_data(), np.zeros(120))


def test_dataset_contract_and_group_identity():
    frame, metadata = load_dataset()
    assert len(frame) == metadata["sample_count"] == 5857
    assert frame.source_flag.notna().all()
    assert set(frame.source_id) == {"complete_source_results"}
    candidate = row_to_candidate(frame.iloc[0])
    assert candidate["geometry"]["radius_mm"] == 160
    assert candidate["material_system"]["G12_GPa"] == 3.35
    assert candidate["material_system"]["nu12"] == 0.16
    assert len(candidate["layup"]["angles_deg"]) == 40
    changed = copy.deepcopy(candidate)
    changed["geometry"]["imperfection_ratio"] = 0.008
    assert design_group(candidate) == design_group(changed)
    _, groups, audit = runtime_features(frame)
    assert len(groups) == len(frame)
    assert audit["stiffness_max_abs_error"] <= 0.051
    assert audit["descriptor_radius_reference"] == "inner"


@pytest.mark.parametrize("component", STIFFNESS_COMPONENTS)
def test_missing_source_stiffness_is_rejected(component):
    frame, _ = load_dataset()
    with pytest.raises(ValueError, match="16 个"):
        runtime_features(frame.head(1).drop(columns=[component]))


@pytest.mark.parametrize("prefix", ["dataset", "regression"])
def test_dataset_fingerprint_is_required(tmp_path, prefix):
    metadata_name = "dataset_metadata.json" if prefix == "dataset" else "regression_metadata.json"
    data_name = "design_dataset.csv" if prefix == "dataset" else "regression_dataset.csv"
    (tmp_path / metadata_name).write_text((DATA / metadata_name).read_text(encoding="utf-8"), encoding="utf-8")
    (tmp_path / data_name).write_text("invalid", encoding="utf-8")
    loader = load_dataset if prefix == "dataset" else load_regression_dataset
    with pytest.raises(ValueError, match="指纹"):
        loader(tmp_path)


def test_regression_descriptor_and_q_source_are_verified(tmp_path):
    frame, metadata = load_regression_dataset()
    frame.loc[0, "D2"] += 1
    frame.to_csv(tmp_path / "regression_dataset.csv", index=False, encoding="utf-8")
    metadata["sha256"] = digest(tmp_path / "regression_dataset.csv")
    (tmp_path / "regression_metadata.json").write_text(json.dumps(metadata), encoding="utf-8")
    with pytest.raises(ValueError, match="描述符"):
        load_regression_dataset(tmp_path)
    metadata["q_source"] = "ASME_RD_1172"
    (tmp_path / "regression_metadata.json").write_text(json.dumps(metadata), encoding="utf-8")
    with pytest.raises(ValueError, match="有限元"):
        load_regression_dataset(tmp_path)

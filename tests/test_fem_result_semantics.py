import json
from types import SimpleNamespace

from core.fem_result_semantics import (
    is_passed_design_check,
    normalize_result_semantics,
    required_fem_artifact_fields,
    result_semantic_errors,
    verified_capacity_pressure,
)
from core.config_loader import load_param_ranges
from core.case_retriever import CaseRetriever
from core.surrogate_model import SurrogateModelManager, _pbipf_descriptors, record_to_training_sample


def test_pbipf_descriptor_converts_ratio_to_permille_once():
    descriptors = _pbipf_descriptors(
        {"imperfection_ratio_to_permille": 1000},
        q_value=100.0,
        length_mm=600.0,
        radius_mm=150.0,
        thickness_mm=10.0,
        imperfection_ratio=0.005,
        a22=1_000_000.0,
        d12=2_000_000.0,
        d22=50_000_000.0,
        d33=6_000_000.0,
    )

    assert descriptors["D1"] == 0.13333333333333333
    assert descriptors["D2"] == 1250.0
    assert descriptors["D3"] == 0.3


def test_pbipf_runtime_configuration_declares_single_unit_contract():
    pbipf = load_param_ranges()["surrogate_coefficients"]["PBIPF"]

    assert pbipf["imperfection_input"] == "permille"
    assert pbipf["imperfection_ratio_to_permille"] == 1000
    assert all(name in pbipf for name in ("d1", "d2", "d3", "d0"))


def test_failed_result_cannot_be_a_pass_or_capacity_sample():
    results = {
        "status": "failed",
        "verdict": "通过",
        "ultimate_pressure_MPa": 80.0,
        "linear_buckling_pressure_MPa": 120.0,
    }

    assert not is_passed_design_check(results)
    assert verified_capacity_pressure(results) is None
    assert result_semantic_errors(results)
    assert record_to_training_sample({"design": {}, "abaqus_results": results}) is None

    normalized = normalize_result_semantics(results)
    assert normalized["verdict"] is None
    assert normalized["ultimate_pressure_MPa"] is None
    assert normalized["linear_buckling_pressure_MPa"] == 120.0


def test_case_retrieval_requires_complete_submodel_stress_coverage():
    record = {"design": {"candidate_id": "C1"}, "abaqus_results": {
        "status": "success", "verdict": "通过",
        "verification_scope": "composite_cylindrical_shell_submodel",
        "target_stress_coverage": {"status": "incomplete"},
    }}
    retriever = CaseRetriever(use_vector_index=False)
    assert not retriever._is_transferable(record)
    record["abaqus_results"]["target_stress_coverage"]["status"] = "complete"
    assert retriever._is_transferable(record)


def test_linear_buckling_pressure_is_not_capacity_training_target():
    results = {
        "status": "success",
        "verdict": "不通过",
        "linear_buckling_pressure_MPa": 120.0,
    }

    assert verified_capacity_pressure(results) is None
    assert record_to_training_sample({"design": {}, "abaqus_results": results}) is None


def test_verified_capacity_pressure_accepts_completed_capacity_evidence():
    results = {
        "status": "success",
        "verdict": "通过",
        "ultimate_pressure_MPa": 80.0,
        "linear_buckling_pressure_MPa": 120.0,
    }

    assert is_passed_design_check(results)
    assert verified_capacity_pressure(results) == 80.0


def test_shell_pass_and_capacity_require_full_ply_and_damage_evidence():
    result = {"status": "success", "verdict": "通过", "ultimate_pressure_MPa": 80.0,
              "verification_scope": "composite_cylindrical_shell_submodel"}
    assert not is_passed_design_check(result)
    assert verified_capacity_pressure(result) is None
    result["target_stress_coverage"] = {"status": "complete"}
    assert is_passed_design_check(result)
    assert verified_capacity_pressure(result) is None
    result.update(progressive_damage_complete=True, damage_state_output_complete=True, riks_limit_point_confirmed=True)
    assert verified_capacity_pressure(result) == 80.0


def test_training_record_loader_excludes_target_only_and_failed_results(tmp_path):
    cases = tmp_path / "cases"
    models = tmp_path / "models"
    cases.mkdir()
    (cases / "CASE_1.json").write_text(
        '{"design": {}, "abaqus_results": {"status": "success", "linear_buckling_pressure_MPa": 120.0}}',
        encoding="utf-8",
    )
    (cases / "CASE_2.json").write_text(
        '{"design": {}, "abaqus_results": {"status": "failed", "ultimate_pressure_MPa": 90.0}}',
        encoding="utf-8",
    )
    (cases / "CASE_3.json").write_text(
        '{"design": {}, "abaqus_results": {"status": "success", "ultimate_pressure_MPa": 80.0}}',
        encoding="utf-8",
    )

    records = SurrogateModelManager(models_dir=models, case_dir=cases).load_training_records()

    assert len(records) == 1
    assert records[0]["abaqus_results"]["ultimate_pressure_MPa"] == 80.0


def test_required_artifacts_follow_available_analysis_evidence():
    linear_only = {
        "linear_buckling_pressure_MPa": 120.0,
        "abaqus_inp": "C1.inp",
        "linear_buckling_odb": "C1.odb",
        "abaqus_odb": "C1.odb",
        "visualization_json": "C1.json",
    }
    assert required_fem_artifact_fields(linear_only) == (
        "abaqus_inp",
        "linear_buckling_odb",
        "abaqus_odb",
        "visualization_json",
    )

    with_riks = {**linear_only, "riks_increment_count": 12}
    assert "postbuckling_inp" in required_fem_artifact_fields(with_riks)
    assert "postbuckling_odb" in required_fem_artifact_fields(with_riks)


def test_legacy_calibration_without_validation_status_is_not_applied(tmp_path):
    models = tmp_path / "models"
    models.mkdir()
    (models / "pressure_hull_surrogate_calibration.json").write_text(
        json.dumps({"bias_MPa": 50.0, "scale": 2.0}),
        encoding="utf-8",
    )

    calibration = SurrogateModelManager(models_dir=models, case_dir=tmp_path / "cases")._load_calibration()

    assert calibration["calibration_status"] == "legacy_unverified"
    assert calibration["bias_MPa"] == 0.0
    assert calibration["scale"] == 1.0
    assert calibration["uncertainty_MPa"] is None


def test_scale_calibration_is_applied_only_after_leave_one_out_improvement(tmp_path):
    models = tmp_path / "models"
    manager = SurrogateModelManager(models_dir=models, case_dir=tmp_path / "cases")
    predictions = [10.0, 20.0, 30.0, 40.0]
    targets = [20.0, 40.0, 60.0, 80.0]
    records = [
        {
            "design": {"prediction_index": index},
            "abaqus_results": {"status": "success", "ultimate_pressure_MPa": target},
        }
        for index, target in enumerate(targets)
    ]
    manager.formula_prediction = lambda design, apply_calibration=False: SimpleNamespace(
        ultimate_pressure_MPa=predictions[design["prediction_index"]]
    )

    summary = manager.train_from_records(records)

    assert summary["calibration_status"] == "accepted"
    assert summary["bias_MPa"] == 0.0
    assert summary["scale"] == 2.0
    assert manager._load_calibration()["scale"] == 2.0


def test_unstable_scale_calibration_is_rejected(tmp_path):
    manager = SurrogateModelManager(models_dir=tmp_path / "models", case_dir=tmp_path / "cases")
    predictions = [14.969, 36.764, 42.902, 12.743, 33.693, 148.628, 121.99, 67.428]
    targets = [12.739613, 64.254111, 55.094194, 12.895442, 30.550128, 324.205742, 297.759563, 440.474224]
    records = [
        {
            "design": {"prediction_index": index},
            "abaqus_results": {"status": "success", "ultimate_pressure_MPa": target},
        }
        for index, target in enumerate(targets)
    ]
    manager.formula_prediction = lambda design, apply_calibration=False: SimpleNamespace(
        ultimate_pressure_MPa=predictions[design["prediction_index"]]
    )

    summary = manager.train_from_records(records)

    assert summary["calibration_status"] == "rejected"
    assert summary["scale"] == 1.0
    assert summary["validation"]["leave_one_out_candidate"]["mape_pct"] > summary["validation"]["baseline"]["mape_pct"]
    assert manager._load_calibration()["scale"] == 1.0

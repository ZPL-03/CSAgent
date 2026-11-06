from pathlib import Path

import pytest

from abaqus.runtime_build_pressure_hull import (
    classify_riks_limit_point,
    hashin_failure_indices,
    max_hashin_index_from_frame,
    riks_first_ply_evidence,
    runtime_script_sha256,
    service_load_evidence,
    validate_runtime_candidate,
)
from agents.fem_agent import FEMAgent


def test_riks_limit_point_requires_successful_job_and_post_peak_drop() -> None:
    curve = [(0.0, 0.0), (1.0, 0.8), (2.0, 1.0), (3.0, 0.98), (4.0, 0.9), (5.0, 0.82)]

    result = classify_riks_limit_point(curve, "JOB_STATUS_COMPLETED_SUCCESSFULLY")

    assert result["job_completed_successfully"] is True
    assert result["limit_point_observed"] is True
    assert result["limit_point_confirmed"] is True
    assert result["max_index"] == 2
    assert result["post_peak_drop_ratio"] > 0.1


def test_riks_last_point_maximum_is_not_an_ultimate_pressure() -> None:
    curve = [(0.0, 0.0), (1.0, 0.8), (2.0, 0.9), (3.0, 1.0)]

    result = classify_riks_limit_point(curve, "JOB_STATUS_EXITED_WITH_ERROR")

    assert result["job_completed_successfully"] is False
    assert result["limit_point_observed"] is False
    assert result["limit_point_confirmed"] is False
    assert result["max_index"] == 3


def test_riks_error_status_never_confirms_limit_point() -> None:
    curve = [(0.0, 0.0), (1.0, 1.0), (2.0, 0.9), (3.0, 0.8), (4.0, 0.7)]

    result = classify_riks_limit_point(curve, "JOB_STATUS_EXITED_WITH_ERROR")

    assert result["limit_point_observed"] is True
    assert result["limit_point_confirmed"] is False


def test_cleanup_preserves_solver_evidence_logs(tmp_path: Path) -> None:
    agent = FEMAgent.__new__(FEMAgent)
    agent._run_dir = lambda _candidate_id: tmp_path
    for suffix in (".msg", ".dat", ".sta", ".log", ".lck", ".com"):
        (tmp_path / f"C1{suffix}").write_text("evidence", encoding="utf-8")

    agent._cleanup_run_artifacts("C1", keep_logs=True)

    for suffix in (".msg", ".dat", ".sta", ".log"):
        assert (tmp_path / f"C1{suffix}").exists()
    for suffix in (".lck", ".com"):
        assert not (tmp_path / f"C1{suffix}").exists()


def test_diagnosis_summary_reports_service_pressure_failure_without_target_placeholders() -> None:
    agent = FEMAgent.__new__(FEMAgent)

    summary = agent._diagnosis_summary(
        {
            "status": "success",
            "verdict": "不通过",
            "linear_buckling_pressure_MPa": 200.62,
            "design_check_status": "failed_at_service_pressure",
            "service_pressure_check_status": "failed",
            "service_pressure_checked_MPa": 50.259081,
            "service_hashin_index_max": 1.53507021,
            "service_hashin_failure_mode": "matrix_tension",
        }
    )

    assert "服务压力 50.259081 MPa" in summary
    assert "最大 Hashin 指数 1.53507021" in summary
    assert "容量分析因服务压力校核未通过而未运行" in summary
    assert "None" not in summary


def test_hashin_failure_indices_distinguish_compression_modes() -> None:
    material = {"Xt": 1000.0, "Xc": 500.0, "Yt": 40.0, "Yc": 100.0, "S": 50.0}

    indices = hashin_failure_indices((-250.0, -50.0, 0.0, 25.0), material)

    assert indices["fiber_compression"] == 0.25
    assert indices["matrix_compression"] == 0.5
    assert "fiber_matrix_shear" not in indices
    assert "fiber_tension" not in indices


def test_hashin_fiber_tension_includes_in_plane_shear() -> None:
    material = {"Xt": 1000.0, "Xc": 500.0, "Yt": 40.0, "Yc": 100.0, "S": 50.0}

    indices = hashin_failure_indices((500.0, 0.0, 0.0, 25.0), material)

    assert indices["fiber_tension"] == 0.5


def test_max_hashin_index_keeps_element_and_ply_trace() -> None:
    class SectionPoint:
        description = "Layer = 4"

    class Value:
        data = (-250.0, -80.0, 0.0, 25.0)
        elementLabel = 17
        sectionPoint = SectionPoint()

    class StressOutput:
        values = [Value()]

    class Frame:
        fieldOutputs = {"S": StressOutput()}

    material = {"Xt": 1000.0, "Xc": 500.0, "Yt": 40.0, "Yc": 100.0, "S": 50.0}

    maximum = max_hashin_index_from_frame(Frame(), material)

    assert maximum == {
        "failure_index": 0.8900000000000001,
        "failure_mode": "matrix_compression",
        "element_label": 17,
        "section_point": "Layer = 4",
        "stress_MPa": [-250.0, -80.0, 0.0, 25.0],
    }


def test_hashin_failure_pressure_is_reported_as_interval_not_exact_value() -> None:
    class Value:
        data = (0.0, 50.0, 0.0, 0.0)
        elementLabel = 1
        sectionPoint = type("SectionPoint", (), {"description": "Layer = 1"})()

    class StressOutput:
        values = [Value()]

    class Frame:
        frameValue = 1.0
        fieldOutputs = {"S": StressOutput()}

    class Step:
        frames = [Frame()]

    evidence = riks_first_ply_evidence(
        Step(), [(0.0, 0.5), (1.0, 1.0)], 100.0, {"Xt": 1000.0, "Xc": 500.0, "Yt": 40.0, "Yc": 100.0, "S": 50.0}
    )

    assert evidence["first_ply_failure_pressure_MPa"] is None
    assert evidence["first_ply_failure_pressure_lower_bound_MPa"] is None
    assert evidence["first_ply_failure_pressure_upper_bound_MPa"] == 100.0


def test_exact_service_load_requires_successful_final_frame() -> None:
    class SectionPoint:
        description = "Layer = 4"

    class Value:
        data = (-100.0, -10.0, 0.0, 5.0)
        elementLabel = 17
        sectionPoint = SectionPoint()

    class StressOutput:
        values = [Value()]

    class Frame:
        frameValue = 1.0
        fieldOutputs = {"S": StressOutput()}

    class Step:
        frames = [Frame()]

    class DiagnosticData:
        jobStatus = "JOB_STATUS_COMPLETED_SUCCESSFULLY"

    class Odb:
        diagnosticData = DiagnosticData()
        steps = {"Step-1": Step()}

    material = {"Xt": 1000.0, "Xc": 500.0, "Yt": 40.0, "Yc": 100.0, "S": 50.0}

    evidence = service_load_evidence(Odb(), 50.0, material, linear_pressure=80.0)

    assert evidence["service_pressure_check_status"] == "passed"
    assert evidence["service_pressure_checked_MPa"] == 50.0
    assert evidence["service_hashin_index_max"] < 1.0


def test_runtime_script_fingerprint_does_not_require_dunder_file(tmp_path, monkeypatch) -> None:
    script = tmp_path / "build_C1.py"
    script.write_text("print('runtime')", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    assert len(runtime_script_sha256("C1")) == 64


def test_runtime_keeps_service_pressure_separate_from_ultimate_target() -> None:
    candidate = {
        "candidate_id": "C1",
        "design_revision_id": "DR_" + "a" * 64,
        "hull_type": "CYLINDRICAL",
        "geometry": {
            "length_mm": 600.0,
            "radius_mm": 150.0,
            "thickness_mm": 20.0,
            "alpha_deg": 45.0,
            "beta_deg": 70.0,
            "imperfection_ratio": 0.001,
        },
        "layup": {
            "angles_deg": [90.0, 45.0, -45.0, 90.0],
            "ply_count": 4,
            "ply_thickness_mm": 5.0,
            "balanced": True,
            "symmetric": False,
        },
        "material_system": {
            "name": "T700/Epoxy",
            "material_key": "T700_EPOXY",
            "density_kg_per_m3": 1600.0,
            "E1_GPa": 102.0,
            "E2_GPa": 7.0,
            "G12_GPa": 3.35,
            "nu12": 0.16,
            "Xt_MPa": 1400.0,
            "Xc_MPa": 1050.0,
            "Yt_MPa": 28.0,
            "Yc_MPa": 105.0,
            "S_MPa": 75.0,
        },
        "load_conditions": {"type": "external_pressure", "external_pressure_MPa": 50.0},
        "boundary_conditions": {"type": "FLANGE_CONSTRAINED"},
        "design_targets": {"ultimate_pressure_min_MPa": 75.0},
    }

    validated = validate_runtime_candidate(candidate)

    assert validated["service_pressure"] == 50.0
    assert validated["target_pressure"] == 75.0


def test_runtime_rejects_false_layup_declarations() -> None:
    candidate = {
        "candidate_id": "C1",
        "design_revision_id": "DR_" + "a" * 64,
        "hull_type": "CYLINDRICAL",
        "geometry": {
            "length_mm": 600.0,
            "radius_mm": 150.0,
            "thickness_mm": 20.0,
            "alpha_deg": 45.0,
            "beta_deg": 70.0,
            "imperfection_ratio": 0.001,
        },
        "layup": {
            "angles_deg": [45.0, -45.0, 70.0, -70.0],
            "ply_count": 4,
            "ply_thickness_mm": 5.0,
            "balanced": True,
            "symmetric": True,
        },
        "material_system": {
            "name": "T700/Epoxy",
            "material_key": "T700_Epoxy",
            "density_kg_per_m3": 1550.0,
            "E1_GPa": 102.0,
            "E2_GPa": 7.0,
            "G12_GPa": 3.35,
            "nu12": 0.16,
            "Xt_MPa": 1400.0,
            "Xc_MPa": 1050.0,
            "Yt_MPa": 28.0,
            "Yc_MPa": 105.0,
            "S_MPa": 75.0,
        },
        "load_conditions": {"type": "external_pressure", "external_pressure_MPa": 50.0},
        "boundary_conditions": {"type": "FLANGE_CONSTRAINED"},
        "design_targets": {"ultimate_pressure_min_MPa": 50.0},
    }

    with pytest.raises(ValueError, match="layup.symmetric"):
        validate_runtime_candidate(candidate)

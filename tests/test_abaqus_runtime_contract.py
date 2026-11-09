from pathlib import Path

import pytest

from abaqus.runtime_build_pressure_hull import (
    classify_riks_limit_point,
    configure_ply_stress_output,
    ply_stress_coverage,
    riks_status_curve,
    run_riks_job,
    hashin_failure_indices,
    max_hashin_index_from_frame,
    riks_first_ply_evidence,
    runtime_script_sha256,
    service_load_evidence,
    validate_runtime_candidate,
)
from agents.fem_agent import FEMAgent


def test_riks_status_parser_uses_only_converged_rows() -> None:
    text = """
 STEP INC ATT SEVERE EQUIL TOTAL LPF ARC
 1 1 1 0 2 2 0.00999 0.009989 R
 1 2 1U 0 8 8 0.01900 0.02 R
 1 2 2 0 3 3 0.01500 0.015 R
 1 3 1 0 2 2 0.01700 0.02
"""
    assert riks_status_curve(text) == [(1, 0.00999), (2, 0.015)]


def test_monitor_process_starts_before_blocking_submission(tmp_path, monkeypatch) -> None:
    import subprocess
    import json
    monkeypatch.chdir(tmp_path)
    calls = []
    class Process:
        returncode = 0
        def __init__(self, command, **kwargs):
            calls.append("monitor")
        def poll(self):
            return 0
    class Job:
        name = "C1_post"
        def submit(self, **kwargs):
            assert calls == ["monitor"]
            calls.append("submit")
            (tmp_path / "C1_post.monitor.json").write_text(json.dumps({"controlled": True, "error": None}), encoding="utf-8")
        def waitForCompletion(self):
            calls.append("wait")
    monkeypatch.setattr(subprocess, "Popen", Process)
    assert run_riks_job(Job(), "abaqus")["controlled"]
    assert calls == ["monitor", "submit", "wait"]
    assert not (tmp_path / "C1_post.monitor.stop").exists()


def test_subroutine_and_candidate_strengths_are_staged_together(tmp_path) -> None:
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    source = source_dir / "damage.for"
    source.write_text("      INCLUDE 'pressure_hull_strength.inc'\n", encoding="utf-8")
    agent = FEMAgent.__new__(FEMAgent)
    agent.abaqus_config = {"user_subroutine": str(source)}
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    agent._run_dir = lambda _cid: run_dir
    agent._input_path = lambda _cid: run_dir / "input.json"
    agent._result_path = lambda _cid: run_dir / "result.json"
    candidate = {"candidate_id": "C1", "analysis": {"use_user_subroutine": True},
                 "material_system": {"Xc_MPa": 1050, "Xt_MPa": 1400, "Yc_MPa": 105, "Yt_MPa": 28, "S_MPa": 75}}
    script = agent.generate_script(candidate)
    assert (run_dir / "damage.for").read_bytes() == source.read_bytes()
    assert str(run_dir / "damage.for") in script.read_text(encoding="utf-8")
    include = (run_dir / "pressure_hull_strength.inc").read_text(encoding="utf-8")
    assert "XC=1.050000000000D+03" in include
    assert "YT=2.800000000000D+01" in include
    assert all(len(line) <= 72 for line in include.splitlines())


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


def test_riks_controlled_post_peak_stop_requires_observed_decline() -> None:
    curve = [(0.0, 0.0), (1.0, 1.0), (2.0, 0.95), (3.0, 0.85), (4.0, 0.79)]
    evidence = classify_riks_limit_point(curve, "JOB_STATUS_TERMINATED_BY_USER", controlled_post_peak_stop=True)
    assert evidence["job_completed_successfully"] is False
    assert evidence["limit_point_confirmed"] is True
    assert evidence["increment_count"] == 4
    assert not classify_riks_limit_point(curve[:2], "JOB_STATUS_TERMINATED_BY_USER",
                                        controlled_post_peak_stop=True)["limit_point_confirmed"]


def test_stress_request_contains_every_ply_section_point() -> None:
    recorded = {}
    request = type("Request", (), {"setValues": lambda self, **values: recorded.update(values)})()
    model = type("Model", (), {"fieldOutputRequests": {"F-Output-1": request}})()
    configure_ply_stress_output(model, 40, damage=True)
    assert recorded["sectionPoints"] == tuple(range(1, 121))
    assert {"S", "SDV", "FV"}.issubset(recorded["variables"])


def test_stress_coverage_rejects_outer_surfaces_and_per_element_gaps() -> None:
    from types import SimpleNamespace as Item
    def frame(points):
        values = [Item(instance=Item(name="Shell"), elementLabel=element, integrationPoint=1,
                       sectionPoint=Item(number=point)) for element, point in points]
        return Item(fieldOutputs={"S": Item(values=values)})
    assert ply_stress_coverage(frame([(1, 1), (1, 120)]), 40)["status"] == "incomplete"
    assert ply_stress_coverage(frame([(1, n) for n in range(1, 121)]), 40)["status"] == "complete"
    assert ply_stress_coverage(frame([(1, n) for n in range(1, 61)] + [(2, n) for n in range(61, 121)]), 40)["status"] == "incomplete"


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


def test_completed_capacity_payload_keeps_both_exact_load_artifact_pairs() -> None:
    import ast
    import inspect
    from abaqus.runtime_build_pressure_hull import build_and_run
    tree = ast.parse(inspect.getsource(build_and_run))
    payloads = [node.value for node in ast.walk(tree) if isinstance(node, ast.Assign)
                and any(isinstance(target, ast.Name) and target.id == "payload" for target in node.targets)]
    output = payloads[-1]
    fields = {key.value: value for key, value in zip(output.keys, output.values)}
    for stage in ("service", "target"):
        for kind in ("odb", "inp"):
            expression = ast.unparse(fields[stage + "_" + kind])
            assert expression == f"{stage}_run['{kind}_path']"


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

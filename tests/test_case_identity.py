from __future__ import annotations

import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy

import pytest

from agents.knowledge_agent import KnowledgeAgent
from core import id_utils as ids
from core.fem_result_semantics import complete_case_result_errors


@pytest.fixture
def case_store(monkeypatch, tmp_path):
    import agents.knowledge_agent as knowledge

    cases = tmp_path / "cases"
    library = tmp_path / "library"
    cases.mkdir()
    library.mkdir()
    for module in (ids, knowledge):
        monkeypatch.setattr(module, "CASES_DIR", cases)
        monkeypatch.setattr(module, "CASE_LIBRARY_DIR", library)
    return cases, library


def complete_payload(tmp_path, candidate_id="C10", run_id="RUN_A"):
    coverage = {"status": "complete", "expected_section_points": 3,
                "incomplete_element_positions": 0, "checked_element_positions": 1}
    result = {
        "candidate_id": candidate_id, "run_id": run_id, "task_id": "TASK_1",
        "session_candidate_id": "TMP_1", "status": "success", "retry_count": 0,
        "verdict": "通过", "ultimate_pressure_MPa": 40.0,
        "riks_limit_point_confirmed": True, "riks_increment_count": 10,
        "progressive_damage_complete": True, "damage_state_output_complete": True,
        "service_pressure_check_status": "passed", "target_pressure_check_status": "passed",
        "service_stress_coverage": coverage, "target_stress_coverage": dict(coverage),
    }
    for field in ("postbuckling_inp", "postbuckling_odb", "service_inp", "service_odb", "target_inp", "target_odb",
                  "user_subroutine_path", "material_strength_include"):
        path = tmp_path / f"{candidate_id}_{field}"
        path.write_text("单元测试工件", encoding="utf-8")
        result[field] = str(path)
    return {
        "task": {"task_id": "TASK_1", "run_id": run_id},
        "design": {"candidate_id": candidate_id, "run_id": run_id, "task_id": "TASK_1",
                   "session_candidate_id": "TMP_1", "source": "DOE"},
        "abaqus_results": result,
    }


def isolated_agent(monkeypatch):
    agent = KnowledgeAgent.__new__(KnowledgeAgent)
    monkeypatch.setattr(agent, "_case_memory_index", lambda: None)
    monkeypatch.setattr(agent, "_maybe_retrain_surrogate", lambda: None)
    monkeypatch.setattr(agent, "emit", lambda *_args: None)
    return agent


def test_case_ids_follow_storage_order_not_solver_ids(case_store, monkeypatch, tmp_path):
    agent = isolated_agent(monkeypatch)
    first = agent.run(complete_payload(tmp_path, "C10", "RUN_A"))
    second = agent.run(complete_payload(tmp_path, "C12", "RUN_B"))
    assert [first["case_id"], second["case_id"]] == ["CASE_1", "CASE_2"]
    records = [json.loads(path.read_text(encoding="utf-8")) for path in sorted(case_store[0].glob("*.json"))]
    assert [record["candidate_id"] for record in records] == ["C10", "C12"]
    assert [record["run_id"] for record in records] == ["RUN_A", "RUN_B"]
    assert all(record["session_candidate_id"] == "TMP_1" for record in records)


def test_incomplete_results_do_not_consume_case_numbers(case_store, monkeypatch, tmp_path):
    agent = isolated_agent(monkeypatch)
    payload = complete_payload(tmp_path)
    payload["abaqus_results"]["target_stress_coverage"]["incomplete_element_positions"] = 1
    skipped = agent.run(payload)
    assert skipped["status"] == "not_stored_incomplete"
    assert skipped["case_id"] is None
    assert not list(case_store[0].glob("*.json"))
    payload["abaqus_results"]["target_stress_coverage"]["incomplete_element_positions"] = 0
    assert agent.run(payload)["case_id"] == "CASE_1"


def test_case_write_is_idempotent_and_rejects_changed_design(case_store, monkeypatch, tmp_path):
    agent = isolated_agent(monkeypatch)
    payload = complete_payload(tmp_path)
    assert agent.run(payload)["case_id"] == "CASE_1"
    assert agent.run(deepcopy(payload))["already_stored"] is True
    payload["design"]["geometry"] = {"length_mm": 123}
    with pytest.raises(ValueError, match="不同设计或结果"):
        agent.run(payload)
    assert len(list(case_store[0].glob("*.json"))) == 1


def test_case_rejects_conflicting_run_identity(case_store, monkeypatch, tmp_path):
    agent = isolated_agent(monkeypatch)
    payload = complete_payload(tmp_path)
    payload["abaqus_results"]["run_id"] = "RUN_B"
    with pytest.raises(ValueError, match="run_id"):
        agent.run(payload)
    assert not list(case_store[0].glob("*.json"))


def test_missing_artifacts_prevent_storage(case_store, monkeypatch, tmp_path):
    agent = isolated_agent(monkeypatch)
    payload = complete_payload(tmp_path)
    (tmp_path / "C10_target_odb").unlink()
    assert agent.run(payload)["status"] == "not_stored_incomplete"
    assert not list(case_store[0].glob("*.json"))


def test_unconfirmed_damage_peak_is_not_complete(tmp_path):
    result = complete_payload(tmp_path)["abaqus_results"]
    assert not complete_case_result_errors(result)
    result["riks_limit_point_confirmed"] = False
    assert complete_case_result_errors(result)


def test_solver_reservations_persist_before_solving(case_store):
    assert ids.reserve_candidate_ids(2) == ["C1", "C2"]
    assert ids.reserve_candidate_ids(1) == ["C3"]
    assert (ids.ABAQUS_RUNS_DIR / "C3").is_dir()


def test_solver_reservations_are_unique_between_threads(case_store):
    with ThreadPoolExecutor(max_workers=6) as pool:
        batches = list(pool.map(ids.reserve_candidate_ids, [3] * 6))
    reserved = [value for batch in batches for value in batch]
    assert len(set(reserved)) == 18
    assert sorted(ids.candidate_index(value) for value in reserved) == list(range(1, 19))


def test_solver_reservations_are_unique_between_processes(case_store):
    code = (
        "import sys,json; from pathlib import Path; from core import id_utils as i; "
        "i.ABAQUS_RUNS_DIR=Path(sys.argv[1]); i.CASES_DIR=Path(sys.argv[2]); "
        "i.CASE_LIBRARY_DIR=Path(sys.argv[3]); i.IO_DIR=Path(sys.argv[4]); "
        "print(json.dumps(i.reserve_candidate_ids(3)))"
    )
    processes = [subprocess.Popen(
        [sys.executable, "-B", "-c", code, str(ids.ABAQUS_RUNS_DIR), str(case_store[0]),
         str(case_store[1]), str(ids.IO_DIR)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    ) for _ in range(4)]
    reserved = []
    for process in processes:
        stdout, stderr = process.communicate(timeout=30)
        assert process.returncode == 0, stderr
        reserved.extend(json.loads(stdout))
    assert len(set(reserved)) == 12
    assert sorted(ids.candidate_index(value) for value in reserved) == list(range(1, 13))


def test_solver_sequence_is_independent_of_case_sequence(case_store):
    (case_store[0] / "CASE_500.json").write_text(
        json.dumps({"case_id": "CASE_500", "candidate_id": "C7"}), encoding="utf-8")
    assert ids.reserve_candidate_ids(1) == ["C8"]
    assert ids.next_case_id() == "CASE_501"


def test_report_files_are_isolated_by_run(monkeypatch, tmp_path):
    import agents.report_gen as reports

    monkeypatch.setenv("CSDM_cph_DISABLE_LLM_AUTO", "1")
    monkeypatch.setattr(reports, "RESULTS_DIR", tmp_path)
    agent = reports.ReportGenAgent()
    monkeypatch.setattr(agent, "_render_markdown", lambda task, *_args: task["run_id"])
    monkeypatch.setattr(agent, "_write_pdf", lambda *_args: None)
    first = agent.run({"task": {"run_id": "RUN_A"}})
    saved = (tmp_path / "RUN_A/overall_design_report.md").read_bytes()
    second = agent.run({"task": {"run_id": "RUN_B"}})
    assert first["markdown_path"] != second["markdown_path"]
    assert (tmp_path / "RUN_A/overall_design_report.md").read_bytes() == saved
    assert (tmp_path / "RUN_B/overall_design_report.md").read_text(encoding="utf-8") == "RUN_B"

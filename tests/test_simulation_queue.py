from __future__ import annotations

from workflow.simulation_queue import SimulationJobQueue


def test_simulation_queue_tracks_success_and_failure(tmp_path):
    queue = SimulationJobQueue(tmp_path / "workflow.sqlite3")

    job_id = queue.enqueue("RUN_TEST", {"candidate_id": "TMP_1", "source": "DOE"})
    queue.mark_running(job_id)
    queue.mark_success(job_id, {"candidate_id": "C1", "ultimate_pressure_MPa": 42.5, "verdict": "通过"})

    failed_id = queue.enqueue("RUN_TEST", {"candidate_id": "TMP_2", "source": "LLM"})
    queue.mark_running(failed_id)
    queue.mark_failed(failed_id, "Abaqus 作业失败")

    jobs = queue.list_jobs("RUN_TEST")

    assert [job["status"] for job in jobs] == ["success", "failed"]
    assert jobs[0]["session_candidate_id"] == "TMP_1"
    assert jobs[0]["formal_candidate_id"] == "C1"
    assert jobs[0]["result"]["ultimate_pressure_MPa"] == 42.5
    assert jobs[1]["error_message"] == "Abaqus 作业失败"

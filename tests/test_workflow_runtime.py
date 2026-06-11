from __future__ import annotations

from workflow.event_store import WorkflowEventStore
from workflow.runtime import DesignWorkflowRuntime


class FakeOrchestrator:
    def __init__(self) -> None:
        self.progress_callback = None
        self.calls: list[str] = []
        self.screener = type("Screener", (), {"score_formula_text": "score = P_ult"})()

    def _emit(self, sender: str, message: str, event_type: str) -> None:
        if self.progress_callback:
            self.progress_callback(sender, message, {"event_type": event_type, "payload": {"sender": sender}})

    def parse_instruction(self, instruction, overrides=None):
        self.calls.append("parse")
        self._emit("ORCHESTRATOR", "任务已解析", "task_parsed")
        return {
            "task_id": "TASK_TEST",
            "application": "复合材料外压圆柱耐压壳",
            "candidate_generation_preferences": {"total_candidates": 2},
            "screening_preferences": {"top_k_candidates": 1},
            "load_conditions": {"type": "external_pressure", "external_pressure_MPa": 30.0},
            "boundary_conditions": {"type": "END_CLAMPED"},
            "design_targets": {"ultimate_pressure_min_MPa": 35.0},
        }

    def generate_candidates(self, task):
        self.calls.append("generate")
        self._emit("CANDIDATE_GEN", "候选已生成", "candidate_generation_completed")
        return [
            {"candidate_id": "TMP_1", "display_name": "TMP_1", "source": "LLM"},
            {"candidate_id": "TMP_2", "display_name": "TMP_2", "source": "DOE"},
        ]

    def screen_candidates(self, task, candidates):
        self.calls.append("screen")
        self._emit("SCREENER", "初筛已完成", "screening_completed")
        return [dict(candidates[0], rank_score=42.0)]

    def evaluate_candidate(self, task, candidate):
        self.calls.append(f"evaluate:{candidate['candidate_id']}")
        self._emit("FEM", "有限元已完成", "fem_completed")
        return {
            "candidate_id": "C1",
            "session_candidate_id": candidate["candidate_id"],
            "status": "success",
            "ultimate_pressure_MPa": 40.0,
            "verdict": "通过",
        }

    def generate_report(self, task, results, candidates=None):
        self.calls.append("report")
        self._emit("REPORT", "报告已生成", "report_completed")
        return {"markdown_path": "data/results/latest_report.md", "pdf_path": "data/results/latest_report.pdf"}


def test_workflow_runtime_persists_and_resumes_without_repeating_completed_nodes(tmp_path):
    store = WorkflowEventStore(tmp_path / "workflow.sqlite3")
    orchestrator = FakeOrchestrator()
    runtime = DesignWorkflowRuntime(orchestrator=orchestrator, event_store=store)

    state = runtime.start("生成 2 个候选，初筛保留 1 个候选")

    assert state["stage"] == "awaiting_screen_confirmation"
    assert state["pending_confirmation"] == "screen_candidates"
    assert state["source_counter"] == {"DOE": 1, "LLM": 1}
    assert orchestrator.calls == ["parse", "generate"]

    resumed = runtime.resume(state["run_id"])
    assert resumed["stage"] == "awaiting_screen_confirmation"
    assert resumed["candidates"][0]["candidate_id"] == "TMP_1"

    next_state = runtime.continue_after_confirmation(state["run_id"], True)

    assert next_state["stage"] == "awaiting_fem_confirmation"
    assert next_state["pending_confirmation"] == "fem_evaluation"
    assert [candidate["candidate_id"] for candidate in next_state["evaluated_candidates"]] == ["TMP_1"]
    assert orchestrator.calls == ["parse", "generate", "screen"]

    paused = runtime.continue_after_confirmation(next_state["run_id"], False)

    assert paused["stage"] == "paused_before_fem"
    assert paused["pending_confirmation"] is None
    assert orchestrator.calls == ["parse", "generate", "screen"]

    event_types = [event["event_type"] for event in store.list_events(state["run_id"])]
    assert "workflow_started" in event_types
    assert "tool_started" in event_types
    assert "tool_completed" in event_types
    assert "human_confirmation" in event_types


def test_workflow_runtime_completes_full_approved_path(tmp_path):
    store = WorkflowEventStore(tmp_path / "workflow.sqlite3")
    orchestrator = FakeOrchestrator()
    runtime = DesignWorkflowRuntime(orchestrator=orchestrator, event_store=store)

    state = runtime.start("生成 2 个候选，初筛保留 1 个候选")
    state = runtime.continue_after_confirmation(state, True)
    state = runtime.continue_after_confirmation(state, True)
    state = runtime.continue_after_confirmation(state, True)

    assert state["stage"] == "completed"
    assert state["pending_confirmation"] is None
    assert state["results"][0]["ultimate_pressure_MPa"] == 40.0
    assert state["report"]["markdown_path"].endswith("latest_report.md")
    assert orchestrator.calls == ["parse", "generate", "screen", "evaluate:TMP_1", "report"]

    stored = store.load_snapshot(state["run_id"])
    assert stored["stage"] == "completed"
    assert stored["report"]["pdf_path"].endswith("latest_report.pdf")

    jobs = runtime.simulation_queue.list_jobs(state["run_id"])
    assert len(jobs) == 1
    assert jobs[0]["session_candidate_id"] == "TMP_1"
    assert jobs[0]["formal_candidate_id"] == "C1"
    assert jobs[0]["status"] == "success"
    event_types = [event["event_type"] for event in store.list_events(state["run_id"])]
    assert "simulation_job_queued" in event_types
    assert "simulation_job_completed" in event_types

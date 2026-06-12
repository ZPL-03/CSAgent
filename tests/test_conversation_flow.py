from __future__ import annotations

from pathlib import Path

from core.conversation_flow import ConversationFlowController
from tests.test_workflow_runtime import FakeOrchestrator
from workflow.event_store import WorkflowEventStore


REALISTIC_INSTRUCTION = (
    "请为复合材料外压圆柱耐压壳设计方案，外压 30 MPa，"
    "极限压力不低于 35 MPa，生成 2 个候选，初筛保留 1 个候选"
)


def _controller(tmp_path: Path):
    events: list[tuple[str, str, dict]] = []
    orchestrator = FakeOrchestrator()
    store = WorkflowEventStore(tmp_path / "workflow.sqlite3")
    controller = ConversationFlowController(
        orchestrator,
        event_callback=lambda event_type, message, payload: events.append((event_type, message, payload)),
        event_store=store,
    )
    return controller, orchestrator, store, events


def _runtime_events(events: list[tuple[str, str, dict]]) -> list[dict]:
    return [payload for event_type, _message, payload in events if event_type == "workflow_runtime_event"]


def _runtime_event_types(events: list[tuple[str, str, dict]]) -> set[str]:
    return {payload["runtime_event_type"] for payload in _runtime_events(events)}


def _runtime_stages(events: list[tuple[str, str, dict]]) -> set[str]:
    return {payload.get("runtime_stage", "") for payload in _runtime_events(events)}


def test_conversation_flow_emits_human_confirmed_full_path(tmp_path):
    controller, orchestrator, store, events = _controller(tmp_path)

    state = controller.start(REALISTIC_INSTRUCTION)

    assert state.workflow_run_id
    assert state.stage == "awaiting_screen_confirmation"
    assert state.pending_confirmation == "screen_candidates"
    high_level = [event for event in events if event[0] != "workflow_runtime_event"]
    runtime_events = _runtime_events(events)
    assert [event[0] for event in high_level[:4]] == [
        "conversation_started",
        "task_summary",
        "assistant_commentary",
        "candidate_summary",
    ]
    assert high_level[-1][0] == "confirmation_requested"
    assert high_level[-1][2]["confirmation_id"] == "screen_candidates"
    assert any(item["runtime_event_type"] == "node_started" for item in runtime_events)
    assert any(item["runtime_event_type"] == "tool_completed" for item in runtime_events)
    assert {"parse_task", "generate_candidates", "wait_screen"}.issubset(_runtime_stages(events))

    state = controller.continue_after_confirmation(state, True)

    assert state.stage == "awaiting_fem_confirmation"
    assert state.pending_confirmation == "fem_evaluation"
    assert state.evaluated_candidates[0]["candidate_id"] == "TMP_1"
    assert any(event_type == "screening_summary" for event_type, _, _ in events)
    high_level = [event for event in events if event[0] != "workflow_runtime_event"]
    assert high_level[-1][0] == "confirmation_requested"
    assert high_level[-1][2]["confirmation_id"] == "fem_evaluation"
    assert {"screen_candidates", "wait_fem"}.issubset(_runtime_stages(events))

    state = controller.continue_after_confirmation(state, True)

    assert state.stage == "awaiting_report_confirmation"
    assert state.pending_confirmation == "export_report"
    assert state.results[0]["candidate_id"] == "C1"
    assert state.knowledge_updates[0]["case_id"] == "CASE_100"
    assert any(event_type == "fem_summary" for event_type, _, _ in events)
    high_level = [event for event in events if event[0] != "workflow_runtime_event"]
    assert high_level[-1][0] == "confirmation_requested"
    assert high_level[-1][2]["confirmation_id"] == "export_report"
    assert {"evaluate_candidates", "persist_knowledge", "wait_report"}.issubset(_runtime_stages(events))
    assert {"simulation_job_queued", "simulation_job_started", "simulation_job_completed"}.issubset(
        _runtime_event_types(events)
    )

    state = controller.continue_after_confirmation(state, True)

    assert state.stage == "completed"
    assert state.pending_confirmation is None
    assert state.report["markdown_path"].endswith("latest_report.md")
    high_level = [event for event in events if event[0] != "workflow_runtime_event"]
    assert high_level[-2][0] == "report_summary"
    assert high_level[-1][0] == "assistant_commentary"
    assert orchestrator.calls == ["parse", "generate", "screen", "evaluate:TMP_1", "knowledge", "report"]
    assert "generate_report" in _runtime_stages(events)

    stored = store.load_snapshot(state.workflow_run_id)
    assert stored["stage"] == "completed"
    assert stored["instruction"] == REALISTIC_INSTRUCTION
    assert stored["candidates"][0]["candidate_id"] == "TMP_1"
    assert stored["screened_candidates"][0]["candidate_id"] == "TMP_1"
    assert stored["fem_designs"][0]["candidate_id"] == "C1"
    assert stored["fem_designs"][0]["session_candidate_id"] == "TMP_1"
    assert store.list_runs(limit=1)[0]["status"] == "completed"


def test_conversation_flow_pause_before_fem_keeps_screened_candidates(tmp_path):
    controller, orchestrator, store, events = _controller(tmp_path)

    state = controller.start(REALISTIC_INSTRUCTION)
    state = controller.continue_after_confirmation(state, True)
    state = controller.continue_after_confirmation(state, False)

    assert state.stage == "paused_before_fem"
    assert state.pending_confirmation is None
    assert state.evaluated_candidates[0]["candidate_id"] == "TMP_1"
    assert orchestrator.calls == ["parse", "generate", "screen"]
    high_level = [event for event in events if event[0] != "workflow_runtime_event"]
    assert high_level[-2][0] == "conversation_paused"
    assert high_level[-1][0] == "assistant_commentary"
    assert store.list_runs(limit=1)[0]["status"] == "paused"
    stored = store.load_snapshot(state.workflow_run_id)
    assert stored["instruction"] == REALISTIC_INSTRUCTION
    assert stored["stage"] == "paused_before_fem"
    assert stored["evaluated_candidates"][0]["candidate_id"] == "TMP_1"

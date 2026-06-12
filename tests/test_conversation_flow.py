from __future__ import annotations

from pathlib import Path

from core.conversation_flow import ConversationFlowController
from tests.test_workflow_runtime import FakeOrchestrator
from workflow.event_store import WorkflowEventStore


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


def test_conversation_flow_emits_human_confirmed_full_path(tmp_path):
    controller, orchestrator, store, events = _controller(tmp_path)

    state = controller.start("生成 2 个候选，初筛保留 1 个候选")

    assert state.workflow_run_id
    assert state.stage == "awaiting_screen_confirmation"
    assert state.pending_confirmation == "screen_candidates"
    high_level = [event for event in events if event[0] != "workflow_runtime_event"]
    runtime_events = [event for event in events if event[0] == "workflow_runtime_event"]
    assert [event[0] for event in high_level[:4]] == [
        "conversation_started",
        "task_summary",
        "assistant_commentary",
        "candidate_summary",
    ]
    assert high_level[-1][0] == "confirmation_requested"
    assert high_level[-1][2]["confirmation_id"] == "screen_candidates"
    assert any(item[2]["runtime_event_type"] == "node_started" for item in runtime_events)
    assert any(item[2]["runtime_event_type"] == "tool_completed" for item in runtime_events)

    state = controller.continue_after_confirmation(state, True)

    assert state.stage == "awaiting_fem_confirmation"
    assert state.pending_confirmation == "fem_evaluation"
    assert state.evaluated_candidates[0]["candidate_id"] == "TMP_1"
    assert any(event_type == "screening_summary" for event_type, _, _ in events)
    high_level = [event for event in events if event[0] != "workflow_runtime_event"]
    assert high_level[-1][0] == "confirmation_requested"
    assert high_level[-1][2]["confirmation_id"] == "fem_evaluation"

    state = controller.continue_after_confirmation(state, True)

    assert state.stage == "awaiting_report_confirmation"
    assert state.pending_confirmation == "export_report"
    assert state.results[0]["candidate_id"] == "C1"
    assert state.knowledge_updates[0]["case_id"] == "CASE_100"
    assert any(event_type == "fem_summary" for event_type, _, _ in events)
    high_level = [event for event in events if event[0] != "workflow_runtime_event"]
    assert high_level[-1][0] == "confirmation_requested"
    assert high_level[-1][2]["confirmation_id"] == "export_report"

    state = controller.continue_after_confirmation(state, True)

    assert state.stage == "completed"
    assert state.pending_confirmation is None
    assert state.report["markdown_path"].endswith("latest_report.md")
    high_level = [event for event in events if event[0] != "workflow_runtime_event"]
    assert high_level[-2][0] == "report_summary"
    assert high_level[-1][0] == "assistant_commentary"
    assert orchestrator.calls == ["parse", "generate", "screen", "evaluate:TMP_1", "knowledge", "report"]

    stored = store.load_snapshot(state.workflow_run_id)
    assert stored["stage"] == "completed"
    assert store.list_runs(limit=1)[0]["status"] == "completed"


def test_conversation_flow_pause_before_fem_keeps_screened_candidates(tmp_path):
    controller, orchestrator, store, events = _controller(tmp_path)

    state = controller.start("生成 2 个候选，初筛保留 1 个候选")
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

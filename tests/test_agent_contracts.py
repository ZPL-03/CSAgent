from __future__ import annotations

from workflow.agent_contracts import list_agent_contracts
from workflow.event_store import WorkflowEventStore
from workflow.runtime import DesignWorkflowRuntime


class ContractFakeOrchestrator:
    def __init__(self) -> None:
        self.progress_callback = None

    def parse_instruction(self, instruction, overrides=None):
        return {}

    def generate_candidates(self, task):
        return []

    def screen_candidates(self, task, candidates):
        return []

    def prepare_candidate_for_fem(self, task, candidate):
        return candidate

    def evaluate_prepared_candidate(self, task, candidate):
        return {}

    def persist_knowledge_records(self, task, designs, results):
        return []

    def generate_report(self, task, results, candidates=None):
        return {}


def test_agent_contracts_match_registered_tools(tmp_path) -> None:
    runtime = DesignWorkflowRuntime(
        orchestrator=ContractFakeOrchestrator(),
        event_store=WorkflowEventStore(tmp_path / "workflow.sqlite3"),
    )
    contracts = list_agent_contracts()
    tools = {item["name"]: item for item in runtime.tools.describe()}

    assert {contract.tool_name for contract in contracts} == set(tools)
    assert {contract.node_name for contract in contracts} == {
        "parse_task",
        "generate_candidates",
        "screen_candidates",
        "evaluate_candidates",
        "persist_knowledge",
        "generate_report",
    }

    for contract in contracts:
        registered = tools[contract.tool_name]
        assert registered["agent"] == contract.runtime_agent
        assert contract.responsibility in registered["description"]
        assert contract.input_contract
        assert contract.output_contract
        assert contract.llm_policy
        assert contract.memory_policy
        assert contract.event_policy
        assert contract.failure_policy
        assert any(
            token in contract.memory_policy
            for token in ("workflow_snapshots", "simulation_jobs", "data/cases", "data/results")
        )
        assert "node_failed" in contract.event_policy

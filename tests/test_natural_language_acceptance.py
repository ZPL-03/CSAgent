from __future__ import annotations

import os
from copy import deepcopy

import pytest

from agents.orchestrator import OrchestratorAgent
from core.conversation_flow import ConversationFlowController
from core.id_utils import candidate_index
from core.task_contract import (
    requested_candidate_pool_size,
    requested_screen_top_k,
    task_payload_from_request,
)
from workflow.event_store import WorkflowEventStore
from scripts.run_natural_language_acceptance import (
    _assert_unique_candidates as _assert_unique,
    _candidate_signature,
    _select_instruction_cases,
)


def test_acceptance_signature_preserves_radius_reference():
    candidate = {"hull_type": "CYLINDRICAL", "material_system": {"name": "T700/Epoxy"},
                 "geometry": {"radius_mm": 150, "radius_reference": "inner", "imperfection_ratio": 0.008},
                 "layup": {"layup": "[45/-45]"}}
    alternate = deepcopy(candidate)
    alternate["geometry"]["radius_reference"] = "middle_surface"
    assert _candidate_signature(candidate) != _candidate_signature(alternate)
    _assert_unique([candidate, alternate])
    with pytest.raises(AssertionError, match="重复"):
        _assert_unique([candidate, deepcopy(candidate)])


def _patch_fem_boundary(monkeypatch, orchestrator: OrchestratorAgent, tmp_path) -> None:
    """替换外部 Abaqus 边界，保留正式候选、事件和报告流程。"""

    def evaluate_prepared_candidate(task, candidate):
        ultimate_pressure = float(candidate["surrogate_ultimate_pressure_MPa"])
        linear_pressure = float(candidate["asme_linear_buckling_pressure_MPa"])
        return {
            "candidate_id": candidate["candidate_id"],
            "display_name": candidate["display_name"],
            "session_candidate_id": candidate["session_candidate_id"],
            "status": "success",
            "verdict": "通过",
            "linear_buckling_pressure_MPa": linear_pressure,
            "ultimate_pressure_MPa": ultimate_pressure,
            "failure_mode": "test_fem_boundary",
            "solved_design": deepcopy(candidate),
        }

    def persist_knowledge_records(task, fem_designs, results):
        return [
            {
                "status": "stored",
                "case_id": f"CASE_TEST_{index}",
                "candidate_id": design["candidate_id"],
                "session_candidate_id": design["session_candidate_id"],
            }
            for index, design in enumerate(fem_designs, start=1)
        ]

    def generate_report(task, results, candidates=None):
        markdown_path = tmp_path / "acceptance_report.md"
        pdf_path = tmp_path / "acceptance_report.pdf"
        markdown_path.write_text("# CSAgent 耐压壳设计报告\n\n验收报告。", encoding="utf-8")
        pdf_path.write_bytes(b"%PDF-1.4\n% acceptance\n")
        artifact = {
            "markdown_path": str(markdown_path), "pdf_path": str(pdf_path),
            "title": "CSAgent 总体设计方案报告", "report_kind": "overall",
            "markdown_generated": True, "pdf_generated": True,
        }
        return {
            **artifact, "content": markdown_path.read_text(encoding="utf-8"),
            "llm_explanation_used": False, "report_outputs": {"overall": artifact},
        }
    monkeypatch.setattr(orchestrator, "evaluate_prepared_candidate", evaluate_prepared_candidate)
    monkeypatch.setattr(orchestrator, "persist_knowledge_records", persist_knowledge_records)
    monkeypatch.setattr(orchestrator, "generate_report", generate_report)


def test_acceptance_runner_can_limit_default_case_count() -> None:
    cases = [{"instruction": f"case {index}"} for index in range(5)]

    assert _select_instruction_cases(cases, 0) == cases
    assert _select_instruction_cases(cases, None) == cases
    assert _select_instruction_cases(cases, 2) == cases[:2]

    with pytest.raises(ValueError, match="max-cases"):
        _select_instruction_cases(cases, -1)


@pytest.mark.parametrize(
    ("instruction", "expected"),
    [
        (
            "请为复合材料外压圆柱耐压壳设计方案，外压 30 MPa，生成 12 个候选，初筛保留 5 个候选",
            {
                "pressure": 30.0,
                "total": 12,
                "top_k": 5,
                "boundary_type": "END_CLAMPED",
                "has_geometry_reference": False,
                "has_fixed_geometry": False,
            },
        ),
        (
            "请为深海潜器复合材料外压圆柱耐压壳设计方案，外压 28 MPa，生成 8 个候选，初筛保留 3 个候选，两端简支",
            {
                "pressure": 28.0,
                "total": 8,
                "top_k": 3,
                "boundary_type": "END_SIMPLY_SUPPORTED",
                "has_geometry_reference": False,
                "has_fixed_geometry": False,
            },
        ),
        (
            "复合材料外压圆柱耐压壳，目标工况外压 35 MPa，要求两端固支，生成 8 个候选，初筛保留 3 个候选",
            {
                "pressure": 35.0,
                "total": 8,
                "top_k": 3,
                "boundary_type": "END_CLAMPED",
                "has_geometry_reference": False,
                "has_fixed_geometry": False,
            },
        ),
        (
            "Design a composite external-pressure cylindrical pressure hull, external pressure 25 MPa, generate 8 candidates, keep 3 after screening, simply supported ends",
            {
                "pressure": 25.0,
                "total": 8,
                "top_k": 3,
                "boundary_type": "END_SIMPLY_SUPPORTED",
                "has_geometry_reference": False,
                "has_fixed_geometry": False,
            },
        ),
        (
            "Design a composite external-pressure cylindrical pressure hull for 25 MPa hydrostatic pressure, simply supported ends, generate 8 candidates and retain 3 screened candidates.",
            {
                "pressure": 25.0,
                "total": 8,
                "top_k": 3,
                "boundary_type": "END_SIMPLY_SUPPORTED",
                "has_geometry_reference": False,
                "has_fixed_geometry": False,
            },
        ),
        (
            "Composite pressure hull preliminary design: external pressure 40 MPa, generate 8 candidate designs and retain 3 screened candidates.",
            {
                "pressure": 40.0,
                "total": 8,
                "top_k": 3,
                "boundary_type": "END_CLAMPED",
                "has_geometry_reference": False,
                "has_fixed_geometry": False,
            },
        ),
        (
            "设计一个外压圆柱耐压壳，外压 24 MPa，半径约 120 mm，长度约 600 mm，生成 8 个候选，预筛 4 个进入校核",
            {
                "pressure": 24.0,
                "total": 8,
                "top_k": 4,
                "boundary_type": "END_CLAMPED",
                "has_geometry_reference": True,
                "has_fixed_geometry": False,
            },
        ),
        (
            "面向深海外压工况给出复合材料耐压壳方案，外压 18 MPa，生成 6 个候选，初筛 3 个",
            {
                "pressure": 18.0,
                "total": 6,
                "top_k": 3,
                "boundary_type": "END_CLAMPED",
                "has_geometry_reference": False,
                "has_fixed_geometry": False,
            },
        ),
        (
            "外压 32 MPa，长度 520 mm，半径 105 mm，厚度 11 mm，候选池 8 个，初筛 Top-3",
            {
                "pressure": 32.0,
                "total": 8,
                "top_k": 3,
                "boundary_type": "END_CLAMPED",
                "has_geometry_reference": False,
                "has_fixed_geometry": True,
            },
        ),
    ],
)
def test_multi_natural_language_inputs_run_candidate_and_screening_pipeline(monkeypatch, instruction, expected):
    monkeypatch.setenv("CSDM_cph_DISABLE_LLM_AUTO", "1")
    orchestrator = OrchestratorAgent()

    task = orchestrator.parse_instruction(instruction)
    payload = task_payload_from_request(task)

    assert requested_candidate_pool_size(task) == expected["total"]
    assert requested_screen_top_k(task) == expected["top_k"]
    assert payload["load_conditions"]["external_pressure_MPa"] == expected["pressure"]
    assert payload["boundary_conditions"]["type"] == expected["boundary_type"]

    facts = payload["user_input_facts"]
    assert ("geometry_reference" in facts) is expected["has_geometry_reference"]
    assert ("fixed_geometry" in facts) is expected["has_fixed_geometry"]

    candidates = orchestrator.generate_candidates(task)
    assert len(candidates) == expected["total"]
    assert all(candidate["candidate_id"] == candidate["display_name"] for candidate in candidates)
    assert all(not candidate.get("persistent_candidate_id") for candidate in candidates)
    assert all(candidate["rule_check"]["is_valid"] for candidate in candidates)
    _assert_unique(candidates)

    audit = orchestrator.candidate_gen.last_generation_audit
    assert audit["source_targets"]["total"] == expected["total"]
    assert audit["source_targets"]["LLM"] + audit["source_targets"]["CASE_TRANSFER"] + audit["source_targets"]["DOE"] == expected["total"]
    assert audit["duplicate_counts"]["total"] >= 0
    assert sum(audit["added_counts"].values()) == expected["total"]

    screened = orchestrator.screen_candidates(task, candidates)
    assert len(screened) == expected["top_k"]
    assert all(candidate["candidate_id"] == candidate["display_name"] for candidate in screened)
    assert all(candidate["asme_linear_buckling_pressure_MPa"] is not None for candidate in screened)
    assert all(candidate["surrogate_PBIPF_MPa"] is not None for candidate in screened)
    assert all(candidate["surrogate_ultimate_pressure_MPa"] is not None for candidate in screened)
    assert all(candidate["selection_reason"] for candidate in screened)
    _assert_unique(screened)


@pytest.mark.parametrize(
    "instruction",
    [
        "请为复合材料外压圆柱耐压壳设计方案，外压 30 MPa，生成 4 个候选，初筛保留 2 个候选",
        "Design a composite external-pressure cylindrical pressure hull, external pressure 26 MPa, generate 4 candidates, keep 2 after screening",
    ],
)
def test_natural_language_inputs_complete_workflow_with_fem_contract(monkeypatch, tmp_path, instruction):
    monkeypatch.setenv("CSDM_cph_DISABLE_LLM_AUTO", "1")
    orchestrator = OrchestratorAgent()
    _patch_fem_boundary(monkeypatch, orchestrator, tmp_path)
    events: list[tuple[str, str, dict]] = []
    store = WorkflowEventStore(tmp_path / "workflow.sqlite3")
    controller = ConversationFlowController(
        orchestrator,
        event_callback=lambda event_type, message, payload: events.append((event_type, message, payload)),
        event_store=store,
    )

    state = controller.start(instruction)

    assert state.workflow_run_id
    assert state.stage == "awaiting_screen_confirmation"
    assert state.pending_confirmation == "screen_candidates"
    assert len(state.candidates) == 4
    assert all(candidate["rule_check"]["is_valid"] for candidate in state.candidates)
    _assert_unique(state.candidates)

    state = controller.continue_after_confirmation(state, True)

    assert state.stage == "awaiting_fem_confirmation"
    assert state.pending_confirmation == "fem_evaluation"
    assert len(state.evaluated_candidates) == 2
    assert all(candidate["asme_linear_buckling_pressure_MPa"] for candidate in state.evaluated_candidates)
    assert all(candidate["surrogate_PBIPF_MPa"] for candidate in state.evaluated_candidates)

    state = controller.continue_after_confirmation(state, True)

    assert state.stage == "awaiting_report_confirmation"
    assert state.pending_confirmation == "export_report"
    assert len(state.results) == len(state.evaluated_candidates)
    assert all(candidate_index(result["candidate_id"]) is not None for result in state.results)
    assert len({result["candidate_id"] for result in state.results}) == len(state.results)
    assert all(result["session_candidate_id"].startswith("TMP_") for result in state.results)
    assert state.knowledge_updates[0]["case_id"] == "CASE_TEST_1"

    state = controller.continue_after_confirmation(state, True)

    assert state.stage == "completed"
    assert state.pending_confirmation is None
    assert state.report and state.report["markdown_path"].endswith("acceptance_report.md")
    assert set(state.report["report_outputs"]) == {"overall"}
    for payload in state.report["report_outputs"].values():
        assert os.path.exists(payload["markdown_path"])
        assert os.path.exists(payload["pdf_path"])

    snapshot = store.load_snapshot(state.workflow_run_id)
    assert snapshot["stage"] == "completed"
    assert snapshot["instruction"] == instruction
    assert len(snapshot["candidates"]) == 4
    assert len(snapshot["screened_candidates"]) == 2
    assert snapshot["fem_designs"][0]["session_candidate_id"].startswith("TMP_")
    assert snapshot["knowledge_updates"][0]["status"] == "stored"
    assert store.list_runs(limit=1)[0]["status"] == "completed"
    runtime_event_types = {
        payload["runtime_event_type"]
        for event_type, _message, payload in events
        if event_type == "workflow_runtime_event"
    }
    assert {
        "node_started",
        "tool_started",
        "tool_completed",
        "simulation_job_queued",
        "simulation_job_completed",
    }.issubset(runtime_event_types)

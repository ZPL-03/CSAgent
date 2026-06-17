from __future__ import annotations

import os
from collections.abc import Iterable

import pytest

from agents.orchestrator import OrchestratorAgent
from core.conversation_flow import ConversationFlowController
from core.task_contract import (
    requested_candidate_pool_size,
    requested_screen_top_k,
    task_payload_from_request,
)
from workflow.event_store import WorkflowEventStore


def _signature(candidate: dict) -> tuple:
    geometry = candidate.get("geometry") or {}
    material = candidate.get("material_system") or {}
    layup = candidate.get("layup") or {}
    return (
        candidate.get("hull_type"),
        material.get("material_key") or material.get("name"),
        tuple(
            (key, round(float(value), 6 if key == "imperfection_ratio" else 3))
            for key, value in sorted(geometry.items())
            if value is not None
        ),
        layup.get("template_name"),
        layup.get("layup"),
    )


def _assert_unique(candidates: Iterable[dict]) -> None:
    signatures = [_signature(candidate) for candidate in candidates]
    assert len(signatures) == len(set(signatures))


def _patch_deterministic_downstream(monkeypatch, orchestrator: OrchestratorAgent, tmp_path) -> None:
    def prepare_candidate_for_fem(task, candidate):
        return {
            **candidate,
            "candidate_id": "C_TEST",
            "display_name": "C_TEST",
            "session_candidate_id": candidate["candidate_id"],
        }

    def evaluate_prepared_candidate(task, candidate):
        predicted = float(candidate.get("surrogate_ultimate_pressure_MPa") or 45.0)
        return {
            "candidate_id": candidate["candidate_id"],
            "display_name": candidate["display_name"],
            "session_candidate_id": candidate["session_candidate_id"],
            "status": "success",
            "verdict": "通过",
            "linear_buckling_pressure_MPa": float(candidate.get("asme_linear_buckling_pressure_MPa") or predicted),
            "ultimate_pressure_MPa": round(max(predicted, 45.0), 3),
            "failure_mode": "deterministic_acceptance_adapter",
        }

    def persist_knowledge_records(task, fem_designs, results):
        return [
            {
                "status": "stored",
                "case_id": "CASE_ACCEPTANCE",
                "candidate_id": fem_designs[0]["candidate_id"],
                "session_candidate_id": fem_designs[0]["session_candidate_id"],
            }
        ]

    def generate_report(task, results, candidates=None):
        markdown_path = tmp_path / "acceptance_report.md"
        pdf_path = tmp_path / "acceptance_report.pdf"
        markdown_path.write_text("# CSAgent 耐压壳设计报告\n\n验收报告。", encoding="utf-8")
        pdf_path.write_bytes(b"%PDF-1.4\n% acceptance\n")
        report_outputs = {}
        for key, title in {
            "overall": "CSAgent 总体设计报告",
            "fem": "CSAgent FEM 校核报告",
            "design_solution": "CSAgent 推荐设计方案",
        }.items():
            artifact_markdown = tmp_path / f"{key}_acceptance.md"
            artifact_pdf = tmp_path / f"{key}_acceptance.pdf"
            artifact_markdown.write_text(f"# {title}\n\n验收交付件。", encoding="utf-8")
            artifact_pdf.write_bytes(b"%PDF-1.4\n% acceptance artifact\n")
            report_outputs[key] = {
                "markdown_path": str(artifact_markdown),
                "pdf_path": str(artifact_pdf),
                "title": title,
                "report_kind": key,
                "markdown_generated": True,
                "pdf_generated": True,
            }
        return {
            "markdown_path": str(markdown_path),
            "pdf_path": str(pdf_path),
            "content": markdown_path.read_text(encoding="utf-8"),
            "llm_explanation_used": False,
            "report_kind": "all",
            "report_outputs": report_outputs,
        }

    monkeypatch.setattr(orchestrator, "prepare_candidate_for_fem", prepare_candidate_for_fem)
    monkeypatch.setattr(orchestrator, "evaluate_prepared_candidate", evaluate_prepared_candidate)
    monkeypatch.setattr(orchestrator, "persist_knowledge_records", persist_knowledge_records)
    monkeypatch.setattr(orchestrator, "generate_report", generate_report)


@pytest.mark.parametrize(
    ("instruction", "expected"),
    [
        (
            "请为复合材料外压圆柱耐压壳设计方案，外压 30 MPa，极限压力不低于 35 MPa，生成 12 个候选，初筛保留 5 个候选",
            {
                "pressure": 30.0,
                "target": 35.0,
                "total": 12,
                "top_k": 5,
                "boundary_type": "END_CLAMPED",
                "has_geometry_reference": False,
                "has_fixed_geometry": False,
            },
        ),
        (
            "请为深海潜器复合材料外压圆柱耐压壳设计方案，外压 28 MPa，极限压力目标不低于 36 MPa，生成 8 个候选，初筛保留 3 个候选，两端简支",
            {
                "pressure": 28.0,
                "target": 36.0,
                "total": 8,
                "top_k": 3,
                "boundary_type": "END_SIMPLY_SUPPORTED",
                "has_geometry_reference": False,
                "has_fixed_geometry": False,
            },
        ),
        (
            "复合材料外压圆柱耐压壳，目标工况外压 35 MPa，极限压力不少于 45 MPa，要求两端固支，生成 8 个候选，初筛保留 3 个候选",
            {
                "pressure": 35.0,
                "target": 45.0,
                "total": 8,
                "top_k": 3,
                "boundary_type": "END_CLAMPED",
                "has_geometry_reference": False,
                "has_fixed_geometry": False,
            },
        ),
        (
            "Design a composite external-pressure cylindrical pressure hull, external pressure 25 MPa, ultimate pressure at least 40 MPa, generate 8 candidates, keep 3 after screening, simply supported ends",
            {
                "pressure": 25.0,
                "target": 40.0,
                "total": 8,
                "top_k": 3,
                "boundary_type": "END_SIMPLY_SUPPORTED",
                "has_geometry_reference": False,
                "has_fixed_geometry": False,
            },
        ),
        (
            "Design a composite external-pressure cylindrical pressure hull for 25 MPa hydrostatic pressure, ultimate pressure at least 40 MPa, simply supported ends, generate 8 candidates and retain 3 screened candidates.",
            {
                "pressure": 25.0,
                "target": 40.0,
                "total": 8,
                "top_k": 3,
                "boundary_type": "END_SIMPLY_SUPPORTED",
                "has_geometry_reference": False,
                "has_fixed_geometry": False,
            },
        ),
        (
            "Composite pressure hull preliminary design: external pressure 40 MPa, required ultimate pressure no less than 52 MPa, generate 8 candidate designs and retain 3 screened candidates.",
            {
                "pressure": 40.0,
                "target": 52.0,
                "total": 8,
                "top_k": 3,
                "boundary_type": "END_CLAMPED",
                "has_geometry_reference": False,
                "has_fixed_geometry": False,
            },
        ),
        (
            "外压 32 MPa，长度 520 mm，半径 105 mm，厚度 11 mm，极限压力不低于 42 MPa，候选池 8 个，初筛 Top-3",
            {
                "pressure": 32.0,
                "target": 42.0,
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
    assert payload["design_targets"]["ultimate_pressure_min_MPa"] == expected["target"]
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
        "请为复合材料外压圆柱耐压壳设计方案，外压 30 MPa，极限压力不低于 35 MPa，生成 4 个候选，初筛保留 2 个候选",
        "Design a composite external-pressure cylindrical pressure hull, external pressure 26 MPa, ultimate pressure at least 38 MPa, generate 4 candidates, keep 2 after screening",
    ],
)
def test_natural_language_inputs_complete_runtime_workflow_with_real_candidate_screening(monkeypatch, tmp_path, instruction):
    monkeypatch.setenv("CSDM_cph_DISABLE_LLM_AUTO", "1")
    orchestrator = OrchestratorAgent()
    _patch_deterministic_downstream(monkeypatch, orchestrator, tmp_path)
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
    assert state.results[0]["candidate_id"] == "C_TEST"
    assert state.results[0]["session_candidate_id"].startswith("TMP_")
    assert state.knowledge_updates[0]["case_id"] == "CASE_ACCEPTANCE"

    state = controller.continue_after_confirmation(state, True)

    assert state.stage == "completed"
    assert state.pending_confirmation is None
    assert state.report and state.report["markdown_path"].endswith("acceptance_report.md")
    assert set(state.report["report_outputs"]) == {"overall", "fem", "design_solution"}
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

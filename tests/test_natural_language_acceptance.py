from __future__ import annotations

import os
from collections.abc import Iterable

import pytest

from agents.orchestrator import OrchestratorAgent
from core.task_contract import (
    requested_candidate_pool_size,
    requested_screen_top_k,
    task_payload_from_request,
)


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
            },
        ),
        (
            "请为深海潜器复合材料外压圆柱耐压壳设计方案，外压 28 MPa，极限压力不低于 36 MPa，生成 8 个候选，初筛保留 3 个候选，两端简支",
            {
                "pressure": 28.0,
                "target": 36.0,
                "total": 8,
                "top_k": 3,
                "boundary_type": "END_SIMPLY_SUPPORTED",
                "has_geometry_reference": False,
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
                "has_geometry_reference": True,
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
    assert "fixed_geometry" not in facts

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

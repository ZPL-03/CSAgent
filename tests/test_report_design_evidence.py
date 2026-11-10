"""求解修订、容量约束与报告推荐使用同一设计证据。"""
from types import SimpleNamespace
import pytest

from agents.orchestrator import OrchestratorAgent
from agents.report_gen import ReportGenAgent
from core.task_contract import normalize_task_payload


def _result(index, thickness):
    coverage = {"status": "complete", "checked_element_positions": 8,
                "expected_section_points": 120, "incomplete_element_positions": 0}
    return {
        "candidate_id": f"C{index}", "session_candidate_id": f"TMP_{index}",
        "status": "success", "verdict": "通过", "ultimate_pressure_MPa": 30,
        "riks_limit_point_confirmed": True, "progressive_damage_complete": True,
        "damage_state_output_complete": True, "weight_kg_per_m2": 15.5,
        "service_pressure_check_status": "passed", "target_pressure_check_status": "passed",
        "service_stress_coverage": coverage, "target_stress_coverage": dict(coverage),
        "solved_design": {"geometry": {"thickness_mm": thickness}},
    }


def test_recommendation_uses_solved_thickness_and_explicit_capacity_constraint(monkeypatch):
    monkeypatch.setenv("CSDM_cph_DISABLE_LLM_AUTO", "1")
    task = normalize_task_payload({"load_conditions": {"external_pressure_MPa": 20},
                                   "design_targets": {"ultimate_pressure_min_MPa": 20,
                                                      "primary_objective": "最小厚度"}})
    candidates = [{"candidate_id": "TMP_1", "geometry": {"thickness_mm": 10}},
                  {"candidate_id": "TMP_2", "geometry": {"thickness_mm": 10.4}}]
    results = [_result(1, 10.8), _result(2, 10.4)]
    agent = ReportGenAgent()
    text = agent._render_markdown(task, results, candidates)
    assert "- 推荐：TMP_2 / C2" in text
    task["design_targets"]["ultimate_pressure_min_MPa"] = 35
    text = agent._render_markdown(task, results, candidates)
    assert "当前没有同时具备完整通过证据" in text


def test_case_write_receives_actual_solved_design():
    captured = {}
    orchestrator = object.__new__(OrchestratorAgent)
    orchestrator.emit_event = lambda *_args: None
    def store(payload):
        captured.update(payload)
        return {"status": "stored", "case_id": "CASE_1"}
    orchestrator.knowledge_agent = SimpleNamespace(run=store)
    design = {"candidate_id": "C1", "session_candidate_id": "TMP_1", "geometry": {"thickness_mm": 10}}
    result = _result(1, 10.8)
    orchestrator.persist_knowledge_records({}, [design], [result])
    assert captured["design"]["geometry"]["thickness_mm"] == 10.8
    assert design["geometry"]["thickness_mm"] == 10


def test_explanation_distinguishes_analysis_defect_from_manufacturing_limits(monkeypatch):
    monkeypatch.setenv("CSDM_cph_DISABLE_LLM_AUTO", "1")
    agent = ReportGenAgent()
    payload = {"all_candidates": [{"imperfection_ratio": 0.008}]}
    with pytest.raises(ValueError, match="缺陷条件已提供"):
        agent._validate_llm_engineering_text("所有候选均未提供明确的缺陷幅值。", payload)
    with pytest.raises(ValueError, match="安全验收结论"):
        agent._validate_llm_engineering_text("满足安全裕度要求。", payload)
    agent._validate_llm_engineering_text("分析采用固定缺陷条件，制造验收阈值尚未指定。", payload)

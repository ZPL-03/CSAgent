"""求解修订、容量约束与报告推荐使用同一设计证据。"""
from types import SimpleNamespace

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


def test_report_and_model_share_three_state_counts_and_recommendation(monkeypatch):
    monkeypatch.setenv("CSDM_cph_DISABLE_LLM_AUTO", "1")
    task = normalize_task_payload({"load_conditions": {"external_pressure_MPa": 20},
                                   "design_targets": {"ultimate_pressure_min_MPa": 20,
                                                      "primary_objective": "最小厚度"}})
    results = [_result(1, 10.8), {**_result(2, 10.4), "verdict": "不通过"},
               {"candidate_id": "C3", "status": "failed", "verdict": None}]
    agent = ReportGenAgent()
    summary = agent._build_structured_summary(task, results, [])
    payload = agent._build_llm_explanation_payload(summary)
    assert [summary[key] for key in ("passed_count", "failed_count", "unknown_count")] == [1, 1, 1]
    assert [row["state"] for row in payload["result_assessments"]] == ["passed", "failed", "unknown"]
    assert payload["recommendation"]["selected"]["candidate_id"] == "C1"
    assert payload["recommendation"] == summary["recommendation"]
    assert "- 推荐：TMP_1 / C1" in agent._render_markdown(task, results, [])


def test_solver_failure_is_not_a_failed_design_check(monkeypatch):
    monkeypatch.setenv("CSDM_cph_DISABLE_LLM_AUTO", "1")
    task = normalize_task_payload({"load_conditions": {"external_pressure_MPa": 20}})
    agent = ReportGenAgent()
    results = [{"candidate_id": "C1", "status": "failed", "verdict": None},
               {"candidate_id": "C2", "status": "failed", "verdict": "通过"}]
    summary = agent._build_structured_summary(task, results, [])
    payload = agent._build_llm_explanation_payload(summary)
    assert payload["aggregate"]["failed_count"] == payload["aggregate"]["passed_count"] == 0
    assert payload["aggregate"]["unknown_count"] == 2
    assert payload["recommendation"]["selected"] is None
    assert summary["result_assessments"][1]["semantic_errors"]


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

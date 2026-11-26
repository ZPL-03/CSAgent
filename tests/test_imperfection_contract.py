"""任务缺陷比在候选、预筛、求解输入和结果记录中的传递。"""

from copy import deepcopy

import pytest

from abaqus.runtime_build_pressure_hull import imperfection_amplitude_mm
from agents.candidate_gen import CandidateGenAgent
from agents.fem_agent import FEMAgent
from agents.knowledge_agent import KnowledgeAgent
from agents.orchestrator import OrchestratorAgent
from agents.report_gen import ReportGenAgent
from core.case_retriever import CaseRetriever
from core.config_loader import load_param_ranges
from core.fem_input_contract import compute_design_revision_id
from core.surrogate_model import SurrogateModelManager
from core.task_contract import normalize_geometry_envelope, task_payload_from_request
from core.task_parser import TaskParser


@pytest.mark.parametrize("text,value", [
    ("", 0.008), ("缺陷比0.005", 0.005), ("初始几何缺陷比为5‰", 0.005),
    ("缺陷比取0.5%", 0.005), ("缺陷比为千分之五", 0.005),
    ("缺陷比百分之零点五", 0.005), ("Ir=5e-3", 0.005),
    ("imperfection ratio: 5 per mille", 0.005), ("缺陷比千分之十", 0.01),
    ("缺陷比千分之五点二", 0.0052), ("缺陷比0.005123456", 0.005123456),
    ("按千分之五的缺陷比", 0.005), ("采用0.5%的初始缺陷比", 0.005),
    ("use 5 per mille imperfection ratio", 0.005),
])
def test_parser_uses_explicit_scalar_or_configured_default(text, value):
    payload = task_payload_from_request(TaskParser().parse_instruction("外压12MPa，" + text))
    assert payload["geometry_envelope"]["imperfection_ratio"] == pytest.approx([value, value])
    facts = payload["user_input_facts"].get("fixed_geometry", {})
    assert payload["analysis_condition_sources"]["imperfection_ratio"] == ("user" if text else "default")
    if text:
        assert facts["imperfection_ratio"] == pytest.approx(value)
    else:
        assert "imperfection_ratio" not in facts


def test_geometry_reference_does_not_make_defect_a_search_variable():
    task = TaskParser().parse_instruction("外压12MPa，几何参考长度500mm，缺陷比0.005")
    payload = task_payload_from_request(task)
    assert payload["geometry_envelope"]["length_mm"] == [440, 560]
    assert payload["geometry_envelope"]["imperfection_ratio"] == [0.005, 0.005]
    assert payload["user_input_facts"]["fixed_geometry"]["imperfection_ratio"] == 0.005


@pytest.mark.parametrize("text", [
    "缺陷比-0.005", "缺陷比0", "缺陷比0.5", "缺陷比0.02", "缺陷比5",
    "缺陷比0.005-0.008", "缺陷比5‰到8‰", "缺陷比千分之五或千分之八",
    "缺陷比0.005mm", "缺陷比0.005，Ir=0.008", "缺陷比千分之五%",
    "缺陷比NaN", "缺陷比为abc", "Ir=Infinity", "缺陷比true", "缺陷比为", "缺陷比5‰‰",
    "5‰到8‰的缺陷比", "0.005-0.008的缺陷比",
])
def test_parser_rejects_invalid_ambiguous_or_variable_defect(text):
    with pytest.raises(ValueError, match="缺陷比"):
        TaskParser().parse_instruction("外压12MPa，" + text)


@pytest.mark.parametrize("value", [None, True, False, "0.005", float("nan"), float("inf"),
                                  -0.005, 0, 0.02, [], [0.005], [0.005, 0.008]])
def test_structured_defect_requires_one_finite_in_range_number(value):
    with pytest.raises(ValueError, match="缺陷比"):
        normalize_geometry_envelope({"imperfection_ratio": value})


def test_structured_aliases_and_default_use_the_same_contract(monkeypatch):
    for value in (0.003, [0.003, 0.003]):
        assert normalize_geometry_envelope({"Ir": value})["imperfection_ratio"] == [0.003, 0.003]
    with pytest.raises(ValueError, match="冲突"):
        normalize_geometry_envelope({"Ir": 0.003, "imperfection": 0.004})
    monkeypatch.setitem(load_param_ranges()["analysis_assumptions"], "imperfection_ratio", 0.006)
    assert normalize_geometry_envelope({})["imperfection_ratio"] == [0.006, 0.006]
    assert normalize_geometry_envelope({"imperfection_ratio": 0.004})["imperfection_ratio"] == [0.004, 0.004]


def test_user_fixed_fact_is_used_and_conflicting_task_values_are_rejected():
    fact = {"fixed_geometry": {"imperfection_ratio": 0.004}}
    task = task_payload_from_request({"user_input_facts": fact})
    assert task["geometry_envelope"]["imperfection_ratio"] == [0.004, 0.004]
    with pytest.raises(ValueError, match="冲突"):
        task_payload_from_request({"user_input_facts": fact, "geometry_envelope": {"Ir": 0.005}})


@pytest.mark.parametrize("defect", [0.003, 0.005123456, 0.008])
def test_fixed_defect_reaches_candidates_surrogate_fem_and_case_record(monkeypatch, defect):
    monkeypatch.setenv("CSDM_cph_DISABLE_LLM_AUTO", "1")
    task = TaskParser().parse_instruction(
        f"外压12MPa，长度500mm，半径100mm，缺陷比{defect}，生成4个方案，预筛保留1个"
    )
    generator = CandidateGenAgent()
    candidates = generator.run(task)
    assert len(candidates) == 4
    assert all(item["geometry"]["imperfection_ratio"] == defect for item in candidates)
    assert all(item["geometry"]["length_mm"] == 500 for item in candidates)
    assert all(item["geometry"]["radius_mm"] == 100 for item in candidates)
    for source in ("LLM", "CASE_TRANSFER"):
        proposal = deepcopy(candidates[0])
        proposal["geometry"]["imperfection_ratio"] = 0.002
        original = deepcopy(proposal)
        normalized = generator._normalize_candidate(task, proposal, 1, source)
        assert normalized["geometry"]["imperfection_ratio"] == defect
        assert normalized["provenance"]["proposed_imperfection_ratio"] == 0.002
        assert proposal == original
    _, prompt = generator._build_prompt(task, desired_count=1, knowledge_guidance=[])
    assert f"任务采用 {defect:g}" in prompt
    assert CaseRetriever(use_vector_index=False)._geometry_center(task["task"])["imperfection_ratio"] == defect

    candidate = candidates[0]
    prediction = SurrogateModelManager().formula_prediction(candidate, apply_calibration=False)
    # D3 随输入比例线性变化，核对单位转换而不把经验公式当作有限元结果。
    other = deepcopy(candidate)
    other["geometry"]["imperfection_ratio"] = defect / 2
    reference = SurrogateModelManager().formula_prediction(other, apply_calibration=False)
    assert prediction.descriptors["D3"] == pytest.approx(2 * reference.descriptors["D3"], abs=2e-12)

    orchestrator = object.__new__(OrchestratorAgent)
    promoted = orchestrator.prepare_candidate_for_fem(task, candidate)
    assert promoted["geometry"]["imperfection_ratio"] == defect
    assert imperfection_amplitude_mm(promoted["geometry"]) == pytest.approx(defect * 100)
    fem = FEMAgent()
    annotated = fem._annotate_result(promoted, {"status": "failed", "error_type": "convergence_fail"})
    knowledge = object.__new__(KnowledgeAgent)
    stored = knowledge._sanitize_design(promoted)
    result = knowledge._sanitize_abaqus_results(annotated)
    assert compute_design_revision_id(stored) == promoted["design_revision_id"]
    assert compute_design_revision_id(result["solved_design"]) == result["design_revision_id"]
    assert result["solved_design"]["geometry"]["imperfection_ratio"] == defect
    assert ReportGenAgent()._compact_candidate_record(promoted)["imperfection_ratio"] == defect
    report = ReportGenAgent()._render_markdown(task, [annotated], candidates)
    assert f"任务初始几何缺陷比：{defect}（比例，用户指定）" in report
    assert f"实际求解缺陷比：{defect}" in report
    assert "求解缺陷条件与任务：一致" in report


def test_audit_preserves_task_candidate_and_solved_conditions(monkeypatch):
    from workflow.run_audit import build_run_audit_markdown

    monkeypatch.setenv("CSDM_cph_DISABLE_LLM_AUTO", "1")
    task = TaskParser().parse_instruction("外压12MPa，缺陷比0.005")
    candidates = [{"candidate_id": "TMP_1", "geometry": {"imperfection_ratio": 0.005}},
                  {"candidate_id": "TMP_2", "geometry": {"imperfection_ratio": 0.008}}]
    results = [{"session_candidate_id": "TMP_1", "candidate_id": "C1",
                "solved_design": {"geometry": {"imperfection_ratio": 0.003}}}]
    snapshot = {"task": task, "candidates": candidates, "results": results}
    original = deepcopy(snapshot)
    text = build_run_audit_markdown("RUN_DEFECT", snapshot, [], [])
    assert "| 任务初始几何缺陷比 | 0.005 |" in text
    assert "| 缺陷比来源 | 用户指定 |" in text
    assert "| TMP_1 | 0.005 | 一致 | 0.003 | 不一致 |" in text
    assert "| TMP_2 | 0.008 | 不一致 | - | 未求解 |" in text
    assert snapshot == original


def test_condition_source_survives_normalization_and_default_config_change(monkeypatch):
    task = TaskParser().parse_instruction("外压12MPa")
    monkeypatch.setitem(load_param_ranges()["analysis_assumptions"], "imperfection_ratio", 0.006)
    normalized = task_payload_from_request(task)
    assert normalized["geometry_envelope"]["imperfection_ratio"] == [0.008, 0.008]
    assert normalized["analysis_condition_sources"]["imperfection_ratio"] == "default"
    assert task_payload_from_request({"geometry_envelope": {"Ir": 0.004}})["analysis_condition_sources"]["imperfection_ratio"] == "task"


def test_conflicting_candidate_is_rejected_before_screening_or_fem_numbering(monkeypatch):
    import agents.orchestrator as module

    from agents.screener import ScreenerAgent

    task = {"geometry_envelope": {"imperfection_ratio": 0.005}, "screening_preferences": {"top_k_candidates": 1}}
    candidate = {"geometry": {"imperfection_ratio": 0.008}}
    orchestrator = object.__new__(OrchestratorAgent)
    monkeypatch.setattr(module, "reserve_candidate_ids", lambda *_: pytest.fail("分析条件未通过"))
    with pytest.raises(ValueError, match="任务不一致"):
        orchestrator.prepare_candidates_for_fem(task, [candidate])
    with pytest.raises(ValueError, match="任务不一致"):
        ScreenerAgent().rank_candidates(task, [candidate])


def test_fixed_geometry_is_preserved_in_llm_prompt_and_doe(monkeypatch):
    monkeypatch.setenv("CSDM_cph_DISABLE_LLM_AUTO", "1")
    task = TaskParser().parse_instruction("外压12MPa，长度1000mm，内半径210mm，生成4个方案，预筛保留1个")
    agent = CandidateGenAgent()
    _, prompt = agent._build_prompt(task, desired_count=4)
    assert "长度 L固定为 1000 mm" in prompt
    assert "内半径固定为 210 mm" in prompt
    candidates = agent.doe_sampler.sample_candidates(task, 4)
    assert len(candidates) == 4
    assert {(item["geometry"]["length_mm"], item["geometry"]["radius_mm"]) for item in candidates} == {(1000, 210)}
    assert all(item["geometry"]["radius_reference"] == "inner" for item in candidates)

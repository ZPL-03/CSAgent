"""后端扩展参数、显式层序与模型重放的职责边界。"""

from copy import deepcopy
import hashlib
import json
from types import SimpleNamespace

import pytest

from agents.candidate_gen import CandidateGenAgent
from agents.orchestrator import OrchestratorAgent
from agents.report_gen import ReportGenAgent
from abaqus.runtime_build_pressure_hull import validate_runtime_candidate
from core.case_memory import case_record_to_search_text
from core.doe_sampler import DOESampler
from core.fem_input_contract import validate_fem_input
from core.layup_parameters import active_geometry, active_layup
from core.llm_backend import LLMBackend
from core.schema_validator import validate_or_raise
from core.surrogate_model import SurrogateModelManager
from tests.test_audit_contracts import task
from tests.test_report_design_evidence import _result


def test_backend_extensions_are_isolated_and_not_inferred_from_model_name():
    config = {"backends": [
        {"name": "primary", "base_url": "http://localhost/v1", "api_key": "test", "model": "local"},
        {"name": "fallback", "base_url": "https://example.org/v1", "api_key": "test", "model": "provider-model",
         "extra_body": {"thinking": {"type": "disabled"}}},
    ]}
    backend = LLMBackend(config)
    calls = []
    def create(**request):
        calls.append(deepcopy(request))
        return SimpleNamespace(choices=[SimpleNamespace(finish_reason="stop", message=SimpleNamespace(content="ok"))])
    for runtime in backend.backends:
        runtime.client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
    assert backend.chat("system", "user") == "ok"
    assert backend.chat("system", "user", excluded_backend_names={"primary"}) == "ok"
    assert "extra_body" not in calls[0]
    assert calls[1]["extra_body"] == {"thinking": {"type": "disabled"}}
    assert backend.last_call_trace[0]["thinking"] == {"type": "disabled"}
    assert len(calls) == 2


@pytest.mark.parametrize("extension", [[], {"model": "another"}, {"max_tokens": 90000}, {"messages": []}])
def test_backend_extensions_cannot_override_request_contract(extension):
    with pytest.raises(ValueError, match="extra_body"):
        LLMBackend({"backends": [{"name": "test", "base_url": "http://localhost/v1", "api_key": "test",
                                  "model": "test", "extra_body": extension}]})


def test_task_angle_parameters_do_not_reappear_at_solver_or_case_transfer(monkeypatch):
    monkeypatch.setenv("CSDM_cph_DISABLE_LLM_AUTO", "1")
    current = task()
    candidate = DOESampler().sample_candidates(current, 1)[0]
    for part in (candidate["geometry"], candidate["layup"]):
        assert not {"alpha_deg", "beta_deg"}.intersection(part)
    validate_or_raise("candidate.schema.json", candidate)
    promoted = object.__new__(OrchestratorAgent)._promote_candidate_for_fem(current, candidate, "C1")
    assert not validate_fem_input(promoted)
    validate_runtime_candidate(promoted)
    migrated = CandidateGenAgent()._normalize_candidate(current, promoted, 1, "CASE_TRANSFER")
    for design in (promoted, migrated):
        for part in (design["geometry"], design["layup"]):
            assert not {"alpha_deg", "beta_deg"}.intersection(part)


def test_unused_parameters_do_not_change_approved_surrogate_prediction(tmp_path):
    candidate = DOESampler().sample_candidates(task(), 1)[0]
    historical = deepcopy(candidate)
    for part in (historical["geometry"], historical["layup"]):
        part.update(alpha_deg=54.416, beta_deg=37.135)
    model = SurrogateModelManager(models_dir=tmp_path)
    assert model.predict_candidate_payload(candidate) == model.predict_candidate_payload(historical)


def test_report_and_search_exclude_unused_parameters_without_changing_original(monkeypatch):
    monkeypatch.setenv("CSDM_cph_DISABLE_LLM_AUTO", "1")
    current = task()
    candidate = DOESampler().sample_candidates(current, 1)[0]
    for part in (candidate["geometry"], candidate["layup"]):
        part.update(alpha_deg=54.416, beta_deg=37.135)
    result = _result(1, candidate["geometry"]["thickness_mm"])
    result["solved_design"] = deepcopy(candidate)
    original = deepcopy(candidate)
    agent = ReportGenAgent()
    compact = agent._compact_candidate_record(candidate)
    assert "alpha_deg" not in compact and "beta_deg" not in compact
    report = agent._render_markdown(current, [result], [candidate])
    search = case_record_to_search_text({"task": current, "design": candidate, "abaqus_results": result})
    for text in (report, search):
        assert "54.416" not in text and "37.135" not in text
        assert "alpha=" not in text and "beta=" not in text
    assert candidate == original and result["solved_design"] == original


def test_historical_parameterized_templates_keep_their_angles():
    current = task()
    current["layup_constraints"].update(allowed_angles=[], min_ratio_per_angle=0)
    candidate = DOESampler().sample_candidates(current, 1)[0]
    assert "alpha_deg" in active_geometry(candidate) and "beta_deg" in active_geometry(candidate)
    assert "alpha_deg" in active_layup(candidate["layup"])


def _candidate_answer(layup, include_parameters=True):
    columns = "| alpha(deg) | beta(deg) " if include_parameters else ""
    separator = "| --- | --- " if include_parameters else ""
    values = "| 45 | 90 " if include_parameters else ""
    return (
        f"| 编号 | 材料 | 长度(mm) | 半径(mm) | 厚度(mm) {columns}| 缺陷比 | 铺层形式 |\n"
        f"| --- | --- | --- | --- | --- {separator}| --- | --- |\n"
        f"| C1 | T700/Epoxy | 500 | 100 | 12 {values}| 0.006 | {layup} |"
    )


@pytest.mark.parametrize("include_parameters", [True, False])
def test_explicit_llm_sequence_is_independent_of_unused_parameter_columns(monkeypatch, include_parameters):
    monkeypatch.setenv("CSDM_cph_DISABLE_LLM_AUTO", "1")
    agent = CandidateGenAgent()
    # 真实响应中的 beta=90 不参与这一完整数值层序。
    sequence = [0, 45, -45, 90, 0, 45, -45, 90]
    answer = _candidate_answer("[0/45/-45/90/0/45/-45/90]s", include_parameters)
    raw = agent._extract_candidates_from_natural_answer(answer)[0]
    assert agent._llm_raw_candidate_is_usable(raw)
    candidate = agent._normalize_candidate(task(), raw, 1, "LLM")
    assert candidate["rule_check"]["is_valid"]
    assert candidate["layup"]["template_name"] == "TASK_ANGLES"
    assert candidate["layup"]["angles_deg"] == sequence + list(reversed(sequence))
    for part in (candidate["geometry"], candidate["layup"]):
        assert not {"alpha_deg", "beta_deg"}.intersection(part)


@pytest.mark.parametrize("layup,failed_check", [
    ("[0/45/-45/90/60/-60]s", "ply_count_ok"),
    ("[0/45/-45/90/60/-60/0/90]s", "allowed_angles_ok"),
    ("[0/45/-45/90]_4", "symmetric"),
    ("[(0/45/45/90)_2]s", "balanced"),
])
def test_explicit_llm_sequence_preserves_physical_rejections(monkeypatch, layup, failed_check):
    monkeypatch.setenv("CSDM_cph_DISABLE_LLM_AUTO", "1")
    agent = CandidateGenAgent()
    raw = agent._extract_candidates_from_natural_answer(_candidate_answer(layup))[0]
    candidate = agent._normalize_candidate(task(), raw, 1, "LLM")
    assert not candidate["rule_check"]["is_valid"]
    assert not candidate["rule_check"]["details"][failed_check]


def test_symbolic_llm_template_keeps_and_validates_its_parameters(monkeypatch):
    monkeypatch.setenv("CSDM_cph_DISABLE_LLM_AUTO", "1")
    agent = CandidateGenAgent()
    current = task()
    current["layup_constraints"].update(allowed_angles=[], min_ratio_per_angle=0)
    raw = agent._extract_candidates_from_natural_answer(_candidate_answer("[(0/alpha/-alpha/beta)_2]s"))[0]
    candidate = agent._normalize_candidate(current, raw, 1, "LLM")
    assert candidate["geometry"]["beta_deg"] == 90
    assert candidate["layup"]["template_name"] == "BASE_90_AB"
    assert not candidate["rule_check"]["details"]["beta_deg_ok"]
    raw["geometry"]["beta_deg"] = 70
    raw["layup"]["layup"] = "[(0/alpha/-alpha/beta/-beta)_2]s"
    candidate = agent._normalize_candidate(current, raw, 1, "LLM")
    assert candidate["rule_check"]["is_valid"]
    assert candidate["layup"]["angles_deg"][:5] == [0, 45, -45, 70, -70]


def test_captured_candidate_retry_preserves_rejection_and_accepts_valid_sequence(monkeypatch):
    monkeypatch.setenv("CSDM_cph_DISABLE_LLM_AUTO", "1")
    agent = CandidateGenAgent()
    current = task()
    current["candidate_generation_preferences"].update(
        total_candidates=1, llm_candidates=1, case_transfer_candidates=0, doe_candidates=0,
    )
    calls = []
    answers = iter([
        _candidate_answer("[0/45/-45/90/60/-60]s"),
        _candidate_answer("[0/45/-45/90/0/45/-45/90]s"),
    ])
    def chat(system, prompt, **_kwargs):
        calls.append(prompt)
        assert "alpha(deg)" not in prompt and "beta(deg)" not in prompt
        return next(answers)
    agent.llm_backend = SimpleNamespace(chat=chat)
    monkeypatch.setattr(agent, "_knowledge_guidance", lambda *_args, **_kwargs: [])
    candidates = agent.run(current)
    audit = agent.last_generation_audit
    assert len(calls) == 2 and len(candidates) == 1
    assert candidates[0]["source"] == "LLM"
    assert audit["raw_counts"]["LLM"] == 2
    assert audit["invalid_counts"]["LLM"] == 1
    assert audit["added_counts"]["LLM"] == 1
    assert audit["added_counts"]["DOE"] == 0
    assert not audit["llm_diagnostics"][0]["candidate_checks"][0]["rule_check"]["is_valid"]


def test_replay_does_not_create_solver_or_rebind_results_to_generated_candidates(monkeypatch, tmp_path):
    import agents.candidate_gen as generation
    import agents.report_gen as reports
    import agents.orchestrator as orchestrator
    from scripts.validate_model_workflow import replay_models

    current = task()
    source_candidate = DOESampler().sample_candidates(current, 1)[0]
    solved = _result(1, source_candidate["geometry"]["thickness_mm"])
    solved["solved_design"] = deepcopy(source_candidate)
    source = {"task": current, "candidates": [source_candidate], "results": [solved],
              "knowledge_updates": [{"status": "stored"}], "report": {"pdf_generated": True}}
    source_path = tmp_path / "workflow.json"
    source_path.write_text(json.dumps(source), encoding="utf-8")
    source_bytes = source_path.read_bytes()
    replay_candidate = deepcopy(source_candidate)
    replay_candidate["geometry"]["thickness_mm"] = 12.345
    captured = {}
    class Generator:
        last_generation_audit = {"llm_diagnostics": [], "filter_reasons": {"LLM": []}}
        def __init__(self, _callback):
            pass
        def run(self, supplied):
            assert supplied == current
            return [replay_candidate]
    class Reporter:
        def __init__(self, _callback):
            pass
        def run(self, supplied):
            captured.update(supplied)
            return {"pdf_generated": True, "llm_explanation_used": True, "llm_explanation_audit": {"status": "accepted"}}
    monkeypatch.setattr(generation, "CandidateGenAgent", Generator)
    monkeypatch.setattr(reports, "ReportGenAgent", Reporter)
    monkeypatch.setattr(orchestrator, "OrchestratorAgent", lambda: pytest.fail("重放不能创建求解流程"))
    audit = replay_models(source_path, object(), tmp_path / "replay")
    assert audit["status"] == "passed" and audit["flow_status"] == "not_run"
    assert audit["source_flow_status"] == "passed" and audit["solver_executed"] is False
    assert captured["results"] == source["results"]
    assert captured["candidates"] == source["candidates"]
    assert captured["candidates"][0]["geometry"]["thickness_mm"] != 12.345
    assert source_path.read_bytes() == source_bytes
    assert audit["source_workflow_sha256"] == hashlib.sha256(source_bytes).hexdigest()


@pytest.mark.parametrize("quantities_in_instruction", [True, False])
def test_model_validation_uses_conversation_state_and_persistent_queue(monkeypatch, tmp_path, quantities_in_instruction):
    from scripts.validate_model_workflow import run_conversation_workflow
    from tests.test_natural_language_acceptance import _patch_fem_boundary
    from workflow.event_store import WorkflowEventStore
    from workflow.simulation_queue import SimulationJobQueue

    monkeypatch.setenv("CSDM_cph_DISABLE_LLM_AUTO", "1")
    orchestrator = OrchestratorAgent()
    _patch_fem_boundary(monkeypatch, orchestrator, tmp_path)
    instruction = "工作压力30MPa，长度500mm，半径100mm"
    if quantities_in_instruction:
        instruction += "，生成4个候选，初筛保留1个"
    result = run_conversation_workflow(orchestrator, instruction, tmp_path, {
        "candidate_count": "4", "screen_count": "1",
    })
    validation = result["runtime_validation"]
    assert validation["stage"] == "completed"
    assert validation["candidate_count"] == 4 and validation["screened_count"] == 1
    assert validation["result_count"] == 1 and validation["knowledge_update_count"] == 1
    store = WorkflowEventStore(tmp_path / "workflow_runtime.sqlite3")
    snapshot = store.load_snapshot(validation["run_id"])
    assert snapshot["stage"] == "completed"
    jobs = SimulationJobQueue(store.db_path).list_jobs(validation["run_id"])
    assert len(jobs) == 1 and jobs[0]["status"] == "success"
    assert jobs[0]["formal_candidate_id"] == result["results"][0]["candidate_id"]
    assert jobs[0]["session_candidate_id"] == result["results"][0]["session_candidate_id"]


@pytest.mark.parametrize("reply", [None, "-1", "abc"])
def test_model_validation_does_not_guess_missing_quantity(monkeypatch, tmp_path, reply):
    from scripts.validate_model_workflow import run_conversation_workflow

    monkeypatch.setenv("CSDM_cph_DISABLE_LLM_AUTO", "1")
    with pytest.raises(ValueError, match="candidate_count"):
        run_conversation_workflow(OrchestratorAgent(), "工作压力30MPa", tmp_path, {"candidate_count": reply})

"""任务约束、报告事实绑定及运行配置的独立反例。"""

from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest

from agents.candidate_gen import CandidateGenAgent
from agents.orchestrator import OrchestratorAgent
from agents.report_gen import ReportGenAgent
from agents.screener import ScreenerAgent
from core.doe_sampler import DOESampler
from core.fem_input_contract import attach_design_revision, validate_fem_input
from core.llm_backend import LLMBackend, backend_trust_env
from core.pressure_hull_profile import normalize_layup
from core.report_facts import build_report_facts, format_fact_value
from core.rule_checker import RuleChecker
from core.task_contract import normalize_task_payload


def task():
    return normalize_task_payload({
        "geometry_envelope": {"length_mm": 500.123456789, "radius_mm": 100, "imperfection_ratio": 0.006},
        "screening_preferences": {"top_k_candidates": 1},
    })


@pytest.mark.parametrize("state", ["passed", "failed", "unknown", "not_run"])
def test_report_design_state_renders_once_without_mutating_facts(state):
    fact = {"candidate_id": "C1", "metric": "design_check", "value": state,
            "unit": None, "status": state}
    snapshot = deepcopy(fact)
    assert format_fact_value(fact) == {"passed": "通过", "failed": "不通过", "unknown": "未判定", "not_run": "未求解"}[state]
    assert fact == snapshot


@pytest.mark.parametrize("source", ["LLM", "CASE_TRANSFER", "DOE"])
def test_all_sources_obey_task_not_only_global_domain(monkeypatch, source):
    monkeypatch.setenv("CSDM_cph_DISABLE_LLM_AUTO", "1")
    current = task()
    candidate = DOESampler().sample_candidates(current, 1)[0]
    if source != "DOE":
        candidate["geometry"].update(length_mm=600, imperfection_ratio=0.008)
        candidate = CandidateGenAgent()._normalize_candidate(current, candidate, 1, source)
    assert candidate["geometry"]["length_mm"] == 500.123456789
    assert candidate["geometry"]["imperfection_ratio"] == 0.006
    assert candidate["layup"]["symmetric"] is True
    assert candidate["rule_check"]["is_valid"]
    original = deepcopy(candidate)
    candidate["layup"] = normalize_layup({"template_name": "BENCHMARK_A"}, candidate["geometry"])
    check = RuleChecker().run(candidate, task=current)
    assert not check["is_valid"] and not check["details"]["symmetric"]
    assert candidate["layup"]["symmetric"] is False
    candidate = original
    candidate["geometry"]["length_mm"] = 600
    assert not RuleChecker().run(candidate, task=current)["is_valid"]


def test_symmetry_false_is_optional_not_a_request_to_falsify_physical_properties():
    current = task()
    current["layup_constraints"]["symmetric"] = False
    candidate = DOESampler().sample_candidates(current, 1)[0]
    candidate["geometry"].update(alpha_deg=45, beta_deg=45)
    candidate["layup"] = normalize_layup({"template_name": "BENCHMARK_A"}, candidate["geometry"])
    assert RuleChecker().run(candidate, task=current)["is_valid"]
    current["layup_constraints"]["allowed_angles"] = [0, 90]
    assert not RuleChecker().run(candidate, task=current)["is_valid"]


def test_task_mutation_is_blocked_before_fem_id_reservation_and_before_solver(monkeypatch):
    import agents.orchestrator as module

    current = task()
    candidate = DOESampler().sample_candidates(current, 1)[0]
    orchestrator = object.__new__(OrchestratorAgent)
    promoted = orchestrator._promote_candidate_for_fem(current, candidate, "C1")
    promoted["geometry"]["length_mm"] = 600
    promoted = attach_design_revision(promoted)
    assert any("task_constraints" in error for error in validate_fem_input(promoted))
    monkeypatch.setattr(module, "reserve_candidate_ids", lambda *_: pytest.fail("不能分配编号"))
    for action in (orchestrator.prepare_candidates_for_fem, ScreenerAgent().rank_candidates):
        with pytest.raises(ValueError, match="任务不一致"):
            action(current, [promoted])
    with pytest.raises(ValueError, match="任务不一致"):
        orchestrator.evaluate_prepared_candidate(current, promoted)


def report_summary():
    return {
        "external_pressure_MPa": 30, "imperfection_ratio": 0.006,
        "all_candidates": [{"candidate_id": "C3", "surrogate_ultimate_pressure_MPa": -2.5,
                            "surrogate_prediction_status": "nonpositive", "imperfection_ratio": 0.006}],
        "results": [
            {"candidate_id": "C1", "ultimate_pressure_MPa": 122.81234, "verified_capacity": True,
             "solved_imperfection_ratio": 0.006, "imperfection_amplitude_mm": 0.6,
             "service_hashin_index_max": 0.05712345,
             "riks_termination_reason": "post_peak_drop_20_percent"},
            {"candidate_id": "C2", "ultimate_pressure_MPa": 55.0, "verified_capacity": True},
        ],
        "result_assessments": [{"candidate_id": "C1", "state": "passed"}, {"candidate_id": "C2", "state": "failed"}],
    }


def test_report_facts_keep_prediction_ratio_amplitude_and_state():
    facts = build_report_facts(report_summary())
    original = deepcopy(facts)
    by_key = {(row["candidate_id"], row["metric"]): row for row in facts}
    assert format_fact_value(by_key["C1", "solved_imperfection_ratio"]) == "0.006（无量纲）"
    assert format_fact_value(by_key["C1", "imperfection_amplitude_mm"]) == "0.6 mm"
    for metric in ("candidate_count", "result_count", "comparable_count"):
        fact = by_key[None, metric]
        assert fact["unit"] == "个"
        assert format_fact_value(fact) == str(fact["value"])
    assert by_key["C3", "surrogate_ultimate_pressure_MPa"]["value"] == -2.5
    assert by_key["C1", "ultimate_pressure_MPa"]["value"] == 122.81234
    assert by_key["C1", "service_hashin_index_max"]["value"] == 0.05712345
    assert format_fact_value(by_key["C1", "riks_termination_reason"]) == "峰后载荷下降达到 20% 阈值，受控终止"
    assert by_key["C1", "riks_termination_reason"]["value"] == "post_peak_drop_20_percent"
    assert by_key["C3", "design_check"]["value"] == "not_run"
    assert facts == original


def test_report_facts_bind_proposal_and_solver_to_one_design():
    summary = report_summary()
    summary["results"][0]["session_candidate_id"] = "TMP_2"
    summary["all_candidates"].append({
        "candidate_id": "TMP_2", "imperfection_ratio": 0.006,
        "surrogate_ultimate_pressure_MPa": 79.967, "surrogate_prediction_status": "positive",
    })
    before = deepcopy(summary)
    facts = build_report_facts(summary)
    checks = {row["candidate_id"]: row["value"] for row in facts if row["metric"] == "design_check"}
    assert checks == {"C1": "passed", "C2": "failed", "C3": "not_run"}
    assert all(row["candidate_id"] != "TMP_2" for row in facts)
    prediction = next(row for row in facts if (row["candidate_id"], row["metric"]) == ("C1", "surrogate_ultimate_pressure_MPa"))
    capacity = next(row for row in facts if (row["candidate_id"], row["metric"]) == ("C1", "ultimate_pressure_MPa"))
    assert prediction["value"] == 79.967 and prediction["status"] == "positive"
    assert capacity["value"] == 122.81234 and capacity["status"] == "passed"
    assert summary == before


def test_report_rejects_multiple_results_for_one_session_candidate():
    summary = report_summary()
    for result in summary["results"]:
        result["session_candidate_id"] = "TMP_2"
    with pytest.raises(ValueError, match="关联了多个"):
        build_report_facts(summary)


def test_unconfirmed_capacity_cannot_be_rendered_as_a_verified_limit(monkeypatch):
    from tests.test_report_design_evidence import _result

    monkeypatch.setenv("CSDM_cph_DISABLE_LLM_AUTO", "1")
    result = _result(1, 10)
    result["riks_limit_point_confirmed"] = False
    summary = ReportGenAgent()._build_structured_summary(task(), [result], [])
    fact = next(row for row in build_report_facts(summary) if row["metric"] == "ultimate_pressure_MPa")
    assert fact["value"] is None and fact["status"] == "unknown"
    assert summary["result_assessments"][0]["state"] == "unknown"
    assert summary["recommendation"]["selected"] is None


def test_report_model_review_and_rejection_are_separate_from_export(monkeypatch):
    from tests.test_report_design_evidence import _result

    monkeypatch.setenv("CSDM_cph_DISABLE_LLM_AUTO", "1")
    agent = ReportGenAgent()
    current = task()
    current["design_targets"]["primary_objective"] = "最小厚度"
    current["load_conditions"]["external_pressure_MPa"] = 30
    summary = agent._build_structured_summary(current, [_result(1, 10)], [])
    def respond(_system, user, **kwargs):
        assert kwargs["json_mode"] is True
        payload = json.loads(user)
        if set(payload) == {"report", "evidence"}:
            return json.dumps({"accepted": True, "issues": []})
        refs = "、".join("{{" + ref + "}}" for ref in payload["required_assessment_refs"])
        scope = next(row["ref"] for row in payload["facts"] if row["metric"] == "analysis_scope")
        return json.dumps({"recommendation_candidate_id": payload["recommendation"]["selected"]["candidate_id"],
                           "assessment": "推荐判断依据为" + refs + "，仅在完成当前校核的方案中比较。",
                           "tradeoffs": [],
                           "verification": ["计算边界为{{" + scope + "}}；需核查实际连接能否实现任务约束再决定放行。"]})
    agent.llm_backend = SimpleNamespace(max_tokens=4096, chat=respond)
    text = agent._render_engineering_explanation(summary)
    assert agent._last_llm_explanation_used and "30 MPa" in text
    assert agent._last_llm_explanation_audit["review"]["recommendation_candidate_id"] == "C1"
    agent.llm_backend.chat = lambda *_args, **_kw: "实际缺陷比不得超过 0.006"
    with pytest.raises(ValueError):
        agent._render_engineering_explanation(summary)
    assert not agent._last_llm_explanation_used
    assert agent._last_llm_explanation_audit["status"] == "rejected"
    assert agent._last_llm_explanation_audit["raw_response"] == "实际缺陷比不得超过 0.006"


@pytest.mark.parametrize("url,expected", [("http://127.0.0.1:9000/v1", False), ("http://localhost/v1", False),
                                        ("http://[::1]/v1", False), ("https://api.example.org/v1", True)])
def test_proxy_policy_and_openai_client_match(url, expected):
    assert backend_trust_env(url, "bypass_loopback") is expected
    assert backend_trust_env(url, "direct") is False
    backend = LLMBackend({"backends": [{"name": "probe", "base_url": url, "api_key": "test", "model": "test"}]})
    observed = {}
    backend._openai_cls = lambda **kwargs: observed.update(kwargs) or SimpleNamespace()
    backend._client_for(backend.active_backend)
    try:
        assert observed["http_client"].trust_env is expected
    finally:
        observed["http_client"].close()


def test_cpu_encoder_does_not_query_cuda_availability(monkeypatch):
    import torch
    import transformers
    from core.builtin_knowledge import _encoder

    monkeypatch.setattr(torch.cuda, "is_available", lambda: pytest.fail("CPU 配置不得探测 CUDA"))
    observed = {}
    class Model:
        def to(self, device):
            observed["device"] = device
            return self
        def eval(self):
            return self
    monkeypatch.setattr(transformers.AutoTokenizer, "from_pretrained", lambda *_args, **_kwargs: object())
    monkeypatch.setattr(transformers.AutoModel, "from_pretrained", lambda *_args, **kwargs: observed.update(kwargs) or Model())
    _encoder.cache_clear()
    try:
        _encoder("test-local-model", "cpu")
        assert observed["device"] == "cpu" and observed["dtype"] == torch.float32
    finally:
        _encoder.cache_clear()


@pytest.mark.parametrize("model_used,expected", [(True, "passed"), (False, "failed")])
def test_validation_separates_doe_workflow_from_model_report(model_used, expected):
    from scripts.validate_model_workflow import assess_workflow
    from tests.test_report_design_evidence import _result

    current = task()
    candidate = DOESampler().sample_candidates(current, 1)[0]
    candidate["generation_audit"] = {"llm_diagnostics": [{"stage": "rule_check", "message": "非对称提案被拒绝"}],
                                     "filter_reasons": {"LLM": ["非对称提案被拒绝"]}}
    solved = _result(1, candidate["geometry"]["thickness_mm"])
    solved["solved_design"] = deepcopy(candidate)
    workflow = {"task": current, "candidates": [candidate], "results": [solved],
                "knowledge_updates": [{"status": "stored"}],
                "report": {"pdf_generated": True, "llm_explanation_used": model_used,
                           "llm_explanation_audit": {"status": "accepted" if model_used else "rejected"}}}
    audit = assess_workflow(workflow)
    assert audit["status"] == expected
    assert audit["flow_status"] == "passed"
    assert audit["model_report_status"] == expected
    assert audit["source_counter"] == {"LLM": 0, "DOE": 1, "CASE_TRANSFER": 0}
    assert audit["llm_candidate_branch"]["status"] == "not_adopted"
    assert audit["llm_candidate_branch"]["filter_reasons"]
    workflow["report"]["llm_explanation_audit"] = {"status": "rejected", "error": "报告事实与记录不一致"}
    rejected = assess_workflow(workflow)
    assert rejected["model_report_status"] == "failed"
    assert "报告事实与记录不一致" in rejected["model_report_failures"]
    solved["solved_design"]["geometry"]["imperfection_ratio"] = 0.008
    assert assess_workflow(workflow)["flow_status"] == "failed"


def test_real_workflow_requires_explicit_solver_flag(monkeypatch, tmp_path):
    import scripts.validate_model_workflow as module

    output_root = tmp_path / "validation"
    monkeypatch.setattr(module, "ROOT", output_root)
    with pytest.raises(SystemExit) as caught:
        module.main(["--backend", "primary"])
    assert caught.value.code == 2
    assert not output_root.exists()


@pytest.mark.skipif(os.name != "nt", reason="Windows PowerShell 启动器解析")
def test_conda_launcher_parses_in_windows_powershell():
    command = """
[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false)
$tokens = $null
$errors = $null
[Management.Automation.Language.Parser]::ParseFile(
    [IO.Path]::GetFullPath('scripts/run_agent.ps1'), [ref]$tokens, [ref]$errors
) | Out-Null
if ($errors) {
    $errors | ForEach-Object { $_.Message }
    exit 1
}
exit 0
"""
    completed = subprocess.run(
        ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", command],
        cwd=Path(__file__).resolve().parents[1], capture_output=True,
        text=True, encoding="utf-8", timeout=30,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr


def test_validation_paths_isolate_mutable_state_without_moving_sources(tmp_path):
    root = Path(__file__).resolve().parents[1]
    code = """
import json
from core import paths
from core.config_loader import load_app_config
print(json.dumps({
    'paths': {key: str(getattr(paths, key)) for key in (
        'DATA_DIR', 'IO_DIR', 'TASKS_DIR', 'CASES_DIR', 'RESULTS_DIR', 'ABAQUS_RUNS_DIR',
        'RUNTIME_DIR', 'CHROMA_DIR', 'CASE_LIBRARY_DIR', 'MODELS_DIR', 'RUNTIME_KNOWLEDGE_DIR',
        'ROOT_DIR', 'KNOWLEDGE_DIR', 'CONFIG_DIR', 'ABAQUS_DIR')},
    'knowledge': load_app_config()['project_knowledge'],
    'embedding_cache': load_app_config()['rag']['embedding_cache_dir'],
}))
"""
    completed = subprocess.run(
        [sys.executable, "-B", "-c", code], cwd=root,
        env={**os.environ, "CSDM_CPH_RUN_ROOT": str(tmp_path)},
        capture_output=True, text=True, encoding="utf-8", timeout=30, check=True,
    )
    observed = json.loads(completed.stdout)
    readonly = {"ROOT_DIR", "KNOWLEDGE_DIR", "CONFIG_DIR", "ABAQUS_DIR"}
    for name, value in observed["paths"].items():
        assert Path(value).is_relative_to(root if name in readonly else tmp_path)
    for name in ("base_dir", "upload_dir", "rag_chunks_path", "kg_dir", "manifest_path", "structured_dir", "vector_chroma_dir"):
        assert Path(observed["knowledge"][name]).is_relative_to(tmp_path)
    assert (root / observed["embedding_cache"]).is_relative_to(root)

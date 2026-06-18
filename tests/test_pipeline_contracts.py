from __future__ import annotations

from collections import Counter

import pytest

from agents.candidate_gen import CandidateGenAgent
from agents.knowledge_agent import KnowledgeAgent
from agents.orchestrator import OrchestratorAgent
from agents.report_gen import ReportGenAgent
from core.id_utils import format_temp_candidate_id
from core.llm_backend import LLMBackend
from core.schema_validator import SchemaValidationError, validate_or_raise
from core.task_contract import requested_candidate_pool_size, requested_screen_top_k, task_payload_from_request
from core.task_parser import TaskParser


class _FakeKnowledge:
    def __init__(self, snippets=None):
        self.snippets = snippets or []

    def format_snippets(self, _task, top_k=5):
        return list(self.snippets[:top_k])


def test_parser_reads_natural_language_pool_counts(monkeypatch):
    monkeypatch.setenv("CSDM_cph_DISABLE_LLM_AUTO", "1")
    instruction = (
        "请为复合材料外压圆柱耐压壳设计方案，外压 30 MPa，长度 500 mm，半径 100 mm，"
        "厚度 10 mm，极限压力不低于 35 MPa，生成 12 个候选，初筛保留 5 个候选"
    )

    task = TaskParser().parse_instruction(instruction)
    payload = task_payload_from_request(task)
    generation = payload["candidate_generation_preferences"]

    assert requested_candidate_pool_size(task) == 12
    assert requested_screen_top_k(task) == 5
    assert payload["design_targets"]["ultimate_pressure_min_MPa"] == 35.0
    assert generation["llm_candidates"] is None
    assert generation["case_transfer_candidates"] is None
    assert generation["doe_candidates"] is None
    assert generation["source_allocation_mode"] == "ratio_2_1_1"
    facts = payload["user_input_facts"]
    assert facts["load_conditions"]["external_pressure_MPa"] == 30.0
    assert facts["fixed_geometry"]["length_mm"] == 500.0
    assert facts["fixed_geometry"]["radius_mm"] == 100.0
    assert facts["fixed_geometry"]["thickness_mm"] == 10.0
    assert "geometry_reference" not in facts
    assert payload["geometry_envelope"]["length_mm"] == [500.0, 500.0]
    assert payload["geometry_envelope"]["radius_mm"] == [100.0, 100.0]
    assert payload["geometry_envelope"]["thickness_mm"] == [10.0, 10.0]
    assert facts["design_targets"]["ultimate_pressure_min_MPa"] == 35.0


def test_parser_distinguishes_fixed_geometry_from_reference_geometry(monkeypatch):
    monkeypatch.setenv("CSDM_cph_DISABLE_LLM_AUTO", "1")
    task = TaskParser().parse_instruction(
        "请为复合材料外压圆柱耐压壳设计方案，外压 30 MPa，固定几何尺寸：长度 500 mm，"
        "半径 100 mm，厚度 10 mm，极限压力不低于 35 MPa，生成 8 个候选，初筛保留 3 个候选"
    )
    payload = task_payload_from_request(task)
    facts = payload["user_input_facts"]

    assert facts["fixed_geometry"]["length_mm"] == 500.0
    assert facts["fixed_geometry"]["radius_mm"] == 100.0
    assert facts["fixed_geometry"]["thickness_mm"] == 10.0
    assert "geometry_reference" not in facts
    assert payload["geometry_envelope"]["length_mm"] == [500.0, 500.0]
    assert payload["geometry_envelope"]["radius_mm"] == [100.0, 100.0]
    assert payload["geometry_envelope"]["thickness_mm"] == [10.0, 10.0]


def test_parser_keeps_reference_geometry_when_user_marks_it_as_reference(monkeypatch):
    monkeypatch.setenv("CSDM_cph_DISABLE_LLM_AUTO", "1")
    task = TaskParser().parse_instruction(
        "请为复合材料外压圆柱耐压壳设计方案，外压 30 MPa，参考长度 500 mm，"
        "半径约 100 mm，厚度大约 10 mm，极限压力不低于 35 MPa，生成 8 个候选，初筛保留 3 个候选"
    )
    payload = task_payload_from_request(task)
    facts = payload["user_input_facts"]

    assert facts["geometry_reference"]["length_mm"] == 500.0
    assert facts["geometry_reference"]["radius_mm"] == 100.0
    assert facts["geometry_reference"]["thickness_mm"] == 10.0
    assert "fixed_geometry" not in facts
    assert payload["geometry_envelope"]["length_mm"] == [440.0, 560.0]
    assert payload["geometry_envelope"]["radius_mm"] == [80.0, 120.0]
    assert payload["geometry_envelope"]["thickness_mm"] == [7.0, 13.0]


def test_parser_accepts_field_level_fixed_geometry_phrasing(monkeypatch):
    monkeypatch.setenv("CSDM_cph_DISABLE_LLM_AUTO", "1")
    task = TaskParser().parse_instruction(
        "请为复合材料外压圆柱耐压壳设计方案，外压 30 MPa，长度固定 500 mm，"
        "半径必须等于 100 mm，厚度限定 10 mm，极限压力不低于 35 MPa，"
        "生成 8 个候选，初筛保留 3 个候选"
    )
    payload = task_payload_from_request(task)
    facts = payload["user_input_facts"]

    assert facts["fixed_geometry"]["length_mm"] == 500.0
    assert facts["fixed_geometry"]["radius_mm"] == 100.0
    assert facts["fixed_geometry"]["thickness_mm"] == 10.0
    assert "geometry_reference" not in facts
    assert payload["geometry_envelope"]["length_mm"] == [500.0, 500.0]
    assert payload["geometry_envelope"]["radius_mm"] == [100.0, 100.0]
    assert payload["geometry_envelope"]["thickness_mm"] == [10.0, 10.0]


def test_candidate_prompt_separates_user_facts_from_system_constraints(monkeypatch):
    monkeypatch.setenv("CSDM_cph_DISABLE_LLM_AUTO", "1")
    task = TaskParser().parse_instruction("外压 30 MPa，生成 12 个候选，初筛保留 5 个候选")
    agent = CandidateGenAgent()
    knowledge_guidance = ["[项目知识库 1] pressure hull buckling guidance"]

    system_prompt, user_prompt = agent._build_prompt(task, desired_count=6, knowledge_guidance=knowledge_guidance)

    assert "工程任务：批量生成复合材料耐压壳初始候选方案" in user_prompt
    assert "需要生成的 LLM 来源候选数量：6" in user_prompt
    assert "instruction:" not in user_prompt
    assert "input:" not in user_prompt
    user_fact_section = user_prompt.split("系统候选字段约束", 1)[0]
    assert "外压：30.0 MPa" in user_fact_section
    assert "T700/Epoxy" not in user_fact_section
    assert "500.0" not in user_fact_section
    assert "T700/Epoxy" in user_prompt
    assert "0.001-0.01" in user_prompt
    assert "结构化任务 JSON" not in user_prompt
    assert "不要输出 JSON" in system_prompt
    assert "结构性能依据和制造/缺陷风险依据" in user_prompt

    assert "pressure hull buckling guidance" in user_prompt


def test_llm_candidate_generation_token_budget_handles_reasoning_models(monkeypatch):
    monkeypatch.setenv("CSDM_cph_DISABLE_LLM_AUTO", "1")
    agent = CandidateGenAgent()

    class ControlledBackend:
        max_tokens = 1800
        json_output_tokens = 4096

    agent.llm_backend = ControlledBackend()

    assert agent._llm_generation_token_budget(2) >= 3000
    assert agent._llm_generation_token_budget(2) <= 4096


def test_llm_backend_uses_fallback_backend_after_primary_unusable_response(monkeypatch):
    monkeypatch.setenv("CSDM_cph_DISABLE_LLM_AUTO", "1")
    backend = LLMBackend(
        {
            "backends": [
                {
                    "name": "primary",
                    "base_url": "http://primary.local/v1",
                    "api_key": "primary-key",
                    "model": "primary-model",
                    "temperature": 0.1,
                    "max_tokens": 16,
                    "timeout_seconds": 1,
                    "json_output_tokens": 16,
                },
                {
                    "name": "fallback",
                    "base_url": "http://fallback.local/v1",
                    "api_key": "fallback-key",
                    "model": "fallback-model",
                    "temperature": 0.1,
                    "max_tokens": 16,
                    "timeout_seconds": 1,
                    "json_output_tokens": 16,
                },
            ]
        }
    )
    calls = []

    class FakeCompletions:
        def __init__(self, owner):
            self.owner = owner

        def create(self, **payload):
            calls.append((self.owner.base_url, payload["model"]))

            class Message:
                content = ""

            class Choice:
                message = Message()

            class Response:
                choices = [Choice()]

            if "primary" in self.owner.base_url:
                return Response()

            Message.content = "fallback-ok"
            return Response()

    class FakeChat:
        def __init__(self, owner):
            self.completions = FakeCompletions(owner)

    class FakeOpenAI:
        def __init__(self, base_url, api_key, timeout, default_headers):
            self.base_url = base_url
            self.chat = FakeChat(self)

    backend._openai_cls = FakeOpenAI

    result = backend.chat("system", "user")

    assert result == "fallback-ok"
    assert backend.active_backend.name == "fallback"
    assert calls == [
        ("http://primary.local/v1", "primary-model"),
        ("http://fallback.local/v1", "fallback-model"),
    ]
    assert backend.last_call_trace == [
        {
            "backend": "primary",
            "model": "primary-model",
            "json_mode": False,
            "max_tokens": 16,
            "status": "failed",
            "finish_reason": None,
            "content_chars": 0,
            "error_type": "ValueError",
            "error": "LLM 后端 primary 返回空文本",
            "latency_ms": backend.last_call_trace[0]["latency_ms"],
        },
        {
            "backend": "fallback",
            "model": "fallback-model",
            "json_mode": False,
            "max_tokens": 16,
            "status": "success",
            "finish_reason": None,
            "content_chars": 11,
            "latency_ms": backend.last_call_trace[1]["latency_ms"],
        },
    ]
    trace_text = str(backend.last_call_trace)
    assert "primary-key" not in trace_text
    assert "fallback-key" not in trace_text
    assert "primary.local" not in trace_text
    assert "fallback.local" not in trace_text
    assert backend.call_history[-1] == backend.last_call_trace
    fake_secret = "sk-" + "1234567890abcdef"
    sanitized_error = backend._sanitize_trace_error(
        RuntimeError(
            "request failed at http://primary.local/v1 with primary-key and "
            f"https://api.deepseek.com/v1 using {fake_secret}"
        )
    )
    assert "http://primary.local/v1" not in sanitized_error
    assert "https://api.deepseek.com/v1" not in sanitized_error
    assert "primary-key" not in sanitized_error
    assert fake_secret not in sanitized_error


def test_count_overrides_keep_ratio_mode(monkeypatch):
    monkeypatch.setenv("CSDM_cph_DISABLE_LLM_AUTO", "1")
    instruction = "外压 30 MPa，生成 12 个候选，初筛保留 5 个候选"
    task = TaskParser().parse_instruction(
        instruction,
        overrides={
            "total_candidates": 9,
            "top_k_candidates": 4,
        },
    )
    generation = task_payload_from_request(task)["candidate_generation_preferences"]

    assert requested_candidate_pool_size(task) == 9
    assert requested_screen_top_k(task) == 4
    assert generation["source_allocation_mode"] == "ratio_2_1_1"


def test_candidate_source_targets_follow_default_ratio(monkeypatch):
    monkeypatch.setenv("CSDM_cph_DISABLE_LLM_AUTO", "1")
    task = TaskParser().parse_instruction("外压 30 MPa，生成 12 个候选，初筛保留 5 个候选")
    targets = CandidateGenAgent()._resolve_source_targets(task)

    assert targets == {"total": 12, "llm": 6, "case_transfer": 3, "doe": 3}


@pytest.mark.parametrize(
    ("instruction", "message"),
    [
        ("外压 30 MPa，初筛保留 3 个候选", "候选池总数"),
        ("外压 30 MPa，生成 6 个候选", "初筛保留数量"),
        ("生成 6 个候选，初筛保留 3 个候选", "外部静水压力"),
    ],
)
def test_parser_requires_pool_and_screen_counts(monkeypatch, instruction, message):
    monkeypatch.setenv("CSDM_cph_DISABLE_LLM_AUTO", "1")
    with pytest.raises(ValueError, match=message):
        TaskParser().parse_instruction(instruction)


def test_candidate_generation_uses_three_initial_sources(monkeypatch):
    monkeypatch.setenv("CSDM_cph_DISABLE_LLM_AUTO", "1")
    task = TaskParser().parse_instruction("外压 30 MPa，生成 6 个候选，初筛保留 3 个候选")
    agent = CandidateGenAgent()
    requested = {}

    def controlled_source(source: str, task_payload: dict, start_index: int, desired_count: int):
        requested[source] = desired_count
        candidates = agent.doe_sampler.sample_candidates(
            task_payload,
            n_samples=desired_count,
            start_index=start_index,
            strict_solver_window=True,
            hull_type="CYLINDRICAL",
            id_factory=format_temp_candidate_id,
        )
        for candidate in candidates:
            candidate["source"] = source
        return candidates

    monkeypatch.setattr(agent, "_llm_candidates", lambda task_payload, start_index, desired_count: controlled_source("LLM", task_payload, start_index, desired_count))
    monkeypatch.setattr(agent, "_case_transfer_candidates", lambda task_payload, start_index, desired_count: controlled_source("CASE_TRANSFER", task_payload, start_index, desired_count))

    candidates = agent.run(task)

    assert len(candidates) == 6
    assert {candidate["candidate_id"] for candidate in candidates} == {f"TMP_{index}" for index in range(1, 7)}
    assert all(candidate["display_name"] == candidate["candidate_id"] for candidate in candidates)
    assert requested == {"LLM": 3, "CASE_TRANSFER": 2}
    assert Counter(candidate["source"] for candidate in candidates) == Counter({"LLM": 3, "CASE_TRANSFER": 2, "DOE": 1})
    audit = candidates[0]["generation_audit"]
    assert audit["source_targets"] == {"total": 6, "LLM": 3, "CASE_TRANSFER": 2, "DOE": 1}
    assert audit["added_counts"] == {"LLM": 3, "CASE_TRANSFER": 2, "DOE": 1}
    assert audit["duplicate_counts"]["total"] == 0
    assert "有效进入候选池 LLM=3" in audit["summary"]


def test_candidate_generation_changes_actual_source_counts_when_transfer_cases_are_fewer(monkeypatch):
    monkeypatch.setenv("CSDM_cph_DISABLE_LLM_AUTO", "1")
    task = TaskParser().parse_instruction("外压 30 MPa，生成 10 个候选，初筛保留 4 个候选")
    messages = []
    agent = CandidateGenAgent(progress_callback=lambda _agent, message, _event=None: messages.append(message))

    def controlled_source(source: str, task_payload: dict, start_index: int, desired_count: int, actual_count: int):
        candidates = agent.doe_sampler.sample_candidates(
            task_payload,
            n_samples=actual_count,
            start_index=start_index,
            strict_solver_window=True,
            hull_type="CYLINDRICAL",
            id_factory=format_temp_candidate_id,
        )
        for candidate in candidates:
            candidate["source"] = source
        return candidates

    monkeypatch.setattr(
        agent,
        "_llm_candidates",
        lambda task_payload, start_index, desired_count: controlled_source("LLM", task_payload, start_index, desired_count, desired_count),
    )
    monkeypatch.setattr(
        agent,
        "_case_transfer_candidates",
        lambda task_payload, start_index, desired_count: controlled_source("CASE_TRANSFER", task_payload, start_index, desired_count, 1),
    )

    candidates = agent.run(task)

    assert len(candidates) == 10
    assert Counter(candidate["source"] for candidate in candidates) == Counter({"LLM": 5, "CASE_TRANSFER": 1, "DOE": 4})
    assert candidates[0]["generation_audit"]["raw_counts"]["CASE_TRANSFER"] == 1
    assert candidates[0]["generation_audit"]["added_counts"]["DOE"] == 4
    assert "初始配额 LLM=5 / 案例迁移=3 / DOE=2" in messages[-1]
    assert "有效进入候选池 LLM=5，案例迁移=1，DOE补足=4" in messages[-1]


def test_candidate_generation_deduplicates_equivalent_designs(monkeypatch):
    monkeypatch.setenv("CSDM_cph_DISABLE_LLM_AUTO", "1")
    task = TaskParser().parse_instruction("外压 30 MPa，生成 4 个候选，初筛保留 2 个候选")
    messages = []
    agent = CandidateGenAgent(progress_callback=lambda _agent, message, _event=None: messages.append(message))

    raw = {
        "geometry": {
            "length_mm": 500.0,
            "radius_mm": 100.0,
            "thickness_mm": 10.0,
            "alpha_deg": 35.0,
            "beta_deg": 65.0,
            "imperfection_ratio": 0.005,
        },
        "layup": {"layup": "[90_4/(±35/±65)_8/90_4]"},
        "material_system": {"name": "T700/Epoxy", "material_key": "T700_Epoxy"},
        "rationale": "重复候选",
    }

    def duplicated_llm(task_payload, start_index, desired_count):
        return [
            agent._normalize_candidate(task_payload, raw, start_index, "LLM"),
            agent._normalize_candidate(task_payload, raw, start_index + 1, "LLM"),
        ][:desired_count]

    monkeypatch.setattr(agent, "_llm_candidates", duplicated_llm)
    monkeypatch.setattr(agent, "_case_transfer_candidates", lambda task_payload, start_index, desired_count: [])

    candidates = agent.run(task)
    signatures = [agent._candidate_signature(candidate) for candidate in candidates]

    assert len(candidates) == 4
    assert len(signatures) == len(set(signatures))
    assert [candidate["candidate_id"] for candidate in candidates] == [f"TMP_{index}" for index in range(1, 5)]
    assert any("候选去重过滤" in message for message in messages)
    assert candidates[0]["generation_audit"]["duplicate_counts"]["LLM"] == 1
    assert candidates[0]["generation_audit"]["duplicate_counts"]["total"] == 1


def test_llm_candidates_are_extracted_from_engineering_natural_answer(monkeypatch):
    monkeypatch.setenv("CSDM_cph_DISABLE_LLM_AUTO", "1")
    task = TaskParser().parse_instruction(
        "请为复合材料外压圆柱耐压壳设计方案，材料 T700/Epoxy，外压 30 MPa，几何参考长度约 500 mm，"
        "半径约 100 mm，厚度约 10 mm，初始缺陷比参考 0.5%，极限压力不低于 35 MPa，生成 6 个候选，初筛保留 3 个候选"
    )
    agent = CandidateGenAgent()

    class ControlledBackend:
        json_output_tokens = 4096

        def chat(self, system_prompt, user_prompt, max_tokens_override=None, json_mode=False, **_kwargs):
            assert "不要输出 JSON" in system_prompt
            assert "需要生成的 LLM 来源候选数量：2" in user_prompt
            assert "pressure hull buckling guidance" in user_prompt
            return (
                "<think>内部推理不应进入候选审计字段。</think>\n"
                "## 候选方案\n"
                "| 编号 | 材料 | 长度(mm) | 半径(mm) | 厚度(mm) | alpha(deg) | beta(deg) | 缺陷比 | 铺层形式 | 推荐理由 |\n"
                "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n"
                "| S01 | T700/Epoxy | 520 | 108 | 11 | 35 | 65 | 0.005 | [90_4/(±35/±65)_8/90_4] | 屈曲稳定性和制造性折中 |\n"
                "| S02 | T700/Epoxy | 485 | 96 | 9.5 | 45 | 70 | 0.006 | [90_4/(±45/±70)_8/90_4] | 环向刚度较高 |\n"
                + ("完整回答追踪" * 360)
                + "END_MARKER"
            )

    agent.knowledge_base = _FakeKnowledge(["[项目知识库 1] pressure hull buckling guidance"])
    agent.llm_backend = ControlledBackend()
    candidates = agent._llm_candidates(task, start_index=1, desired_count=2)

    assert len(candidates) == 2
    assert [candidate["source"] for candidate in candidates] == ["LLM", "LLM"]
    assert candidates[0]["geometry"]["length_mm"] == 520.0
    assert candidates[0]["geometry"]["radius_mm"] == 108.0
    assert candidates[0]["geometry"]["thickness_mm"] == 11.0
    assert candidates[0]["geometry"]["imperfection_ratio"] == 0.005
    assert candidates[0]["geometry"]["alpha_deg"] == 35.0
    assert candidates[0]["geometry"]["beta_deg"] == 65.0
    assert "S01" in candidates[0]["origin_summary"]
    assert "候选方案" in candidates[0]["llm_output_excerpt"]
    assert "END_MARKER" in candidates[0]["llm_output_excerpt"]
    assert "<think" not in candidates[0]["llm_output_excerpt"].lower()
    assert "</think>" not in candidates[0]["llm_output_excerpt"].lower()
    assert len(candidates[0]["llm_output_excerpt"]) > 2000


def test_llm_candidate_generation_tries_next_backend_after_unparseable_primary(monkeypatch):
    monkeypatch.setenv("CSDM_cph_DISABLE_LLM_AUTO", "1")
    task = TaskParser().parse_instruction(
        "请为复合材料外压圆柱耐压壳设计方案，外压 30 MPa，极限压力不低于 35 MPa，生成 4 个候选，初筛保留 2 个候选"
    )
    agent = CandidateGenAgent()
    agent.llm_config["fallback"]["max_format_retries"] = 1

    class Runtime:
        def __init__(self, name):
            self.name = name

    class ControlledBackend:
        max_tokens = 4096
        json_output_tokens = 4096

        def __init__(self):
            self.backends = [Runtime("primary"), Runtime("fallback")]
            self.active_backend = self.backends[0]
            self.calls = []

        def chat(
            self,
            system_prompt,
            user_prompt,
            max_tokens_override=None,
            json_mode=False,
            excluded_backend_names=None,
        ):
            excluded = set(excluded_backend_names or set())
            if "primary" not in excluded:
                self.active_backend = self.backends[0]
                self.calls.append("primary")
                return "| 긍뵀 | 꼼죕 |\n| --- | --- |"
            self.active_backend = self.backends[1]
            self.calls.append("fallback")
            return (
                "| 编号 | 材料 | 长度(mm) | 半径(mm) | 厚度(mm) | alpha(deg) | beta(deg) | 缺陷比 | 铺层形式 | 推荐理由 |\n"
                "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n"
                "| S01 | T700/Epoxy | 520 | 110 | 12 | 35 | 65 | 0.005 | [90_4/(±35/±65)_8/90_4] | 屈曲稳定性和缠绕角控制折中 |\n"
            )

    backend = ControlledBackend()
    agent.llm_backend = backend

    candidates = agent._llm_candidates(task, start_index=1, desired_count=1)

    assert backend.calls == ["primary", "fallback"]
    assert len(candidates) == 1
    assert candidates[0]["source"] == "LLM"
    assert candidates[0]["rule_check"]["is_valid"] is True


def test_llm_candidate_table_without_material_or_imperfection_is_rejected(monkeypatch):
    monkeypatch.setenv("CSDM_cph_DISABLE_LLM_AUTO", "1")
    task = TaskParser().parse_instruction(
        "请为复合材料外压圆柱耐压壳设计方案，外压 30 MPa，长度 500 mm，半径 100 mm，"
        "厚度 10 mm，极限压力不低于 35 MPa，生成 6 个候选，初筛保留 3 个候选"
    )
    agent = CandidateGenAgent()

    class ControlledBackend:
        json_output_tokens = 4096

        def chat(self, system_prompt, user_prompt, max_tokens_override=None, json_mode=False, **_kwargs):
            assert "用户已给信息" in user_prompt
            assert "表格列使用" in user_prompt
            return (
                "## 候选方案\n"
                "| 候选方案编号 | 壳体半径(mm) | 壳体长度(mm) | 壁厚(mm) | 铺层角 | 铺层形式 | 推荐理由 |\n"
                "| --- | --- | --- | --- | --- | --- | --- |\n"
                "| 1 | 100 | 500 | 10 | ±45/0/90 | [±45/0/90]s | 环向承载与铺放工艺折中 |\n"
                "| 2 | 100 | 500 | 10 | ±60/0/90 | [±60/0/90]s | 提高环向刚度 |\n"
            )

    agent.llm_backend = ControlledBackend()
    candidates = agent._llm_candidates(task, start_index=1, desired_count=2)

    assert candidates == []


def test_llm_generation_failure_diagnostics_are_written_to_audit(monkeypatch):
    monkeypatch.setenv("CSDM_cph_DISABLE_LLM_AUTO", "1")
    task = TaskParser().parse_instruction("外压 30 MPa，生成 4 个候选，初筛保留 2 个候选")
    agent = CandidateGenAgent()
    agent.llm_config["fallback"]["max_format_retries"] = 1

    class Runtime:
        name = "fake_primary"

    class ControlledBackend:
        json_output_tokens = 4096

        def __init__(self):
            self.backends = [Runtime()]
            self.active_backend = self.backends[0]
            self.last_call_trace = []

        def chat(self, *_args, **_kwargs):
            return "当前只能给出原则性建议，未列出完整候选参数。"

    agent.llm_backend = ControlledBackend()
    monkeypatch.setattr(agent, "_case_transfer_candidates", lambda task_payload, start_index, desired_count: [])

    candidates = agent.run(task)
    audit = candidates[0]["generation_audit"]

    assert len(candidates) == 4
    assert audit["added_counts"]["LLM"] == 0
    assert audit["added_counts"]["DOE"] == 4
    assert audit["llm_diagnostics"]
    assert audit["llm_diagnostics"][0]["stage"] == "parse"
    assert audit["llm_diagnostics"][0]["answer_char_count"] > 0
    assert audit["filter_reasons"]["LLM"]


def test_candidate_normalization_rejects_incomplete_source_geometry(monkeypatch):
    monkeypatch.setenv("CSDM_cph_DISABLE_LLM_AUTO", "1")
    task = TaskParser().parse_instruction("外压 30 MPa，生成 6 个候选，初筛保留 3 个候选")
    agent = CandidateGenAgent()

    with pytest.raises(SchemaValidationError, match="缺少必要几何字段"):
        agent._normalize_candidate(
            task,
            {
                "geometry": {"length_mm": 500.0, "radius_mm": 100.0},
                "material_system": {"name": "T700/Epoxy"},
            },
            index=1,
            source="CASE_TRANSFER",
        )


def test_candidate_schema_requires_non_empty_display_name(monkeypatch):
    monkeypatch.setenv("CSDM_cph_DISABLE_LLM_AUTO", "1")
    task = TaskParser().parse_instruction("外压 30 MPa，生成 6 个候选，初筛保留 3 个候选")
    candidate = CandidateGenAgent().doe_sampler.sample_candidates(
        task,
        n_samples=1,
        start_index=1,
        strict_solver_window=True,
        id_factory=format_temp_candidate_id,
    )[0]

    assert candidate["display_name"] == candidate["candidate_id"]
    validate_or_raise("candidate.schema.json", candidate)

    missing_display_name = dict(candidate)
    missing_display_name.pop("display_name")
    with pytest.raises(SchemaValidationError):
        validate_or_raise("candidate.schema.json", missing_display_name)

    null_persistent_id = dict(candidate)
    null_persistent_id["persistent_candidate_id"] = None
    with pytest.raises(SchemaValidationError):
        validate_or_raise("candidate.schema.json", null_persistent_id)


def test_orchestrator_promotes_candidate_to_formal_identity_without_persistent_id(monkeypatch):
    monkeypatch.setenv("CSDM_cph_DISABLE_LLM_AUTO", "1")
    task = TaskParser().parse_instruction("外压 30 MPa，生成 6 个候选，初筛保留 3 个候选")
    candidate = CandidateGenAgent().doe_sampler.sample_candidates(
        task,
        n_samples=1,
        start_index=1,
        strict_solver_window=True,
        id_factory=format_temp_candidate_id,
    )[0]
    candidate["persistent_candidate_id"] = "C999"
    orchestrator = OrchestratorAgent.__new__(OrchestratorAgent)

    promoted = orchestrator._promote_candidate_for_fem(task, candidate)

    assert promoted["candidate_id"].startswith("C")
    assert promoted["display_name"] == promoted["candidate_id"]
    assert promoted["session_candidate_id"] == "TMP_1"
    assert "persistent_candidate_id" not in promoted
    assert candidate["candidate_id"] == "TMP_1"
    validate_or_raise("candidate.schema.json", promoted)


def test_knowledge_case_record_keeps_only_real_task_trace(monkeypatch):
    monkeypatch.setenv("CSDM_cph_DISABLE_LLM_AUTO", "1")
    task_record = TaskParser().parse_instruction("外压 30 MPa，生成 6 个候选，初筛保留 3 个候选")
    task_payload = task_payload_from_request(task_record)
    design = {
        "candidate_id": "C999",
        "source": "DOE",
        "geometry": {"length_mm": 500.0, "radius_mm": 100.0, "thickness_mm": 10.0},
        "layup": {},
        "material_system": {},
    }
    abaqus_results = {
        "candidate_id": "C999",
        "status": "success",
        "retry_count": 0,
        "ultimate_pressure_MPa": 40.0,
        "verdict": "通过",
    }
    agent = KnowledgeAgent.__new__(KnowledgeAgent)

    untraced_record = agent._build_record(task_payload, design, abaqus_results)
    traced_design = {**design, "candidate_id": "C998"}
    traced_results = {**abaqus_results, "candidate_id": "C998"}
    traced_record = agent._build_record(task_record, traced_design, traced_results)

    assert "task_id" not in untraced_record
    assert traced_record["task_id"] == task_record["task_id"]


def _report_sample():
    task = TaskParser().parse_instruction(
        "请为复合材料外压圆柱耐压壳设计方案，外压 30 MPa，长度 500 mm，半径 100 mm，"
        "厚度 10 mm，极限压力不低于 35 MPa，生成 6 个候选，初筛保留 3 个候选"
    )
    candidate = {
        "candidate_id": "TMP_1",
        "display_name": "TMP_1",
        "source": "DOE",
        "geometry": {
            "length_mm": 500.0,
            "radius_mm": 100.0,
            "thickness_mm": 10.0,
            "alpha_deg": 35.0,
            "beta_deg": 65.0,
            "imperfection_ratio": 0.005,
        },
        "layup": {"layup": "[90_4/(±35/±65)_8/90_4]"},
        "material_system": {"name": "T700/Epoxy"},
        "rationale": "兼顾环向刚度和制造角度。",
        "screening_summary": "PBIPF 公式初筛通过。",
        "selection_reason": "代理模型排序靠前。",
        "surrogate_ultimate_pressure_MPa": 41.0,
        "asme_linear_buckling_pressure_MPa": 52.0,
        "rank_score": 39.0,
        "surrogate_weight": 15.5,
    }
    result = {
        "candidate_id": "C1",
        "session_candidate_id": "TMP_1",
        "display_name": "C1",
        "status": "completed",
        "ultimate_pressure_MPa": 40.0,
        "linear_buckling_pressure_MPa": 52.0,
        "ultimate_pressure_basis": "ABAQUS Riks",
        "riks_lpf_max": 1.14,
        "imperfection_amplitude_mm": 0.5,
        "weight_kg_per_m2": 15.5,
        "failure_mode": "整体屈曲",
        "verdict": "通过",
        "diagnosis_summary": "非线性极限压力达到目标。",
        "visualization_json": "data/results/CASE_1_mode.json",
    }
    return task, [result], [candidate]


def test_report_falls_back_to_structured_engineering_explanation(monkeypatch):
    monkeypatch.setenv("CSDM_cph_DISABLE_LLM_AUTO", "1")
    task, results, candidates = _report_sample()
    agent = ReportGenAgent()

    markdown = agent._render_markdown(task, results, candidates)

    assert "## 工程解释与制造建议" in markdown
    assert "### 制造工艺适配性" in markdown
    assert "缺陷与质量控制" in markdown
    assert markdown.index("## 有限元校核结果") < markdown.index("## 工程解释与制造建议")
    assert agent._last_llm_explanation_used is False


def test_report_all_generates_overall_fem_and_solution_artifacts(monkeypatch, tmp_path):
    monkeypatch.setenv("CSDM_cph_DISABLE_LLM_AUTO", "1")
    task, results, candidates = _report_sample()
    agent = ReportGenAgent()

    report = agent.run(
        {
            "task": task,
            "results": results,
            "candidates": candidates,
            "report_kind": "all",
            "output_dir": str(tmp_path),
        }
    )

    assert report["report_kind"] == "all"
    assert set(report["report_outputs"]) == {"overall", "fem", "design_solution"}
    assert report["markdown_path"].endswith("latest_report.md")
    assert (tmp_path / "latest_report.md").is_file()
    for key, title in {
        "overall": "CSAgent 总体设计报告",
        "fem": "CSAgent FEM 校核报告",
        "design_solution": "CSAgent 推荐设计方案",
    }.items():
        payload = report["report_outputs"][key]
        stem = ReportGenAgent.REPORT_ARTIFACTS[key][0]
        markdown_path = tmp_path / f"{stem}.md"
        assert payload["title"] == title
        assert payload["report_kind"] == key
        assert payload["markdown_path"] == str(markdown_path)
        assert markdown_path.is_file()
        assert title in markdown_path.read_text(encoding="utf-8")
        if payload["pdf_generated"]:
            assert payload["pdf_path"]
            assert (tmp_path / f"{stem}.pdf").is_file()
        else:
            assert payload["pdf_path"] is None


def test_design_solution_report_can_be_generated_before_fem(monkeypatch, tmp_path):
    monkeypatch.setenv("CSDM_cph_DISABLE_LLM_AUTO", "1")
    task, _results, candidates = _report_sample()
    agent = ReportGenAgent()

    report = agent.run(
        {
            "task": task,
            "results": [],
            "candidates": candidates,
            "report_kind": "design_solution",
            "output_dir": str(tmp_path),
        }
    )

    markdown_path = tmp_path / "recommended_design_solution.md"
    assert report["report_kind"] == "design_solution"
    assert report["markdown_path"] == str(markdown_path)
    assert set(report["report_outputs"]) == {"design_solution"}
    assert markdown_path.is_file()
    markdown = markdown_path.read_text(encoding="utf-8")
    assert "CSAgent 推荐设计方案" in markdown
    assert "尚未校核" in markdown
    assert "CSAgent FEM 校核报告" not in markdown
    assert not (tmp_path / "latest_report.md").exists()


def test_report_uses_llm_only_for_grounded_engineering_explanation(monkeypatch):
    monkeypatch.setenv("CSDM_cph_DISABLE_LLM_AUTO", "1")
    task, results, candidates = _report_sample()
    agent = ReportGenAgent()

    class ControlledBackend:
        max_tokens = 1800

        def chat(self, system_prompt, user_prompt, max_tokens_override=None, json_mode=False, **_kwargs):
            assert "不得新增候选编号、数值" in system_prompt
            assert "制造工艺适配性" in user_prompt
            assert "只做定性解释" in user_prompt
            assert json_mode is False
            return (
                "### 制造工艺适配性\n"
                "- 先围绕候选铺层组织缠绕和铺放可制造性评审。\n\n"
                "### 缺陷与质量控制\n"
                "- 重点比较圆度、铺层角偏差和分层风险。\n\n"
                "### 有限元结果解读\n"
                "- 结果解释沿用结构化校核结论。"
            )

    agent.llm_backend = ControlledBackend()

    markdown = agent._render_markdown(task, results, candidates)

    assert "缠绕和铺放可制造性评审" in markdown
    assert "PBIPF 公式初筛通过" in markdown
    assert agent._last_llm_explanation_used is True


def test_report_postprocess_removes_duplicate_heading_and_mixed_verdict_text(monkeypatch):
    monkeypatch.setenv("CSDM_cph_DISABLE_LLM_AUTO", "1")
    agent = ReportGenAgent()
    malformed_verdict = "Ver" + "\uff44" + "Dict"

    cleaned = agent._postprocess_engineering_explanation(
        "### 工程解释与制造建议\n"
        "### 有限元结果解读\n"
        f"- {malformed_verdict}为通过，说明结论由结构化结果给出。"
    )

    assert "工程解释与制造建议" not in cleaned
    assert "Verdict" not in cleaned
    assert malformed_verdict not in cleaned
    assert "结论为通过" in cleaned


def test_report_emits_llm_trace_when_engineering_explanation_fails(monkeypatch):
    monkeypatch.setenv("CSDM_cph_DISABLE_LLM_AUTO", "1")
    task, results, candidates = _report_sample()
    events = []
    agent = ReportGenAgent(progress_callback=lambda *args: events.append(args))

    class ControlledBackend:
        max_tokens = 1800

        def __init__(self):
            self.last_call_trace = []

        def chat(self, system_prompt, user_prompt, max_tokens_override=None, json_mode=False, **_kwargs):
            self.last_call_trace = [
                {
                    "backend": "primary",
                    "model": "csllm",
                    "status": "failed",
                    "error_type": "ConnectionError",
                    "error": "connection refused",
                    "latency_ms": 10.0,
                },
                {
                    "backend": "fallback",
                    "model": "deepseek-v4-pro",
                    "status": "failed",
                    "error_type": "TimeoutError",
                    "error": "request timeout",
                    "latency_ms": 20.0,
                },
            ]
            raise RuntimeError("all llm backends failed")

    agent.llm_backend = ControlledBackend()

    markdown = agent._render_markdown(task, results, candidates)

    assert agent._last_llm_explanation_used is False
    assert "### 制造工艺适配性" in markdown
    trace_events = [
        payload
        for _, _, payload in events
        if payload.get("event_type") == "llm_call_trace"
    ]
    assert trace_events
    trace_payload = trace_events[-1]["payload"]
    assert trace_payload["context"]["failed"] is True
    assert trace_payload["selected_backend"] is None
    assert trace_payload["fallback_used"] is False
    assert [item["backend"] for item in trace_payload["trace"]] == ["primary", "fallback"]
    assert "csllm" in str(trace_payload["trace"])
    assert "deepseek-v4-pro" in str(trace_payload["trace"])


def test_report_cleans_llm_explanation_before_using_it(monkeypatch):
    monkeypatch.setenv("CSDM_cph_DISABLE_LLM_AUTO", "1")
    task, results, candidates = _report_sample()
    agent = ReportGenAgent()

    class ControlledBackend:
        max_tokens = 1800

        def __init__(self):
            self.calls = 0

        def chat(self, system_prompt, user_prompt, max_tokens_override=None, json_mode=False, **_kwargs):
            self.calls += 1
            if self.calls == 1:
                return "### 缺陷控制\n- 建议控制到 0.3 mm，并可考虑 T800 替代材料。"
            assert "报告解释文本约束清理器" in system_prompt
            return (
                "### 缺陷与质量控制\n"
                "- 建议围绕圆度、铺层角偏差和分层风险开展质量控制，不引入额外阈值或替代材料。"
            )

    backend = ControlledBackend()
    agent.llm_backend = backend

    markdown = agent._render_markdown(task, results, candidates)

    assert "额外阈值或替代材料" in markdown
    assert "0.3 mm" not in markdown
    assert "T800" not in markdown
    assert backend.calls == 2
    assert agent._last_llm_explanation_used is True

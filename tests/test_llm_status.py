from __future__ import annotations

import pytest

from core.llm_backend import LLMBackend
from core.llm_status import configured_llm_backends, probe_llm_backends


def test_configured_llm_backends_hide_secrets_and_report_availability(monkeypatch) -> None:
    monkeypatch.setenv("PRIMARY_URL", "https://primary.example/v1")
    monkeypatch.setenv("PRIMARY_KEY", "secret-primary")
    monkeypatch.setenv("PRIMARY_MODEL", "domain-model")
    monkeypatch.delenv("FALLBACK_KEY", raising=False)

    statuses = configured_llm_backends(
        {
            "backends": [
                {
                    "name": "primary",
                    "provider": "openai_compatible",
                    "base_url_env": "PRIMARY_URL",
                    "api_key_env": "PRIMARY_KEY",
                    "model_env": "PRIMARY_MODEL",
                },
                {
                    "name": "fallback",
                    "provider": "openai_compatible",
                    "base_url": "https://fallback.example/v1",
                    "api_key_env": "FALLBACK_KEY",
                    "model": "fallback-model",
                },
            ]
        }
    )

    assert statuses[0]["role"] == "primary"
    assert statuses[0]["model"] == "domain-model"
    assert statuses[0]["available_for_call"] is True
    assert statuses[1]["role"] == "fallback"
    assert statuses[1]["available_for_call"] is False
    assert "secret-primary" not in str(statuses)


def test_probe_llm_backends_reports_live_status_without_secrets(monkeypatch) -> None:
    monkeypatch.setenv("CSDM_cph_DISABLE_LLM_AUTO", "0")
    config = {
        "backends": [
            {
                "name": "primary",
                "base_url": "http://primary.local/v1",
                "api_key": "primary-key",
                "model": "primary-model",
                "temperature": 0.1,
                "max_tokens": 16,
                "timeout_seconds": 30,
                "json_output_tokens": 16,
            },
            {
                "name": "fallback",
                "base_url": "http://fallback.local/v1",
                "api_key": "fallback-key",
                "model": "fallback-model",
                "temperature": 0.1,
                "max_tokens": 16,
                "timeout_seconds": 30,
                "json_output_tokens": 16,
            },
        ]
    }
    backend = LLMBackend(config)

    class FakeCompletions:
        def __init__(self, owner):
            self.owner = owner

        def create(self, **payload):
            if "primary" in self.owner.base_url:
                fake_secret = "sk-" + "1234567890abcdef"
                raise RuntimeError(f"failed at http://primary.local/v1 with primary-key and {fake_secret}")

            class Message:
                content = "OK"

            class Choice:
                message = Message()
                finish_reason = "stop"

            class Response:
                choices = [Choice()]

            return Response()

    class FakeChat:
        def __init__(self, owner):
            self.completions = FakeCompletions(owner)

    class FakeOpenAI:
        def __init__(self, base_url, api_key, timeout, default_headers):
            self.base_url = base_url
            self.chat = FakeChat(self)

    backend._openai_cls = FakeOpenAI

    results = probe_llm_backends(config=config, timeout_seconds=1, backend=backend)
    by_name = {item["name"]: item for item in results}

    assert by_name["primary"]["health_status"] == "failed"
    assert by_name["primary"]["health_message"] == "调用失败"
    assert by_name["fallback"]["health_status"] == "success"
    assert by_name["fallback"]["health_message"] == "可用"
    assert by_name["fallback"]["latency_ms"] is not None

    text = str(results)
    assert "primary-model" in text
    assert "fallback-model" in text
    assert "primary-key" not in text
    assert "fallback-key" not in text
    assert "primary.local" not in text
    assert "fallback.local" not in text
    assert "sk-" + "1234567890abcdef" not in text


def test_llm_backend_records_reasoning_budget_empty_content(monkeypatch) -> None:
    monkeypatch.setenv("CSDM_cph_DISABLE_LLM_AUTO", "0")
    backend = LLMBackend(
        {
            "backends": [
                {
                    "name": "reasoning",
                    "base_url": "http://reasoning.local/v1",
                    "api_key": "reasoning-key",
                    "model": "reasoning-model",
                    "temperature": 0.1,
                    "max_tokens": 16,
                    "timeout_seconds": 30,
                    "json_output_tokens": 16,
                }
            ]
        }
    )

    class FakeCompletions:
        def create(self, **payload):
            class Message:
                content = ""
                reasoning_content = "先进行推理但预算耗尽"

            class Choice:
                message = Message()
                finish_reason = "length"

            class Response:
                choices = [Choice()]

            return Response()

    class FakeChat:
        completions = FakeCompletions()

    class FakeOpenAI:
        def __init__(self, base_url, api_key, timeout, default_headers):
            self.chat = FakeChat()

    backend._openai_cls = FakeOpenAI

    with pytest.raises(ValueError, match="推理 token 预算耗尽"):
        backend.chat("system", "user", max_tokens_override=16)

    assert backend.last_call_trace[0]["reasoning_chars"] > 0
    assert backend.last_call_trace[0]["finish_reason"] == "length"
    assert "reasoning-key" not in str(backend.last_call_trace)

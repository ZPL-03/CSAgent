from __future__ import annotations

from core.llm_status import configured_llm_backends


def test_configured_llm_backends_hide_secrets_and_report_availability(monkeypatch):
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

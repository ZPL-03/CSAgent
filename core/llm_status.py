"""LLM 后端配置与健康状态。"""

from __future__ import annotations

import re
from typing import Any, Dict, List

from core.config_loader import load_llm_config
from core.llm_backend import LLMBackend, auto_llm_enabled, resolve_config_value


def configured_llm_backends(config: Dict[str, Any] | None = None) -> List[Dict[str, Any]]:
    """返回不含密钥明文的 LLM 后端配置状态。"""

    llm_config = config or load_llm_config()
    raw_backends = llm_config.get("backends")
    if not isinstance(raw_backends, list) or not raw_backends:
        raw_backends = [llm_config.get("backend", {})]

    statuses = []
    for index, backend in enumerate(item for item in raw_backends if isinstance(item, dict)):
        base_url = resolve_config_value(backend.get("base_url_env"), backend.get("base_url", ""))
        api_key = resolve_config_value(backend.get("api_key_env"), backend.get("api_key", ""))
        model = resolve_config_value(backend.get("model_env"), backend.get("model", ""))
        statuses.append(
            {
                "name": str(backend.get("name") or f"backend_{index + 1}"),
                "provider": str(backend.get("provider") or "openai_compatible"),
                "role": "primary" if index == 0 else "fallback",
                "model": model or "未设置",
                "base_url_configured": bool(base_url),
                "api_key_configured": bool(api_key),
                "available_for_call": bool(base_url and api_key and model),
            }
        )
    return statuses


def _sanitize_status_error(text: Any, config: Dict[str, Any]) -> str:
    cleaned = str(text or "")
    raw_backends = config.get("backends")
    if not isinstance(raw_backends, list) or not raw_backends:
        raw_backends = [config.get("backend", {})]
    for backend in (item for item in raw_backends if isinstance(item, dict)):
        base_url = resolve_config_value(backend.get("base_url_env"), backend.get("base_url", ""))
        api_key = resolve_config_value(backend.get("api_key_env"), backend.get("api_key", ""))
        if base_url:
            cleaned = cleaned.replace(base_url, "[url]")
        if api_key:
            cleaned = cleaned.replace(api_key, "[secret]")
    cleaned = re.sub(r"https?://[^\s'\"),}]+", "[url]", cleaned)
    cleaned = re.sub(r"\b(?:sk|tp)-[A-Za-z0-9_-]{8,}\b", "[secret]", cleaned)
    return cleaned[:500]


def probe_llm_backends(
    config: Dict[str, Any] | None = None,
    timeout_seconds: int = 12,
    backend: LLMBackend | None = None,
) -> List[Dict[str, Any]]:
    """逐个真实探测 LLM 后端，不返回 URL、密钥或提示词内容。"""

    llm_config = config or getattr(backend, "config", None) or load_llm_config()
    statuses = configured_llm_backends(llm_config)
    if not auto_llm_enabled():
        return [
            {
                **status,
                "health_status": "disabled",
                "health_message": "LLM 自动调用已关闭",
                "latency_ms": None,
                "error": "",
            }
            for status in statuses
        ]

    try:
        llm_backend = backend or LLMBackend(llm_config)
    except Exception as exc:
        error = _sanitize_status_error(exc, llm_config)
        return [
            {
                **status,
                "health_status": "failed" if status.get("available_for_call") else "not_configured",
                "health_message": "后端初始化失败" if status.get("available_for_call") else "配置不完整",
                "latency_ms": None,
                "error": error if status.get("available_for_call") else "",
            }
            for status in statuses
        ]

    runtimes = {runtime.name: runtime for runtime in llm_backend.backends}
    runtime_names = set(runtimes)
    results: list[dict[str, Any]] = []
    for status in statuses:
        name = str(status.get("name") or "")
        result = dict(status)
        runtime = runtimes.get(name)
        if not status.get("available_for_call"):
            result.update(
                {
                    "health_status": "not_configured",
                    "health_message": "配置不完整",
                    "latency_ms": None,
                    "error": "",
                }
            )
            results.append(result)
            continue
        if runtime is None:
            result.update(
                {
                    "health_status": "failed",
                    "health_message": "后端运行时不可用",
                    "latency_ms": None,
                    "error": "后端未进入可调用列表",
                }
            )
            results.append(result)
            continue

        original_timeout = runtime.timeout_seconds
        runtime.timeout_seconds = max(1, min(int(timeout_seconds), int(original_timeout or timeout_seconds)))
        runtime.client = None
        excluded = runtime_names - {name}
        try:
            llm_backend.chat(
                "你是 LLM 后端健康检查助手。请只回复 OK。",
                "请回复 OK。",
                max_tokens_override=8,
                excluded_backend_names=excluded,
            )
            trace = list(llm_backend.last_call_trace or [])
            attempt = trace[-1] if trace else {}
            result.update(
                {
                    "health_status": "success",
                    "health_message": "可用",
                    "latency_ms": attempt.get("latency_ms"),
                    "error": "",
                }
            )
        except Exception as exc:
            trace = list(llm_backend.last_call_trace or [])
            attempt = trace[-1] if trace else {}
            result.update(
                {
                    "health_status": "failed",
                    "health_message": "调用失败",
                    "latency_ms": attempt.get("latency_ms"),
                    "error": _sanitize_status_error(attempt.get("error") or exc, llm_config),
                }
            )
        finally:
            runtime.timeout_seconds = original_timeout
        results.append(result)
    return results

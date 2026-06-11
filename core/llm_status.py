"""LLM 后端配置状态。"""

from __future__ import annotations

from typing import Any, Dict, List

from core.config_loader import load_llm_config
from core.llm_backend import resolve_config_value


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

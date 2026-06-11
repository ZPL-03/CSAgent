"""OpenAI 兼容 LLM 后端与回退调用。"""

from __future__ import annotations

import json
import os
import re
import time
from dataclasses import dataclass
from typing import Any, Dict, List
from urllib.parse import urlparse

from core.config_loader import load_llm_config


def resolve_config_value(env_name: str | None, fallback_value: str = "") -> str:
    """从环境变量或配置默认值读取 LLM 参数。"""
    if env_name:
        env_value = os.getenv(env_name, "").strip()
        if env_value:
            return env_value
    return str(fallback_value or "").strip()


def resolve_backend_configs(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """返回按优先级排列的 OpenAI 兼容后端配置。"""
    configured = config.get("backends")
    if isinstance(configured, list) and configured:
        backends = [item for item in configured if isinstance(item, dict)]
    else:
        backend = config.get("backend", {})
        backends = [backend] if isinstance(backend, dict) else []
    if not backends:
        raise ValueError("llm_config.yaml 缺少 backends 配置")

    for backend in backends:
        provider = str(backend.get("provider") or "openai_compatible")
        if provider != "openai_compatible":
            raise ValueError("当前项目只支持 openai_compatible LLM 后端")
    return backends


def resolve_backend_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """返回首个可用 OpenAI 兼容后端配置。"""
    return resolve_backend_configs(config)[0]


@dataclass
class BackendRuntime:
    """单个 OpenAI 兼容后端运行时配置。"""

    name: str
    base_url: str
    api_key: str
    model: str
    temperature: float
    max_tokens: int
    timeout_seconds: int
    json_output_tokens: int
    client: Any = None


def _runtime_from_config(backend: Dict[str, Any]) -> BackendRuntime | None:
    """解析单个后端，缺少关键参数时返回空。"""
    base_url = resolve_config_value(backend.get("base_url_env"), backend.get("base_url", ""))
    api_key = resolve_config_value(backend.get("api_key_env"), backend.get("api_key", ""))
    model = resolve_config_value(backend.get("model_env"), backend.get("model", ""))
    if not base_url or not api_key or not model:
        return None
    return BackendRuntime(
        name=str(backend.get("name") or "openai_compatible"),
        base_url=base_url,
        api_key=api_key,
        model=model,
        temperature=float(backend.get("temperature", 0.2)),
        max_tokens=int(backend.get("max_tokens", 1800)),
        timeout_seconds=int(backend.get("timeout_seconds", 180)),
        json_output_tokens=int(backend.get("json_output_tokens", max(int(backend.get("max_tokens", 1800)), 4096))),
    )


def auto_llm_enabled() -> bool:
    """控制业务对象是否自动初始化 LLM，测试环境可关闭外部调用。"""
    disabled = os.getenv("CSDM_cph_DISABLE_LLM_AUTO", "0")
    return str(disabled).strip() != "1"


def llm_user_agent() -> str:
    value = os.getenv("LLM_USER_AGENT", "CSGPT/1.0").strip()
    return value or "CSGPT/1.0"


class LLMBackend:
    """面向当前项目 LLM 接口的主后端与回退封装。"""

    def __init__(self, config: Dict[str, Any] | None = None) -> None:
        self.config = config or load_llm_config()
        try:
            from openai import OpenAI
        except Exception as exc:
            raise ValueError("当前环境未安装 openai 依赖") from exc
        self._openai_cls = OpenAI

        self.backends: List[BackendRuntime] = []
        missing_groups: list[str] = []
        for backend in resolve_backend_configs(self.config):
            runtime = _runtime_from_config(backend)
            if runtime is None:
                missing_groups.append(str(backend.get("name") or backend.get("model_env") or "openai_compatible"))
                continue
            self.backends.append(runtime)
        if not self.backends:
            raise ValueError(f"LLM 配置不完整，请检查后端：{', '.join(missing_groups) or 'openai_compatible'}")

        self.active_backend = self.backends[0]
        self.last_call_trace: List[Dict[str, Any]] = []
        self.call_history: List[List[Dict[str, Any]]] = []
        self._sync_public_attrs(self.active_backend)

    def _record_call_trace(self, trace: List[Dict[str, Any]]) -> None:
        safe_trace = [dict(item) for item in trace]
        self.last_call_trace = safe_trace
        self.call_history.append(safe_trace)

    def _sanitize_trace_error(self, error: Exception | str) -> str:
        text = str(error)
        for runtime in self.backends:
            if runtime.base_url:
                text = text.replace(runtime.base_url, "[url]")
                host = urlparse(runtime.base_url).netloc
                if host:
                    text = text.replace(host, "[host]")
            if runtime.api_key:
                text = text.replace(runtime.api_key, "[secret]")
        text = re.sub(r"https?://[^\s'\"),}]+", "[url]", text)
        text = re.sub(r"\b(?:sk|tp)-[A-Za-z0-9_-]{8,}\b", "[secret]", text)
        return text[:500]

    def _sync_public_attrs(self, runtime: BackendRuntime) -> None:
        self.base_url = runtime.base_url
        self.api_key = runtime.api_key
        self.model = runtime.model
        self.temperature = runtime.temperature
        self.max_tokens = runtime.max_tokens
        self.timeout_seconds = runtime.timeout_seconds
        self.json_output_tokens = runtime.json_output_tokens
        self.client = runtime.client

    def _client_for(self, runtime: BackendRuntime):
        if runtime.client is None:
            runtime.client = self._openai_cls(
                base_url=runtime.base_url,
                api_key=runtime.api_key,
                timeout=runtime.timeout_seconds,
                default_headers={"User-Agent": llm_user_agent()},
            )
        return runtime.client

    def _json_output_budget(self) -> int:
        return max(int(self.active_backend.json_output_tokens), int(self.active_backend.max_tokens), 4096)

    def chat(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens_override: int | None = None,
        json_mode: bool = False,
        excluded_backend_names: set[str] | None = None,
    ) -> str:
        """按配置优先级调用 LLM，失败时自动尝试回退后端。"""
        last_error: Exception | None = None
        excluded = set(excluded_backend_names or set())
        trace: List[Dict[str, Any]] = []
        for runtime in self.backends:
            if runtime.name in excluded:
                continue
            request_payload = {
                "model": runtime.model,
                "temperature": runtime.temperature,
                "max_tokens": int(max_tokens_override or runtime.max_tokens),
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            }
            if json_mode:
                request_payload["response_format"] = {"type": "json_object"}
            attempt = {
                "backend": runtime.name,
                "model": runtime.model,
                "json_mode": bool(json_mode),
                "max_tokens": int(max_tokens_override or runtime.max_tokens),
                "status": "started",
            }
            started_at = time.perf_counter()
            try:
                client = self._client_for(runtime)
                try:
                    response = client.chat.completions.create(**request_payload)
                except Exception as exc:
                    if not json_mode or "response_format" not in str(exc):
                        raise
                    request_payload.pop("response_format", None)
                    response = client.chat.completions.create(**request_payload)
                self.active_backend = runtime
                self._sync_public_attrs(runtime)
                choice = response.choices[0]
                content = choice.message.content or ""
                attempt["finish_reason"] = getattr(choice, "finish_reason", None)
                attempt["content_chars"] = len(content)
                if not content.strip():
                    attempt["status"] = "failed"
                    attempt["error_type"] = "ValueError"
                    attempt["error"] = f"LLM 后端 {runtime.name} 返回空文本"
                    raise ValueError(f"LLM 后端 {runtime.name} 返回空文本")
                attempt["status"] = "success"
                attempt["latency_ms"] = round((time.perf_counter() - started_at) * 1000.0, 3)
                trace.append(attempt)
                self._record_call_trace(trace)
                return content
            except Exception as exc:
                attempt.setdefault("content_chars", 0)
                attempt["status"] = "failed"
                attempt["error_type"] = type(exc).__name__
                attempt["error"] = self._sanitize_trace_error(exc)
                attempt["latency_ms"] = round((time.perf_counter() - started_at) * 1000.0, 3)
                trace.append(attempt)
                last_error = exc
                continue
        self._record_call_trace(trace)
        if last_error is not None:
            raise last_error
        raise ValueError("LLM 后端列表为空")

    def _extract_json_text(self, text: str) -> str:
        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.strip("`")
            cleaned = cleaned.replace("json\n", "", 1).replace("JSON\n", "", 1)
            cleaned = cleaned.strip()

        candidates = [cleaned]
        array_start = cleaned.find("[")
        array_end = cleaned.rfind("]")
        if array_start != -1 and array_end != -1 and array_end > array_start:
            candidates.append(cleaned[array_start : array_end + 1])

        object_start = cleaned.find("{")
        object_end = cleaned.rfind("}")
        if object_start != -1 and object_end != -1 and object_end > object_start:
            candidates.append(cleaned[object_start : object_end + 1])

        for candidate in candidates:
            try:
                json.loads(candidate)
                return candidate
            except json.JSONDecodeError:
                continue
        return cleaned

    def _repair_json(self, broken_text: str) -> str:
        repair_system = "你是 JSON 修复器。请把用户提供的内容修复成合法 JSON，除 JSON 外不要输出任何说明。"
        repair_user = f"请修复为合法 JSON：\n{broken_text}"
        return self.chat(repair_system, repair_user, max_tokens_override=self._json_output_budget())

    def _parse_json_robust(self, text: str) -> Dict[str, Any] | List[Any]:
        """多级解析 LLM 输出，确保候选生成链路得到结构化 JSON。"""
        extracted = self._extract_json_text(text)
        try:
            return json.loads(extracted)
        except json.JSONDecodeError:
            pass

        try:
            repaired = self._extract_json_text(self._repair_json(extracted))
            return json.loads(repaired)
        except Exception:
            pass

        for wrapper_start, wrapper_end in [("{", "}"), ("[", "]")]:
            depth = 0
            start = -1
            end = -1
            for index, char in enumerate(text):
                if char == wrapper_start:
                    if depth == 0:
                        start = index
                    depth += 1
                elif char == wrapper_end:
                    depth -= 1
                    if depth == 0:
                        end = index + 1
                        break
            if start != -1 and end != -1 and end > start:
                candidate = text[start:end]
                try:
                    parsed = json.loads(candidate)
                except json.JSONDecodeError:
                    continue
                if isinstance(parsed, (dict, list)):
                    return parsed
        return {}

    def generate_json(self, system_prompt: str, user_prompt: str) -> Dict[str, Any] | List[Any]:
        """调用当前 LLM 并解析 JSON 输出。"""
        text = self.chat(
            system_prompt,
            user_prompt,
            max_tokens_override=self._json_output_budget(),
            json_mode=True,
        )
        return self._parse_json_robust(text)

"""OpenAI 兼容 LLM 后端与回退调用。"""

from __future__ import annotations

import os
import ipaddress
import re
import time
from copy import deepcopy
from dataclasses import dataclass, field
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
    proxy_policy: str = "bypass_loopback"
    extra_body: Dict[str, Any] = field(default_factory=dict)
    client: Any = None


def _runtime_from_config(backend: Dict[str, Any]) -> BackendRuntime | None:
    """解析单个后端，缺少关键参数时返回空。"""
    base_url = resolve_config_value(backend.get("base_url_env"), backend.get("base_url", ""))
    api_key = resolve_config_value(backend.get("api_key_env"), backend.get("api_key", ""))
    model = resolve_config_value(backend.get("model_env"), backend.get("model", ""))
    if not base_url or not api_key or not model:
        return None
    proxy_policy = str(backend.get("proxy_policy", "bypass_loopback"))
    if proxy_policy not in {"bypass_loopback", "direct", "environment"}:
        raise ValueError("proxy_policy 必须为 bypass_loopback、direct 或 environment")
    extra_body = backend.get("extra_body", {})
    if not isinstance(extra_body, dict) or set(extra_body).intersection({"model", "messages", "max_tokens", "temperature", "response_format", "stream"}):
        raise ValueError("extra_body 必须是对象，且不能覆盖模型、消息、输出预算或响应格式")
    return BackendRuntime(
        name=str(backend.get("name") or "openai_compatible"),
        base_url=base_url,
        api_key=api_key,
        model=model,
        temperature=float(backend.get("temperature", 0.2)),
        max_tokens=int(backend.get("max_tokens", 1800)),
        timeout_seconds=int(backend.get("timeout_seconds", 180)),
        json_output_tokens=int(backend.get("json_output_tokens", max(int(backend.get("max_tokens", 1800)), 4096))),
        proxy_policy=proxy_policy,
        extra_body=deepcopy(extra_body),
    )


def backend_trust_env(base_url: str, proxy_policy: str) -> bool:
    """回环服务直连，外部 API 按配置继承环境代理；不修改进程代理变量。"""
    if proxy_policy == "direct":
        return False
    if proxy_policy == "environment":
        return True
    host = (urlparse(base_url).hostname or "").lower().rstrip(".")
    if host == "localhost":
        return False
    try:
        return not ipaddress.ip_address(host).is_loopback
    except ValueError:
        return True


def auto_llm_enabled() -> bool:
    """控制业务对象是否自动初始化 LLM，测试环境可关闭外部调用。"""
    disabled = os.getenv("CSDM_cph_DISABLE_LLM_AUTO", "0")
    return str(disabled).strip() != "1"


def llm_user_agent() -> str:
    value = os.getenv("LLM_USER_AGENT", "CSAgent/1.0").strip()
    return value or "CSAgent/1.0"


class LLMCallError(RuntimeError):
    """全部后端调用失败；异常文本只包含脱敏后的调用信息。"""


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
            import httpx

            runtime.client = self._openai_cls(
                base_url=runtime.base_url,
                api_key=runtime.api_key,
                timeout=runtime.timeout_seconds,
                default_headers={"User-Agent": llm_user_agent()},
                http_client=httpx.Client(trust_env=backend_trust_env(runtime.base_url, runtime.proxy_policy)),
            )
        return runtime.client

    def chat(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens_override: int | None = None,
        json_mode: bool = False,
        excluded_backend_names: set[str] | None = None,
    ) -> str:
        """按配置优先级调用 LLM，失败时自动尝试回退后端。"""
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
            if runtime.extra_body:
                # 扩展参数属于单个后端，不根据模型名称猜测供应商协议。
                request_payload["extra_body"] = deepcopy(runtime.extra_body)
            attempt = {
                "backend": runtime.name,
                "model": runtime.model,
                "json_mode": bool(json_mode),
                "max_tokens": int(max_tokens_override or runtime.max_tokens),
                "status": "started",
            }
            if "thinking" in runtime.extra_body:
                attempt["thinking"] = deepcopy(runtime.extra_body["thinking"])
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
                message = choice.message
                content = message.content or ""
                reasoning_content = getattr(message, "reasoning_content", "") or ""
                attempt["finish_reason"] = getattr(choice, "finish_reason", None)
                attempt["content_chars"] = len(content)
                if reasoning_content:
                    attempt["reasoning_chars"] = len(reasoning_content)
                if not content.strip():
                    attempt["status"] = "failed"
                    attempt["error_type"] = "ValueError"
                    if reasoning_content and attempt.get("finish_reason") == "length":
                        attempt["error"] = f"LLM 后端 {runtime.name} 推理 token 预算耗尽，content 为空"
                    else:
                        attempt["error"] = f"LLM 后端 {runtime.name} 返回空文本"
                    raise ValueError(attempt["error"])
                if attempt["finish_reason"] != "stop":
                    raise ValueError(f"LLM 回答未完整结束（finish_reason={attempt['finish_reason']}）")
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
                continue
        self._record_call_trace(trace)
        if trace:
            errors = "；".join(f"{item['backend']} ({item['error_type']}): {item['error']}" for item in trace)
            raise LLMCallError(f"LLM 调用失败：{errors}") from None
        raise LLMCallError("没有可调用的 LLM 后端") from None

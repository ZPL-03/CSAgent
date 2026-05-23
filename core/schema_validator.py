"""JSON Schema 校验工具。"""

from __future__ import annotations

import json
from functools import lru_cache
from typing import Any, Dict

from core.paths import SCHEMA_DIR

try:
    from jsonschema import Draft202012Validator
except Exception:
    Draft202012Validator = Any  # type: ignore[assignment]
    _JSONSCHEMA_AVAILABLE = False
else:
    _JSONSCHEMA_AVAILABLE = True


class SchemaValidationError(ValueError):
    """Schema 校验失败。"""


@lru_cache(maxsize=None)
def load_schema(schema_name: str) -> Dict[str, Any]:
    schema_path = SCHEMA_DIR / schema_name
    with schema_path.open("r", encoding="utf-8") as file:
        return json.load(file)


@lru_cache(maxsize=None)
def get_validator(schema_name: str) -> Draft202012Validator:
    if not _JSONSCHEMA_AVAILABLE:
        raise SchemaValidationError("当前环境未安装 jsonschema 依赖")
    return Draft202012Validator(load_schema(schema_name))


def validate_or_raise(schema_name: str, payload: Dict[str, Any]) -> None:
    if not _JSONSCHEMA_AVAILABLE:
        return
    validator = get_validator(schema_name)
    errors = sorted(validator.iter_errors(payload), key=lambda err: list(err.path))
    if errors:
        first = errors[0]
        path = ".".join(str(part) for part in first.path) or "<root>"
        raise SchemaValidationError(f"{schema_name} 校验失败: {path} -> {first.message}")

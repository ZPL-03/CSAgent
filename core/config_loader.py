"""YAML 配置加载器。"""

from __future__ import annotations

from functools import lru_cache
import math
import os
import re
from pathlib import Path
from typing import Any, Dict

import yaml
from dotenv import load_dotenv

from core.paths import CONFIG_DIR, ROOT_DIR

# 自动加载项目根目录下的 .env 文件
_load_dotenv_result = load_dotenv(ROOT_DIR / ".env")


def _load_yaml(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as file:
        data = yaml.safe_load(file) or {}
    return data


@lru_cache(maxsize=None)
def load_app_config() -> Dict[str, Any]:
    config = _load_yaml(CONFIG_DIR / "app_config.yaml")
    from core.paths import RUN_ROOT

    if RUN_ROOT is not None:
        # 隔离验收只改运行数据路径，内置资料、嵌入模型及代理公式资料仍只读。
        knowledge = config["project_knowledge"]
        for key in ("base_dir", "upload_dir", "rag_chunks_path", "kg_dir", "manifest_path", "structured_dir", "vector_chroma_dir"):
            knowledge[key] = str(RUN_ROOT / knowledge[key])
    return config


@lru_cache(maxsize=None)
def load_llm_config() -> Dict[str, Any]:
    return _load_yaml(CONFIG_DIR / "llm_config.yaml")


def embedding_device() -> str:
    """显式选择嵌入设备；CPU 路径不探测 CUDA 驱动。"""
    device = os.getenv("CSDM_CPH_EMBEDDING_DEVICE", "").strip() or str(load_app_config()["rag"].get("embedding_device", "cpu"))
    if not re.fullmatch(r"cpu|cuda(?::[0-9]+)?", device):
        raise ValueError("嵌入设备必须为 cpu、cuda 或 cuda:N，不支持自动探测。")
    return device


@lru_cache(maxsize=None)
def load_param_ranges() -> Dict[str, Any]:
    return _load_yaml(CONFIG_DIR / "param_ranges.yaml")


def validate_imperfection_ratio(value: Any) -> float:
    """校验以比例表示的分析缺陷比，不推测单位或截断数值。"""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("初始几何缺陷比必须是有限数值，单位为比例。")
    value = float(value)
    bounds = load_param_ranges()["analysis_assumptions"]["imperfection_ratio_bounds"]
    if not math.isfinite(value) or not float(bounds["min"]) <= value <= float(bounds["max"]):
        raise ValueError(f"初始几何缺陷比需要位于 {bounds['min']:g}-{bounds['max']:g} 的分析设置范围。")
    return value


def default_imperfection_ratio() -> float:
    """读取用户未指定分析缺陷比时采用的配置值。"""
    return validate_imperfection_ratio(load_param_ranges()["analysis_assumptions"]["imperfection_ratio"])


@lru_cache(maxsize=None)
def load_material_db() -> Dict[str, Any]:
    return _load_yaml(CONFIG_DIR / "material_db.yaml")

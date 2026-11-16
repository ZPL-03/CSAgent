"""界面和报告的数值显示，不改变计算输入与结果。"""

from __future__ import annotations

import math


def format_number(value: object, digits: int | None = 1, missing: str = "-") -> str:
    """省略末尾零；小于显示分辨率的非零值使用科学计数法。"""
    if value is None or value == "":
        return missing
    if isinstance(value, bool):
        return str(value)
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)
    if not math.isfinite(number):
        return str(value)
    if digits is None:
        return str(int(number)) if number.is_integer() else str(value)
    text = f"{number:.{digits}f}"
    if number and float(text) == 0:
        return f"{number:.{digits}e}"
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return "0" if text == "-0" else text


def format_parameter(name: str, value: object) -> str:
    """角度、比例和层厚保留给定值，其余工程摘要最多一位小数。"""
    exact = name.endswith(("_deg", "_ratio", "_factor")) or "thickness" in name or name.startswith("skin_f")
    return format_number(value, None if exact else 1)


NUMBER_DISPLAY_INSTRUCTION = (
    "压力、几何尺寸和质量等汇总值最多显示一位小数，省略末尾零；整数角度不带小数，非整数角度保留给定值。"
    "缺陷比、单层厚度、材料常数和刚度分量保留必要精度；计算、排序和阈值判断使用原值。"
    "显示值相同时仍说明原值对应的判定，接近零的非零量可用科学计数法。"
)

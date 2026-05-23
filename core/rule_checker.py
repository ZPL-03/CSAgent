"""耐压壳候选方案规则检查器。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

from core.config_loader import load_param_ranges
from core.pressure_hull_profile import (
    load_param_ranges_for_type,
    normalize_layup,
    resolve_hull_type,
    rule_check_param_keys,
    solver_safe_window_keys,
)


@dataclass
class RuleCheckResult:
    is_valid: bool
    errors: List[str]
    suggestions: List[str]
    details: Dict[str, bool]


class RuleChecker:
    """执行参数域内的几何、缺陷和铺层约束校验。"""

    def __init__(self) -> None:
        self.param_ranges = load_param_ranges()

    def _check_range(
        self,
        key: str,
        value: float,
        errors: List[str],
        details: Dict[str, bool],
        type_ranges: Dict[str, Dict[str, float]],
    ) -> None:
        rule = type_ranges.get(key, {})
        if rule.get("min") is not None and value < float(rule["min"]):
            errors.append(f"{key} 小于参数下限 {rule['min']}")
            details[f"{key}_ok"] = False
            return
        if rule.get("max") is not None and value > float(rule["max"]):
            errors.append(f"{key} 大于参数上限 {rule['max']}")
            details[f"{key}_ok"] = False
            return
        details[f"{key}_ok"] = True

    def _balanced_angle_pairs(self, angles: list[float]) -> bool:
        non_zero = [
            round(float(angle), 3)
            for angle in angles
            if 1e-6 < abs(float(angle)) < 89.999
        ]
        for angle in non_zero:
            if angle > 0 and -angle not in non_zero:
                return False
            if angle < 0 and -angle not in non_zero:
                return False
        return True

    def run(
        self,
        candidate: Dict[str, Any],
        strict_solver_window: bool = False,
        hull_type: str | None = None,
    ) -> Dict[str, Any]:
        geometry = candidate.get("geometry", {})
        layup = normalize_layup(candidate.get("layup", {}), geometry)
        errors: List[str] = []
        suggestions: List[str] = []
        details: Dict[str, bool] = {}

        htype = resolve_hull_type(hull_type or candidate.get("hull_type"))
        type_ranges = load_param_ranges_for_type(htype)
        for key in rule_check_param_keys(htype):
            self._check_range(key, float(geometry.get(key, 0.0)), errors, details, type_ranges)

        length = float(geometry.get("length_mm", 0.0))
        radius = float(geometry.get("radius_mm", 1.0))
        thickness = float(geometry.get("thickness_mm", 0.0))
        imperfection = float(geometry.get("imperfection_ratio", 0.0))
        slenderness = length / max(radius, 1e-9)
        thickness_ratio = thickness / max(radius, 1e-9)

        details["slenderness_ok"] = 1.5 <= slenderness <= 10.0
        details["thickness_radius_ratio_ok"] = 0.025 <= thickness_ratio <= 0.26
        details["imperfection_positive_ok"] = imperfection > 0.0
        if not details["slenderness_ok"]:
            errors.append("壳体长径比 L/R 超出当前圆柱耐压壳适用区间")
            suggestions.append("将 L/R 控制在 1.5-10.0 范围内")
        if not details["thickness_radius_ratio_ok"]:
            errors.append("厚径比 t/R 超出当前代理模型适用区间")
            suggestions.append("将厚度和半径调整到当前样本范围内")
        if not details["imperfection_positive_ok"]:
            errors.append("初始缺陷比必须为正值")
            suggestions.append("设置 0.001-0.01 的初始缺陷比")

        angles = [float(angle) for angle in layup.get("angles_deg", [])]
        details["layup_defined"] = bool(angles)
        details["ply_count_ok"] = int(layup.get("ply_count", 0) or 0) >= 16
        details["balanced"] = self._balanced_angle_pairs(angles)
        details["angle_range_ok"] = all(abs(angle) <= 90.0 for angle in angles)
        if not details["layup_defined"]:
            errors.append("铺层定义为空")
            suggestions.append("使用 [90_4/(±alpha/±beta)_8/90_4] 或同等格式")
        if not details["ply_count_ok"]:
            errors.append("铺层层数低于当前耐压壳基准建模下限")
            suggestions.append("至少使用 16 层以上铺层")
        if not details["balanced"]:
            errors.append("铺层中正负角未成对出现")
            suggestions.append("保持 ±α 与 ±β 平衡铺设")
        if not details["angle_range_ok"]:
            errors.append("铺层角超出 ±90° 范围")
            suggestions.append("将铺层角控制在 0-90° 的工程可制造区间")

        if strict_solver_window:
            for detail_key, (lower, upper) in solver_safe_window_keys(htype).items():
                geometry_key = detail_key.replace("solver_", "").replace("_ok", "")
                geometry_key = {
                    "length": "length_mm",
                    "radius": "radius_mm",
                    "thickness": "thickness_mm",
                    "imperfection": "imperfection_ratio",
                }.get(geometry_key, geometry_key)
                value = float(geometry.get(geometry_key, 0.0))
                ok = lower <= value <= upper
                details[detail_key] = ok
                if not ok:
                    errors.append(f"{geometry_key} 超出当前真实求解安全区 {lower}-{upper}")
                    suggestions.append("回到当前参数范围后重新生成候选")

        return {
            "is_valid": not errors,
            "errors": errors,
            "suggestions": suggestions,
            "details": details,
        }

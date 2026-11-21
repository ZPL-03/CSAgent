"""耐压壳候选方案规则检查器。"""

from __future__ import annotations

import math
from typing import Any, Dict, List

from abaqus.cylindrical_geometry import radius_reference, shell_radii
from core.layup_parameters import TEMPLATE_ANGLE_FIELDS, uses_task_angles
from core.pressure_hull_profile import (
    load_param_ranges_for_type,
    normalize_layup,
    resolve_hull_type,
    rule_check_param_keys,
    solver_safe_window_keys,
    sequence_is_balanced,
    sequence_is_symmetric,
)
from core.task_contract import candidate_constraints, normalize_boundary_conditions, normalize_load_conditions, task_geometry_bounds


class RuleChecker:
    """执行参数域内的几何、缺陷和铺层约束校验。"""

    MIN_PLY_COUNT = 16

    def _check_range(
        self,
        key: str,
        value: float,
        errors: List[str],
        details: Dict[str, bool],
        type_ranges: Dict[str, Dict[str, float]],
    ) -> None:
        rule = type_ranges.get(key, {})
        if not math.isfinite(value):
            errors.append(f"{key} 必须是有限数值")
            details[f"{key}_ok"] = False
            return
        if rule.get("min") is not None and value < float(rule["min"]):
            errors.append(f"{key} 小于参数下限 {rule['min']}")
            details[f"{key}_ok"] = False
            return
        if rule.get("max") is not None and value > float(rule["max"]):
            errors.append(f"{key} 大于参数上限 {rule['max']}")
            details[f"{key}_ok"] = False
            return
        details[f"{key}_ok"] = True

    def run(
        self,
        candidate: Dict[str, Any],
        strict_solver_window: bool = False,
        hull_type: str | None = None,
        task: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        geometry = candidate.get("geometry", {})
        errors: List[str] = []
        suggestions: List[str] = []
        details: Dict[str, bool] = {}
        try:
            shell_radii(geometry)
            details["radius_reference_ok"] = True
        except ValueError as exc:
            errors.append(f"半径基准或壳体尺寸无效：{exc}")
            details["radius_reference_ok"] = False
        try:
            layup = normalize_layup(candidate.get("layup", {}), geometry)
        except ValueError as exc:
            errors.append(f"铺层无效：{exc}")
            layup = {}

        htype = resolve_hull_type(hull_type or candidate.get("hull_type"))
        type_ranges = load_param_ranges_for_type(htype)
        active_task = task if task is not None else candidate.get("task_constraints")
        constraints = candidate_constraints(active_task) if active_task is not None else None
        if constraints is not None:
            try:
                type_ranges = task_geometry_bounds(constraints, htype)
            except ValueError as exc:
                errors.append(str(exc))
            details["task_context_ok"] = True
            comparisons = {
                "hull_type": (candidate.get("hull_type"), constraints["hull_type"]),
                "load_conditions": (normalize_load_conditions(candidate.get("load_conditions")), constraints["load_conditions"]),
                "boundary_conditions": (normalize_boundary_conditions(candidate.get("boundary_conditions"))["type"], constraints["boundary_conditions"]["type"]),
                "design_targets": ((candidate.get("design_targets") or {}).get("ultimate_pressure_min_MPa"), constraints["design_targets"]["ultimate_pressure_min_MPa"]),
            }
            for key, (actual, expected) in comparisons.items():
                if key in candidate and actual != expected:
                    errors.append(f"候选 {key} 与任务不一致")
                    details["task_context_ok"] = False
            if radius_reference(geometry) != constraints["radius_reference"]:
                errors.append("候选半径基准与任务不一致")
            material = constraints["material_system"]
            if material.get("is_user_specified") and any(
                (candidate.get("material_system") or {}).get(key) != value
                for key, value in material.items() if key != "is_user_specified"
            ):
                errors.append("候选材料与任务固定材料不一致")
        for key in rule_check_param_keys(htype):
            if uses_task_angles(candidate.get("layup")) and key in TEMPLATE_ANGLE_FIELDS:
                continue
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
        details["ply_count_ok"] = int(layup.get("ply_count", 0) or 0) >= self.MIN_PLY_COUNT
        details["balanced"] = bool(angles) and sequence_is_balanced(angles)
        details["symmetric"] = bool(angles) and sequence_is_symmetric(angles)
        layup_constraints = constraints["layup_constraints"] if constraints is not None else {"balanced": True}
        details["angle_range_ok"] = all(abs(angle) <= 90.0 for angle in angles)
        if not details["layup_defined"]:
            errors.append("铺层定义为空")
            suggestions.append("使用 [90_4/(±alpha/±beta)_8/90_4] 或同等格式")
        if not details["ply_count_ok"]:
            errors.append("铺层层数低于当前耐压壳基准建模下限")
            suggestions.append(f"至少使用 {self.MIN_PLY_COUNT} 层铺层")
        if layup_constraints.get("balanced") and not details["balanced"]:
            errors.append("铺层中正负角层数不相等")
            suggestions.append("保持 ±α 与 ±β 平衡铺设")
        if layup_constraints.get("symmetric") and not details["symmetric"]:
            errors.append("铺层不满足当前任务的中面对称约束")
        allowed = layup_constraints.get("allowed_angles") or []
        details["allowed_angles_ok"] = not allowed or all(angle in allowed for angle in angles)
        if not details["allowed_angles_ok"]:
            errors.append("物理层序含有任务允许集合之外的角度")
        minimum = layup_constraints.get("min_ratio_per_angle", 0.0)
        ratio_angles = set(allowed or angles)
        details["angle_ratios_ok"] = bool(angles) and all(angles.count(angle) / len(angles) >= minimum for angle in ratio_angles)
        if not details["angle_ratios_ok"]:
            errors.append("物理层序不满足任务的各角度最小比例")
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

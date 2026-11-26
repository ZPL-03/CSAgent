"""耐压壳候选方案规则检查器。"""

from __future__ import annotations

from typing import Any, Dict, List

from abaqus.cylindrical_geometry import positive_number, radius_reference, shell_radii
from core.config_loader import validate_imperfection_ratio
from core.layup_parameters import TEMPLATE_ANGLE_FIELDS, uses_task_angles
from core.pressure_hull_profile import (
    normalize_layup,
    required_geometry_params,
    sequence_is_balanced,
    sequence_is_symmetric,
)
from core.task_contract import candidate_constraints, normalize_boundary_conditions, normalize_load_conditions


class RuleChecker:
    """校验可建模几何和任务的尺寸、工况及物理铺层约束。"""

    MIN_PLY_COUNT = 16

    def run(
        self,
        candidate: Dict[str, Any],
        task: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        geometry = candidate.get("geometry") or {}
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

        active_task = task if task is not None else candidate.get("task_constraints")
        constraints = candidate_constraints(active_task) if active_task is not None else None
        if constraints is not None:
            details["task_context_ok"] = True
            comparisons = {
                "hull_type": (candidate.get("hull_type"), constraints["hull_type"]),
                "load_conditions": (normalize_load_conditions(candidate.get("load_conditions")), constraints["load_conditions"]),
                "boundary_conditions": (normalize_boundary_conditions(candidate.get("boundary_conditions"))["type"], constraints["boundary_conditions"]["type"]),
                "design_targets": (candidate.get("design_targets"), constraints["design_targets"]),
            }
            for key, (actual, expected) in comparisons.items():
                if key in candidate and actual != expected:
                    errors.append(f"候选 {key} 与任务不一致")
                    details["task_context_ok"] = False
            if details["radius_reference_ok"] and radius_reference(geometry) != constraints["radius_reference"]:
                errors.append("候选半径基准与任务不一致")
            material = constraints["material_system"]
            if material.get("is_user_specified") and any(
                (candidate.get("material_system") or {}).get(key) != value
                for key, value in material.items() if key != "is_user_specified"
            ):
                errors.append("候选材料与任务固定材料不一致")
        # 默认搜索范围只随任务生效，不用于限制独立的建模输入。
        envelope = constraints["geometry_envelope"] if constraints is not None else {}
        for key in required_geometry_params(candidate.get("hull_type")):
            is_template_angle = key in TEMPLATE_ANGLE_FIELDS
            if is_template_angle and uses_task_angles(candidate.get("layup")):
                continue
            try:
                value = (validate_imperfection_ratio(geometry.get(key)) if key == "imperfection_ratio"
                         else positive_number(geometry.get(key), key))
                if is_template_angle and value > 90:
                    raise ValueError(f"{key} 不得超过 90 度")
                if key in envelope:
                    low, high = envelope[key]
                    if not low <= value <= high:
                        raise ValueError(f"候选 {key}={value:g} 与任务不一致：要求 {low:g} 至 {high:g}")
            except ValueError as exc:
                errors.append(str(exc))
                details[f"{key}_ok"] = False
            else:
                details[f"{key}_ok"] = True

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

        return {
            "is_valid": not errors,
            "errors": errors,
            "suggestions": suggestions,
            "details": details,
        }

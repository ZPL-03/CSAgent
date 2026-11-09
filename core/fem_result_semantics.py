"""有限元结果状态、设计判定与容量证据的统一语义。"""

from __future__ import annotations

import math
from typing import Any, Dict, Tuple


CAPACITY_PRESSURE_FIELDS = (
    "ultimate_pressure_MPa",
    "failure_pressure_MPa",
    "collapse_pressure_MPa",
)

FEM_ARTIFACT_FIELDS = (
    "abaqus_inp",
    "linear_buckling_odb",
    "postbuckling_odb",
    "abaqus_odb",
    "service_odb",
    "target_odb",
    "postbuckling_inp",
    "service_inp",
    "target_inp",
    "visualization_json",
    "user_subroutine_path",
    "material_strength_include",
)


def is_successful_result(results: Dict[str, Any]) -> bool:
    """返回求解链路是否形成可用结果，不把失败作业的局部判定视为成功。"""
    return isinstance(results, dict) and results.get("status") == "success"


def is_passed_design_check(results: Dict[str, Any]) -> bool:
    """返回当前验证范围内的设计目标校核是否通过。"""
    passed = is_successful_result(results) and str(results.get("verdict") or "").strip() == "通过"
    if results.get("verification_scope") == "composite_cylindrical_shell_submodel":
        return passed and (results.get("target_stress_coverage") or {}).get("status") == "complete"
    return passed


def result_semantic_errors(results: Dict[str, Any]) -> Tuple[str, ...]:
    """返回状态、判定和容量字段之间的语义冲突。"""
    errors = []
    status = results.get("status")
    verdict = str(results.get("verdict") or "").strip()

    if status not in {"success", "failed", "max_retries_exceeded"}:
        errors.append(f"未知求解状态：{status}")
    if verdict and verdict not in {"通过", "不通过"}:
        errors.append(f"未知设计判定：{verdict}")
    if status != "success" and verdict:
        errors.append("失败或超限结果不得保留设计通过/不通过判定")
    if status != "success" and any(results.get(field) is not None for field in CAPACITY_PRESSURE_FIELDS):
        errors.append("失败或超限结果不得作为容量压力证据")

    for field in CAPACITY_PRESSURE_FIELDS:
        value = results.get(field)
        if value is None:
            continue
        try:
            pressure = float(value)
        except (TypeError, ValueError):
            errors.append(f"{field} 不是有效数值")
            continue
        if not math.isfinite(pressure) or pressure <= 0.0:
            errors.append(f"{field} 必须为正的有限数值")

    return tuple(errors)


def normalize_result_semantics(results: Dict[str, Any]) -> Dict[str, Any]:
    """规范化可持久化结果，保留诊断量但不让失败结果携带设计或容量结论。"""
    normalized = dict(results)
    if normalized.get("status") != "success":
        normalized["verdict"] = None
        for field in CAPACITY_PRESSURE_FIELDS:
            normalized[field] = None
    return normalized


def verified_capacity_pressure(results: Dict[str, Any]) -> float | None:
    """返回已完成求解给出的容量压力，不用线性屈曲值替代容量证据。"""
    if not is_successful_result(results):
        return None
    if results.get("verification_scope") == "composite_cylindrical_shell_submodel" and not (
        results.get("progressive_damage_complete") and results.get("damage_state_output_complete")
        and results.get("riks_limit_point_confirmed")
        and (results.get("target_stress_coverage") or {}).get("status") == "complete"
    ):
        return None
    for field in CAPACITY_PRESSURE_FIELDS:
        value = results.get(field)
        if value is None or isinstance(value, bool):
            continue
        try:
            pressure = float(value)
        except (TypeError, ValueError):
            continue
        if math.isfinite(pressure) and pressure > 0.0:
            return pressure
    return None


def required_fem_artifact_fields(results: Dict[str, Any]) -> Tuple[str, ...]:
    """返回结果实际引用或其已声明证据所要求的有限元工件字段。"""
    required = {
        field
        for field in FEM_ARTIFACT_FIELDS
        if isinstance(results.get(field), str) and str(results.get(field)).strip()
    }

    if results.get("linear_buckling_pressure_MPa") is not None:
        required.update({"abaqus_inp", "linear_buckling_odb", "abaqus_odb", "visualization_json"})
    if results.get("service_pressure_check_status") in {"passed", "failed"}:
        required.update({"service_inp", "service_odb"})
    if results.get("target_pressure_check_status") in {"passed", "failed"}:
        required.update({"target_inp", "target_odb"})
    if any(results.get(field) is not None for field in ("riks_lpf_max", "riks_lpf_last", "riks_increment_count")):
        required.update({"postbuckling_inp", "postbuckling_odb"})
    if results.get("progressive_damage_complete"):
        required.update({"user_subroutine_path", "material_strength_include"})

    return tuple(field for field in FEM_ARTIFACT_FIELDS if field in required)


def complete_case_result_errors(results: Dict[str, Any]) -> Tuple[str, ...]:
    """返回完整设计案例所缺少的求解证据，不把阶段结果当作完整案例。"""
    errors = list(result_semantic_errors(results))
    if not is_successful_result(results):
        errors.append("求解链路未成功完成")
    for stage in ("service", "target"):
        coverage = results.get(f"{stage}_stress_coverage") or {}
        if (coverage.get("status") != "complete"
                or not coverage.get("checked_element_positions")
                or not coverage.get("expected_section_points")
                or coverage.get("incomplete_element_positions") != 0):
            errors.append(f"{stage} 压力缺少全部铺层应力覆盖证据")
        if results.get(f"{stage}_pressure_check_status") not in {"passed", "failed"}:
            errors.append(f"{stage} 压力校核未完成")
    if results.get("riks_limit_point_confirmed") is not True or verified_capacity_pressure(results) is None:
        errors.append("损伤后屈曲路径未确认极限点")
    if results.get("progressive_damage_complete") is not True or results.get("damage_state_output_complete") is not True:
        errors.append("渐进损伤分析或状态变量输出不完整")
    return tuple(errors)

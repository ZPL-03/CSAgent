"""有限元输入完整性校验与设计修订指纹。"""

from __future__ import annotations

import hashlib
import json
import math
import re
from typing import Any, Dict, Iterable

from core.config_loader import load_material_db
from abaqus.cylindrical_geometry import shell_radii
from core.pressure_hull_profile import sequence_is_balanced, sequence_is_symmetric


class FEMInputValidationError(ValueError):
    """表示候选缺少当前圆柱壳 Abaqus 模型所需输入。"""


REVISION_FIELDS = (
    "hull_type",
    "geometry",
    "layup",
    "load_conditions",
    "boundary_conditions",
    "material_system",
    "design_targets",
    "analysis",
)


def design_revision_payload(candidate: Dict[str, Any]) -> Dict[str, Any]:
    """提取会改变有限元模型或判定目标的设计输入。"""
    return {field: candidate.get(field) for field in REVISION_FIELDS}


def compute_design_revision_id(candidate: Dict[str, Any]) -> str:
    """根据规范 JSON 计算稳定设计修订号。"""
    encoded = json.dumps(
        design_revision_payload(candidate),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return "DR_" + hashlib.sha256(encoded).hexdigest()


def attach_design_revision(candidate: Dict[str, Any], parent_revision_id: str | None = None) -> Dict[str, Any]:
    """为候选附加当前修订号，并在设计改变时记录父修订号。"""
    updated = dict(candidate)
    current_revision = compute_design_revision_id(updated)
    previous_revision = str(parent_revision_id or candidate.get("design_revision_id") or "").strip()
    if previous_revision and previous_revision != current_revision:
        updated["parent_design_revision_id"] = previous_revision
    elif not previous_revision:
        updated.pop("parent_design_revision_id", None)
    updated["design_revision_id"] = current_revision
    return updated


def _finite_positive(value: Any, field: str, issues: list[str], *, allow_zero: bool = False) -> float | None:
    if isinstance(value, bool):
        issues.append(field)
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        issues.append(field)
        return None
    if not math.isfinite(number) or number < 0 or (not allow_zero and number <= 0):
        issues.append(field)
        return None
    return number


def validate_fem_input(candidate: Dict[str, Any], material_db: Dict[str, Any] | None = None) -> list[str]:
    """返回当前圆柱壳求解输入中缺失或不一致的字段。"""
    issues: list[str] = []
    if candidate.get("hull_type") != "CYLINDRICAL":
        issues.append("hull_type")

    geometry = candidate.get("geometry")
    if not isinstance(geometry, dict):
        issues.append("geometry")
    else:
        for field in ("length_mm", "radius_mm", "thickness_mm", "alpha_deg", "beta_deg", "imperfection_ratio"):
            _finite_positive(geometry.get(field), f"geometry.{field}", issues)
        try:
            shell_radii(geometry)
        except ValueError:
            issues.append("geometry.radius_reference_or_dimensions")

    layup = candidate.get("layup")
    if not isinstance(layup, dict):
        issues.append("layup")
    else:
        angles = layup.get("angles_deg")
        ply_count = layup.get("ply_count")
        if not isinstance(angles, list) or not angles:
            issues.append("layup.angles_deg")
        else:
            normalized_angles: list[float] = []
            for index, angle in enumerate(angles):
                if isinstance(angle, bool):
                    issues.append(f"layup.angles_deg[{index}]")
                    continue
                try:
                    value = float(angle)
                except (TypeError, ValueError):
                    issues.append(f"layup.angles_deg[{index}]")
                    continue
                if not math.isfinite(value) or abs(value) > 90:
                    issues.append(f"layup.angles_deg[{index}]")
                normalized_angles.append(value)
            if not isinstance(ply_count, int) or isinstance(ply_count, bool) or ply_count != len(angles):
                issues.append("layup.ply_count")
            ply_thickness = layup.get("ply_thickness_mm")
            if ply_thickness is None:
                issues.append("layup.ply_thickness_mm")
            elif isinstance(geometry, dict):
                ply_value = _finite_positive(ply_thickness, "layup.ply_thickness_mm", issues)
                total_value = _finite_positive(geometry.get("thickness_mm"), "geometry.thickness_mm", [])
                if ply_value is not None and total_value is not None:
                    if abs(ply_value * len(angles) - total_value) > 1e-5:
                        issues.append("layup.ply_thickness_mm")
            if len(normalized_angles) == len(angles):
                if layup.get("balanced") is not sequence_is_balanced(normalized_angles):
                    issues.append("layup.balanced")
                if layup.get("symmetric") is not sequence_is_symmetric(normalized_angles):
                    issues.append("layup.symmetric")
            for field in ("layup", "skin_layup"):
                value = layup.get(field)
                if value is not None and re.search(r"±|\]s|_\d+", str(value)):
                    issues.append("layup.compact_notation")

    material = candidate.get("material_system")
    material_db = material_db or load_material_db()
    required_material_fields: Iterable[str] = (
        "name",
        "material_key",
        "density_kg_per_m3",
        "E1_GPa",
        "E2_GPa",
        "G12_GPa",
        "nu12",
        "Xt_MPa",
        "Xc_MPa",
        "Yt_MPa",
        "Yc_MPa",
        "S_MPa",
    )
    if not isinstance(material, dict):
        issues.append("material_system")
    else:
        for field in required_material_fields:
            if field in {"name", "material_key"}:
                if not str(material.get(field) or "").strip():
                    issues.append(f"material_system.{field}")
            else:
                _finite_positive(material.get(field), f"material_system.{field}", issues)
        material_key = str(material.get("material_key") or "").strip()
        if material_key and material_key not in material_db:
            issues.append("material_system.material_key")
        elif material_key:
            expected = material_db[material_key]
            if str(material.get("name") or "").strip() != str(expected.get("display_name") or "").strip():
                issues.append("material_system.name")
            for field in (
                "density_kg_per_m3",
                "E1_GPa",
                "E2_GPa",
                "G12_GPa",
                "nu12",
                "Xt_MPa",
                "Xc_MPa",
                "Yt_MPa",
                "Yc_MPa",
                "S_MPa",
            ):
                try:
                    actual_value = float(material.get(field))
                    expected_value = float(expected.get(field))
                except (TypeError, ValueError):
                    continue
                tolerance = max(1e-9, abs(expected_value) * 1e-9)
                if abs(actual_value - expected_value) > tolerance:
                    issues.append(f"material_system.{field}")

    load = candidate.get("load_conditions")
    if not isinstance(load, dict) or load.get("type") != "external_pressure":
        issues.append("load_conditions.type")
        service_pressure = None
    else:
        service_pressure = _finite_positive(
            load.get("external_pressure_MPa"),
            "load_conditions.external_pressure_MPa",
            issues,
        )

    boundary = candidate.get("boundary_conditions")
    if not isinstance(boundary, dict) or boundary.get("type") not in {
        "END_CLAMPED",
        "END_SIMPLY_SUPPORTED",
        "FLANGE_CONSTRAINED",
    }:
        issues.append("boundary_conditions.type")

    targets = candidate.get("design_targets")
    if not isinstance(targets, dict):
        issues.append("design_targets")
    else:
        target_pressure = _finite_positive(
            targets.get("ultimate_pressure_min_MPa"),
            "design_targets.ultimate_pressure_min_MPa",
            issues,
        )
        if service_pressure is not None and target_pressure is not None and target_pressure < service_pressure:
            issues.append("design_targets.ultimate_pressure_min_MPa")

    revision = str(candidate.get("design_revision_id") or "").strip()
    if revision != compute_design_revision_id(candidate):
        issues.append("design_revision_id")
    return sorted(set(issues))


def validate_fem_input_or_raise(candidate: Dict[str, Any]) -> None:
    """拒绝会触发错误模型或隐式默认值的候选。"""
    issues = validate_fem_input(candidate)
    if issues:
        raise FEMInputValidationError("有限元输入不完整或不一致：" + ", ".join(issues))

"""耐压壳设计任务契约与工况归一化工具。"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import math
import re
from typing import Any, Dict, Iterable

from abaqus.cylindrical_geometry import radius_reference, shell_radii
from core.config_loader import default_imperfection_ratio, load_param_ranges, validate_imperfection_ratio


DEFAULT_ALLOWED_ANGLES = [0, 45, -45, 90]
DEFAULT_DESIGN_TARGETS = {
    "primary_objective": "最小壳体质量",
}
DEFAULT_SCREENING_PREFERENCES = {
    "top_k_candidates": None,
}
DEFAULT_CANDIDATE_GENERATION_PREFERENCES = {
    "total_candidates": None,
    "llm_candidates": None,
    "case_transfer_candidates": None,
    "doe_candidates": None,
    "source_allocation_mode": "ratio_2_1_1",
}
DEFAULT_LAYUP_CONSTRAINTS = {
    "allowed_angles": DEFAULT_ALLOWED_ANGLES,
    "symmetric": True,
    "balanced": True,
    "min_ratio_per_angle": 0.05,
}
DEFAULT_BOUNDARY_TYPE = "END_CLAMPED"
DEFAULT_LOAD_TYPE = "external_pressure"
DEFAULT_EXTERNAL_PRESSURE_MPA = 30.0

LOAD_CASE_LABELS = {
    "external_pressure": "外部静水压力",
}

BOUNDARY_CONDITION_LIBRARY = {
    "END_CLAMPED": {
        "type": "END_CLAMPED",
        "label": "两端固支",
        "description": "圆柱耐压壳两端截面平动与转动约束，用于基准外压屈曲与后屈曲校核。",
        "axial_edges": ["X0", "X1"],
        "radial_constraint": True,
        "rotation_constraint": True,
    },
    "END_SIMPLY_SUPPORTED": {
        "type": "END_SIMPLY_SUPPORTED",
        "label": "两端简支",
        "description": "两端径向位移受限，轴向与转角按简支等效处理。",
        "axial_edges": ["X0", "X1"],
        "radial_constraint": True,
        "rotation_constraint": False,
    },
    "FLANGE_CONSTRAINED": {
        "type": "FLANGE_CONSTRAINED",
        "label": "端部法兰等效约束",
        "description": "端部采用法兰或刚性环等效约束，适合端部夹持边界建模。",
        "axial_edges": ["X0", "X1"],
        "radial_constraint": True,
        "rotation_constraint": True,
    },
}


def _finite_float(value: Any, field: str) -> float:
    """解析显式工程数值；非法输入由调用方处理。"""
    if isinstance(value, bool):
        raise ValueError(f"{field} 必须是有限数值。")
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError(f"{field} 必须是有限数值。") from exc
    if not math.isfinite(number):
        raise ValueError(f"{field} 必须是有限数值。")
    return number


def validate_quantity(value: Any, field: str, available: int | None = None) -> int:
    """校验显式数量，不把非法值截断或替换为默认值。"""
    limits = {
        "total_candidates": ("候选方案数量", 1, 60),
        "top_k_candidates": ("预筛保留数量", 1, min(30, available if available is not None else 30)),
        "llm_candidates": ("LLM 来源数量", 0, 60),
        "case_transfer_candidates": ("案例迁移来源数量", 0, 60),
        "doe_candidates": ("DOE 来源数量", 0, 60),
    }
    if field not in limits:
        raise ValueError(f"不支持的数量字段：{field}。")
    label, minimum, maximum = limits[field]
    message = f"{label}需要输入 {minimum} 至 {maximum} 的整数。"
    if isinstance(value, bool) or not isinstance(value, (int, str)) or not re.fullmatch(r"[0-9]+", str(value).strip()):
        raise ValueError(message)
    number = int(value)
    if not minimum <= number <= maximum:
        raise ValueError(message)
    return number


def _normalize_range(value: Any, field: str) -> list[float]:
    if isinstance(value, Iterable) and not isinstance(value, (str, bytes, dict)):
        values = list(value)
        if len(values) != 2:
            raise ValueError(f"{field} 需要一个数值或两个范围端点。")
        endpoints = [_finite_float(item, field) for item in values]
        return [min(endpoints), max(endpoints)]
    number = _finite_float(value, field)
    return [number, number]


def boundary_condition_payload(boundary_type: str) -> Dict[str, Any]:
    boundary_key = str(DEFAULT_BOUNDARY_TYPE if boundary_type is None else boundary_type).strip().upper()
    alias_map = {
        "CLAMPED": "END_CLAMPED",
        "CCCC": "END_CLAMPED",
        "固支": "END_CLAMPED",
        "固定": "END_CLAMPED",
        "SIMPLY_SUPPORTED": "END_SIMPLY_SUPPORTED",
        "SSSS": "END_SIMPLY_SUPPORTED",
        "简支": "END_SIMPLY_SUPPORTED",
        "FLANGE": "FLANGE_CONSTRAINED",
        "法兰": "FLANGE_CONSTRAINED",
        "夹持": "FLANGE_CONSTRAINED",
    }
    boundary_key = alias_map.get(boundary_key, boundary_key)
    if boundary_key not in BOUNDARY_CONDITION_LIBRARY:
        raise ValueError(f"不支持的边界类型：{boundary_type}。")
    return deepcopy(BOUNDARY_CONDITION_LIBRARY[boundary_key])


def normalize_boundary_conditions(boundary_conditions: Any) -> Dict[str, Any]:
    if isinstance(boundary_conditions, dict):
        boundary_type = str(boundary_conditions.get("type", DEFAULT_BOUNDARY_TYPE)).strip().upper()
        normalized = boundary_condition_payload(boundary_type)
        normalized["label"] = str(boundary_conditions.get("label") or normalized["label"])
        normalized["description"] = str(boundary_conditions.get("description") or normalized["description"])
        return normalized

    text = str(boundary_conditions or "").strip()
    lowered = text.lower()
    if "法兰" in text or "夹持" in text or "flange" in lowered:
        return boundary_condition_payload("FLANGE_CONSTRAINED")
    if "简支" in text or "simply" in lowered or "ssss" in lowered:
        return boundary_condition_payload("END_SIMPLY_SUPPORTED")
    return boundary_condition_payload("END_CLAMPED")


def describe_boundary_conditions(boundary_conditions: Any) -> str:
    normalized = normalize_boundary_conditions(boundary_conditions)
    return str(normalized.get("label", BOUNDARY_CONDITION_LIBRARY[DEFAULT_BOUNDARY_TYPE]["label"]))


def load_condition_payload(load_type: str, external_pressure_MPa: float = DEFAULT_EXTERNAL_PRESSURE_MPA) -> Dict[str, Any]:
    normalized_type = str(DEFAULT_LOAD_TYPE if load_type is None else load_type).strip()
    if normalized_type not in LOAD_CASE_LABELS:
        raise ValueError(f"不支持的载荷类型：{load_type}。")
    pressure = _finite_float(external_pressure_MPa, "external_pressure_MPa")
    if pressure < 0:
        raise ValueError("external_pressure_MPa 必须为非负数值。")
    return {
        "type": normalized_type,
        "label": LOAD_CASE_LABELS[normalized_type],
        "external_pressure_MPa": round(pressure, 6),
    }


def normalize_load_conditions(load_conditions: Any) -> Dict[str, Any]:
    if isinstance(load_conditions, dict):
        raw_type = str(load_conditions.get("type", DEFAULT_LOAD_TYPE)).strip()
        type_mapping = {
            "外压": "external_pressure",
            "静水压力": "external_pressure",
            "external": "external_pressure",
            "external_pressure": "external_pressure",
            "hydrostatic_pressure": "external_pressure",
        }
        normalized_type = type_mapping.get(raw_type, type_mapping.get(raw_type.lower(), raw_type))
        pressures = [
            _finite_float(load_conditions[key], key)
            for key in ("external_pressure_MPa", "pressure_MPa") if key in load_conditions
        ]
        if len(set(pressures)) > 1:
            raise ValueError("工作压力字段与 pressure_MPa 别名取值冲突。")
        normalized = load_condition_payload(normalized_type, pressures[0] if pressures else DEFAULT_EXTERNAL_PRESSURE_MPA)
        for field, digits in (("service_depth_m", 6), ("seawater_density_kg_per_m3", 6), ("gravity_m_per_s2", 8)):
            if field in load_conditions:
                value = _finite_float(load_conditions[field], field)
                if value < 0:
                    raise ValueError(f"{field} 必须为非负数值。")
                normalized[field] = round(value, digits)
        if load_conditions.get("pressure_basis"):
            normalized["pressure_basis"] = str(load_conditions["pressure_basis"])
        return normalized

    text = str(load_conditions or "").strip()
    match = re.search(r"([+-]?(?:[0-9]+(?:\.[0-9]+)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?)\s*(?:MPa|兆帕)", text, flags=re.IGNORECASE)
    if text and not match:
        raise ValueError("载荷需要提供以 MPa 为单位的工作压力。")
    pressure = _finite_float(match.group(1), "external_pressure_MPa") if match else DEFAULT_EXTERNAL_PRESSURE_MPA
    return load_condition_payload(DEFAULT_LOAD_TYPE, pressure)


def describe_load_conditions(load_conditions: Any, *, display: bool = False) -> str:
    """描述工况；显示出口可简化压力，检索和计算说明保留原值。"""
    normalized = normalize_load_conditions(load_conditions)
    pressure = normalized.get("external_pressure_MPa", 0.0)
    if display:
        from core.display import format_number
        pressure = format_number(pressure)
    return f"{normalized['label']}：p={pressure} MPa"


def equivalent_in_plane_load(load_conditions: Any) -> float:
    normalized = normalize_load_conditions(load_conditions)
    return round(float(normalized.get("external_pressure_MPa", 0.0)), 3)


def load_case_code(load_conditions: Any) -> float:
    normalize_load_conditions(load_conditions)
    return 0.0


def boundary_condition_code(boundary_conditions: Any) -> float:
    normalized = normalize_boundary_conditions(boundary_conditions)
    mapping = {
        "END_SIMPLY_SUPPORTED": 0.0,
        "END_CLAMPED": 1.0,
        "FLANGE_CONSTRAINED": 2.0,
    }
    return mapping.get(normalized["type"], 1.0)


def normalize_geometry_envelope(envelope: Dict[str, Any] | None) -> Dict[str, Any]:
    """显式尺寸和区间定义任务搜索范围，配置仅提供缺省范围。"""
    defaults = load_param_ranges()["geometry_search_defaults"]
    values = {}
    aliases = {
        "L": "length_mm",
        "length": "length_mm",
        "shell_length_mm": "length_mm",
        "R": "radius_mm",
        "radius": "radius_mm",
        "shell_radius_mm": "radius_mm",
        "t": "thickness_mm",
        "thickness": "thickness_mm",
        "shell_thickness_mm": "thickness_mm",
        "alpha": "alpha_deg",
        "beta": "beta_deg",
        "Ir": "imperfection_ratio",
        "imperfection": "imperfection_ratio",
    }
    for raw_key, value in (envelope or {}).items():
        key = aliases.get(str(raw_key), str(raw_key))
        if key == "imperfection_ratio":
            endpoints = list(value) if isinstance(value, (list, tuple)) else [value, value]
            if len(endpoints) != 2:
                raise ValueError("初始几何缺陷比需要一个固定值，不作为搜索变量。")
            bounds = [validate_imperfection_ratio(item) for item in endpoints]
            if bounds[0] != bounds[1]:
                raise ValueError("初始几何缺陷比需要一个固定值，不作为搜索变量。")
        elif key in defaults:
            bounds = _normalize_range(value, f"geometry_envelope.{key}")
        else:
            continue
        if key in values and values[key] != bounds:
            label = "初始几何缺陷比" if key == "imperfection_ratio" else key
            raise ValueError(f"{label} 字段与别名取值冲突。")
        values[key] = bounds
    for key, default in defaults.items():
        if key not in values:
            values[key] = _normalize_range([default["min"], default["max"]], f"geometry_envelope.{key}")
        low, high = values[key]
        if low <= 0:
            raise ValueError(f"任务的 {key} 必须为正数。")
        if key in {"alpha_deg", "beta_deg"} and high > 90:
            raise ValueError(f"任务的 {key} 不得超过 90 度。")
    if "imperfection_ratio" not in values:
        defect = default_imperfection_ratio()
        values["imperfection_ratio"] = [defect, defect]
    return values


def normalize_screening_preferences(preferences: Dict[str, Any] | None) -> Dict[str, Any]:
    normalized = deepcopy(DEFAULT_SCREENING_PREFERENCES)
    if not isinstance(preferences, dict):
        return normalized
    top_k_value = preferences.get("top_k_candidates", normalized["top_k_candidates"])
    if top_k_value is None:
        normalized["top_k_candidates"] = None
        return normalized
    normalized["top_k_candidates"] = validate_quantity(top_k_value, "top_k_candidates")
    return normalized


def normalize_candidate_generation_preferences(preferences: Dict[str, Any] | None) -> Dict[str, Any]:
    normalized = deepcopy(DEFAULT_CANDIDATE_GENERATION_PREFERENCES)
    if not isinstance(preferences, dict):
        return normalized
    total_value = preferences.get("total_candidates", normalized["total_candidates"])
    normalized["total_candidates"] = (
        None if total_value is None else validate_quantity(total_value, "total_candidates")
    )
    explicit_sources = False
    for key in ["llm_candidates", "case_transfer_candidates", "doe_candidates"]:
        if preferences.get(key) is None:
            normalized[key] = None
            continue
        normalized[key] = validate_quantity(preferences[key], key)
        explicit_sources = True
    normalized["source_allocation_mode"] = (
        "explicit_counts" if explicit_sources else str(preferences.get("source_allocation_mode") or "ratio_2_1_1")
    )
    return normalized


def normalize_task_payload(
    task: Dict[str, Any],
    *,
    material_system: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    normalized = dict(task or {})
    normalized.pop("task_id", None)
    if material_system:
        normalized["material_system"] = dict(material_system)

    normalized["application"] = str(normalized.get("application") or "复合材料外压圆柱耐压壳")
    normalized["load_conditions"] = normalize_load_conditions(normalized.get("load_conditions"))
    normalized["boundary_conditions"] = normalize_boundary_conditions(normalized.get("boundary_conditions"))
    envelope = dict(normalized.get("geometry_envelope") or {})
    fixed_facts = (normalized.get("user_input_facts") or {}).get("fixed_geometry") or {}
    search_defaults = load_param_ranges()["geometry_search_defaults"]
    # 固定几何是任务约束，不把它当作采样中心或截断到全局范围。
    for key, value in fixed_facts.items():
        if key not in search_defaults:
            continue
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            raise ValueError(f"固定几何 {key} 必须是有限数值。")
        if key in envelope and _normalize_range(envelope[key], f"geometry_envelope.{key}") != [value, value]:
            raise ValueError(f"任务 {key} 与用户固定条件冲突。")
        envelope[key] = [value, value]
    if "imperfection_ratio" in fixed_facts:
        fact_defect = validate_imperfection_ratio(fixed_facts["imperfection_ratio"])
        supplied_keys = {"imperfection_ratio", "Ir", "imperfection"}.intersection(envelope)
        if supplied_keys and normalize_geometry_envelope(envelope)["imperfection_ratio"][0] != fact_defect:
            raise ValueError("任务缺陷比与用户固定条件冲突。")
        envelope["imperfection_ratio"] = fact_defect
    normalized["geometry_envelope"] = normalize_geometry_envelope(envelope)
    # 来源随任务保存，读取历史任务时不根据配置值是否相等猜测用户意图。
    condition_sources = dict(normalized.get("analysis_condition_sources") or {})
    if "imperfection_ratio" in fixed_facts:
        condition_sources["imperfection_ratio"] = "user"
    else:
        condition_sources.setdefault(
            "imperfection_ratio", "task" if {"imperfection_ratio", "Ir", "imperfection"}.intersection(envelope) else "default"
        )
    if condition_sources["imperfection_ratio"] not in {"user", "task", "default"}:
        raise ValueError("初始几何缺陷比来源应为 user、task 或 default。")
    normalized["analysis_condition_sources"] = condition_sources
    normalized["radius_reference"] = radius_reference(normalized)
    bounds = normalized["geometry_envelope"]
    # 半径最大且厚度最小时仍无正内半径，包络中不存在可建模的圆柱壳。
    try:
        shell_radii({"radius_mm": bounds["radius_mm"][1], "thickness_mm": bounds["thickness_mm"][0],
                     "radius_reference": normalized["radius_reference"]})
    except ValueError as exc:
        raise ValueError("任务半径与厚度范围不能形成有效的圆柱壳。") from exc
    normalized["candidate_generation_preferences"] = normalize_candidate_generation_preferences(
        normalized.get("candidate_generation_preferences")
    )
    normalized["screening_preferences"] = normalize_screening_preferences(normalized.get("screening_preferences"))
    normalized["layup_constraints"] = {
        **deepcopy(DEFAULT_LAYUP_CONSTRAINTS),
        **dict(normalized.get("layup_constraints", {})),
    }
    constraints = normalized["layup_constraints"]
    for key in ("symmetric", "balanced"):
        if not isinstance(constraints[key], bool):
            raise ValueError(f"layup_constraints.{key} 必须是布尔值。")
    angles = constraints["allowed_angles"]
    if not isinstance(angles, list) or any(
        isinstance(angle, bool) or not isinstance(angle, (int, float))
        or not math.isfinite(angle) or abs(angle) > 90 for angle in angles
    ):
        raise ValueError("allowed_angles 必须是 ±90 度范围内的有限角度数组。")
    ratio = constraints["min_ratio_per_angle"]
    if isinstance(ratio, bool) or not isinstance(ratio, (int, float)) or not math.isfinite(ratio) or not 0 <= ratio <= 1:
        raise ValueError("min_ratio_per_angle 必须在 0 到 1 之间。")
    targets = dict(normalized.get("design_targets", {}))
    unknown_targets = set(targets).difference(DEFAULT_DESIGN_TARGETS)
    if unknown_targets:
        raise ValueError("不支持的设计目标字段：" + "、".join(sorted(unknown_targets)))
    normalized["design_targets"] = {
        **deepcopy(DEFAULT_DESIGN_TARGETS),
        **targets,
    }

    from core.pressure_hull_profile import resolve_hull_type

    hull_type = resolve_hull_type(normalized.get("hull_type"))
    normalized["hull_type"] = hull_type
    normalized.setdefault("material_system", {})
    return normalized


def task_instance_label(task_record: Dict[str, Any] | None) -> str:
    task_id = str((task_record or {}).get("task_id") or "").strip()
    return task_id or "-"


def task_payload_from_request(task_record: Dict[str, Any] | None) -> Dict[str, Any]:
    if not isinstance(task_record, dict):
        return normalize_task_payload({})
    if isinstance(task_record.get("task"), dict):
        return normalize_task_payload(dict(task_record.get("task") or {}))
    return normalize_task_payload(dict(task_record))


def task_imperfection_ratio(task: Dict[str, Any] | None) -> float:
    """所有候选路径使用任务的固定缺陷比；缺省值由任务归一化提供。"""
    return task_payload_from_request(task)["geometry_envelope"]["imperfection_ratio"][0]


def candidate_constraints(task: Dict[str, Any]) -> Dict[str, Any]:
    """提取候选生成、预筛与求解共同使用的任务约束快照。"""
    payload = task_payload_from_request(task)
    return deepcopy({key: payload[key] for key in (
        "hull_type", "geometry_envelope", "radius_reference", "layup_constraints",
        "load_conditions", "boundary_conditions", "design_targets", "material_system",
    )})


def describe_imperfection_source(task: Dict[str, Any] | None) -> str:
    """返回任务保存的缺陷比取值来源。"""
    source = task_payload_from_request(task)["analysis_condition_sources"]["imperfection_ratio"]
    return {"user": "用户指定", "task": "任务参数", "default": "配置默认"}[source]


def build_task_request_record(
    task: Dict[str, Any],
    *,
    task_id: str,
    source: str,
    created_at: str | None = None,
) -> Dict[str, Any]:
    return {
        "task_id": str(task_id).strip(),
        "created_at": str(created_at or datetime.now(timezone.utc).isoformat()),
        "source": str(source),
        "task": normalize_task_payload(task),
    }


def task_identity_payload(task_record: Dict[str, Any] | None) -> Dict[str, str]:
    task_id = str((task_record or {}).get("task_id") or "").strip()
    return {"task_id": task_id} if task_id else {}


def summarize_task(task: Dict[str, Any]) -> Dict[str, str]:
    normalized_task = task_payload_from_request(task)
    return {
        "application": normalized_task["application"],
        "load_conditions": describe_load_conditions(normalized_task["load_conditions"]),
        "boundary_conditions": describe_boundary_conditions(normalized_task["boundary_conditions"]),
        "candidate_pool": f"候选池目标 {normalized_task['candidate_generation_preferences']['total_candidates'] or '待确认'}",
        "top_k": f"初筛保留 {normalized_task['screening_preferences']['top_k_candidates'] or '待确认'}",
        "objective": (
            f"P_ult >= {normalized_task['load_conditions']['external_pressure_MPa']} MPa，"
            f"{normalized_task['design_targets']['primary_objective']}"
        ),
    }


def requested_candidate_pool_size(task: Dict[str, Any] | None) -> int | None:
    if not isinstance(task, dict) or not task:
        raise ValueError("缺少任务记录，无法读取候选池总数。")
    normalized_task = task_payload_from_request(task)
    value = normalized_task["candidate_generation_preferences"]["total_candidates"]
    return int(value) if value is not None else None


def requested_screen_top_k(task: Dict[str, Any] | None) -> int | None:
    if not isinstance(task, dict) or not task:
        raise ValueError("缺少任务记录，无法读取初筛保留数量。")
    normalized_task = task_payload_from_request(task)
    value = normalized_task["screening_preferences"]["top_k_candidates"]
    return int(value) if value is not None else None


def effective_screen_top_k(task: Dict[str, Any] | None, available_count: int) -> int:
    requested = requested_screen_top_k(task)
    return max(0, min(requested, max(int(available_count), 0))) if requested is not None else 0

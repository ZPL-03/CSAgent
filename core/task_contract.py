"""耐压壳设计任务契约与工况归一化工具。"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Dict, Iterable


DEFAULT_ALLOWED_ANGLES = [0, 45, -45, 90]
DEFAULT_GEOMETRY_ENVELOPE = {
    "length_mm": [300.0, 800.0],
    "radius_mm": [80.0, 180.0],
    "thickness_mm": [5.0, 20.0],
    "alpha_deg": [10.0, 80.0],
    "beta_deg": [10.0, 80.0],
    "imperfection_ratio": [0.001, 0.01],
}
DEFAULT_DESIGN_TARGETS = {
    "ultimate_pressure_min_MPa": 30.0,
    "primary_objective": "最小壳体质量",
}
DEFAULT_SCREENING_PREFERENCES = {
    "top_k_candidates": 5,
}
DEFAULT_CANDIDATE_GENERATION_PREFERENCES = {
    "total_candidates": 10,
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


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_int(value: Any, default: int) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _normalize_range(value: Any, fallback: list[float]) -> list[float]:
    if isinstance(value, Iterable) and not isinstance(value, (str, bytes, dict)):
        values = list(value)
        if len(values) >= 2:
            low = _safe_float(values[0], fallback[0])
            high = _safe_float(values[1], fallback[1])
            return [min(low, high), max(low, high)]
    if isinstance(value, (int, float, str)):
        number = _safe_float(value, (fallback[0] + fallback[1]) / 2.0)
        return [number, number]
    return list(fallback)


def boundary_condition_payload(boundary_type: str) -> Dict[str, Any]:
    boundary_key = str(boundary_type or DEFAULT_BOUNDARY_TYPE).strip().upper()
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
        boundary_key = DEFAULT_BOUNDARY_TYPE
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
    normalized_type = str(load_type or DEFAULT_LOAD_TYPE).strip()
    if normalized_type not in LOAD_CASE_LABELS:
        normalized_type = DEFAULT_LOAD_TYPE
    pressure = max(_safe_float(external_pressure_MPa, DEFAULT_EXTERNAL_PRESSURE_MPA), 0.0)
    return {
        "type": normalized_type,
        "label": LOAD_CASE_LABELS[normalized_type],
        "external_pressure_MPa": round(pressure, 3),
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
        pressure = (
            load_conditions.get("external_pressure_MPa")
            if load_conditions.get("external_pressure_MPa") is not None
            else load_conditions.get("pressure_MPa")
        )
        return load_condition_payload(normalized_type, _safe_float(pressure, DEFAULT_EXTERNAL_PRESSURE_MPA))

    text = str(load_conditions or "").strip()
    import re

    match = re.search(r"([0-9]+(?:\.[0-9]+)?)\s*(?:MPa|兆帕)", text, flags=re.IGNORECASE)
    pressure = _safe_float(match.group(1), DEFAULT_EXTERNAL_PRESSURE_MPA) if match else DEFAULT_EXTERNAL_PRESSURE_MPA
    return load_condition_payload(DEFAULT_LOAD_TYPE, pressure)


def describe_load_conditions(load_conditions: Any) -> str:
    normalized = normalize_load_conditions(load_conditions)
    return f"{normalized['label']}：p={normalized.get('external_pressure_MPa', 0.0)} MPa"


def equivalent_in_plane_load(load_conditions: Any) -> float:
    normalized = normalize_load_conditions(load_conditions)
    return round(float(normalized.get("external_pressure_MPa", 0.0)), 3)


def boundary_stiffness_factor(boundary_conditions: Any) -> float:
    normalized = normalize_boundary_conditions(boundary_conditions)
    mapping = {
        "END_SIMPLY_SUPPORTED": 0.94,
        "END_CLAMPED": 1.00,
        "FLANGE_CONSTRAINED": 1.06,
    }
    return mapping.get(normalized["type"], 1.00)


def load_case_code(load_conditions: Any) -> float:
    normalized = normalize_load_conditions(load_conditions)
    return 0.0 if normalized["type"] == "external_pressure" else 0.0


def boundary_condition_code(boundary_conditions: Any) -> float:
    normalized = normalize_boundary_conditions(boundary_conditions)
    mapping = {
        "END_SIMPLY_SUPPORTED": 0.0,
        "END_CLAMPED": 1.0,
        "FLANGE_CONSTRAINED": 2.0,
    }
    return mapping.get(normalized["type"], 1.0)


def normalize_geometry_envelope(envelope: Dict[str, Any] | None) -> Dict[str, Any]:
    data = deepcopy(DEFAULT_GEOMETRY_ENVELOPE)
    if not isinstance(envelope, dict):
        return data
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
    for raw_key, value in envelope.items():
        key = aliases.get(str(raw_key), str(raw_key))
        if key in data:
            data[key] = _normalize_range(value, data[key])
    if data["imperfection_ratio"][1] > 1.0:
        data["imperfection_ratio"] = [value / 1000.0 for value in data["imperfection_ratio"]]
    elif data["imperfection_ratio"][1] > 0.05:
        data["imperfection_ratio"] = [value / 100.0 for value in data["imperfection_ratio"]]
    return data


def normalize_screening_preferences(preferences: Dict[str, Any] | None) -> Dict[str, Any]:
    normalized = deepcopy(DEFAULT_SCREENING_PREFERENCES)
    if not isinstance(preferences, dict):
        return normalized
    top_k_value = preferences.get("top_k_candidates", normalized["top_k_candidates"])
    normalized["top_k_candidates"] = int(max(1, min(_safe_int(top_k_value, normalized["top_k_candidates"]), 30)))
    return normalized


def normalize_candidate_generation_preferences(preferences: Dict[str, Any] | None) -> Dict[str, Any]:
    normalized = deepcopy(DEFAULT_CANDIDATE_GENERATION_PREFERENCES)
    if not isinstance(preferences, dict):
        return normalized
    total_value = preferences.get("total_candidates", normalized["total_candidates"])
    normalized["total_candidates"] = int(max(1, min(_safe_int(total_value, normalized["total_candidates"]), 60)))
    explicit_sources = False
    for key in ["llm_candidates", "case_transfer_candidates", "doe_candidates"]:
        if preferences.get(key) is None:
            normalized[key] = None
            continue
        normalized[key] = int(max(0, min(_safe_int(preferences.get(key), 0), 60)))
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
    normalized["geometry_envelope"] = normalize_geometry_envelope(normalized.get("geometry_envelope"))
    normalized["candidate_generation_preferences"] = normalize_candidate_generation_preferences(
        normalized.get("candidate_generation_preferences")
    )
    normalized["screening_preferences"] = normalize_screening_preferences(normalized.get("screening_preferences"))
    normalized["layup_constraints"] = {
        **deepcopy(DEFAULT_LAYUP_CONSTRAINTS),
        **dict(normalized.get("layup_constraints", {})),
    }
    normalized["design_targets"] = {
        **deepcopy(DEFAULT_DESIGN_TARGETS),
        **dict(normalized.get("design_targets", {})),
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
        "candidate_pool": f"候选池目标 {normalized_task['candidate_generation_preferences']['total_candidates']} 个",
        "top_k": f"初筛保留 Top-{normalized_task['screening_preferences']['top_k_candidates']}",
        "objective": (
            f"P_ult >= {normalized_task['design_targets']['ultimate_pressure_min_MPa']} MPa，"
            f"{normalized_task['design_targets']['primary_objective']}"
        ),
    }


def requested_candidate_pool_size(task: Dict[str, Any] | None) -> int:
    if not isinstance(task, dict) or not task:
        raise ValueError("缺少任务记录，无法读取候选池总数。")
    normalized_task = task_payload_from_request(task)
    return int(normalized_task["candidate_generation_preferences"]["total_candidates"])


def requested_screen_top_k(task: Dict[str, Any] | None) -> int:
    if not isinstance(task, dict) or not task:
        raise ValueError("缺少任务记录，无法读取初筛保留数量。")
    normalized_task = task_payload_from_request(task)
    return int(normalized_task["screening_preferences"]["top_k_candidates"])


def effective_screen_top_k(task: Dict[str, Any] | None, available_count: int) -> int:
    return max(0, min(requested_screen_top_k(task), max(int(available_count), 0)))

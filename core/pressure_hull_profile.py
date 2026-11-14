"""耐压壳设计参数与层合板描述符。"""

from __future__ import annotations

import math
import re
from functools import lru_cache
from typing import Any, Dict, List

from core.config_loader import load_param_ranges as _load_param_ranges_raw
from core.config_loader import fixed_imperfection_ratio
from abaqus.cylindrical_geometry import positive_number, radius_reference, shell_radii


HULL_TYPES = ["CYLINDRICAL"]
TYPE_DISPLAY_NAMES = {
    "CYLINDRICAL": "外压圆柱耐压壳",
}

ALL_GEOMETRY_PARAMS = [
    "length_mm",
    "radius_mm",
    "thickness_mm",
    "alpha_deg",
    "beta_deg",
    "imperfection_ratio",
]
REQUIRED_GEOMETRY_PARAMS = {
    "CYLINDRICAL": list(ALL_GEOMETRY_PARAMS),
}
CANONICAL_GEOMETRY_ORDER = list(ALL_GEOMETRY_PARAMS)

DEFAULT_GEOMETRY = {
    "CYLINDRICAL": {
        "length_mm": 500.0,
        "radius_mm": 100.0,
        "thickness_mm": 10.0,
        "alpha_deg": 40.0,
        "beta_deg": 70.0,
        "imperfection_ratio": fixed_imperfection_ratio(),
    }
}

GEOMETRY_LABELS = {
    "length_mm": "壳体长度 L (mm)",
    "radius_mm": "壳体半径 R (mm)",
    "radius_reference": "半径基准",
    "thickness_mm": "壳体厚度 t (mm)",
    "alpha_deg": "铺层角 α (deg)",
    "beta_deg": "铺层角 β (deg)",
    "imperfection_ratio": "初始缺陷比 Ir",
}

_TYPE_ALIASES = {
    "cylindrical": "CYLINDRICAL",
    "cylinder": "CYLINDRICAL",
    "external_pressure_cylinder": "CYLINDRICAL",
    "圆柱": "CYLINDRICAL",
    "圆柱壳": "CYLINDRICAL",
    "外压圆柱": "CYLINDRICAL",
    "外压圆柱耐压壳": "CYLINDRICAL",
    "耐压壳": "CYLINDRICAL",
}

_GEOMETRY_ALIASES = {
    "L": "length_mm",
    "length": "length_mm",
    "length_mm": "length_mm",
    "shell_length_mm": "length_mm",
    "R": "radius_mm",
    "radius": "radius_mm",
    "radius_mm": "radius_mm",
    "shell_radius_mm": "radius_mm",
    "t": "thickness_mm",
    "thickness": "thickness_mm",
    "thickness_mm": "thickness_mm",
    "shell_thickness_mm": "thickness_mm",
    "alpha": "alpha_deg",
    "alpha_deg": "alpha_deg",
    "beta": "beta_deg",
    "beta_deg": "beta_deg",
    "Ir": "imperfection_ratio",
    "ir": "imperfection_ratio",
    "imperfection": "imperfection_ratio",
    "imperfection_ratio": "imperfection_ratio",
}

LAYUP_TEMPLATE_BY_PC = {
    1: "BASE_90_AB",
    2: "NO_OUTER_90",
}


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def validate_hull_type(name: str | None) -> str:
    """返回标准壳体类型。"""
    if not name:
        return "CYLINDRICAL"
    direct = str(name).strip().upper()
    if direct in HULL_TYPES:
        return direct
    lowered = str(name).strip().lower()
    if lowered in _TYPE_ALIASES:
        return _TYPE_ALIASES[lowered]
    for alias, hull_type in _TYPE_ALIASES.items():
        if alias.lower() in lowered:
            return hull_type
    raise ValueError(f"未知壳体类型：{name}")


def resolve_hull_type(raw: str | None) -> str:
    """宽松解析壳体类型。"""
    try:
        return validate_hull_type(raw)
    except ValueError:
        return "CYLINDRICAL"


def required_geometry_params(hull_type: str = "CYLINDRICAL") -> List[str]:
    return list(REQUIRED_GEOMETRY_PARAMS.get(resolve_hull_type(hull_type), ALL_GEOMETRY_PARAMS))


def all_geometry_params() -> List[str]:
    return list(ALL_GEOMETRY_PARAMS)


def default_geometry(hull_type: str = "CYLINDRICAL") -> Dict[str, float]:
    return dict(DEFAULT_GEOMETRY.get(resolve_hull_type(hull_type), DEFAULT_GEOMETRY["CYLINDRICAL"]))


def canonical_geometry_values(raw_geom: Dict[str, Any] | None) -> Dict[str, float]:
    """只返回输入中真实提供的几何字段，不补齐默认值。"""
    geometry: Dict[str, float] = {}
    if not isinstance(raw_geom, dict):
        return geometry
    for key, value in raw_geom.items():
        normalized_key = _GEOMETRY_ALIASES.get(str(key), str(key))
        if normalized_key in ALL_GEOMETRY_PARAMS and value is not None:
            geometry[normalized_key] = _safe_float(value)
    if "imperfection_ratio" in geometry:
        if geometry["imperfection_ratio"] > 1.0:
            geometry["imperfection_ratio"] = geometry["imperfection_ratio"] / 1000.0
        elif geometry["imperfection_ratio"] > 0.05:
            geometry["imperfection_ratio"] = geometry["imperfection_ratio"] / 100.0
    return {key: round(float(value), 6) for key, value in geometry.items()}


def missing_geometry_params(raw_geom: Dict[str, Any] | None, hull_type: str = "CYLINDRICAL") -> List[str]:
    provided = canonical_geometry_values(raw_geom)
    return [key for key in required_geometry_params(hull_type) if key not in provided]


def normalize_geometry(hull_type: str, raw_geom: Dict[str, Any] | None) -> Dict[str, Any]:
    """补齐并规范候选几何。"""
    geometry = default_geometry(hull_type)
    geometry.update(canonical_geometry_values(raw_geom))
    normalized = {key: round(float(value), 6) for key, value in geometry.items()}
    normalized["radius_reference"] = radius_reference(raw_geom or {})
    return normalized


@lru_cache(maxsize=8)
def load_param_ranges_for_type(hull_type: str = "CYLINDRICAL") -> Dict[str, Dict[str, float]]:
    """读取耐压壳设计变量范围。"""
    _ = resolve_hull_type(hull_type)
    ranges = _load_param_ranges_raw()
    geometry_ranges = ranges.get("geometry", {})
    merged: Dict[str, Dict[str, float]] = {}
    for key in ALL_GEOMETRY_PARAMS:
        value = geometry_ranges.get(key, {})
        if isinstance(value, dict) and "min" in value and "max" in value:
            merged[key] = {"min": float(value["min"]), "max": float(value["max"])}
    return merged


def geometry_to_feature_vector(geometry: Dict[str, Any]) -> List[float]:
    return [float(geometry.get(key, 0.0)) for key in CANONICAL_GEOMETRY_ORDER]


def rule_check_param_keys(hull_type: str = "CYLINDRICAL") -> List[str]:
    return required_geometry_params(hull_type)


def solver_safe_window_keys(hull_type: str = "CYLINDRICAL") -> Dict[str, tuple[float, float]]:
    _ = resolve_hull_type(hull_type)
    return {
        "solver_length_ok": (300.0, 800.0),
        "solver_radius_ok": (80.0, 180.0),
        "solver_thickness_ok": (5.0, 20.0),
        "solver_imperfection_ok": (0.001, 0.01),
    }


def layup_pattern(alpha_deg: float, beta_deg: float, template_name: str = "BASE_90_AB") -> str:
    alpha = f"{float(alpha_deg):g}"
    beta = f"{float(beta_deg):g}"
    if template_name == "NO_OUTER_90":
        return f"[(±{alpha}/±{beta})_10]"
    if template_name == "BENCHMARK_A":
        return "[90_4/(90/±45/0)_8/90_4]"
    return f"[90_4/(±{alpha}/±{beta})_8/90_4]"


def layup_template_name_from_pc(pc_value: Any) -> str | None:
    """返回 PC 标签对应的铺层模板名称。"""
    try:
        pc = int(round(float(pc_value)))
    except (TypeError, ValueError):
        return None
    return LAYUP_TEMPLATE_BY_PC.get(pc)


def parse_layup_sequence(layup_text: str, alpha_deg: float = 40.0, beta_deg: float = 70.0) -> List[float]:
    """展开角度、正负角、重复组和中面对称记号；未知记号不转换为物理层。"""
    text = str(layup_text or "").strip()
    text = text.replace("alpha", str(alpha_deg)).replace("α", str(alpha_deg))
    text = text.replace("beta", str(beta_deg)).replace("β", str(beta_deg))
    text = text.replace("+/-", "±").replace("+-", "±")
    text = text.replace("−", "-").replace("－", "-").replace("deg", "").replace("°", "")
    text = re.sub(r"\s+", "", text)
    index = 0

    def parse_group(closing: str | None = None, depth: int = 0) -> List[float]:
        nonlocal index
        if depth > 32:
            raise ValueError("铺层嵌套深度超过解析上限。")
        sequence: List[float] = []
        while index < len(text):
            char = text[index]
            if char in "[(":
                index += 1
                item = parse_group("]" if char == "[" else ")", depth + 1)
            else:
                match = re.match(r"(±)?([+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?)", text[index:])
                if not match:
                    raise ValueError(f"铺层在位置 {index + 1} 包含无效角度或记号。")
                angle = float(match.group(2))
                if not math.isfinite(angle):
                    raise ValueError("铺层角度必须是有限数值。")
                item = [angle, -angle] if match.group(1) else [angle]
                index += len(match.group(0))
            suffix = re.match(r"(?:_([1-9]\d*|[sS])|([sS]))", text[index:])
            if suffix:
                value = suffix.group(1) or suffix.group(2)
                if value.lower() == "s":
                    item = item + list(reversed(item))
                else:
                    repeat = int(value)
                    if len(item) * repeat > 10000:
                        raise ValueError("展开层数超过解析上限 10000。")
                    item = item * repeat
                index += len(suffix.group(0))
            sequence.extend(item)
            if len(sequence) > 10000:
                raise ValueError("展开层数超过解析上限 10000。")
            if index == len(text):
                if closing is not None:
                    raise ValueError("铺层括号未闭合。")
                return sequence
            if closing is not None and text[index] == closing:
                index += 1
                return sequence
            if text[index] != "/":
                raise ValueError(f"铺层在位置 {index + 1} 缺少分隔符或括号不匹配。")
            index += 1
        raise ValueError("铺层为空或分隔符后缺少角度。")

    return parse_group()


def normalize_layup(raw_layup: Any, geometry: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """返回统一铺层载荷。"""
    geometry = geometry or {}
    alpha = _safe_float(geometry.get("alpha_deg"), 40.0)
    beta = _safe_float(geometry.get("beta_deg"), 70.0)
    if isinstance(raw_layup, dict):
        pc_template = layup_template_name_from_pc(raw_layup.get("PC", raw_layup.get("pc_label")))
        template = str(raw_layup.get("template_name") or raw_layup.get("template") or pc_template or "BASE_90_AB")
        alpha = _safe_float(raw_layup.get("alpha_deg"), alpha)
        beta = _safe_float(raw_layup.get("beta_deg"), beta)
        text = str(raw_layup.get("layup") or raw_layup.get("skin_layup") or "")
        raw_angles = raw_layup.get("angles_deg")
        if raw_angles is not None:
            if not isinstance(raw_angles, list) or not raw_angles or any(
                isinstance(angle, bool) or not isinstance(angle, (float, int)) or not math.isfinite(angle)
                for angle in raw_angles
            ):
                raise ValueError("angles_deg 必须是非空有限数值数组。")
            for field in ("layup", "skin_layup"):
                value = raw_layup.get(field)
                if value and value != "explicit":
                    parsed = parse_layup_sequence(value, alpha, beta)
                    if len(parsed) != len(raw_angles) or any(abs(a - b) > 1e-6 for a, b in zip(parsed, raw_angles)):
                        raise ValueError("铺层文本与 angles_deg 的物理层顺序不一致。")
            for field, expected in (("ply_count", len(raw_angles)), ("symmetric", sequence_is_symmetric(raw_angles)), ("balanced", sequence_is_balanced(raw_angles))):
                if field in raw_layup and (type(raw_layup[field]) is not type(expected) or raw_layup[field] != expected):
                    raise ValueError(f"{field} 与物理层序不一致。")
            text = render_explicit_layup(raw_angles)
        if not text:
            if not any(raw_layup.get(field) for field in ("template_name", "template", "PC", "pc_label")):
                raise ValueError("缺少铺层文本、物理层数组或模板名称。")
            text = layup_pattern(alpha, beta, template)
    else:
        template = "BASE_90_AB"
        text = str(raw_layup or "")

    sequence = parse_layup_sequence(text, alpha, beta)
    total = max(len(sequence), 1)
    count_0 = sum(1 for angle in sequence if abs(angle) < 1e-6)
    count_45 = sum(1 for angle in sequence if abs(abs(angle) - 45.0) < 1e-6)
    count_90 = sum(1 for angle in sequence if abs(abs(angle) - 90.0) < 1e-6)
    total_thickness = _safe_float(geometry.get("thickness_mm"), 0.0)
    return {
        "template_name": template,
        "layup": text,
        "skin_layup": text,
        "alpha_deg": round(alpha, 3),
        "beta_deg": round(beta, 3),
        "ply_count": total,
        "ply_thickness_mm": round(total_thickness / total, 6) if total_thickness > 0.0 else None,
        "angles_deg": [round(float(angle), 3) for angle in sequence],
        "symmetric": sequence_is_symmetric(sequence),
        "balanced": sequence_is_balanced(sequence),
        "skin_f0": round(count_0 / total, 3),
        "skin_f45": round(count_45 / total, 3),
        "skin_f90": round(count_90 / total, 3),
    }


def sequence_is_balanced(sequence: List[float]) -> bool:
    """按每个非 0/90 度角的正负层数判断均衡性。"""
    values = [round(float(angle), 6) for angle in sequence]
    magnitudes = {abs(angle) for angle in values if abs(angle) not in {0.0, 90.0}}
    return all(values.count(magnitude) == values.count(-magnitude) for magnitude in magnitudes)


def sequence_is_symmetric(sequence: List[float]) -> bool:
    """判断逐层序列是否关于层合中面对称。"""
    values = [round(float(angle), 6) for angle in sequence]
    return values == list(reversed(values))


def _format_explicit_angle(angle: float) -> str:
    """把单层角度格式化为不含压缩记号的文本。"""
    value = round(float(angle), 6)
    if abs(value) < 1e-9:
        return "0"
    if value.is_integer():
        return str(int(value))
    return f"{value:.6f}".rstrip("0").rstrip(".")


def render_explicit_layup(sequence: List[float]) -> str:
    """按逐个物理层顺序渲染铺层文本。"""
    return "[" + "/".join(_format_explicit_angle(angle) for angle in sequence) + "]"


def expand_layup_for_fem(raw_layup: Any, geometry: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """把候选铺层统一为 Abaqus 输入所需的逐层显式表示。"""
    geometry = geometry or {}
    raw = dict(raw_layup) if isinstance(raw_layup, dict) else {"layup": str(raw_layup or "")}
    normalized = normalize_layup(raw, geometry)
    explicit_text = all(
        isinstance(raw.get(field), str)
        and not re.search(r"±|\]s|_\d+", raw[field])
        for field in ("layup", "skin_layup")
    )
    raw_angles = raw.get("angles_deg")
    if explicit_text and isinstance(raw_angles, list) and raw_angles:
        try:
            angles = [round(float(angle), 3) for angle in raw_angles]
        except (TypeError, ValueError):
            angles = []
        total_thickness = _safe_float(geometry.get("thickness_mm"), 0.0)
        thickness = raw.get("ply_thickness_mm")
        thickness_ok = False
        try:
            thickness_ok = total_thickness > 0.0 and abs(float(thickness) * len(angles) - total_thickness) <= 1e-5
        except (TypeError, ValueError):
            pass
        if (
            angles
            and raw.get("ply_count") == len(angles)
            and thickness_ok
            and raw.get("balanced") is sequence_is_balanced(angles)
            and raw.get("symmetric") is sequence_is_symmetric(angles)
        ):
            return raw
    else:
        angles = []

    if not angles:
        angles = normalized["angles_deg"]

    total_thickness = _safe_float(geometry.get("thickness_mm"), 0.0)
    count = max(len(angles), 1)
    rendered = render_explicit_layup(angles)
    updated = dict(raw)
    updated.update(
        {
            "layup": rendered,
            "skin_layup": rendered,
            "ply_count": len(angles),
            "angles_deg": angles,
            "ply_thickness_mm": total_thickness / count if total_thickness > 0.0 else raw.get("ply_thickness_mm"),
            "symmetric": sequence_is_symmetric(angles),
            "balanced": sequence_is_balanced(angles),
            "skin_f0": round(sum(1 for angle in angles if abs(angle) < 1e-6) / count, 3),
            "skin_f45": round(sum(1 for angle in angles if abs(abs(angle) - 45.0) < 1e-6) / count, 3),
            "skin_f90": round(sum(1 for angle in angles if abs(abs(angle) - 90.0) < 1e-6) / count, 3),
        }
    )
    return updated


def _qbar(angle_deg: float, material: Dict[str, Any]) -> List[List[float]]:
    values = []
    for key in ("E1_GPa", "E2_GPa", "G12_GPa", "nu12"):
        value = material.get(key)
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            raise ValueError(f"material.{key} 必须是有限数值。")
        values.append(float(value))
    e1, e2, g12 = (value * 1000.0 for value in values[:3])
    nu12 = values[3]
    if any(not math.isfinite(value) or value <= 0 for value in (e1, e2, g12)):
        raise ValueError("单层弹性模量必须为正有限数值。")
    nu21 = nu12 * e2 / e1
    denom = 1.0 - nu12 * nu21
    if not math.isfinite(denom) or denom <= 0:
        raise ValueError("单层面内柔度矩阵不满足正定性。")
    q11 = e1 / denom
    q22 = e2 / denom
    q12 = nu12 * e2 / denom
    q66 = g12

    theta = math.radians(angle_deg)
    m = math.cos(theta)
    n = math.sin(theta)
    m2 = m * m
    n2 = n * n
    m4 = m2 * m2
    n4 = n2 * n2
    q16 = (q11 - q12 - 2.0 * q66) * m2 * m * n - (q22 - q12 - 2.0 * q66) * m * n2 * n
    q26 = (q11 - q12 - 2.0 * q66) * m * n2 * n - (q22 - q12 - 2.0 * q66) * m2 * m * n
    return [
        [q11 * m4 + 2.0 * (q12 + 2.0 * q66) * m2 * n2 + q22 * n4,
         (q11 + q22 - 4.0 * q66) * m2 * n2 + q12 * (m4 + n4),
         q16],
        [(q11 + q22 - 4.0 * q66) * m2 * n2 + q12 * (m4 + n4),
         q11 * n4 + 2.0 * (q12 + 2.0 * q66) * m2 * n2 + q22 * m4,
         q26],
        [q16, q26, (q11 + q22 - 2.0 * q12 - 2.0 * q66) * m2 * n2 + q66 * (m4 + n4)],
    ]


def compute_laminate_stiffness(layup: Dict[str, Any], material: Dict[str, Any], thickness_mm: float) -> Dict[str, Any]:
    """按经典层合板理论计算 A/B/D 刚度矩阵。"""
    if isinstance(thickness_mm, bool) or not isinstance(thickness_mm, (int, float)) or not math.isfinite(thickness_mm) or thickness_mm <= 0:
        raise ValueError("层合板总厚度必须是正有限数值。")
    normalized = normalize_layup(layup, {"alpha_deg": layup.get("alpha_deg"), "beta_deg": layup.get("beta_deg")})
    angles = normalized["angles_deg"]
    ply_count = max(len(angles), 1)
    ply_t = float(thickness_mm) / ply_count
    z0 = -float(thickness_mm) / 2.0
    a = [[0.0 for _ in range(3)] for _ in range(3)]
    b = [[0.0 for _ in range(3)] for _ in range(3)]
    d = [[0.0 for _ in range(3)] for _ in range(3)]

    for idx, angle in enumerate(angles):
        z_bot = z0 + idx * ply_t
        z_top = z_bot + ply_t
        q = _qbar(angle, material)
        for i in range(3):
            for j in range(3):
                a[i][j] += q[i][j] * (z_top - z_bot)
                b[i][j] += 0.5 * q[i][j] * (z_top ** 2 - z_bot ** 2)
                d[i][j] += (1.0 / 3.0) * q[i][j] * (z_top ** 3 - z_bot ** 3)

    return {
        "A": a,
        "B": b,
        "D": d,
        "A22": a[1][1],
        "B23": b[1][2],
        "D12": d[0][1],
        "D22": d[1][1],
        "D33": d[2][2],
    }


def estimate_asme_rd1172_linear_buckling_q(
    geometry: Dict[str, Any],
    stiffness: Dict[str, Any],
    material: Dict[str, Any],
    boundary_conditions: Dict[str, Any] | None = None,
) -> float:
    """按 ASME RD-1172 计算 PBIPF 输入的线性屈曲压力 Q，单位 MPa。"""
    import numpy as np

    _ = material, boundary_conditions
    length = positive_number(geometry.get("length_mm"), "geometry.length_mm")
    radius = shell_radii(geometry)["outer"]
    thickness = positive_number(geometry.get("thickness_mm"), "geometry.thickness_mm")
    a = np.array(stiffness.get("A", []), dtype=float)
    b = np.array(stiffness.get("B", []), dtype=float)
    d = np.array(stiffness.get("D", []), dtype=float)
    if a.shape != (3, 3) or b.shape != (3, 3) or d.shape != (3, 3):
        raise ValueError("ASME RD-1172 Q 计算缺少 3x3 A/B/D 刚度矩阵")

    abd = np.vstack((np.hstack((a, b)), np.hstack((b, d))))
    if not np.isfinite(abd).all() or not np.allclose(abd, abd.T, rtol=1e-10, atol=1e-8):
        raise ValueError("ASME RD-1172 Q 计算要求有限、对称的 ABD 刚度矩阵")
    try:
        np.linalg.cholesky(abd)
        inverse_abd = np.linalg.inv(abd)
    except np.linalg.LinAlgError as exc:
        raise ValueError("ASME RD-1172 Q 计算要求正定的 ABD 刚度矩阵") from exc

    bending_aa = positive_number(inverse_abd[3][3], "ABD_inverse[4,4]")
    bending_hh = positive_number(inverse_abd[4][4], "ABD_inverse[5,5]")
    coupling = float(inverse_abd[4][3])
    vx = -coupling / bending_aa
    vy = -coupling / bending_hh
    eaf = 12.0 / (thickness ** 3 * bending_aa)
    ehf = 12.0 / (thickness ** 3 * bending_hh)

    a12 = float(a[0][1])
    # Lee & Sohn (2024), Eq. (2a): E_at 的分母为 A22*t；Eq. (2) 使用外径 Do。
    eat = positive_number((float(a[0][0]) * float(a[1][1]) - a12 ** 2) / (float(a[1][1]) * thickness), "E_at")
    vxy = positive_number(1.0 - vx * vy, "1-vx*vy")

    zp = ehf ** 1.5 * eat ** 0.5 * vxy ** 0.5 * (length ** 2 / (radius * thickness)) / eaf ** 2
    gamma_d = 0.9 if zp > 100.0 else 1.0 - 0.001 * zp
    knockdown_factor = 0.84
    safety_factor = 1.0
    q_value = (
        0.8531
        * knockdown_factor
        * gamma_d
        * ehf ** 0.75
        * eat ** 0.25
        * thickness ** 2.5
        / (vxy ** 0.75 * length * safety_factor * radius ** 1.5)
    )
    return round(positive_number(q_value, "ASME_Q"), 6)


def estimate_linear_buckling_feature_q(
    geometry: Dict[str, Any],
    stiffness: Dict[str, Any],
    material: Dict[str, Any],
    boundary_conditions: Dict[str, Any] | None = None,
) -> float:
    """返回 PBIPF 当前采用的线性屈曲压力 Q，单位 MPa。"""
    return estimate_asme_rd1172_linear_buckling_q(geometry, stiffness, material, boundary_conditions)


def estimate_shell_mass_kg(geometry: Dict[str, Any], material: Dict[str, Any]) -> float:
    length_m = positive_number(geometry.get("length_mm"), "geometry.length_mm") / 1000.0
    radius_m = shell_radii(geometry)["middle_surface"] / 1000.0
    thickness_m = positive_number(geometry.get("thickness_mm"), "geometry.thickness_mm") / 1000.0
    density = positive_number(material.get("density_kg_per_m3"), "material.density_kg_per_m3")
    volume = 2.0 * math.pi * radius_m * length_m * thickness_m
    return round(max(volume * density, 0.0), 6)


def estimate_areal_density_kg_per_m2(geometry: Dict[str, Any], material: Dict[str, Any]) -> float:
    thickness = positive_number(geometry.get("thickness_mm"), "geometry.thickness_mm")
    density = positive_number(material.get("density_kg_per_m3"), "material.density_kg_per_m3")
    return round(thickness * density / 1000.0, 6)


def describe_geometry_text(hull_type: str, geometry: Dict[str, Any], layup: Dict[str, Any] | None = None) -> str:
    _ = resolve_hull_type(hull_type)
    return (
        f"L={_safe_float(geometry.get('length_mm')):.1f}mm, "
        f"R({radius_reference(geometry)})={_safe_float(geometry.get('radius_mm')):.1f}mm, "
        f"t={_safe_float(geometry.get('thickness_mm')):.2f}mm, "
        f"alpha={_safe_float(geometry.get('alpha_deg')):.1f}deg, "
        f"beta={_safe_float(geometry.get('beta_deg')):.1f}deg, "
        f"Ir={_safe_float(geometry.get('imperfection_ratio')):.4f}"
    )


def build_pressure_hull_meshes(hull_type: str, geometry: Dict[str, Any]) -> List[tuple]:
    """生成 GUI 预览用的完整圆柱壳网格。"""
    try:
        import pyvista as pv
    except ImportError:
        return []

    _ = resolve_hull_type(hull_type)
    length = max(_safe_float(geometry.get("length_mm"), 500.0), 1.0)
    radii = shell_radii(geometry)
    radius = radii["outer"]
    inner_radius = radii["inner"]
    thickness = radius - inner_radius

    axial_count = 28
    circum_count = 144
    xs = [length * i / axial_count for i in range(axial_count + 1)]
    thetas = [2.0 * math.pi * j / circum_count for j in range(circum_count + 1)]

    def _point(x_value: float, radius_value: float, theta_value: float) -> list[float]:
        return [
            x_value,
            radius_value * math.cos(theta_value),
            radius_value * math.sin(theta_value),
        ]

    def _surface_mesh(radius_value: float, reverse: bool = False):
        points = [_point(x_value, radius_value, theta_value) for x_value in xs for theta_value in thetas]
        faces: list[int] = []
        row = circum_count + 1
        for i in range(axial_count):
            for j in range(circum_count):
                a = i * row + j
                b = (i + 1) * row + j
                c = (i + 1) * row + j + 1
                d = i * row + j + 1
                faces.extend([4, a, d, c, b] if reverse else [4, a, b, c, d])
        return pv.PolyData(points, faces)

    def _end_wall_mesh():
        points: list[list[float]] = []
        faces: list[int] = []

        def add_point(x_value: float, radius_value: float, theta_value: float) -> int:
            points.append(_point(x_value, radius_value, theta_value))
            return len(points) - 1

        for x_value in (0.0, length):
            for j in range(circum_count):
                outer_0 = add_point(x_value, radius, thetas[j])
                outer_1 = add_point(x_value, radius, thetas[j + 1])
                inner_1 = add_point(x_value, inner_radius, thetas[j + 1])
                inner_0 = add_point(x_value, inner_radius, thetas[j])
                faces.extend([4, outer_0, outer_1, inner_1, inner_0])
        return pv.PolyData(points, faces)

    outer = _surface_mesh(radius)
    inner = _surface_mesh(inner_radius, reverse=True)
    end_wall = _end_wall_mesh()
    gauge_theta = math.radians(45.0)
    gauge = pv.Line(
        _point(length * 0.52, inner_radius, gauge_theta),
        _point(length * 0.52, radius, gauge_theta),
    ).tube(radius=max(thickness * 0.08, radius * 0.004, 0.35))
    axis = pv.Line((0.0, 0.0, 0.0), (length, 0.0, 0.0)).tube(radius=max(radius * 0.003, 0.25))

    return [
        (outer, {"color": "#6aa5c8", "smooth_shading": True, "opacity": 0.46, "show_edges": True, "edge_color": "#3b657a", "name": "outer_shell"}),
        (inner, {"color": "#d99f54", "smooth_shading": True, "opacity": 0.34, "show_edges": True, "edge_color": "#8a5b20", "name": "inner_surface"}),
        (end_wall, {"color": "#f2cf66", "smooth_shading": False, "opacity": 0.96, "show_edges": True, "edge_color": "#8c6d1f", "name": "end_wall_thickness"}),
        (gauge, {"color": "#d94841", "smooth_shading": True, "opacity": 1.0, "name": "thickness_gauge"}),
        (axis, {"color": "#475569", "smooth_shading": True, "opacity": 0.7, "name": "center_axis"}),
    ]

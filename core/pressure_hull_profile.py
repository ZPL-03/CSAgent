"""耐压壳设计参数与层合板描述符。"""

from __future__ import annotations

import math
import re
from functools import lru_cache
from typing import Any, Dict, List

from core.config_loader import load_param_ranges as _load_param_ranges_raw


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
        "imperfection_ratio": 0.005,
    }
}

GEOMETRY_LABELS = {
    "length_mm": "壳体长度 L (mm)",
    "radius_mm": "壳体半径 R (mm)",
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


def normalize_geometry(hull_type: str, raw_geom: Dict[str, Any] | None) -> Dict[str, float]:
    """补齐并规范候选几何。"""
    geometry = default_geometry(hull_type)
    geometry.update(canonical_geometry_values(raw_geom))
    return {key: round(float(value), 6) for key, value in geometry.items()}


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
    alpha = int(round(float(alpha_deg)))
    beta = int(round(float(beta_deg)))
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


def _expand_token(token: str, alpha_deg: float, beta_deg: float) -> List[float]:
    token = token.strip()
    token = token.replace("alpha", str(alpha_deg)).replace("α", str(alpha_deg))
    token = token.replace("beta", str(beta_deg)).replace("β", str(beta_deg))
    token = token.replace("deg", "").replace("°", "")
    token = token.replace("−", "-").replace("－", "-")
    if not token:
        return []
    if token.startswith("±") or token.startswith("+/-"):
        number = token[1:] if token.startswith("±") else token[3:]
        angle = _safe_float(number, 45.0)
        return [angle, -angle]
    if token.startswith("+-"):
        angle = _safe_float(token[2:], 45.0)
        return [angle, -angle]
    return [_safe_float(token, 0.0)]


def _expand_layup_item(token: str, alpha_deg: float, beta_deg: float) -> List[float]:
    token = token.strip()
    repeat = 1
    match = re.match(r"(.+?)_([0-9]+)$", token)
    if match:
        token = match.group(1)
        repeat = int(match.group(2))
    return _expand_token(token, alpha_deg, beta_deg) * max(repeat, 1)


def _expand_group(group: str, repeat: int, alpha_deg: float, beta_deg: float) -> List[float]:
    items: List[float] = []
    for raw in group.split("/"):
        items.extend(_expand_layup_item(raw, alpha_deg, beta_deg))
    return items * max(repeat, 1)


def parse_layup_sequence(layup_text: str, alpha_deg: float = 40.0, beta_deg: float = 70.0) -> List[float]:
    """展开简写铺层表达式。"""
    text = str(layup_text or "").strip()
    if not text:
        text = layup_pattern(alpha_deg, beta_deg)
    text = text.strip("[] ")
    result: List[float] = []
    index = 0
    while index < len(text):
        if text[index] == "/":
            index += 1
            continue
        if text[index] == "(":
            end = text.find(")", index)
            if end < 0:
                break
            group = text[index + 1:end]
            repeat = 1
            after = end + 1
            match = re.match(r"_([0-9]+)", text[after:])
            if match:
                repeat = int(match.group(1))
                after += len(match.group(0))
            elif text[after:].startswith("_s"):
                after += 2
            result.extend(_expand_group(group, repeat, alpha_deg, beta_deg))
            index = after
            continue
        next_sep = text.find("/", index)
        if next_sep < 0:
            next_sep = len(text)
        token = text[index:next_sep]
        repeat = 1
        match = re.match(r"(.+?)_([0-9]+)$", token)
        if match:
            token = match.group(1)
            repeat = int(match.group(2))
        result.extend(_expand_token(token, alpha_deg, beta_deg) * max(repeat, 1))
        index = next_sep + 1
    return result or [90.0, 90.0, 90.0, 90.0, alpha_deg, -alpha_deg, beta_deg, -beta_deg]


def normalize_layup(raw_layup: Any, geometry: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """返回统一铺层载荷。"""
    geometry = geometry or {}
    alpha = _safe_float(geometry.get("alpha_deg"), 40.0)
    beta = _safe_float(geometry.get("beta_deg"), 70.0)
    if isinstance(raw_layup, dict):
        pc_template = layup_template_name_from_pc(raw_layup.get("PC", raw_layup.get("pc_label")))
        template = str(raw_layup.get("template_name") or raw_layup.get("template") or pc_template or "BASE_90_AB")
        text = str(raw_layup.get("layup") or raw_layup.get("skin_layup") or layup_pattern(alpha, beta, template))
        alpha = _safe_float(raw_layup.get("alpha_deg"), alpha)
        beta = _safe_float(raw_layup.get("beta_deg"), beta)
    else:
        template = "BASE_90_AB"
        text = str(raw_layup or layup_pattern(alpha, beta, template))

    sequence = parse_layup_sequence(text, alpha, beta)
    total = max(len(sequence), 1)
    count_0 = sum(1 for angle in sequence if abs(angle) < 1e-6)
    count_45 = sum(1 for angle in sequence if abs(abs(angle) - 45.0) < 1e-6)
    count_90 = sum(1 for angle in sequence if abs(abs(angle) - 90.0) < 1e-6)
    return {
        "template_name": template,
        "layup": text,
        "skin_layup": text,
        "alpha_deg": round(alpha, 3),
        "beta_deg": round(beta, 3),
        "ply_count": total,
        "angles_deg": [round(float(angle), 3) for angle in sequence],
        "skin_f0": round(count_0 / total, 3),
        "skin_f45": round(count_45 / total, 3),
        "skin_f90": round(count_90 / total, 3),
    }


def _qbar(angle_deg: float, material: Dict[str, Any]) -> List[List[float]]:
    e1 = _safe_float(material.get("E1_GPa"), 102.0) * 1000.0
    e2 = _safe_float(material.get("E2_GPa"), 7.0) * 1000.0
    g12 = _safe_float(material.get("G12_GPa"), 3.35) * 1000.0
    nu12 = _safe_float(material.get("nu12"), 0.16)
    nu21 = nu12 * e2 / max(e1, 1e-9)
    denom = max(1.0 - nu12 * nu21, 1e-9)
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

    a22 = abs(a[1][1])
    b23_raw = abs(b[1][2])
    d12 = abs(d[0][1])
    d22 = abs(d[1][1])
    d33 = abs(d[2][2])
    # 对称铺层 B 项接近零时，使用弱耦合等效量保证符号公式数值稳定。
    b23 = max(b23_raw, 1e-3 * math.sqrt(max(a22 * d33, 1e-9)))
    return {
        "A": a,
        "B": b,
        "D": d,
        "A22": a22,
        "B23": b23,
        "D12": d12,
        "D22": d22,
        "D33": d33,
        "B23_raw": b23_raw,
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
    length = max(_safe_float(geometry.get("length_mm"), 500.0), 1e-9)
    radius = max(_safe_float(geometry.get("radius_mm"), 100.0), 1e-9)
    thickness = max(_safe_float(geometry.get("thickness_mm"), 10.0), 1e-9)
    a = np.array(stiffness.get("A", []), dtype=float)
    b = np.array(stiffness.get("B", []), dtype=float)
    d = np.array(stiffness.get("D", []), dtype=float)
    if a.shape != (3, 3) or b.shape != (3, 3) or d.shape != (3, 3):
        raise ValueError("ASME RD-1172 Q 计算缺少 3x3 A/B/D 刚度矩阵")

    abd = np.vstack((np.hstack((a, b)), np.hstack((b, d))))
    try:
        inverse_abd = np.linalg.inv(abd)
    except np.linalg.LinAlgError as exc:
        raise ValueError("ASME RD-1172 Q 计算的 ABD 刚度矩阵不可逆") from exc

    eps = 1e-12
    bending_aa = max(abs(float(inverse_abd[3][3])), eps)
    bending_hh = max(abs(float(inverse_abd[4][4])), eps)
    coupling = float(inverse_abd[4][3])
    vx = -coupling / bending_aa
    vy = -coupling / bending_hh
    eaf = 12.0 / (thickness ** 3 * bending_aa)
    ehf = 12.0 / (thickness ** 3 * bending_hh)

    a12 = float(a[0][1])
    eat_denom = max(abs(a12 * thickness), eps)
    eat = (float(a[0][0]) * float(a[1][1]) - a12 ** 2) / eat_denom
    vxy = max(1.0 - vx * vy, eps)
    eaf = max(eaf, eps)
    ehf = max(ehf, eps)
    eat = max(eat, eps)

    zp = ehf ** 1.5 * eat ** 0.5 * vxy ** 0.5 * (length ** 2 / (radius * thickness)) / eaf ** 2
    gamma_d = 0.9 if zp > 100.0 else max(1.0 - 0.001 * zp, eps)
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
    return round(max(float(q_value), 0.0), 6)


def estimate_linear_buckling_feature_q(
    geometry: Dict[str, Any],
    stiffness: Dict[str, Any],
    material: Dict[str, Any],
    boundary_conditions: Dict[str, Any] | None = None,
) -> float:
    """返回 PBIPF 当前采用的线性屈曲压力 Q，单位 MPa。"""
    return estimate_asme_rd1172_linear_buckling_q(geometry, stiffness, material, boundary_conditions)


def estimate_shell_mass_kg(geometry: Dict[str, Any], material: Dict[str, Any]) -> float:
    length_m = _safe_float(geometry.get("length_mm"), 500.0) / 1000.0
    radius_m = _safe_float(geometry.get("radius_mm"), 100.0) / 1000.0
    thickness_m = _safe_float(geometry.get("thickness_mm"), 10.0) / 1000.0
    density = _safe_float(material.get("density_kg_per_m3"), 1550.0)
    volume = 2.0 * math.pi * radius_m * length_m * thickness_m
    return round(max(volume * density, 0.0), 6)


def estimate_areal_density_kg_per_m2(geometry: Dict[str, Any], material: Dict[str, Any]) -> float:
    length_m = max(_safe_float(geometry.get("length_mm"), 500.0) / 1000.0, 1e-9)
    radius_m = max(_safe_float(geometry.get("radius_mm"), 100.0) / 1000.0, 1e-9)
    area = 2.0 * math.pi * radius_m * length_m
    return round(estimate_shell_mass_kg(geometry, material) / area, 6)


def describe_geometry_text(hull_type: str, geometry: Dict[str, Any], layup: Dict[str, Any] | None = None) -> str:
    _ = resolve_hull_type(hull_type)
    return (
        f"L={_safe_float(geometry.get('length_mm')):.1f}mm, "
        f"R={_safe_float(geometry.get('radius_mm')):.1f}mm, "
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
    radius = max(_safe_float(geometry.get("radius_mm"), 100.0), 1.0)
    thickness = max(_safe_float(geometry.get("thickness_mm"), 10.0), 0.5)
    inner_radius = max(radius - thickness, 1.0)
    if inner_radius >= radius:
        inner_radius = max(radius * 0.85, radius - 0.5)

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

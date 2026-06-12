"""几何与模态可视化辅助函数。"""

from __future__ import annotations

import io
import json
from pathlib import Path
from typing import Dict, List, Tuple

from gui.i18n import DEFAULT_LANGUAGE, text as tr

try:
    import pyvista as pv
except Exception:  # pragma: no cover
    pv = None

from core.pressure_hull_profile import build_pressure_hull_meshes


def _float(value: object, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def _matplotlib_font(language: str):
    try:
        from matplotlib.font_manager import FontProperties
    except Exception:
        return None
    for font_path in [
        Path("C:/Windows/Fonts/NotoSansSC-VF.ttf"),
        Path("C:/Windows/Fonts/msyh.ttc"),
        Path("C:/Windows/Fonts/simhei.ttf"),
        Path("C:/Windows/Fonts/simsun.ttc"),
    ]:
        if font_path.exists():
            return FontProperties(fname=str(font_path))
    return None


def _text_props(language: str) -> dict:
    font = _matplotlib_font(language)
    return {"fontproperties": font} if font is not None else {}


def build_candidate_scene(candidate: Dict) -> Tuple[list[tuple[object, Dict]], str] | None:
    if pv is None:
        return None
    geometry = dict(candidate.get("geometry", {}))
    if not geometry:
        return None

    htype = str(candidate.get("hull_type", "CYLINDRICAL"))
    meshes = build_pressure_hull_meshes(htype, geometry)

    display_name = candidate.get("display_name") or candidate.get("candidate_id") or "Candidate"
    title = (
        f"{display_name} | "
        f"L={float(geometry.get('length_mm', 0.0)):.1f} mm, "
        f"R={float(geometry.get('radius_mm', 0.0)):.1f} mm, "
        f"t={float(geometry.get('thickness_mm', 0.0)):.2f} mm"
    )
    return meshes, str(title)


def load_mode_shape_payload(result: Dict) -> Dict | None:
    visualization_json = result.get("visualization_json")
    if not visualization_json:
        return None
    path = Path(str(visualization_json))
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def mode_shape_payload_status(result: Dict) -> Dict:
    """返回模态云图数据的可用性摘要，供 GUI 做审计展示。"""

    visualization_json = result.get("visualization_json")
    if not visualization_json:
        return {"available": False, "message": "未提供模态数据路径"}
    path = Path(str(visualization_json))
    if not path.exists():
        return {"available": False, "message": f"模态数据文件不存在：{path}"}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"available": False, "message": f"模态数据读取失败：{exc}"}
    points = payload.get("points") or []
    faces = payload.get("faces") or []
    scalars = payload.get("scalars") or []
    if not points or not faces:
        return {
            "available": False,
            "message": f"模态数据不完整：points={len(points)}，faces={len(faces)}",
        }
    return {
        "available": True,
        "message": f"模态数据可用：points={len(points)}，faces={len(faces)}，scalars={len(scalars)}",
        "points": len(points),
        "faces": len(faces),
        "scalars": len(scalars),
        "path": str(path),
    }


def build_mode_shape_scene(result: Dict) -> Tuple[object, str | None, str] | None:
    if pv is None:
        return None
    payload = load_mode_shape_payload(result)
    if not payload:
        return None

    points = payload.get("points", [])
    faces = payload.get("faces", [])
    scalars = payload.get("scalars", [])
    if not points or not faces:
        return None

    flattened_faces: List[int] = []
    for face in faces:
        flattened_faces.extend(int(value) for value in face)

    mesh = pv.PolyData(points, flattened_faces)
    scalar_name = payload.get("scalar_name", "ModeMagnitude") if scalars and len(scalars) == len(points) else None
    if scalar_name is not None:
        mesh.point_data[scalar_name] = scalars
    title = payload.get("title") or result.get("candidate_id") or "First Buckling Mode"
    return mesh, scalar_name, str(title)


def render_candidate_png_bytes(
    candidate: Dict,
    width: int = 900,
    height: int = 520,
    language: str = DEFAULT_LANGUAGE,
    theme: str = "dark",
    show_annotations: bool = False,
) -> bytes | None:
    """生成候选几何的离线工程剖面图，供无 OpenGL 或离线审计环境使用。"""

    geometry = dict(candidate.get("geometry") or {})
    if not geometry:
        return None
    length = _float(geometry.get("length_mm"))
    radius = _float(geometry.get("radius_mm"))
    thickness = _float(geometry.get("thickness_mm"))
    if length <= 0.0 or radius <= 0.0 or thickness <= 0.0:
        return None

    try:
        import numpy as np
        from matplotlib.backends.backend_agg import FigureCanvasAgg
        from matplotlib.figure import Figure
    except Exception:
        np = None
    if np is not None:
        try:
            dpi = 100
            dark = theme != "light"
            bg = "#101821" if dark else "#f8fbff"
            panel = bg
            text_color = "#dbe4ef" if dark else "#172033"
            muted = "#94a3b8" if dark else "#475569"
            edge = "#38bdf8" if dark else "#1d4ed8"
            figure = Figure(figsize=(width / dpi, height / dpi), dpi=dpi, facecolor=bg)
            canvas = FigureCanvasAgg(figure)
            axis = figure.add_subplot(111, projection="3d", facecolor=panel)
            text_props = _text_props(language)
            theta = np.linspace(0, 2 * np.pi, 96)
            x_values = np.linspace(-length / 2.0, length / 2.0, 36)
            theta_grid, x_grid = np.meshgrid(theta, x_values)
            outer_y = radius * np.cos(theta_grid)
            outer_z = radius * np.sin(theta_grid)
            inner_radius = max(radius - thickness, radius * 0.82)
            inner_y = inner_radius * np.cos(theta_grid)
            inner_z = inner_radius * np.sin(theta_grid)
            axis.plot_surface(x_grid, outer_y, outer_z, color="#2563eb", alpha=0.72, linewidth=0, shade=True)
            axis.plot_surface(x_grid, inner_y, inner_z, color="#0f172a" if dark else "#dbeafe", alpha=0.18, linewidth=0, shade=True)
            for x in (-length / 2.0, length / 2.0):
                axis.plot(np.full_like(theta, x), radius * np.cos(theta), radius * np.sin(theta), color=edge, linewidth=1.5)
                axis.plot(
                    np.full_like(theta, x),
                    inner_radius * np.cos(theta),
                    inner_radius * np.sin(theta),
                    color="#60a5fa" if dark else "#2563eb",
                    linewidth=1.0,
                    alpha=0.78,
                )
            axis.plot([-length / 2.0, length / 2.0], [radius, radius], [0, 0], color=edge, linewidth=1.0, alpha=0.82)
            axis.plot([-length / 2.0, length / 2.0], [-radius, -radius], [0, 0], color=edge, linewidth=1.0, alpha=0.82)
            axis.set_position([0.025, 0.035, 0.95, 0.93])
            figure.subplots_adjust(left=0.02, right=0.98, bottom=0.025, top=0.975)
            try:
                axis.set_proj_type("ortho")
            except Exception:
                pass
            try:
                axis.set_box_aspect((max(length, 1.0), max(radius * 2.0, 1.0), max(radius * 2.0, 1.0)), zoom=1.16)
            except TypeError:
                axis.set_box_aspect((max(length, 1.0), max(radius * 2.0, 1.0), max(radius * 2.0, 1.0)))
            radial_limit = radius * 1.12
            axial_limit = length * 0.59
            axis.set_xlim(-axial_limit, axial_limit)
            axis.set_ylim(-radial_limit, radial_limit)
            axis.set_zlim(-radial_limit, radial_limit)
            axis.view_init(elev=18, azim=-56)
            axis.set_axis_off()
            if show_annotations:
                axis.set_position([0.02, 0.02, 0.96, 0.9])
                display_name = candidate.get("display_name") or candidate.get("candidate_id") or tr(
                    "render.candidate_fallback", language=language
                )
                material = (candidate.get("material_system") or {}).get("name") or "-"
                alpha = _float(geometry.get("alpha_deg"))
                beta = _float(geometry.get("beta_deg"))
                title = tr(
                    "render.candidate_section",
                    language=language,
                    name=display_name,
                    length=length,
                    radius=radius,
                    thickness=thickness,
                )
                subtitle = tr(
                    "render.material_layup",
                    language=language,
                    material=material,
                    alpha=alpha,
                    beta=beta,
                )
                figure.text(0.035, 0.94, title, color=text_color, fontsize=10, weight="bold", **text_props)
                figure.text(0.035, 0.885, subtitle, color=muted, fontsize=8, **text_props)
            buffer = io.BytesIO()
            canvas.print_png(buffer)
            return buffer.getvalue()
        except Exception:
            pass

    try:
        from matplotlib.backends.backend_agg import FigureCanvasAgg
        from matplotlib.figure import Figure
        from matplotlib.patches import Rectangle
    except Exception:
        return None

    dpi = 100
    figure = Figure(figsize=(width / dpi, height / dpi), dpi=dpi, facecolor="white")
    canvas = FigureCanvasAgg(figure)
    axis = figure.add_subplot(111)
    text_props = _text_props(language)

    inner_radius = max(radius - thickness, 0.0)
    display_name = candidate.get("display_name") or candidate.get("candidate_id") or tr(
        "render.candidate_fallback", language=language
    )
    material = (candidate.get("material_system") or {}).get("name") or "-"
    alpha = _float(geometry.get("alpha_deg"))
    beta = _float(geometry.get("beta_deg"))

    axis.add_patch(Rectangle((0, inner_radius), length, thickness, facecolor="#2563eb", alpha=0.72, edgecolor="#1e3a8a"))
    axis.add_patch(
        Rectangle((0, -radius), length, thickness, facecolor="#2563eb", alpha=0.72, edgecolor="#1e3a8a")
    )
    axis.add_patch(
        Rectangle((0, -inner_radius), length, inner_radius * 2.0, facecolor="#f8fafc", edgecolor="#cbd5e1")
    )
    axis.plot([0, length], [radius, radius], color="#0f172a", linewidth=1.2)
    axis.plot([0, length], [-radius, -radius], color="#0f172a", linewidth=1.2)
    axis.plot([0, length], [inner_radius, inner_radius], color="#64748b", linestyle="--", linewidth=0.9)
    axis.plot([0, length], [-inner_radius, -inner_radius], color="#64748b", linestyle="--", linewidth=0.9)
    axis.plot([0, 0], [-radius, radius], color="#0f172a", linewidth=1.0)
    axis.plot([length, length], [-radius, radius], color="#0f172a", linewidth=1.0)
    axis.annotate(
        tr("render.thickness", language=language, thickness=thickness),
        xy=(length * 0.52, radius - thickness / 2.0),
        xytext=(length * 0.52, radius + max(radius * 0.11, thickness * 3.0)),
        arrowprops={"arrowstyle": "->", "color": "#334155", "linewidth": 1.0},
        ha="center",
        color="#334155",
        fontsize=9,
        **text_props,
    )

    title = tr(
        "render.candidate_section",
        language=language,
        name=display_name,
        length=length,
        radius=radius,
        thickness=thickness,
    )
    subtitle = tr(
        "render.material_layup",
        language=language,
        material=material,
        alpha=alpha,
        beta=beta,
    )
    axis.set_title(f"{title}\n{subtitle}", fontsize=11, color="#111827", **text_props)
    axis.set_xlabel(tr("render.x_axis", language=language), **text_props)
    axis.set_ylabel(tr("render.y_axis", language=language), **text_props)
    axis.set_aspect("equal", adjustable="box")
    margin_x = max(length * 0.05, 20.0)
    margin_y = max(radius * 0.18, thickness * 6.0, 20.0)
    axis.set_xlim(-margin_x, length + margin_x)
    axis.set_ylim(-radius - margin_y, radius + margin_y)
    axis.grid(color="#e2e8f0", linewidth=0.8)
    figure.tight_layout()

    buffer = io.BytesIO()
    canvas.print_png(buffer)
    return buffer.getvalue()


def _face_indexes(face: object) -> list[int]:
    try:
        values = [int(item) for item in face]
    except Exception:
        return []
    if not values:
        return []
    count = values[0]
    indexes = values[1:]
    if count == len(indexes):
        return indexes
    return values


def render_mode_shape_png_bytes(
    result: Dict,
    width: int = 900,
    height: int = 560,
    max_faces: int = 1800,
    language: str = DEFAULT_LANGUAGE,
    theme: str = "dark",
) -> bytes | None:
    """生成一阶模态云图离线 PNG，供无 OpenGL 或离线审计环境使用。"""

    payload = load_mode_shape_payload(result)
    if not payload:
        return None
    points = payload.get("points") or []
    faces = payload.get("faces") or []
    scalars = payload.get("scalars") or []
    if not points or not faces:
        return None

    try:
        import numpy as np
        from matplotlib import colormaps, colors
        from matplotlib.backends.backend_agg import FigureCanvasAgg
        from matplotlib.figure import Figure
        from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    except Exception:
        return None

    point_array = np.asarray(points, dtype=float)
    if point_array.ndim != 2 or point_array.shape[1] != 3:
        return None
    scalar_array = np.asarray(scalars, dtype=float) if len(scalars) == len(points) else np.zeros(len(points))
    if len(scalar_array) != len(points):
        scalar_array = np.zeros(len(points))

    face_indexes = [_face_indexes(face) for face in faces]
    face_indexes = [indexes for indexes in face_indexes if len(indexes) >= 3 and max(indexes) < len(point_array)]
    if not face_indexes:
        return None
    if len(face_indexes) > max_faces:
        stride = max(1, len(face_indexes) // max_faces)
        face_indexes = face_indexes[::stride]

    polygons = [point_array[indexes] for indexes in face_indexes]
    face_values = np.asarray([float(np.mean(scalar_array[indexes])) for indexes in face_indexes])
    if np.nanmax(face_values) - np.nanmin(face_values) < 1e-12:
        norm = colors.Normalize(vmin=0.0, vmax=1.0)
    else:
        norm = colors.Normalize(vmin=float(np.nanmin(face_values)), vmax=float(np.nanmax(face_values)))
    cmap = colormaps.get_cmap("viridis")

    dpi = 100
    dark = theme != "light"
    bg = "#101821" if dark else "#f8fbff"
    text_color = "#dbe4ef" if dark else "#172033"
    edge_color = (0.22, 0.74, 0.97, 0.16) if dark else (0.15, 0.30, 0.55, 0.18)
    figure = Figure(figsize=(width / dpi, height / dpi), dpi=dpi, facecolor=bg)
    canvas = FigureCanvasAgg(figure)
    axis = figure.add_subplot(111, projection="3d", facecolor=bg)
    text_props = _text_props(language)
    collection = Poly3DCollection(
        polygons,
        facecolors=cmap(norm(face_values)),
        linewidths=0.08,
        edgecolors=edge_color,
        alpha=0.96,
    )
    axis.add_collection3d(collection)
    mins = point_array.min(axis=0)
    maxs = point_array.max(axis=0)
    centers = (mins + maxs) / 2.0
    span = float(max(maxs - mins))
    if span <= 0.0:
        span = 1.0
    half = span / 2.0
    axis.set_xlim(centers[0] - half, centers[0] + half)
    axis.set_ylim(centers[1] - half, centers[1] + half)
    axis.set_zlim(centers[2] - half, centers[2] + half)
    try:
        axis.set_proj_type("ortho")
    except Exception:
        pass
    try:
        axis.set_box_aspect((1, 1, 1), zoom=1.08)
    except TypeError:
        axis.set_box_aspect((1, 1, 1))
    axis.view_init(elev=20, azim=-58)
    axis.set_axis_off()
    axis.set_position([0.02, 0.03, 0.83, 0.94])
    scalar_name = tr("render.mode_scalar", language=language)
    from matplotlib.cm import ScalarMappable

    mappable = ScalarMappable(norm=norm, cmap=cmap)
    mappable.set_array(face_values)
    colorbar = figure.colorbar(mappable, ax=axis, shrink=0.72, pad=0.02, fraction=0.048)
    colorbar.set_label(str(scalar_name), color=text_color, **text_props)
    colorbar.ax.tick_params(colors=text_color, labelsize=8, length=2)
    colorbar.outline.set_edgecolor(text_color)
    figure.subplots_adjust(left=0.0, right=0.97, bottom=0.0, top=1.0)

    buffer = io.BytesIO()
    canvas.print_png(buffer)
    return buffer.getvalue()

"""几何与模态可视化辅助函数。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Tuple

try:
    import pyvista as pv
except Exception:  # pragma: no cover
    pv = None

from core.pressure_hull_profile import build_pressure_hull_meshes


def build_candidate_scene(candidate: Dict) -> Tuple[list[tuple[object, Dict]], str] | None:
    if pv is None:
        return None
    geometry = dict(candidate.get("geometry", {}))
    if not geometry:
        return None

    htype = str(candidate.get("hull_type", "CYLINDRICAL"))
    meshes = build_pressure_hull_meshes(htype, geometry)

    display_name = candidate.get("display_name") or candidate.get("candidate_id") or "候选方案"
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

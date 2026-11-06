# -*- coding: utf-8 -*-
"""ABAQUS 运行时耐压壳建模与线性外压屈曲结果提取脚本。"""

from __future__ import print_function

import json
import hashlib
import math
import os
import re
import traceback

try:
    text_type = unicode
    binary_type = str
except NameError:
    text_type = str
    binary_type = bytes


def safe_float(value, default):
    try:
        return float(value)
    except Exception:
        return default


def require_mapping(value, field):
    if not isinstance(value, dict):
        raise ValueError("missing or invalid FEM field: %s" % field)
    return value


def require_float(value, field, positive=True):
    if isinstance(value, bool):
        raise ValueError("missing or invalid FEM field: %s" % field)
    try:
        number = float(value)
    except Exception:
        raise ValueError("missing or invalid FEM field: %s" % field)
    if math.isnan(number) or math.isinf(number) or (positive and number <= 0.0):
        raise ValueError("missing or invalid FEM field: %s" % field)
    return number


def ensure_parent(path):
    parent = os.path.dirname(os.path.abspath(path))
    if parent and not os.path.exists(parent):
        os.makedirs(parent)


def write_json(path, payload):
    ensure_parent(path)
    safe_payload = safe_json_value(payload)
    text = json.dumps(safe_payload, ensure_ascii=True, indent=2)
    with open(path, "w") as handle:
        handle.write(text)


def safe_json_value(value):
    if isinstance(value, dict):
        return {safe_json_value(key): safe_json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [safe_json_value(item) for item in value]
    if value is None or isinstance(value, (int, float, bool)):
        return value
    if isinstance(value, text_type):
        return value
    if isinstance(value, binary_type):
        for encoding in ("utf-8", "mbcs", "gbk", "latin-1"):
            try:
                return value.decode(encoding, "replace")
            except Exception:
                pass
    return str(value)


def boundary_implementation(boundary_type):
    if boundary_type == "END_SIMPLY_SUPPORTED":
        return "两端边线径向约束，其中一端附加轴向约束以消除刚体位移"
    if boundary_type == "FLANGE_CONSTRAINED":
        return "金属法兰未显式建模，两端边线采用 Encastre 等效约束"
    if boundary_type == "END_CLAMPED":
        return "两端边线采用 Encastre 固支约束"
    return None


def read_json(path):
    with open(path, "r") as handle:
        return json.load(handle)


def file_sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        while True:
            block = handle.read(1024 * 1024)
            if not block:
                break
            digest.update(block)
    return digest.hexdigest()


def runtime_script_sha256(candidate_id=None):
    """在 Abaqus noGUI 没有 __file__ 时仍从候选运行目录取得脚本指纹。"""
    paths = []
    if candidate_id:
        paths.append(os.path.join(os.getcwd(), "build_%s.py" % candidate_id))
    try:
        paths.append(os.path.abspath(__file__))
    except NameError:
        pass
    for path in paths:
        if os.path.exists(path):
            return file_sha256(path)
    return None


def result_shell(candidate, result_json, status, error_type=None, error_log=None, extra=None):
    candidate_id = str(candidate.get("candidate_id") or "UNKNOWN")
    boundary_type = str((candidate.get("boundary_conditions") or {}).get("type") or "")
    payload = {
        "candidate_id": candidate_id,
        "design_revision_id": candidate.get("design_revision_id"),
        "parent_design_revision_id": candidate.get("parent_design_revision_id"),
        "status": status,
        "retry_count": 0,
        "ultimate_pressure_MPa": None,
        "failure_pressure_MPa": None,
        "linear_buckling_pressure_MPa": None,
        "first_mode_eigenvalue": None,
        "failure_mode": None,
        "max_displacement_mm": None,
        "weight_kg_per_m2": None,
        "verdict": None,
        "abaqus_odb": None,
        "abaqus_inp": None,
        "visualization_json": None,
        "artifact_dir": os.getcwd(),
        "error_type": error_type,
        "error_log": error_log,
        "mode_eigenvalues": None,
        "runtime_script_sha256": runtime_script_sha256(candidate_id),
        "boundary_condition_type": boundary_type or None,
        "boundary_implementation": boundary_implementation(boundary_type),
    }
    if extra:
        payload.update(extra)
    if status != "success":
        payload["verdict"] = None
    write_json(result_json, payload)
    return payload


def layup_angles(candidate):
    layup = require_mapping(candidate.get("layup"), "layup")
    angles = layup.get("angles_deg")
    if not isinstance(angles, list) or not angles:
        raise ValueError("missing or invalid FEM field: layup.angles_deg")
    ply_count = layup.get("ply_count")
    if isinstance(ply_count, bool) or not isinstance(ply_count, int) or ply_count != len(angles):
        raise ValueError("missing or invalid FEM field: layup.ply_count")
    values = [require_float(value, "layup.angles_deg[%d]" % index, positive=False) for index, value in enumerate(angles)]
    if any(abs(value) > 90.0 for value in values):
        raise ValueError("missing or invalid FEM field: layup.angles_deg")
    return values


def sequence_is_balanced(sequence):
    values = [round(float(angle), 6) for angle in sequence]
    magnitudes = set(abs(angle) for angle in values if abs(angle) not in (0.0, 90.0))
    return all(values.count(magnitude) == values.count(-magnitude) for magnitude in magnitudes)


def sequence_is_symmetric(sequence):
    values = [round(float(angle), 6) for angle in sequence]
    return values == list(reversed(values))


def material_payload(candidate):
    material = require_mapping(candidate.get("material_system"), "material_system")
    if not str(material.get("name") or "").strip() or not str(material.get("material_key") or "").strip():
        raise ValueError("missing or invalid FEM field: material_system.name/material_key")
    return {
        "name": str(material["name"]),
        "density": require_float(material.get("density_kg_per_m3"), "material_system.density_kg_per_m3"),
        "E1": require_float(material.get("E1_GPa"), "material_system.E1_GPa") * 1000.0,
        "E2": require_float(material.get("E2_GPa"), "material_system.E2_GPa") * 1000.0,
        "G12": require_float(material.get("G12_GPa"), "material_system.G12_GPa") * 1000.0,
        "nu12": require_float(material.get("nu12"), "material_system.nu12"),
        "Xt": require_float(material.get("Xt_MPa"), "material_system.Xt_MPa"),
        "Xc": require_float(material.get("Xc_MPa"), "material_system.Xc_MPa"),
        "Yt": require_float(material.get("Yt_MPa"), "material_system.Yt_MPa"),
        "Yc": require_float(material.get("Yc_MPa"), "material_system.Yc_MPa"),
        "S": require_float(material.get("S_MPa"), "material_system.S_MPa"),
    }


def validate_runtime_candidate(candidate):
    """在导入 Abaqus API 前拒绝不完整或不可追溯的模型输入。"""
    revision = str(candidate.get("design_revision_id") or "")
    if not re.match(r"^DR_[a-f0-9]{64}$", revision):
        raise ValueError("missing or invalid FEM field: design_revision_id")
    if str(candidate.get("hull_type") or "") != "CYLINDRICAL":
        raise ValueError("missing or invalid FEM field: hull_type")
    geometry = require_mapping(candidate.get("geometry"), "geometry")
    length = require_float(geometry.get("length_mm"), "geometry.length_mm")
    radius = require_float(geometry.get("radius_mm"), "geometry.radius_mm")
    thickness = require_float(geometry.get("thickness_mm"), "geometry.thickness_mm")
    require_float(geometry.get("alpha_deg"), "geometry.alpha_deg")
    require_float(geometry.get("beta_deg"), "geometry.beta_deg")
    require_float(geometry.get("imperfection_ratio"), "geometry.imperfection_ratio")
    material = material_payload(candidate)
    angles = layup_angles(candidate)
    layup = require_mapping(candidate.get("layup"), "layup")
    ply_thickness = require_float(layup.get("ply_thickness_mm"), "layup.ply_thickness_mm")
    if abs(ply_thickness * len(angles) - thickness) > 1.0e-5:
        raise ValueError("missing or invalid FEM field: layup.ply_thickness_mm")
    if layup.get("balanced") is not sequence_is_balanced(angles):
        raise ValueError("missing or invalid FEM field: layup.balanced")
    if layup.get("symmetric") is not sequence_is_symmetric(angles):
        raise ValueError("missing or invalid FEM field: layup.symmetric")
    target_pressure = require_float(
        require_mapping(candidate.get("design_targets"), "design_targets").get("ultimate_pressure_min_MPa"),
        "design_targets.ultimate_pressure_min_MPa",
    )
    load_conditions = require_mapping(candidate.get("load_conditions"), "load_conditions")
    if str(load_conditions.get("type") or "") != "external_pressure":
        raise ValueError("missing or invalid FEM field: load_conditions.type")
    service_pressure = require_float(
        load_conditions.get("external_pressure_MPa"),
        "load_conditions.external_pressure_MPa",
    )
    if target_pressure + 1.0e-9 < service_pressure:
        raise ValueError("design_targets.ultimate_pressure_min_MPa must not be below service pressure")
    boundary_conditions = require_mapping(candidate.get("boundary_conditions"), "boundary_conditions")
    boundary_type = str(boundary_conditions.get("type") or "")
    if boundary_type not in ("END_CLAMPED", "END_SIMPLY_SUPPORTED", "FLANGE_CONSTRAINED"):
        raise ValueError("missing or invalid FEM field: boundary_conditions.type")
    return {
        "geometry": geometry,
        "material": material,
        "length": length,
        "radius": radius,
        "thickness": thickness,
        "service_pressure": service_pressure,
        "target_pressure": target_pressure,
        "boundary_type": boundary_type,
        "angles": angles,
        "ply_thickness": ply_thickness,
    }


def estimate_areal_density(geometry, material):
    thickness_m = require_float(geometry.get("thickness_mm"), "geometry.thickness_mm") / 1000.0
    density = require_float(material.get("density"), "material_system.density_kg_per_m3")
    return round(thickness_m * density, 6)


def extract_eigenvalue(description):
    text = str(description or "")
    match = re.search(r"=\s*([-+0-9.Ee]+)", text)
    if not match:
        return None
    return safe_float(match.group(1), None)


def first_positive_mode(odb):
    values = []
    step = odb.steps["Step-1"]
    for index in range(1, len(step.frames)):
        frame = step.frames[index]
        value = extract_eigenvalue(frame.description)
        if value is not None:
            values.append(value)
            if value > 0.0:
                return value, values, index
    return None, values, None


def first_positive_eigenvalue(odb):
    value, values, _ = first_positive_mode(odb)
    return value, values


def _dict_values(mapping):
    return [mapping[key] for key in mapping.keys()]


def max_displacement_from_frame(frame, instance=None):
    try:
        field = frame.fieldOutputs["U"]
    except Exception:
        return None
    try:
        if instance is not None:
            field = field.getSubset(region=instance)
    except Exception:
        pass
    max_value = 0.0
    found = False
    for value in field.values:
        data = value.data
        mag = math.sqrt(sum(float(item) * float(item) for item in data[:3]))
        if mag > max_value:
            max_value = mag
        found = True
    if not found:
        return None
    return max_value


def write_mode_shape_json(odb, candidate_id, output_path, frame_index, length_scale):
    step = odb.steps["Step-1"]
    if frame_index is None or frame_index >= len(step.frames):
        return None
    instances = _dict_values(odb.rootAssembly.instances)
    if not instances:
        return None
    instance = instances[0]
    frame = step.frames[frame_index]
    try:
        displacement_field = frame.fieldOutputs["U"].getSubset(region=instance)
    except Exception:
        return None

    displacement_by_label = {}
    scalars_by_label = {}
    max_mag = 0.0
    for value in displacement_field.values:
        data = [float(item) for item in value.data[:3]]
        mag = math.sqrt(sum(item * item for item in data))
        displacement_by_label[int(value.nodeLabel)] = data
        scalars_by_label[int(value.nodeLabel)] = mag
        max_mag = max(max_mag, mag)
    if max_mag <= 0.0:
        return None

    scale = 0.08 * max(length_scale, 1.0) / max_mag
    points = []
    scalars = []
    label_to_index = {}
    for index, node in enumerate(instance.nodes):
        label = int(node.label)
        coord = [float(item) for item in node.coordinates[:3]]
        disp = displacement_by_label.get(label, [0.0, 0.0, 0.0])
        points.append([coord[i] + disp[i] * scale for i in range(3)])
        scalars.append(scalars_by_label.get(label, 0.0) / max_mag)
        label_to_index[label] = index

    faces = []
    for element in instance.elements:
        indexes = []
        for node_label in element.connectivity:
            idx = label_to_index.get(int(node_label))
            if idx is not None:
                indexes.append(idx)
        if len(indexes) >= 3:
            faces.append([len(indexes)] + indexes)
    if not points or not faces:
        return None

    payload = {
        "candidate_id": candidate_id,
        "title": "%s 一阶线性屈曲模态" % candidate_id,
        "points": points,
        "faces": faces,
        "scalars": scalars,
        "scalar_name": "归一化模态位移",
        "mode_index": 1,
        "deformation_scale": scale,
    }
    write_json(output_path, payload)
    return output_path


def keyword_position(model, block_prefix, occurrence=1):
    try:
        model.keywordBlock.synchVersions(storeNodesAndElements=False)
        blocks = model.keywordBlock.sieBlocks
    except Exception:
        return None
    prefix = str(block_prefix).lower()
    found = 0
    for index, block in enumerate(blocks):
        if str(block[:len(block_prefix)]).lower() == prefix:
            found += 1
            if found >= occurrence:
                return index
    return len(blocks)


def insert_keyword(model, before_prefix, text):
    position = keyword_position(model, before_prefix)
    if position is None:
        return False
    try:
        model.keywordBlock.insert(max(position - 1, 0), text)
        return True
    except Exception:
        return False


def postbuckling_reference_pressure(linear_pressure):
    if linear_pressure > 10.0:
        return max(math.floor(linear_pressure / 10.0) * 10.0, 10.0)
    if linear_pressure < 5.0:
        return 5.0
    return 10.0


def imperfection_amplitude_mm(geometry):
    radius = require_float(geometry.get("radius_mm"), "geometry.radius_mm")
    thickness = require_float(geometry.get("thickness_mm"), "geometry.thickness_mm")
    ratio = require_float(geometry.get("imperfection_ratio"), "geometry.imperfection_ratio")
    return max(ratio * (radius + 0.5 * thickness), 1.0e-6)


def enable_field_degradation(model, material_name, material):
    try:
        base = (material["E1"], material["E2"], material["nu12"], material["G12"], material["G12"], material["G12"] * 0.8)
        weak_matrix = (material["E1"], material["E2"] * 0.1, 0.0, material["G12"], material["G12"], material["G12"] * 0.08)
        weak_shear = (material["E1"], material["E2"] * 0.1, 0.0, material["G12"] * 0.1, material["G12"] * 0.1, material["G12"] * 0.08)
        weak_fiber = (material["E1"] * 0.14, material["E2"] * 0.1, 0.0, material["G12"] * 0.1, material["G12"] * 0.1, material["G12"] * 0.08)
        model.materials[material_name].elastic.setValues(
            dependencies=3,
            table=(
                base + (0.0, 0.0, 0.0),
                weak_matrix + (1.0, 0.0, 0.0),
                weak_shear + (0.0, 1.0, 0.0),
                weak_shear + (1.0, 1.0, 0.0),
                weak_fiber + (0.0, 0.0, 1.0),
                weak_fiber + (1.0, 0.0, 1.0),
                weak_fiber + (0.0, 1.0, 1.0),
                weak_fiber + (1.0, 1.0, 1.0),
            ),
        )
        model.materials[material_name].Depvar(n=3)
        model.materials[material_name].UserDefinedField()
        return True
    except Exception:
        return False


def extract_lpf_history(session, odb):
    pairs = []
    try:
        xy_data = session.XYDataFromHistory(
            name="LPF Whole Model",
            odb=odb,
            outputVariableName="Load proportionality factor: LPF for Whole Model",
            steps=("Step-1", ),
        )
        pairs = [(float(item[0]), float(item[1])) for item in xy_data]
    except Exception:
        pairs = []

    if pairs:
        return pairs

    try:
        step = odb.steps["Step-1"]
        for region in _dict_values(step.historyRegions):
            for output in _dict_values(region.historyOutputs):
                label = (str(getattr(output, "name", "")) + " " + str(getattr(output, "description", ""))).lower()
                if "lpf" not in label and "load proportionality" not in label:
                    continue
                return [(float(item[0]), float(item[1])) for item in output.data]
    except Exception:
        return []
    return []


def odb_job_status(odb):
    """读取 ODB 记录的真实作业终止状态。"""
    try:
        return str(odb.diagnosticData.jobStatus)
    except Exception:
        return "JOB_STATUS_UNKNOWN"


def classify_riks_limit_point(lpf_pairs, job_status, minimum_post_peak_points=3, minimum_drop_ratio=0.005):
    """只有成功作业且存在明确后峰下降时才确认 Riks 极限点。"""
    normalized = [(float(item[0]), float(item[1])) for item in (lpf_pairs or [])]
    successful = str(job_status) == "JOB_STATUS_COMPLETED_SUCCESSFULLY"
    if not normalized:
        return {
            "job_completed_successfully": successful,
            "limit_point_observed": False,
            "limit_point_confirmed": False,
            "increment_count": 0,
            "max_index": None,
            "post_peak_drop_ratio": None,
        }

    max_index = max(range(len(normalized)), key=lambda index: normalized[index][1])
    max_lpf = normalized[max_index][1]
    post_peak = normalized[max_index + 1:]
    drop_ratio = 0.0
    if max_lpf > 0.0 and post_peak:
        drop_ratio = max(0.0, (max_lpf - min(item[1] for item in post_peak)) / max_lpf)
    observed = len(post_peak) >= int(minimum_post_peak_points) and drop_ratio >= float(minimum_drop_ratio)
    return {
        "job_completed_successfully": successful,
        "limit_point_observed": observed,
        "limit_point_confirmed": successful and observed,
        "increment_count": len(normalized),
        "max_index": max_index,
        "post_peak_drop_ratio": drop_ratio,
    }


def hashin_failure_indices(stress, material):
    """按二维 Hashin 1980 平面应力形式计算铺层失效起始指数。"""
    sigma_1 = float(stress[0])
    sigma_2 = float(stress[1])
    tau_12 = float(stress[3])
    xt = require_float(material.get("Xt"), "material_system.Xt_MPa")
    xc = require_float(material.get("Xc"), "material_system.Xc_MPa")
    yt = require_float(material.get("Yt"), "material_system.Yt_MPa")
    yc = require_float(material.get("Yc"), "material_system.Yc_MPa")
    shear = require_float(material.get("S"), "material_system.S_MPa")
    indices = {}
    shear_term = (tau_12 / shear) ** 2
    if sigma_1 >= 0.0:
        indices["fiber_tension"] = (sigma_1 / xt) ** 2 + shear_term
    else:
        indices["fiber_compression"] = (sigma_1 / xc) ** 2
    if sigma_2 >= 0.0:
        indices["matrix_tension"] = (sigma_2 / yt) ** 2 + shear_term
    else:
        indices["matrix_compression"] = (
            (sigma_2 / (2.0 * shear)) ** 2
            + ((yc / (2.0 * shear)) ** 2 - 1.0) * (sigma_2 / yc)
            + shear_term
        )
    return indices


def max_hashin_index_from_frame(frame, material):
    """返回一个收敛帧中所有单元、铺层和积分点的最大 Hashin 指数。"""
    try:
        values = frame.fieldOutputs["S"].values
    except Exception:
        return None
    maximum = None
    for value in values:
        data = value.data
        if len(data) < 4:
            continue
        indices = hashin_failure_indices(data, material)
        mode, failure_index = max(indices.items(), key=lambda item: item[1])
        if maximum is None or failure_index > maximum["failure_index"]:
            section_point = getattr(value, "sectionPoint", None)
            maximum = {
                "failure_index": float(failure_index),
                "failure_mode": mode,
                "element_label": int(getattr(value, "elementLabel", 0) or 0),
                "section_point": str(getattr(section_point, "description", "") or ""),
                "stress_MPa": [float(item) for item in data[:4]],
            }
    return maximum


def riks_first_ply_evidence(step, lpf_pairs, reference_pressure, material):
    """从已收敛的单调加载包络提取首层失效和目标压力证据。"""
    pairs = [(float(item[0]), float(item[1])) for item in (lpf_pairs or [])]
    evidence = {
        "first_ply_failure_criterion": "Hashin_2D_1980_plane_stress",
        "first_ply_failure_pressure_MPa": None,
        "first_ply_failure_index": None,
        "first_ply_failure_mode": None,
        "first_ply_failure_element_label": None,
        "first_ply_failure_section_point": None,
        "first_ply_failure_pressure_lower_bound_MPa": None,
        "first_ply_failure_pressure_upper_bound_MPa": None,
    }
    if not pairs:
        return evidence

    maximum_pressure_seen = -1.0
    previous_pressure = None
    frames = list(getattr(step, "frames", []) or [])
    for frame in frames:
        frame_value = float(getattr(frame, "frameValue", 0.0))
        _, lpf = min(pairs, key=lambda item: abs(item[0] - frame_value))
        pressure = float(lpf) * float(reference_pressure)
        if pressure <= maximum_pressure_seen + 1.0e-9:
            continue
        maximum_pressure_seen = pressure
        maximum = max_hashin_index_from_frame(frame, material)
        if maximum is None:
            continue
        if evidence["first_ply_failure_pressure_upper_bound_MPa"] is None and maximum["failure_index"] >= 1.0:
            evidence.update({
                "first_ply_failure_pressure_lower_bound_MPa": (
                    round(previous_pressure, 6) if previous_pressure is not None else None
                ),
                "first_ply_failure_pressure_upper_bound_MPa": round(pressure, 6),
                "first_ply_failure_index": round(maximum["failure_index"], 8),
                "first_ply_failure_mode": maximum["failure_mode"],
                "first_ply_failure_element_label": maximum["element_label"],
                "first_ply_failure_section_point": maximum["section_point"],
            })
        if evidence["first_ply_failure_pressure_upper_bound_MPa"] is not None:
            break
        previous_pressure = pressure
    return evidence


def exact_load_evidence(odb, checked_pressure, material, linear_pressure):
    """从精确压力非线性作业提取收敛、屈曲和首层失效判定。"""
    job_status = odb_job_status(odb)
    evidence = {
        "failure_criterion": "Hashin_2D_1980_plane_stress",
        "abaqus_job_status": job_status,
        "pressure_check_status": "solver_failed",
        "pressure_checked_MPa": None,
        "hashin_index_max": None,
        "hashin_failure_mode": None,
        "hashin_element_label": None,
        "hashin_section_point": None,
    }
    try:
        step = odb.steps["Step-1"]
        frame = step.frames[-1]
        completed = job_status == "JOB_STATUS_COMPLETED_SUCCESSFULLY" and float(frame.frameValue) >= 1.0 - 1.0e-6
        maximum = max_hashin_index_from_frame(frame, material)
    except Exception:
        return evidence
    if not completed or maximum is None:
        return evidence
    hashin_passed = maximum["failure_index"] < 1.0
    buckling_passed = float(linear_pressure) > float(checked_pressure)
    evidence.update({
        "pressure_check_status": "passed" if hashin_passed and buckling_passed else "failed",
        "pressure_checked_MPa": round(float(checked_pressure), 6),
        "hashin_index_max": round(maximum["failure_index"], 8),
        "hashin_failure_mode": maximum["failure_mode"],
        "hashin_element_label": maximum["element_label"],
        "hashin_section_point": maximum["section_point"],
    })
    return evidence


def prefixed_load_evidence(evidence, prefix):
    return {prefix + key: value for key, value in evidence.items()}


def service_load_evidence(odb, checked_pressure, material, linear_pressure):
    return prefixed_load_evidence(
        exact_load_evidence(odb, checked_pressure, material, linear_pressure),
        "service_",
    )


def target_load_evidence(odb, checked_pressure, material, linear_pressure):
    return prefixed_load_evidence(
        exact_load_evidence(odb, checked_pressure, material, linear_pressure),
        "target_",
    )


def build_and_run(candidate, result_json, user_subroutine):
    validated = validate_runtime_candidate(candidate)
    geometry = validated["geometry"]
    material = validated["material"]
    length = validated["length"]
    radius = validated["radius"]
    service_pressure = validated["service_pressure"]
    target_pressure = validated["target_pressure"]
    boundary_type = validated["boundary_type"]
    angles = validated["angles"]

    from abaqus import mdb, session
    from abaqusConstants import (
        ANALYSIS,
        CARTESIAN,
        DEFAULT,
        DEFORMABLE_BODY,
        FROM_SECTION,
        GRADIENT,
        MIDDLE_SURFACE,
        OFF,
        ON,
        ODB,
        PERCENTAGE,
        ROTATION_NONE,
        SHELL,
        SIMPSON,
        SINGLE,
        SPECIFY_ORIENT,
        SPECIFY_THICKNESS,
        STANDARD,
        THREE_D,
        UNIFORM,
        AXIS_3,
        LAMINA,
        S4R,
        SYSTEM,
    )
    import mesh
    import regionToolset

    candidate_id = str(candidate.get("candidate_id") or "CPH")
    mesh_size = safe_float((candidate.get("analysis") or {}).get("mesh_size_mm"), max(min(length / 30.0, radius / 5.0), 4.0))
    ply_thickness = validated["ply_thickness"]

    mdb.Model(name="CPH_Model")
    if "Model-1" in mdb.models:
        del mdb.models["Model-1"]
    model = mdb.models["CPH_Model"]
    model.rootAssembly.DatumCsysByDefault(CARTESIAN)

    sketch = model.ConstrainedSketch(name="shell_profile", sheetSize=max(length, radius) * 4.0)
    sketch.ConstructionLine(point1=(0.0, -length), point2=(0.0, length * 2.0))
    sketch.Line(point1=(radius, 0.0), point2=(radius, length))
    part = model.Part(name="CompositeHull", dimensionality=THREE_D, type=DEFORMABLE_BODY)
    part.BaseShellRevolve(sketch=sketch, angle=360.0, flipRevolveDirection=OFF)
    del model.sketches["shell_profile"]
    axial_csys_feature = part.DatumCsysByThreePoints(
        name="AxialMaterialCSYS",
        coordSysType=CARTESIAN,
        origin=(0.0, 0.0, 0.0),
        point1=(0.0, 1.0, 0.0),
        point2=(0.0, 0.0, 1.0),
    )
    axial_material_csys = part.datums[axial_csys_feature.id]

    model.Material(name="Composite")
    model.materials["Composite"].Density(table=((material["density"] * 1.0e-12, ), ))
    model.materials["Composite"].Elastic(
        type=LAMINA,
        table=((material["E1"], material["E2"], material["nu12"], material["G12"], material["G12"], material["G12"] * 0.8), ),
    )
    try:
        model.materials["Composite"].elastic.FailStress(
            table=((material["Xt"], material["Xc"], material["Yt"], material["Yc"], material["S"], 0.0, 0.0), )
        )
    except Exception:
        pass

    layup = part.CompositeLayup(
        name="CompositeLayup-1",
        description="",
        elementType=SHELL,
        offsetType=MIDDLE_SURFACE,
        symmetric=False,
        thicknessAssignment=FROM_SECTION,
    )
    layup.Section(
        preIntegrate=OFF,
        integrationRule=SIMPSON,
        thicknessType=UNIFORM,
        poissonDefinition=DEFAULT,
        temperature=GRADIENT,
        useDensity=ON,
    )
    layup.ReferenceOrientation(
        orientationType=SYSTEM,
        localCsys=axial_material_csys,
        fieldName="",
        additionalRotationType=ROTATION_NONE,
        angle=0.0,
        axis=AXIS_3,
    )
    ply_region = regionToolset.Region(faces=part.faces[:])
    for index, angle in enumerate(angles):
        layup.CompositePly(
            suppressed=False,
            plyName="Ply-%d" % (index + 1),
            region=ply_region,
            material="Composite",
            thicknessType=SPECIFY_THICKNESS,
            thickness=ply_thickness,
            orientationType=SPECIFY_ORIENT,
            orientationValue=angle,
            additionalRotationType=ROTATION_NONE,
            additionalRotationField="",
            axis=AXIS_3,
            angle=0.0,
            numIntPoints=3,
        )

    assembly = model.rootAssembly
    instance = assembly.Instance(name="CompositeHull-1", part=part, dependent=ON)
    model.BuckleStep(name="Step-1", previous="Initial", numEigen=8, vectors=12, maxIterations=300)
    try:
        model.fieldOutputRequests["F-Output-1"].setValues(variables=("S", "E", "U", "RF"))
    except Exception:
        pass

    pressure_region = regionToolset.Region(side1Faces=instance.faces[:])
    model.Pressure(name="ExternalPressure", createStepName="Step-1", region=pressure_region, magnitude=1.0)

    tol = max(mesh_size * 0.25, 1.0)
    end_edges_0 = instance.edges.getByBoundingBox(yMin=-tol, yMax=tol)
    end_edges_1 = instance.edges.getByBoundingBox(yMin=length - tol, yMax=length + tol)
    if boundary_type == "END_SIMPLY_SUPPORTED":
        model.DisplacementBC(
            name="BC-End-0",
            createStepName="Initial",
            region=regionToolset.Region(edges=end_edges_0),
            u1=0.0,
            u3=0.0,
        )
        model.DisplacementBC(
            name="BC-End-1",
            createStepName="Initial",
            region=regionToolset.Region(edges=end_edges_1),
            u1=0.0,
            u2=0.0,
            u3=0.0,
        )
    else:
        model.EncastreBC(name="BC-End-0", createStepName="Initial", region=regionToolset.Region(edges=end_edges_0))
        model.EncastreBC(name="BC-End-1", createStepName="Initial", region=regionToolset.Region(edges=end_edges_1))

    elem_type = mesh.ElemType(elemCode=S4R, elemLibrary=STANDARD)
    part.setElementType(regions=(part.faces[:], ), elemTypes=(elem_type, ))
    part.seedPart(size=mesh_size, deviationFactor=0.1, minSizeFactor=0.1)
    part.generateMesh()
    assembly.regenerate()

    post_model = mdb.Model(name="CPH_Post_Model", objectToCopy=model)
    insert_keyword(model, "*End Step", "*Node File\nU")

    job = mdb.Job(
        name=candidate_id,
        model="CPH_Model",
        description="CSDM_cph pressure hull linear buckling",
        type=ANALYSIS,
        memory=90,
        memoryUnits=PERCENTAGE,
        explicitPrecision=SINGLE,
        nodalOutputPrecision=SINGLE,
        echoPrint=OFF,
        modelPrint=OFF,
        contactPrint=OFF,
        historyPrint=OFF,
        userSubroutine="",
        resultsFormat=ODB,
        multiprocessingMode=DEFAULT,
        numCpus=1,
        numGPUs=0,
    )
    try:
        job.writeInput(consistencyChecking=OFF)
    except Exception:
        pass
    job.submit(consistencyChecking=OFF)
    job.waitForCompletion()

    odb_path = os.path.abspath(candidate_id + ".odb")
    odb = session.openOdb(name=odb_path)
    eigenvalue, eigenvalues, mode_frame_index = first_positive_mode(odb)
    mode_json_path = None
    if eigenvalue is not None:
        mode_json_path = write_mode_shape_json(
            odb,
            candidate_id,
            os.path.abspath(candidate_id + "_mode1.json"),
            mode_frame_index,
            max(length, radius),
        )
    odb.close()
    if eigenvalue is None:
        return result_shell(candidate, result_json, "failed", "pressure_negative", "屈曲步未输出正特征值")

    linear_pressure = float(eigenvalue)
    reference_pressure = postbuckling_reference_pressure(linear_pressure)
    imperfection_amplitude = imperfection_amplitude_mm(geometry)

    def run_exact_pressure_job(model_name, job_suffix, pressure, description):
        check_model = mdb.Model(name=model_name, objectToCopy=post_model)
        try:
            if "ExternalPressure" in check_model.loads:
                del check_model.loads["ExternalPressure"]
        except Exception:
            pass
        try:
            if "Step-1" in check_model.steps:
                del check_model.steps["Step-1"]
        except Exception:
            pass
        check_model.StaticStep(
            name="Step-1",
            previous="Initial",
            maxNumInc=200,
            initialInc=0.05,
            minInc=1.0e-8,
            maxInc=0.1,
            nlgeom=ON,
        )
        try:
            check_model.fieldOutputRequests["F-Output-1"].setValues(variables=("S", "E", "U", "RF"))
        except Exception:
            pass
        check_instance = check_model.rootAssembly.instances["CompositeHull-1"]
        check_region = regionToolset.Region(side1Faces=check_instance.faces[:])
        check_model.Pressure(
            name="ExternalPressure",
            createStepName="Step-1",
            region=check_region,
            magnitude=pressure,
        )
        insert_keyword(
            check_model,
            "*Step",
            "*Imperfection, file=%s, step=1\n1, %.9f" % (candidate_id, imperfection_amplitude),
        )
        job_id = candidate_id + job_suffix
        check_job = mdb.Job(
            name=job_id,
            model=model_name,
            description=description,
            type=ANALYSIS,
            memory=90,
            memoryUnits=PERCENTAGE,
            explicitPrecision=SINGLE,
            nodalOutputPrecision=SINGLE,
            echoPrint=OFF,
            modelPrint=OFF,
            contactPrint=OFF,
            historyPrint=OFF,
            userSubroutine="",
            resultsFormat=ODB,
            multiprocessingMode=DEFAULT,
            numCpus=1,
            numGPUs=0,
        )
        try:
            check_job.writeInput(consistencyChecking=OFF)
        except Exception:
            pass
        check_job.submit(consistencyChecking=OFF)
        check_job.waitForCompletion()
        return {
            "job_id": job_id,
            "odb_path": os.path.abspath(job_id + ".odb"),
            "inp_path": os.path.abspath(job_id + ".inp") if os.path.exists(job_id + ".inp") else None,
        }

    service_run = run_exact_pressure_job(
        "CPH_Service_Model",
        "_service",
        service_pressure,
        "CSDM_cph exact service pressure nonlinear check",
    )
    service_odb_path = service_run["odb_path"]
    service_extra = {
        "linear_buckling_pressure_MPa": round(linear_pressure, 6),
        "first_mode_eigenvalue": round(eigenvalue, 6),
        "abaqus_odb": odb_path,
        "linear_buckling_odb": odb_path,
        "abaqus_inp": os.path.abspath(candidate_id + ".inp") if os.path.exists(candidate_id + ".inp") else None,
        "visualization_json": mode_json_path,
        "mode_eigenvalues": eigenvalues,
        "imperfection_amplitude_mm": round(imperfection_amplitude, 9),
        "service_odb": service_odb_path if os.path.exists(service_odb_path) else None,
        "service_inp": service_run["inp_path"],
        "artifact_dir": os.getcwd(),
        "analysis_type": "linear_buckling_plus_exact_service_load_plus_capacity_riks",
        "user_subroutine_used": False,
        "verification_scope": "composite_cylindrical_shell_submodel",
    }
    if not os.path.exists(service_odb_path):
        return result_shell(
            candidate,
            result_json,
            "failed",
            "service_load_solver_failed",
            "服务压力精确加载作业未生成 ODB 文件。",
            service_extra,
        )
    service_odb = session.openOdb(name=service_odb_path)
    service_evidence = service_load_evidence(service_odb, service_pressure, material, linear_pressure)
    service_odb.close()
    service_extra.update(service_evidence)
    if service_evidence["service_pressure_check_status"] == "solver_failed":
        reason = (
            "服务压力精确加载作业状态为 %s，未形成可判定的最终收敛帧。" % (
                service_evidence.get("service_abaqus_job_status"),
            )
        )
        return result_shell(
            candidate,
            result_json,
            "failed",
            "service_load_solver_failed",
            reason,
            service_extra,
        )
    if service_evidence["service_pressure_check_status"] != "passed":
        service_extra.update({
            "verdict": "不通过",
            "failure_mode": (
                "线性屈曲压力低于服务压力"
                if linear_pressure <= service_pressure
                else "服务压力处 Hashin 首层失效"
            ),
            "design_check_status": "failed_at_service_pressure",
            "design_verdict_basis": "精确服务压力下的线性屈曲与二维 Hashin 首层失效联合判据",
            "capacity_assessment_status": "not_run_service_check_failed",
            "progressive_damage_complete": False,
            "weight_kg_per_m2": estimate_areal_density(geometry, material),
        })
        return result_shell(candidate, result_json, "success", extra=service_extra)

    if abs(target_pressure - service_pressure) <= 1.0e-9:
        target_run = service_run
        target_evidence = {
            "target_" + key[len("service_"):]: value
            for key, value in service_evidence.items()
            if key.startswith("service_")
        }
    else:
        target_run = run_exact_pressure_job(
            "CPH_Target_Model",
            "_target",
            target_pressure,
            "CSDM_cph exact design target pressure nonlinear check",
        )
        if not os.path.exists(target_run["odb_path"]):
            service_extra.update({
                "target_odb": None,
                "target_inp": target_run["inp_path"],
            })
            return result_shell(
                candidate,
                result_json,
                "failed",
                "target_load_solver_failed",
                "设计目标压力精确加载作业未生成 ODB 文件。",
                service_extra,
            )
        target_odb = session.openOdb(name=target_run["odb_path"])
        target_evidence = target_load_evidence(target_odb, target_pressure, material, linear_pressure)
        target_odb.close()

    service_extra.update({
        "target_odb": target_run["odb_path"],
        "target_inp": target_run["inp_path"],
    })
    service_extra.update(target_evidence)
    if target_evidence["target_pressure_check_status"] == "solver_failed":
        return result_shell(
            candidate,
            result_json,
            "failed",
            "target_load_solver_failed",
            "设计目标压力精确加载作业未形成可判定的最终收敛帧。",
            service_extra,
        )
    if target_evidence["target_pressure_check_status"] != "passed":
        service_extra.update({
            "verdict": "不通过",
            "failure_mode": (
                "线性屈曲压力低于设计目标压力"
                if linear_pressure <= target_pressure
                else "设计目标压力处 Hashin 首层失效"
            ),
            "design_check_status": "failed_at_design_target_pressure",
            "design_verdict_basis": "精确设计目标压力下的线性屈曲与二维 Hashin 首层失效联合判据",
            "capacity_assessment_status": "not_run_target_check_failed",
            "progressive_damage_complete": False,
            "weight_kg_per_m2": estimate_areal_density(geometry, material),
        })
        return result_shell(candidate, result_json, "success", extra=service_extra)

    service_extra.update({
        "verdict": "通过",
        "design_check_status": "passed_at_design_target_pressure",
        "design_verdict_basis": (
            "精确设计目标压力下线性屈曲压力高于目标值，且二维 Hashin 首层失效指数小于 1；"
            "结论不包含金属封头、连接、渐进损伤或试验认证。"
        ),
        "progressive_damage_complete": False,
        "weight_kg_per_m2": estimate_areal_density(geometry, material),
    })

    post_job_id = candidate_id + "_post"
    try:
        if "ExternalPressure" in post_model.loads:
            del post_model.loads["ExternalPressure"]
    except Exception:
        pass
    try:
        if "Step-1" in post_model.steps:
            del post_model.steps["Step-1"]
    except Exception:
        pass

    post_model.StaticRiksStep(
        name="Step-1",
        previous="Initial",
        maxNumInc=220,
        initialArcInc=0.01,
        minArcInc=1.0e-10,
        maxArcInc=0.1,
        nlgeom=ON,
    )
    try:
        post_model.fieldOutputRequests["F-Output-1"].setValues(variables=("S", "E", "U", "RF"))
    except Exception:
        pass

    post_instance = post_model.rootAssembly.instances["CompositeHull-1"]
    post_pressure_region = regionToolset.Region(side1Faces=post_instance.faces[:])
    post_model.Pressure(
        name="ExternalPressure",
        createStepName="Step-1",
        region=post_pressure_region,
        magnitude=reference_pressure,
    )

    analysis_settings = candidate.get("analysis") or {}
    subroutine_path = str(user_subroutine or "")
    use_subroutine = bool(analysis_settings.get("use_user_subroutine")) and bool(subroutine_path and os.path.exists(subroutine_path))
    if use_subroutine:
        enable_field_degradation(post_model, "Composite", material)

    insert_keyword(
        post_model,
        "*Step",
        "*Imperfection, file=%s, step=1\n1, %.9f" % (candidate_id, imperfection_amplitude),
    )

    post_job = mdb.Job(
        name=post_job_id,
        model="CPH_Post_Model",
        description="CSDM_cph pressure hull first-mode imperfection Riks postbuckling",
        type=ANALYSIS,
        memory=90,
        memoryUnits=PERCENTAGE,
        explicitPrecision=SINGLE,
        nodalOutputPrecision=SINGLE,
        echoPrint=OFF,
        modelPrint=OFF,
        contactPrint=OFF,
        historyPrint=OFF,
        userSubroutine=subroutine_path if use_subroutine else "",
        resultsFormat=ODB,
        multiprocessingMode=DEFAULT,
        numCpus=1,
        numGPUs=0,
    )
    try:
        post_job.writeInput(consistencyChecking=OFF)
    except Exception:
        pass
    post_job.submit(consistencyChecking=OFF)
    post_job.waitForCompletion()

    post_odb_path = os.path.abspath(post_job_id + ".odb")
    linear_extra = dict(service_extra)
    linear_extra.update({
        "linear_buckling_pressure_MPa": round(linear_pressure, 6),
        "first_mode_eigenvalue": round(eigenvalue, 6),
        "abaqus_odb": odb_path,
        "linear_buckling_odb": odb_path,
        "abaqus_inp": os.path.abspath(candidate_id + ".inp") if os.path.exists(candidate_id + ".inp") else None,
        "visualization_json": mode_json_path,
        "mode_eigenvalues": eigenvalues,
        "postbuckling_reference_pressure_MPa": round(reference_pressure, 6),
        "imperfection_amplitude_mm": round(imperfection_amplitude, 9),
        "artifact_dir": os.getcwd(),
    })
    if not os.path.exists(post_odb_path):
        return result_shell(
            candidate,
            result_json,
            "failed",
            "convergence_fail",
            "后屈曲 Riks 作业未生成 ODB 文件",
            linear_extra,
        )

    post_odb = session.openOdb(name=post_odb_path)
    lpf_pairs = extract_lpf_history(session, post_odb)
    post_job_status = odb_job_status(post_odb)
    if not lpf_pairs:
        post_odb.close()
        return result_shell(
            candidate,
            result_json,
            "failed",
            "convergence_fail",
            "后屈曲 Riks 步未输出 LPF 历史",
            linear_extra,
        )

    riks_classification = classify_riks_limit_point(lpf_pairs, post_job_status)
    max_time, max_lpf = max(lpf_pairs, key=lambda item: item[1])
    last_time, last_lpf = lpf_pairs[-1]
    observed_max_pressure = float(max_lpf) * reference_pressure
    last_pressure = float(last_lpf) * reference_pressure
    first_ply_evidence = riks_first_ply_evidence(
        post_odb.steps["Step-1"],
        lpf_pairs,
        reference_pressure,
        material,
    )
    linear_extra.update({
        "postbuckling_odb": post_odb_path,
        "postbuckling_inp": os.path.abspath(post_job_id + ".inp") if os.path.exists(post_job_id + ".inp") else None,
        "abaqus_job_status": post_job_status,
        "riks_increment_count": riks_classification["increment_count"],
        "riks_limit_point_observed": riks_classification["limit_point_observed"],
        "riks_limit_point_confirmed": riks_classification["limit_point_confirmed"],
        "riks_post_peak_drop_ratio": round(float(riks_classification["post_peak_drop_ratio"]), 8),
        "riks_lpf_max": round(float(max_lpf), 8),
        "riks_lpf_last": round(float(last_lpf), 8),
        "riks_time_at_lpf_max": round(float(max_time), 8),
        "riks_time_last": round(float(last_time), 8),
        "postbuckling_reference_pressure_MPa": round(reference_pressure, 6),
        "postbuckling_last_pressure_MPa": round(last_pressure, 6),
        "geometric_limit_pressure_observed_MPa": round(observed_max_pressure, 6),
        "analysis_type": "linear_buckling_plus_exact_service_load_plus_capacity_riks",
        "user_subroutine_used": use_subroutine,
    })
    linear_extra.update(first_ply_evidence)
    if not riks_classification["limit_point_confirmed"]:
        post_odb.close()
        reason = (
            "Riks 作业状态为 %s，且载荷路径未在成功作业中形成满足判据的后峰下降；"
            "最大观测 LPF 仅作诊断，不得作为几何极限压力。" % post_job_status
        )
        if post_job_status == "JOB_STATUS_COMPLETED_SUCCESSFULLY":
            linear_extra.update({
                "capacity_assessment_status": "geometric_limit_not_reached_within_riks_path",
                "failure_mode": (
                    "Hashin 首层失效起始"
                    if first_ply_evidence.get("first_ply_failure_pressure_upper_bound_MPa") is not None
                    else None
                ),
                "error_type": None,
                "error_log": None,
            })
            return result_shell(candidate, result_json, "success", extra=linear_extra)
        return result_shell(
            candidate,
            result_json,
            "failed",
            "limit_point_not_confirmed",
            reason,
            linear_extra,
        )

    max_displacement = None
    try:
        step = post_odb.steps["Step-1"]
        max_frame_index = min(range(len(step.frames)), key=lambda idx: abs(float(step.frames[idx].frameValue) - float(max_time)))
        max_displacement = max_displacement_from_frame(step.frames[max_frame_index])
    except Exception:
        max_displacement = None
    post_odb.close()

    geometric_limit_pressure = observed_max_pressure
    progressive_damage_complete = bool(use_subroutine)
    ultimate_pressure = geometric_limit_pressure if progressive_damage_complete else None
    failure_mode = "渐进损伤极限点" if progressive_damage_complete else "几何非线性极限点"
    verdict = "通过"
    if progressive_damage_complete:
        verdict = "通过" if ultimate_pressure >= target_pressure else "不通过"
    payload = {
        "candidate_id": candidate_id,
        "design_revision_id": candidate.get("design_revision_id"),
        "parent_design_revision_id": candidate.get("parent_design_revision_id"),
        "status": "success",
        "retry_count": 0,
        "ultimate_pressure_MPa": round(ultimate_pressure, 6) if ultimate_pressure is not None else None,
        "failure_pressure_MPa": round(ultimate_pressure, 6) if ultimate_pressure is not None else None,
        "linear_buckling_pressure_MPa": round(linear_pressure, 6),
        "first_mode_eigenvalue": round(eigenvalue, 6),
        "postbuckling_pressure_MPa": round(geometric_limit_pressure, 6),
        "geometric_limit_pressure_MPa": round(geometric_limit_pressure, 6),
        "postbuckling_reference_pressure_MPa": round(reference_pressure, 6),
        "postbuckling_last_pressure_MPa": round(last_pressure, 6),
        "riks_lpf_max": round(float(max_lpf), 8),
        "riks_lpf_last": round(float(last_lpf), 8),
        "riks_time_at_lpf_max": round(float(max_time), 8),
        "riks_time_last": round(float(last_time), 8),
        "imperfection_amplitude_mm": round(imperfection_amplitude, 9),
        "ultimate_pressure_basis": (
            "渐进损伤 Static Riks 已确认后峰极限点"
            if progressive_damage_complete else None
        ),
        "geometric_limit_pressure_basis": "一阶屈曲模态缺陷 Static Riks 已确认后峰极限点",
        "failure_mode": failure_mode,
        "max_displacement_mm": round(float(max_displacement), 6) if max_displacement is not None else None,
        "weight_kg_per_m2": estimate_areal_density(geometry, material),
        "verdict": verdict,
        "abaqus_odb": post_odb_path,
        "linear_buckling_odb": odb_path,
        "postbuckling_odb": post_odb_path,
        "abaqus_inp": os.path.abspath(candidate_id + ".inp") if os.path.exists(candidate_id + ".inp") else None,
        "postbuckling_inp": os.path.abspath(post_job_id + ".inp") if os.path.exists(post_job_id + ".inp") else None,
        "visualization_json": mode_json_path,
        "artifact_dir": os.getcwd(),
        "error_type": None,
        "error_log": None,
        "mode_eigenvalues": eigenvalues,
        "analysis_type": "linear_buckling_plus_exact_service_load_plus_capacity_riks",
        "user_subroutine_used": use_subroutine,
        "progressive_damage_complete": progressive_damage_complete,
        "design_check_status": "passed_at_design_target_pressure",
        "design_verdict_basis": service_extra["design_verdict_basis"],
        "capacity_assessment_status": "geometric_limit_confirmed",
        "verification_scope": "composite_cylindrical_shell_submodel",
        "abaqus_job_status": post_job_status,
        "riks_increment_count": riks_classification["increment_count"],
        "riks_limit_point_observed": riks_classification["limit_point_observed"],
        "riks_limit_point_confirmed": riks_classification["limit_point_confirmed"],
        "riks_post_peak_drop_ratio": round(float(riks_classification["post_peak_drop_ratio"]), 8),
        "target_odb": target_run["odb_path"],
        "target_inp": target_run["inp_path"],
        "runtime_script_sha256": runtime_script_sha256(candidate_id),
    }
    payload.update(first_ply_evidence)
    payload.update(service_evidence)
    payload.update(target_evidence)
    write_json(result_json, payload)
    return payload


def main(input_json, result_json, user_subroutine):
    candidate = {}
    try:
        candidate = read_json(input_json)
        build_and_run(candidate, result_json, user_subroutine)
    except Exception:
        result_shell(candidate, result_json, "failed", "process_crash", traceback.format_exc())

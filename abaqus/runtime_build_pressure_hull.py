# -*- coding: utf-8 -*-
"""ABAQUS 运行时耐压壳建模与线性外压屈曲结果提取脚本。"""

from __future__ import print_function

import json
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


def read_json(path):
    with open(path, "r") as handle:
        return json.load(handle)


def result_shell(candidate, result_json, status, error_type=None, error_log=None, extra=None):
    candidate_id = str(candidate.get("candidate_id") or "UNKNOWN")
    payload = {
        "candidate_id": candidate_id,
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
    }
    if extra:
        payload.update(extra)
    write_json(result_json, payload)
    return payload


def layup_angles(candidate):
    layup = candidate.get("layup") or {}
    angles = layup.get("angles_deg")
    if isinstance(angles, list) and angles:
        return [safe_float(value, 90.0) for value in angles]
    alpha = safe_float((candidate.get("geometry") or {}).get("alpha_deg"), 40.0)
    beta = safe_float((candidate.get("geometry") or {}).get("beta_deg"), 70.0)
    return [90.0, 90.0, 90.0, 90.0] + [alpha, -alpha, beta, -beta] * 8 + [90.0, 90.0, 90.0, 90.0]


def material_payload(candidate):
    material = candidate.get("material_system") or {}
    return {
        "name": str(material.get("name") or "Composite"),
        "density": safe_float(material.get("density_kg_per_m3"), 1550.0),
        "E1": safe_float(material.get("E1_GPa"), 102.0) * 1000.0,
        "E2": safe_float(material.get("E2_GPa"), 7.0) * 1000.0,
        "G12": safe_float(material.get("G12_GPa"), 3.35) * 1000.0,
        "nu12": safe_float(material.get("nu12"), 0.16),
        "Xt": safe_float(material.get("Xt_MPa"), 1400.0),
        "Xc": safe_float(material.get("Xc_MPa"), 1050.0),
        "Yt": safe_float(material.get("Yt_MPa"), 28.0),
        "Yc": safe_float(material.get("Yc_MPa"), 105.0),
        "S": safe_float(material.get("S_MPa"), 75.0),
    }


def estimate_areal_density(geometry, material):
    thickness_m = safe_float(geometry.get("thickness_mm"), 10.0) / 1000.0
    density = safe_float(material.get("density"), 1550.0)
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
    radius = safe_float(geometry.get("radius_mm"), 100.0)
    thickness = safe_float(geometry.get("thickness_mm"), 10.0)
    ratio = safe_float(geometry.get("imperfection_ratio"), 0.005)
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


def build_and_run(candidate, result_json, user_subroutine):
    from abaqus import mdb, session
    from abaqusConstants import (
        ANALYSIS,
        CARTESIAN,
        DEFAULT,
        DEFORMABLE_BODY,
        FROM_SECTION,
        GRADIENT,
        GLOBAL,
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
        AXIS_1,
        AXIS_3,
        LAMINA,
        S4R,
    )
    import mesh
    import regionToolset

    candidate_id = str(candidate.get("candidate_id") or "CPH")
    geometry = candidate.get("geometry") or {}
    material = material_payload(candidate)
    length = safe_float(geometry.get("length_mm"), 500.0)
    radius = safe_float(geometry.get("radius_mm"), 100.0)
    thickness = safe_float(geometry.get("thickness_mm"), 10.0)
    mesh_size = safe_float((candidate.get("analysis") or {}).get("mesh_size_mm"), max(min(length / 30.0, radius / 5.0), 4.0))
    target_pressure = safe_float((candidate.get("design_targets") or {}).get("ultimate_pressure_min_MPa"), 30.0)
    boundary_type = str((candidate.get("boundary_conditions") or {}).get("type") or "END_CLAMPED")
    angles = layup_angles(candidate)
    ply_thickness = thickness / max(len(angles), 1)

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
        orientationType=GLOBAL,
        localCsys=None,
        fieldName="",
        additionalRotationType=ROTATION_NONE,
        angle=0.0,
        axis=AXIS_1,
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
    linear_extra = {
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
    }
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

    max_time, max_lpf = max(lpf_pairs, key=lambda item: item[1])
    last_time, last_lpf = lpf_pairs[-1]
    ultimate_pressure = float(max_lpf) * reference_pressure
    last_pressure = float(last_lpf) * reference_pressure
    max_displacement = None
    try:
        step = post_odb.steps["Step-1"]
        max_frame_index = min(range(len(step.frames)), key=lambda idx: abs(float(step.frames[idx].frameValue) - float(max_time)))
        max_displacement = max_displacement_from_frame(step.frames[max_frame_index])
    except Exception:
        max_displacement = None
    post_odb.close()

    failure_mode = "非线性后屈曲极限点"
    payload = {
        "candidate_id": candidate_id,
        "status": "success",
        "retry_count": 0,
        "ultimate_pressure_MPa": round(ultimate_pressure, 6),
        "failure_pressure_MPa": round(ultimate_pressure, 6),
        "linear_buckling_pressure_MPa": round(linear_pressure, 6),
        "first_mode_eigenvalue": round(eigenvalue, 6),
        "postbuckling_pressure_MPa": round(ultimate_pressure, 6),
        "postbuckling_reference_pressure_MPa": round(reference_pressure, 6),
        "postbuckling_last_pressure_MPa": round(last_pressure, 6),
        "riks_lpf_max": round(float(max_lpf), 8),
        "riks_lpf_last": round(float(last_lpf), 8),
        "riks_time_at_lpf_max": round(float(max_time), 8),
        "riks_time_last": round(float(last_time), 8),
        "imperfection_amplitude_mm": round(imperfection_amplitude, 9),
        "ultimate_pressure_basis": "一阶屈曲模态缺陷 Static Riks 最大 LPF × 基准外压",
        "failure_mode": failure_mode,
        "max_displacement_mm": round(float(max_displacement), 6) if max_displacement is not None else None,
        "weight_kg_per_m2": estimate_areal_density(geometry, material),
        "verdict": "通过" if ultimate_pressure >= target_pressure else "不通过",
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
        "analysis_type": "linear_buckling_plus_first_mode_imperfection_riks",
        "user_subroutine_used": use_subroutine,
    }
    write_json(result_json, payload)
    return payload


def main(input_json, result_json, user_subroutine):
    candidate = {}
    try:
        candidate = read_json(input_json)
        build_and_run(candidate, result_json, user_subroutine)
    except Exception:
        result_shell(candidate, result_json, "failed", "process_crash", traceback.format_exc())

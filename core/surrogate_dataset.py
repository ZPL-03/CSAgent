"""压力预筛数据的字段、单位、铺层及刚度校验。"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from abaqus.cylindrical_geometry import shell_radii
from core.io_utils import text_file_sha256 as digest
from core.pressure_hull_profile import compute_laminate_stiffness, estimate_linear_buckling_feature_q, parse_layup_sequence
from core.surrogate_model import _pbipf_descriptors

DATA = Path(__file__).resolve().parents[1] / "data/surrogate"
DESCRIPTORS = ["D1", "D2", "D3"]
STIFFNESS_COMPONENTS = (
    "A11", "A12", "A22", "A33", "B11", "B12", "B13", "B22", "B23", "B33",
    "D11", "D12", "D13", "D22", "D23", "D33",
)


def row_to_candidate(row: pd.Series) -> dict:
    geometry = {name: float(row[name]) for name in ("length_mm", "thickness_mm", "alpha_deg", "beta_deg")}
    geometry.update(radius_mm=float(row.inner_radius_mm), radius_reference="inner", imperfection_ratio=float(row.imperfection_permille) / 1000)
    material = {name + "_GPa": float(row[name + "_MPa"]) / 1000 for name in ("E1", "E2", "G12")}
    material["nu12"] = float(row.nu12)
    return {"geometry": geometry, "material_system": material, "layup": {"angles_deg": parse_layup_sequence(str(row.layup))}}


def design_group(candidate: dict) -> str:
    geometry = {k: v for k, v in candidate["geometry"].items() if k not in {"imperfection_ratio", "alpha_deg", "beta_deg"}}
    payload = {"geometry": geometry, "material": candidate["material_system"], "angles": candidate["layup"]["angles_deg"]}
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


def load_dataset(directory: Path = DATA) -> tuple[pd.DataFrame, dict]:
    metadata = json.loads((directory / "dataset_metadata.json").read_text(encoding="utf-8"))
    path = directory / "design_dataset.csv"
    if metadata.get("hash_format") != "utf8_lf" or metadata.get("dataset_file") != path.name or metadata.get("sha256") != digest(path):
        raise ValueError("压力数据集与元数据指纹不一致")
    frame = pd.read_csv(path, encoding="utf-8")
    if len(frame) != metadata.get("sample_count") or frame.sample_id.duplicated().any():
        raise ValueError("压力数据集样本数量或身份不一致")
    required = set(STIFFNESS_COMPONENTS) | {
        "sample_id", "source_id", "source_row", "material", "layup", "source_flag",
        "ultimate_pressure_MPa", "eigenvalue_pressure_MPa", "imperfection_permille",
        "thickness_mm", "inner_radius_mm", "length_mm", "alpha_deg", "beta_deg",
        "E1_MPa", "E2_MPa", "G12_MPa", "nu12", "Xt_MPa", "Xc_MPa", "Yt_MPa", "Yc_MPa", "S_MPa",
    }
    if missing := required - set(frame.columns):
        raise ValueError(f"压力数据集缺少字段：{', '.join(sorted(missing))}")
    if not set(frame.source_id) <= metadata.get("sources", {}).keys():
        raise ValueError("压力数据集包含未登记的来源")
    numerical = frame.drop(columns=["sample_id", "source_id", "material", "layup"])
    if not np.isfinite(numerical.to_numpy(dtype=float)).all():
        raise ValueError("压力数据集含非有限数值")
    if np.any(frame[["ultimate_pressure_MPa", "eigenvalue_pressure_MPa", "thickness_mm", "inner_radius_mm", "length_mm"]].to_numpy() <= 0):
        raise ValueError("压力和几何尺寸必须为正")
    if np.any(frame.imperfection_permille.to_numpy() < 0):
        raise ValueError("缺陷幅值必须非负")
    return frame, metadata


def load_regression_dataset(directory: Path = DATA) -> tuple[pd.DataFrame, dict]:
    """核验有限元 Q 训练表及其工程单位描述符。"""
    metadata = json.loads((directory / "regression_metadata.json").read_text(encoding="utf-8"))
    path = directory / "regression_dataset.csv"
    if metadata.get("hash_format") != "utf8_lf" or metadata.get("dataset_file") != path.name or metadata.get("sha256") != digest(path):
        raise ValueError("线性拟合数据与元数据指纹不一致")
    if metadata.get("q_source") != "finite_element_eigenvalue" or metadata.get("radius_reference") != "inner":
        raise ValueError("线性拟合要求有限元特征根 Q 和内半径")
    if metadata.get("target_column") != "maxP" or metadata.get("descriptor_columns") != DESCRIPTORS:
        raise ValueError("线性拟合的目标或描述符字段不一致")
    frame = pd.read_csv(path, encoding="utf-8-sig")
    required = {"maxP", "Q", "QF", "t", "R", "L", "A22", "D12", "D22", "D33", *DESCRIPTORS}
    if len(frame) != metadata.get("sample_count") or not required <= set(frame.columns):
        raise ValueError("线性拟合数据的样本数或字段不一致")
    if not np.isfinite(frame[list(required)].to_numpy(dtype=float)).all():
        raise ValueError("线性拟合数据含非有限数值")
    computed = []
    for row in frame.itertuples(index=False):
        if row.maxP <= 0:
            raise ValueError("线性拟合压力目标必须为正")
        values = _pbipf_descriptors(
            {"imperfection_ratio_to_permille": 1000}, q_value=row.Q,
            length_mm=row.L, radius_mm=row.R, thickness_mm=row.t, imperfection_ratio=row.QF / 1000,
            a22=row.A22, d12=row.D12, d22=row.D22, d33=row.D33,
        )
        computed.append([values[name] for name in DESCRIPTORS])
    # 表内三个描述符的小数舍入精度不同，按列核对绝对误差。
    if np.any(np.abs(frame[DESCRIPTORS].to_numpy() - np.array(computed)) > [5.1e-10, 5.1e-6, 5.1e-10]):
        raise ValueError("线性拟合描述符与有限元 Q、几何或刚度不一致")
    return frame, metadata


def runtime_features(frame: pd.DataFrame) -> tuple[np.ndarray, np.ndarray, dict]:
    """复算刚度并生成 ASME Q 对应的平台预测描述符。"""
    if frame.empty or not set(STIFFNESS_COMPONENTS) <= set(frame.columns):
        raise ValueError("刚度核对需要非空数据和全部 16 个源表分量")
    features, groups, errors = [], [], []
    for _, row in frame.iterrows():
        candidate = row_to_candidate(row)
        geometry, material, layup = (candidate[k] for k in ("geometry", "material_system", "layup"))
        stiffness = compute_laminate_stiffness(layup, material, geometry["thickness_mm"])
        errors.append(max(
            abs(stiffness[column[0]][int(column[1]) - 1][int(column[2]) - 1] - float(row[column]))
            for column in STIFFNESS_COMPONENTS
        ))
        q = estimate_linear_buckling_feature_q(geometry, stiffness, material)
        values = _pbipf_descriptors(
            {"imperfection_ratio_to_permille": 1000}, q_value=q,
            length_mm=geometry["length_mm"], radius_mm=shell_radii(geometry)["inner"],
            thickness_mm=geometry["thickness_mm"], imperfection_ratio=geometry["imperfection_ratio"],
            a22=stiffness["A22"], d12=stiffness["D12"], d22=stiffness["D22"], d33=stiffness["D33"],
        )
        features.append([values[name] for name in DESCRIPTORS])
        groups.append(design_group(candidate))
    if max(errors) > 0.051:
        raise ValueError("ABD 复算与源表的差异超出一位小数舍入误差")
    return np.array(features), np.array(groups), {
        "stiffness_max_abs_error": max(errors), "q_source": "ASME_RD_1172",
        "asme_radius_reference": "outer", "descriptor_radius_reference": "inner",
        "imperfection_unit": "permille",
    }

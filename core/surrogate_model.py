"""耐压壳代理模型推理与案例校准。"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence

from core.config_loader import load_param_ranges
from abaqus.cylindrical_geometry import positive_number, shell_radii
from core.fem_result_semantics import verified_capacity_pressure
from core.io_utils import read_json
from core.paths import CASES_DIR, MODELS_DIR
from core.pressure_regression import PressureRegression
from core.pressure_hull_profile import (
    CANONICAL_GEOMETRY_ORDER,
    compute_laminate_stiffness,
    estimate_areal_density_kg_per_m2,
    estimate_linear_buckling_feature_q,
    geometry_to_feature_vector,
    normalize_layup,
)
from core.task_contract import boundary_condition_code, load_case_code, normalize_boundary_conditions, normalize_load_conditions


FEATURE_ORDER = [
    "length_mm",
    "radius_mm",
    "thickness_mm",
    "alpha_deg",
    "beta_deg",
    "imperfection_ratio",
    "ply_count",
    "A22",
    "B23",
    "D12",
    "D22",
    "D33",
    "asme_linear_buckling_pressure_MPa",
    "external_pressure_MPa",
    "load_case_code",
    "boundary_condition_code",
    "density_kg_per_m3",
    "E1_GPa",
    "E2_GPa",
    "G12_GPa",
    "nu12",
]


def _finite_number(value: Any, field: str) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{field} 必须为有限数值")
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError(f"{field} 必须为有限数值") from exc
    if not math.isfinite(number):
        raise ValueError(f"{field} 必须为有限数值")
    return number


@lru_cache(maxsize=1)
def _coefficients() -> Dict[str, Dict[str, Any]]:
    payload = load_param_ranges()
    coefficients = dict(payload.get("surrogate_coefficients", {}))
    pbipf = coefficients.get("PBIPF", {})
    _validate_regression_report(pbipf)
    return coefficients


def _validate_regression_report(pbipf: Dict[str, Any]) -> Dict[str, Any]:
    root = Path(__file__).resolve().parents[1]
    path = (root / str(pbipf.get("validation_report", ""))).resolve()
    if not path.is_relative_to(root) or not path.is_file():
        raise ValueError("压力回归缺少项目内验证报告")
    report = json.loads(path.read_text(encoding="utf-8"))
    if report.get("status") != "validated_candidate" or pbipf.get("q_method") != "ASME_RD_1172":
        raise ValueError("压力回归验证状态或 Q 定义不一致")
    if pbipf.get("imperfection_input") != "permille" or pbipf.get("imperfection_ratio_to_permille") != 1000:
        raise ValueError("压力回归缺陷单位与描述符定义不一致")
    model = report.get("model", {})
    expected = {
        "coefficients": [pbipf.get(name) for name in ("d1", "d2", "d3")],
        "intercept_MPa": pbipf.get("d0"), "link": pbipf.get("link"),
        "link_scale_MPa": pbipf.get("link_scale_MPa"),
    }
    if model != expected:
        raise ValueError("压力回归参数与验证报告不一致")
    required = {"core/pressure_regression.py", "core/pressure_hull_profile.py", "abaqus/cylindrical_geometry.py", "core/surrogate_model.py"}
    hashes = report.get("code_hashes", {})
    if not required <= hashes.keys():
        raise ValueError("压力回归报告缺少计算代码指纹")
    for name in required:
        if hashlib.sha256((root / name).read_bytes()).hexdigest() != hashes[name]:
            raise ValueError(f"压力回归计算代码与验证报告不一致：{name}")
    dataset = root / "data/surrogate/design_dataset.csv"
    if hashlib.sha256(dataset.read_bytes()).hexdigest() != report.get("dataset_sha256"):
        raise ValueError("压力回归数据与验证报告不一致")
    return report


def _formula_fingerprint() -> str:
    root = Path(__file__).resolve().parents[1]
    sources = {name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in (
        "core/surrogate_model.py", "core/pressure_regression.py", "core/pressure_hull_profile.py", "abaqus/cylindrical_geometry.py")}
    payload = {"sources": sources, "coefficients": _coefficients()}
    return hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


def _pbipf_descriptors(
    pbipf: Dict[str, Any],
    *,
    q_value: float,
    length_mm: float,
    radius_mm: float,
    thickness_mm: float,
    imperfection_ratio: float,
    a22: float,
    d12: float,
    d22: float,
    d33: float,
) -> Dict[str, float]:
    """按配置中的工程单位计算 PBIPF 三个描述符。

    候选合同把缺陷保存为比例值；PBIPF 公式的第三个描述符使用千分比值。
    两者的转换集中在这里，避免单条和批量预测使用不同口径。
    """
    ratio_to_permille = positive_number(pbipf.get("imperfection_ratio_to_permille"), "imperfection_ratio_to_permille")
    q = positive_number(q_value, "Q")
    length = positive_number(length_mm, "length_mm")
    radius = positive_number(radius_mm, "radius_mm")
    thickness = positive_number(thickness_mm, "thickness_mm")
    a22 = positive_number(a22, "A22")
    d22 = positive_number(d22, "D22")
    d33 = positive_number(d33, "D33")
    d12 = _finite_number(d12, "D12")
    imperfection = _finite_number(imperfection_ratio, "imperfection_ratio")
    if imperfection < 0:
        raise ValueError("imperfection_ratio 不能为负数")
    d_delta = d33 - d12
    if abs(d_delta) <= 1e-12 * max(abs(d33), abs(d12)):
        raise ValueError("PBIPF 描述符在 D33-D12 接近零时无定义")
    descriptors = {
        "D1": math.log10(q) * thickness / radius,
        "D2": q * d22 / d_delta,
        "D3": q * imperfection * ratio_to_permille * length / a22,
    }
    return {name: _finite_number(value, name) for name, value in descriptors.items()}


def _evaluate_pbipf(pbipf: Dict[str, Any], descriptors: Dict[str, float]) -> float:
    """按工程单位描述符和配置链接计算预筛压力。"""
    try:
        coefficients = [_finite_number(pbipf[name], name) for name in ("d1", "d2", "d3", "d0")]
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("PBIPF 配置必须包含 d1、d2、d3 和 d0") from exc
    d1, d2, d3, d0 = coefficients
    import numpy as np

    model = PressureRegression((d1, d2, d3), d0, str(pbipf.get("link", "identity")), pbipf.get("link_scale_MPa"))
    pressure = model.predict(np.array([[descriptors[name] for name in ("D1", "D2", "D3")]]))[0]
    return positive_number(pressure, "PBIPF_MPa")


def _error_metrics(targets: Sequence[float], predictions: Sequence[float]) -> Dict[str, float]:
    if len(targets) != len(predictions) or not targets:
        raise ValueError("误差评估需要数量一致的非空目标与预测")
    errors = [float(target) - float(prediction) for target, prediction in zip(targets, predictions)]
    absolute_errors = [abs(error) for error in errors]
    relative_errors = [
        abs(error) / abs(float(target))
        for target, error in zip(targets, errors)
        if abs(float(target)) > 1e-12
    ]
    return {
        "mae_MPa": round(sum(absolute_errors) / len(absolute_errors), 6),
        "rmse_MPa": round(math.sqrt(sum(error * error for error in errors) / len(errors)), 6),
        "mape_pct": round(100.0 * sum(relative_errors) / len(relative_errors), 6),
    }


def _fit_positive_scale(predictions: Sequence[float], targets: Sequence[float]) -> float:
    if not predictions or len(predictions) != len(targets):
        raise ValueError("比例校准需要数量一致的非空预测与目标")
    predictions = [positive_number(value, "prediction") for value in predictions]
    targets = [positive_number(value, "target") for value in targets]
    denominator = sum(float(prediction) ** 2 for prediction in predictions)
    numerator = sum(float(prediction) * float(target) for prediction, target in zip(predictions, targets))
    return positive_number(numerator / denominator, "calibration.scale")


def _leave_one_out_scale_predictions(predictions: Sequence[float], targets: Sequence[float]) -> List[float]:
    estimates: List[float] = []
    for held_out in range(len(targets)):
        training_predictions = [value for index, value in enumerate(predictions) if index != held_out]
        training_targets = [value for index, value in enumerate(targets) if index != held_out]
        estimates.append(float(predictions[held_out]) * _fit_positive_scale(training_predictions, training_targets))
    return estimates


def candidate_to_features(candidate: Dict[str, Any], task: Dict[str, Any] | None = None, feature_order: Sequence[str] | None = None) -> List[float]:
    geometry = dict(candidate.get("geometry", {}))
    layup = normalize_layup(candidate.get("layup", {}), geometry)
    material = dict(candidate.get("material_system", {}))
    load_source = task.get("load_conditions", {}) if task else candidate.get("load_conditions", {})
    boundary_source = task.get("boundary_conditions", {}) if task else candidate.get("boundary_conditions", {})
    load_conditions = normalize_load_conditions(load_source)
    boundary_conditions = normalize_boundary_conditions(boundary_source)
    stiffness = compute_laminate_stiffness(layup, material, positive_number(geometry.get("thickness_mm"), "thickness_mm"))
    q_value = estimate_linear_buckling_feature_q(geometry, stiffness, material, boundary_conditions)

    geom_features = geometry_to_feature_vector(geometry)
    feature_map = {
        **{CANONICAL_GEOMETRY_ORDER[i]: geom_features[i] for i in range(len(CANONICAL_GEOMETRY_ORDER))},
        "radius_mm": shell_radii(geometry)["middle_surface"],
        "ply_count": float(layup.get("ply_count", 0.0)),
        "A22": float(stiffness["A22"]),
        "B23": float(stiffness["B23"]),
        "D12": float(stiffness["D12"]),
        "D22": float(stiffness["D22"]),
        "D33": float(stiffness["D33"]),
        "asme_linear_buckling_pressure_MPa": float(q_value),
        "external_pressure_MPa": float(load_conditions.get("external_pressure_MPa", 0.0)),
        "load_case_code": float(load_case_code(load_conditions)),
        "boundary_condition_code": float(boundary_condition_code(boundary_conditions)),
        "density_kg_per_m3": float(material.get("density_kg_per_m3", 0.0)),
        "E1_GPa": float(material.get("E1_GPa", 0.0)),
        "E2_GPa": float(material.get("E2_GPa", 0.0)),
        "G12_GPa": float(material.get("G12_GPa", 0.0)),
        "nu12": float(material.get("nu12", 0.0)),
    }
    active_feature_order = list(feature_order or FEATURE_ORDER)
    unknown = set(active_feature_order) - feature_map.keys()
    if unknown:
        raise ValueError(f"未知代理模型特征：{sorted(unknown)}")
    return [_finite_number(feature_map[name], name) for name in active_feature_order]


def _ultimate_pressure_from_results(results: Dict[str, Any]) -> float | None:
    return verified_capacity_pressure(results)


def record_to_training_sample(record: Dict[str, Any], feature_order: Sequence[str] | None = None) -> tuple[List[float], float] | None:
    abaqus_results = record.get("abaqus_results", {})
    if abaqus_results.get("status") != "success":
        return None
    pressure = _ultimate_pressure_from_results(abaqus_results)
    if pressure is None:
        return None
    return candidate_to_features(record.get("design", {}), record.get("task"), feature_order), float(pressure)


@dataclass
class FormulaPrediction:
    pbipf_MPa: float
    ultimate_pressure_MPa: float
    linear_buckling_pressure_MPa: float
    linear_buckling_source: str
    uncertainty_MPa: float | None
    calibration_status: str
    descriptors: Dict[str, float]
    imperfection_input: str
    stiffness: Dict[str, Any]
    model_validation: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "PBIPF_MPa": self.pbipf_MPa,
            "ultimate_pressure_MPa": self.ultimate_pressure_MPa,
            "asme_linear_buckling_pressure_MPa": self.linear_buckling_pressure_MPa,
            "linear_buckling_feature_Q": self.linear_buckling_pressure_MPa,
            "linear_buckling_source": self.linear_buckling_source,
            "uncertainty_MPa": self.uncertainty_MPa,
            "calibration_status": self.calibration_status,
            "model_validation": self.model_validation,
            "PBIPF_descriptors": self.descriptors,
            "PBIPF_imperfection_input": self.imperfection_input,
            "stiffness_terms": {
                "A22": self.stiffness["A22"],
                "B23": self.stiffness["B23"],
                "D12": self.stiffness["D12"],
                "D22": self.stiffness["D22"],
                "D33": self.stiffness["D33"],
            },
        }


class SurrogateModelManager:
    """使用验证报告对应的压力回归，并应用已接受的案例比例校准。"""

    def __init__(self, models_dir: Path | None = None, case_dir: Path | None = None) -> None:
        self.models_dir = models_dir or MODELS_DIR
        self.case_dir = case_dir or CASES_DIR
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.calibration_path = self.models_dir / "pressure_hull_surrogate_calibration.json"
        self.validation_report = _validate_regression_report(_coefficients()["PBIPF"])

    def _load_calibration(self) -> Dict[str, Any]:
        if not self.calibration_path.exists():
            return {"bias_MPa": 0.0, "scale": 1.0, "uncertainty_MPa": None, "calibration_status": "not_available"}
        try:
            payload = json.loads(self.calibration_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError(f"代理模型校准文件不可读取：{self.calibration_path}") from exc
        if not isinstance(payload, dict):
            raise ValueError("代理模型校准文件必须是对象")
        status = str(payload.get("calibration_status") or "legacy_unverified")
        if status not in {"accepted", "rejected", "legacy_unverified"}:
            raise ValueError(f"未知代理模型校准状态：{status}")
        accepted = status == "accepted"
        if accepted and payload.get("formula_fingerprint") != _formula_fingerprint():
            raise ValueError("校准记录与当前公式、刚度计算或系数不一致")
        uncertainty = _finite_number(payload.get("uncertainty_MPa"), "calibration.uncertainty_MPa") if accepted else None
        if uncertainty is not None and uncertainty < 0:
            raise ValueError("校准误差不能为负数")
        return {
            "bias_MPa": _finite_number(payload.get("bias_MPa"), "calibration.bias_MPa") if accepted else 0.0,
            "scale": positive_number(payload.get("scale"), "calibration.scale") if accepted else 1.0,
            "uncertainty_MPa": uncertainty,
            "calibration_status": status,
        }

    def load_training_records(self) -> List[Dict[str, Any]]:
        records: List[Dict[str, Any]] = []
        for path in sorted(self.case_dir.glob("CASE_*.json")):
            record = read_json(path)
            if record_to_training_sample(record) is not None:
                records.append(record)
        return records

    def formula_prediction(self, candidate: Dict[str, Any], apply_calibration: bool = True) -> FormulaPrediction:
        geometry = dict(candidate.get("geometry", {}))
        material = dict(candidate.get("material_system", {}))
        layup = normalize_layup(candidate.get("layup", {}), geometry)
        stiffness = compute_laminate_stiffness(layup, material, positive_number(geometry.get("thickness_mm"), "thickness_mm"))
        boundary_conditions = normalize_boundary_conditions(candidate.get("boundary_conditions", {}))
        q_value = estimate_linear_buckling_feature_q(geometry, stiffness, material, boundary_conditions)
        q_source = "ASME RD-1172线性屈曲公式"
        coefficients = _coefficients()
        pbipf = coefficients.get("PBIPF", {})

        length = geometry.get("length_mm")
        radius = shell_radii(geometry)["middle_surface"]
        thickness = geometry.get("thickness_mm")
        imperfection = geometry.get("imperfection_ratio")
        a22 = float(stiffness["A22"])
        d12 = float(stiffness["D12"])
        d22 = float(stiffness["D22"])
        d33 = float(stiffness["D33"])
        descriptors = _pbipf_descriptors(
            pbipf,
            q_value=q_value,
            length_mm=length,
            radius_mm=radius,
            thickness_mm=thickness,
            imperfection_ratio=imperfection,
            a22=a22,
            d12=d12,
            d22=d22,
            d33=d33,
        )
        pbipf_pressure = _evaluate_pbipf(pbipf, descriptors)

        calibration = (
            self._load_calibration()
            if apply_calibration
            else {"bias_MPa": 0.0, "scale": 1.0, "uncertainty_MPa": None, "calibration_status": "disabled"}
        )
        ultimate_pressure = positive_number(pbipf_pressure * calibration["scale"] + calibration["bias_MPa"], "calibrated_PBIPF_MPa")
        uncertainty = calibration["uncertainty_MPa"]
        return FormulaPrediction(
            pbipf_MPa=float(ultimate_pressure),
            ultimate_pressure_MPa=float(ultimate_pressure),
            linear_buckling_pressure_MPa=round(float(q_value), 6),
            linear_buckling_source=q_source,
            uncertainty_MPa=round(float(uncertainty), 3) if uncertainty is not None else None,
            calibration_status=str(calibration.get("calibration_status") or "not_available"),
            descriptors={key: round(float(value), 12) for key, value in descriptors.items()},
            imperfection_input=str(pbipf.get("imperfection_input") or "permille"),
            stiffness=stiffness,
            model_validation={
                "link": pbipf["link"],
                "cross_validation_rmse_MPa": self.validation_report["cross_validation"]["metrics"][pbipf["link"]]["rmse_MPa"],
                "testing_rmse_MPa": self.validation_report["testing"]["candidate"]["rmse_MPa"],
                "outside_descriptor_range": any(
                    not low <= descriptors[name] <= high
                    for name, low, high in zip(("D1", "D2", "D3"), self.validation_report["training_feature_min"], self.validation_report["training_feature_max"])
                ),
            },
        )

    def train_from_records(self, records: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
        predictions: List[float] = []
        targets: List[float] = []
        for record in records:
            pressure = _ultimate_pressure_from_results(record.get("abaqus_results", {}))
            if pressure is None:
                continue
            prediction = self.formula_prediction(record.get("design", {}), apply_calibration=False).ultimate_pressure_MPa
            predictions.append(float(prediction))
            targets.append(float(pressure))
        if len(targets) < 3:
            raise RuntimeError("代理模型校准至少需要 3 条成功耐压壳案例")

        candidate_scale = _fit_positive_scale(predictions, targets)
        baseline_metrics = _error_metrics(targets, predictions)
        validation_predictions = _leave_one_out_scale_predictions(predictions, targets)
        validation_metrics = _error_metrics(targets, validation_predictions)
        accepted = all(
            validation_metrics[name] < baseline_metrics[name]
            for name in ("mae_MPa", "rmse_MPa", "mape_pct")
        )
        applied_scale = candidate_scale if accepted else 1.0
        uncertainty = validation_metrics["rmse_MPa"] if accepted else baseline_metrics["rmse_MPa"]
        summary = {
            "selected_model": "ASME_descriptor_pressure_regression",
            "training_size": len(targets),
            "calibration_status": "accepted" if accepted else "rejected",
            "calibration_method": "positive_scale_leave_one_out",
            "formula_fingerprint": _formula_fingerprint(),
            "bias_MPa": 0.0,
            "scale": round(applied_scale, 6),
            "candidate_scale": round(candidate_scale, 6),
            "uncertainty_MPa": round(uncertainty, 6),
            "validation": {
                "baseline": baseline_metrics,
                "leave_one_out_candidate": validation_metrics,
                "acceptance_rule": "MAE、RMSE 和 MAPE 均严格优于未校准公式",
            },
            "feature_order": FEATURE_ORDER,
            "linear_buckling_model": "ASME_RD_1172",
        }
        self.calibration_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
        return summary

    def predict(self, feature_rows: Sequence[Sequence[float]]) -> List[float]:
        coefficients = _coefficients().get("PBIPF", {})
        calibration = self._load_calibration()
        predictions: List[float] = []
        for row in feature_rows:
            if len(row) != len(FEATURE_ORDER):
                raise ValueError(f"代理模型特征需要 {len(FEATURE_ORDER)} 项，实际为 {len(row)} 项")
            values = {name: _finite_number(value, name) for name, value in zip(FEATURE_ORDER, row)}
            descriptors = _pbipf_descriptors(
                coefficients,
                q_value=values["asme_linear_buckling_pressure_MPa"],
                length_mm=values["length_mm"],
                radius_mm=values["radius_mm"],
                thickness_mm=values["thickness_mm"],
                imperfection_ratio=values["imperfection_ratio"],
                a22=values["A22"],
                d12=values["D12"],
                d22=values["D22"],
                d33=values["D33"],
            )
            pressure = _evaluate_pbipf(coefficients, descriptors)
            pressure = positive_number(pressure * calibration["scale"] + calibration["bias_MPa"], "calibrated_PBIPF_MPa")
            predictions.append(pressure)
        return predictions

    def predict_candidates(self, candidates: Iterable[Dict[str, Any]], task: Dict[str, Any] | None = None) -> List[float]:
        return [self.formula_prediction(candidate).ultimate_pressure_MPa for candidate in candidates]

    def predict_candidate_payload(self, candidate: Dict[str, Any]) -> Dict[str, Any]:
        payload = self.formula_prediction(candidate).to_dict()
        payload["areal_density_kg_per_m2"] = estimate_areal_density_kg_per_m2(
            candidate.get("geometry", {}),
            candidate.get("material_system", {}),
        )
        return payload

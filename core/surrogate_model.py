"""耐压壳代理模型推理与案例校准。"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence

from core.config_loader import load_param_ranges
from core.fem_result_semantics import verified_capacity_pressure
from core.io_utils import read_json
from core.paths import CASES_DIR, MODELS_DIR
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


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _coefficients() -> Dict[str, Dict[str, Any]]:
    payload = load_param_ranges()
    return dict(payload.get("surrogate_coefficients", {}))


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
    ratio_to_permille_value = pbipf.get("imperfection_ratio_to_permille")
    ratio_to_permille = _safe_float(ratio_to_permille_value, 0.0)
    if ratio_to_permille <= 0:
        raise ValueError("PBIPF 配置缺少有效的 imperfection_ratio_to_permille")
    imperfection_permille = max(float(imperfection_ratio), 1e-9) * ratio_to_permille
    d_delta = float(d33) - float(d12)
    if abs(d_delta) < 1e-9:
        d_delta = math.copysign(1e-9, d_delta or 1.0)
    return {
        "D1": math.log10(max(float(q_value), 1e-6)) * float(thickness_mm) / max(float(radius_mm), 1e-9),
        "D2": float(q_value) * float(d22) / d_delta,
        "D3": float(q_value) * imperfection_permille * float(length_mm) / max(float(a22), 1e-9),
    }


def _evaluate_pbipf(pbipf: Dict[str, Any], descriptors: Dict[str, float]) -> float:
    """使用已计算的工程单位描述符评估 PBIPF 公式。"""
    try:
        coefficients = [float(pbipf[name]) for name in ("d1", "d2", "d3", "d0")]
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("PBIPF 配置必须包含 d1、d2、d3 和 d0") from exc
    d1, d2, d3, d0 = coefficients
    return d1 * descriptors["D1"] + d2 * descriptors["D2"] + d3 * descriptors["D3"] + d0


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
    denominator = sum(float(prediction) ** 2 for prediction in predictions)
    if denominator <= 1e-12:
        return 1.0
    numerator = sum(float(prediction) * float(target) for prediction, target in zip(predictions, targets))
    return max(numerator / denominator, 1e-9)


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
    stiffness = compute_laminate_stiffness(layup, material, _safe_float(geometry.get("thickness_mm"), 10.0))
    q_value = estimate_linear_buckling_feature_q(geometry, stiffness, material, boundary_conditions)

    geom_features = geometry_to_feature_vector(geometry)
    feature_map = {
        **{CANONICAL_GEOMETRY_ORDER[i]: geom_features[i] for i in range(len(CANONICAL_GEOMETRY_ORDER))},
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
    return [float(feature_map.get(name, 0.0)) for name in active_feature_order]


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
    uncertainty_MPa: float
    calibration_status: str
    descriptors: Dict[str, float]
    imperfection_input: str
    stiffness: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "PBIPF_MPa": self.pbipf_MPa,
            "ultimate_pressure_MPa": self.ultimate_pressure_MPa,
            "asme_linear_buckling_pressure_MPa": self.linear_buckling_pressure_MPa,
            "linear_buckling_feature_Q": self.linear_buckling_pressure_MPa,
            "linear_buckling_source": self.linear_buckling_source,
            "uncertainty_MPa": self.uncertainty_MPa,
            "calibration_status": self.calibration_status,
            "PBIPF_descriptors": self.descriptors,
            "PBIPF_imperfection_input": self.imperfection_input,
            "stiffness_terms": {
                "A22": self.stiffness["A22"],
                "B23": self.stiffness["B23"],
                "D12": self.stiffness["D12"],
                "D22": self.stiffness["D22"],
                "D33": self.stiffness["D33"],
                "B23_raw": self.stiffness["B23_raw"],
            },
        }


class SurrogateModelManager:
    """以 PBIPF 符号公式为主，仅应用通过留一验证的全局比例校准。"""

    def __init__(self, models_dir: Path | None = None, case_dir: Path | None = None) -> None:
        self.models_dir = models_dir or MODELS_DIR
        self.case_dir = case_dir or CASES_DIR
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.calibration_path = self.models_dir / "pressure_hull_surrogate_calibration.json"

    def _load_calibration(self) -> Dict[str, Any]:
        if not self.calibration_path.exists():
            return {"bias_MPa": 0.0, "scale": 1.0, "uncertainty_MPa": None, "calibration_status": "not_available"}
        try:
            payload = json.loads(self.calibration_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {"bias_MPa": 0.0, "scale": 1.0, "uncertainty_MPa": None, "calibration_status": "invalid"}
        status = str(payload.get("calibration_status") or "legacy_unverified")
        accepted = status == "accepted"
        return {
            "bias_MPa": _safe_float(payload.get("bias_MPa"), 0.0) if accepted else 0.0,
            "scale": (_safe_float(payload.get("scale"), 1.0) or 1.0) if accepted else 1.0,
            "uncertainty_MPa": payload.get("uncertainty_MPa") if accepted else None,
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
        stiffness = compute_laminate_stiffness(layup, material, _safe_float(geometry.get("thickness_mm"), 10.0))
        boundary_conditions = normalize_boundary_conditions(candidate.get("boundary_conditions", {}))
        q_value = max(estimate_linear_buckling_feature_q(geometry, stiffness, material, boundary_conditions), 1e-6)
        q_source = "ASME RD-1172线性屈曲公式"
        coefficients = _coefficients()
        pbipf = coefficients.get("PBIPF", {})

        length = max(_safe_float(geometry.get("length_mm"), 500.0), 1e-9)
        radius = max(_safe_float(geometry.get("radius_mm"), 100.0), 1e-9)
        thickness = max(_safe_float(geometry.get("thickness_mm"), 10.0), 1e-9)
        imperfection = max(_safe_float(geometry.get("imperfection_ratio"), 0.005), 1e-9)
        a22 = max(float(stiffness["A22"]), 1e-9)
        d12 = float(stiffness["D12"])
        d22 = max(float(stiffness["D22"]), 1e-9)
        d33 = max(float(stiffness["D33"]), 1e-9)
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
        pbipf_pressure = max(pbipf_pressure * calibration["scale"] + calibration["bias_MPa"], 0.1)
        ultimate_pressure = max(pbipf_pressure, 0.1)
        uncertainty = max(
            _safe_float(pbipf.get("rmse_MPa"), 5.04),
            _safe_float(calibration.get("uncertainty_MPa"), 0.0),
        )
        return FormulaPrediction(
            pbipf_MPa=round(float(pbipf_pressure), 3),
            ultimate_pressure_MPa=round(float(ultimate_pressure), 3),
            linear_buckling_pressure_MPa=round(float(q_value), 6),
            linear_buckling_source=q_source,
            uncertainty_MPa=round(float(uncertainty), 3),
            calibration_status=str(calibration.get("calibration_status") or "not_available"),
            descriptors={key: round(float(value), 12) for key, value in descriptors.items()},
            imperfection_input=str(pbipf.get("imperfection_input") or "permille"),
            stiffness=stiffness,
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
            "selected_model": "PBIPF_ASME_RD_1172",
            "training_size": len(targets),
            "calibration_status": "accepted" if accepted else "rejected",
            "calibration_method": "positive_scale_leave_one_out",
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

    def train(self, feature_rows: Sequence[Sequence[float]], targets: Sequence[float]) -> Dict[str, Any]:
        if len(targets) < 3:
            raise RuntimeError("代理模型校准至少需要 3 条目标数据")
        target_mean = sum(float(value) for value in targets) / len(targets)
        summary = {
            "selected_model": "PBIPF_ASME_RD_1172",
            "training_size": len(targets),
            "calibration_status": "not_applicable",
            "calibration_method": "external_targets_without_formula_validation",
            "bias_MPa": 0.0,
            "scale": 1.0,
            "target_mean_MPa": round(target_mean, 6),
            "feature_order": FEATURE_ORDER,
            "linear_buckling_model": "ASME_RD_1172",
        }
        self.calibration_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
        return summary

    def predict(self, feature_rows: Sequence[Sequence[float]]) -> List[float]:
        coefficients = _coefficients().get("PBIPF", {})
        calibration = self._load_calibration()
        index_by_name = {name: index for index, name in enumerate(FEATURE_ORDER)}

        def value(row: Sequence[float], name: str, default: float) -> float:
            index = index_by_name.get(name)
            if index is None or index >= len(row):
                return default
            return _safe_float(row[index], default)

        predictions: List[float] = []
        for row in feature_rows:
            q_value = max(value(row, "asme_linear_buckling_pressure_MPa", 1e-6), 1e-6)
            length = max(value(row, "length_mm", 500.0), 1e-9)
            radius = max(value(row, "radius_mm", 100.0), 1e-9)
            thickness = max(value(row, "thickness_mm", 10.0), 1e-9)
            imperfection = max(value(row, "imperfection_ratio", 0.005), 1e-9)
            a22 = max(value(row, "A22", 1.0), 1e-9)
            d12 = value(row, "D12", 0.0)
            d22 = max(value(row, "D22", 1.0), 1e-9)
            d33 = max(value(row, "D33", 1.0), 1e-9)
            descriptors = _pbipf_descriptors(
                coefficients,
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
            pressure = _evaluate_pbipf(coefficients, descriptors)
            pressure = max(pressure * calibration["scale"] + calibration["bias_MPa"], 0.1)
            predictions.append(round(float(pressure), 3))
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

"""按数据集划分拟合压力预筛模型，输出交叉验证与测试误差。"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import GroupKFold, GroupShuffleSplit

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.pressure_regression import fit_pressure_regression  # noqa: E402
from core.surrogate_dataset import (  # noqa: E402
    DATA, digest, load_dataset, runtime_features,
)


def evaluate(coefficients: dict, features: np.ndarray) -> np.ndarray:
    return features @ np.array([coefficients[f"d{i}"] for i in range(1, 4)]) + coefficients["d0"]


def metrics(target: np.ndarray, prediction: np.ndarray) -> dict:
    if target.shape != prediction.shape or not len(target):
        raise ValueError("评估需要等长的非空目标和预测")
    if not np.isfinite(target).all() or not np.isfinite(prediction).all() or np.any(target <= 0):
        raise ValueError("目标必须为正有限数值，预测必须为有限数值")
    relative = (prediction - target) / target
    return {
        "count": len(target), "rmse_MPa": float(np.sqrt(mean_squared_error(target, prediction))),
        "mae_MPa": float(mean_absolute_error(target, prediction)), "r2": float(r2_score(target, prediction)) if len(target) > 1 else None,
        "mape_pct": float(np.mean(np.abs(relative)) * 100), "nonpositive_count": int(np.sum(prediction <= 0)),
        "max_overprediction_MPa": float(max(0.0, np.max(prediction - target))), "max_overprediction_pct": float(max(0.0, np.max(relative) * 100)),
    }


def screening_metrics(target: np.ndarray, prediction: np.ndarray) -> dict:
    result = metrics(target, prediction)
    count = max(1, int(np.ceil(len(target) * 0.1)))
    actual_top = set(np.argsort(target)[-count:])
    predicted_top = set(np.argsort(prediction)[-count:])
    result["spearman"] = float(spearmanr(target, prediction).statistic) if len(np.unique(target)) > 1 and len(np.unique(prediction)) > 1 else None
    result["top_decile_recall"] = len(actual_top & predicted_top) / count
    return result


def material_metrics(frame: pd.DataFrame, prediction: np.ndarray) -> dict:
    return {str(material): screening_metrics(group.ultimate_pressure_MPa.to_numpy(), prediction[group.index.to_numpy()])
            for material, group in frame.groupby("material")}


def split_design_groups(groups: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    splitter = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
    training, testing = next(splitter.split(np.zeros(len(groups)), groups=groups))
    if set(groups[training]) & set(groups[testing]):
        raise ValueError("建模集与测试集存在共享设计")
    return training, testing


def cross_validate(x: np.ndarray, y: np.ndarray, groups: np.ndarray) -> tuple[dict, pd.DataFrame]:
    splitter = GroupKFold(n_splits=5, shuffle=True, random_state=42)
    predictions = {name: np.full(len(y), np.nan) for name in ("identity", "softplus")}
    assignments = np.full(len(y), -1)
    folds = []
    for fold, (training, testing) in enumerate(splitter.split(x, y, groups)):
        if set(groups[training]) & set(groups[testing]):
            raise ValueError("交叉验证设计组交叉")
        fold_report = {"fold": fold, "training_count": len(training), "testing_count": len(testing), "models": {}}
        assignments[testing] = fold
        for link in predictions:
            model = fit_pressure_regression(x[training], y[training], link)
            predictions[link][testing] = model.predict(x[testing])
            fold_report["models"][link] = model.to_dict()
        folds.append(fold_report)
    report = {"folds": folds, "group_overlap_count": 0,
              "metrics": {name: screening_metrics(y, value) for name, value in predictions.items()}}
    return report, pd.DataFrame({"fold": assignments, "design_group": groups,
                                 "target_MPa": y, **{name + "_MPa": value for name, value in predictions.items()}})


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("输出目录已存在，评估证据不覆盖")
    dataset, metadata = load_dataset()
    features, all_groups, feature_audit = runtime_features(dataset)
    training, testing = split_design_groups(all_groups)
    frame = dataset.iloc[training].reset_index(drop=True)
    held_out = dataset.iloc[testing].reset_index(drop=True)
    x, groups = features[training], all_groups[training]
    y = frame.ultimate_pressure_MPa.to_numpy()
    validation, rows = cross_validate(x, y, groups)
    baseline_record = json.loads((DATA / "baseline_validation.json").read_text(encoding="utf-8"))
    baseline_coefficients = baseline_record["coefficients"]
    validation["baseline"] = screening_metrics(y, evaluate(baseline_coefficients, x))
    eligible = [name for name, values in validation["metrics"].items() if values["nonpositive_count"] == 0]
    if not eligible:
        raise ValueError("所有回归链接均出现非正预测")
    selected = min(eligible, key=lambda name: validation["metrics"][name]["rmse_MPa"])
    model = fit_pressure_regression(x, y, selected)
    # 测试集不参与链接选型和系数拟合。
    hold_x, hold_groups = features[testing], all_groups[testing]
    hold_y = held_out.ultimate_pressure_MPa.to_numpy()
    predicted, baseline = model.predict(hold_x), evaluate(baseline_coefficients, hold_x)
    hold_metrics = screening_metrics(hold_y, predicted)
    baseline_metrics = screening_metrics(hold_y, baseline)
    accepted = all(hold_metrics[name] < baseline_metrics[name] for name in ("rmse_MPa", "mae_MPa"))
    accepted = accepted and hold_metrics["spearman"] >= baseline_metrics["spearman"] and hold_metrics["nonpositive_count"] == 0
    report = {
        "schema_version": 2, "status": "validated_candidate" if accepted else "rejected_holdout_metrics",
        "selection_rule": "五折分组验证中无非正预测的模型按 RMSE 选型；测试集 RMSE、MAE 严格优于基线，Spearman 不低于基线",
        "published": False, "model": model.to_dict(), "baseline_coefficients": baseline_coefficients,
        "baseline_formula_fingerprint": baseline_record["formula_fingerprint"], "dataset_sha256": metadata["sha256"],
        "split": {"method": "GroupShuffleSplit", "random_state": 42, "test_group_fraction": 0.2,
                  "group_fields": ["material_elastic_constants", "physical_layup", "length_mm", "inner_radius_mm", "thickness_mm"],
                  "sample_count": len(dataset), "training_count": len(training), "testing_count": len(testing),
                  "training_group_count": len(set(groups)), "testing_group_count": len(set(hold_groups)),
                  "group_overlap_count": 0},
        "cross_validation": validation, "testing": {"candidate": hold_metrics, "baseline": baseline_metrics},
        "material_metrics": {
            "cross_validation": material_metrics(frame, rows[selected + "_MPa"].to_numpy()),
            "testing": material_metrics(held_out, predicted),
        },
        "training_count": len(y), "training_feature_min": x.min(axis=0).tolist(), "training_feature_max": x.max(axis=0).tolist(),
        "testing_outside_feature_range_count": int(np.sum(np.any((hold_x < x.min(axis=0)) | (hold_x > x.max(axis=0)), axis=1))),
        "stiffness_max_abs_error": feature_audit["stiffness_max_abs_error"],
        "dataset_metadata_sha256": digest(DATA / "dataset_metadata.json"),
        "code_hashes": {str(p.relative_to(ROOT)).replace("\\", "/"): digest(p) for p in (
            Path(__file__), ROOT / "core/surrogate_dataset.py", ROOT / "core/pressure_regression.py",
            ROOT / "core/surrogate_model.py", ROOT / "core/pressure_hull_profile.py", ROOT / "abaqus/cylindrical_geometry.py")},
    }
    args.output.mkdir(parents=True)
    rows.insert(0, "sample_id", frame.sample_id)
    rows.to_csv(args.output / "cross_validation.csv", index=False, encoding="utf-8")
    pd.DataFrame({"sample_id": held_out.sample_id, "design_group": hold_groups, "target_MPa": hold_y,
                  "candidate_MPa": predicted, "baseline_MPa": baseline}).to_csv(args.output / "testing.csv", index=False, encoding="utf-8")
    report["prediction_hashes"] = {p.name: digest(p) for p in sorted(args.output.glob("*.csv"))}
    (args.output / "report.json").write_text(json.dumps(report, ensure_ascii=False, allow_nan=False, indent=2), encoding="utf-8")
    print(json.dumps({"status": report["status"], "model": report["model"], "cross_validation": validation["metrics"],
                      "testing": report["testing"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()

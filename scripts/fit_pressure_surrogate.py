"""使用有限元 Q 拟合线性压力公式，分别评估回归与 ASME 代入误差。"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.pressure_regression import fit_pressure_regression  # noqa: E402
from core.surrogate_dataset import (  # noqa: E402
    DATA, DESCRIPTORS, digest, load_dataset, load_regression_dataset, runtime_features,
)


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
        "min_prediction_MPa": float(np.min(prediction)),
        "max_overprediction_MPa": float(max(0.0, np.max(prediction - target))),
        "max_overprediction_pct": float(max(0.0, np.max(relative) * 100)),
    }


def screening_metrics(target: np.ndarray, prediction: np.ndarray) -> dict:
    result = metrics(target, prediction)
    count = max(1, int(np.ceil(len(target) * 0.1)))
    actual_top = set(np.argsort(target)[-count:])
    predicted_top = set(np.argsort(prediction)[-count:])
    result["spearman"] = float(spearmanr(target, prediction).statistic) if len(np.unique(target)) > 1 and len(np.unique(prediction)) > 1 else None
    result["top_decile_recall"] = len(actual_top & predicted_top) / count
    return result


def split_regression_rows(count: int) -> tuple[np.ndarray, np.ndarray]:
    return train_test_split(np.arange(count), test_size=0.25, random_state=15)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("输出目录已存在，评估证据不覆盖")
    # ASME 代入仅做应用评估，不参与系数求解。
    regression, regression_metadata = load_regression_dataset()
    x, y = regression[DESCRIPTORS].to_numpy(), regression.maxP.to_numpy()
    training, testing = split_regression_rows(len(regression))
    model = fit_pressure_regression(x[training], y[training])
    predicted = model.predict(x)

    deployment, _ = load_dataset()
    deployment_x, groups, feature_audit = runtime_features(deployment)
    deployed_prediction = model.predict(deployment_x)
    deployment_target = deployment.ultimate_pressure_MPa.to_numpy()
    report = {
        "schema_version": 3, "status": "evaluated", "hash_format": "utf8_lf", "model_type": "linear", "model": model.to_dict(),
        "descriptor_contract": {
            "training_q_source": "finite_element_eigenvalue", "prediction_q_source": "ASME_RD_1172",
            "asme_radius_reference": "outer", "descriptor_radius_reference": "inner",
            "imperfection_input": "permille", "imperfection_ratio_to_permille": 1000,
        },
        "split": {"method": "train_test_split", "random_state": 15, "test_fraction": 0.25,
                  "sample_count": len(regression), "training_count": len(training), "testing_count": len(testing)},
        "regression_evaluation": {"q_source": regression_metadata["q_source"],
            "training": screening_metrics(y[training], predicted[training]),
            "testing": screening_metrics(y[testing], predicted[testing])},
        "deployment_evaluation": {"q_source": "ASME_RD_1172", "population": "complete_dataset_not_independent_holdout",
            "sample_count": len(deployment), "design_group_count": len(set(groups)),
            "metrics": screening_metrics(deployment_target, deployed_prediction),
            "materials": {str(material): screening_metrics(group.ultimate_pressure_MPa.to_numpy(), deployed_prediction[group.index.to_numpy()])
                          for material, group in deployment.groupby("material")}},
        "training_feature_min": x[training].min(axis=0).tolist(), "training_feature_max": x[training].max(axis=0).tolist(),
        "deployment_outside_feature_range_count": int(np.sum(np.any((deployment_x < x[training].min(axis=0)) | (deployment_x > x[training].max(axis=0)), axis=1))),
        "stiffness_max_abs_error": feature_audit["stiffness_max_abs_error"],
        "data_hashes": {str(p.relative_to(ROOT)).replace("\\", "/"): digest(p) for p in (
            DATA / "regression_dataset.csv", DATA / "regression_metadata.json", DATA / "design_dataset.csv", DATA / "dataset_metadata.json")},
        "code_hashes": {str(p.relative_to(ROOT)).replace("\\", "/"): digest(p) for p in (
            Path(__file__), ROOT / "core/surrogate_dataset.py", ROOT / "core/pressure_regression.py",
            ROOT / "core/surrogate_model.py", ROOT / "core/io_utils.py", ROOT / "core/pressure_hull_profile.py", ROOT / "abaqus/cylindrical_geometry.py")},
    }
    args.output.mkdir(parents=True)
    partition = np.full(len(regression), "training", dtype=object)
    partition[testing] = "testing"
    pd.DataFrame({"source_row": np.arange(len(regression)) + 2, "partition": partition,
                  "finite_element_Q_MPa": regression.Q, "target_MPa": y,
                  "prediction_MPa": predicted}).to_csv(args.output / "regression_predictions.csv", index=False, encoding="utf-8")
    pd.DataFrame({"sample_id": deployment.sample_id, "source_row": deployment.source_row,
                  "target_MPa": deployment_target, "prediction_MPa": deployed_prediction,
                  "nonpositive_prediction": deployed_prediction <= 0}).to_csv(args.output / "deployment_predictions.csv", index=False, encoding="utf-8")
    report["prediction_hashes"] = {p.name: digest(p) for p in sorted(args.output.glob("*.csv"))}
    (args.output / "report.json").write_text(json.dumps(report, ensure_ascii=False, allow_nan=False, indent=2), encoding="utf-8")
    print(json.dumps({"model": report["model"], "regression_evaluation": report["regression_evaluation"],
                      "deployment_evaluation": report["deployment_evaluation"]["metrics"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()

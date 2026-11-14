"""三个工程描述符的线性压力回归。"""

from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np


@dataclass(frozen=True)
class PressureRegression:
    """保存工程单位系数，返回未截断的线性估计。"""

    coefficients: tuple[float, float, float]
    intercept_MPa: float

    def predict(self, features: np.ndarray) -> np.ndarray:
        x = np.asarray(features, dtype=float)
        if x.ndim != 2 or x.shape[1] != 3 or not np.isfinite(x).all():
            raise ValueError("压力回归需要有限的三列描述符")
        coefficients = np.asarray(self.coefficients, dtype=float)
        if coefficients.shape != (3,) or not np.isfinite(coefficients).all() or not np.isfinite(self.intercept_MPa):
            raise ValueError("压力回归需要有限的三个系数和截距")
        prediction = x @ coefficients + self.intercept_MPa
        if not np.isfinite(prediction).all():
            raise ValueError("压力预测超出数值表示范围")
        return prediction

    def to_dict(self) -> dict:
        return asdict(self)


def fit_pressure_regression(features: np.ndarray, targets: np.ndarray) -> PressureRegression:
    """对有限元 Q 对应的三个描述符作最小二乘拟合。"""
    x, y = np.asarray(features, dtype=float), np.asarray(targets, dtype=float)
    if x.ndim != 2 or x.shape[1] != 3 or y.shape != (len(x),) or len(y) < 6:
        raise ValueError("回归需要至少六条三描述符样本及对应目标")
    if not np.isfinite(x).all() or not np.isfinite(y).all() or np.any(y <= 0):
        raise ValueError("回归输入必须有限，压力目标必须为正")
    # 标准化改善数值条件；预测系数和截距反算回工程单位。
    center, spread = x.mean(axis=0), x.std(axis=0)
    y_scale = y.std()
    if np.any(spread <= 0) or y_scale <= 0:
        raise ValueError("回归描述符和压力目标需要非零方差")
    design = np.column_stack([np.ones(len(x)), (x - center) / spread])
    initial, _, rank, _ = np.linalg.lstsq(design, y / y_scale, rcond=None)
    if rank != 4:
        raise ValueError("回归设计矩阵秩不足")
    coefficients = initial[1:] * y_scale / spread
    intercept = float(initial[0] * y_scale - coefficients @ center)
    return PressureRegression(tuple(float(v) for v in coefficients), intercept)

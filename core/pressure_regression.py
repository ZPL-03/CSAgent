"""同一组三个工程描述符的压力回归与正值链接。"""

from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np
from scipy.optimize import least_squares


@dataclass(frozen=True)
class PressureRegression:
    coefficients: tuple[float, float, float]
    intercept_MPa: float
    link: str
    link_scale_MPa: float | None = None

    def predict(self, features: np.ndarray) -> np.ndarray:
        x = np.asarray(features, dtype=float)
        if x.ndim != 2 or x.shape[1] != 3 or not np.isfinite(x).all():
            raise ValueError("压力回归需要有限的三列描述符")
        eta = x @ np.array(self.coefficients) + self.intercept_MPa
        if self.link == "identity":
            prediction = eta
        elif self.link == "softplus":
            scale = self.link_scale_MPa
            if scale is None or not np.isfinite(scale) or scale <= 0:
                raise ValueError("softplus 链接尺度必须为正有限数值")
            prediction = scale * np.logaddexp(0, eta / scale)
        else:
            raise ValueError(f"未知压力链接：{self.link}")
        if not np.isfinite(prediction).all():
            raise ValueError("压力预测超出数值表示范围")
        if self.link == "softplus" and np.any(prediction <= 0):
            raise ValueError("正值链接发生数值下溢，不能提供有效压力预测")
        return prediction

    def to_dict(self) -> dict:
        return asdict(self)


def fit_pressure_regression(features: np.ndarray, targets: np.ndarray, link: str) -> PressureRegression:
    x, y = np.asarray(features, dtype=float), np.asarray(targets, dtype=float)
    if x.ndim != 2 or x.shape[1] != 3 or y.shape != (len(x),) or len(y) < 6:
        raise ValueError("回归需要至少六条三描述符样本及对应目标")
    if not np.isfinite(x).all() or not np.isfinite(y).all() or np.any(y <= 0):
        raise ValueError("回归输入必须有限，压力目标必须为正")
    if link not in {"identity", "softplus"}:
        raise ValueError(f"未知压力链接：{link}")
    center, spread = x.mean(axis=0), x.std(axis=0)
    y_scale = y.std()
    if np.any(spread <= 0) or y_scale <= 0:
        raise ValueError("回归描述符和压力目标需要非零方差")
    design = np.column_stack([np.ones(len(x)), (x - center) / spread])
    initial, _, rank, _ = np.linalg.lstsq(design, y / y_scale, rcond=None)
    if rank != 4:
        raise ValueError("回归设计矩阵秩不足")
    link_scale = None
    if link == "softplus":
        def residual(parameters):
            scale = np.exp(parameters[4])
            return scale * np.logaddexp(0, design @ parameters[:4] / scale) - y / y_scale

        # 对链接尺度取对数；边界限制浮点动态范围，不约束工程输入或替代无效预测。
        solution = least_squares(
            residual, np.r_[initial, -2.0],
            bounds=(np.r_[np.full(4, -np.inf), -20.0], np.r_[np.full(4, np.inf), 20.0]),
            max_nfev=2000, ftol=1e-10, xtol=1e-10, gtol=1e-10,
        )
        if not solution.success or solution.active_mask[4]:
            raise ValueError("正值压力回归未收敛到内部解")
        initial = solution.x[:4]
        link_scale = float(np.exp(solution.x[4]) * y_scale)
    coefficients = initial[1:] * y_scale / spread
    intercept = float(initial[0] * y_scale - coefficients @ center)
    return PressureRegression(tuple(float(v) for v in coefficients), intercept, link, link_scale)

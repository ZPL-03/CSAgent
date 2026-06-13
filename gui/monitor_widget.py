"""监控页优化历史与案例 Pareto 看板。"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QColor, QFont, QFontMetrics, QPainter, QPen
from PyQt6.QtWidgets import QFrame, QGridLayout, QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout, QWidget

from core.paths import CASES_DIR
from gui.theme import resolve_theme


@dataclass(frozen=True)
class MonitorCasePoint:
    """监控页使用的正式案例指标。"""

    case_id: str
    weight_kg_per_m2: float
    ultimate_pressure_MPa: float
    linear_buckling_pressure_MPa: float
    length_mm: float
    radius_mm: float
    thickness_mm: float
    alpha_deg: float
    beta_deg: float
    source: str


def _float_value(value: Any, default: float = 0.0) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return default
    if math.isnan(result) or math.isinf(result):
        return default
    return result


def _case_sort_key(path: Path) -> tuple[int, str]:
    stem = path.stem.upper().replace("CASE_", "")
    try:
        return int(stem), path.name
    except ValueError:
        return 10**9, path.name


def load_monitor_case_points(case_dir: Path = CASES_DIR) -> list[MonitorCasePoint]:
    """从正式案例库读取可绘制的真实监控指标。"""

    points: list[MonitorCasePoint] = []
    for path in sorted(case_dir.glob("CASE_*.json"), key=_case_sort_key):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        design = payload.get("design") if isinstance(payload.get("design"), dict) else {}
        geometry = design.get("geometry") if isinstance(design.get("geometry"), dict) else {}
        results = payload.get("abaqus_results") if isinstance(payload.get("abaqus_results"), dict) else {}
        pressure = _float_value(results.get("ultimate_pressure_MPa") or results.get("failure_pressure_MPa"))
        weight = _float_value(results.get("weight_kg_per_m2") or design.get("surrogate_weight"))
        if pressure <= 0.0 or weight <= 0.0:
            continue
        points.append(
            MonitorCasePoint(
                case_id=str(payload.get("case_id") or path.stem),
                weight_kg_per_m2=weight,
                ultimate_pressure_MPa=pressure,
                linear_buckling_pressure_MPa=_float_value(results.get("linear_buckling_pressure_MPa")),
                length_mm=_float_value(geometry.get("length_mm")),
                radius_mm=_float_value(geometry.get("radius_mm")),
                thickness_mm=_float_value(geometry.get("thickness_mm")),
                alpha_deg=_float_value(geometry.get("alpha_deg")),
                beta_deg=_float_value(geometry.get("beta_deg")),
                source=str(design.get("source") or payload.get("source") or "-"),
            )
        )
    return points


def _pareto_front(points: list[MonitorCasePoint]) -> list[MonitorCasePoint]:
    """质量越低越好、极限压力越高越好的二维 Pareto 前沿。"""

    front: list[MonitorCasePoint] = []
    best_pressure = -1.0
    for point in sorted(points, key=lambda item: (item.weight_kg_per_m2, -item.ultimate_pressure_MPa)):
        if point.ultimate_pressure_MPa > best_pressure:
            front.append(point)
            best_pressure = point.ultimate_pressure_MPa
    return front


def _best_point(points: list[MonitorCasePoint]) -> MonitorCasePoint | None:
    if not points:
        return None
    return max(points, key=lambda item: (item.ultimate_pressure_MPa / max(item.weight_kg_per_m2, 1e-6), item.ultimate_pressure_MPa))


class ParetoPlotWidget(QWidget):
    """不依赖外部绘图库的工程监控图。"""

    def __init__(self, mode: str) -> None:
        super().__init__()
        self.mode = mode
        self.theme = "dark"
        self.points: list[MonitorCasePoint] = []
        self.front: list[MonitorCasePoint] = []
        self.best: MonitorCasePoint | None = None
        self.setMinimumHeight(260 if mode == "pareto" else 190)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def set_theme(self, theme: str) -> None:
        self.theme = resolve_theme(theme)
        self.update()

    def set_points(self, points: list[MonitorCasePoint]) -> None:
        self.points = list(points)
        self.front = _pareto_front(self.points)
        self.best = _best_point(self.points)
        self.update()

    def _colors(self) -> dict[str, QColor]:
        if self.theme == "light":
            return {
                "bg": QColor("#ffffff"),
                "panel": QColor("#f8fbff"),
                "border": QColor("#c3cedd"),
                "grid": QColor("#d8e1ec"),
                "text": QColor("#172033"),
                "muted": QColor("#64748b"),
                "point": QColor("#64748b"),
                "line": QColor("#2563eb"),
                "best": QColor("#f59e0b"),
                "good": QColor("#0f766e"),
            }
        return {
            "bg": QColor("#101821"),
            "panel": QColor("#111a28"),
            "border": QColor("#2b3a52"),
            "grid": QColor("#223044"),
            "text": QColor("#dbe4ef"),
            "muted": QColor("#94a3b8"),
            "point": QColor("#64748b"),
            "line": QColor("#3b82f6"),
            "best": QColor("#f59e0b"),
            "good": QColor("#34d399"),
        }

    def paintEvent(self, event) -> None:
        colors = self._colors()
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), colors["bg"])
        panel = QRectF(1, 1, self.width() - 2, self.height() - 2)
        painter.setBrush(colors["panel"])
        painter.setPen(QPen(colors["border"], 1.0))
        painter.drawRoundedRect(panel, 12, 12)

        title = "Pareto 前沿 · 结构面密度 vs 极限压力" if self.mode == "pareto" else "收敛历史 · 当前最优极限压力"
        title_font = QFont(self.font())
        title_font.setPointSize(11)
        title_font.setBold(True)
        painter.setFont(title_font)
        painter.setPen(colors["text"])
        painter.drawText(QRectF(18, 14, self.width() - 36, 24), Qt.AlignmentFlag.AlignLeft, title)

        if not self.points:
            painter.setPen(colors["muted"])
            painter.drawText(QRectF(18, 44, self.width() - 36, self.height() - 62), Qt.AlignmentFlag.AlignCenter, "等待正式案例或 FEM 结果。")
            return

        plot = QRectF(58, 54, max(120, self.width() - 92), max(90, self.height() - 88))
        painter.setPen(QPen(colors["grid"], 1.0))
        for i in range(5):
            x = plot.left() + plot.width() * i / 4
            y = plot.top() + plot.height() * i / 4
            painter.drawLine(QPointF(x, plot.top()), QPointF(x, plot.bottom()))
            painter.drawLine(QPointF(plot.left(), y), QPointF(plot.right(), y))
        painter.setPen(QPen(colors["muted"], 1.4))
        painter.drawLine(plot.bottomLeft(), plot.bottomRight())
        painter.drawLine(plot.bottomLeft(), plot.topLeft())

        if self.mode == "pareto":
            weights = [p.weight_kg_per_m2 for p in self.points]
            pressures = [p.ultimate_pressure_MPa for p in self.points]
            x_min, x_max = min(weights), max(weights)
            y_min, y_max = min(pressures), max(pressures)
            x_pad = max((x_max - x_min) * 0.12, 1.0)
            y_pad = max((y_max - y_min) * 0.12, 1.0)
            x_min -= x_pad
            x_max += x_pad
            y_min -= y_pad
            y_max += y_pad

            def map_point(point: MonitorCasePoint) -> QPointF:
                x = plot.left() + (point.weight_kg_per_m2 - x_min) / max(x_max - x_min, 1e-6) * plot.width()
                y = plot.bottom() - (point.ultimate_pressure_MPa - y_min) / max(y_max - y_min, 1e-6) * plot.height()
                return QPointF(x, y)

            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(colors["point"])
            for point in self.points:
                pt = map_point(point)
                painter.drawEllipse(pt, 3.4, 3.4)

            if len(self.front) >= 2:
                painter.setPen(QPen(colors["line"], 2.0))
                previous = map_point(self.front[0])
                for point in self.front[1:]:
                    current = map_point(point)
                    painter.drawLine(previous, current)
                    previous = current
            for point in self.front:
                pt = map_point(point)
                painter.setPen(QPen(colors["line"], 1.8))
                painter.setBrush(colors["panel"])
                painter.drawEllipse(pt, 5.8, 5.8)
            if self.best:
                best_pt = map_point(self.best)
                painter.setPen(QPen(colors["best"], 2.2))
                painter.setBrush(colors["panel"])
                painter.drawEllipse(best_pt, 7.2, 7.2)
                self._draw_annotation(painter, colors, best_pt, self.best)

            self._draw_axis_labels(painter, colors, plot, "结构面密度 kg/m²", "极限压力 MPa")
            return

        best_history: list[tuple[int, float]] = []
        current_best = -1.0
        for index, point in enumerate(self.points, start=1):
            current_best = max(current_best, point.ultimate_pressure_MPa)
            best_history.append((index, current_best))
        y_values = [value for _index, value in best_history]
        y_min, y_max = min(y_values), max(y_values)
        y_pad = max((y_max - y_min) * 0.12, 1.0)
        y_min -= y_pad
        y_max += y_pad

        def map_history(index: int, value: float) -> QPointF:
            x = plot.left() + (index - 1) / max(len(best_history) - 1, 1) * plot.width()
            y = plot.bottom() - (value - y_min) / max(y_max - y_min, 1e-6) * plot.height()
            return QPointF(x, y)

        painter.setPen(QPen(colors["line"], 2.0))
        previous: QPointF | None = None
        for index, value in best_history:
            current = map_history(index, value)
            if previous is not None:
                painter.drawLine(previous, current)
            previous = current
            painter.setBrush(colors["line"])
            painter.drawEllipse(current, 4.4, 4.4)
        if best_history:
            last = map_history(*best_history[-1])
            painter.setPen(colors["best"])
            painter.drawText(QRectF(last.x() - 80, last.y() - 30, 96, 22), Qt.AlignmentFlag.AlignRight, f"{best_history[-1][1]:.2f} MPa")
        self._draw_axis_labels(painter, colors, plot, "案例序号", "当前最优 MPa")

    def _draw_axis_labels(self, painter: QPainter, colors: dict[str, QColor], plot: QRectF, x_label: str, y_label: str) -> None:
        small_font = QFont(self.font())
        small_font.setPointSize(8)
        painter.setFont(small_font)
        painter.setPen(colors["muted"])
        painter.drawText(QRectF(plot.left(), plot.bottom() + 8, plot.width(), 18), Qt.AlignmentFlag.AlignCenter, x_label)
        painter.save()
        painter.translate(16, plot.center().y() + 40)
        painter.rotate(-90)
        painter.drawText(QRectF(0, 0, 120, 18), Qt.AlignmentFlag.AlignCenter, y_label)
        painter.restore()

    def _draw_annotation(self, painter: QPainter, colors: dict[str, QColor], point: QPointF, best: MonitorCasePoint) -> None:
        text = f"{best.case_id} · {best.ultimate_pressure_MPa:.2f} MPa · {best.weight_kg_per_m2:.2f} kg/m²"
        metrics = QFontMetrics(self.font())
        width = min(max(metrics.horizontalAdvance(text) + 24, 180), 330)
        rect = QRectF(min(point.x() + 16, self.width() - width - 18), max(44, point.y() - 52), width, 42)
        painter.setBrush(colors["panel"])
        painter.setPen(QPen(colors["best"], 1.6))
        painter.drawRoundedRect(rect, 8, 8)
        painter.setPen(colors["text"])
        painter.drawText(rect.adjusted(12, 6, -12, -6), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, text)


class MonitorDashboardWidget(QWidget):
    """面向真实案例库的监控页中心看板。"""

    def __init__(self) -> None:
        super().__init__()
        self.theme = "dark"
        self.points: list[MonitorCasePoint] = []
        self.pareto_plot = ParetoPlotWidget("pareto")
        self.convergence_plot = ParetoPlotWidget("convergence")
        self.summary_label = QLabel()
        self.summary_label.setObjectName("statusLabel")
        self.summary_label.setWordWrap(True)
        self.best_card = self._metric_card("当前最优", "-")
        self.mass_card = self._metric_card("结构面密度", "-")
        self.buckling_card = self._metric_card("线性屈曲", "-")
        self.case_card = self._metric_card("正式案例", "-")

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(10)
        root.addWidget(self.pareto_plot, 3)
        root.addWidget(self.convergence_plot, 2)
        cards = QGridLayout()
        cards.setContentsMargins(0, 0, 0, 0)
        cards.setHorizontalSpacing(10)
        cards.setVerticalSpacing(10)
        for index, card in enumerate([self.best_card, self.mass_card, self.buckling_card, self.case_card]):
            cards.addWidget(card, 0, index)
            cards.setColumnStretch(index, 1)
        root.addLayout(cards)
        root.addWidget(self.summary_label)
        self.refresh()

    def set_theme(self, theme: str) -> None:
        self.theme = resolve_theme(theme)
        self.pareto_plot.set_theme(theme)
        self.convergence_plot.set_theme(theme)

    def refresh(self) -> None:
        self.points = load_monitor_case_points()
        self.pareto_plot.set_points(self.points)
        self.convergence_plot.set_points(self.points)
        best = _best_point(self.points)
        front = _pareto_front(self.points)
        if best is None:
            self._set_card(self.best_card, "当前最优", "-", "等待正式案例")
            self._set_card(self.mass_card, "结构面密度", "-", "等待 FEM 回流")
            self._set_card(self.buckling_card, "线性屈曲", "-", "等待结果")
            self._set_card(self.case_card, "正式案例", "0", "案例库暂无可绘制指标")
            self.summary_label.setText("监控页读取正式案例库和 FEM 结果；没有真实数据时不绘制假 Pareto。")
            return
        self._set_card(self.best_card, "当前最优", f"{best.ultimate_pressure_MPa:.2f} MPa", best.case_id)
        self._set_card(self.mass_card, "结构面密度", f"{best.weight_kg_per_m2:.2f} kg/m²", "越低越好")
        self._set_card(self.buckling_card, "线性屈曲", f"{best.linear_buckling_pressure_MPa:.2f} MPa", "FEM 线性阶段")
        self._set_card(self.case_card, "正式案例", str(len(self.points)), f"Pareto 前沿 {len(front)} 个")
        self.summary_label.setText(
            " · ".join(
                [
                    f"累计读取 {len(self.points)} 个有 FEM 指标的正式案例",
                    f"Pareto 前沿 {len(front)} 个",
                    f"最优方案 {best.case_id}",
                    f"L={best.length_mm:.1f} mm / R={best.radius_mm:.1f} mm / t={best.thickness_mm:.2f} mm",
                ]
            )
        )

    def _metric_card(self, title: str, value: str) -> QFrame:
        frame = QFrame()
        frame.setObjectName("configCard")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(4)
        title_label = QLabel(title)
        title_label.setObjectName("configSubtitle")
        value_label = QLabel(value)
        value_label.setObjectName("configTitle")
        detail_label = QLabel("-")
        detail_label.setObjectName("configSubtitle")
        detail_label.setWordWrap(True)
        layout.addWidget(title_label)
        layout.addWidget(value_label)
        layout.addWidget(detail_label)
        frame.setProperty("title_label", title_label)
        frame.setProperty("value_label", value_label)
        frame.setProperty("detail_label", detail_label)
        return frame

    def _set_card(self, frame: QFrame, title: str, value: str, detail: str) -> None:
        title_label = frame.property("title_label")
        value_label = frame.property("value_label")
        detail_label = frame.property("detail_label")
        if isinstance(title_label, QLabel):
            title_label.setText(title)
        if isinstance(value_label, QLabel):
            value_label.setText(value)
        if isinstance(detail_label, QLabel):
            detail_label.setText(detail)

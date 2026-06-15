"""知识库上传、入库、检索和证据展示组件。"""

from __future__ import annotations

import gzip
import json
import math
from dataclasses import asdict
from html import escape
from pathlib import Path
from typing import Any

from PyQt6.QtCore import QLineF, QObject, QPointF, QRectF, QSize, QThread, Qt, pyqtSignal
from PyQt6.QtGui import QBrush, QColor, QFont, QFontMetrics, QPainter, QPainterPath, QPen, QPolygonF
from PyQt6.QtWidgets import (
    QFileDialog,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QFrame,
    QSizePolicy,
    QSplitter,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from core.case_memory import CaseMemoryIndex
from core.domain_knowledge import DomainKnowledgeBase
from core.knowledge_ingestion import KnowledgeIngestionService, SUPPORTED_QT_FILE_FILTER
from core.paths import ABAQUS_RUNS_DIR, CASES_DIR, CASE_LIBRARY_DIR, MODELS_DIR
from gui.theme import resolve_theme
from gui.workbench_widgets import PipelineStatusWidget, StatusPill


DEFAULT_EVIDENCE_QUERY = "复合材料外压圆柱耐压壳 外部静水压力 线性屈曲 极限压力 初始缺陷 制造质量控制"


class KnowledgeGraphView(QWidget):
    """运行时知识图谱可视化画布。"""

    nodeSelected = pyqtSignal(str)

    def __init__(self) -> None:
        super().__init__()
        self.theme = "dark"
        self.entities: list[dict[str, Any]] = []
        self.relations: list[dict[str, Any]] = []
        self.highlight_relations: list[dict[str, Any]] = []
        self.filter_text = ""
        self.show_labels = True
        self._scale = 1.0
        self._pan = QPointF(0.0, 0.0)
        self._drag_start: QPointF | None = None
        self._drag_pan_start = QPointF(0.0, 0.0)
        self._drag_node_name: str | None = None
        self._drag_node_start = QPointF(0.0, 0.0)
        self._node_offset_start = QPointF(0.0, 0.0)
        self._manual_node_offsets: dict[str, QPointF] = {}
        self._last_node_positions: dict[str, QPointF] = {}
        self._last_node_radii: dict[str, float] = {}
        self._selected_node_name = ""
        self.setMinimumHeight(300)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMouseTracking(True)

    def sizeHint(self) -> QSize:
        return QSize(760, 380)

    def set_theme(self, theme: str) -> None:
        self.theme = resolve_theme(theme)
        self.update()

    def set_graph(
        self,
        entities: list[dict[str, Any]],
        relations: list[dict[str, Any]],
        highlight_relations: list[dict[str, Any]] | None = None,
    ) -> None:
        self.entities = list(entities)
        self.relations = list(relations)
        self.highlight_relations = list(highlight_relations or [])
        available_names = {str(entity.get("name") or "").strip() for entity in self.entities}
        available_names.update(str(relation.get("source") or "").strip() for relation in self.relations)
        available_names.update(str(relation.get("target") or "").strip() for relation in self.relations)
        if self._selected_node_name and self._selected_node_name not in available_names:
            self._selected_node_name = ""
            self.nodeSelected.emit("")
        self.update()

    def set_filter_text(self, value: str) -> None:
        """设置图谱节点过滤词。"""

        self.filter_text = str(value or "").strip().lower()
        if self._selected_node_name:
            self._selected_node_name = ""
            self.nodeSelected.emit("")
        self.update()

    def reset_view(self) -> None:
        """恢复图谱默认视角。"""

        self._scale = 1.0
        self._pan = QPointF(0.0, 0.0)
        self._manual_node_offsets.clear()
        self.update()

    def selected_node_name(self) -> str:
        """返回当前选中的图谱节点名称。"""

        return self._selected_node_name

    def zoom_by(self, factor: float) -> None:
        """按比例缩放图谱画布。"""

        self._scale = max(0.55, min(2.4, self._scale * factor))
        self.update()

    def set_show_labels(self, enabled: bool) -> None:
        """设置节点标签显示状态。"""

        self.show_labels = bool(enabled)
        self.update()

    def _colors(self) -> dict[str, QColor]:
        if self.theme == "light":
            return {
                "bg": QColor("#ffffff"),
                "panel": QColor("#f8fbff"),
                "border": QColor("#c3cedd"),
                "text": QColor("#172033"),
                "muted": QColor("#64748b"),
                "edge": QColor("#8aa0ba"),
                "highlight": QColor("#8b5cf6"),
                "grid": QColor(100, 116, 139, 28),
                "label_bg": QColor(255, 255, 255, 205),
                "selected": QColor("#0f766e"),
            }
        return {
            "bg": QColor("#101821"),
            "panel": QColor("#111a28"),
            "border": QColor("#2b3a52"),
            "text": QColor("#dbe4ef"),
            "muted": QColor("#94a3b8"),
                "edge": QColor("#52647e"),
            "highlight": QColor("#a78bfa"),
            "grid": QColor(148, 163, 184, 24),
            "label_bg": QColor(15, 23, 42, 210),
            "selected": QColor("#38bdf8"),
        }

    def _type_color(self, entity_type: str) -> QColor:
        palette = {
            "Application": "#0087a8",
            "DesignVariable": "#b05f6d",
            "Material": "#38bdf8",
            "Structure": "#34d399",
            "FailureMode": "#f59e0b",
            "DesignFormula": "#a78bfa",
            "LoadCase": "#c05a9d",
            "Property": "#d08a00",
            "Standard": "#7b61ff",
            "StiffnessCoeff": "#5c6ac4",
            "TaskCategory": "#6a7a89",
            "Literature": "#8c6f47",
            "VerificationMethod": "#60a5fa",
            "ManufacturingProcess": "#fb7185",
        }
        return QColor(palette.get(entity_type, "#64748b"))

    def _entity_counts(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for entity in self.entities:
            name = str(entity.get("name") or "").strip()
            if not name:
                continue
            try:
                counts[name] = max(1, int(entity.get("count") or 1))
            except (TypeError, ValueError):
                counts[name] = 1
        return counts

    def _node_payload(self) -> tuple[list[tuple[str, str]], list[dict[str, Any]], int, int]:
        node_types: dict[str, str] = {}
        for entity in self.entities:
            name = str(entity.get("name") or "").strip()
            if name:
                node_types[name] = str(entity.get("type") or "Entity")
        for relation in self.relations:
            source = str(relation.get("source") or "").strip()
            target = str(relation.get("target") or "").strip()
            if source:
                node_types.setdefault(source, str(relation.get("source_type") or "Entity"))
            if target:
                node_types.setdefault(target, str(relation.get("target_type") or "Entity"))
        degree: dict[str, int] = {name: 0 for name in node_types}
        for relation in self.relations:
            source = str(relation.get("source") or "").strip()
            target = str(relation.get("target") or "").strip()
            if source in degree:
                degree[source] += 1
            if target in degree:
                degree[target] += 1
        counts = self._entity_counts()
        sorted_nodes = sorted(
            node_types.items(),
            key=lambda item: (-(math.log1p(counts.get(item[0], 1)) + degree.get(item[0], 0) * 2.0), item[1], item[0]),
        )
        if self.filter_text:
            seed_names = {
                name
                for name, entity_type in sorted_nodes
                if self.filter_text in name.lower() or self.filter_text in entity_type.lower()
            }
            neighbor_names: set[str] = set(seed_names)
            for relation in self.relations:
                source = str(relation.get("source") or "").strip()
                target = str(relation.get("target") or "").strip()
                relation_name = str(relation.get("relation") or "").strip().lower()
                if source in seed_names or target in seed_names or self.filter_text in relation_name:
                    if source:
                        neighbor_names.add(source)
                    if target:
                        neighbor_names.add(target)
            sorted_nodes = [item for item in sorted_nodes if item[0] in neighbor_names]
        max_nodes = 42
        visible_nodes = sorted_nodes[:max_nodes]
        visible_names = {name for name, _ in visible_nodes}
        visible_relations = [
            relation
            for relation in self.relations
            if str(relation.get("source") or "") in visible_names and str(relation.get("target") or "") in visible_names
        ]
        visible_relations.sort(
            key=lambda relation: (
                -(
                    degree.get(str(relation.get("source") or ""), 0)
                    + degree.get(str(relation.get("target") or ""), 0)
                ),
                str(relation.get("relation") or ""),
            )
        )
        visible_relations = visible_relations[:56]
        return visible_nodes, visible_relations, len(node_types), len(self.relations)

    def _visible_degrees(self, relations: list[dict[str, Any]]) -> dict[str, int]:
        degrees: dict[str, int] = {}
        for relation in relations:
            source = str(relation.get("source") or "").strip()
            target = str(relation.get("target") or "").strip()
            if source:
                degrees[source] = degrees.get(source, 0) + 1
            if target:
                degrees[target] = degrees.get(target, 0) + 1
        return degrees

    def _node_weight(self, name: str, degrees: dict[str, int], counts: dict[str, int]) -> float:
        return math.log1p(counts.get(name, 1)) + degrees.get(name, 0) * 1.8

    def _node_radius(self, name: str, degrees: dict[str, int], counts: dict[str, int]) -> float:
        weight = self._node_weight(name, degrees, counts)
        return max(6.0, min(16.0, 6.0 + math.sqrt(max(weight, 1.0)) * 2.1))

    def _layout_positions(
        self,
        visible_nodes: list[tuple[str, str]],
        visible_relations: list[dict[str, Any]],
        graph_rect: QRectF,
    ) -> dict[str, QPointF]:
        if not visible_nodes:
            return {}

        degrees = self._visible_degrees(visible_relations)
        counts = self._entity_counts()
        node_map = {name: entity_type for name, entity_type in visible_nodes}
        adjacency: dict[str, set[str]] = {name: set() for name in node_map}
        for relation in visible_relations:
            source = str(relation.get("source") or "").strip()
            target = str(relation.get("target") or "").strip()
            if source in adjacency and target in adjacency:
                adjacency[source].add(target)
                adjacency[target].add(source)

        seen: set[str] = set()
        components: list[list[tuple[str, str]]] = []
        for name, entity_type in sorted(
            visible_nodes,
            key=lambda item: (-self._node_weight(item[0], degrees, counts), item[1], item[0]),
        ):
            if name in seen:
                continue
            stack = [name]
            seen.add(name)
            component: list[tuple[str, str]] = []
            while stack:
                current = stack.pop()
                component.append((current, node_map[current]))
                for neighbor in sorted(adjacency.get(current, set())):
                    if neighbor not in seen:
                        seen.add(neighbor)
                        stack.append(neighbor)
            components.append(component)

        components.sort(key=lambda item: (-len(item), -sum(degrees.get(name, 0) for name, _ in item)))
        positions: dict[str, QPointF] = {}
        graph_center = QPointF(graph_rect.center().x() + self._pan.x(), graph_rect.center().y() + self._pan.y())

        def place_component(component: list[tuple[str, str]], center: QPointF, rx: float, ry: float, phase: float = 0.0) -> None:
            ranked = sorted(component, key=lambda item: (-self._node_weight(item[0], degrees, counts), item[1], item[0]))
            if not ranked:
                return
            core_name = ranked[0][0]
            positions[core_name] = center + self._manual_node_offsets.get(core_name, QPointF(0.0, 0.0))
            remaining = ranked[1:]
            if not remaining:
                return
            ring_sizes = [10, 18, 30]
            start = 0
            for ring_index, capacity in enumerate(ring_sizes):
                ring_nodes = remaining[start : start + capacity]
                if not ring_nodes:
                    break
                start += len(ring_nodes)
                ring_rx = rx * (0.48 + ring_index * 0.28)
                ring_ry = ry * (0.48 + ring_index * 0.28)
                for index, (name, _entity_type) in enumerate(ring_nodes):
                    angle = -math.pi / 2.0 + phase + ring_index * 0.18 + 2.0 * math.pi * index / len(ring_nodes)
                    offset = self._manual_node_offsets.get(name, QPointF(0.0, 0.0))
                    positions[name] = QPointF(
                        center.x() + ring_rx * math.cos(angle) + offset.x(),
                        center.y() + ring_ry * math.sin(angle) + offset.y(),
                    )

        main_component = components[0]
        has_side_components = len(components) > 1 and graph_rect.width() >= 520
        main_center = QPointF(graph_center.x() - (graph_rect.width() * 0.08 if has_side_components else 0), graph_center.y())
        main_rx = max(96.0, graph_rect.width() * (0.30 if has_side_components else 0.40)) * self._scale
        main_ry = max(66.0, graph_rect.height() * 0.36) * self._scale
        place_component(main_component, main_center, main_rx, main_ry)

        small_components = components[1:]
        if small_components:
            columns = max(1, min(3, int(math.ceil(math.sqrt(len(small_components))))))
            if has_side_components:
                cell_width = max(116.0, graph_rect.width() * 0.16)
                cell_height = max(86.0, graph_rect.height() * 0.22)
                start_x = graph_rect.right() - cell_width * columns + cell_width * 0.52 + self._pan.x()
                start_y = graph_center.y() - cell_height * max(0.0, math.ceil(len(small_components) / columns) - 1) * 0.5
                for index, component in enumerate(small_components):
                    column = index % columns
                    row = index // columns
                    center = QPointF(start_x + column * cell_width, start_y + row * cell_height)
                    place_component(component, center, cell_width * 0.36 * self._scale, cell_height * 0.34 * self._scale, phase=0.28)
            else:
                outer_rx = max(78.0, graph_rect.width() * 0.36) * self._scale
                outer_ry = max(52.0, graph_rect.height() * 0.32) * self._scale
                for index, component in enumerate(small_components):
                    angle = -math.pi / 2.0 + 2.0 * math.pi * index / max(1, len(small_components))
                    center = QPointF(graph_center.x() + outer_rx * math.cos(angle), graph_center.y() + outer_ry * math.sin(angle))
                    place_component(component, center, 38.0 * self._scale, 30.0 * self._scale, phase=0.28)
        return positions

    def _draw_grid(self, painter: QPainter, rect: QRectF, color: QColor) -> None:
        painter.save()
        painter.setClipRect(rect)
        painter.setPen(QPen(color, 1.0))
        spacing = 30
        x = int(rect.left()) - int(rect.left()) % spacing
        while x <= rect.right():
            painter.drawLine(QPointF(x, rect.top()), QPointF(x, rect.bottom()))
            x += spacing
        y = int(rect.top()) - int(rect.top()) % spacing
        while y <= rect.bottom():
            painter.drawLine(QPointF(rect.left(), y), QPointF(rect.right(), y))
            y += spacing
        painter.restore()

    def _draw_edge(
        self,
        painter: QPainter,
        source: QPointF,
        target: QPointF,
        color: QColor,
        highlight: bool,
    ) -> None:
        line = QLineF(source, target)
        if line.length() < 2:
            return
        dx = target.x() - source.x()
        dy = target.y() - source.y()
        length = max(1.0, math.hypot(dx, dy))
        normal = QPointF(-dy / length, dx / length)
        curve = 18.0 if not highlight else 28.0
        control = QPointF((source.x() + target.x()) / 2.0 + normal.x() * curve, (source.y() + target.y()) / 2.0 + normal.y() * curve)

        painter.setPen(QPen(color, 2.0 if highlight else 1.05, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        path = QPainterPath(source)
        path.quadTo(control, target)
        painter.drawPath(path)

        arrow_len = 7.0 if highlight else 5.6
        angle = math.atan2(target.y() - control.y(), target.x() - control.x())
        arrow = QPolygonF(
            [
                target,
                QPointF(target.x() - arrow_len * math.cos(angle - 0.42), target.y() - arrow_len * math.sin(angle - 0.42)),
                QPointF(target.x() - arrow_len * math.cos(angle + 0.42), target.y() - arrow_len * math.sin(angle + 0.42)),
            ]
        )
        painter.setBrush(QBrush(color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawPolygon(arrow)

    def _draw_label(
        self,
        painter: QPainter,
        name: str,
        point: QPointF,
        radius: float,
        graph_rect: QRectF,
        colors: dict[str, QColor],
        font: QFont,
        metrics: QFontMetrics,
        occupied: list[QRectF] | None = None,
        force: bool = False,
    ) -> bool:
        label = metrics.elidedText(name, Qt.TextElideMode.ElideRight, 116)
        width = min(124.0, max(48.0, float(metrics.horizontalAdvance(label) + 14)))
        height = 20.0
        x = point.x() - width / 2.0
        y = point.y() + radius + 5.0
        if y + height > graph_rect.bottom():
            y = point.y() - radius - height - 5.0
        x = min(max(x, graph_rect.left() + 2.0), graph_rect.right() - width - 2.0)
        label_rect = QRectF(x, y, width, height)
        if occupied is not None and not force:
            padded_rect = label_rect.adjusted(-5, -4, 5, 4)
            if any(padded_rect.intersects(existing) for existing in occupied):
                return False
        painter.setBrush(QBrush(colors["label_bg"]))
        painter.setPen(QPen(colors["border"], 0.8))
        painter.drawRoundedRect(label_rect, 5, 5)
        painter.setFont(font)
        painter.setPen(colors["text"])
        painter.drawText(label_rect.adjusted(6, 0, -6, 0), Qt.AlignmentFlag.AlignCenter, label)
        if occupied is not None:
            occupied.append(label_rect.adjusted(-5, -4, 5, 4))
        return True

    def _draw_legend(self, painter: QPainter, visible_nodes: list[tuple[str, str]], colors: dict[str, QColor]) -> None:
        type_counts: dict[str, int] = {}
        for _name, entity_type in visible_nodes:
            type_counts[entity_type] = type_counts.get(entity_type, 0) + 1
        items = sorted(type_counts.items(), key=lambda item: (-item[1], item[0]))[:4]
        if not items or self.width() < 620:
            return
        font = QFont(self.font())
        font.setPointSize(8)
        painter.setFont(font)
        metrics = QFontMetrics(font)
        x = self.width() - 18.0
        y = 14.0
        for entity_type, count in reversed(items):
            label = f"{entity_type} {count}"
            width = metrics.horizontalAdvance(label) + 22
            x -= width
            rect = QRectF(x, y, width - 6, 20)
            painter.setBrush(QBrush(colors["label_bg"]))
            painter.setPen(QPen(colors["border"], 0.8))
            painter.drawRoundedRect(rect, 6, 6)
            painter.setBrush(QBrush(self._type_color(entity_type)))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(QPointF(rect.left() + 9, rect.center().y()), 4.0, 4.0)
            painter.setPen(colors["muted"])
            painter.drawText(rect.adjusted(18, 0, -4, 0), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, label)

    def paintEvent(self, event) -> None:
        colors = self._colors()
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), colors["bg"])

        panel = QRectF(1, 1, self.width() - 2, self.height() - 2)
        painter.setBrush(QBrush(colors["panel"]))
        painter.setPen(QPen(colors["border"], 1.0))
        painter.drawRoundedRect(panel, 12, 12)
        graph_rect = panel.adjusted(16, 42, -16, -18)
        self._draw_grid(painter, graph_rect, colors["grid"])

        visible_nodes, visible_relations, total_nodes, total_relations = self._node_payload()
        subtitle = f"核心图谱 · 实体 {total_nodes} · 关系 {total_relations}"
        if total_nodes > len(visible_nodes) or total_relations > len(visible_relations):
            subtitle += f" · 显示核心子图 {len(visible_nodes)} / {len(visible_relations)}"
        small_font = QFont(self.font())
        small_font.setPointSize(9)
        small_font.setBold(True)
        painter.setFont(small_font)
        painter.setPen(colors["muted"])
        painter.drawText(QRectF(16, 12, self.width() - 32, 20), Qt.AlignmentFlag.AlignLeft, subtitle)
        self._draw_legend(painter, visible_nodes, colors)

        if not visible_nodes:
            painter.drawText(
                graph_rect,
                Qt.AlignmentFlag.AlignCenter,
                "知识图谱等待资料入库或检索命中。",
            )
            return

        positions = self._layout_positions(visible_nodes, visible_relations, graph_rect)
        self._last_node_positions = positions
        degrees = self._visible_degrees(visible_relations)
        counts = self._entity_counts()

        highlighted = {
            (
                str(relation.get("source") or ""),
                str(relation.get("relation") or ""),
                str(relation.get("target") or ""),
            )
            for relation in self.highlight_relations
        }
        for relation in visible_relations:
            source = str(relation.get("source") or "")
            target = str(relation.get("target") or "")
            if source not in positions or target not in positions:
                continue
            key = (source, str(relation.get("relation") or ""), target)
            selected_edge = bool(self._selected_node_name and self._selected_node_name in {source, target})
            edge_color = colors["highlight"] if key in highlighted or selected_edge else colors["edge"]
            edge_color.setAlpha(218 if key in highlighted else (154 if selected_edge else 54))
            self._draw_edge(painter, positions[source], positions[target], edge_color, key in highlighted or selected_edge)

        label_font = QFont(self.font())
        label_font.setPointSize(8)
        label_font.setBold(True)
        label_metrics = QFontMetrics(label_font)
        ranked_label_names = {
            name
            for name, _entity_type in sorted(
                visible_nodes,
                key=lambda item: (-self._node_weight(item[0], degrees, counts), item[1], item[0]),
            )[:7]
        }
        self._last_node_radii = {}
        occupied_label_rects: list[QRectF] = []
        for name, entity_type in visible_nodes:
            point = positions[name]
            color = self._type_color(entity_type)
            radius = self._node_radius(name, degrees, counts)
            if self.filter_text and self.filter_text in name.lower():
                radius += 2.0
            self._last_node_radii[name] = radius
            is_selected = name == self._selected_node_name
            if is_selected:
                halo = QColor(colors["selected"])
                halo.setAlpha(74)
                painter.setBrush(QBrush(halo))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawEllipse(point, radius + 8.0, radius + 8.0)
            painter.setBrush(QBrush(color))
            painter.setPen(QPen(colors["selected"] if is_selected or name in ranked_label_names else colors["panel"], 2.6 if is_selected else 1.8))
            painter.drawEllipse(point, radius, radius)
            should_label = is_selected or (self.show_labels and name in ranked_label_names) or (
                self.filter_text and self.filter_text in name.lower()
            )
            if should_label:
                self._draw_label(
                    painter,
                    name,
                    point,
                    radius,
                    graph_rect,
                    colors,
                    label_font,
                    label_metrics,
                    occupied_label_rects,
                    force=is_selected,
                )

    def wheelEvent(self, event) -> None:
        old_scale = self._scale
        factor = 1.12 if event.angleDelta().y() > 0 else 1 / 1.12
        self._scale = max(0.55, min(2.4, self._scale * factor))
        if self._scale != old_scale:
            cursor = event.position()
            center = QPointF(self.width() / 2.0, self.height() / 2.0 + 8)
            before = QPointF(
                (cursor.x() - center.x() - self._pan.x()) / old_scale,
                (cursor.y() - center.y() - self._pan.y()) / old_scale,
            )
            self._pan = QPointF(
                cursor.x() - center.x() - before.x() * self._scale,
                cursor.y() - center.y() - before.y() * self._scale,
            )
            self.update()
        event.accept()

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            hovered = self._hovered_node(event.position())
            if hovered:
                self._selected_node_name = hovered
                self.nodeSelected.emit(hovered)
                self._drag_node_name = hovered
                self._drag_node_start = event.position()
                self._node_offset_start = QPointF(self._manual_node_offsets.get(hovered, QPointF(0.0, 0.0)))
            else:
                self._drag_start = event.position()
                self._drag_pan_start = QPointF(self._pan)
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        if self._drag_node_name is not None:
            delta = event.position() - self._drag_node_start
            self._manual_node_offsets[self._drag_node_name] = QPointF(
                self._node_offset_start.x() + delta.x(),
                self._node_offset_start.y() + delta.y(),
            )
            self.update()
            event.accept()
            return
        if self._drag_start is not None:
            delta = event.position() - self._drag_start
            self._pan = QPointF(self._drag_pan_start.x() + delta.x(), self._drag_pan_start.y() + delta.y())
            self.update()
            event.accept()
            return
        hovered = self._hovered_node(event.position())
        self.setToolTip(hovered or "")
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton and self._drag_node_name is not None:
            self._drag_node_name = None
            self.setCursor(Qt.CursorShape.ArrowCursor)
            event.accept()
            return
        if event.button() == Qt.MouseButton.LeftButton and self._drag_start is not None:
            self._drag_start = None
            self.setCursor(Qt.CursorShape.ArrowCursor)
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.reset_view()
            event.accept()
            return
        super().mouseDoubleClickEvent(event)

    def _hovered_node(self, point: QPointF) -> str:
        for name, position in self._last_node_positions.items():
            dx = point.x() - position.x()
            dy = point.y() - position.y()
            radius = max(18.0, self._last_node_radii.get(name, 8.0) + 8.0)
            if dx * dx + dy * dy <= radius * radius:
                return name
        return ""


class KnowledgeIngestWorker(QObject):
    """在后台线程执行资料入库。"""

    progress = pyqtSignal(list)
    finished = pyqtSignal(dict)
    failed = pyqtSignal(str)

    def __init__(self, paths: str | list[str]) -> None:
        super().__init__()
        if isinstance(paths, str):
            self.paths = [paths]
        else:
            self.paths = [str(path) for path in paths]

    def run(self) -> None:
        results: list[dict[str, Any]] = []
        failures: list[dict[str, str]] = []
        service = KnowledgeIngestionService(progress_callback=self.progress.emit)
        for path in self.paths:
            if not path:
                continue
            try:
                result = service.ingest_file(path)
            except Exception as exc:
                failures.append({"path": path, "error": str(exc)})
                continue
            payload = asdict(result)
            payload["success"] = result.success
            results.append(payload)
        if not results and failures:
            self.failed.emit("；".join(f"{Path(item['path']).name}: {item['error']}" for item in failures))
            return
        self.finished.emit(
            {
                "success": not failures,
                "results": results,
                "failures": failures,
                "batch_total": len([path for path in self.paths if path]),
                "batch_success_count": len(results),
                "batch_failed_count": len(failures),
            }
        )


class KnowledgeMaintenanceWorker(QObject):
    """在后台线程执行知识库维护操作。"""

    finished = pyqtSignal(dict)
    failed = pyqtSignal(str)

    def __init__(self, operation: str) -> None:
        super().__init__()
        self.operation = operation

    def run(self) -> None:
        try:
            service = KnowledgeIngestionService()
            if self.operation == "rebuild":
                self.finished.emit({"operation": self.operation, "result": service.rebuild_indexes()})
                return
            if self.operation == "export":
                path = service.export_snapshot()
                self.finished.emit({"operation": self.operation, "path": str(path)})
                return
            raise RuntimeError(f"未知知识库维护操作：{self.operation}")
        except Exception as exc:
            self.failed.emit(str(exc))


class KnowledgeWidget(QWidget):
    """管理项目内可更新 RAG/KG 知识库并展示检索证据。"""

    def __init__(self) -> None:
        super().__init__()
        self.knowledge_base = DomainKnowledgeBase()
        self.ingestion_service = KnowledgeIngestionService()
        self.theme = "dark"
        self._last_task: dict[str, Any] | None = None
        self._ingest_thread: QThread | None = None
        self._ingest_worker: KnowledgeIngestWorker | None = None
        self._maintenance_thread: QThread | None = None
        self._maintenance_worker: KnowledgeMaintenanceWorker | None = None

        self.store_pill = StatusPill("知识库待入库", "pending")
        self.rag_pill = StatusPill("RAG 0 文本块", "pending")
        self.vector_pill = StatusPill("Vector 0 向量块", "pending")
        self.kg_pill = StatusPill("KG 0 关系", "pending")
        self.parser_pill = StatusPill("解析器待调用", "pending")

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索知识库：外压圆柱壳 屈曲 缺陷敏感性 制造质量")
        self.search_button = QPushButton("执行混合检索")
        self.upload_button = QPushButton("上传资料并入库")
        self.batch_button = QPushButton("批量解析")
        self.rebuild_button = QPushButton("重建索引")
        self.export_snapshot_button = QPushButton("导出快照")
        self.refresh_button = QPushButton("刷新状态")

        self.document_table = QTableWidget(0, 6)
        self.document_table.setHorizontalHeaderLabels(["文档", "解析器", "Chunk", "SHA256", "入库时间", "路径"])
        self.document_table.setAlternatingRowColors(True)
        self.document_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for section in range(1, 5):
            self.document_table.horizontalHeader().setSectionResizeMode(section, QHeaderView.ResizeMode.ResizeToContents)
        self.document_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        self.document_table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.document_empty_state = QFrame()
        self.document_empty_state.setObjectName("settingsCard")
        empty_layout = QVBoxLayout(self.document_empty_state)
        empty_layout.setContentsMargins(18, 14, 18, 14)
        empty_layout.setSpacing(8)
        empty_title = QLabel("资料库等待入库")
        empty_title.setObjectName("sectionTitle")
        empty_body = QLabel("上传资料并入库后，这里显示解析器、Chunk、SHA256、入库时间和路径。")
        empty_body.setWordWrap(True)
        empty_hint = QLabel("支持解析、token 分块、overlap、内容去重、向量索引和 KG 实体关系抽取。")
        empty_hint.setObjectName("chatStatus")
        empty_hint.setWordWrap(True)
        empty_layout.addWidget(empty_title)
        empty_layout.addWidget(empty_body)
        empty_layout.addWidget(empty_hint)
        self.document_empty_state.setMinimumHeight(96)
        self.document_empty_state.setMaximumHeight(126)
        empty_page = QWidget()
        empty_page_layout = QVBoxLayout(empty_page)
        empty_page_layout.setContentsMargins(0, 0, 0, 0)
        empty_page_layout.setSpacing(0)
        empty_page_layout.addWidget(self.document_empty_state, 0, Qt.AlignmentFlag.AlignTop)
        self.document_stack = QStackedWidget()
        self.document_stack.addWidget(empty_page)
        self.document_stack.addWidget(self.document_table)
        self.document_stack.setMinimumHeight(116)

        self.source_overview_browser = QTextBrowser()
        self.source_overview_browser.setOpenExternalLinks(True)
        self.source_overview_browser.setMaximumHeight(126)
        self.source_overview_browser.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.source_overview_browser.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.source_overview_browser.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.pipeline_widget = PipelineStatusWidget()
        self.pipeline_widget.setMinimumHeight(238)
        self.pipeline_widget.setMaximumHeight(276)
        self.graph_view = KnowledgeGraphView()
        self.graph_view.setMinimumHeight(330)
        self.graph_search_input = QLineEdit()
        self.graph_search_input.setPlaceholderText("搜索图谱节点或关系")
        self.graph_reset_button = QPushButton("F")
        self.graph_reset_button.setToolTip("适配图谱")
        self.graph_zoom_in_button = QPushButton("+")
        self.graph_zoom_in_button.setToolTip("放大图谱")
        self.graph_zoom_out_button = QPushButton("−")
        self.graph_zoom_out_button.setToolTip("缩小图谱")
        self.graph_label_button = QPushButton("A")
        self.graph_label_button.setToolTip("显示或隐藏节点标签")
        self.graph_label_button.setCheckable(True)
        self.graph_label_button.setChecked(True)
        for button in [
            self.graph_reset_button,
            self.graph_zoom_in_button,
            self.graph_zoom_out_button,
            self.graph_label_button,
        ]:
            button.setObjectName("graphToolButton")
            button.setFixedSize(34, 32)
        self.graph_detail_browser = QTextBrowser()
        self.graph_detail_browser.setOpenExternalLinks(False)
        self.graph_detail_browser.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.graph_detail_browser.setMinimumWidth(250)
        self.graph_detail_browser.setMinimumHeight(330)
        self.evidence_browser = QTextBrowser()
        self.evidence_browser.setOpenExternalLinks(True)
        self.evidence_browser.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.evidence_browser.setMinimumHeight(142)
        self.summary_browser = QTextBrowser()
        self.summary_browser.setMaximumHeight(138)
        self.summary_browser.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.summary_browser.setOpenExternalLinks(True)
        self.summary_browser.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.summary_browser.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self._build_layout()
        self._connect_signals()
        self.refresh(load_evidence=False)

    def set_theme(self, theme: str) -> None:
        self.theme = resolve_theme(theme)
        for pill in [self.store_pill, self.rag_pill, self.vector_pill, self.kg_pill, self.parser_pill]:
            pill.set_theme(self.theme)
        self.pipeline_widget.set_theme(self.theme)
        self.graph_view.set_theme(self.theme)
        self.refresh(query_text=self.search_input.text().strip(), load_evidence=bool(self.search_input.text().strip()))

    def _build_layout(self) -> None:
        top_layout = QHBoxLayout()
        top_layout.setSpacing(8)
        top_layout.addWidget(self.search_input, 1)
        top_layout.addWidget(self.search_button)

        action_layout = QHBoxLayout()
        action_layout.setSpacing(8)
        action_layout.addWidget(self.upload_button)
        action_layout.addWidget(self.batch_button)
        action_layout.addWidget(self.rebuild_button)
        action_layout.addWidget(self.export_snapshot_button)
        action_layout.addWidget(self.refresh_button)
        action_layout.addStretch(1)

        pill_layout = QHBoxLayout()
        pill_layout.setSpacing(8)
        for pill in [self.store_pill, self.rag_pill, self.vector_pill, self.kg_pill, self.parser_pill]:
            pill_layout.addWidget(pill)
        pill_layout.addStretch(1)

        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(9)
        left_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        left_layout.addWidget(self.summary_browser)
        document_label = QLabel("资料库 · DOCUMENTS")
        document_label.setObjectName("sectionTitle")
        left_layout.addWidget(document_label)
        left_layout.addWidget(self.document_stack)

        pipeline_panel = QWidget()
        pipeline_layout = QVBoxLayout(pipeline_panel)
        pipeline_layout.setContentsMargins(0, 0, 0, 0)
        pipeline_layout.setSpacing(9)
        pipeline_layout.addWidget(self.pipeline_widget, 0, Qt.AlignmentFlag.AlignTop)
        pipeline_layout.addStretch(1)

        overview_splitter = QSplitter(Qt.Orientation.Horizontal)
        overview_splitter.addWidget(left)
        overview_splitter.addWidget(pipeline_panel)
        overview_splitter.setChildrenCollapsible(False)
        overview_splitter.setSizes([620, 420])
        overview_splitter.setStretchFactor(0, 1)
        overview_splitter.setStretchFactor(1, 0)

        graph_panel = QWidget()
        graph_layout = QVBoxLayout(graph_panel)
        graph_layout.setContentsMargins(0, 0, 0, 0)
        graph_layout.setSpacing(8)
        graph_header = QHBoxLayout()
        graph_header.setContentsMargins(0, 0, 0, 0)
        graph_header.setSpacing(8)
        graph_label = QLabel("知识图谱 · GRAPH")
        graph_label.setObjectName("sectionTitle")
        graph_header.addWidget(graph_label)
        graph_header.addWidget(self.graph_search_input, 1)
        graph_header.addWidget(self.graph_reset_button)
        graph_header.addWidget(self.graph_zoom_in_button)
        graph_header.addWidget(self.graph_zoom_out_button)
        graph_header.addWidget(self.graph_label_button)
        graph_layout.addLayout(graph_header)
        graph_splitter = QSplitter(Qt.Orientation.Horizontal)
        graph_splitter.addWidget(self.graph_view)
        graph_splitter.addWidget(self.graph_detail_browser)
        graph_splitter.setChildrenCollapsible(False)
        graph_splitter.setSizes([820, 280])
        graph_splitter.setStretchFactor(0, 1)
        graph_splitter.setStretchFactor(1, 0)
        graph_layout.addWidget(graph_splitter, 1)

        evidence_panel = QWidget()
        evidence_layout = QVBoxLayout(evidence_panel)
        evidence_layout.setContentsMargins(0, 0, 0, 0)
        evidence_layout.setSpacing(8)
        evidence_label = QLabel("检索证据 · EVIDENCE")
        evidence_label.setObjectName("sectionTitle")
        evidence_layout.addWidget(evidence_label)
        evidence_layout.addWidget(self.evidence_browser, 1)

        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.addWidget(overview_splitter)
        splitter.addWidget(graph_panel)
        splitter.addWidget(evidence_panel)
        splitter.setChildrenCollapsible(False)
        splitter.setSizes([260, 520, 150])
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setStretchFactor(2, 0)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)
        layout.addLayout(top_layout)
        layout.addLayout(action_layout)
        layout.addLayout(pill_layout)
        layout.addWidget(splitter, 1)

    def _connect_signals(self) -> None:
        self.search_button.clicked.connect(self._search_from_input)
        self.search_input.returnPressed.connect(self._search_from_input)
        self.upload_button.clicked.connect(self._select_and_ingest_file)
        self.batch_button.clicked.connect(self._select_and_ingest_files)
        self.rebuild_button.clicked.connect(lambda: self._run_maintenance("rebuild"))
        self.export_snapshot_button.clicked.connect(lambda: self._run_maintenance("export"))
        self.refresh_button.clicked.connect(lambda: self.refresh(load_evidence=False))
        self.graph_search_input.returnPressed.connect(self._filter_graph_from_input)
        self.graph_search_input.textChanged.connect(self._on_graph_filter_text_changed)
        self.graph_reset_button.clicked.connect(self.graph_view.reset_view)
        self.graph_zoom_in_button.clicked.connect(lambda: self.graph_view.zoom_by(1.18))
        self.graph_zoom_out_button.clicked.connect(lambda: self.graph_view.zoom_by(0.84))
        self.graph_label_button.toggled.connect(self.graph_view.set_show_labels)
        self.graph_view.nodeSelected.connect(self._update_graph_detail)

    def refresh(
        self,
        task: dict[str, Any] | None = None,
        query_text: str | None = None,
        load_evidence: bool = True,
    ) -> None:
        if task is not None:
            self._last_task = task
        self.knowledge_base = DomainKnowledgeBase()
        status = self.knowledge_base.status()
        ingest_status = self.ingestion_service.status()
        merged_status = {**status, **ingest_status}
        self._update_status_pills(merged_status)
        self._update_summary(merged_status)
        self._update_source_overview(merged_status)
        self._update_document_table()
        self._update_pipeline(merged_status)
        evidence_payload = self._retrieve_evidence(task, query_text) if load_evidence else {"query": "", "chunks": [], "relations": []}
        self._update_graph_view(evidence_payload)
        self._set_evidence_payload(evidence_payload)

    def toHtml(self) -> str:
        """兼容测试和外部读取当前 HTML 摘要。"""
        return self.summary_browser.toHtml() + self.evidence_browser.toHtml()

    def _select_and_ingest_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "选择需要入库的资料",
            "",
            SUPPORTED_QT_FILE_FILTER,
        )
        if path:
            self.ingest_path(path)

    def _select_and_ingest_files(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(
            self,
            "选择需要批量解析入库的资料",
            "",
            SUPPORTED_QT_FILE_FILTER,
        )
        if paths:
            self.ingest_paths(paths)

    def ingest_path(self, path: str | Path) -> None:
        """供 GUI 和测试直接触发资料入库。"""
        self.ingest_paths([path])

    def ingest_paths(self, paths: list[str | Path]) -> None:
        """批量触发资料入库。"""
        if self._ingest_thread is not None:
            return
        normalized_paths = [str(path) for path in paths if str(path)]
        if not normalized_paths:
            return
        self._set_operation_buttons_enabled(False)
        self.parser_pill.set_state("解析运行中", "running")
        self.pipeline_widget.set_steps(
            [
                {"name": "MinerU / Docling 文档解析", "status": "running", "message": "正在解析上传资料"},
                {"name": "语义分块", "status": "pending", "message": "等待解析输出"},
                {"name": "BGE-M3 向量化索引", "status": "pending", "message": "等待文本块"},
                {"name": "KG 实体/关系抽取", "status": "pending", "message": "等待文本块"},
                {"name": "检索验证 / 证据引用", "status": "pending", "message": "等待索引和关系写入"},
            ]
        )
        self._ingest_thread = QThread(self)
        self._ingest_worker = KnowledgeIngestWorker(normalized_paths)
        self._ingest_worker.moveToThread(self._ingest_thread)
        self._ingest_thread.started.connect(self._ingest_worker.run)
        self._ingest_worker.progress.connect(self._on_ingest_progress)
        self._ingest_worker.finished.connect(self._on_ingest_finished)
        self._ingest_worker.failed.connect(self._on_ingest_failed)
        self._ingest_worker.finished.connect(self._cleanup_ingest_worker)
        self._ingest_worker.failed.connect(self._cleanup_ingest_worker)
        self._ingest_thread.start()

    def _cleanup_ingest_worker(self) -> None:
        if self._ingest_thread is not None:
            self._ingest_thread.quit()
            self._ingest_thread.wait()
        self._ingest_thread = None
        self._ingest_worker = None
        self._set_operation_buttons_enabled(True)

    def _set_operation_buttons_enabled(self, enabled: bool) -> None:
        for button in [
            self.search_button,
            self.upload_button,
            self.batch_button,
            self.rebuild_button,
            self.export_snapshot_button,
            self.refresh_button,
            self.graph_reset_button,
            self.graph_zoom_in_button,
            self.graph_zoom_out_button,
            self.graph_label_button,
        ]:
            button.setEnabled(enabled)

    def _filter_graph_from_input(self) -> None:
        self.graph_view.set_filter_text(self.graph_search_input.text())
        self._update_graph_detail("")

    def _on_graph_filter_text_changed(self, value: str) -> None:
        self.graph_view.set_filter_text(value)
        self._update_graph_detail("")

    def _on_ingest_progress(self, steps: list) -> None:
        self.pipeline_widget.set_steps(steps)
        active_step = next((step for step in steps if isinstance(step, dict) and step.get("status") == "running"), None)
        if isinstance(active_step, dict):
            self.parser_pill.set_state(str(active_step.get("name") or "入库运行中"), "running")

    def _on_ingest_finished(self, payload: dict) -> None:
        results = payload.get("results") if isinstance(payload.get("results"), list) else []
        last_result = results[-1] if results else payload
        steps = last_result.get("steps") if isinstance(last_result.get("steps"), list) else []
        self.pipeline_widget.set_steps(steps)
        success_count = int(payload.get("batch_success_count") or (1 if payload.get("success") else 0))
        failed_count = int(payload.get("batch_failed_count") or 0)
        status = "warning" if failed_count else "success"
        label = f"入库完成 {success_count} / 失败 {failed_count}" if payload.get("batch_total") else f"{payload.get('parser_backend') or '解析'} 完成"
        self.parser_pill.set_state(label, status)
        failure_html = ""
        if failed_count:
            failures = payload.get("failures") if isinstance(payload.get("failures"), list) else []
            detail = "<br>".join(escape(f"{Path(str(item.get('path') or '')).name}: {item.get('error') or ''}") for item in failures)
            failure_html = f"<h3>批量入库部分失败</h3><p>{detail}</p>"
        self.refresh(query_text=self.search_input.text().strip() or DEFAULT_EVIDENCE_QUERY)
        if failure_html:
            self._set_evidence_html(failure_html, scrollable=True)

    def _on_ingest_failed(self, message: str) -> None:
        self.parser_pill.set_state("解析失败", "failed")
        self.pipeline_widget.set_steps(
            [
                {"name": "MinerU / Docling 文档解析", "status": "failed", "message": message},
                {"name": "语义分块", "status": "pending", "message": "解析失败，未生成文本块"},
                {"name": "BGE-M3 向量化索引", "status": "pending", "message": "解析失败，未更新索引"},
                {"name": "KG 实体/关系抽取", "status": "pending", "message": "解析失败，未抽取关系"},
                {"name": "检索验证 / 证据引用", "status": "pending", "message": "解析失败，未生成证据"},
            ]
        )
        self._set_evidence_html(f"<h3>入库失败</h3><p>{escape(message)}</p>", scrollable=True)

    def _run_maintenance(self, operation: str) -> None:
        if self._maintenance_thread is not None or self._ingest_thread is not None:
            return
        self._set_operation_buttons_enabled(False)
        if operation == "rebuild":
            self.parser_pill.set_state("重建索引中", "running")
            self.pipeline_widget.set_steps(
                [
                    {"name": "MinerU / Docling 文档解析", "status": "success", "message": "复用已解析资料"},
                    {"name": "语义分块", "status": "running", "message": "读取并去重文本块"},
                    {"name": "BGE-M3 向量化索引", "status": "pending", "message": "等待重建"},
                    {"name": "KG 实体/关系抽取", "status": "pending", "message": "等待重建"},
                    {"name": "检索验证 / 证据引用", "status": "pending", "message": "等待验证"},
                ]
            )
        else:
            self.parser_pill.set_state("导出快照中", "running")
        self._maintenance_thread = QThread(self)
        self._maintenance_worker = KnowledgeMaintenanceWorker(operation)
        self._maintenance_worker.moveToThread(self._maintenance_thread)
        self._maintenance_thread.started.connect(self._maintenance_worker.run)
        self._maintenance_worker.finished.connect(self._on_maintenance_finished)
        self._maintenance_worker.failed.connect(self._on_maintenance_failed)
        self._maintenance_worker.finished.connect(self._cleanup_maintenance_worker)
        self._maintenance_worker.failed.connect(self._cleanup_maintenance_worker)
        self._maintenance_thread.start()

    def _cleanup_maintenance_worker(self) -> None:
        if self._maintenance_thread is not None:
            self._maintenance_thread.quit()
            self._maintenance_thread.wait()
        self._maintenance_thread = None
        self._maintenance_worker = None
        self._set_operation_buttons_enabled(True)

    def _on_maintenance_finished(self, payload: dict) -> None:
        operation = payload.get("operation")
        if operation == "rebuild":
            result = payload.get("result") if isinstance(payload.get("result"), dict) else {}
            steps = result.get("pipeline") if isinstance(result.get("pipeline"), list) else []
            if steps:
                self.pipeline_widget.set_steps(steps)
            self.refresh(query_text=self.search_input.text().strip() or DEFAULT_EVIDENCE_QUERY)
            self.parser_pill.set_state("索引重建完成", "success")
            return
        if operation == "export":
            path = str(payload.get("path") or "")
            self.refresh(load_evidence=False)
            self.parser_pill.set_state("快照已导出", "success")
            self._set_evidence_html(f"<h3>知识库快照已导出</h3><p>{escape(path)}</p>", scrollable=True)

    def _on_maintenance_failed(self, message: str) -> None:
        self.parser_pill.set_state("维护失败", "failed")
        self._set_evidence_html(f"<h3>知识库维护失败</h3><p>{escape(message)}</p>", scrollable=True)

    def _search_from_input(self) -> None:
        query = self.search_input.text().strip() or DEFAULT_EVIDENCE_QUERY
        self.search_input.setText(query)
        self.refresh(query_text=query)

    def _retrieve_evidence(self, task: dict[str, Any] | None, query_text: str | None) -> dict[str, Any]:
        if query_text is not None:
            query = query_text.strip() or DEFAULT_EVIDENCE_QUERY
            self.search_input.setText(query)
            return self.knowledge_base.retrieve_by_query(query, top_k=5, kg_top_k=8)
        active_task = task if task is not None else self._last_task
        if active_task:
            return self.knowledge_base.retrieve(active_task, top_k=5, kg_top_k=8)
        query = self.search_input.text().strip() or DEFAULT_EVIDENCE_QUERY
        self.search_input.setText(query)
        return self.knowledge_base.retrieve_by_query(query, top_k=5, kg_top_k=8)

    def _load_jsonl_rows(self, path: Path | str | None, limit: int | None = None) -> list[dict[str, Any]]:
        if path is None:
            return []
        target = Path(path)
        if not target.exists():
            return []
        rows: list[dict[str, Any]] = []
        opener = gzip.open if target.suffix.lower() == ".gz" else open
        with opener(target, "rt", encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                try:
                    payload = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(payload, dict):
                    rows.append(payload)
                    if limit is not None and len(rows) >= limit:
                        break
        return rows

    def _merged_graph_sources(self, evidence_payload: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
        entities_path = getattr(self.ingestion_service, "entities_path", None)
        relations_path = getattr(self.ingestion_service, "relations_path", None)
        builtin_kg_dir = Path(getattr(self.ingestion_service, "builtin_kg_dir", "") or "")

        runtime_entities = self._load_jsonl_rows(entities_path, limit=500)
        runtime_relations = self._load_jsonl_rows(relations_path, limit=160)
        builtin_entities = self._load_jsonl_rows(builtin_kg_dir / "entities.jsonl", limit=500)
        builtin_relations = self._load_jsonl_rows(builtin_kg_dir / "relations.compact.jsonl.gz", limit=160)
        evidence_relations = evidence_payload.get("relations") if isinstance(evidence_payload.get("relations"), list) else []

        relations = self._dedupe_relations([*evidence_relations, *runtime_relations[:80], *builtin_relations[:160]])
        entities = self._dedupe_entities([*runtime_entities, *builtin_entities], relations)
        return entities, relations, evidence_relations

    def _dedupe_entities(self, entities: list[dict[str, Any]], relations: list[dict[str, Any]]) -> list[dict[str, Any]]:
        entity_seen: set[tuple[str, str]] = set()
        merged: list[dict[str, Any]] = []
        for entity in entities:
            entity_type = str(entity.get("type") or "Entity")
            name = str(entity.get("name") or "").strip()
            if not name or (entity_type, name) in entity_seen:
                continue
            entity_seen.add((entity_type, name))
            merged.append(entity)
        for relation in relations:
            for name_key, type_key in [("source", "source_type"), ("target", "target_type")]:
                name = str(relation.get(name_key) or "").strip()
                entity_type = str(relation.get(type_key) or "Entity")
                if not name or (entity_type, name) in entity_seen:
                    continue
                entity_seen.add((entity_type, name))
                merged.append({"type": entity_type, "name": name})
        return merged

    def _dedupe_relations(self, relations: list[dict[str, Any]]) -> list[dict[str, Any]]:
        seen: set[tuple[str, str, str, str]] = set()
        merged: list[dict[str, Any]] = []
        for relation in relations:
            source = str(relation.get("source") or "").strip()
            relation_type = str(relation.get("relation") or "").strip()
            target = str(relation.get("target") or "").strip()
            record_id = str(relation.get("record_id") or relation.get("source_id") or "").strip()
            if not source or not target:
                continue
            key = (source, relation_type, target, record_id)
            if key in seen:
                continue
            seen.add(key)
            merged.append(relation)
        return merged

    def _update_graph_view(self, evidence_payload: dict[str, Any]) -> None:
        entities, relations, evidence_relations = self._merged_graph_sources(evidence_payload)
        self.graph_view.set_graph(entities, relations, evidence_relations)
        self._update_graph_detail(self.graph_view.selected_node_name())

    def _graph_detail_card(self, title: str, value: str, detail: str = "") -> str:
        if self.theme == "light":
            border = "#c8d2df"
            background = "#f8fafc"
            muted = "#64748b"
            foreground = "#172033"
        else:
            border = "#2b3a52"
            background = "#111a28"
            muted = "#94a3b8"
            foreground = "#dbe4ef"
        detail_html = f"<br><span style='color:{muted};font-size:11px;'>{escape(detail)}</span>" if detail else ""
        return (
            f"<div style='border:1px solid {border};border-radius:8px;padding:7px 9px;background:{background};margin-bottom:7px;'>"
            f"<span style='color:{muted};font-size:11px;'>{escape(title)}</span><br>"
            f"<span style='font-size:15px;font-weight:800;color:{foreground};'>{escape(value)}</span>"
            f"{detail_html}</div>"
        )

    def _update_graph_detail(self, selected_name: str = "") -> None:
        visible_nodes, visible_relations, total_nodes, total_relations = self.graph_view._node_payload()
        degrees = self.graph_view._visible_degrees(visible_relations)
        counts = self.graph_view._entity_counts()
        node_types = {name: entity_type for name, entity_type in visible_nodes}
        selected_name = selected_name or self.graph_view.selected_node_name()
        if selected_name and selected_name not in node_types:
            selected_name = ""

        if self.theme == "light":
            muted = "#64748b"
            foreground = "#172033"
            relation_bg = "#f8fafc"
            relation_border = "#c8d2df"
        else:
            muted = "#94a3b8"
            foreground = "#dbe4ef"
            relation_bg = "#111a28"
            relation_border = "#2b3a52"

        relation_counts: dict[str, int] = {}
        type_counts: dict[str, int] = {}
        for _name, entity_type in visible_nodes:
            type_counts[entity_type] = type_counts.get(entity_type, 0) + 1
        for relation in visible_relations:
            relation_name = str(relation.get("relation") or "RELATED_TO")
            relation_counts[relation_name] = relation_counts.get(relation_name, 0) + 1

        html = ["<h3>图谱审计</h3>"]
        if selected_name:
            entity_type = node_types.get(selected_name, "Entity")
            related = [
                relation
                for relation in visible_relations
                if selected_name in {str(relation.get("source") or ""), str(relation.get("target") or "")}
            ]
            html.append(self._graph_detail_card("选中节点", selected_name, entity_type))
            html.append(
                "<div style='display:grid;grid-template-columns:repeat(2,1fr);gap:7px;'>"
                + self._graph_detail_card("度数", str(degrees.get(selected_name, 0)))
                + self._graph_detail_card("计数", str(counts.get(selected_name, 1)))
                + "</div>"
            )
            html.append("<h4>关联关系</h4>")
            if not related:
                html.append(f"<p style='color:{muted};'>当前核心子图中没有该节点的可见关系。</p>")
            for relation in related[:18]:
                source = str(relation.get("source") or "")
                target = str(relation.get("target") or "")
                relation_name = str(relation.get("relation") or "RELATED_TO")
                other = target if source == selected_name else source
                html.append(
                    f"<div style='border:1px solid {relation_border};border-radius:8px;padding:7px 8px;"
                    f"background:{relation_bg};margin:6px 0;'>"
                    f"<span style='color:{muted};font-size:11px;'>{escape(relation_name)}</span><br>"
                    f"<span style='color:{foreground};font-weight:700;'>{escape(other)}</span>"
                    "</div>"
                )
        else:
            html.append(
                "<p style='margin-top:0;'>当前画布显示合并知识库的高连接核心子图。点击节点可查看关联关系，搜索框可按节点、类型或关系过滤。</p>"
            )
            html.append(
                "<div style='display:grid;grid-template-columns:repeat(2,1fr);gap:7px;'>"
                + self._graph_detail_card("总实体", str(total_nodes), f"可见 {len(visible_nodes)}")
                + self._graph_detail_card("总关系", str(total_relations), f"可见 {len(visible_relations)}")
                + "</div>"
            )
            if type_counts:
                html.append("<h4>节点类型</h4>")
                for entity_type, count in sorted(type_counts.items(), key=lambda item: (-item[1], item[0]))[:8]:
                    color = self.graph_view._type_color(entity_type).name()
                    html.append(
                        f"<div style='display:flex;align-items:center;gap:7px;margin:5px 0;color:{foreground};'>"
                        f"<span style='display:inline-block;width:8px;height:8px;border-radius:4px;background:{color};'></span>"
                        f"<span>{escape(entity_type)}</span>"
                        f"<span style='margin-left:auto;color:{muted};'>{count}</span>"
                        "</div>"
                    )
            if relation_counts:
                html.append("<h4>关系类型</h4>")
                for relation_name, count in sorted(relation_counts.items(), key=lambda item: (-item[1], item[0]))[:8]:
                    html.append(
                        f"<div style='border:1px solid {relation_border};border-radius:8px;padding:6px 8px;"
                        f"background:{relation_bg};margin:5px 0;color:{foreground};'>"
                        f"{escape(relation_name)}"
                        f"<span style='float:right;color:{muted};'>{count}</span>"
                        "</div>"
                    )
        self.graph_detail_browser.setHtml("".join(html))

    def _update_status_pills(self, status: dict[str, Any]) -> None:
        ready = bool(status.get("ready"))
        doc_count = int(status.get("runtime_document_count", status.get("document_count", 0)) or 0)
        chunk_count = int(status.get("rag_chunk_count", 0) or 0)
        vector_count = int(status.get("vector_chunk_count", 0) or 0)
        vector_status = str(status.get("vector_status") or "")
        vector_ready = bool(status.get("vector_ready")) and vector_status == "success"
        relation_count = int(status.get("kg_relation_count", 0) or 0)
        parser = (status.get("last_ingestion") or {}).get("parser_backend") if isinstance(status.get("last_ingestion"), dict) else ""
        self.store_pill.set_state(f"合并 RAG {chunk_count} 文本块", "success" if ready else "pending")
        self.rag_pill.set_state(f"RAG {chunk_count} 文本块", "success" if chunk_count else "pending")
        vector_label = f"Vector {vector_count} 向量块" if vector_count else f"Vector {vector_status or 'pending'}"
        vector_state = "success" if vector_ready else ("warning" if vector_status in {"warning", "failed"} else "pending")
        self.vector_pill.set_state(vector_label, vector_state)
        self.kg_pill.set_state(f"KG {relation_count} 关系", "success" if relation_count else "pending")
        self.parser_pill.set_state(str(parser or "解析器待调用"), "success" if parser else "pending")

    def _update_summary(self, status: dict[str, Any]) -> None:
        metrics = self._load_metrics()
        archive_cases = sorted(CASES_DIR.glob("CASE_*.json"))
        formal_cases = sorted(CASE_LIBRARY_DIR.glob("CASE_*.json"))
        odb_count, vis_count = self._abaqus_archive_counts()
        chunk_size = status.get("chunk_token_size", "-")
        overlap = status.get("chunk_overlap_tokens", "-")
        last = status.get("last_ingestion") if isinstance(status.get("last_ingestion"), dict) else {}
        verification = status.get("last_retrieval_verification") if isinstance(status.get("last_retrieval_verification"), dict) else {}
        doc_count = int(status.get("runtime_document_count", status.get("document_count", 0)) or 0)
        builtin_chunks = int(status.get("builtin_rag_chunk_count", 0) or 0)
        runtime_chunks = int(status.get("runtime_rag_chunk_count", 0) or 0)
        builtin_relations = int(status.get("builtin_kg_relation_count", 0) or 0)
        runtime_relations = int(status.get("runtime_kg_relation_count", 0) or 0)
        html = [
            "<h2>项目知识库状态</h2>",
            "<p>项目知识库由内置数据和用户增量组成。用户上传资料后进入解析、分块、索引、实体关系抽取和检索验证流程，最终检索入口读取合并后的总 RAG/KG。检索证据用于 LLM 工程上下文和人工审计，不替代代理公式或 FEM 结果。</p>",
            "<div style='display:grid;grid-template-columns:repeat(2,1fr);gap:8px;'>",
            self._summary_card("内置数据", f"{builtin_chunks} 文本块", f"{status.get('builtin_kg_entity_count', 0)} 实体 / {builtin_relations} 关系"),
            self._summary_card("用户增量", f"{doc_count} 文档", f"{runtime_chunks} 文本块 / {runtime_relations} 关系"),
            self._summary_card("合并 RAG", f"{status.get('rag_chunk_count', 0)} 文本块"),
            self._summary_card(
                "Vector",
                f"{status.get('vector_chunk_count', 0)} 向量块",
                f"后端 {status.get('vector_backend') or '-'}；状态 {status.get('vector_status') or '-'}",
            ),
            self._summary_card("合并 KG", f"{status.get('kg_entity_count', 0)} 实体 / {status.get('kg_relation_count', 0)} 关系"),
            self._summary_card("分块", f"{chunk_size} token / overlap {overlap}"),
            self._summary_card("案例", f"会话 {len(archive_cases)} / 正式 {len(formal_cases)}"),
            self._summary_card("FEM", f"ODB {odb_count} / 云图 {vis_count}"),
            "</div>",
            f"<p><b>最后入库：</b>{escape(str(last.get('title') or '-'))}；<b>解析器：</b>{escape(str(last.get('parser_backend') or '-'))}</p>",
            f"<p><b>向量索引：</b>{escape(str(status.get('vector_status') or '-'))}；{escape(str(status.get('vector_message') or '-'))}</p>",
            f"<p><b>检索验证：</b>{escape(str(verification.get('message') or '-'))}</p>",
            f"<p><b>用户增量清单：</b>{escape(str(status.get('manifest_path') or '-'))}</p>",
            f"<p><b>内置数据清单：</b>{escape(str(status.get('builtin_manifest_path') or '-'))}</p>",
        ]
        if metrics:
            html.append(
                "<p><b>代理模型：</b>"
                f"{escape(str(metrics.get('selected_model', '-')))}，训练样本 {escape(str(metrics.get('training_size', '-')))}</p>"
            )
        self.summary_browser.setHtml("".join(html))

    def _summary_card(self, title: str, value: str, detail: str = "") -> str:
        if self.theme == "light":
            border = "#c8d2df"
            background = "#f8fafc"
            muted = "#64748b"
            foreground = "#172033"
        else:
            border = "#2b3a52"
            background = "#111a28"
            muted = "#64748b"
            foreground = "#dbe4ef"
        detail_html = f"<br><span style='color:{muted};font-size:11px;'>{escape(detail)}</span>" if detail else ""
        return (
            f"<div style='border:1px solid {border};border-radius:8px;padding:8px 10px;background:{background};'>"
            f"<span style='color:{muted};font-size:12px;'>{escape(title)}</span><br>"
            f"<span style='font-size:18px;font-weight:800;color:{foreground};'>{escape(value)}</span>"
            f"{detail_html}</div>"
        )

    def _update_source_overview(self, status: dict[str, Any]) -> None:
        builtin_chunks = int(status.get("builtin_rag_chunk_count", 0) or 0)
        builtin_entities = int(status.get("builtin_kg_entity_count", 0) or 0)
        builtin_relations = int(status.get("builtin_kg_relation_count", 0) or 0)
        runtime_docs = int(status.get("runtime_document_count", status.get("document_count", 0)) or 0)
        runtime_chunks = int(status.get("runtime_rag_chunk_count", 0) or 0)
        runtime_relations = int(status.get("runtime_kg_relation_count", 0) or 0)
        vector_status = status.get("vector_status") or "pending"
        html = [
            "<h3>知识来源与索引</h3>",
            "<ul>",
            f"<li><b>系统资料包：</b>{builtin_chunks} 文本块，{builtin_entities} 实体，{builtin_relations} 关系。</li>",
            f"<li><b>用户增量：</b>{runtime_docs} 文档，{runtime_chunks} 文本块，{runtime_relations} 关系。</li>",
            f"<li><b>合并索引：</b>{status.get('rag_chunk_count', 0)} 文本块，{status.get('kg_entity_count', 0)} 实体，{status.get('kg_relation_count', 0)} 关系。</li>",
            f"<li><b>向量状态：</b>{escape(str(vector_status))}；chunk {escape(str(status.get('chunk_token_size', '-')))} / overlap {escape(str(status.get('chunk_overlap_tokens', '-')))}。</li>",
            "</ul>",
        ]
        self.source_overview_browser.setHtml("".join(html))

    def _html_card_style(self) -> str:
        if self.theme == "light":
            return "border:1px solid #c8d2df;border-radius:10px;padding:10px;margin:8px 0;background:#f8fafc;"
        return "border:1px solid #2b3a52;border-radius:10px;padding:10px;margin:8px 0;background:#111a28;"

    def _update_document_table(self) -> None:
        documents_path = self.ingestion_service.documents_path
        rows = []
        if documents_path.exists():
            with documents_path.open("r", encoding="utf-8") as handle:
                for line in handle:
                    if not line.strip():
                        continue
                    try:
                        payload = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if isinstance(payload, dict):
                        rows.append(payload)
        self.document_table.setRowCount(len(rows))
        if not rows:
            self.document_stack.setCurrentIndex(0)
            self.document_stack.setMaximumHeight(132)
            self.document_stack.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            return
        self.document_stack.setCurrentIndex(1)
        self.document_stack.setMaximumHeight(420)
        self.document_stack.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        for row_index, item in enumerate(rows):
            values = [
                item.get("title") or item.get("file_name") or item.get("document_id") or "",
                item.get("parser_backend") or "",
                item.get("chunk_count") or 0,
                str(item.get("file_sha256") or "")[:12],
                item.get("updated_at") or "",
                item.get("stored_path") or "",
            ]
            for col_index, value in enumerate(values):
                self.document_table.setItem(row_index, col_index, QTableWidgetItem(str(value)))
        self.document_table.resizeRowsToContents()

    def _update_pipeline(self, status: dict[str, Any]) -> None:
        pipeline = status.get("pipeline") if isinstance(status.get("pipeline"), list) else []
        if pipeline:
            self.pipeline_widget.set_steps(pipeline)
            return
        self.pipeline_widget.set_steps(
            [
                {"name": "MinerU / Docling 文档解析", "status": "pending", "message": "等待用户上传资料"},
                {"name": "语义分块", "status": "pending", "message": "chunk_token_size / overlap 由配置控制"},
                {"name": "BGE-M3 向量化索引", "status": "pending", "message": "等待文本块写入索引"},
                {"name": "KG 实体/关系抽取", "status": "pending", "message": "等待实体关系抽取"},
                {"name": "检索验证 / 证据引用", "status": "pending", "message": "等待可引用证据"},
            ]
        )

    def _load_metrics(self) -> dict[str, Any]:
        metrics_path = MODELS_DIR / "surrogate_metrics.json"
        if not metrics_path.exists():
            return {}
        try:
            payload = json.loads(metrics_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}
        return payload if isinstance(payload, dict) else {}

    def _abaqus_archive_counts(self) -> tuple[int, int]:
        odb_count = 0
        vis_count = 0
        for run_dir in ABAQUS_RUNS_DIR.glob("C*"):
            if (run_dir / f"{run_dir.name}.odb").exists():
                odb_count += 1
            if (run_dir / f"{run_dir.name}_mode1.json").exists():
                vis_count += 1
        return odb_count, vis_count

    def _case_memory_count(self) -> int:
        try:
            return int(CaseMemoryIndex().engine.count())
        except Exception:
            return 0

    def _evidence_html(self, payload: dict[str, Any]) -> str:
        query = str(payload.get("query") or "").strip()
        chunks = payload.get("chunks") if isinstance(payload.get("chunks"), list) else []
        relations = payload.get("relations") if isinstance(payload.get("relations"), list) else []
        lines = [
            "<h3>混合检索结果</h3>",
            f"<p><b>检索词：</b>{escape(query or '-')}</p>",
        ]
        lines.append("<h4>RAG 文本块</h4>")
        if chunks:
            for index, item in enumerate(chunks, start=1):
                title = item.get("document_title") or item.get("title") or item.get("record_id") or f"资料片段 {index}"
                source_parts = [
                    f"记录 {item.get('record_id')}" if item.get("record_id") else "",
                    f"页码 {self._page_text(item)}" if self._page_text(item) else "",
                    f"DOI {item.get('doi')}" if item.get("doi") else "",
                    str(item.get("source_url") or ""),
                ]
                source_line = " · ".join(escape(str(part)) for part in source_parts if part)
                lines.append(
                    f"<div style='{self._html_card_style()}'>"
                    f"<b>{index}. {escape(str(title))}</b><br>"
                    f"<span style='color:#34d399;'>score {escape(str(item.get('score', '-')))}</span><br>"
                    f"<span style='color:#64748b;'>{source_line}</span>"
                    f"<p>{escape(str(item.get('text') or ''))}</p>"
                    "</div>"
                )
        else:
            lines.append("<p>当前没有命中的 RAG 文本块。上传资料并完成入库后可检索。</p>")

        lines.append("<h4>知识图谱关系</h4>")
        if relations:
            for index, item in enumerate(relations, start=1):
                lines.append(
                    "<p>"
                    f"<b>{index}. {escape(str(item.get('source') or '-'))}({escape(str(item.get('source_type') or '-'))}) "
                    f"-[{escape(str(item.get('relation') or '-'))}]-&gt; "
                    f"{escape(str(item.get('target') or '-'))}({escape(str(item.get('target_type') or '-'))})</b><br>"
                    f"<span style='color:#34d399;'>score {escape(str(item.get('score', '-')))}</span>"
                    "</p>"
                )
        else:
            lines.append("<p>当前没有命中的知识图谱关系。</p>")
        return "".join(lines)

    def _set_evidence_payload(self, payload: dict[str, Any]) -> None:
        chunks = payload.get("chunks") if isinstance(payload.get("chunks"), list) else []
        relations = payload.get("relations") if isinstance(payload.get("relations"), list) else []
        query = str(payload.get("query") or "").strip()
        scrollable = bool(query or chunks or relations)
        self._set_evidence_html(self._evidence_html(payload), scrollable=scrollable)

    def _set_evidence_html(self, html: str, scrollable: bool) -> None:
        policy = Qt.ScrollBarPolicy.ScrollBarAsNeeded if scrollable else Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        self.evidence_browser.setVerticalScrollBarPolicy(policy)
        self.evidence_browser.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.evidence_browser.setHtml(html)

    def _page_text(self, item: dict[str, Any]) -> str:
        page_start = item.get("page_start")
        page_end = item.get("page_end")
        if page_start in (None, "", 0):
            return ""
        if page_end in (None, "", page_start, 0):
            return str(page_start)
        return f"{page_start}-{page_end}"

"""知识库上传、入库、检索和证据展示组件。"""

from __future__ import annotations

import gzip
import json
import math
import re
from dataclasses import asdict
from html import escape
from pathlib import Path
from typing import Any

from PyQt6.QtCore import QLineF, QObject, QPointF, QRectF, QSize, QThread, Qt, pyqtSignal
from PyQt6.QtGui import QBrush, QColor, QFont, QFontMetrics, QPainter, QPainterPath, QPen, QPolygonF, QRadialGradient
from PyQt6.QtWidgets import (
    QFileDialog,
    QGridLayout,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QComboBox,
    QFrame,
    QScrollArea,
    QSizePolicy,
    QSplitter,
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


def _read_document_rows(documents_path: Path | str | None) -> list[dict[str, Any]]:
    if documents_path is None:
        return []
    target = Path(documents_path)
    if not target.exists():
        return []
    rows: list[dict[str, Any]] = []
    with target.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(payload, dict):
                rows.append(payload)
    return rows


class GraphChipButton(QPushButton):
    """知识图谱筛选 chip，自绘以避免平台原生按钮样式干扰。"""

    def __init__(self, value: str, count: int, accent_color: str, theme: str) -> None:
        super().__init__()
        self.value = value
        self.count = count
        self.accent_color = QColor(accent_color)
        self.theme = resolve_theme(theme)
        self.setCheckable(True)
        self.setMinimumHeight(28)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def set_theme(self, theme: str) -> None:
        self.theme = resolve_theme(theme)
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        if self.theme == "light":
            fill = QColor("#ffffff")
            hover_fill = QColor("#eef5ff")
            active_fill = QColor("#eaf2ff")
            border = QColor("#c8d2df")
            text = QColor("#172033")
            muted = QColor("#64748b")
        else:
            fill = QColor("#111a28")
            hover_fill = QColor("#162237")
            active_fill = QColor("#18243a")
            border = QColor("#2b3a52")
            text = QColor("#dbe4ef")
            muted = QColor("#94a3b8")
        active = self.isChecked()
        rect = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        painter.setBrush(QBrush(active_fill if active else (hover_fill if self.underMouse() else fill)))
        painter.setPen(QPen(self.accent_color if active or self.underMouse() else border, 1.0))
        painter.drawRoundedRect(rect, 8, 8)

        dot = QColor(self.accent_color)
        dot.setAlpha(255 if active or self.underMouse() else 210)
        painter.setBrush(QBrush(dot))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QPointF(12.5, rect.center().y()), 3.7, 3.7)

        font = QFont(self.font())
        font.setPointSize(8)
        font.setBold(True)
        painter.setFont(font)
        metrics = QFontMetrics(font)
        count_text = str(self.count)
        count_width = max(18, metrics.horizontalAdvance(count_text) + 8)
        label_width = max(28, int(rect.width() - count_width - 34))
        label = metrics.elidedText(self.value, Qt.TextElideMode.ElideRight, label_width)
        painter.setPen(text)
        painter.drawText(QRectF(22, 0, label_width, self.height()), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, label)
        painter.setPen(muted)
        painter.drawText(
            QRectF(self.width() - count_width - 7, 0, count_width, self.height()),
            Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight,
            count_text,
        )


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
        self.active_node_types: set[str] = set()
        self.active_relation_types: set[str] = set()
        self.show_labels = True
        self.show_relations = True
        self.show_relation_labels = True
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
        self._hovered_node_name = ""
        self.setMinimumHeight(360)
        self.setMinimumWidth(560)
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

    def set_type_filter(self, entity_types: set[str]) -> None:
        """设置节点类型过滤。"""

        self.active_node_types = {str(item).strip() for item in entity_types if str(item).strip()}
        if self._selected_node_name:
            self._selected_node_name = ""
            self.nodeSelected.emit("")
        self.update()

    def set_relation_filter(self, relation_types: set[str]) -> None:
        """设置关系类型过滤。"""

        self.active_relation_types = {str(item).strip() for item in relation_types if str(item).strip()}
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

    def set_show_relations(self, enabled: bool) -> None:
        """统一控制关系标签显示状态。"""

        self.set_show_relation_labels(enabled)

    def set_show_relation_labels(self, enabled: bool) -> None:
        """设置关系标签显示状态。"""

        self.show_relation_labels = bool(enabled)
        self.show_relations = True
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
                "node_ring": QColor("#ffffff"),
                "node_shadow": QColor(15, 23, 42, 34),
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
            "node_ring": QColor("#0f172a"),
            "node_shadow": QColor(0, 0, 0, 96),
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

        candidate_relations = []
        for relation in self.relations:
            relation_name = str(relation.get("relation") or "RELATED_TO").strip()
            if self.active_relation_types and relation_name not in self.active_relation_types:
                continue
            candidate_relations.append(relation)

        for relation in candidate_relations:
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
        if self.active_relation_types:
            relation_names: set[str] = set()
            for relation in candidate_relations:
                source = str(relation.get("source") or "").strip()
                target = str(relation.get("target") or "").strip()
                if source:
                    relation_names.add(source)
                if target:
                    relation_names.add(target)
            sorted_nodes = [item for item in sorted_nodes if item[0] in relation_names]
        if self.active_node_types:
            seed_names = {name for name, entity_type in sorted_nodes if entity_type in self.active_node_types}
            neighbor_names: set[str] = set(seed_names)
            for relation in candidate_relations:
                source = str(relation.get("source") or "").strip()
                target = str(relation.get("target") or "").strip()
                if source in seed_names or target in seed_names:
                    if source:
                        neighbor_names.add(source)
                    if target:
                        neighbor_names.add(target)
            sorted_nodes = [item for item in sorted_nodes if item[0] in neighbor_names]
        if self.filter_text:
            seed_names = {
                name
                for name, entity_type in sorted_nodes
                if self.filter_text in name.lower() or self.filter_text in entity_type.lower()
            }
            neighbor_names: set[str] = set(seed_names)
            for relation in candidate_relations:
                source = str(relation.get("source") or "").strip()
                target = str(relation.get("target") or "").strip()
                relation_name = str(relation.get("relation") or "").strip().lower()
                if source in seed_names or target in seed_names or self.filter_text in relation_name:
                    if source:
                        neighbor_names.add(source)
                    if target:
                        neighbor_names.add(target)
            sorted_nodes = [item for item in sorted_nodes if item[0] in neighbor_names]
        max_nodes = 80
        visible_nodes = sorted_nodes[:max_nodes]
        visible_names = {name for name, _ in visible_nodes}
        visible_relations = [
            relation
            for relation in candidate_relations
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
        relation_limit = 140 if self.filter_text or self.active_node_types or self.active_relation_types else 28
        visible_relations = visible_relations[:relation_limit]
        if visible_relations:
            connected_names: set[str] = set()
            for relation in visible_relations:
                source = str(relation.get("source") or "").strip()
                target = str(relation.get("target") or "").strip()
                if source:
                    connected_names.add(source)
                if target:
                    connected_names.add(target)
            if connected_names:
                visible_nodes = [item for item in visible_nodes if item[0] in connected_names]
        return visible_nodes, visible_relations, len(node_types), len(self.relations)

    def filter_options(self) -> tuple[list[tuple[str, int]], list[tuple[str, int]]]:
        """返回图谱可用节点类型和关系类型。"""

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
        type_counts: dict[str, int] = {}
        for entity_type in node_types.values():
            type_counts[entity_type] = type_counts.get(entity_type, 0) + 1
        relation_counts: dict[str, int] = {}
        for relation in self.relations:
            relation_type = str(relation.get("relation") or "RELATED_TO").strip()
            if relation_type:
                relation_counts[relation_type] = relation_counts.get(relation_type, 0) + 1
        return (
            sorted(type_counts.items(), key=lambda item: (-item[1], item[0])),
            sorted(relation_counts.items(), key=lambda item: (-item[1], item[0])),
        )

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
        return math.log1p(counts.get(name, 1)) + degrees.get(name, 0) * 2.2

    def _node_radius(self, name: str, degrees: dict[str, int], counts: dict[str, int]) -> float:
        weight = self._node_weight(name, degrees, counts)
        return max(7.5, min(22.0, 7.0 + math.sqrt(max(weight, 1.0)) * 2.65))

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
        main_center = QPointF(graph_center.x() - (graph_rect.width() * 0.06 if has_side_components else 0), graph_center.y())
        main_rx = max(136.0, graph_rect.width() * (0.42 if has_side_components else 0.50)) * self._scale
        main_ry = max(96.0, graph_rect.height() * 0.43) * self._scale
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
                outer_ry = max(48.0, graph_rect.height() * 0.26) * self._scale
                for index, component in enumerate(small_components):
                    angle = -math.pi / 2.0 + 2.0 * math.pi * index / max(1, len(small_components))
                    center = QPointF(graph_center.x() + outer_rx * math.cos(angle), graph_center.y() + outer_ry * math.sin(angle))
                    place_component(component, center, 38.0 * self._scale, 30.0 * self._scale, phase=0.28)
        if abs(self._pan.x()) < 0.01 and abs(self._pan.y()) < 0.01 and self._scale <= 1.02:
            positions = self._fit_positions_to_rect(positions, graph_rect)
        return positions

    def _fit_positions_to_rect(self, positions: dict[str, QPointF], graph_rect: QRectF) -> dict[str, QPointF]:
        if len(positions) < 2:
            return positions
        padding = 12.0
        min_x = min(point.x() for point in positions.values())
        max_x = max(point.x() for point in positions.values())
        min_y = min(point.y() for point in positions.values())
        max_y = max(point.y() for point in positions.values())
        width = max(1.0, max_x - min_x)
        height = max(1.0, max_y - min_y)
        available_width = max(1.0, graph_rect.width() - padding * 2.0)
        available_height = max(1.0, graph_rect.height() - padding * 2.0)
        factor = min(1.92, available_width / width, available_height / height)
        vertical_factor = min(2.55, max(factor, available_height / height * 1.08))
        current_center = QPointF((min_x + max_x) / 2.0, (min_y + max_y) / 2.0)
        target_center = graph_rect.center()
        fitted: dict[str, QPointF] = {}
        safe_left = graph_rect.left() + 16.0
        safe_right = graph_rect.right() - 16.0
        safe_top = graph_rect.top() + 12.0
        safe_bottom = graph_rect.bottom() - 12.0
        for name, point in positions.items():
            x = target_center.x() + (point.x() - current_center.x()) * factor
            y = target_center.y() + (point.y() - current_center.y()) * vertical_factor
            fitted[name] = QPointF(
                min(max(x, safe_left), safe_right),
                min(max(y, safe_top), safe_bottom),
            )
        return fitted

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

    def _draw_background(self, painter: QPainter, panel: QRectF, graph_rect: QRectF, colors: dict[str, QColor]) -> None:
        painter.save()
        border = QColor(colors["border"])
        border.setAlpha(86 if self.theme == "light" else 78)
        painter.setPen(QPen(border, 0.9))
        painter.setBrush(QBrush(colors["panel"]))
        painter.drawRoundedRect(panel, 12, 12)

        glow = QRadialGradient(graph_rect.center(), max(graph_rect.width(), graph_rect.height()) * 0.62)
        if self.theme == "light":
            glow.setColorAt(0.0, QColor(219, 234, 254, 92))
            glow.setColorAt(0.48, QColor(248, 251, 255, 28))
            glow.setColorAt(1.0, QColor(248, 251, 255, 0))
        else:
            glow.setColorAt(0.0, QColor(37, 99, 235, 38))
            glow.setColorAt(0.46, QColor(56, 189, 248, 12))
            glow.setColorAt(1.0, QColor(15, 23, 42, 0))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(glow))
        painter.drawRect(graph_rect.adjusted(1.0, 1.0, -1.0, -1.0))
        painter.restore()

    def _draw_node(
        self,
        painter: QPainter,
        point: QPointF,
        radius: float,
        color: QColor,
        colors: dict[str, QColor],
        selected: bool,
        hovered: bool,
    ) -> None:
        painter.save()
        if selected or hovered:
            halo = QColor(colors["selected"] if selected else color)
            halo.setAlpha(70 if selected else 42)
            painter.setBrush(QBrush(halo))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(point, radius + (9.0 if selected else 6.0), radius + (9.0 if selected else 6.0))

        shadow = QColor(colors["node_shadow"])
        painter.setBrush(QBrush(shadow))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QPointF(point.x() + 1.2, point.y() + 2.0), radius + 2.0, radius + 2.0)

        gradient = QRadialGradient(QPointF(point.x() - radius * 0.35, point.y() - radius * 0.38), radius * 1.9)
        lighter = QColor(color)
        lighter = lighter.lighter(145 if self.theme == "light" else 130)
        darker = QColor(color)
        darker = darker.darker(118)
        gradient.setColorAt(0.0, lighter)
        gradient.setColorAt(0.62, color)
        gradient.setColorAt(1.0, darker)
        painter.setBrush(QBrush(gradient))
        ring = QColor(colors["selected"] if selected else colors["node_ring"])
        if not selected and hovered:
            ring = QColor(color).lighter(155)
        painter.setPen(QPen(ring, 2.6 if selected else (2.0 if hovered else 1.25)))
        painter.drawEllipse(point, radius, radius)

        inner = QColor("#ffffff" if self.theme == "light" else "#e2e8f0")
        inner.setAlpha(66)
        painter.setBrush(QBrush(inner))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QPointF(point.x() - radius * 0.32, point.y() - radius * 0.34), max(2.0, radius * 0.18), max(2.0, radius * 0.18))
        painter.restore()

    def _trim_edge(self, source: QPointF, target: QPointF, source_radius: float, target_radius: float) -> tuple[QPointF, QPointF]:
        dx = target.x() - source.x()
        dy = target.y() - source.y()
        length = math.hypot(dx, dy)
        if length < 2.0:
            return source, target
        ux = dx / length
        uy = dy / length
        return (
            QPointF(source.x() + ux * source_radius, source.y() + uy * source_radius),
            QPointF(target.x() - ux * target_radius, target.y() - uy * target_radius),
        )

    def _draw_edge(
        self,
        painter: QPainter,
        source: QPointF,
        target: QPointF,
        color: QColor,
        highlight: bool,
        show_arrow: bool,
    ) -> None:
        line = QLineF(source, target)
        if line.length() < 2:
            return
        dx = target.x() - source.x()
        dy = target.y() - source.y()
        length = max(1.0, math.hypot(dx, dy))
        normal = QPointF(-dy / length, dx / length)
        curve = 6.0 if not highlight else 26.0
        control = QPointF((source.x() + target.x()) / 2.0 + normal.x() * curve, (source.y() + target.y()) / 2.0 + normal.y() * curve)

        path = QPainterPath(source)
        path.quadTo(control, target)
        width = 0.84 if highlight else 0.54
        shadow = QColor("#020617" if self.theme == "dark" else "#ffffff")
        shadow.setAlpha(96 if self.theme == "dark" else 132)
        painter.setPen(QPen(shadow, width + 0.28, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.drawPath(path)
        painter.setPen(QPen(color, width, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.drawPath(path)

        if show_arrow:
            arrow_len = 5.4 if highlight else 4.2
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

    def _draw_edge_label(
        self,
        painter: QPainter,
        source: QPointF,
        target: QPointF,
        relation_name: str,
        graph_rect: QRectF,
        colors: dict[str, QColor],
        occupied: list[QRectF] | None = None,
        force: bool = False,
    ) -> bool:
        label = str(relation_name or "RELATED_TO").strip()
        if not label:
            return False
        font = QFont(self.font())
        font.setPointSize(7)
        font.setBold(True)
        painter.setFont(font)
        metrics = QFontMetrics(font)
        text = metrics.elidedText(label, Qt.TextElideMode.ElideRight, 122)
        width = min(132.0, max(48.0, float(metrics.horizontalAdvance(text) + 14)))
        height = 18.0
        dx = target.x() - source.x()
        dy = target.y() - source.y()
        length = max(1.0, math.hypot(dx, dy))
        normal = QPointF(-dy / length, dx / length)
        candidates: list[QRectF] = []
        for ratio, offset in ((0.50, 12.0), (0.38, -12.0), (0.62, 12.0)):
            mid = QPointF(source.x() + dx * ratio + normal.x() * offset, source.y() + dy * ratio + normal.y() * offset)
            rect = QRectF(mid.x() - width / 2.0, mid.y() - height / 2.0, width, height)
            rect.moveLeft(min(max(rect.left(), graph_rect.left() + 4.0), graph_rect.right() - rect.width() - 4.0))
            rect.moveTop(min(max(rect.top(), graph_rect.top() + 4.0), graph_rect.bottom() - rect.height() - 4.0))
            candidates.append(rect)

        selected_rect = candidates[0]
        if occupied is not None and not force:
            selected_rect = QRectF()
            for candidate in candidates:
                padded = candidate.adjusted(-4, -3, 4, 3)
                if not any(padded.intersects(existing) for existing in occupied):
                    selected_rect = candidate
                    break
            if selected_rect.isNull():
                return False
        rect = selected_rect
        painter.setBrush(QBrush(colors["label_bg"]))
        painter.setPen(QPen(colors["highlight"], 0.8))
        painter.drawRoundedRect(rect, 5, 5)
        painter.setPen(colors["text"])
        painter.drawText(rect.adjusted(5, 0, -5, 0), Qt.AlignmentFlag.AlignCenter, text)
        if occupied is not None:
            occupied.append(rect.adjusted(-4, -3, 4, 3))
        return True

    def _wrapped_label_lines(self, name: str, metrics: QFontMetrics, max_width: int, max_lines: int = 2) -> list[str]:
        raw = str(name or "").strip()
        if not raw:
            return []
        text_width = max(24, max_width - 14)
        if metrics.horizontalAdvance(raw) <= text_width:
            return [raw]

        tokens = [token for token in re.split(r"([\s/_-]+)", raw) if token]
        if len(tokens) == 1:
            current = ""
            lines: list[str] = []
            for char in raw:
                candidate = current + char
                if current and metrics.horizontalAdvance(candidate) > text_width:
                    lines.append(current)
                    current = char
                    if len(lines) == max_lines - 1:
                        break
                else:
                    current = candidate
            if current:
                lines.append(current)
            if len(lines) > max_lines:
                tail = "".join(lines[max_lines - 1 :])
                lines = lines[: max_lines - 1] + [metrics.elidedText(tail, Qt.TextElideMode.ElideRight, text_width)]
            return [metrics.elidedText(line, Qt.TextElideMode.ElideRight, text_width) for line in lines[:max_lines] if line]

        lines: list[str] = []
        current = ""
        for token in tokens:
            candidate = f"{current}{token}" if current else token.strip()
            if not current or metrics.horizontalAdvance(candidate) <= text_width:
                current = candidate
                continue
            lines.append(current.strip())
            current = token.strip()
            if len(lines) == max_lines - 1:
                break
        rest = current.strip()
        if len(lines) == max_lines - 1:
            consumed = "".join(lines)
            if raw.startswith(consumed):
                rest = raw[len(consumed) :].strip(" /_-")
            if not rest:
                rest = current.strip()
        if rest:
            lines.append(metrics.elidedText(rest, Qt.TextElideMode.ElideRight, text_width))
        if not lines:
            lines = [metrics.elidedText(raw, Qt.TextElideMode.ElideRight, text_width)]
        if len(lines) > max_lines:
            tail = " ".join(lines[max_lines - 1 :])
            lines = lines[: max_lines - 1] + [metrics.elidedText(tail, Qt.TextElideMode.ElideRight, text_width)]
        return [line for line in lines if line]

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
        max_width = 270
        lines = self._wrapped_label_lines(name, metrics, max_width=max_width, max_lines=2)
        if not lines:
            return False
        width = min(float(max_width), max(52.0, float(max(metrics.horizontalAdvance(line) for line in lines) + 16)))
        line_height = max(12, metrics.height())
        height = float(line_height * len(lines) + 7)
        raw_candidates = [
            QRectF(point.x() - width / 2.0, point.y() + radius + 5.0, width, height),
            QRectF(point.x() - width / 2.0, point.y() - radius - height - 5.0, width, height),
            QRectF(point.x() + radius + 7.0, point.y() - height / 2.0, width, height),
            QRectF(point.x() - radius - width - 7.0, point.y() - height / 2.0, width, height),
        ]
        candidates: list[QRectF] = []
        for candidate in raw_candidates:
            candidate = QRectF(candidate)
            candidate.moveLeft(min(max(candidate.left(), graph_rect.left() + 2.0), graph_rect.right() - candidate.width() - 2.0))
            candidate.moveTop(min(max(candidate.top(), graph_rect.top() + 2.0), graph_rect.bottom() - candidate.height() - 2.0))
            candidates.append(candidate)

        label_rect = candidates[0]
        if occupied is not None and not force:
            label_rect = QRectF()
            for candidate in candidates:
                padded_rect = candidate.adjusted(-5, -4, 5, 4)
                if not any(padded_rect.intersects(existing) for existing in occupied):
                    label_rect = candidate
                    break
            if label_rect.isNull():
                return False
        painter.setBrush(QBrush(colors["label_bg"]))
        painter.setPen(QPen(colors["border"], 0.8))
        painter.drawRoundedRect(label_rect, 5, 5)
        painter.setFont(font)
        painter.setPen(colors["text"])
        text_rect = label_rect.adjusted(7, 3, -7, -3)
        for index, line in enumerate(lines):
            line_rect = QRectF(text_rect.left(), text_rect.top() + index * line_height, text_rect.width(), line_height)
            painter.drawText(line_rect, Qt.AlignmentFlag.AlignCenter, line)
        if occupied is not None:
            occupied.append(label_rect.adjusted(-5, -4, 5, 4))
        return True

    def _draw_legend(
        self,
        painter: QPainter,
        visible_nodes: list[tuple[str, str]],
        colors: dict[str, QColor],
        min_left: float,
        row_top: float,
        row_height: float,
    ) -> None:
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
        y = row_top + (row_height - 20.0) / 2.0
        for entity_type, count in reversed(items):
            label = f"{entity_type} {count}"
            width = metrics.horizontalAdvance(label) + 22
            next_x = x - width
            if next_x < min_left:
                break
            x = next_x
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
        graph_rect = panel.adjusted(12, 24, -12, -6)
        self._draw_background(painter, panel, graph_rect, colors)
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
        legend_left = max(320.0, self.width() * 0.56)
        header_top = 4.0
        header_height = 20.0
        painter.drawText(
            QRectF(18, header_top, max(120.0, legend_left - 28.0), header_height),
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            subtitle,
        )
        self._draw_legend(painter, visible_nodes, colors, legend_left, header_top, header_height)

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
        edge_label_requests: list[tuple[QPointF, QPointF, str, bool]] = []
        show_all_relation_labels = self.show_relation_labels and self.show_labels and len(visible_relations) <= 48
        for relation in visible_relations:
            source = str(relation.get("source") or "")
            target = str(relation.get("target") or "")
            if source not in positions or target not in positions:
                continue
            key = (source, str(relation.get("relation") or ""), target)
            selected_edge = bool(self._selected_node_name and self._selected_node_name in {source, target})
            highlight = key in highlighted or selected_edge
            edge_color = QColor(colors["highlight"]) if highlight else QColor("#1d4ed8" if self.theme == "light" else "#f59e0b")
            edge_color.setAlpha(232 if key in highlighted else (196 if selected_edge else (162 if self.theme == "light" else 172)))
            source_radius = self._node_radius(source, degrees, counts) + 3.0
            target_radius = self._node_radius(target, degrees, counts) + 5.0
            edge_source, edge_target = self._trim_edge(positions[source], positions[target], source_radius, target_radius)
            self._draw_edge(painter, edge_source, edge_target, edge_color, highlight, show_arrow=highlight)
            if show_all_relation_labels or (self.show_relation_labels and (key in highlighted or selected_edge)):
                edge_label_requests.append(
                    (
                        edge_source,
                        edge_target,
                        str(relation.get("relation") or ""),
                        key in highlighted or selected_edge,
                    )
                )

        label_font = QFont(self.font())
        label_font.setPointSize(8)
        label_font.setBold(True)
        label_metrics = QFontMetrics(label_font)
        label_budget = len(visible_nodes) if len(visible_nodes) <= 24 else min(len(visible_nodes), 22)
        ranked_label_names = {
            name
            for name, _entity_type in sorted(
                visible_nodes,
                key=lambda item: (-self._node_weight(item[0], degrees, counts), item[1], item[0]),
            )[:label_budget]
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
            is_hovered = name == self._hovered_node_name
            self._draw_node(painter, point, radius, color, colors, is_selected, is_hovered)
            should_label = is_selected or (self.show_labels and name in ranked_label_names) or (
                self.filter_text and self.filter_text in name.lower()
            ) or is_hovered
            if self.show_labels is False:
                should_label = is_selected or is_hovered or (self.filter_text and self.filter_text in name.lower())
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
                    force=is_selected or len(visible_nodes) <= 14,
                )

        edge_label_rects = list(occupied_label_rects)
        for edge_source, edge_target, relation_name, force_relation_label in edge_label_requests:
            self._draw_edge_label(
                painter,
                edge_source,
                edge_target,
                relation_name,
                graph_rect,
                colors,
                edge_label_rects,
                force=force_relation_label,
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
        if hovered != self._hovered_node_name:
            self._hovered_node_name = hovered
            self.update()
        self.setToolTip(hovered or "")
        super().mouseMoveEvent(event)

    def leaveEvent(self, event) -> None:
        if self._hovered_node_name:
            self._hovered_node_name = ""
            self.update()
        super().leaveEvent(event)

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


class KnowledgeRefreshWorker(QObject):
    """在后台线程收集知识库状态和检索证据。"""

    finished = pyqtSignal(dict)
    failed = pyqtSignal(str)

    def __init__(self, task: dict[str, Any] | None, query_text: str | None, load_evidence: bool) -> None:
        super().__init__()
        self.task = task
        self.query_text = query_text
        self.load_evidence = load_evidence

    def run(self) -> None:
        try:
            knowledge_base = DomainKnowledgeBase()
            ingestion_service = KnowledgeIngestionService()
            status = knowledge_base.status()
            ingest_status = ingestion_service.status()
            merged_status = {**status, **ingest_status}
            if self.load_evidence:
                evidence_payload = self._retrieve_evidence(knowledge_base)
            else:
                evidence_payload = {"query": "", "chunks": [], "relations": []}
            self.finished.emit(
                {
                    "status": merged_status,
                    "evidence": evidence_payload,
                    "documents": _read_document_rows(getattr(ingestion_service, "documents_path", None)),
                    "query_text": self.query_text,
                    "task": self.task,
                }
            )
        except Exception as exc:
            self.failed.emit(str(exc))

    def _retrieve_evidence(self, knowledge_base: DomainKnowledgeBase) -> dict[str, Any]:
        if self.query_text is not None:
            query = self.query_text.strip() or DEFAULT_EVIDENCE_QUERY
            return knowledge_base.retrieve_by_query(query, top_k=5, kg_top_k=8)
        if self.task:
            return knowledge_base.retrieve(self.task, top_k=5, kg_top_k=8)
        return knowledge_base.retrieve_by_query(DEFAULT_EVIDENCE_QUERY, top_k=5, kg_top_k=8)


class KnowledgeWidget(QWidget):
    """管理项目内可更新 RAG/KG 知识库并展示检索证据。"""

    pipelineChanged = pyqtSignal(list)
    refreshed = pyqtSignal()

    def __init__(self) -> None:
        super().__init__()
        self.knowledge_base = DomainKnowledgeBase()
        self.ingestion_service = KnowledgeIngestionService()
        self.theme = "dark"
        self._last_task: dict[str, Any] | None = None
        self._last_merged_status: dict[str, Any] = {}
        self._ingest_thread: QThread | None = None
        self._ingest_worker: KnowledgeIngestWorker | None = None
        self._maintenance_thread: QThread | None = None
        self._maintenance_worker: KnowledgeMaintenanceWorker | None = None
        self._refresh_thread: QThread | None = None
        self._refresh_worker: KnowledgeRefreshWorker | None = None
        self._pending_refresh_request: tuple[dict[str, Any] | None, str | None, bool] | None = None
        self._pending_parser_notice: tuple[str, str] | None = None

        self.store_pill = StatusPill("知识库待入库", "pending")
        self.rag_pill = StatusPill("RAG 0 文本块", "pending")
        self.vector_pill = StatusPill("Vector 0 向量块", "pending")
        self.kg_pill = StatusPill("KG 0 关系", "pending")
        self.parser_pill = StatusPill("解析器待调用", "pending")
        self.case_pill = StatusPill("案例库 0 条", "pending")

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

        self.document_overview_label = self._make_panel_label()
        self.document_overview_scroll = self._scrollable_panel(self.document_overview_label)
        self._set_document_empty_html()

        self.source_overview_label = self._make_panel_label()
        self.source_overview_scroll = self._scrollable_panel(self.source_overview_label)

        self.pipeline_widget = PipelineStatusWidget("入库流水线 · PIPELINE")
        self.pipeline_widget.setMinimumHeight(174)
        self.pipeline_widget.setMaximumHeight(188)
        self.graph_view = KnowledgeGraphView()
        self.graph_view.setMinimumHeight(360)
        self.graph_summary_label = QLabel("核心图谱等待知识库数据")
        self.graph_summary_label.setObjectName("graphSummaryLabel")
        self.graph_summary_label.setWordWrap(False)
        self.graph_summary_label.setMinimumWidth(0)
        self.graph_summary_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.graph_summary_label.setFixedHeight(28)
        self.graph_summary_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.graph_search_input = QLineEdit()
        self.graph_search_input.setObjectName("graphSearchInput")
        self.graph_search_input.setPlaceholderText("搜索图谱节点或关系")
        self.graph_type_filter = QComboBox()
        self.graph_type_filter.setObjectName("graphFilterCombo")
        self.graph_relation_filter = QComboBox()
        self.graph_relation_filter.setObjectName("graphFilterCombo")
        for combo in [self.graph_type_filter, self.graph_relation_filter]:
            combo.setMinimumWidth(250)
            combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
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
        self.graph_relation_button = QPushButton("线标")
        self.graph_relation_button.setToolTip("显示或隐藏关系标签")
        self.graph_relation_button.setCheckable(True)
        self.graph_relation_button.setChecked(True)
        for button in [
            self.graph_reset_button,
            self.graph_zoom_in_button,
            self.graph_zoom_out_button,
            self.graph_label_button,
            self.graph_relation_button,
        ]:
            button.setObjectName("graphToolButton")
            button.setFixedSize(70 if button is self.graph_relation_button else 32, 28)
        self.graph_relation_button.setObjectName("graphRelationButton")
        self.graph_relation_button.setFixedSize(70, 28)
        self.graph_detail_browser = QTextBrowser()
        self.graph_detail_browser.setOpenExternalLinks(False)
        self._configure_panel_browser(self.graph_detail_browser)
        self.graph_detail_browser.setMinimumWidth(220)
        self.graph_detail_browser.setMinimumHeight(74)
        self.graph_type_chip_layout: QGridLayout | None = None
        self.graph_relation_chip_layout: QGridLayout | None = None
        self.graph_type_chip_buttons: list[QPushButton] = []
        self.graph_relation_chip_buttons: list[QPushButton] = []
        self.evidence_browser = QTextBrowser()
        self.evidence_browser.setOpenExternalLinks(True)
        self._configure_panel_browser(self.evidence_browser)
        self.evidence_browser.setMinimumHeight(74)
        self.summary_label = self._make_panel_label()
        self.summary_scroll = self._scrollable_panel(self.summary_label)
        self._summary_html_cache = ""
        for overview_scroll in [self.summary_scroll, self.source_overview_scroll, self.document_overview_scroll]:
            overview_scroll.setMinimumHeight(58)
            overview_scroll.setMaximumHeight(72)
            overview_scroll.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self._build_layout()
        self._connect_signals()

    def _set_pipeline_steps(self, steps: list) -> None:
        self.pipeline_widget.set_steps(steps)
        self.pipelineChanged.emit(steps)

    def _make_panel_label(self) -> QLabel:
        label = QLabel()
        label.setObjectName("knowledgeBodyLabel")
        label.setTextFormat(Qt.TextFormat.PlainText)
        label.setWordWrap(True)
        label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        return label

    def _scrollable_panel(self, label: QLabel) -> QScrollArea:
        scroll = QScrollArea()
        scroll.setObjectName("knowledgeTextScroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setAutoFillBackground(False)
        scroll.viewport().setAutoFillBackground(False)
        scroll.setStyleSheet("background: transparent; border: none;")
        scroll.setWidget(label)
        return scroll

    def _configure_panel_browser(self, browser: QTextBrowser) -> None:
        browser.setObjectName("knowledgePanelBrowser")
        browser.setFrameShape(QFrame.Shape.NoFrame)
        browser.document().setDocumentMargin(8)
        browser.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        browser.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        browser.setAutoFillBackground(False)
        browser.viewport().setAutoFillBackground(False)
        browser.viewport().setStyleSheet("background: transparent;")

    def _panel_html(self, body: str) -> str:
        if self.theme == "light":
            text = "#172033"
            muted = "#64748b"
            strong = "#0f172a"
        else:
            text = "#dbe4ef"
            muted = "#94a3b8"
            strong = "#f3f7fb"
        return (
            "<html><head><style>"
            "body{margin:0;padding:0;background:transparent;"
            "font-family:'Microsoft YaHei UI','Segoe UI',Arial,sans-serif;"
            f"font-size:13px;line-height:1.42;color:{text};}}"
            "p{margin:0 0 7px 0;}"
            f"b{{color:{strong};font-weight:800;}}"
            f".muted{{color:{muted};}}"
            ".metric{font-size:17px;font-weight:800;}"
            "</style></head><body>"
            f"{body}"
            "</body></html>"
        )

    def _browser_html(self, body: str) -> str:
        if self.theme == "light":
            text = "#172033"
            muted = "#64748b"
            strong = "#0f172a"
        else:
            text = "#dbe4ef"
            muted = "#94a3b8"
            strong = "#f3f7fb"
        return (
            "<html><head><style>"
            "body{margin:0;padding:0;background:transparent;"
            "font-family:'Microsoft YaHei UI','Segoe UI',Arial,sans-serif;"
            f"font-size:13px;line-height:1.42;color:{text};}}"
            "p{margin:0 0 8px 0;}"
            "h4{margin:2px 0 8px 0;padding:0;font-size:14px;line-height:1.35;}"
            f"h4,b{{color:{strong};font-weight:800;}}"
            f".muted{{color:{muted};}}"
            "</style></head><body>"
            f"{body}"
            "</body></html>"
        )

    def _set_document_empty_html(self) -> None:
        self.document_overview_label.setText(
            "等待入库资料。资料完成解析后显示解析器、Chunk、SHA256、入库时间和路径。\n"
            "支持 token 分块、overlap、内容去重、向量索引和 KG 实体关系抽取。"
        )

    def set_theme(self, theme: str) -> None:
        self.theme = resolve_theme(theme)
        for pill in [self.store_pill, self.rag_pill, self.vector_pill, self.kg_pill, self.parser_pill, self.case_pill]:
            pill.set_theme(self.theme)
        self.pipeline_widget.set_theme(self.theme)
        self.graph_view.set_theme(self.theme)

    def _build_layout(self) -> None:
        top_layout = QHBoxLayout()
        top_layout.setSpacing(8)
        top_layout.addWidget(self.search_input, 1)
        top_layout.addWidget(self.search_button)

        action_layout = QGridLayout()
        action_layout.setContentsMargins(0, 0, 0, 0)
        action_layout.setHorizontalSpacing(8)
        action_layout.setVerticalSpacing(8)
        for index, button in enumerate(
            [self.upload_button, self.batch_button, self.rebuild_button, self.export_snapshot_button, self.refresh_button]
        ):
            action_layout.addWidget(button, 0, index)
            action_layout.setColumnStretch(index, 1)

        pill_layout = QGridLayout()
        pill_layout.setContentsMargins(0, 0, 0, 0)
        pill_layout.setHorizontalSpacing(8)
        pill_layout.setVerticalSpacing(8)
        for index, pill in enumerate(
            [self.store_pill, self.rag_pill, self.vector_pill, self.kg_pill, self.parser_pill, self.case_pill]
        ):
            row = index // 3
            column = index % 3
            pill_layout.addWidget(pill, row, column)
            pill_layout.setColumnStretch(column, 1)

        def titled_panel(title: str, widget: QWidget, object_name: str = "knowledgeMiniPanel") -> QFrame:
            card = QFrame()
            card.setObjectName(object_name)
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(12, 10, 12, 10)
            card_layout.setSpacing(6)
            label = QLabel(title)
            label.setObjectName("knowledgePanelTitle")
            label.setFixedHeight(22)
            label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            card_layout.addWidget(label)
            card_layout.addWidget(widget, 1)
            return card

        overview_panel = QFrame()
        overview_panel.setObjectName("knowledgeOverviewPanel")
        overview_panel.setMinimumHeight(112)
        overview_panel.setMaximumHeight(124)
        overview_layout = QHBoxLayout(overview_panel)
        overview_layout.setContentsMargins(10, 8, 10, 8)
        overview_layout.setSpacing(10)
        overview_layout.addWidget(titled_panel("资料状态 · STATUS", self.summary_scroll), 1)
        overview_layout.addWidget(titled_panel("知识来源 · SOURCES", self.source_overview_scroll), 1)
        overview_layout.addWidget(titled_panel("资料库 · DOCUMENTS", self.document_overview_scroll), 1)
        self.overview_panel = overview_panel

        graph_panel = QFrame()
        graph_panel.setObjectName("knowledgeGraphPanel")
        graph_panel.setMinimumHeight(458)
        graph_panel.setMaximumHeight(500)
        graph_layout = QVBoxLayout(graph_panel)
        graph_layout.setContentsMargins(8, 3, 8, 7)
        graph_layout.setSpacing(0)
        graph_header = QHBoxLayout()
        graph_header.setContentsMargins(0, 0, 0, 0)
        graph_header.setSpacing(8)
        graph_label = QLabel("知识图谱 · GRAPH")
        graph_label.setObjectName("graphHeaderTitle")
        graph_label.setMinimumWidth(graph_label.fontMetrics().horizontalAdvance(graph_label.text()) + 6)
        graph_label.setFixedHeight(28)
        graph_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        graph_header.addWidget(graph_label, 0, Qt.AlignmentFlag.AlignVCenter)
        graph_header.addWidget(self.graph_summary_label, 1, Qt.AlignmentFlag.AlignVCenter)
        graph_header.addWidget(self.graph_reset_button, 0, Qt.AlignmentFlag.AlignVCenter)
        graph_header.addWidget(self.graph_zoom_in_button, 0, Qt.AlignmentFlag.AlignVCenter)
        graph_header.addWidget(self.graph_zoom_out_button, 0, Qt.AlignmentFlag.AlignVCenter)
        graph_header.addWidget(self.graph_label_button, 0, Qt.AlignmentFlag.AlignVCenter)
        graph_header.addWidget(self.graph_relation_button, 0, Qt.AlignmentFlag.AlignVCenter)
        graph_layout.addLayout(graph_header)

        graph_filter_panel = QFrame()
        graph_filter_panel.setObjectName("graphFilterPanel")
        graph_filter_panel.setMinimumHeight(34)
        graph_filter_panel.setMaximumHeight(36)
        self.graph_filter_panel = graph_filter_panel
        graph_filter_layout = QHBoxLayout(graph_filter_panel)
        graph_filter_layout.setContentsMargins(8, 1, 8, 1)
        graph_filter_layout.setSpacing(8)
        self.graph_type_filter.setVisible(True)
        self.graph_relation_filter.setVisible(True)
        graph_filter_layout.addWidget(self.graph_search_input, 3)
        graph_filter_layout.addWidget(self.graph_type_filter, 1)
        graph_filter_layout.addWidget(self.graph_relation_filter, 1)
        hidden_type_chip_widget = QWidget(graph_filter_panel)
        hidden_relation_chip_widget = QWidget(graph_filter_panel)
        hidden_type_chip_widget.hide()
        hidden_relation_chip_widget.hide()
        self.graph_type_chip_layout = QGridLayout(hidden_type_chip_widget)
        self.graph_type_chip_layout.setContentsMargins(0, 0, 0, 0)
        self.graph_type_chip_layout.setHorizontalSpacing(6)
        self.graph_type_chip_layout.setVerticalSpacing(6)
        self.graph_relation_chip_layout = QGridLayout(hidden_relation_chip_widget)
        self.graph_relation_chip_layout.setContentsMargins(0, 0, 0, 0)
        self.graph_relation_chip_layout.setHorizontalSpacing(6)
        self.graph_relation_chip_layout.setVerticalSpacing(6)
        graph_layout.addWidget(graph_filter_panel, 0)
        graph_layout.addWidget(self.graph_view, 2)

        evidence_panel = QFrame()
        evidence_panel.setObjectName("knowledgeEvidencePanel")
        evidence_panel.setMinimumHeight(220)
        evidence_layout = QVBoxLayout(evidence_panel)
        evidence_layout.setContentsMargins(12, 12, 12, 12)
        evidence_layout.setSpacing(8)
        evidence_label = QLabel("图谱审计与检索证据 · EVIDENCE")
        evidence_label.setObjectName("sectionTitle")
        evidence_label.setMinimumHeight(24)
        evidence_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        evidence_layout.addWidget(evidence_label)
        evidence_splitter = QSplitter(Qt.Orientation.Horizontal)
        evidence_splitter.addWidget(titled_panel("图谱审计", self.graph_detail_browser))
        evidence_splitter.addWidget(titled_panel("混合检索结果", self.evidence_browser))
        evidence_splitter.setChildrenCollapsible(False)
        evidence_splitter.setMinimumHeight(132)
        evidence_splitter.setSizes([360, 720])
        evidence_splitter.setStretchFactor(0, 0)
        evidence_splitter.setStretchFactor(1, 1)
        evidence_layout.addWidget(evidence_splitter, 1)

        main = QWidget()
        main.setMinimumWidth(0)
        main.setMinimumHeight(840)
        main_layout = QVBoxLayout(main)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(6)
        main_layout.addWidget(overview_panel, 0)
        main_layout.addWidget(graph_panel, 2)
        main_layout.addWidget(evidence_panel, 0)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)
        layout.addLayout(top_layout)
        layout.addLayout(action_layout)
        layout.addLayout(pill_layout)
        main_scroll = QScrollArea()
        main_scroll.setObjectName("knowledgeMainScroll")
        main_scroll.setFrameShape(QFrame.Shape.NoFrame)
        main_scroll.setWidgetResizable(True)
        main_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        main_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        main_scroll.setStyleSheet("background: transparent; border: none;")
        main_scroll.setWidget(main)
        layout.addWidget(main_scroll, 1)

    def _connect_signals(self) -> None:
        self.search_button.clicked.connect(self._search_from_input)
        self.search_input.returnPressed.connect(self._search_from_input)
        self.upload_button.clicked.connect(self._select_and_ingest_file)
        self.batch_button.clicked.connect(self._select_and_ingest_files)
        self.rebuild_button.clicked.connect(lambda: self._run_maintenance("rebuild"))
        self.export_snapshot_button.clicked.connect(lambda: self._run_maintenance("export"))
        self.refresh_button.clicked.connect(lambda: self.refresh_async(load_evidence=False))
        self.graph_search_input.returnPressed.connect(self._filter_graph_from_input)
        self.graph_search_input.textChanged.connect(self._on_graph_filter_text_changed)
        self.graph_type_filter.currentIndexChanged.connect(self._apply_graph_filters_from_controls)
        self.graph_relation_filter.currentIndexChanged.connect(self._apply_graph_filters_from_controls)
        self.graph_reset_button.clicked.connect(self.graph_view.reset_view)
        self.graph_zoom_in_button.clicked.connect(lambda: self.graph_view.zoom_by(1.18))
        self.graph_zoom_out_button.clicked.connect(lambda: self.graph_view.zoom_by(0.84))
        self.graph_label_button.toggled.connect(self.graph_view.set_show_labels)
        self.graph_relation_button.toggled.connect(self.graph_view.set_show_relation_labels)
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
        self._last_merged_status = dict(merged_status)
        self._update_status_pills(merged_status)
        self._update_summary(merged_status)
        self._update_source_overview(merged_status)
        self._update_document_table(_read_document_rows(getattr(self.ingestion_service, "documents_path", None)))
        self._update_pipeline(merged_status)
        evidence_payload = self._retrieve_evidence(task, query_text) if load_evidence else {"query": "", "chunks": [], "relations": []}
        self._update_graph_view(evidence_payload)
        self._set_evidence_payload(evidence_payload)
        self.refreshed.emit()

    def refresh_async(
        self,
        task: dict[str, Any] | None = None,
        query_text: str | None = None,
        load_evidence: bool = True,
    ) -> None:
        if task is not None:
            self._last_task = task
        if query_text is not None:
            query = query_text.strip() or DEFAULT_EVIDENCE_QUERY
            self.search_input.setText(query)
            query_text = query
        if self._refresh_thread is not None:
            self._pending_refresh_request = (task, query_text, load_evidence)
            return
        self._refresh_thread = QThread(self)
        self._refresh_worker = KnowledgeRefreshWorker(task, query_text, load_evidence)
        self._refresh_worker.moveToThread(self._refresh_thread)
        self._refresh_thread.started.connect(self._refresh_worker.run)
        self._refresh_worker.finished.connect(self._on_refresh_finished)
        self._refresh_worker.failed.connect(self._on_refresh_failed)
        self._refresh_worker.finished.connect(self._cleanup_refresh_worker)
        self._refresh_worker.failed.connect(self._cleanup_refresh_worker)
        self._refresh_thread.start()

    def current_status(self) -> dict[str, Any]:
        return dict(self._last_merged_status)

    def _stop_worker_thread(self, thread_attr: str, worker_attr: str) -> None:
        thread = getattr(self, thread_attr, None)
        if thread is None:
            setattr(self, worker_attr, None)
            return
        if thread is QThread.currentThread():
            return
        if thread.isRunning():
            thread.quit()
            if not thread.wait(3000):
                thread.terminate()
                thread.wait(1000)
        setattr(self, thread_attr, None)
        setattr(self, worker_attr, None)

    def shutdown_workers(self) -> None:
        self._pending_refresh_request = None
        self._stop_worker_thread("_refresh_thread", "_refresh_worker")
        self._stop_worker_thread("_ingest_thread", "_ingest_worker")
        self._stop_worker_thread("_maintenance_thread", "_maintenance_worker")
        self._set_operation_buttons_enabled(True)

    def closeEvent(self, event) -> None:
        self.shutdown_workers()
        super().closeEvent(event)

    def _on_refresh_finished(self, payload: dict) -> None:
        status = payload.get("status") if isinstance(payload.get("status"), dict) else {}
        documents = payload.get("documents") if isinstance(payload.get("documents"), list) else []
        evidence_payload = payload.get("evidence") if isinstance(payload.get("evidence"), dict) else {"query": "", "chunks": [], "relations": []}
        self._last_merged_status = dict(status)
        self._update_status_pills(status)
        if self._pending_parser_notice is not None:
            label, notice_status = self._pending_parser_notice
            self.parser_pill.set_state(label, notice_status)
            self._pending_parser_notice = None
        self._update_summary(status)
        self._update_source_overview(status)
        self._update_document_table(documents)
        self._update_pipeline(status)
        self._update_graph_view(evidence_payload)
        self._set_evidence_payload(evidence_payload)
        self.refreshed.emit()

    def _on_refresh_failed(self, message: str) -> None:
        self._set_evidence_html(f"<h3>知识库刷新失败</h3><p>{escape(message)}</p>", scrollable=True)
        self.refreshed.emit()

    def _cleanup_refresh_worker(self) -> None:
        if self._refresh_thread is not None:
            self._refresh_thread.quit()
            self._refresh_thread.wait()
        self._refresh_thread = None
        self._refresh_worker = None
        pending = self._pending_refresh_request
        self._pending_refresh_request = None
        if pending is not None:
            task, query_text, load_evidence = pending
            self.refresh_async(task, query_text=query_text, load_evidence=load_evidence)

    def toHtml(self) -> str:
        """兼容测试和外部读取当前 HTML 摘要。"""
        return (self._summary_html_cache or self.summary_label.text()) + self.evidence_browser.toHtml()

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
        self._set_pipeline_steps(
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
            self.graph_type_filter,
            self.graph_relation_filter,
            self.graph_reset_button,
            self.graph_zoom_in_button,
            self.graph_zoom_out_button,
            self.graph_label_button,
            self.graph_relation_button,
        ]:
            button.setEnabled(enabled)

    def _filter_graph_from_input(self) -> None:
        self.graph_view.set_filter_text(self.graph_search_input.text())
        self._update_graph_detail("")

    def _on_graph_filter_text_changed(self, value: str) -> None:
        self.graph_view.set_filter_text(value)
        self._update_graph_detail("")

    def _populate_graph_filter_combo(
        self,
        combo: QComboBox,
        placeholder: str,
        entries: list[tuple[str, int]],
        current_value: str,
    ) -> None:
        combo.blockSignals(True)
        combo.clear()
        combo.addItem(placeholder, "")
        for name, count in entries[:24]:
            combo.addItem(f"{name} ({count})", name)
        index = combo.findData(current_value)
        combo.setCurrentIndex(index if index >= 0 else 0)
        combo.blockSignals(False)

    def _clear_graph_chip_layout(self, layout: QGridLayout | None) -> None:
        if layout is None:
            return
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def _create_graph_chip(self, label: str, count: int, color: str, checked: bool, tooltip: str) -> GraphChipButton:
        button = GraphChipButton(label, count, color, self.theme)
        button.setObjectName("graphChipButton")
        button.setChecked(checked)
        button.setToolTip(tooltip)
        return button

    def _rebuild_graph_filter_chips(
        self,
        type_entries: list[tuple[str, int]],
        relation_entries: list[tuple[str, int]],
    ) -> None:
        self._clear_graph_chip_layout(self.graph_type_chip_layout)
        self._clear_graph_chip_layout(self.graph_relation_chip_layout)
        self.graph_type_chip_buttons = []
        self.graph_relation_chip_buttons = []

        def add_chip(layout: QGridLayout | None, button: QPushButton, index: int) -> None:
            if layout is None:
                return
            layout.addWidget(button, index // 4, index % 4)

        for index, (name, count) in enumerate(type_entries[:8]):
            color = self.graph_view._type_color(name).name()
            checked = name in self.graph_view.active_node_types
            button = self._create_graph_chip(name, count, color, checked, f"按节点类型过滤：{name}")
            button.toggled.connect(lambda _checked: self._apply_graph_chip_filters())
            self.graph_type_chip_buttons.append(button)
            add_chip(self.graph_type_chip_layout, button, index)
        for index, (name, count) in enumerate(relation_entries[:8]):
            color = "#38bdf8" if self.theme != "light" else "#2563eb"
            checked = name in self.graph_view.active_relation_types
            button = self._create_graph_chip(name, count, color, checked, f"按关系类型过滤：{name}")
            button.toggled.connect(lambda _checked: self._apply_graph_chip_filters())
            self.graph_relation_chip_buttons.append(button)
            add_chip(self.graph_relation_chip_layout, button, index)

    def _refresh_graph_filter_options(self) -> None:
        type_entries, relation_entries = self.graph_view.filter_options()
        current_type = str(self.graph_type_filter.currentData() or "")
        current_relation = str(self.graph_relation_filter.currentData() or "")
        self._populate_graph_filter_combo(self.graph_type_filter, "全部节点类型", type_entries, current_type)
        self._populate_graph_filter_combo(self.graph_relation_filter, "全部关系类型", relation_entries, current_relation)
        self._rebuild_graph_filter_chips(type_entries, relation_entries)

    def _sync_graph_combos_from_filters(self) -> None:
        type_value = next(iter(self.graph_view.active_node_types), "") if len(self.graph_view.active_node_types) == 1 else ""
        relation_value = (
            next(iter(self.graph_view.active_relation_types), "") if len(self.graph_view.active_relation_types) == 1 else ""
        )
        for combo, value in [(self.graph_type_filter, type_value), (self.graph_relation_filter, relation_value)]:
            combo.blockSignals(True)
            index = combo.findData(value)
            combo.setCurrentIndex(index if index >= 0 else 0)
            combo.blockSignals(False)

    def _sync_graph_chips_from_filters(self) -> None:
        for button in self.graph_type_chip_buttons:
            value = getattr(button, "value", button.toolTip().replace("按节点类型过滤：", ""))
            button.blockSignals(True)
            button.setChecked(value in self.graph_view.active_node_types)
            if isinstance(button, GraphChipButton):
                button.set_theme(self.theme)
            button.blockSignals(False)
        relation_color = "#38bdf8" if self.theme != "light" else "#2563eb"
        for button in self.graph_relation_chip_buttons:
            value = getattr(button, "value", button.toolTip().replace("按关系类型过滤：", ""))
            button.blockSignals(True)
            button.setChecked(value in self.graph_view.active_relation_types)
            if isinstance(button, GraphChipButton):
                button.accent_color = QColor(relation_color)
                button.set_theme(self.theme)
            button.blockSignals(False)

    def _apply_graph_chip_filters(self) -> None:
        node_types = {
            getattr(button, "value", button.toolTip().replace("按节点类型过滤：", ""))
            for button in self.graph_type_chip_buttons
            if button.isChecked()
        }
        relation_types = {
            getattr(button, "value", button.toolTip().replace("按关系类型过滤：", ""))
            for button in self.graph_relation_chip_buttons
            if button.isChecked()
        }
        self.graph_view.set_type_filter(node_types)
        self.graph_view.set_relation_filter(relation_types)
        self._sync_graph_combos_from_filters()
        self._update_graph_detail("")

    def _apply_graph_filters_from_controls(self) -> None:
        node_type = str(self.graph_type_filter.currentData() or "")
        relation_type = str(self.graph_relation_filter.currentData() or "")
        self.graph_view.set_type_filter({node_type} if node_type else set())
        self.graph_view.set_relation_filter({relation_type} if relation_type else set())
        self._sync_graph_chips_from_filters()
        self._update_graph_detail("")

    def _on_ingest_progress(self, steps: list) -> None:
        self._set_pipeline_steps(steps)
        active_step = next((step for step in steps if isinstance(step, dict) and step.get("status") == "running"), None)
        if isinstance(active_step, dict):
            self.parser_pill.set_state(str(active_step.get("name") or "入库运行中"), "running")

    def _on_ingest_finished(self, payload: dict) -> None:
        results = payload.get("results") if isinstance(payload.get("results"), list) else []
        last_result = results[-1] if results else payload
        steps = last_result.get("steps") if isinstance(last_result.get("steps"), list) else []
        self._set_pipeline_steps(steps)
        success_count = int(payload.get("batch_success_count") or (1 if payload.get("success") else 0))
        failed_count = int(payload.get("batch_failed_count") or 0)
        status = "warning" if failed_count else "success"
        label = f"入库完成 {success_count} / 失败 {failed_count}" if payload.get("batch_total") else f"{payload.get('parser_backend') or '解析'} 完成"
        self.parser_pill.set_state(label, status)
        try:
            ingest_status = dict(self.ingestion_service.status())
            immediate_status = {
                **ingest_status,
                "ready": True,
                "last_ingestion": last_result,
            }
            immediate_status.setdefault("rag_chunk_count", sum(int(item.get("chunk_count") or 0) for item in results))
            immediate_status.setdefault("kg_entity_count", sum(int(item.get("entity_count") or 0) for item in results))
            immediate_status.setdefault("kg_relation_count", sum(int(item.get("relation_count") or 0) for item in results))
            self._last_merged_status = {**self._last_merged_status, **immediate_status}
            self._update_status_pills(self._last_merged_status)
            self.parser_pill.set_state(label, status)
            self._update_document_table(_read_document_rows(getattr(self.ingestion_service, "documents_path", None)))
            self._update_pipeline(self._last_merged_status)
            self.refreshed.emit()
        except Exception:
            pass
        failure_html = ""
        if failed_count:
            failures = payload.get("failures") if isinstance(payload.get("failures"), list) else []
            detail = "<br>".join(escape(f"{Path(str(item.get('path') or '')).name}: {item.get('error') or ''}") for item in failures)
            failure_html = f"<h3>批量入库部分失败</h3><p>{detail}</p>"
        self.refresh_async(query_text=self.search_input.text().strip() or DEFAULT_EVIDENCE_QUERY)
        if failure_html:
            self._set_evidence_html(failure_html, scrollable=True)

    def _on_ingest_failed(self, message: str) -> None:
        self.parser_pill.set_state("解析失败", "failed")
        self._set_pipeline_steps(
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
            self._set_pipeline_steps(
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
                self._set_pipeline_steps(steps)
            self.refresh_async(query_text=self.search_input.text().strip() or DEFAULT_EVIDENCE_QUERY)
            self._pending_parser_notice = ("索引重建完成", "success")
            self.parser_pill.set_state("索引重建完成", "success")
            return
        if operation == "export":
            path = str(payload.get("path") or "")
            self._pending_parser_notice = ("快照已导出", "success")
            self.parser_pill.set_state("快照已导出", "success")
            self._set_evidence_html(f"<h3>知识库快照已导出</h3><p>{escape(path)}</p>", scrollable=True)

    def _on_maintenance_failed(self, message: str) -> None:
        self.parser_pill.set_state("维护失败", "failed")
        self._set_evidence_html(f"<h3>知识库维护失败</h3><p>{escape(message)}</p>", scrollable=True)

    def _search_from_input(self) -> None:
        query = self.search_input.text().strip() or DEFAULT_EVIDENCE_QUERY
        self.search_input.setText(query)
        self.refresh_async(query_text=query)

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
        self._refresh_graph_filter_options()
        self._apply_graph_filters_from_controls()
        self._update_graph_detail(self.graph_view.selected_node_name())

    def _update_graph_summary_label(
        self,
        visible_nodes: list[tuple[str, str]],
        visible_relations: list[dict[str, Any]],
        total_nodes: int,
        total_relations: int,
    ) -> None:
        active_filters = []
        if self.graph_search_input.text().strip():
            active_filters.append("搜索")
        if str(self.graph_type_filter.currentData() or ""):
            active_filters.append("节点类型")
        if str(self.graph_relation_filter.currentData() or ""):
            active_filters.append("关系类型")
        filter_text = f" · 过滤 {'/'.join(active_filters)}" if active_filters else ""
        self.graph_summary_label.setText(
            f"{total_nodes} 实体 / {total_relations} 关系 · 可见 {len(visible_nodes)} / {len(visible_relations)}{filter_text}"
        )

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
        self._update_graph_summary_label(visible_nodes, visible_relations, total_nodes, total_relations)
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

        html: list[str] = []
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
                        f"<div style='margin:5px 0;color:{foreground};'>"
                        f"<span style='display:inline-block;width:8px;height:8px;border-radius:4px;background:{color};'></span>"
                        f"<span style='margin-left:7px;'>{escape(entity_type)}</span>"
                        f"<span style='color:{muted};'>&nbsp;&nbsp;{count}</span>"
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
        self.graph_detail_browser.setHtml(self._browser_html("".join(html)))

    def _update_status_pills(self, status: dict[str, Any]) -> None:
        ready = bool(status.get("ready"))
        doc_count = int(status.get("runtime_document_count", status.get("document_count", 0)) or 0)
        chunk_count = int(status.get("rag_chunk_count", 0) or 0)
        vector_count = int(status.get("vector_chunk_count", 0) or 0)
        vector_status = str(status.get("vector_status") or "")
        vector_ready = bool(status.get("vector_ready")) and vector_status == "success"
        relation_count = int(status.get("kg_relation_count", 0) or 0)
        parser = (status.get("last_ingestion") or {}).get("parser_backend") if isinstance(status.get("last_ingestion"), dict) else ""
        self.store_pill.set_state(f"合并 RAG {chunk_count} 块", "success" if ready else "pending")
        self.rag_pill.set_state(f"RAG {chunk_count} 块", "success" if chunk_count else "pending")
        vector_label = f"Vector {vector_count} 向量块" if vector_count else f"Vector {vector_status or 'pending'}"
        vector_state = "success" if vector_ready else ("warning" if vector_status in {"warning", "failed"} else "pending")
        self.vector_pill.set_state(vector_label, vector_state)
        self.kg_pill.set_state(f"KG {relation_count} 关系", "success" if relation_count else "pending")
        self.parser_pill.set_state(str(parser or "解析器待调用"), "success" if parser else "pending")
        case_count = len(list(CASES_DIR.glob("CASE_*.json"))) + len(list(CASE_LIBRARY_DIR.glob("CASE_*.json")))
        self.case_pill.set_state(f"案例库 {case_count} 条", "success" if case_count else "pending")

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
        display_lines = [
            f"内置数据：{builtin_chunks} 文本块，{status.get('builtin_kg_entity_count', 0)} 实体，{builtin_relations} 关系。",
            f"用户增量：{doc_count} 文档，{runtime_chunks} 文本块，{runtime_relations} 关系。",
            f"合并索引：{status.get('rag_chunk_count', 0)} 文本块，{status.get('kg_entity_count', 0)} 实体，"
            f"{status.get('kg_relation_count', 0)} 关系。",
            f"案例记忆：会话案例 {len(archive_cases)}，正式案例 {len(formal_cases)}，ODB {odb_count}，云图 {vis_count}。",
            f"分块：{chunk_size} token / overlap {overlap}；Vector：{status.get('vector_status') or '-'}。",
        ]
        display_html = [
            "<p>项目知识库由内置数据和用户增量组成，检索入口读取合并后的总 RAG/KG。</p>",
            f"<p><b>内置数据：</b><span class='metric'>{builtin_chunks}</span> 文本块，"
            f"{status.get('builtin_kg_entity_count', 0)} 实体，{builtin_relations} 关系。</p>",
            f"<p><b>用户增量：</b>{doc_count} 文档，{runtime_chunks} 文本块，{runtime_relations} 关系。</p>",
            f"<p><b>合并索引：</b>{status.get('rag_chunk_count', 0)} 文本块，"
            f"{status.get('kg_entity_count', 0)} 实体，{status.get('kg_relation_count', 0)} 关系。</p>",
            f"<p><b>案例记忆：</b>会话案例 {len(archive_cases)}，正式案例 {len(formal_cases)}；"
            f"ODB {odb_count}，云图 {vis_count}。</p>",
        ]
        full_html = [
            *display_html,
            f"<p><b>分块：</b>{chunk_size} token / overlap {overlap}；"
            f"<b>Vector：</b>{status.get('vector_status') or '-'}。</p>",
            f"<p><b>最后入库：</b>{escape(str(last.get('title') or '-'))}；"
            f"<b>检索验证：</b>{escape(str(verification.get('message') or '-'))}</p>",
            f"<p class='muted'><b>清单：</b>{escape(str(status.get('manifest_path') or '-'))}；"
            f"内置 {escape(str(status.get('builtin_manifest_path') or '-'))}</p>",
        ]
        if metrics:
            full_html.append(
                "<p><b>代理模型：</b>"
                f"{escape(str(metrics.get('selected_model', '-')))}，训练样本 {escape(str(metrics.get('training_size', '-')))}</p>"
            )
        self._summary_html_cache = self._panel_html("".join(full_html))
        self.summary_label.setText("\n".join(display_lines))

    def _update_source_overview(self, status: dict[str, Any]) -> None:
        builtin_chunks = int(status.get("builtin_rag_chunk_count", 0) or 0)
        builtin_entities = int(status.get("builtin_kg_entity_count", 0) or 0)
        builtin_relations = int(status.get("builtin_kg_relation_count", 0) or 0)
        runtime_docs = int(status.get("runtime_document_count", status.get("document_count", 0)) or 0)
        runtime_chunks = int(status.get("runtime_rag_chunk_count", 0) or 0)
        runtime_relations = int(status.get("runtime_kg_relation_count", 0) or 0)
        vector_status = status.get("vector_status") or "pending"
        self.source_overview_label.setText(
            "\n".join(
                [
                    f"系统资料包：{builtin_chunks} 文本块，{builtin_entities} 实体，{builtin_relations} 关系。",
                    f"用户增量：{runtime_docs} 文档，{runtime_chunks} 文本块，{runtime_relations} 关系。",
                    f"合并索引：{status.get('rag_chunk_count', 0)} 文本块，{status.get('kg_entity_count', 0)} 实体，"
                    f"{status.get('kg_relation_count', 0)} 关系。",
                    f"案例记忆：会话案例 {len(list(CASES_DIR.glob('CASE_*.json')))}，"
                    f"正式案例 {len(list(CASE_LIBRARY_DIR.glob('CASE_*.json')))}。",
                    f"向量状态：{vector_status}；chunk {status.get('chunk_token_size', '-')} / "
                    f"overlap {status.get('chunk_overlap_tokens', '-')}。",
                ]
            )
        )

    def _html_card_style(self) -> str:
        if self.theme == "light":
            return "border:1px solid #c8d2df;border-radius:10px;padding:10px;margin:8px 0;background:#f8fafc;"
        return "border:1px solid #2b3a52;border-radius:10px;padding:10px;margin:8px 0;background:#111a28;"

    def _update_document_table(self, rows: list[dict[str, Any]] | None = None) -> None:
        if rows is None:
            rows = _read_document_rows(getattr(self.ingestion_service, "documents_path", None))
        self.document_table.setRowCount(len(rows))
        if not rows:
            self._set_document_empty_html()
            return
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
        latest = rows[-1]
        latest_title = latest.get("title") or latest.get("file_name") or latest.get("document_id") or "-"
        latest_parser = latest.get("parser_backend") or "-"
        latest_chunks = latest.get("chunk_count") or 0
        latest_hash = str(latest.get("file_sha256") or "")[:12] or "-"
        self.document_overview_label.setText(
            "\n".join(
                [
                    f"已入库资料：{len(rows)} 个文档，最近记录 {latest_title}。",
                    f"最近解析：{latest_parser}，{latest_chunks} 个 Chunk。",
                    f"内容指纹：{latest_hash}。",
                ]
            )
        )

    def _update_pipeline(self, status: dict[str, Any]) -> None:
        pipeline = status.get("pipeline") if isinstance(status.get("pipeline"), list) else []
        if pipeline:
            self._set_pipeline_steps(pipeline)
            return
        self._set_pipeline_steps(
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
        self.evidence_browser.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.evidence_browser.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.evidence_browser.setHtml(self._browser_html(html))

    def _page_text(self, item: dict[str, Any]) -> str:
        page_start = item.get("page_start")
        page_end = item.get("page_end")
        if page_start in (None, "", 0):
            return ""
        if page_end in (None, "", page_start, 0):
            return str(page_start)
        return f"{page_start}-{page_end}"

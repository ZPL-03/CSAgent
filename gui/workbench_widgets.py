"""工程工作台专用组件。"""

from __future__ import annotations

from dataclasses import dataclass

from PyQt6.QtCore import QPointF, QRectF, QSize, Qt
from PyQt6.QtGui import QBrush, QColor, QFont, QFontMetrics, QPainter, QPen
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout, QWidget

from gui.i18n import DEFAULT_LANGUAGE, text as tr
from gui.theme import resolve_theme


@dataclass(frozen=True)
class DagNode:
    name: str
    subtitle: str
    agent: str


@dataclass(frozen=True)
class PipelineStepView:
    name: str
    detail: str
    status: str = "pending"


def _status_color(status: str) -> QColor:
    if status in {"success", "done", "ready", "online"}:
        return QColor("#34d399")
    if status in {"running", "active", "warning"}:
        return QColor("#f59e0b")
    if status in {"failed", "error", "offline"}:
        return QColor("#ef4444")
    return QColor("#64748b")


class AgentStatusCard(QFrame):
    """左侧智能体状态卡片，保证状态灯、名称和状态行严格对齐。"""

    def __init__(self) -> None:
        super().__init__()
        self.theme = "dark"
        self.state = "waiting"
        self.setObjectName("agentStatusCard")
        self.setProperty("state", self.state)
        self.setFixedHeight(60)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        self.dot = QLabel()
        self.dot.setFixedSize(9, 9)

        self.title = QLabel()
        self.title.setObjectName("agentTitle")
        self.title.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        self.detail = QLabel()
        self.detail.setObjectName("agentDetail")
        self.detail.setWordWrap(True)
        self.detail.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(10)
        header_layout.addWidget(self.dot, 0, Qt.AlignmentFlag.AlignVCenter)
        header_layout.addWidget(self.title, 1, Qt.AlignmentFlag.AlignVCenter)

        text_layout = QVBoxLayout()
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(3)
        text_layout.addLayout(header_layout)
        text_layout.addWidget(self.detail)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 8, 14, 8)
        layout.setSpacing(0)
        layout.addLayout(text_layout, 1)

    def set_theme(self, theme: str) -> None:
        self.theme = resolve_theme(theme)
        self._sync_visuals()

    def set_content(self, agent_name: str, state: str, status_label: str, description: str) -> None:
        self.state = state
        self.setProperty("state", state)
        self.title.setText(agent_name)
        status_color = self._state_color()
        muted = "#475569" if self.theme == "light" else "#94a3b8"
        self.detail.setText(
            f"<span style='color:{status_color};font-weight:600;'>{status_label}</span>"
            f"<span style='color:{muted};'> · {description}</span>"
        )
        self._sync_visuals()

    def _state_color(self) -> str:
        if self.state == "done":
            return "#0f766e" if self.theme == "light" else "#34d399"
        if self.state == "active":
            return "#2563eb" if self.theme == "light" else "#f59e0b"
        if self.state == "failed":
            return "#dc2626" if self.theme == "light" else "#fb7185"
        return "#64748b"

    def _sync_visuals(self) -> None:
        color = self._state_color()
        text = "#172033" if self.theme == "light" else "#dbe4ef"
        self.dot.setStyleSheet(f"background:{color}; border-radius:4px;")
        self.title.setStyleSheet(f"background:transparent;color:{text};font-size:13px;font-weight:800;")
        self.detail.setStyleSheet("background:transparent;font-size:12px;")
        self.style().unpolish(self)
        self.style().polish(self)


class StatusPill(QWidget):
    """参考工程平台样式绘制带状态灯的胶囊标签。"""

    def __init__(self, text: str = "", status: str = "pending") -> None:
        super().__init__()
        self.text = text
        self.status = status
        self.theme = "dark"
        self.setMinimumSize(128, 32)
        self.setMaximumHeight(34)
        self._sync_width()

    def set_state(self, text: str, status: str) -> None:
        self.text = text
        self.status = status
        self._sync_width()
        self.update()

    def set_theme(self, theme: str) -> None:
        self.theme = resolve_theme(theme)
        self.update()

    def _sync_width(self) -> None:
        font = QFont(self.font())
        font.setPointSize(10)
        text_width = QFontMetrics(font).horizontalAdvance(self.text)
        self.setMinimumWidth(max(128, min(320, text_width + 56)))

    def sizeHint(self) -> QSize:
        return QSize(max(self.minimumWidth(), 128), 34)

    def _content_geometry(self, font: QFont) -> tuple[QPointF, QRectF, str]:
        dot_diameter = 11.0
        dot_gap = 9.0
        side_padding = 14.0
        metrics = QFontMetrics(font)
        available_text_width = max(24, int(self.width() - side_padding * 2 - dot_diameter - dot_gap))
        display_text = metrics.elidedText(self.text, Qt.TextElideMode.ElideRight, available_text_width)
        text_width = metrics.horizontalAdvance(display_text)
        content_width = dot_diameter + dot_gap + text_width
        left = max(side_padding, (self.width() - content_width) / 2.0)
        dot_center = QPointF(left + dot_diameter / 2.0, self.height() / 2.0)
        text_rect = QRectF(left + dot_diameter + dot_gap, 0, text_width + 2, self.height())
        return dot_center, text_rect, display_text

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        if self.theme == "light":
            bg = QColor("#ffffff")
            border = QColor("#c8d2df")
            text = QColor("#475569")
        else:
            bg = QColor("#182337")
            border = QColor("#2b3a52")
            text = QColor("#a9b6c8")
        rect = QRectF(0.5, 0.5, self.width() - 1, self.height() - 1)
        painter.setBrush(QBrush(bg))
        painter.setPen(QPen(border, 1.0))
        painter.drawRoundedRect(rect, self.height() / 2, self.height() / 2)
        painter.setBrush(QBrush(_status_color(self.status)))
        painter.setPen(Qt.PenStyle.NoPen)
        font = QFont(self.font())
        font.setPointSize(10)
        dot_center, text_rect, display_text = self._content_geometry(font)
        painter.drawEllipse(dot_center, 5.5, 5.5)
        painter.setFont(font)
        painter.setPen(text)
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, display_text)


class PipelineStatusWidget(QWidget):
    """绘制知识入库流水线的状态灯和阶段说明。"""

    def __init__(self, title: str = "入库流水线 · PIPELINE") -> None:
        super().__init__()
        self.title = title
        self.theme = "dark"
        self.steps: list[PipelineStepView] = [
            PipelineStepView("MinerU / Docling 文档解析", "PDF -> Markdown · 表格/公式还原", "pending"),
            PipelineStepView("语义分块", "512 token · 10% 重叠", "pending"),
            PipelineStepView("BGE-M3 向量化索引", "本地向量库 / 关键词兼容检索", "pending"),
            PipelineStepView("KG 实体/关系抽取", "领域词典抽取 · JSONL 关系库", "pending"),
            PipelineStepView("检索验证 / 证据引用", "Top-k 命中 · chunk/关系可追溯", "pending"),
        ]
        self.setMinimumHeight(270)

    def set_theme(self, theme: str) -> None:
        self.theme = resolve_theme(theme)
        self.update()

    def set_steps(self, steps: list[dict] | list[PipelineStepView]) -> None:
        parsed: list[PipelineStepView] = []
        for step in steps:
            if isinstance(step, PipelineStepView):
                parsed.append(step)
                continue
            parsed.append(
                PipelineStepView(
                    str(step.get("name") or step.get("label") or "流水线阶段"),
                    str(step.get("message") or step.get("detail") or ""),
                    str(step.get("status") or "pending"),
                )
            )
        if parsed:
            self.steps = parsed
        self.updateGeometry()
        self.update()

    def sizeHint(self) -> QSize:
        return QSize(360, max(280, 70 + len(self.steps) * 40))

    def paintEvent(self, event) -> None:
        colors = self._colors()
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), colors["bg"])
        painter.setPen(colors["muted"])
        title_font = QFont(self.font())
        title_font.setPointSize(10)
        title_font.setBold(True)
        painter.setFont(title_font)
        painter.drawText(QRectF(4, 8, self.width() - 8, 22), Qt.AlignmentFlag.AlignLeft, self.title)

        card = QRectF(4, 38, self.width() - 8, self.height() - 46)
        painter.setBrush(QBrush(colors["panel"]))
        painter.setPen(QPen(colors["border"], 1.1))
        painter.drawRoundedRect(card, 12, 12)

        start_y = 62.0
        inner_bottom = max(start_y + 36.0, self.height() - 22.0)
        step_gap = 40.0
        if self.steps:
            step_gap = min(46.0, max(36.0, (inner_bottom - start_y) / max(1, len(self.steps))))
        line_x = 34
        if len(self.steps) > 1:
            painter.setPen(QPen(colors["line"], 2.0))
            painter.drawLine(
                QPointF(line_x, start_y + 9),
                QPointF(line_x, start_y + 9 + (len(self.steps) - 1) * step_gap),
            )

        name_font = QFont(self.font())
        name_font.setPointSize(10)
        name_font.setBold(True)
        detail_font = QFont(self.font())
        detail_font.setPointSize(9)
        for index, step in enumerate(self.steps):
            y = start_y + index * step_gap
            color = _status_color(step.status)
            painter.setBrush(QBrush(color))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(QPointF(line_x, y + 9), 6.5, 6.5)
            painter.setFont(name_font)
            painter.setPen(colors["text"])
            painter.drawText(QRectF(58, y - 1, self.width() - 74, 18), Qt.AlignmentFlag.AlignLeft, step.name)
            painter.setFont(detail_font)
            painter.setPen(colors["muted"])
            painter.drawText(QRectF(58, y + 20, self.width() - 74, 16), Qt.AlignmentFlag.AlignLeft, step.detail)

    def _colors(self) -> dict[str, QColor]:
        if self.theme == "light":
            return {
                "bg": QColor("#f4f7fb"),
                "panel": QColor("#ffffff"),
                "border": QColor("#c3cedd"),
                "line": QColor("#d3dce8"),
                "text": QColor("#172033"),
                "muted": QColor("#64748b"),
            }
        return {
            "bg": QColor("#101821"),
            "panel": QColor("#1a2434"),
            "border": QColor("#2b3a52"),
            "line": QColor("#2f3f58"),
            "text": QColor("#dbe4ef"),
            "muted": QColor("#64748b"),
        }


class FlowDagWidget(QWidget):
    """绘制 LangGraph 多智能体 DAG。"""

    MAIN_NODES = [
        DagNode("ORCHESTRATOR", "需求解析 / 编排", "ORCHESTRATOR"),
        DagNode("CANDIDATE_GEN", "候选生成", "CANDIDATE_GEN"),
        DagNode("SCREENER", "代理初筛", "SCREENER"),
        DagNode("FEM_AGENT", "有限元校核", "FEM_AGENT"),
        DagNode("REPORT_GEN", "报告生成", "REPORT_GEN"),
    ]
    KNOWLEDGE_NODE = DagNode("KNOWLEDGE_AGENT", "检索证据 / RAG-KG", "KNOWLEDGE_AGENT")

    def __init__(self) -> None:
        super().__init__()
        self.theme = "dark"
        self.language = DEFAULT_LANGUAGE
        self.agent_states: dict[str, str] = {node.agent: "waiting" for node in self.MAIN_NODES}
        self.agent_states["KNOWLEDGE_AGENT"] = "waiting"
        self.stage_text = "等待任务输入"
        self.setMinimumHeight(174)
        self.setMaximumHeight(202)

    def sizeHint(self) -> QSize:
        return QSize(1040, 194)

    def set_theme(self, theme: str) -> None:
        self.theme = resolve_theme(theme)
        self.update()

    def set_language(self, language: str) -> None:
        self.language = language
        self.update()

    def update_state(self, agent_states: dict[str, str], stage_text: str) -> None:
        self.agent_states.update(agent_states)
        self.stage_text = stage_text or "等待任务输入"
        self.update()

    def layout_rects(self, width: int | None = None, height: int | None = None) -> dict[str, object]:
        width = width or self.width()
        height = height or self.height()
        outer = QRectF(10, 8, max(0, width - 20), max(0, height - 16))
        count = len(self.MAIN_NODES)
        left = 26.0
        right = max(left + 1.0, width - 26.0)
        available = max(1.0, right - left)
        gap = max(8.0, min(16.0, available * 0.012))
        node_w = (available - gap * (count - 1)) / count
        if node_w < 118.0:
            gap = max(4.0, min(10.0, (available - 106.0 * count) / max(1, count - 1)))
            node_w = (available - gap * (count - 1)) / count
        node_w = max(94.0, min(188.0, node_w))
        total_w = node_w * count + gap * (count - 1)
        if total_w > available + 0.5:
            gap = max(4.0, (available - 94.0 * count) / max(1, count - 1))
            node_w = max(84.0, (available - gap * (count - 1)) / count)
            total_w = node_w * count + gap * (count - 1)
        left = max(18.0, (width - total_w) / 2.0)
        node_h = 50.0
        y = 58.0
        rects = [QRectF(left + index * (node_w + gap), y, node_w, node_h) for index in range(count)]
        branch_x = (rects[0].right() + rects[1].left()) / 2.0 if len(rects) > 1 else width / 2.0
        knowledge_h = 50.0
        knowledge_top = min(y + 66.0, max(y + 60.0, height - 22.0 - knowledge_h))
        knowledge_w = min(max(236.0, node_w * 1.52), 308.0)
        knowledge_x = min(max(18.0, branch_x - knowledge_w / 2.0), max(18.0, width - knowledge_w - 18.0))
        knowledge_rect = QRectF(knowledge_x, knowledge_top, knowledge_w, knowledge_h)
        return {
            "outer": outer,
            "node_rects": rects,
            "knowledge_rect": knowledge_rect,
            "branch_x": branch_x,
        }

    def _colors(self) -> dict[str, QColor]:
        if self.theme == "light":
            return {
                "bg": QColor("#ffffff"),
                "panel": QColor("#f8fbff"),
                "border": QColor("#c8d2df"),
                "text": QColor("#172033"),
                "muted": QColor("#64748b"),
                "done": QColor("#10b981"),
                "active": QColor("#f59e0b"),
                "failed": QColor("#dc2626"),
                "waiting": QColor("#64748b"),
                "active_fill": QColor("#fff7ed"),
                "done_fill": QColor("#ecfdf5"),
                "failed_fill": QColor("#fff1f2"),
                "wait_fill": QColor("#f8fafc"),
                "line": QColor("#334155"),
                "rag": QColor("#8b5cf6"),
                "blue": QColor("#3b82f6"),
            }
        return {
            "bg": QColor("#0b111a"),
            "panel": QColor("#101821"),
            "border": QColor("#2b3a52"),
            "text": QColor("#dbe4ef"),
            "muted": QColor("#94a3b8"),
            "done": QColor("#34d399"),
            "active": QColor("#f59e0b"),
            "failed": QColor("#fb7185"),
            "waiting": QColor("#64748b"),
            "active_fill": QColor("#1f2937"),
            "done_fill": QColor("#10251f"),
            "failed_fill": QColor("#3c1822"),
            "wait_fill": QColor("#182337"),
            "line": QColor("#3b4a63"),
            "rag": QColor("#a78bfa"),
            "blue": QColor("#3b82f6"),
        }

    def _state_color(self, state: str, colors: dict[str, QColor]) -> QColor:
        if state == "done":
            return colors["done"]
        if state == "active":
            return colors["active"]
        if state == "failed":
            return colors["failed"]
        return colors["waiting"]

    def _fill_color(self, state: str, colors: dict[str, QColor]) -> QColor:
        if state == "done":
            return colors["done_fill"]
        if state == "active":
            return colors["active_fill"]
        if state == "failed":
            return colors["failed_fill"]
        return colors["wait_fill"]

    def _status_text(self, state: str) -> str:
        if state == "failed":
            return "失败"
        return {"done": "完成", "active": "运行中"}.get(state, "等待")

    def _node_status_text(self, node: DagNode, state: str, accent: str | None = None) -> str:
        """返回 DAG 节点的职责与状态合成文本。"""

        if accent == "rag":
            return node.subtitle
        return f"{node.subtitle} · {self._status_text(state)}"

    def paintEvent(self, event) -> None:
        colors = self._colors()
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), colors["bg"])

        layout = self.layout_rects(self.width(), self.height())
        outer = layout["outer"]
        painter.setPen(QPen(colors["border"], 1.2))
        painter.setBrush(QBrush(colors["panel"]))
        painter.drawRoundedRect(outer, 10, 10)

        title_font = QFont(self.font())
        title_font.setPointSize(12)
        title_font.setBold(True)
        painter.setFont(title_font)
        painter.setPen(colors["text"])
        painter.drawText(QRectF(28, 22, 320, 24), Qt.AlignmentFlag.AlignLeft, tr("section.workbench", language=self.language))

        small_font = QFont(self.font())
        small_font.setPointSize(9)
        painter.setFont(small_font)
        painter.setPen(colors["active"])
        painter.drawText(QRectF(250, 25, 320, 20), Qt.AlignmentFlag.AlignLeft, self.stage_text)

        legend_items = [("完成", "done"), ("运行中", "active"), ("失败", "failed"), ("等待", "waiting")]
        legend_x = max(440, self.width() - 330)
        for index, (label, key) in enumerate(legend_items):
            x = legend_x + index * 76
            painter.setBrush(QBrush(colors[key]))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(QPointF(x, 34), 5, 5)
            painter.setPen(colors["muted"])
            painter.drawText(QRectF(x + 10, 25, 66, 20), Qt.AlignmentFlag.AlignLeft, label)

        rects: list[QRectF] = layout["node_rects"]

        for index in range(1, len(rects)):
            prev = rects[index - 1]
            rect = rects[index]
            self._draw_arrow(
                painter,
                QPointF(prev.right(), prev.center().y()),
                QPointF(rect.left(), rect.center().y()),
                colors,
            )

        branch_x = float(layout["branch_x"])
        knowledge_rect = layout["knowledge_rect"]
        self._draw_branch(painter, branch_x, rects[0], knowledge_rect, colors)

        for rect, node in zip(rects, self.MAIN_NODES):
            self._draw_node(painter, rect, node, self.agent_states.get(node.agent, "waiting"), colors)

        self._draw_node(painter, knowledge_rect, self.KNOWLEDGE_NODE, self.agent_states.get("KNOWLEDGE_AGENT", "waiting"), colors, accent="rag")

    def _draw_arrow(self, painter: QPainter, start: QPointF, end: QPointF, colors: dict[str, QColor]) -> None:
        y = start.y()
        painter.setPen(QPen(colors["line"], 1.4))
        painter.drawLine(QPointF(start.x() + 8, y), QPointF(end.x() - 10, y))
        painter.setBrush(QBrush(colors["line"]))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawPolygon(
            QPointF(end.x() - 3, y),
            QPointF(end.x() - 10, y - 4),
            QPointF(end.x() - 10, y + 4),
        )

    def _draw_branch(
        self,
        painter: QPainter,
        branch_x: float,
        orchestrator_rect: QRectF,
        knowledge_rect: QRectF,
        colors: dict[str, QColor],
    ) -> None:
        main_y = orchestrator_rect.center().y()
        branch_start = QPointF(branch_x, main_y)
        branch_end = QPointF(branch_x, knowledge_rect.top() - 8)

        pen = QPen(colors["rag"], 1.3)
        pen.setStyle(Qt.PenStyle.DashLine)
        painter.setPen(pen)
        painter.drawLine(branch_start, branch_end)

        painter.setBrush(QBrush(colors["rag"]))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(branch_start, 3.5, 3.5)
        painter.drawPolygon(
            QPointF(branch_end.x(), branch_end.y() + 6),
            QPointF(branch_end.x() - 4, branch_end.y() - 2),
            QPointF(branch_end.x() + 4, branch_end.y() - 2),
        )

    def _draw_node(
        self,
        painter: QPainter,
        rect: QRectF,
        node: DagNode,
        state: str,
        colors: dict[str, QColor],
        accent: str | None = None,
    ) -> None:
        state_color = colors["rag"] if accent == "rag" else self._state_color(state, colors)
        painter.setPen(QPen(state_color, 1.7))
        painter.setBrush(QBrush(self._fill_color(state, colors)))
        painter.drawRoundedRect(rect, 8, 8)
        painter.setBrush(QBrush(state_color))
        painter.setPen(Qt.PenStyle.NoPen)

        title_font = QFont(self.font())
        title_font.setPointSize(8 if rect.width() < 150 else 9)
        title_font.setBold(True)
        body_font = QFont(self.font())
        body_font.setPointSize(7 if rect.width() < 136 else 8)
        status_text = self._node_status_text(node, state, accent)
        side_margin = 14.0 if accent == "rag" else 10.0
        dot_diameter = 8.0
        dot_gap = 7.0
        title_max_width = max(24.0, rect.width() - side_margin * 2.0 - dot_diameter - dot_gap)
        subtitle_max_width = max(24.0, rect.width() - side_margin * 2.0)
        while title_font.pointSize() > 6:
            title_metrics = QFontMetrics(title_font)
            if title_metrics.horizontalAdvance(node.name) <= title_max_width:
                break
            title_font.setPointSize(title_font.pointSize() - 1)
        title_metrics = QFontMetrics(title_font)
        body_metrics = QFontMetrics(body_font)
        title_text = title_metrics.elidedText(node.name, Qt.TextElideMode.ElideRight, int(title_max_width))
        subtitle_text = body_metrics.elidedText(status_text, Qt.TextElideMode.ElideRight, int(subtitle_max_width))
        title_width = float(title_metrics.horizontalAdvance(title_text))
        subtitle_width = float(body_metrics.horizontalAdvance(subtitle_text))
        title_group_width = dot_diameter + dot_gap + title_width
        line_height = max(13.0, float(title_metrics.height()))
        block_height = line_height + 17.0
        block_y = rect.top() + (rect.height() - block_height) / 2.0
        title_group_x = rect.left() + max(side_margin, (rect.width() - title_group_width) / 2.0)
        title_group_x = min(title_group_x, rect.right() - side_margin - title_group_width)
        dot_center = QPointF(title_group_x + dot_diameter / 2.0, block_y + line_height / 2.0)
        painter.drawEllipse(dot_center, dot_diameter / 2.0, dot_diameter / 2.0)

        title_rect = QRectF(title_group_x + dot_diameter + dot_gap, block_y, title_width + 2.0, line_height)
        status_x = rect.left() + max(side_margin, (rect.width() - subtitle_width) / 2.0)
        status_x = min(status_x, rect.right() - side_margin - subtitle_width)
        status_rect = QRectF(status_x, block_y + line_height + 1.0, subtitle_width + 2.0, 16.0)

        painter.setFont(title_font)
        painter.setPen(colors["text"])
        painter.drawText(title_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, title_text)

        painter.setFont(body_font)
        painter.setPen(state_color if state != "waiting" or accent == "rag" else colors["muted"])
        painter.drawText(status_rect, Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter, subtitle_text)

    @staticmethod
    def _elide(painter: QPainter, value: str, width: float) -> str:
        metrics = QFontMetrics(painter.font())
        return metrics.elidedText(value, Qt.TextElideMode.ElideRight, max(16, int(width)))

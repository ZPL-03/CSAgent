"""工程工作台专用组件。"""

from __future__ import annotations

from dataclasses import dataclass

from PyQt6.QtCore import QPointF, QRectF, QSize, Qt
from PyQt6.QtGui import QBrush, QColor, QFont, QPainter, QPen
from PyQt6.QtWidgets import QWidget

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
        self.setMinimumWidth(max(128, min(300, self.fontMetrics().horizontalAdvance(self.text) + 64)))

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
        painter.drawEllipse(QPointF(18, self.height() / 2), 5.5, 5.5)
        font = QFont(self.font())
        font.setPointSize(10)
        painter.setFont(font)
        painter.setPen(text)
        painter.drawText(QRectF(32, 0, self.width() - 40, self.height()), Qt.AlignmentFlag.AlignVCenter, self.text)


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
            PipelineStepView("Neo4j 实体/关系抽取", "规则抽取 · 可接入图数据库", "pending"),
            PipelineStepView("检索验证 / 证据引用", "Top-k 命中 · chunk/关系可追溯", "pending"),
        ]
        self.setMinimumHeight(260)

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
        return QSize(360, max(210, 70 + len(self.steps) * 46))

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

        start_y = 68
        line_x = 34
        if len(self.steps) > 1:
            painter.setPen(QPen(colors["line"], 2.0))
            painter.drawLine(QPointF(line_x, start_y + 9), QPointF(line_x, start_y + 9 + (len(self.steps) - 1) * 46))

        name_font = QFont(self.font())
        name_font.setPointSize(10)
        name_font.setBold(True)
        detail_font = QFont(self.font())
        detail_font.setPointSize(9)
        for index, step in enumerate(self.steps):
            y = start_y + index * 46
            color = _status_color(step.status)
            painter.setBrush(QBrush(color))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(QPointF(line_x, y + 9), 6.5, 6.5)
            painter.setFont(name_font)
            painter.setPen(colors["text"])
            painter.drawText(QRectF(58, y - 1, self.width() - 74, 20), Qt.AlignmentFlag.AlignLeft, step.name)
            painter.setFont(detail_font)
            painter.setPen(colors["muted"])
            painter.drawText(QRectF(58, y + 21, self.width() - 74, 18), Qt.AlignmentFlag.AlignLeft, step.detail)

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
        DagNode("需求解析", "parse_task", "ORCHESTRATOR"),
        DagNode("ORCHESTRATOR", "任务调度", "ORCHESTRATOR"),
        DagNode("CANDIDATE_GEN", "候选生成", "CANDIDATE_GEN"),
        DagNode("SCREENER", "代理初筛", "SCREENER"),
        DagNode("FEM_AGENT", "有限元校核", "FEM_AGENT"),
        DagNode("REPORT_GEN", "报告生成", "REPORT_GEN"),
    ]
    KNOWLEDGE_NODE = DagNode("KNOWLEDGE_AGENT", "项目 RAG/KG", "KNOWLEDGE_AGENT")

    def __init__(self) -> None:
        super().__init__()
        self.theme = "dark"
        self.agent_states: dict[str, str] = {node.agent: "waiting" for node in self.MAIN_NODES}
        self.agent_states["KNOWLEDGE_AGENT"] = "waiting"
        self.stage_text = "等待任务输入"
        self.setMinimumHeight(166)
        self.setMaximumHeight(190)

    def sizeHint(self) -> QSize:
        return QSize(1040, 178)

    def set_theme(self, theme: str) -> None:
        self.theme = resolve_theme(theme)
        self.update()

    def update_state(self, agent_states: dict[str, str], stage_text: str) -> None:
        self.agent_states.update(agent_states)
        self.stage_text = stage_text or "等待任务输入"
        self.update()

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

    def paintEvent(self, event) -> None:
        colors = self._colors()
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), colors["bg"])

        outer = QRectF(10, 8, self.width() - 20, self.height() - 16)
        painter.setPen(QPen(colors["border"], 1.2))
        painter.setBrush(QBrush(colors["panel"]))
        painter.drawRoundedRect(outer, 10, 10)

        title_font = QFont(self.font())
        title_font.setPointSize(12)
        title_font.setBold(True)
        painter.setFont(title_font)
        painter.setPen(colors["text"])
        painter.drawText(QRectF(28, 22, 320, 24), Qt.AlignmentFlag.AlignLeft, "工作流 · LangGraph DAG")

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

        count = len(self.MAIN_NODES)
        gap = 16
        left = 26
        right = self.width() - 26
        node_w = max(112, min(150, (right - left - gap * (count - 1)) / count))
        node_h = 42
        y = 58
        rects: list[QRectF] = []
        for index, node in enumerate(self.MAIN_NODES):
            x = left + index * (node_w + gap)
            rect = QRectF(x, y, node_w, node_h)
            rects.append(rect)
            self._draw_node(painter, rect, node, self.agent_states.get(node.agent, "waiting"), colors)
            if index > 0:
                prev = rects[index - 1]
                self._draw_arrow(painter, QPointF(prev.right(), prev.center().y()), QPointF(rect.left(), rect.center().y()), colors)

        knowledge_w = node_w * 1.35
        branch_x = (rects[1].right() + rects[2].left()) / 2
        knowledge_rect = QRectF(branch_x - knowledge_w / 2, y + 60, knowledge_w, 38)
        branch_bottom = QPointF(branch_x, knowledge_rect.top())
        painter.setPen(QPen(colors["line"], 1.1))
        painter.drawLine(QPointF(branch_x, rects[1].bottom()), branch_bottom)
        painter.setFont(small_font)
        painter.setPen(colors["muted"])
        painter.drawText(QRectF(branch_x - 86, rects[1].bottom() + 4, 172, 16), Qt.AlignmentFlag.AlignCenter, "检索 / 注入上下文")
        self._draw_node(painter, knowledge_rect, self.KNOWLEDGE_NODE, self.agent_states.get("KNOWLEDGE_AGENT", "waiting"), colors, accent="rag")

    def _draw_arrow(self, painter: QPainter, start: QPointF, end: QPointF, colors: dict[str, QColor]) -> None:
        y = start.y()
        painter.setPen(QPen(colors["line"], 1.2))
        painter.drawLine(QPointF(start.x() + 4, y), QPointF(end.x() - 9, y))
        painter.setBrush(QBrush(colors["line"]))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawPolygon(
            QPointF(end.x() - 3, y),
            QPointF(end.x() - 10, y - 4),
            QPointF(end.x() - 10, y + 4),
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
        painter.drawEllipse(QPointF(rect.left() + 14, rect.top() + 14), 4, 4)

        title_font = QFont(self.font())
        title_font.setPointSize(9)
        title_font.setBold(True)
        painter.setFont(title_font)
        painter.setPen(colors["text"])
        painter.drawText(QRectF(rect.left() + 28, rect.top() + 8, rect.width() - 36, 18), Qt.AlignmentFlag.AlignLeft, node.name)

        body_font = QFont(self.font())
        body_font.setPointSize(8)
        painter.setFont(body_font)
        painter.setPen(state_color if state != "waiting" or accent == "rag" else colors["muted"])
        painter.drawText(
            QRectF(rect.left() + 28, rect.top() + 25, rect.width() - 36, 16),
            Qt.AlignmentFlag.AlignLeft,
            self._status_text(state) if accent is None else node.subtitle,
        )

"""对话消息组件。"""

from __future__ import annotations

from PyQt6.QtCore import QRect, Qt
from PyQt6.QtGui import QFont, QFontMetrics
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QScrollArea, QSizePolicy, QVBoxLayout, QWidget

from gui.theme import resolve_theme


class ChatWidget(QWidget):
    """用于展示用户、智能体和工具调用消息的工作台消息流。"""

    def __init__(self) -> None:
        super().__init__()
        self.theme = "dark"
        self._messages: list[tuple[str, str]] = []
        self.empty_text = ""
        self.empty_state: dict[str, str] = {}
        self._last_render_width = 0

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.content = QWidget()
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(18, 10, 18, 10)
        self.content_layout.setSpacing(6)
        self.scroll_area.setWidget(self.content)

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.addWidget(self.scroll_area)
        self.set_theme(self.theme)

    def set_empty_text(self, text: str) -> None:
        self.empty_text = str(text)
        if not self._messages:
            self._render_messages()

    def set_empty_state(self, **items: str) -> None:
        self.empty_state = {key: str(value) for key, value in items.items()}
        if not self._messages:
            self._render_messages()

    def set_theme(self, theme: str) -> None:
        self.theme = resolve_theme(theme)
        palette = self._palette()
        self.scroll_area.setStyleSheet(
            f"QScrollArea {{ background: {palette['canvas']}; border: none; }}"
            f"QWidget {{ background: {palette['canvas']}; }}"
        )
        self._render_messages()

    def clear(self) -> None:
        self._messages.clear()
        self._render_messages()

    def add_message(self, sender: str, message: str) -> None:
        self._messages.append((str(sender), str(message)))
        self._render_messages()
        self.scroll_area.verticalScrollBar().setValue(self.scroll_area.verticalScrollBar().maximum())

    def toPlainText(self) -> str:
        if not self._messages:
            return "\n".join(value for value in self.empty_state.values() if value)
        return "\n".join(f"{sender}: {message}" for sender, message in self._messages)

    def _palette(self) -> dict[str, str]:
        if self.theme == "light":
            return {
                "canvas": "#f8fbff",
                "body": "#172033",
                "muted": "#64748b",
                "user_bg": "#2563eb",
                "user_text": "#ffffff",
                "agent_bg": "#ffffff",
                "agent_border": "#c8d2df",
                "agent_text": "#172033",
                "system_bg": "#eef2ff",
                "system_border": "#c7d2fe",
                "system_text": "#3730a3",
                "tool_bg": "#fff7ed",
                "tool_border": "#fdba74",
                "tool_text": "#9a3412",
                "avatar_bg": "#2563eb",
                "avatar_text": "#ffffff",
                "chip_bg": "#f1f5f9",
                "chip_border": "#c8d2df",
            }
        return {
            "canvas": "#0b111a",
            "body": "#dbe4ef",
            "muted": "#94a3b8",
            "user_bg": "#3b82f6",
            "user_text": "#ffffff",
            "agent_bg": "#1a2537",
            "agent_border": "#334155",
            "agent_text": "#dbe4ef",
            "system_bg": "#19264a",
            "system_border": "#334a8f",
            "system_text": "#c7d2fe",
            "tool_bg": "#221a32",
            "tool_border": "#8b5cf6",
            "tool_text": "#ddd6fe",
            "avatar_bg": "#2563eb",
            "avatar_text": "#ffffff",
            "chip_bg": "#182337",
            "chip_border": "#334155",
        }

    def _role(self, sender: str) -> str:
        upper = sender.upper()
        if upper == "USER":
            return "user"
        if upper == "SYSTEM":
            return "system"
        if "TOOL" in upper or "ABAQUS" in upper:
            return "tool"
        return "agent"

    def _avatar(self, sender: str) -> str:
        if sender == "助手":
            return "A"
        if not sender:
            return "?"
        parts = [part for part in sender.replace("-", "_").split("_") if part]
        if len(parts) >= 2:
            return "".join(part[:1] for part in parts[:2]).upper()
        return sender[:1].upper()

    def _clear_layout(self) -> None:
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.hide()
                widget.setParent(None)
                widget.deleteLater()

    def _label(self, text: str, color: str, size: int = 13, bold: bool = False) -> QLabel:
        label = QLabel(text)
        label.setWordWrap(True)
        label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        label.setFont(self._text_font(size, bold))
        label.setStyleSheet(f"color:{color};background:transparent;")
        return label

    def _single_line_label(self, text: str, color: str, size: int = 13, bold: bool = False) -> QLabel:
        label = self._label(text, color, size, bold)
        label.setWordWrap(False)
        label.setFixedHeight(max(22, label.fontMetrics().height() + 8))
        return label

    def _text_font(self, size: int = 13, bold: bool = False) -> QFont:
        font = QFont(self.font())
        font.setPixelSize(size)
        font.setWeight(QFont.Weight.Bold if bold else QFont.Weight.Normal)
        return font

    def _text_metrics(self, size: int = 13, bold: bool = False) -> QFontMetrics:
        return QFontMetrics(self._text_font(size, bold))

    def _responsive_width(self, max_width: int, min_width: int) -> tuple[int, int]:
        viewport_width = max(self.scroll_area.viewport().width(), self.width())
        if viewport_width <= 0:
            viewport_width = self.width()
        available = max(260, viewport_width - 136)
        conversational_cap = max(320, int(viewport_width * 0.78))
        available = min(available, conversational_cap)
        target_max = min(max_width, available)
        target_min = min(max(min_width, 180), target_max)
        return target_max, target_min

    def _content_width(self, text: str, target_max: int, target_min: int) -> int:
        metrics = self._text_metrics(13)
        value = str(text)
        line_widths = [metrics.horizontalAdvance(line.rstrip()) for line in value.splitlines() if line.strip()]
        natural = max(line_widths, default=0) + 28
        if natural >= target_max:
            return target_max
        return max(target_min, min(target_max, natural))

    def _wrapped_text_height(self, text: str, width: int) -> int:
        metrics = self._text_metrics(13)
        rect = metrics.boundingRect(
            QRect(0, 0, max(120, width), 4000),
            Qt.TextFlag.TextWordWrap,
            str(text),
        )
        return max(metrics.height(), rect.height())

    def _bubble(
        self,
        text: str,
        bg: str,
        border: str,
        fg: str,
        max_width: int = 760,
        min_width: int = 320,
        fit_content: bool = False,
    ) -> QFrame:
        frame = QFrame()
        frame.setObjectName("chatBubble")
        target_max, target_min = self._responsive_width(max_width, min_width)
        bubble_width = self._content_width(text, target_max, target_min) if fit_content else target_max
        frame.setFixedWidth(bubble_width)
        frame.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        frame.setStyleSheet(
            f"QFrame#chatBubble {{ background:{bg}; border:1px solid {border}; border-radius:14px; }}"
        )
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(12, 6, 12, 6)
        layout.setSpacing(2)
        text_label = self._label(text, fg, 13)
        text_label.setFixedWidth(max(120, bubble_width - 24))
        layout.addWidget(text_label)
        frame.setFixedHeight(max(36, self._wrapped_text_height(text, bubble_width - 24) + 14))
        return frame

    def _avatar_label(self, text: str, bg: str, fg: str) -> QLabel:
        avatar = QLabel(text)
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar.setFixedSize(32, 32)
        avatar.setStyleSheet(
            f"background:{bg}; color:{fg}; border-radius:16px; font-size:13px; font-weight:700;"
        )
        return avatar

    def _message_widget(self, sender: str, message: str) -> QWidget:
        palette = self._palette()
        role = self._role(sender)
        row = QWidget()
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(10)

        if role == "user":
            row_layout.addStretch(1)
            bubble = self._bubble(message, palette["user_bg"], palette["user_bg"], palette["user_text"], 920, 220, fit_content=True)
            row_layout.addWidget(bubble)
            row_layout.addWidget(self._avatar_label("U", palette["user_bg"], palette["user_text"]), 0, Qt.AlignmentFlag.AlignTop)
            return row

        if role == "system":
            bg, border, fg = palette["system_bg"], palette["system_border"], palette["system_text"]
        elif role == "tool":
            bg, border, fg = palette["tool_bg"], palette["tool_border"], palette["tool_text"]
        else:
            bg, border, fg = palette["agent_bg"], palette["agent_border"], palette["agent_text"]

        row_layout.addWidget(self._avatar_label(self._avatar(sender), palette["avatar_bg"], palette["avatar_text"]), 0, Qt.AlignmentFlag.AlignTop)
        column = QWidget()
        column_layout = QVBoxLayout(column)
        column_layout.setContentsMargins(0, 0, 0, 0)
        column_layout.setSpacing(5)
        column_layout.addWidget(self._label(sender, fg, 12, True))
        column_layout.addWidget(self._bubble(message, bg, border, fg, 980, 220, fit_content=True))
        row_layout.addWidget(column, 1)
        return row

    def _empty_widget(self) -> QWidget:
        palette = self._palette()
        box = QWidget()
        box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        layout = QVBoxLayout(box)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        layout.addWidget(self._single_line_label(self.empty_state.get("title", ""), palette["body"], 15, True))
        layout.addWidget(self._single_line_label(self.empty_text, palette["muted"], 13))

        user_row = QWidget()
        user_row.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        user_layout = QHBoxLayout(user_row)
        user_layout.setContentsMargins(0, 0, 0, 0)
        user_layout.setSpacing(10)
        user_layout.addStretch(1)
        user_layout.addWidget(
            self._bubble(
                self.empty_state.get("user_prompt", ""),
                palette["user_bg"],
                palette["user_bg"],
                palette["user_text"],
                920,
                220,
                fit_content=True,
            )
        )
        user_layout.addWidget(self._avatar_label("U", palette["user_bg"], palette["user_text"]), 0, Qt.AlignmentFlag.AlignTop)
        layout.addWidget(user_row)

        agent_group = QWidget()
        agent_group.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        agent_layout = QHBoxLayout(agent_group)
        agent_layout.setContentsMargins(0, 0, 0, 0)
        agent_layout.setSpacing(10)
        agent_layout.addWidget(self._avatar_label("O", palette["avatar_bg"], palette["avatar_text"]), 0, Qt.AlignmentFlag.AlignTop)
        agent_column = QWidget()
        agent_column.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        agent_column_layout = QVBoxLayout(agent_column)
        agent_column_layout.setContentsMargins(0, 0, 0, 0)
        agent_column_layout.setSpacing(6)
        agent_column_layout.addWidget(self._label(self.empty_state.get("agent_title", "ORCHESTRATOR"), palette["user_bg"], 12, True))
        agent_column_layout.addWidget(
            self._bubble(
                self.empty_state.get("agent_body", ""),
                palette["agent_bg"],
                palette["agent_border"],
                palette["agent_text"],
                980,
                220,
                fit_content=True,
            )
        )

        tool = self._bubble(
            f"{self.empty_state.get('tool_title', '')}\n{self.empty_state.get('tool_body', '')}",
            palette["tool_bg"],
            palette["tool_border"],
            palette["tool_text"],
            980,
            220,
            fit_content=True,
        )
        agent_column_layout.addWidget(tool)

        chips = QWidget()
        chips_layout = QHBoxLayout(chips)
        chips_layout.setContentsMargins(0, 0, 0, 0)
        chips_layout.setSpacing(8)
        for key in ["evidence_a", "evidence_b"]:
            chip_text = self.empty_state.get(key, "")
            chip = QFrame()
            chip.setObjectName("chatEvidenceChip")
            chip_width = max(112, min(190, self.fontMetrics().horizontalAdvance(chip_text) + 34))
            chip.setFixedSize(chip_width, 24)
            chip.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
            chip.setStyleSheet(
                f"QFrame#chatEvidenceChip {{ background:{palette['chip_bg']};"
                f"border:1px solid {palette['chip_border']}; border-radius:12px; }}"
            )
            chip_layout = QHBoxLayout(chip)
            chip_layout.setContentsMargins(12, 0, 12, 0)
            chip_layout.setSpacing(0)
            chip_label = QLabel(chip_text)
            chip_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            chip_label.setStyleSheet(f"background:transparent;color:{palette['muted']};font-size:12px;")
            chip_layout.addWidget(chip_label)
            chips_layout.addWidget(chip)
        chips_layout.addStretch(1)
        agent_column_layout.addWidget(chips)
        agent_layout.addWidget(agent_column, 1)
        layout.addWidget(agent_group, 0, Qt.AlignmentFlag.AlignTop)
        layout.addSpacing(2)
        return box

    def _render_messages(self) -> None:
        self._last_render_width = self.width()
        self._clear_layout()
        if not self._messages:
            self.content_layout.addWidget(self._empty_widget(), 0, Qt.AlignmentFlag.AlignTop)
            return
        for sender, message in self._messages:
            self.content_layout.addWidget(self._message_widget(sender, message))
        self.content_layout.addStretch(1)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        if abs(event.size().width() - self._last_render_width) >= 32:
            self._render_messages()

"""对话消息组件。"""

from __future__ import annotations

from html import escape

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QTextBrowser

from gui.theme import resolve_theme


class ChatWidget(QTextBrowser):
    """用于展示用户与智能体消息。"""

    def __init__(self) -> None:
        super().__init__()
        self.theme = "dark"
        self._messages: list[tuple[str, str]] = []
        self.empty_text = ""
        self.setReadOnly(True)
        self.setOpenExternalLinks(False)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.set_theme(self.theme)

    def set_empty_text(self, text: str) -> None:
        self.empty_text = str(text)
        if not self._messages:
            self._render_messages()

    def set_theme(self, theme: str) -> None:
        self.theme = resolve_theme(theme)
        self.document().setDefaultStyleSheet(self._stylesheet())
        self._render_messages()

    def clear(self) -> None:
        self._messages.clear()
        super().clear()

    def add_message(self, sender: str, message: str) -> None:
        self._messages.append((str(sender), str(message)))
        self._render_messages()
        self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())

    def _palette(self) -> dict[str, str]:
        if self.theme == "light":
            return {
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
            }
        return {
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
        }

    def _stylesheet(self) -> str:
        color = self._palette()
        return f"""
            body {{
                margin: 0;
                color: {color["body"]};
                font-size: 13px;
                line-height: 1.45;
            }}
            .sender {{
                font-weight: 700;
                letter-spacing: 0;
            }}
            .time {{
                color: {color["muted"]};
                font-size: 11px;
                padding-left: 8px;
            }}
            .bubble {{
                border-radius: 10px;
                padding: 10px 12px;
                line-height: 1.45;
            }}
        """

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

    def _message_html(self, sender: str, message: str) -> str:
        text = escape(str(message)).replace("\n", "<br>")
        sender_text = escape(str(sender))
        color = self._palette()
        role = self._role(sender)
        if role == "user":
            return (
                "<table width='100%' cellspacing='0' cellpadding='4'>"
                "<tr><td width='24%'></td><td align='right'>"
                f"<div class='bubble' style='background:{color['user_bg']};color:{color['user_text']};'>"
                f"<span class='sender'>{sender_text}</span><br>{text}</div>"
                "</td></tr></table>"
            )
        if role == "system":
            bg, border, fg = color["system_bg"], color["system_border"], color["system_text"]
        elif role == "tool":
            bg, border, fg = color["tool_bg"], color["tool_border"], color["tool_text"]
        else:
            bg, border, fg = color["agent_bg"], color["agent_border"], color["agent_text"]
        avatar = escape(self._avatar(sender))
        return (
            "<table width='100%' cellspacing='0' cellpadding='4'>"
            "<tr>"
            f"<td width='36' valign='top'><div style='background:{color['avatar_bg']};color:{color['avatar_text']};"
            "border-radius:16px;width:28px;height:28px;text-align:center;font-weight:700;'>"
            f"{avatar}</div></td>"
            "<td valign='top'>"
            f"<div><span class='sender' style='color:{fg};'>{sender_text}</span></div>"
            f"<div class='bubble' style='background:{bg};border:1px solid {border};color:{fg};'>{text}</div>"
            "</td></tr></table>"
        )

    def _render_messages(self) -> None:
        if not self._messages:
            color = self._palette()
            text = escape(self.empty_text)
            super().setHtml(
                f"<div style='border:1px dashed {color['agent_border']};"
                f"background:{color['agent_bg']};color:{color['muted']};"
                "border-radius:10px;padding:18px;line-height:1.6;'>"
                f"{text}</div>"
            )
            return
        super().setHtml("".join(self._message_html(sender, message) for sender, message in self._messages))

"""日志展示组件。"""

from __future__ import annotations

from PyQt6.QtWidgets import QTextEdit


class LogWidget(QTextEdit):
    def __init__(self) -> None:
        super().__init__()
        self.setReadOnly(True)

    def append_log(self, sender: str, message: str) -> None:
        self.append(f"[{sender}] {message}")

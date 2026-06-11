"""报告预览组件。"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from PyQt6.QtWidgets import QLabel, QTextBrowser, QVBoxLayout, QWidget

from core.paths import RESULTS_DIR


class ReportWidget(QWidget):
    """展示当前会话报告路径、生成状态和 Markdown 内容。"""

    def __init__(self) -> None:
        super().__init__()
        self.report: dict[str, Any] | None = None
        self.summary_label = QLabel("当前还没有报告。")
        self.summary_label.setWordWrap(True)
        self.preview_browser = QTextBrowser()

        layout = QVBoxLayout(self)
        layout.addWidget(self.summary_label)
        layout.addWidget(self.preview_browser, 1)
        self.reset_view()

    def reset_view(self) -> None:
        self.report = None
        self.summary_label.setText("当前还没有报告。")
        self.preview_browser.setHtml("<p>完成有限元校核并确认导出报告后，这里会显示 Markdown 报告预览。</p>")

    def refresh_latest(self) -> None:
        markdown_path = RESULTS_DIR / "latest_report.md"
        pdf_path = RESULTS_DIR / "latest_report.pdf"
        if markdown_path.exists():
            self.update_report(
                {
                    "markdown_path": str(markdown_path),
                    "pdf_path": str(pdf_path) if pdf_path.exists() else None,
                }
            )
        else:
            self.reset_view()

    def update_report(self, report: dict[str, Any] | None) -> None:
        if not report:
            self.reset_view()
            return
        self.report = dict(report)
        markdown_path = self.report.get("markdown_path")
        pdf_path = self.report.get("pdf_path")
        content = str(self.report.get("content") or "")
        if not content and markdown_path:
            path = Path(str(markdown_path))
            if path.exists():
                content = path.read_text(encoding="utf-8")

        llm_text = "是" if self.report.get("llm_explanation_used") else "否"
        content_chars = len(content)
        self.summary_label.setText(
            "Markdown：{markdown} | PDF：{pdf} | LLM 工程解释：{llm} | 字数：{chars}".format(
                markdown=markdown_path or "-",
                pdf=pdf_path or "-",
                llm=llm_text,
                chars=content_chars,
            )
        )
        if content:
            self.preview_browser.setMarkdown(content)
        else:
            self.preview_browser.setHtml("<p>报告记录存在，但当前没有可预览的 Markdown 内容。</p>")

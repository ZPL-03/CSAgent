import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication

from gui.report_widget import ReportWidget


def _app() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_report_widget_previews_report_content(tmp_path) -> None:
    app = _app()
    widget = ReportWidget()
    try:
        widget.update_report(
            {
                "markdown_path": str(tmp_path / "report.md"),
                "pdf_path": str(tmp_path / "report.pdf"),
                "content": "# 设计报告\n\n工程解释内容。",
                "llm_explanation_used": True,
            }
        )

        assert "report.md" in widget.summary_label.text()
        assert "LLM 工程解释：是" in widget.summary_label.text()
        assert "设计报告" in widget.preview_browser.toPlainText()
        assert "工程解释内容" in widget.preview_browser.toPlainText()
    finally:
        widget.close()
        app.processEvents()


def test_report_widget_reads_markdown_file_when_content_missing(tmp_path) -> None:
    app = _app()
    markdown_path = tmp_path / "latest_report.md"
    markdown_path.write_text("# 文件报告\n\n来自磁盘。", encoding="utf-8")
    widget = ReportWidget()
    try:
        widget.update_report({"markdown_path": str(markdown_path), "llm_explanation_used": False})

        assert "latest_report.md" in widget.summary_label.text()
        assert "LLM 工程解释：否" in widget.summary_label.text()
        assert "文件报告" in widget.preview_browser.toPlainText()
        assert "来自磁盘" in widget.preview_browser.toPlainText()
    finally:
        widget.close()
        app.processEvents()

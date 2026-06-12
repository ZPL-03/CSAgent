from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication

from gui.i18n import LocaleManager
from gui.main_window import MainWindow


def _app() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_locale_manager_persists_language(tmp_path) -> None:
    settings_path = tmp_path / "ui_settings.json"
    locale = LocaleManager(settings_path)

    assert locale.language == "zh"
    assert locale.theme == "dark"
    assert locale.text("app.title") == "CSAgent"
    assert locale.text("agent.failed") == "失败"

    locale.set_language("en")
    locale.set_theme("light")
    reloaded = LocaleManager(settings_path)

    assert reloaded.language == "en"
    assert reloaded.theme == "light"
    assert reloaded.text("app.title") == "CSAgent"


def test_main_window_switches_primary_shell_language(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("CSDM_cph_DISABLE_LLM_AUTO", "1")
    monkeypatch.setenv("CSDM_cph_UI_SETTINGS", str(tmp_path / "ui_settings.json"))
    app = _app()
    window = MainWindow()
    try:
        english_index = window.language_selector.findData("en")
        window.language_selector.setCurrentIndex(english_index)
        app.processEvents()

        assert window.locale.language == "en"
        assert window.app_title_label.text() == "CSAgent"
        assert window.app_subtitle_label.text() == "Multi-Agent Intelligent Design Platform"
        assert window.logo_label.text() == "CS"
        assert window.locale.text("agent.failed") == "Failed"
        assert window.generate_button.text() == "Send"
        assert window.restore_run_button.text() == "Restore Run State"
        assert "without re-running LLM or ABAQUS" in window.restore_run_button.toolTip()
        assert window.tabs.tabText(window.tabs.indexOf(window.candidate_widget)) == "Candidates"
        assert "Sample" in window.candidate_widget.table.horizontalHeaderItem(0).text()

        light_index = window.theme_selector.findData("light")
        window.theme_selector.setCurrentIndex(light_index)
        app.processEvents()

        assert window.locale.theme == "light"
        assert window.theme_selector.currentText() == "Light Engineering"
    finally:
        window.close()
        app.processEvents()

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
    assert "耐压壳" in locale.text("app.title")

    locale.set_language("en")
    reloaded = LocaleManager(settings_path)

    assert reloaded.language == "en"
    assert "Pressure Hull" in reloaded.text("app.title")


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
        assert "Pressure Hull" in window.app_title_label.text()
        assert window.generate_button.text() == "Start Design"
        assert window.tabs.tabText(window.tabs.indexOf(window.candidate_widget)) == "Candidates"
        assert "Sample" in window.candidate_widget.table.horizontalHeaderItem(0).text()
    finally:
        window.close()
        app.processEvents()

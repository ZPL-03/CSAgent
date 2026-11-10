from __future__ import annotations

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication

from gui.i18n import LocaleManager
from gui.main_window import MainWindow
from core.task_parser import TaskParser


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


@pytest.mark.parametrize("language", ["zh", "en"])
def test_default_templates_include_dimensions_and_quantities(tmp_path, language) -> None:
    locale = LocaleManager(tmp_path / "ui_settings.json")
    locale.set_language(language)
    parser = TaskParser()
    for key in ("input.placeholder", "chat.empty.user_prompt"):
        task = parser.parse_instruction(locale.text(key))["task"]
        assert task["candidate_generation_preferences"]["total_candidates"] == 12
        assert task["screening_preferences"]["top_k_candidates"] == 5
        assert task["geometry_envelope"]["length_mm"] == [500, 500]
        assert task["geometry_envelope"]["radius_mm"] == [100, 100]
        assert task["geometry_envelope"]["imperfection_ratio"] == [0.008, 0.008]


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
        assert window.logo_label.property("mode") == "image"
        assert not window.logo_label.pixmap().isNull()
        assert window.locale.text("agent.failed") == "Failed"
        assert window.generate_button.text() == "Send"
        assert window.restore_run_button.text() == "Restore Run State"
        assert "without re-running LLM or ABAQUS" in window.restore_run_button.toolTip()
        assert window.nav_buttons[1].text() == "Knowledge"
        assert "Sample" in window.workbench_candidate_widget.table.horizontalHeaderItem(0).text()

        light_index = window.theme_selector.findData("light")
        window.theme_selector.setCurrentIndex(light_index)
        app.processEvents()

        assert window.locale.theme == "light"
        assert window.theme_selector.currentText() == "Light Engineering"
    finally:
        window.close()
        app.processEvents()

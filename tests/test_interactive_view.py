from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication

from gui.interactive_view import InteractivePlotWidget


def _app() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_interactive_plot_widget_uses_static_candidate_fallback_in_offscreen() -> None:
    app = _app()
    widget = InteractivePlotWidget("empty")
    try:
        widget.resize(640, 420)
        widget.show_candidate(
            {
                "candidate_id": "TMP_1",
                "display_name": "TMP_1",
                "geometry": {
                    "length_mm": 500.0,
                    "radius_mm": 100.0,
                    "thickness_mm": 10.0,
                    "alpha_deg": 35.0,
                    "beta_deg": 65.0,
                },
                "material_system": {"name": "T700/Epoxy"},
            }
        )
        app.processEvents()

        assert widget._interactive is False
        assert widget._static_pixmap is not None
        assert widget.stack.currentWidget() is widget.static_label
    finally:
        widget.close()
        app.processEvents()


def test_reference_hull_does_not_create_static_placeholder_in_offscreen() -> None:
    app = _app()
    widget = InteractivePlotWidget("empty")
    try:
        widget.resize(640, 420)
        shown = widget.show_reference_hull()
        app.processEvents()

        assert shown is False
        assert widget._interactive is False
        assert widget._static_pixmap is None
        assert widget.stack.currentWidget() is widget.message_label
    finally:
        widget.close()
        app.processEvents()

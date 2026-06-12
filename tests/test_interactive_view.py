from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication

from gui.interactive_view import InteractivePlotWidget
from gui.render_utils import render_candidate_png_bytes


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


def test_reference_hull_uses_static_engineering_preview_in_offscreen() -> None:
    app = _app()
    widget = InteractivePlotWidget("empty")
    try:
        widget.resize(640, 420)
        shown = widget.show_reference_hull()
        app.processEvents()

        assert shown is True
        assert widget._interactive is False
        assert widget._static_pixmap is not None
        assert widget.stack.currentWidget() is widget.static_label
    finally:
        widget.close()
        app.processEvents()


def test_static_preview_uses_visible_viewport_size_not_child_minimum() -> None:
    app = _app()
    widget = InteractivePlotWidget("empty")
    try:
        widget.resize(420, 260)
        shown = widget.show_reference_hull()
        app.processEvents()

        assert shown is True
        assert widget._static_render_size == (420, 260)
    finally:
        widget.close()
        app.processEvents()


def test_static_candidate_preview_centers_shell_pixels() -> None:
    app = _app()
    _ = app
    png = render_candidate_png_bytes(
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
        },
        width=420,
        height=280,
        theme="dark",
    )
    assert png

    from PyQt6.QtGui import QImage

    image = QImage()
    assert image.loadFromData(png, "PNG")
    shell_pixels: list[tuple[int, int]] = []
    for y in range(0, image.height(), 3):
        for x in range(0, image.width(), 3):
            color = image.pixelColor(x, y)
            if color.blue() > 120 and color.red() < 90 and color.green() > 40:
                shell_pixels.append((x, y))

    assert shell_pixels
    top = min(y for _x, y in shell_pixels)
    bottom = max(y for _x, y in shell_pixels)
    center_y = (top + bottom) / 2.0
    assert abs(center_y - image.height() / 2.0) < image.height() * 0.09
    assert bottom - top > image.height() * 0.26


def test_static_candidate_preview_keeps_horizontal_safe_margin() -> None:
    png = render_candidate_png_bytes(
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
        },
        width=420,
        height=280,
        theme="dark",
    )
    assert png

    from PyQt6.QtGui import QImage

    image = QImage()
    assert image.loadFromData(png, "PNG")
    shell_pixels: list[tuple[int, int]] = []
    for y in range(0, image.height(), 3):
        for x in range(0, image.width(), 3):
            color = image.pixelColor(x, y)
            if color.blue() > 120 and color.red() < 90 and color.green() > 40:
                shell_pixels.append((x, y))

    assert shell_pixels
    left = min(x for x, _y in shell_pixels)
    right = max(x for x, _y in shell_pixels)
    min_margin = image.width() * 0.06
    assert left > min_margin
    assert image.width() - right > min_margin

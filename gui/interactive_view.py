"""交互式 PyVista 可视化组件。"""

from __future__ import annotations

import os
from typing import Dict

from PyQt6.QtCore import QEvent, Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QLabel, QStackedLayout, QVBoxLayout, QWidget

from gui.i18n import DEFAULT_LANGUAGE, text as tr
from gui.render_utils import (
    build_candidate_scene,
    build_mode_shape_scene,
    render_candidate_png_bytes,
    render_mode_shape_png_bytes,
)

try:
    from pyvistaqt import QtInteractor
except Exception:  # pragma: no cover
    QtInteractor = None


class InteractivePlotWidget(QWidget):
    def __init__(self, empty_message: str, language: str = DEFAULT_LANGUAGE) -> None:
        super().__init__()
        self.empty_message = empty_message
        self.language = language
        platform = os.getenv("QT_QPA_PLATFORM", "").lower()
        disable_interactive = os.getenv("CSDM_cph_DISABLE_INTERACTIVE_3D", "").strip() == "1"
        self._interactive = QtInteractor is not None and platform != "offscreen" and not disable_interactive
        self.plotter = None
        self._initial_camera_position = None
        self._static_pixmap: QPixmap | None = None

        self.message_label = QLabel(empty_message)
        self.message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.message_label.setWordWrap(True)
        self.message_label.setMinimumHeight(320)

        self.static_label = QLabel()
        self.static_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.static_label.setMinimumHeight(360)
        self.static_label.setWordWrap(True)

        self.hint_label = QLabel(tr("plot.hint", language=self.language))
        self.hint_label.setObjectName("plotHint")
        self.hint_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.hint_label.setWordWrap(True)

        self.plot_container = QWidget()
        self.plot_layout = QVBoxLayout(self.plot_container)
        self.plot_layout.setContentsMargins(0, 0, 0, 0)
        self.plot_layout.setSpacing(6)

        self.stack = QStackedLayout()
        self.stack.addWidget(self.message_label)
        self.stack.addWidget(self.static_label)
        self.stack.addWidget(self.plot_container)

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.addLayout(self.stack)

        self.clear_scene(empty_message)

    def set_language(self, language: str, empty_message: str | None = None) -> None:
        self.language = language
        if empty_message is not None:
            self.empty_message = empty_message
        self.hint_label.setText(tr("plot.hint", language=self.language))
        if self.stack.currentWidget() is self.message_label:
            self.message_label.setText(self.empty_message)

    def _ensure_plotter(self) -> bool:
        if self.plotter is not None:
            return True
        if not self._interactive:
            self.clear_scene(tr("plot.no_pyvista", language=self.language))
            return False
        try:
            self.plotter = QtInteractor(self.plot_container)
        except Exception:
            self.plotter = None
            self.clear_scene(tr("plot.opengl_failed", language=self.language))
            return False

        self.plot_layout.addWidget(self.plotter.interactor)
        self.plotter.interactor.installEventFilter(self)
        if self.plot_layout.indexOf(self.hint_label) == -1:
            self.plot_layout.addWidget(self.hint_label)
        self.plotter.set_background("#f5f7fb")
        self.plotter.enable_trackball_style()
        return True

    def _dispose_plotter(self) -> None:
        if self.plotter is None:
            return
        interactor = getattr(self.plotter, "interactor", None)
        try:
            if interactor is not None:
                self.plot_layout.removeWidget(interactor)
                interactor.hide()
                interactor.close()
                interactor.setParent(None)
                interactor.deleteLater()
        except Exception:
            pass
        try:
            ren_win = getattr(self.plotter, "ren_win", None)
            if ren_win is not None:
                ren_win.Finalize()
        except Exception:
            pass
        try:
            self.plotter.close()
        except Exception:
            pass
        self.plotter = None
        self._initial_camera_position = None

    def reset_plotter(self, message: str | None = None) -> None:
        self._dispose_plotter()
        self.clear_scene(message)

    def clear_scene(self, message: str | None = None) -> None:
        self.message_label.setText(message or self.empty_message)
        if self.plotter is not None:
            try:
                self.plotter.clear()
                self.plotter.set_background("#f5f7fb")
            except Exception:
                self._dispose_plotter()
        self._initial_camera_position = None
        self.stack.setCurrentWidget(self.message_label)
        self._static_pixmap = None
        self.static_label.clear()

    def _show_static_png(self, png_bytes: bytes | None, fallback_message: str) -> bool:
        if not png_bytes:
            self.clear_scene(fallback_message)
            return False
        pixmap = QPixmap()
        if not pixmap.loadFromData(png_bytes, "PNG"):
            self.clear_scene(fallback_message)
            return False
        self._static_pixmap = pixmap
        self._update_static_pixmap()
        self.stack.setCurrentWidget(self.static_label)
        return True

    def _update_static_pixmap(self) -> None:
        if self._static_pixmap is None:
            return
        target_size = self.static_label.size()
        if target_size.width() <= 0 or target_size.height() <= 0:
            return
        self.static_label.setPixmap(
            self._static_pixmap.scaled(
                target_size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )

    def _store_initial_camera(self) -> None:
        if self.plotter is not None:
            self._initial_camera_position = self.plotter.camera_position

    def _apply_default_camera(self, zoom: float) -> None:
        assert self.plotter is not None
        self.plotter.view_isometric()
        self.plotter.reset_camera()
        self.plotter.camera.zoom(zoom)
        self._store_initial_camera()
        self.plotter.render()

    def _restore_initial_camera(self) -> None:
        if self.plotter is None or self._initial_camera_position is None:
            return
        self.plotter.camera_position = self._initial_camera_position
        self.plotter.reset_camera()
        self.plotter.render()

    def eventFilter(self, watched, event):
        if self.plotter is not None and watched is getattr(self.plotter, "interactor", None):
            if event.type() == QEvent.Type.MouseButtonDblClick:
                self._restore_initial_camera()
                return True
        return super().eventFilter(watched, event)

    def _activate_plotter(self, title: str) -> bool:
        if not self._ensure_plotter():
            return False
        assert self.plotter is not None
        self.plotter.clear()
        self.plotter.set_background("#f5f7fb")
        self.plotter.add_text(title, position="upper_left", font_size=11, color="#1f2937")
        self.plotter.add_axes(line_width=2)
        self.stack.setCurrentWidget(self.plot_container)
        return True

    def closeEvent(self, event) -> None:
        self.reset_plotter()
        super().closeEvent(event)

    def resizeEvent(self, event) -> None:
        self._update_static_pixmap()
        super().resizeEvent(event)

    def show_candidate(self, candidate: Dict) -> None:
        scene = build_candidate_scene(candidate)
        if scene is None:
            self._show_static_png(
                render_candidate_png_bytes(candidate, language=self.language),
                tr("plot.no_candidate_geometry", language=self.language),
            )
            return
        meshes, title = scene
        if not self._activate_plotter(title):
            self._show_static_png(
                render_candidate_png_bytes(candidate, language=self.language),
                tr("plot.static_candidate_failed", language=self.language),
            )
            return
        assert self.plotter is not None
        for mesh, kwargs in meshes:
            self.plotter.add_mesh(mesh, **kwargs)
        self._apply_default_camera(0.94)

    def show_mode_shape(self, result: Dict) -> None:
        scene = build_mode_shape_scene(result)
        if scene is None:
            self._show_static_png(
                render_mode_shape_png_bytes(result, language=self.language),
                tr("plot.no_mode", language=self.language),
            )
            return
        mesh, scalar_name, title = scene
        if not self._activate_plotter(title):
            self._show_static_png(
                render_mode_shape_png_bytes(result, language=self.language),
                tr("plot.static_mode_failed", language=self.language),
            )
            return
        assert self.plotter is not None
        self.plotter.add_mesh(
            mesh,
            scalars=scalar_name,
            cmap="viridis",
            show_edges=False,
            smooth_shading=True,
            scalar_bar_args={
                "title": scalar_name or "ModeMagnitude",
                "vertical": True,
                "position_x": 0.88,
                "position_y": 0.16,
                "height": 0.68,
                "width": 0.07,
            },
        )
        self._apply_default_camera(0.92)

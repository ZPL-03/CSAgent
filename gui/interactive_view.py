"""交互式 PyVista 可视化组件。"""

from __future__ import annotations

import math
import os
from typing import Dict

from PyQt6.QtCore import QEvent, Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QLabel, QStackedLayout, QVBoxLayout, QWidget

from core.pressure_hull_profile import default_geometry
from gui.i18n import DEFAULT_LANGUAGE, text as tr
from gui.render_utils import (
    build_candidate_scene,
    build_mode_shape_scene,
    render_candidate_png_bytes,
    render_mode_shape_png_bytes,
)
from gui.theme import resolve_theme

try:
    from pyvistaqt import QtInteractor
except Exception:  # pragma: no cover
    QtInteractor = None


class InteractivePlotWidget(QWidget):
    def __init__(self, empty_message: str, language: str = DEFAULT_LANGUAGE) -> None:
        super().__init__()
        self.empty_message = empty_message
        self.language = language
        self.theme = "dark"
        self._platform = os.getenv("QT_QPA_PLATFORM", "").lower()
        self._disable_interactive = os.getenv("CSDM_cph_DISABLE_INTERACTIVE_3D", "").strip() == "1"
        self._interactive = QtInteractor is not None and self._platform != "offscreen" and not self._disable_interactive
        self.plotter = None
        self._initial_camera_position = None
        self._static_pixmap: QPixmap | None = None
        self._static_kind: str | None = None
        self._static_payload: Dict | None = None
        self._static_fallback: str = empty_message
        self._static_render_size: tuple[int, int] | None = None
        self._scene_bounds: tuple[float, float, float, float, float, float] | None = None
        self._display_mode = "message"

        self.message_label = QLabel(empty_message)
        self.message_label.setObjectName("plotEmpty")
        self.message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.message_label.setWordWrap(True)
        self.message_label.setMinimumHeight(0)

        self.static_label = QLabel()
        self.static_label.setObjectName("plotCanvas")
        self.static_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.static_label.setMinimumHeight(0)
        self.static_label.setWordWrap(True)

        self.plot_container = QWidget()
        self.plot_layout = QVBoxLayout(self.plot_container)
        self.plot_layout.setContentsMargins(0, 0, 0, 0)
        self.plot_layout.setSpacing(0)

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
        if self.stack.currentWidget() is self.message_label:
            self.message_label.setText(self.empty_message)

    def set_theme(self, theme: str) -> None:
        self.theme = resolve_theme(theme)
        if self.plotter is not None:
            try:
                self.plotter.set_background(self._plot_background())
                self.plotter.render()
            except Exception:
                pass
        elif self.stack.currentWidget() is self.static_label and self._static_kind == "candidate" and self._static_payload:
            self._show_static_candidate(self._static_payload, self._static_fallback)
        elif self.stack.currentWidget() is self.static_label and self._static_kind == "mode" and self._static_payload:
            self._show_static_mode(self._static_payload, self._static_fallback)

    def _plot_background(self) -> str:
        return "#f8fbff" if self.theme == "light" else "#101821"

    def _ensure_plotter(self) -> bool:
        if self.plotter is not None:
            return True
        if not self._interactive:
            message = (
                tr("plot.no_pyvista", language=self.language)
                if QtInteractor is None
                else tr("plot.offline_preview", language=self.language)
            )
            self.clear_scene(message)
            return False
        try:
            self.plotter = QtInteractor(self.plot_container)
        except Exception:
            self.plotter = None
            self.clear_scene(tr("plot.opengl_failed", language=self.language))
            return False

        self.plot_layout.addWidget(self.plotter.interactor)
        self.plotter.interactor.installEventFilter(self)
        self.plotter.set_background(self._plot_background())
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
                self.plotter.set_background(self._plot_background())
            except Exception:
                self._dispose_plotter()
        self._initial_camera_position = None
        self._static_pixmap = None
        self._static_kind = None
        self._static_payload = None
        self._static_fallback = message or self.empty_message
        self._static_render_size = None
        self._scene_bounds = None
        self.static_label.clear()
        self._display_mode = "message"
        self.stack.setCurrentWidget(self.message_label)

    def _show_static_png(self, png_bytes: bytes | None, fallback_message: str) -> bool:
        if not png_bytes:
            self.clear_scene(fallback_message)
            return False
        pixmap = QPixmap()
        if not pixmap.loadFromData(png_bytes, "PNG"):
            self.clear_scene(fallback_message)
            return False
        self._static_pixmap = pixmap
        self.static_label.setToolTip(tr("plot.offline_preview", language=self.language))
        self._update_static_pixmap()
        self._display_mode = "static"
        self.stack.setCurrentWidget(self.static_label)
        return True

    def _show_static_candidate(self, candidate: Dict, fallback_message: str) -> bool:
        self._static_kind = "candidate"
        self._static_payload = dict(candidate)
        self._static_fallback = fallback_message
        width, height = self._target_static_size()
        self._static_render_size = (width, height)
        return self._show_static_png(
            render_candidate_png_bytes(
                candidate,
                width=width,
                height=height,
                language=self.language,
                theme=self.theme,
            ),
            fallback_message,
        )

    def _show_static_mode(self, result: Dict, fallback_message: str) -> bool:
        self._static_kind = "mode"
        self._static_payload = dict(result)
        self._static_fallback = fallback_message
        width, height = self._target_static_size()
        self._static_render_size = (width, height)
        return self._show_static_png(
            render_mode_shape_png_bytes(result, width=width, height=height, language=self.language, theme=self.theme),
            fallback_message,
        )

    def _target_static_size(self) -> tuple[int, int]:
        size = self.size()
        width = size.width() if size.width() > 0 else self.static_label.width()
        height = size.height() if size.height() > 0 else self.static_label.height()
        return max(320, width), max(240, height)

    def _rerender_static_if_needed(self) -> None:
        if self._display_mode != "static":
            return
        if self._static_kind not in {"candidate", "mode"} or not self._static_payload:
            return
        target = self._target_static_size()
        if self._static_render_size == target:
            return
        if self._static_kind == "candidate":
            self._show_static_candidate(self._static_payload, self._static_fallback)
        else:
            self._show_static_mode(self._static_payload, self._static_fallback)

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

    def _combined_bounds(self, meshes: list[tuple[object, Dict]]) -> tuple[float, float, float, float, float, float] | None:
        bounds: list[tuple[float, float, float, float, float, float]] = []
        for mesh, _kwargs in meshes:
            raw_bounds = getattr(mesh, "bounds", None)
            if raw_bounds is None or len(raw_bounds) != 6:
                continue
            try:
                bounds.append(tuple(float(value) for value in raw_bounds))
            except (TypeError, ValueError):
                continue
        if not bounds:
            return None
        return (
            min(item[0] for item in bounds),
            max(item[1] for item in bounds),
            min(item[2] for item in bounds),
            max(item[3] for item in bounds),
            min(item[4] for item in bounds),
            max(item[5] for item in bounds),
        )

    def _mesh_bounds(self, mesh: object) -> tuple[float, float, float, float, float, float] | None:
        raw_bounds = getattr(mesh, "bounds", None)
        if raw_bounds is None or len(raw_bounds) != 6:
            return None
        try:
            return tuple(float(value) for value in raw_bounds)
        except (TypeError, ValueError):
            return None

    def _apply_default_camera(self, zoom: float, bounds: tuple[float, float, float, float, float, float] | None = None) -> None:
        assert self.plotter is not None
        bounds = bounds or self._scene_bounds
        if bounds is None:
            self.plotter.view_isometric()
            self.plotter.reset_camera()
            self.plotter.camera.zoom(zoom)
            self._store_initial_camera()
            self.plotter.render()
            return

        xmin, xmax, ymin, ymax, zmin, zmax = bounds
        center = ((xmin + xmax) * 0.5, (ymin + ymax) * 0.5, (zmin + zmax) * 0.5)
        dx = max(xmax - xmin, 1.0)
        dy = max(ymax - ymin, 1.0)
        dz = max(zmax - zmin, 1.0)
        diagonal = max(math.sqrt(dx * dx + dy * dy + dz * dz), 1.0)
        direction = (1.55, -1.8, 1.05)
        norm = math.sqrt(sum(value * value for value in direction))
        unit = tuple(value / norm for value in direction)
        distance = diagonal * 1.84
        camera_position = (
            center[0] + unit[0] * distance,
            center[1] + unit[1] * distance,
            center[2] + unit[2] * distance,
        )
        camera = self.plotter.camera
        camera.SetFocalPoint(*center)
        camera.SetPosition(*camera_position)
        camera.SetViewUp(0.0, 0.0, 1.0)
        try:
            camera.ParallelProjectionOn()
            camera.SetParallelScale(max(diagonal * 0.41, dz * 0.88, dy * 0.74))
        except Exception:
            pass
        try:
            self.plotter.reset_camera_clipping_range(bounds)
        except Exception:
            self.plotter.reset_camera_clipping_range()
        if zoom != 1.0:
            self.plotter.camera.zoom(zoom)
        self._store_initial_camera()
        self.plotter.render()

    def _restore_initial_camera(self) -> None:
        if self.plotter is None or self._initial_camera_position is None:
            return
        self.plotter.camera_position = self._initial_camera_position
        self.plotter.reset_camera()
        self.plotter.render()

    def reset_view(self) -> None:
        """恢复当前视口的初始工程等轴测视角。"""
        self._restore_initial_camera()

    def fit_view(self) -> None:
        """将当前三维结果重新适配到可视窗口。"""
        if self.plotter is None:
            self._update_static_pixmap()
            return
        self._apply_default_camera(1.0)
        self._store_initial_camera()
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
        self.plotter.set_background(self._plot_background())
        self.plot_container.setToolTip(title)
        self.plotter.add_axes(line_width=2)
        self._scene_bounds = None
        self._static_kind = None
        self._static_payload = None
        self._display_mode = "plot"
        self.stack.setCurrentWidget(self.plot_container)
        return True

    def show_reference_hull(self) -> bool:
        """在交互视口中显示参考耐压壳；离线环境生成同主题工程预览。"""

        candidate = {
            "candidate_id": "REFERENCE",
            "display_name": tr("plot.reference_hull", language=self.language),
            "hull_type": "CYLINDRICAL",
            "geometry": default_geometry("CYLINDRICAL"),
            "material_system": {"name": "T700/Epoxy"},
        }
        if not self._interactive:
            return self._show_static_candidate(candidate, self.empty_message)
        scene = build_candidate_scene(candidate)
        if scene is None:
            return self._show_static_candidate(candidate, self.empty_message)
        meshes, title = scene
        if not self._activate_plotter(title):
            return self._show_static_candidate(candidate, self.empty_message)
        assert self.plotter is not None
        for mesh, kwargs in meshes:
            self.plotter.add_mesh(mesh, **kwargs)
        self._scene_bounds = self._combined_bounds(meshes)
        self._apply_default_camera(1.0, self._scene_bounds)
        return True

    def closeEvent(self, event) -> None:
        self.reset_plotter()
        super().closeEvent(event)

    def resizeEvent(self, event) -> None:
        self._rerender_static_if_needed()
        self._update_static_pixmap()
        self._restore_display_mode()
        super().resizeEvent(event)

    def showEvent(self, event) -> None:
        self._rerender_static_if_needed()
        self._restore_display_mode()
        super().showEvent(event)

    def _restore_display_mode(self) -> None:
        if self._display_mode == "static" and self._static_pixmap is not None:
            self._update_static_pixmap()
            self.stack.setCurrentWidget(self.static_label)
            return
        if self._display_mode == "plot" and self.plotter is not None:
            self.stack.setCurrentWidget(self.plot_container)
            return
        self.stack.setCurrentWidget(self.message_label)

    def show_candidate(self, candidate: Dict) -> None:
        scene = build_candidate_scene(candidate)
        if scene is None:
            self._show_static_candidate(candidate, tr("plot.no_candidate_geometry", language=self.language))
            return
        meshes, title = scene
        if not self._activate_plotter(title):
            self._show_static_candidate(candidate, tr("plot.static_candidate_failed", language=self.language))
            return
        assert self.plotter is not None
        for mesh, kwargs in meshes:
            self.plotter.add_mesh(mesh, **kwargs)
        self._scene_bounds = self._combined_bounds(meshes)
        self._apply_default_camera(1.0, self._scene_bounds)

    def show_mode_shape(self, result: Dict) -> None:
        scene = build_mode_shape_scene(result)
        if scene is None:
            self._show_static_mode(result, tr("plot.no_mode", language=self.language))
            return
        mesh, scalar_name, title = scene
        if not self._activate_plotter(title):
            self._show_static_mode(result, tr("plot.static_mode_failed", language=self.language))
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
        self._scene_bounds = self._mesh_bounds(mesh)
        self._apply_default_camera(1.02, self._scene_bounds)

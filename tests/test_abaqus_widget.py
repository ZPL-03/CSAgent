from __future__ import annotations

import json
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication

from gui.abaqus_widget import AbaqusWidget


def _app() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_abaqus_widget_reports_mode_shape_payload_status(tmp_path) -> None:
    app = _app()
    mode_path = tmp_path / "mode.json"
    mode_path.write_text(
        json.dumps(
            {
                "title": "C1 first buckling mode",
                "points": [[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0]],
                "faces": [[4, 0, 1, 2, 3]],
                "scalars": [0.0, 0.5, 1.0, 0.25],
                "scalar_name": "Normalized mode displacement",
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    widget = AbaqusWidget()
    widget.preview_widget.show_mode_shape = lambda _result: None
    try:
        widget.update_results(
            [
                {
                    "candidate_id": "C1",
                    "display_name": "C1",
                    "session_candidate_id": "TMP_1",
                    "status": "success",
                    "ultimate_pressure_MPa": 42.0,
                    "linear_buckling_pressure_MPa": 38.0,
                    "visualization_json": str(mode_path),
                    "verdict": "passed",
                }
            ]
        )

        text = widget.detail_browser.toPlainText()
        assert "模态数据状态" in text
        assert "points=4" in text
        assert "faces=1" in text
        assert "scalars=4" in text
    finally:
        widget.close()
        app.processEvents()

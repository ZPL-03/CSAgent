from __future__ import annotations

import json

from gui.render_utils import mode_shape_payload_status, render_candidate_png_bytes, render_mode_shape_png_bytes


def _candidate() -> dict:
    return {
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


def test_render_candidate_static_png() -> None:
    png = render_candidate_png_bytes(_candidate(), width=480, height=300)

    assert png is not None
    assert png.startswith(b"\x89PNG")
    assert len(png) > 1000


def test_render_mode_shape_static_png_and_status(tmp_path) -> None:
    mode_path = tmp_path / "mode.json"
    mode_path.write_text(
        json.dumps(
            {
                "title": "C_TEST first buckling mode",
                "points": [
                    [0.0, 0.0, 0.0],
                    [1.0, 0.0, 0.0],
                    [1.0, 1.0, 0.0],
                    [0.0, 1.0, 0.0],
                    [0.0, 0.0, 1.0],
                    [1.0, 0.0, 1.0],
                    [1.0, 1.0, 1.0],
                    [0.0, 1.0, 1.0],
                ],
                "faces": [
                    [4, 0, 1, 2, 3],
                    [4, 4, 5, 6, 7],
                    [4, 0, 1, 5, 4],
                    [4, 2, 3, 7, 6],
                ],
                "scalars": [0.0, 0.2, 0.6, 0.4, 0.1, 0.5, 1.0, 0.8],
                "scalar_name": "Normalized mode displacement",
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    result = {"candidate_id": "C_TEST", "visualization_json": str(mode_path)}

    status = mode_shape_payload_status(result)
    png = render_mode_shape_png_bytes(result, width=480, height=320)

    assert status["available"] is True
    assert status["points"] == 8
    assert status["faces"] == 4
    assert "scalars=8" in status["message"]
    assert png is not None
    assert png.startswith(b"\x89PNG")
    assert len(png) > 1000

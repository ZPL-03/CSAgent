from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def isolated_ui_settings(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    monkeypatch.setenv("CSDM_cph_UI_SETTINGS", str(tmp_path / "ui_settings.json"))

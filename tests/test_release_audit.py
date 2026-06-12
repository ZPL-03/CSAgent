from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path
import os


ROOT = Path(__file__).resolve().parent.parent


def _clean_test_caches() -> None:
    for path in ROOT.rglob("__pycache__"):
        shutil.rmtree(path, ignore_errors=True)
    shutil.rmtree(ROOT / ".pytest_cache", ignore_errors=True)


def test_release_audit_passes_without_network() -> None:
    _clean_test_caches()
    result = subprocess.run(
        [sys.executable, "scripts/release_audit.py"],
        cwd=ROOT,
        env={**os.environ, "PYTHONIOENCODING": "utf-8"},
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "[PASS] 旧残留关键词" in result.stdout
    assert "[PASS] 产品身份配置" in result.stdout
    assert "[PASS] 案例库编号" in result.stdout
    assert "[PASS] UI 展示资产" in result.stdout

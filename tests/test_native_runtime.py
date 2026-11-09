"""Windows 数值库与嵌入依赖的进程级兼容性。"""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
pytestmark = pytest.mark.skipif(sys.platform != "win32", reason="仅检查 Windows MKL/OpenMP 加载行为")


def run_isolated(source: str, *, threading_layer: str | None = None) -> subprocess.CompletedProcess:
    environment = dict(os.environ)
    environment.pop("MKL_THREADING_LAYER", None)
    if threading_layer is not None:
        environment["MKL_THREADING_LAYER"] = threading_layer
    return subprocess.run(
        [sys.executable, "-B", "-c", source], cwd=ROOT, env=environment,
        capture_output=True, text=True, encoding="utf-8", timeout=60,
    )


def test_numeric_runtime_preserves_explicit_threading_layer() -> None:
    completed = run_isolated(
        "import core, os; assert os.environ['MKL_THREADING_LAYER'] == 'INTEL'",
        threading_layer="INTEL",
    )
    assert completed.returncode == 0, completed.stderr


@pytest.mark.parametrize("torch_first", [False, True])
def test_numpy_and_torch_share_process(torch_first: bool) -> None:
    prefix = "import torch; " if torch_first else ""
    completed = run_isolated(
        "import core, os; assert os.environ['MKL_THREADING_LAYER'] == 'SEQUENTIAL'; "
        + prefix
        + "import numpy as np; "
        "matrix = np.array([[4., 1.], [2., 3.]]); "
        "inverse = np.linalg.inv(matrix); "
        "np.testing.assert_allclose(inverse, [[.3, -.1], [-.2, .4]], atol=1e-12); "
        "import torch; "
        "torch.testing.assert_close(torch.from_numpy(inverse) @ torch.from_numpy(matrix), torch.eye(2, dtype=torch.float64), atol=1e-12, rtol=1e-12); "
        "ones = torch.ones((256, 256)); "
        "torch.testing.assert_close(ones @ ones, torch.full((256, 256), 256.))"
    )
    assert completed.returncode == 0, completed.stderr

"""CSAgent 核心能力包。"""

import os
import sys


if sys.platform == "win32":
    # 代理矩阵运算使用顺序 MKL，避免与 PyTorch 的 LLVM OpenMP 同进程初始化。
    os.environ.setdefault("MKL_THREADING_LAYER", "SEQUENTIAL")

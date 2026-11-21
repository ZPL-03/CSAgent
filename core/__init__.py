"""CSAgent 核心能力包。"""

import os
import sys


if sys.platform == "win32":
    # 代理矩阵运算使用顺序 MKL，避免与 PyTorch 的 LLVM OpenMP 同进程初始化。
    os.environ.setdefault("MKL_THREADING_LAYER", "SEQUENTIAL")
    # 第三方库若主动查询 CUDA，使用 NVML 检测路径，避免默认 Runtime 设备枚举。
    os.environ.setdefault("PYTORCH_NVML_BASED_CUDA_CHECK", "1")

"""ABAQUS 任务工具。"""

from __future__ import annotations

import shutil
import os
import subprocess
import time
from pathlib import Path
from typing import Dict, Iterable, Tuple


def is_abaqus_available(command: str = "abaqus") -> bool:
    return shutil.which(command) is not None


def compiler_environment() -> dict[str, str]:
    """仅为求解子进程加载 oneAPI 与 MSVC，不更改系统或 GUI 环境。"""
    if shutil.which("ifort") and shutil.which("link"):
        return dict(os.environ)
    root = os.environ.get("ONEAPI_ROOT", "")
    script = Path(root) / "setvars.bat" if root else None
    if script is None or not script.is_file():
        raise RuntimeError("未找到 Intel Fortran 编译环境，请配置 ONEAPI_ROOT 或从编译器命令行启动平台")
    completed = subprocess.run(
        f'call "{script}" intel64 --force >nul 2>&1 && set', shell=True,
        capture_output=True, text=True, encoding="mbcs", errors="strict", timeout=60,
    )
    if completed.returncode:
        raise RuntimeError("oneAPI 编译环境初始化失败")
    environment = dict(os.environ)
    for line in completed.stdout.splitlines():
        key, separator, value = line.partition("=")
        if separator and key and not key.startswith("="):
            environment[key] = value
    if not shutil.which("ifort", path=environment.get("Path") or environment.get("PATH")):
        raise RuntimeError("oneAPI 环境中没有 ifort，无法编译 Abaqus/Standard 子程序")
    return environment


def run_command(command: Iterable[str], workdir: Path, timeout: int | None = None,
                environment: dict[str, str] | None = None) -> Tuple[int, str, str]:
    command_list = list(command)
    executable = shutil.which(command_list[0]) or command_list[0]
    if str(executable).lower().endswith((".bat", ".cmd")):
        command_list = ["cmd.exe", "/c", executable, *command_list[1:]]
    else:
        command_list[0] = executable

    process = subprocess.run(
        command_list,
        cwd=str(workdir),
        capture_output=True,
        text=True,
        timeout=timeout,
        encoding="utf-8",
        errors="replace",
        env=environment,
    )
    return process.returncode, process.stdout, process.stderr


def wait_for_result_file(result_path: Path, timeout_seconds: int, poll_interval_seconds: int) -> bool:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        if result_path.exists():
            return True
        time.sleep(poll_interval_seconds)
    return False


def read_tail_text(path: Path, max_chars: int = 4000) -> str:
    if not path.exists():
        return ""
    content = path.read_text(encoding="utf-8", errors="replace")
    return content[-max_chars:]


def diagnose_failure(msg_text: str, dat_text: str, return_code: int) -> Dict[str, str]:
    merged = f"{msg_text}\n{dat_text}".lower()
    if "too many attempts" in merged:
        return {"error_type": "mesh_error", "reason": "网格生成失败"}
    if "assembly error" in merged:
        return {"error_type": "geometry_issue", "reason": "几何装配异常"}
    if "converg" in merged:
        return {"error_type": "convergence_fail", "reason": "求解不收敛"}
    if "negative" in merged and "eigen" in merged:
        return {"error_type": "blf_negative", "reason": "特征值为负"}
    if return_code != 0:
        return {"error_type": "process_crash", "reason": f"ABAQUS 进程退出码 {return_code}"}
    return {"error_type": "failed", "reason": "未知 ABAQUS 失败"}

"""ABAQUS 任务工具。"""

from __future__ import annotations

import shutil
import os
import subprocess
import re
import stat
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
        f'"{os.environ.get("COMSPEC", "cmd.exe")}" /d /u /c call "{script}" intel64 --force >nul 2>&1 && set',
        capture_output=True, timeout=60,
    )
    if completed.returncode:
        raise RuntimeError("oneAPI 编译环境初始化失败")
    environment = dict(os.environ)
    # cmd /u 使内置 set 的重定向输出使用 UTF-16LE，保留中文和非本地代码页字符。
    for line in completed.stdout.decode("utf-16-le").splitlines():
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


def ensure_job_unlocked(workdir: Path) -> None:
    """作业目录有锁或为链接时，不写入或清理其中的文件。"""
    if workdir.is_symlink() or (
        workdir.exists() and getattr(workdir.lstat(), "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT
    ):
        raise ValueError(f"作业目录不能是链接：{workdir}")
    locks = sorted(workdir.glob("*.lck"))
    if locks:
        raise RuntimeError(f"作业锁仍存在：{', '.join(path.name for path in locks)}")


def job_transient_paths(workdir: Path, job_names: Iterable[str]) -> list[Path]:
    """列出作业的求解中间文件，保留模型、结果、输入快照和数值证据。"""
    names = tuple(job_names)
    if not names or any(not re.fullmatch(r"C[1-9][0-9]*(?:_service|_target|_post)?", name) for name in names):
        raise ValueError("无效的 Abaqus 作业名")
    suffixes = (
        ".023", ".com", ".jnl", ".sta", ".prt", ".sim", ".simdir", ".log",
        ".env", ".odb_f", ".msg", ".dat", ".res", ".mdl", ".stt",
        ".pac", ".sel", ".abq", ".monitor.log", ".monitor.stop",
    )
    paths = {workdir / (name + suffix) for name in names for suffix in suffixes}
    paths.update(workdir / f"build_{name}.py" for name in names)
    for pattern in ("abaqus.rpy*", "abaqus*.rec", "candidate_retry_*.json", "*.obj", "*.mod",
                    "standardU.dll", "standardU.lib", "standardU.exp", "standardU.pdb"):
        paths.update(workdir.glob(pattern))
    return sorted(path for path in paths if path.exists() or path.is_symlink())


def cleanup_job_artifacts(workdir: Path, job_names: Iterable[str]) -> None:
    """在求解进程退出且结果落盘后删除中间文件，删除错误直接暴露。"""
    ensure_job_unlocked(workdir)
    paths = job_transient_paths(workdir, job_names)
    for path in paths:
        if path.is_symlink() or not path.resolve().is_relative_to(workdir.resolve()):
            raise ValueError(f"清理目标越过作业目录：{path}")
    for path in paths:
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink()


def solver_log_tails(workdir: Path, job_names: Iterable[str]) -> dict[str, str]:
    """将失败作业的日志末尾写入结果诊断，原日志随后可清理。"""
    return {
        name + suffix: read_tail_text(workdir / (name + suffix))
        for name in job_names for suffix in (".msg", ".dat", ".sta", ".log", ".monitor.log")
        if (workdir / (name + suffix)).is_file()
    }


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

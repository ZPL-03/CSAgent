"""CSAgent 运行环境自检脚本。"""

from __future__ import annotations

import importlib
import importlib.metadata
import os
import shutil
import sys
from pathlib import Path

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

from core.paths import ensure_project_dirs

load_dotenv(ROOT / ".env")


def check_python_version() -> tuple[bool, str]:
    version = sys.version_info
    ok = version >= (3, 10)
    return ok, f"{version.major}.{version.minor}.{version.micro}"


def check_module(name: str, package_name: str | None = None) -> tuple[bool, str]:
    try:
        module = importlib.import_module(name)
        distribution_name = package_name or name
        try:
            version = importlib.metadata.version(distribution_name)
        except importlib.metadata.PackageNotFoundError:
            version = getattr(module, "__version__", "unknown")
        return True, f"{distribution_name} {version}"
    except Exception as exc:
        return False, f"{name} 导入失败: {exc}"


def check_pyqt6_runtime() -> tuple[bool, str]:
    try:
        from PyQt6.QtCore import QT_VERSION_STR

        return True, f"PyQt6.QtCore Qt={QT_VERSION_STR}"
    except Exception as exc:
        return False, f"PyQt6.QtCore 导入失败: {exc}"


def check_pymupdf_runtime() -> tuple[bool, str]:
    try:
        import fitz

        version = getattr(fitz, "__version__", None) or getattr(fitz, "VersionBind", None) or "unknown"
        return True, f"PyMuPDF {version}"
    except Exception as exc:
        return False, f"PyMuPDF 导入失败: {exc}"


def check_pyvistaqt_runtime() -> tuple[bool, str]:
    try:
        import pyvistaqt
        from pyvistaqt import QtInteractor

        version = getattr(pyvistaqt, "__version__", "unknown")
        return True, f"pyvistaqt {version}, QtInteractor={QtInteractor.__name__}"
    except Exception as exc:
        return False, f"pyvistaqt 导入失败: {exc}"


def check_torch_runtime() -> tuple[bool, str]:
    try:
        import torch

        cuda_available = torch.cuda.is_available()
        device_name = torch.cuda.get_device_name(0) if cuda_available else "N/A"
        detail = (
            f"torch {torch.__version__}, cuda={torch.version.cuda}, "
            f"available={cuda_available}, device={device_name}"
        )
        return cuda_available, detail
    except Exception as exc:
        return False, f"torch 运行态检查失败: {exc}"


def main() -> int:
    ensure_project_dirs()
    checks: list[tuple[str, bool, str]] = []

    python_ok, python_detail = check_python_version()
    checks.append(("Python", python_ok, python_detail))

    abaqus_path = shutil.which("abaqus")
    checks.append(("ABAQUS", abaqus_path is not None, abaqus_path or "未找到"))

    checks.append(
        (
            "LLM主模型配置",
            bool(
                os.getenv("LLM_PRIMARY_URL")
                and os.getenv("LLM_PRIMARY_API_KEY")
                and os.getenv("LLM_PRIMARY_MODEL_NAME")
            ),
            f"base_url={'已设置' if os.getenv('LLM_PRIMARY_URL') else '未设置'}, "
            f"api_key={'已设置' if os.getenv('LLM_PRIMARY_API_KEY') else '未设置'}, "
            f"model={os.getenv('LLM_PRIMARY_MODEL_NAME') or '未设置'}",
        )
    )
    checks.append(
        (
            "LLM回退配置",
            bool(os.getenv("URL") and os.getenv("API_KEY") and os.getenv("MODEL_NAME")),
            f"base_url={'已设置' if os.getenv('URL') else '未设置'}, "
            f"api_key={'已设置' if os.getenv('API_KEY') else '未设置'}, "
            f"model={os.getenv('MODEL_NAME') or '未设置'}",
        )
    )

    pyqt_ok, pyqt_detail = check_pyqt6_runtime()
    checks.append(("PyQt6.QtCore", pyqt_ok, pyqt_detail))

    pymupdf_ok, pymupdf_detail = check_pymupdf_runtime()
    checks.append(("PyMuPDF", pymupdf_ok, pymupdf_detail))

    pyvistaqt_ok, pyvistaqt_detail = check_pyvistaqt_runtime()
    checks.append(("pyvistaqt", pyvistaqt_ok, pyvistaqt_detail))

    for module_name, package_name in [
        ("jinja2", None),
        ("yaml", "PyYAML"),
        ("jsonschema", None),
        ("openai", None),
        ("langgraph", None),
        ("chromadb", None),
        ("sentence_transformers", "sentence-transformers"),
        ("torch", None),
        ("sklearn", "scikit-learn"),
        ("matplotlib", None),
        ("pyvista", None),
        ("reportlab", None),
    ]:
        ok, detail = check_module(module_name, package_name)
        checks.append((module_name, ok, detail))

    torch_ok, torch_detail = check_torch_runtime()
    checks.append(("TorchCUDA", torch_ok, torch_detail))

    exit_code = 0
    for name, ok, detail in checks:
        status = "PASS" if ok else "FAIL"
        print(f"[{status}] {name}: {detail}")
        if not ok:
            exit_code = 1
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())

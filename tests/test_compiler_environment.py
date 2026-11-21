from types import SimpleNamespace

import pytest

from abaqus import job_utils


@pytest.fixture(autouse=True)
def isolated_compiler_config(monkeypatch):
    for name in tuple(job_utils.os.environ):
        if name == "ONEAPI_ROOT" or name.startswith("IFORT_COMPILER"):
            monkeypatch.delenv(name)


def test_compiler_environment_preserves_unicode_and_does_not_mutate_parent(monkeypatch, tmp_path):
    script = tmp_path / "setvars.bat"
    script.write_text("@echo off", encoding="utf-8")
    monkeypatch.setenv("ONEAPI_ROOT", str(tmp_path))
    monkeypatch.delenv("UNICODE_TEST_PATH", raising=False)
    monkeypatch.setattr(job_utils.shutil, "which", lambda name, path=None: f"{name}.exe" if path else None)
    output = "Path=C:\\Intel\\bin\r\nUNICODE_TEST_PATH=D:\\中文工程\\测试\U0001f600\r\n=Z:=Z:\\hidden\r\n"

    def run(command, **kwargs):
        assert ' /d /u /c call "' in command
        assert "shell" not in kwargs and "encoding" not in kwargs
        return SimpleNamespace(returncode=0, stdout=output.encode("utf-16-le"))

    monkeypatch.setattr(job_utils.subprocess, "run", run)
    environment = job_utils.compiler_environment()
    assert environment["UNICODE_TEST_PATH"] == "D:\\中文工程\\测试\U0001f600"
    assert "UNICODE_TEST_PATH" not in job_utils.os.environ
    assert "=Z:" not in environment
    assert environment["PATH"] == "C:\\Intel\\bin"
    assert "Path" not in environment


def test_compiler_environment_exposes_initializer_failure(monkeypatch, tmp_path):
    (tmp_path / "setvars.bat").write_text("exit /b 1", encoding="utf-8")
    monkeypatch.setenv("ONEAPI_ROOT", str(tmp_path))
    monkeypatch.setattr(job_utils.shutil, "which", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(job_utils.subprocess, "run", lambda *_args, **_kwargs: SimpleNamespace(returncode=1, stdout=b""))
    with pytest.raises(RuntimeError, match="初始化失败"):
        job_utils.compiler_environment()


def test_parallel_studio_uses_highest_configured_version(monkeypatch, tmp_path):
    for version in (15, 16):
        root = tmp_path / str(version)
        (root / "bin").mkdir(parents=True)
        (root / "bin/ifortvars.bat").write_text("@echo off", encoding="utf-8")
        monkeypatch.setenv(f"IFORT_COMPILER{version}", str(root))
    monkeypatch.setattr(job_utils.shutil, "which", lambda name, path=None: f"{name}.exe" if path else None)
    commands = []

    def run(command, **kwargs):
        commands.append(command)
        return SimpleNamespace(returncode=0, stdout="Path=C:\\Intel16\\bin\r\n".encode("utf-16-le"))

    monkeypatch.setattr(job_utils.subprocess, "run", run)
    environment = job_utils.compiler_environment()
    assert len(commands) == 1
    assert f'call "{tmp_path / "16/bin/ifortvars.bat"}" intel64 >nul' in commands[0]
    assert environment["PATH"] == "C:\\Intel16\\bin"


def test_explicit_oneapi_config_does_not_fall_back_to_parallel_studio(monkeypatch, tmp_path):
    legacy = tmp_path / "legacy"
    (legacy / "bin").mkdir(parents=True)
    (legacy / "bin/ifortvars.bat").write_text("@echo off", encoding="utf-8")
    monkeypatch.setenv("IFORT_COMPILER16", str(legacy))
    monkeypatch.setenv("ONEAPI_ROOT", str(tmp_path / "missing"))
    monkeypatch.setattr(job_utils.shutil, "which", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(job_utils.subprocess, "run", lambda *_args, **_kwargs: pytest.fail("缺失的显式配置不能切换编译器"))
    with pytest.raises(RuntimeError, match="脚本不存在"):
        job_utils.compiler_environment()


@pytest.mark.parametrize("missing", ["ifort", "link"])
def test_compiler_environment_requires_both_tools(monkeypatch, tmp_path, missing):
    (tmp_path / "setvars.bat").write_text("@echo off", encoding="utf-8")
    monkeypatch.setenv("ONEAPI_ROOT", str(tmp_path))
    monkeypatch.setattr(job_utils.shutil, "which", lambda name, path=None: f"{name}.exe" if path and name != missing else None)
    monkeypatch.setattr(job_utils.subprocess, "run", lambda *_args, **_kwargs: SimpleNamespace(
        returncode=0, stdout="Path=C:\\Intel\\bin\r\n".encode("utf-16-le"),
    ))
    with pytest.raises(RuntimeError, match=f"缺少 {missing}"):
        job_utils.compiler_environment()


def test_active_compiler_environment_needs_no_initializer(monkeypatch):
    monkeypatch.setattr(job_utils.shutil, "which", lambda name: f"{name}.exe")
    monkeypatch.setattr(job_utils.subprocess, "run", lambda *_args, **_kwargs: pytest.fail("已激活环境无需重复初始化"))
    assert job_utils.compiler_environment() == dict(job_utils.os.environ)


def test_missing_compiler_config_is_an_explicit_failure(monkeypatch):
    monkeypatch.setattr(job_utils.shutil, "which", lambda *_args, **_kwargs: None)
    with pytest.raises(RuntimeError, match="安装配置"):
        job_utils.compiler_environment()


@pytest.mark.parametrize("available", [True, False])
def test_compiler_only_check_does_not_enter_full_environment_check(monkeypatch, available):
    from scripts import check_env

    monkeypatch.setattr(check_env, "compiler_environment", lambda: {"PATH": "compiler-path"})
    monkeypatch.setattr(check_env.shutil, "which", lambda name, path=None: f"{name}.exe" if available and path == "compiler-path" else None)
    monkeypatch.setattr(check_env, "ensure_project_dirs", lambda: pytest.fail("编译器检查不创建运行目录"))
    monkeypatch.setattr(check_env, "check_torch_runtime", lambda: pytest.fail("编译器检查不加载 GPU 运行时"))
    assert check_env.main(["--compiler-only"]) == (0 if available else 1)

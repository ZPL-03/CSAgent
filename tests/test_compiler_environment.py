from types import SimpleNamespace

import pytest

from abaqus import job_utils


def test_compiler_environment_preserves_unicode_and_does_not_mutate_parent(monkeypatch, tmp_path):
    script = tmp_path / "setvars.bat"
    script.write_text("@echo off", encoding="utf-8")
    monkeypatch.setenv("ONEAPI_ROOT", str(tmp_path))
    monkeypatch.delenv("UNICODE_TEST_PATH", raising=False)
    monkeypatch.setattr(job_utils.shutil, "which", lambda name, path=None: "ifort.exe" if path else None)
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


def test_compiler_environment_exposes_initializer_failure(monkeypatch, tmp_path):
    (tmp_path / "setvars.bat").write_text("exit /b 1", encoding="utf-8")
    monkeypatch.setenv("ONEAPI_ROOT", str(tmp_path))
    monkeypatch.setattr(job_utils.shutil, "which", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(job_utils.subprocess, "run", lambda *_args, **_kwargs: SimpleNamespace(returncode=1, stdout=b""))
    with pytest.raises(RuntimeError, match="初始化失败"):
        job_utils.compiler_environment()

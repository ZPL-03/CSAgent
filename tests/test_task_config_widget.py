from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication

from core.task_contract import task_payload_from_request
from core.task_parser import TaskParser
from gui.task_config_widget import TaskConfigWidget


def _app() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_task_config_widget_renders_fixed_geometry_from_explicit_user_values(monkeypatch) -> None:
    monkeypatch.setenv("CSDM_cph_DISABLE_LLM_AUTO", "1")
    app = _app()
    task = TaskParser().parse_instruction(
        "请为复合材料外压圆柱耐压壳设计方案，外压 30 MPa，长度 500 mm，半径 100 mm，厚度 10 mm，"
        "极限压力不低于 35 MPa，生成 12 个候选，初筛保留 5 个候选"
    )
    widget = TaskConfigWidget()
    try:
        widget.update_task(task)
        text = widget.toPlainText()

        assert "任务配置" in text
        assert "用户已给事实" in text
        assert "参考几何" in text
        assert "固定几何约束" in text
        assert "候选池总数" in text
        assert "12" in text
        assert "初筛保留数量" in text
        assert "5" in text
        assert "length_mm" in text
        assert "500.0" in text
        assert "radius_mm" in text
        assert "100.0" in text
        assert "thickness_mm" in text
        assert "10.0" in text
        facts = task_payload_from_request(task).get("user_input_facts", {})
        assert "fixed_geometry" in str(facts)
        assert "geometry_reference" not in str(facts)
        assert "会覆盖候选对应参数" in text
    finally:
        widget.close()
        app.processEvents()


def test_task_config_widget_renders_reference_geometry_when_user_marks_reference(monkeypatch) -> None:
    monkeypatch.setenv("CSDM_cph_DISABLE_LLM_AUTO", "1")
    app = _app()
    task = TaskParser().parse_instruction(
        "请为复合材料外压圆柱耐压壳设计方案，外压 30 MPa，参考长度 500 mm，半径约 100 mm，"
        "厚度大约 10 mm，极限压力不低于 35 MPa，生成 12 个候选，初筛保留 5 个候选"
    )
    widget = TaskConfigWidget()
    try:
        widget.update_task(task)
        text = widget.toPlainText()

        assert "参考几何" in text
        assert "length_mm" in text
        assert "500.0" in text
        assert "radius_mm" in text
        assert "100.0" in text
        assert "thickness_mm" in text
        assert "10.0" in text
        facts = task_payload_from_request(task).get("user_input_facts", {})
        assert "geometry_reference" in str(facts)
        assert "fixed_geometry" not in str(facts)
        assert "不强制候选方案等于该数值" in text
    finally:
        widget.close()
        app.processEvents()


def test_task_config_widget_renders_fixed_geometry(monkeypatch) -> None:
    monkeypatch.setenv("CSDM_cph_DISABLE_LLM_AUTO", "1")
    app = _app()
    task = TaskParser().parse_instruction(
        "请为复合材料外压圆柱耐压壳设计方案，外压 30 MPa，长度固定 500 mm，半径固定 100 mm，"
        "厚度固定 10 mm，极限压力不低于 35 MPa，生成 6 个候选，初筛保留 3 个候选"
    )
    widget = TaskConfigWidget()
    try:
        widget.update_task(task)
        text = widget.toPlainText()

        assert "固定几何约束" in text
        assert "length_mm" in text
        assert "500.0" in text
        assert "radius_mm" in text
        assert "100.0" in text
        assert "thickness_mm" in text
        assert "10.0" in text
        facts = task_payload_from_request(task).get("user_input_facts", {})
        assert "geometry_reference" not in str(facts)
        assert "会覆盖候选对应参数" in text
    finally:
        widget.close()
        app.processEvents()

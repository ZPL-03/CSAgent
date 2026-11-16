"""显示舍入与工程输入精度。"""

import pytest

from core.display import format_number, format_parameter
from core.task_contract import describe_load_conditions


@pytest.mark.parametrize(("value", "expected"), [
    (None, "-"), ("", "-"), ("未知", "未知"), (True, "True"),
    (45.0, "45"), (90, "90"), (77.845959, "77.8"), (-3.558, "-3.6"),
    (-0.0, "0"), (0.0049, "4.9e-03"), (-0.0049, "-4.9e-03"),
])
def test_summary_number(value, expected):
    assert format_number(value) == expected


@pytest.mark.parametrize(("name", "value", "expected"), [
    ("alpha_deg", 45.0, "45"), ("beta_deg", 22.5, "22.5"),
    ("imperfection_ratio", 0.005123456, "0.005123456"),
    ("ply_thickness_mm", 0.125, "0.125"), ("safety_factor", 1.25, "1.25"),
    ("length_mm", 600.1234, "600.1"), ("external_pressure_MPa", 9.593256116, "9.6"),
])
def test_parameter_precision(name, value, expected):
    assert format_parameter(name, value) == expected


def test_load_summary_retains_exact_input():
    load = {"type": "external_pressure", "external_pressure_MPa": 9.593256}
    assert "9.6 MPa" in describe_load_conditions(load, display=True)
    assert "9.593256 MPa" in describe_load_conditions(load)
    assert load["external_pressure_MPa"] < 9.6

import math

import numpy as np
import pytest

from core.pressure_hull_profile import estimate_asme_rd1172_linear_buckling_q


def isotropic_section(e=70000.0, nu=0.3, t=10.0):
    q = e / (1 - nu**2) * np.array([[1, nu, 0], [nu, 1, 0], [0, 0, (1-nu)/2]])
    return {"A": q * t, "B": np.zeros((3, 3)), "D": q * t**3 / 12}


@pytest.mark.parametrize("length", [300, 600, 1200])
@pytest.mark.parametrize("nu", [0.0, 0.3])
@pytest.mark.parametrize("reference,radius", [("inner", 150), ("middle_surface", 155), ("outer", 160)])
def test_asme_matches_isotropic_closed_form(length, nu, reference, radius):
    e, thickness, outer = 70000.0, 10.0, 160.0
    zp = math.sqrt(1-nu**2) * length**2 / (outer*thickness)
    gamma = 0.9 if zp > 100 else 1 - 0.001*zp
    expected = 0.8531 * 0.84 * gamma * e * thickness**2.5 / ((1-nu**2)**0.75 * length * outer**1.5)
    geometry = {"length_mm": length, "radius_mm": radius, "radius_reference": reference, "thickness_mm": thickness}
    actual = estimate_asme_rd1172_linear_buckling_q(geometry, isotropic_section(e, nu, thickness), {})
    assert actual == pytest.approx(expected, abs=5e-7)


@pytest.mark.parametrize("bad", ["nan", "negative", "singular", "asymmetric"])
def test_asme_rejects_invalid_stiffness_instead_of_clamping(bad):
    stiffness = isotropic_section()
    if bad == "nan":
        stiffness["A"][0, 0] = math.nan
    elif bad == "negative":
        stiffness["D"][0, 0] *= -1
    elif bad == "singular":
        stiffness["D"][:] = 0
    else:
        stiffness["A"][0, 1] *= 2
    with pytest.raises(ValueError, match="ABD"):
        estimate_asme_rd1172_linear_buckling_q(
            {"length_mm": 600, "radius_mm": 150, "thickness_mm": 10}, stiffness, {})

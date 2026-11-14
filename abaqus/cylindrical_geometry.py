# -*- coding: utf-8 -*-
"""圆柱壳半径基准换算；供主程序与 Abaqus Python 共同使用。"""

from __future__ import division

import math


RADIUS_REFERENCES = ("inner", "middle_surface", "outer")


def radius_reference(geometry):
    """未声明基准的项目记录采用壳中面约定。"""
    reference = geometry.get("radius_reference", "middle_surface")
    if reference not in RADIUS_REFERENCES:
        raise ValueError("geometry.radius_reference must be inner, middle_surface or outer")
    return reference


def positive_number(value, field):
    if isinstance(value, bool):
        raise ValueError("invalid positive number: %s" % field)
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError):
        raise ValueError("invalid positive number: %s" % field)
    if math.isnan(number) or math.isinf(number) or number <= 0:
        raise ValueError("invalid positive number: %s" % field)
    return number


def shell_radii(geometry):
    """返回内、中面、外半径，单位 mm；拒绝非正内半径。"""
    radius = positive_number(geometry.get("radius_mm"), "geometry.radius_mm")
    thickness = positive_number(geometry.get("thickness_mm"), "geometry.thickness_mm")
    reference = radius_reference(geometry)
    middle = radius + {"inner": 0.5, "middle_surface": 0.0, "outer": -0.5}[reference] * thickness
    values = {"inner": middle - thickness / 2, "middle_surface": middle, "outer": middle + thickness / 2}
    for key, value in values.items():
        positive_number(value, "geometry.%s_radius_mm" % key)
    return values

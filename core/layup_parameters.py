"""区分显式任务层序与使用 alpha/beta 的历史参数化模板。"""

import re

TEMPLATE_ANGLE_FIELDS = {"alpha_deg", "beta_deg"}


def classify_layup(raw_layup: dict | str | None) -> dict:
    """无模板标识的数值层序属于 TASK_ANGLES；命名模板和符号参数保持定义。"""
    layup = dict(raw_layup) if isinstance(raw_layup, dict) else ({"layup": str(raw_layup)} if raw_layup else {})
    if any(layup.get(key) is not None and layup[key] != "" for key in ("template_name", "template", "PC", "pc_label")):
        return layup
    text = str(layup.get("layup") or layup.get("skin_layup") or "")
    if (layup.get("angles_deg") is not None or text) and not re.search(r"alpha|beta|α|β", text, re.IGNORECASE):
        layup["template_name"] = "TASK_ANGLES"
    return layup


def uses_task_angles(layup: dict | None) -> bool:
    return isinstance(layup, dict) and layup.get("template_name") == "TASK_ANGLES"


def active_geometry(design: dict) -> dict:
    """返回参与设计的几何字段；不改写历史输入或其修订指纹。"""
    geometry = dict(design.get("geometry") or {})
    if uses_task_angles(design.get("layup")):
        for key in TEMPLATE_ANGLE_FIELDS:
            geometry.pop(key, None)
    return geometry


def active_layup(layup: dict) -> dict:
    """显式任务层序由 angles_deg 定义，模板参数不进入后续记录。"""
    result = dict(layup)
    if uses_task_angles(result):
        for key in TEMPLATE_ANGLE_FIELDS:
            result.pop(key, None)
    return result

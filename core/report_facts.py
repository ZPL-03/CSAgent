"""报告事实与目标比较量；提案、确认结果和派生值分别标记。"""

from __future__ import annotations

import math

from abaqus.cylindrical_geometry import radius_reference
from core.display import format_number, format_parameter


# 标签和单位由指标定义，模型不能重命名压力目标、承载结果或缺陷条件。
METRICS = {
    "external_pressure_MPa": ("工作压力", "MPa"),
    "imperfection_ratio": ("分析缺陷比", "1"),
    "solved_imperfection_ratio": ("实际求解缺陷比", "1"),
    "imperfection_amplitude_mm": ("实际缺陷幅值", "mm"),
    "ultimate_pressure_MPa": ("确认极限承载压力", "MPa"),
    "linear_buckling_pressure_MPa": ("线性屈曲压力", "MPa"),
    "surrogate_ultimate_pressure_MPa": ("代理承载压力估计", "MPa"),
    "service_pressure_checked_MPa": ("工作校核压力", "MPa"),
    "service_pressure_check_status": ("工作压力校核状态", None),
    "service_hashin_index_max": ("工作压力最大 Hashin 指数", "1"),
    "weight_kg_per_m2": ("面密度", "kg/m^2"),
    "symmetric": ("中面对称", None),
    "balanced": ("正负角均衡", None),
    "design_check": ("设计校核状态", None),
    "riks_limit_point_confirmed": ("Riks 极限点确认", None),
    "riks_termination_reason": ("Riks 终止原因", None),
    "objective_value": ("优化目标比较值", None),
    "capacity_margin_percent": ("容量相对工作压力的余量", "%"),
    "candidate_count": ("候选总数", "个"),
    "result_count": ("实际校核数", "个"),
    "comparable_count": ("满足推荐条件的方案数", "个"),
    "analysis_scope": ("分析范围", None),
    "recommendation_status": ("推荐状态", None),
    "length_mm": ("实际求解长度", "mm"),
    "radius_mm": ("实际求解半径", "mm"),
    "radius_reference": ("实际求解半径基准", None),
    "thickness_mm": ("实际求解厚度", "mm"),
    "material": ("实际求解材料", None),
    "layup": ("实际求解铺层", None),
}
ANALYSIS_SCOPE = "考虑初始几何缺陷的逐层圆柱壳子模型；不含封头、法兰、层间分层及制造过程，不提供试验认证。"
DESIGN_CHECK_LABELS = {"passed": "通过", "failed": "不通过", "unknown": "未判定", "not_run": "未求解"}


def build_report_facts(summary: dict) -> list[dict]:
    """任务、提案和实际求解分别建账；未确认容量不作为极限承载事实。"""
    facts: list[dict] = []

    def add(candidate_id, metric, value, status, unit=None):
        if isinstance(value, float) and not math.isfinite(value):
            raise ValueError(f"报告事实 {candidate_id}/{metric} 不是有限数值")
        facts.append({"candidate_id": candidate_id, "metric": metric, "value": value,
                      "unit": unit if unit is not None else METRICS[metric][1], "status": status,
                      "label": METRICS[metric][0]})

    for metric in ("external_pressure_MPa", "imperfection_ratio"):
        add(None, metric, summary.get(metric), "specified")
    result_ids = set()
    result_bindings = {}
    assessments = {item["candidate_id"]: item["state"] for item in summary.get("result_assessments", [])}
    for row in summary.get("results", []):
        cid = row.get("candidate_id")
        if not cid or cid in result_ids:
            raise ValueError("有限元报告的候选编号缺失或重复")
        result_ids.add(cid)
        session_id = row.get("session_candidate_id")
        if session_id:
            if session_id in result_bindings:
                raise ValueError("同一会话候选关联了多个有限元结果")
            result_bindings[session_id] = cid
        state = assessments.get(cid, "unknown")
        add(cid, "design_check", state, state)
        for metric in ("solved_imperfection_ratio", "imperfection_amplitude_mm", "ultimate_pressure_MPa",
                       "linear_buckling_pressure_MPa", "service_pressure_checked_MPa", "service_pressure_check_status",
                       "service_hashin_index_max", "weight_kg_per_m2",
                       "riks_limit_point_confirmed", "riks_termination_reason"):
            value = row.get(metric)
            if metric == "ultimate_pressure_MPa" and not row.get("verified_capacity"):
                value = None
            add(cid, metric, value, state if value is not None else "unknown")
    candidate_ids = set()
    for row in summary.get("all_candidates", []):
        cid = row.get("candidate_id")
        if not cid or cid in candidate_ids:
            raise ValueError("候选报告的编号缺失或重复")
        candidate_ids.add(cid)
        # 已求解方案只使用正式身份，提案指标仍以 status 区分于求解事实。
        fact_id = result_bindings.get(cid, cid)
        if cid in result_ids and fact_id != cid:
            raise ValueError("会话候选编号与有限元结果编号关联冲突")
        for metric in ("imperfection_ratio", "symmetric", "balanced", "surrogate_ultimate_pressure_MPa"):
            value = row.get(metric)
            status = "proposal" if metric != "surrogate_ultimate_pressure_MPa" else str(row.get("surrogate_prediction_status") or "unknown")
            add(fact_id, metric, value, status if value is not None else "unknown")
        if fact_id not in result_ids:
            add(fact_id, "design_check", "not_run", "not_run")
    recommendation = summary.get("recommendation") or {}
    ranked = recommendation.get("ranked") or []
    best = recommendation.get("selected")
    add(None, "candidate_count", len(summary.get("all_candidates", [])), "recorded")
    add(None, "result_count", len(summary.get("results", [])), "recorded")
    add(None, "comparable_count", len(ranked), "derived")
    add(None, "analysis_scope", ANALYSIS_SCOPE, "scope")
    add(None, "recommendation_status", "有满足条件的方案" if best else "没有满足完整校核及目标比较条件的方案", "derived")
    units = {"最大极限压力": "MPa", "最小厚度": "mm", "最小壳体质量": "kg"}
    for row in ranked:
        cid = row["candidate_id"]
        add(cid, "objective_value", row["objective_value"], "derived", units.get(recommendation["objective"], "kg/m^2"))
        pressure = summary.get("external_pressure_MPa")
        if pressure and pressure > 0:
            add(cid, "capacity_margin_percent", (row["capacity_MPa"] / pressure - 1) * 100, "derived")
    # 求解尺寸取自 solved_design，与候选提案分别建账。
    for row in summary.get("results", []):
        geometry = row.get("solved_geometry") or {}
        for metric, value in geometry.items():
            if metric in {"length_mm", "radius_mm", "thickness_mm"}:
                add(row["candidate_id"], metric, value, "solved_input")
        if geometry.get("radius_mm") is not None:
            add(row["candidate_id"], "radius_reference", radius_reference(geometry), "solved_input")
        for metric in ("material", "layup"):
            if row.get(metric) is not None:
                add(row["candidate_id"], metric, row[metric], "solved_input")
    return facts


def format_fact_value(fact: dict) -> str:
    """显示值保留当前单位；显示舍入不参与判定或数值比较。"""
    value = fact["value"]
    if fact["metric"] == "analysis_scope":
        return "含初始几何缺陷的复合材料圆柱壳子模型"
    if fact["metric"] == "radius_reference":
        return {"inner": "内半径", "middle_surface": "中面半径", "outer": "外半径"}[value]
    if fact["metric"] == "riks_termination_reason" and value is not None:
        return {"post_peak_drop_20_percent": "峰后载荷下降达到 20% 阈值，受控终止",
                "solver_termination": "求解器终止"}.get(str(value), str(value))
    if value is None:
        display = "未确认"
    elif isinstance(value, bool):
        display = ("已确认" if value else "未确认") if fact["metric"] == "riks_limit_point_confirmed" else "是" if value else "否"
    elif isinstance(value, (int, float)):
        display = (format_number(value, 2) if fact["unit"] == "%"
                   else format_number(value, 4) if fact["metric"] == "objective_value"
                   else format_number(value, 3) if fact["metric"].endswith("hashin_index_max")
                   else format_parameter(fact["metric"], value))
    else:
        display = DESIGN_CHECK_LABELS.get(str(value), str(value))
    # 数量的量词由句子承担，物理量的单位由事实显示值承担。
    unit = ("" if fact["unit"] == "个" else "（无量纲）" if fact["unit"] == "1"
            else " " + fact["unit"] if fact["unit"] else "")
    return display + unit

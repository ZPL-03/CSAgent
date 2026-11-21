"""报告事实契约：模型选择对象与指标，代码回填原值、单位和状态并渲染。"""

from __future__ import annotations

import json
import math
from typing import Any

from core.display import format_number, format_parameter


# 标签和单位由指标定义，模型不能重命名压力目标、承载结果或缺陷条件。
METRICS = {
    "external_pressure_MPa": ("工作压力", "MPa"),
    "ultimate_pressure_min_MPa": ("目标极限压力下限", "MPa"),
    "imperfection_ratio": ("分析缺陷比", "1"),
    "solved_imperfection_ratio": ("实际求解缺陷比", "1"),
    "imperfection_amplitude_mm": ("实际缺陷幅值", "mm"),
    "ultimate_pressure_MPa": ("确认极限承载压力", "MPa"),
    "linear_buckling_pressure_MPa": ("线性屈曲压力", "MPa"),
    "surrogate_ultimate_pressure_MPa": ("代理承载压力估计", "MPa"),
    "target_pressure_checked_MPa": ("目标校核压力", "MPa"),
    "service_pressure_checked_MPa": ("工作校核压力", "MPa"),
    "target_hashin_index_max": ("目标压力最大 Hashin 指数", "1"),
    "service_hashin_index_max": ("工作压力最大 Hashin 指数", "1"),
    "weight_kg_per_m2": ("面密度", "kg/m^2"),
    "symmetric": ("中面对称", None),
    "balanced": ("正负角均衡", None),
    "design_check": ("设计校核状态", None),
    "riks_limit_point_confirmed": ("Riks 极限点确认", None),
    "riks_termination_reason": ("Riks 终止原因", None),
}
FOLLOW_UPS = {
    "manufacturing_review": "制造评审需确定工艺参数和检验标准。",
    "defect_sensitivity": "缺陷敏感性分析需保持材料、几何、铺层和载荷一致，只改变缺陷条件进行对照。",
    "mesh_convergence": "通过网格收敛性和逐层应力覆盖检查评估离散误差。",
    "pressure_test": "数值模型的工程适用性需要静水压试验及工艺证据验证。",
}
FACT_REF_KEYS = {"candidate_id", "metric"}


def build_report_facts(summary: dict) -> list[dict]:
    """任务、提案和实际求解分别建账；未确认容量不作为极限承载事实。"""
    facts: list[dict] = []

    def add(candidate_id, metric, value, status):
        if isinstance(value, float) and not math.isfinite(value):
            raise ValueError(f"报告事实 {candidate_id}/{metric} 不是有限数值")
        facts.append({"candidate_id": candidate_id, "metric": metric, "value": value,
                      "unit": METRICS[metric][1], "status": status})

    for metric in ("external_pressure_MPa", "ultimate_pressure_min_MPa", "imperfection_ratio"):
        add(None, metric, summary.get(metric), "specified")
    result_ids = set()
    assessments = {item["candidate_id"]: item["state"] for item in summary.get("result_assessments", [])}
    for row in summary.get("results", []):
        cid = row.get("candidate_id")
        if not cid or cid in result_ids:
            raise ValueError("有限元报告的候选编号缺失或重复")
        result_ids.add(cid)
        state = assessments.get(cid, "unknown")
        add(cid, "design_check", state, state)
        for metric in ("solved_imperfection_ratio", "imperfection_amplitude_mm", "ultimate_pressure_MPa",
                       "linear_buckling_pressure_MPa", "target_pressure_checked_MPa", "service_pressure_checked_MPa",
                       "target_hashin_index_max", "service_hashin_index_max", "weight_kg_per_m2",
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
        for metric in ("imperfection_ratio", "symmetric", "balanced", "surrogate_ultimate_pressure_MPa"):
            value = row.get(metric)
            status = "proposal" if metric != "surrogate_ultimate_pressure_MPa" else str(row.get("surrogate_prediction_status") or "unknown")
            add(cid, metric, value, status if value is not None else "unknown")
        if cid not in result_ids:
            # 会话编号与正式求解编号保持不同；结果关联不借用 display_name。
            linked = next((row for row in summary.get("results", []) if row.get("session_candidate_id") == cid), None)
            state = assessments.get(linked["candidate_id"], "unknown") if linked else "not_run"
            add(cid, "design_check", state, state)
    return facts


def validate_report_selection(answer: str, facts: list[dict], recommendation: dict) -> dict:
    """校验引用并回填事实，拒绝未知或重复引用及与代码排序不一致的推荐。"""
    def unique_object(pairs):
        value = {}
        for key, item in pairs:
            if key in value:
                raise ValueError("报告 JSON 含重复字段")
            value[key] = item
        return value

    try:
        payload = json.loads(answer, object_pairs_hook=unique_object)
    except (TypeError, json.JSONDecodeError) as exc:
        raise ValueError("报告需要结构化事实选择 JSON") from exc
    if not isinstance(payload, dict) or set(payload) != {"fact_refs", "recommendation_candidate_id", "follow_up_codes"}:
        raise ValueError("报告字段必须为 fact_refs、recommendation_candidate_id、follow_up_codes")
    selected = payload["fact_refs"]
    if not isinstance(selected, list) or not selected or len(selected) > len(facts):
        raise ValueError("报告 fact_refs 必须是非空事实引用子集")
    index = {(row["candidate_id"], row["metric"]): row for row in facts}
    if len(index) != len(facts):
        raise ValueError("报告事实索引含重复对象与指标")
    seen = set()
    resolved = []
    for reference in selected:
        if not isinstance(reference, dict) or set(reference) != FACT_REF_KEYS:
            raise ValueError("报告事实引用只接受 candidate_id/metric")
        if reference["candidate_id"] is not None and not isinstance(reference["candidate_id"], str):
            raise ValueError("报告 candidate_id 类型无效")
        if not isinstance(reference["metric"], str):
            raise ValueError("报告 metric 类型无效")
        key = (reference["candidate_id"], reference["metric"])
        expected = index.get(key)
        if key in seen or expected is None:
            raise ValueError(f"报告事实引用未知或重复：{key}")
        seen.add(key)
        # 数值、单位和状态仅来自索引；模型不复制浮点值，也不能覆盖记录。
        resolved.append(dict(expected))
    expected_id = (recommendation.get("selected") or {}).get("candidate_id")
    if payload["recommendation_candidate_id"] != expected_id:
        raise ValueError("报告推荐对象与任务目标及完整求解证据不一致")
    codes = payload["follow_up_codes"]
    if not isinstance(codes, list) or any(not isinstance(code, str) or code not in FOLLOW_UPS for code in codes):
        raise ValueError("报告含无依据的验证建议或制造阈值")
    if len(set(codes)) != len(codes):
        raise ValueError("报告验证建议重复")
    return {**payload, "facts": resolved}


def render_report_selection(selection: dict) -> str:
    """显示精度不参与事实匹配或工程判定，模型不提供可执行的自由文本。"""
    lines = ["### 事实解读"]
    for fact in selection["facts"]:
        value: Any = fact["value"]
        if value is None:
            value = "未确认"
        elif isinstance(value, bool):
            value = "是" if value else "否"
        elif isinstance(value, (int, float)):
            value = (format_number(value, 3) if fact["metric"].endswith("hashin_index_max")
                     else format_parameter(fact["metric"], value))
        label, unit = METRICS[fact["metric"]]
        unit = "（无量纲）" if unit == "1" else " " + unit if unit else ""
        status = "" if fact["metric"] == "design_check" else f"；状态={fact['status']}"
        lines.append(f"- {fact['candidate_id'] or '任务'}：{label}={value}{unit}{status}。")
    lines.extend(["", "### 验证建议"])
    lines.extend("- " + FOLLOW_UPS[code] for code in selection["follow_up_codes"])
    return "\n".join(lines)

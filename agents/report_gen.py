"""报告生成智能体。"""

from __future__ import annotations

import json
import math
import re
import tempfile
from pathlib import Path
from typing import Any, Dict, List
from xml.sax.saxutils import escape

from abaqus.cylindrical_geometry import shell_radii
from agents.base import BaseAgent
from core.config_loader import load_llm_config
from core.display import format_number, format_parameter
from core.layup_parameters import active_geometry, uses_task_angles
from core.report_facts import build_report_facts, format_fact_value
from core.report_review import (
    REVIEW_PROMPT, parse_engineering_review, prepare_review_payload, render_engineering_review, review_engineering_content,
)
from core.fem_result_semantics import (
    complete_case_result_errors, is_passed_design_check, is_successful_result,
    verified_capacity_pressure,
)
from core.io_utils import write_json, write_text
from core.llm_backend import LLMBackend, auto_llm_enabled
from core.paths import RESULTS_DIR
from core.task_contract import (
    describe_boundary_conditions, describe_imperfection_source, describe_load_conditions,
    task_imperfection_ratio, task_payload_from_request,
)


class ReportGenAgent(BaseAgent):
    agent_name = "REPORT_GEN"
    REPORT_ARTIFACTS = {
        "overall": ("overall_design_report", "CSAgent 总体设计方案报告"),
    }

    def __init__(self, progress_callback=None) -> None:
        super().__init__(progress_callback=progress_callback)
        self.llm_config = load_llm_config()
        self.llm_backend: LLMBackend | None = None
        explanation_config = self.llm_config.get("report_explanation", {})
        self.explanation_max_output_tokens = max(
            512, int(explanation_config.get("max_output_tokens", 2048) or 2048)
        )
        self._last_llm_explanation_used = False
        self._last_llm_explanation_audit = {}
        if auto_llm_enabled():
            self.llm_backend = LLMBackend(self.llm_config)

    def _compact_candidate_record(self, candidate: Dict[str, Any]) -> Dict[str, Any]:
        geometry = active_geometry(candidate)
        if not geometry:
            geometry = {
                key: candidate.get(key)
                for key in ("length_mm", "radius_mm", "thickness_mm", "alpha_deg", "beta_deg", "imperfection_ratio")
                if candidate.get(key) is not None
            }
        raw_layup = candidate.get("layup") or {}
        layup = dict(raw_layup) if isinstance(raw_layup, dict) else {"layup": str(raw_layup)}
        raw_material = candidate.get("material_system") or candidate.get("material") or {}
        material = dict(raw_material) if isinstance(raw_material, dict) else {"name": str(raw_material)}
        return {
            "candidate_id": candidate.get("candidate_id"),
            "session_candidate_id": candidate.get("session_candidate_id") or candidate.get("candidate_id"),
            "display_name": candidate.get("display_name"),
            "source": candidate.get("source"),
            "material": material.get("name") or material.get("display_name") or material.get("material_key"),
            "length_mm": geometry.get("length_mm"),
            "radius_mm": geometry.get("radius_mm"),
            "thickness_mm": geometry.get("thickness_mm"),
            **({} if uses_task_angles(layup) else {
                "alpha_deg": geometry.get("alpha_deg"), "beta_deg": geometry.get("beta_deg"),
            }),
            "imperfection_ratio": geometry.get("imperfection_ratio"),
            "layup": layup.get("layup"),
            "layup_template": layup.get("template_name"),
            "ply_count": layup.get("ply_count", candidate.get("ply_count")),
            "balanced": layup.get("balanced", candidate.get("balanced")),
            "symmetric": layup.get("symmetric", candidate.get("symmetric")),
            "rationale": candidate.get("rationale"),
            "screening_summary": candidate.get("screening_summary"),
            "selection_reason": candidate.get("selection_reason"),
            "screening_rank": candidate.get("screening_rank"),
            "screening_selected": candidate.get("screening_selected"),
            "surrogate_ultimate_pressure_MPa": candidate.get("surrogate_ultimate_pressure_MPa"),
            "surrogate_prediction_status": candidate.get("surrogate_prediction_status"),
            "asme_linear_buckling_pressure_MPa": candidate.get("asme_linear_buckling_pressure_MPa"),
            "rank_score": candidate.get("rank_score"),
            "weight_kg_per_m2": candidate.get("surrogate_weight") or candidate.get("weight_kg_per_m2"),
        }

    def _clip_explanation_text(self, value: Any, limit: int = 320) -> str | None:
        """限制解释上下文中的自由文本长度，完整原文仍保留在正式报告和审计文件中。"""
        if value is None:
            return None
        text = str(value).strip()
        if not text:
            return None
        return text if len(text) <= limit else text[:limit].rstrip() + "…"

    def _compact_explanation_candidate(self, candidate: Dict[str, Any]) -> Dict[str, Any]:
        """保留方案比较所需字段，避免把运行审计和模型原文重复送入解释模型。"""
        compact = self._compact_candidate_record(candidate)
        for key in ("rationale", "screening_summary", "selection_reason"):
            compact[key] = self._clip_explanation_text(compact.get(key))
        return compact

    def _candidate_pool_summary(self, candidates: List[Dict]) -> Dict[str, Any]:
        """为解释模型提供候选池统计，不发送未校核候选的逐项明细。"""
        source_counts: Dict[str, int] = {}
        selected_ids: List[str] = []
        surrogate_pressures: List[float] = []
        for candidate in candidates:
            source = str(candidate.get("source") or "UNKNOWN")
            source_counts[source] = source_counts.get(source, 0) + 1
            candidate_id = str(candidate.get("candidate_id") or "").strip()
            if candidate.get("screening_selected") and candidate_id:
                selected_ids.append(candidate_id)
            pressure = candidate.get("surrogate_ultimate_pressure_MPa")
            if isinstance(pressure, (int, float)) and math.isfinite(float(pressure)):
                surrogate_pressures.append(float(pressure))
        pressure_range = None
        if surrogate_pressures:
            pressure_range = {
                "min_MPa": min(surrogate_pressures),
                "max_MPa": max(surrogate_pressures),
            }
        return {
            "total_count": len(candidates),
            "source_counts": source_counts,
            "screening_selected_count": len(selected_ids),
            "screening_selected_ids": selected_ids,
            "surrogate_pressure_range_MPa": pressure_range,
        }

    def _compact_explanation_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """只保留工程评议需要的结果字段，排除运行工件和嵌套诊断。"""
        text_fields = {
            "ultimate_pressure_basis", "failure_mode", "verification_scope",
            "diagnosis_summary", "progressive_damage_model", "riks_termination_reason",
        }
        fields = (
            "candidate_id", "session_candidate_id", "display_name", "status", "solved_geometry",
            "material", "layup", "ultimate_pressure_MPa", "verified_capacity",
            "linear_buckling_pressure_MPa", "ultimate_pressure_basis", "riks_lpf_max",
            "imperfection_amplitude_mm", "solved_imperfection_ratio", "weight_kg_per_m2", "verdict",
            "service_pressure_checked_MPa", "service_hashin_index_max", "service_pressure_check_status",
            "riks_increment_count", "riks_limit_point_confirmed", "progressive_damage_complete",
            "damage_state_output_complete", "progressive_damage_model", "damage_state_maxima",
            "service_stress_coverage", "riks_termination_reason", "verification_scope",
            "design_check_status", "capacity_assessment_status", "diagnosis_summary",
        )
        compact: Dict[str, Any] = {}
        for key in fields:
            if key not in result:
                continue
            value = result.get(key)
            if key in text_fields:
                compact[key] = self._clip_explanation_text(value)
            elif key in {"damage_state_maxima", "service_stress_coverage"} and isinstance(value, dict):
                compact[key] = {
                    str(name): self._clip_explanation_text(item, limit=96)
                    if isinstance(item, str) else item
                    for name, item in list(value.items())[:12]
                }
            else:
                compact[key] = value
        return compact

    def _explanation_facts(self, summary: Dict[str, Any]) -> List[Dict[str, Any]]:
        """只向解释模型提供决策相关事实，候选全集仍写入正式报告。"""
        facts = build_report_facts(summary)
        recommendation = summary.get("recommendation") or {}
        result_ids = {
            str(row.get("candidate_id"))
            for row in summary.get("results", [])
            if row.get("candidate_id")
        }
        selected_id = str((recommendation.get("selected") or {}).get("candidate_id") or "")
        global_metrics = {
            "external_pressure_MPa", "imperfection_ratio", "candidate_count", "result_count",
            "comparable_count", "analysis_scope", "recommendation_status",
        }
        result_metrics = {
            "design_check", "ultimate_pressure_MPa", "service_pressure_checked_MPa",
            "service_hashin_index_max", "weight_kg_per_m2", "riks_limit_point_confirmed",
            "riks_termination_reason", "objective_value", "capacity_margin_percent",
        }
        selected_metrics = {
            "solved_imperfection_ratio", "imperfection_amplitude_mm", "linear_buckling_pressure_MPa",
            "length_mm", "radius_mm", "radius_reference", "thickness_mm", "material", "layup",
            "progressive_damage_complete", "damage_state_output_complete", "riks_lpf_max",
        }
        filtered = []
        for fact in facts:
            candidate_id = str(fact.get("candidate_id") or "")
            metric = str(fact.get("metric") or "")
            if not candidate_id and metric in global_metrics:
                filtered.append(fact)
            elif candidate_id in result_ids and metric in result_metrics | (selected_metrics if candidate_id == selected_id else set()):
                filtered.append(fact)
        return filtered or facts

    def _candidate_context_maps(self, candidates: List[Dict]) -> tuple[Dict[str, Dict], Dict[str, Dict]]:
        by_candidate_id = {
            str(candidate.get("candidate_id")): candidate
            for candidate in candidates
            if str(candidate.get("candidate_id") or "").strip()
        }
        by_display_name = {
            str(candidate.get("display_name")): candidate
            for candidate in candidates
            if str(candidate.get("display_name") or "").strip()
        }
        return by_candidate_id, by_display_name

    def _enrich_results_with_candidate_context(self, results: List[Dict], candidates: List[Dict]) -> List[Dict]:
        by_candidate_id, by_display_name = self._candidate_context_maps(candidates)
        enriched_results: List[Dict] = []
        for result in results:
            enriched = dict(result)
            candidate = (
                by_candidate_id.get(str(result.get("session_candidate_id") or ""))
                or by_candidate_id.get(str(result.get("candidate_id") or ""))
                or by_display_name.get(str(result.get("display_name") or ""))
                or {}
            )
            if enriched.get("weight_kg_per_m2") is None:
                enriched["weight_kg_per_m2"] = candidate.get("surrogate_weight") or candidate.get("weight_kg_per_m2")
            if enriched.get("diagnosis_summary") is None and candidate.get("selection_reason"):
                enriched["diagnosis_summary"] = candidate.get("selection_reason")
            if enriched.get("display_name") is None:
                enriched["display_name"] = result.get("candidate_id")
            enriched_results.append(enriched)
        return enriched_results

    def _build_structured_summary(self, task: Dict, results: List[Dict], candidates: List[Dict]) -> Dict:
        task_payload = task_payload_from_request(task)
        design_targets = dict(task_payload.get("design_targets", {}))
        assessments = []
        for result in results:
            # 总体设计判定需要完整求解证据，阶段 verdict 不代表全流程通过。
            errors = complete_case_result_errors(result)
            if not errors and is_passed_design_check(result):
                state = "passed"
            elif not errors and is_successful_result(result) and result.get("verdict") == "不通过":
                state = "failed"
            else:
                state = "unknown"
            assessments.append({
                "candidate_id": result.get("candidate_id"),
                "session_candidate_id": result.get("session_candidate_id"),
                "state": state, "semantic_errors": list(errors),
            })
        confirmed_ultimate_results = [
            result for result in results if not complete_case_result_errors(result)
            and verified_capacity_pressure(result) is not None
            and result.get("ultimate_pressure_MPa") is not None
            and result.get("riks_limit_point_confirmed") is True
        ]
        best_pressure = max(
            confirmed_ultimate_results,
            key=lambda item: float(item["ultimate_pressure_MPa"]),
            default=None,
        )
        lightest = min(results, key=lambda item: float(item.get("weight_kg_per_m2") or 1e9), default=None)
        return {
            "session_task_id": task.get("task_id"),
            "application": task_payload["application"],
            "load_conditions": describe_load_conditions(task_payload["load_conditions"]),
            "external_pressure_MPa": task_payload["load_conditions"]["external_pressure_MPa"],
            "boundary_conditions": describe_boundary_conditions(task_payload["boundary_conditions"]),
            "imperfection_ratio": task_imperfection_ratio(task_payload),
            "imperfection_source": describe_imperfection_source(task_payload),
            "primary_objective": design_targets.get("primary_objective"),
            "result_count": len(results),
            "passed_count": sum(item["state"] == "passed" for item in assessments),
            "failed_count": sum(item["state"] == "failed" for item in assessments),
            "unknown_count": sum(item["state"] == "unknown" for item in assessments),
            "result_assessments": assessments,
            "recommendation": self._recommendation_facts(task_payload, results, candidates),
            "best_pressure_candidate": best_pressure.get("candidate_id") if best_pressure else None,
            "best_pressure_MPa": best_pressure.get("ultimate_pressure_MPa") if best_pressure else None,
            "lightest_candidate": lightest.get("candidate_id") if lightest else None,
            "lightest_weight_kg_per_m2": lightest.get("weight_kg_per_m2") if lightest else None,
            "all_candidates": [
                self._compact_candidate_record(candidate)
                for candidate in candidates
            ],
            "screened_candidates": [
                self._compact_candidate_record(candidate)
                for candidate in candidates if candidate.get("screening_selected")
            ],
            "results": [
                {
                    "candidate_id": result.get("candidate_id"),
                    "session_candidate_id": result.get("session_candidate_id"),
                    "display_name": result.get("display_name"),
                    "status": result.get("status"),
                    "solved_geometry": active_geometry(result["solved_design"]) if result.get("solved_design") else {},
                    "material": ((result.get("solved_design") or {}).get("material_system") or {}).get("name"),
                    "layup": ((result.get("solved_design") or {}).get("layup") or {}).get("layup"),
                    "ultimate_pressure_MPa": result.get("ultimate_pressure_MPa"),
                    "verified_capacity": not complete_case_result_errors(result) and verified_capacity_pressure(result) is not None,
                    "linear_buckling_pressure_MPa": result.get("linear_buckling_pressure_MPa"),
                    "ultimate_pressure_basis": result.get("ultimate_pressure_basis"),
                    "riks_lpf_max": result.get("riks_lpf_max"),
                    "imperfection_amplitude_mm": result.get("imperfection_amplitude_mm"),
                    "solved_imperfection_ratio": ((result.get("solved_design") or {}).get("geometry") or {}).get("imperfection_ratio"),
                    "weight_kg_per_m2": result.get("weight_kg_per_m2"),
                    "verdict": result.get("verdict"),
                    "failure_mode": result.get("failure_mode"),
                    "service_pressure_checked_MPa": result.get("service_pressure_checked_MPa"),
                    "service_hashin_index_max": result.get("service_hashin_index_max"),
                    "service_pressure_check_status": result.get("service_pressure_check_status"),
                    "riks_increment_count": result.get("riks_increment_count"),
                    "riks_limit_point_confirmed": result.get("riks_limit_point_confirmed"),
                    "progressive_damage_complete": result.get("progressive_damage_complete"),
                    "damage_state_output_complete": result.get("damage_state_output_complete"),
                    "progressive_damage_model": result.get("progressive_damage_model"),
                    "damage_state_maxima": result.get("damage_state_maxima"),
                    "damage_observed": result.get("damage_observed"),
                    "service_stress_coverage": result.get("service_stress_coverage"),
                    "riks_termination_reason": result.get("riks_termination_reason"),
                    "verification_scope": result.get("verification_scope"),
                    "design_check_status": result.get("design_check_status"),
                    "design_verdict_basis": result.get("design_verdict_basis"),
                    "capacity_assessment_status": result.get("capacity_assessment_status"),
                    "diagnosis_summary": result.get("diagnosis_summary"),
                }
                for result in results
            ],
        }

    def _recommendation_facts(self, task_payload: Dict, results: List[Dict], candidates: List[Dict]) -> Dict:
        """按完整求解证据和任务目标排序，供报告正文与模型解释共同使用。"""
        working_pressure = float(task_payload["load_conditions"]["external_pressure_MPa"])
        objective = str(task_payload["design_targets"]["primary_objective"])
        defect = task_imperfection_ratio(task_payload)
        ranked, excluded = [], []
        for result in results:
            reasons = list(complete_case_result_errors(result))
            if not is_passed_design_check(result):
                reasons.append("设计校核没有通过")
            capacity = verified_capacity_pressure(result)
            if capacity is None or capacity < working_pressure:
                reasons.append("确认极限压力未达到工作压力")
            candidate = next((item for item in candidates if str(item.get("candidate_id")) in {
                str(result.get("session_candidate_id")), str(result.get("candidate_id")),
            }), {})
            solved_geometry = (result.get("solved_design") or {}).get("geometry") or {}
            geometry = solved_geometry or (candidate.get("geometry") if not result.get("retry_count") else {}) or {}
            if solved_geometry.get("imperfection_ratio") not in (None, defect):
                reasons.append("求解缺陷条件与任务不一致")
            if objective == "最大极限压力":
                score = -capacity if capacity is not None else float("inf")
            elif objective == "最小厚度":
                score = float(geometry.get("thickness_mm") or float("inf"))
            else:
                density = result.get("weight_kg_per_m2")
                if density is None:
                    density = candidate.get("surrogate_weight") or candidate.get("weight_kg_per_m2")
                score = float(density) if density is not None else float("inf")
                if objective == "最小壳体质量":
                    length = geometry.get("length_mm")
                    if all(geometry.get(key) is not None for key in ("length_mm", "radius_mm", "thickness_mm")):
                        # 面密度对应壳中面面积，输入的内、外半径必须按厚度换算。
                        radius = shell_radii(geometry)["middle_surface"]
                        score = score * 2 * math.pi * radius * float(length) / 1_000_000
                    else:
                        score = float("inf")
            if not math.isfinite(score):
                reasons.append("缺少目标比较数据")
            identity = {"candidate_id": result.get("candidate_id"),
                        "session_candidate_id": result.get("session_candidate_id")}
            if reasons:
                excluded.append({**identity, "reasons": reasons})
            else:
                ranked.append({**identity, "objective_value": -score if objective == "最大极限压力" else score,
                               "capacity_MPa": capacity, "sort_value": score})
        ranked.sort(key=lambda item: item["sort_value"])
        for item in ranked:
            item.pop("sort_value")
        return {"objective": objective,
                "selected": ranked[0] if ranked else None, "ranked": ranked, "excluded": excluded}


    def _field_text(self, value: Any, default: str = "-") -> str:
        if value is None:
            return default
        text = str(value).strip()
        if not text or text.lower() == "none":
            return default
        return text

    def _explanation_chat(self, system_prompt: str, user_prompt: str, **kwargs: Any) -> str:
        """统一使用报告解释的输出预算，保证输入和输出不超过模型上下文。"""
        try:
            return self.llm_backend.chat(
                system_prompt,
                user_prompt,
                max_tokens_override=self.explanation_max_output_tokens,
                json_mode=True,
                **kwargs,
            )
        finally:
            trace = getattr(self.llm_backend, "last_call_trace", [])
            if trace:
                self._last_llm_explanation_audit.setdefault("call_traces", []).append(
                    [dict(item) for item in trace]
                )

    def _build_llm_explanation_payload(self, summary: Dict[str, Any]) -> Dict[str, Any]:
        passed_count = int(summary.get("passed_count") or 0)
        result_count = int(summary.get("result_count") or 0)
        failed_count = int(summary.get("failed_count") or 0)
        unknown_count = int(summary.get("unknown_count") or 0)
        if result_count <= 0:
            overall = "当前未提供有限元校核结果"
        elif failed_count == result_count:
            overall = "当前校核样本未满足设计目标"
        elif passed_count <= 0:
            overall = "当前没有已通过设计校核的结果，部分结果尚未判定"
        elif passed_count == result_count:
            overall = "当前校核样本均满足设计目标"
        else:
            overall = "当前校核样本中存在满足设计目标的方案"

        context = {
            "task": {
                "application": summary.get("application"),
                "load_case": summary.get("load_conditions"),
                "external_pressure_MPa": summary.get("external_pressure_MPa"),
                "boundary_conditions": summary.get("boundary_conditions"),
                "primary_objective": summary.get("primary_objective"),
            },
            "screened_candidates": [self._compact_explanation_candidate(candidate)
                                    for candidate in summary.get("screened_candidates", [])],
            "candidate_pool_summary": self._candidate_pool_summary(summary.get("all_candidates", [])),
            "results": [
                self._compact_explanation_result(result)
                for result in summary.get("results", [])
            ],
            "aggregate": {"overall": overall, "result_count": result_count, "passed_count": passed_count,
                          "failed_count": failed_count, "unknown_count": unknown_count,
                          "population": "有限元结果记录"},
            "result_assessments": summary.get("result_assessments", []),
            "recommendation": summary.get("recommendation"),
            "analysis_conditions": {
                "task_imperfection_ratio": summary.get("imperfection_ratio"),
                "imperfection_source": summary.get("imperfection_source"),
                "imperfection_ratios": sorted({item["imperfection_ratio"] for item in summary.get("all_candidates", [])
                                               if item.get("imperfection_ratio") is not None}),
            },
            "field_semantics": {
                "candidate_sets": "candidate_pool_summary 统计全部候选，screened_candidates 为预筛入选候选，results 为实际校核结果；aggregate 只统计 results，未送检候选不在统计母集中。",
                "result_assessments": "passed 为设计校核通过，failed 为设计校核不通过，unknown 为求解失败、未判定或结果语义不一致。",
                "recommendation": "selected 为按任务目标选出的推荐对象，ranked 为具备完整证据且可比较的方案，excluded 记录未入选原因。",
                "layup": "symmetric 和 balanced 是逐层核查结果；false 表示属性不满足，null 表示没有记录。",
                "pressure_checks": "工作压力下检查应力与首层失效；极限压力由含损伤 Riks 分析的已确认极限点确定，并与工作压力比较。",
                "progressive_damage_complete": "容量分析是否包含场变量损伤退化。",
                "damage_state_maxima": "局部损伤触发标志的最大值，不表示整体损伤程度。",
                "riks_lpf_max": "Riks 路径的最大载荷比例系数。",
                "post_peak_drop_20_percent": "峰后受控终止状态。",
                "imperfection_ratio": "分析使用的初始几何缺陷比，制造验收阈值需另行给定。",
            },
            "analysis_scope": "复合材料圆柱壳数值模型，未建模金属封头、法兰连接和层间分层；制造工艺和试验认证不在求解范围内。",
        }
        best = (summary.get("recommendation") or {}).get("selected")
        required = ([(best["candidate_id"], "ultimate_pressure_MPa"), (best["candidate_id"], "objective_value"),
                     (None, "external_pressure_MPa")] if best else [(None, "recommendation_status")])
        return prepare_review_payload(self._explanation_facts(summary), summary["recommendation"], format_fact_value,
                                      context=context, required_metrics=required)

    def _render_engineering_explanation(self, summary: Dict[str, Any]) -> str:
        """模型失败阻止导出，关闭模型时只展示确定性结论及分析范围。"""
        self._last_llm_explanation_used = False
        self._last_llm_explanation_audit = {"status": "disabled" if self.llm_backend is None else "pending",
                                            "call_traces": []}
        if self.llm_backend is None:
            return ""
        payload = self._build_llm_explanation_payload(summary)
        self._last_llm_explanation_audit["input"] = payload
        attempts, excluded = [], set()
        try:
            while True:
                options = {"excluded_backend_names": excluded} if excluded else {}
                answer = self._explanation_chat(
                    REVIEW_PROMPT, json.dumps(payload, ensure_ascii=False, allow_nan=False), **options,
                )
                self._last_llm_explanation_audit["raw_response"] = answer
                runtime = getattr(self.llm_backend, "active_backend", None)
                name = getattr(runtime, "name", None)
                attempt = {"backend": name, "raw_response": answer}
                attempts.append(attempt)
                self._last_llm_explanation_audit["attempts"] = attempts
                try:
                    def chat_review(system, user):
                        return self._explanation_chat(system, user, excluded_backend_names=excluded)
                    review = parse_engineering_review(chat_review, answer, payload, attempt)
                    review = review_engineering_content(
                        chat_review, review, payload, attempt,
                    )
                except ValueError as exc:
                    attempt.update(status="rejected", error=str(exc))
                    # 内容不合格的后端不重复调用；仅使用配置中尚未尝试的后端，并保留拒绝证据。
                    excluded.update(row.get("backend") for row in getattr(self.llm_backend, "last_call_trace", []) if row.get("backend"))
                    if name:
                        excluded.add(name)
                    remaining = [row for row in getattr(self.llm_backend, "backends", []) if row.name not in excluded]
                    if not remaining:
                        raise
                    self.emit_llm_trace(self.llm_backend, {"purpose": "report_engineering_explanation", "content_rejected": True})
                    self.emit_event("report_explanation_backend_rejected", f"报告后端 {name} 解释未通过，使用下一配置后端：{exc}",
                                    {"backend": name, "reason": str(exc)})
                    continue
                attempt["status"] = "accepted"
                break
        except Exception as exc:
            self._last_llm_explanation_audit.update(status="rejected" if isinstance(exc, ValueError) else "failed", error=str(exc))
            self.emit_llm_trace(self.llm_backend, {"purpose": "report_engineering_explanation", "failed": True})
            event = "report_explanation_rejected" if isinstance(exc, ValueError) else "report_explanation_failed"
            self.emit_event(event, f"工程评议未通过，报告未导出：{exc}",
                            {"report_kind": "overall", "reason": str(exc)})
            raise
        self.emit_llm_trace(self.llm_backend, {"purpose": "report_engineering_explanation"})
        self._last_llm_explanation_used = True
        self._last_llm_explanation_audit.update(status="accepted", review=review)
        return render_engineering_review(review, payload)

    def _render_markdown(self, task: Dict, results: List[Dict], candidates: List[Dict], summary: Dict | None = None) -> str:
        task_payload = task_payload_from_request(task)
        summary = summary if summary is not None else self._build_structured_summary(task, results, candidates)
        working_pressure = float(task_payload["load_conditions"]["external_pressure_MPa"])
        lines = [
            "# CSAgent 总体设计方案报告", "",
            "## 设计需求与校核依据", "",
            f"- 会话任务编号：`{task.get('task_id') or '-'}`",
            f"- 运行编号：`{task.get('run_id') or '-'}`",
            f"- 设计对象：{task_payload['application']}",
            f"- 工作压力：{format_number(working_pressure)} MPa",
            f"- 边界条件：{describe_boundary_conditions(task_payload['boundary_conditions'])}",
            f"- 任务初始几何缺陷比：{summary['imperfection_ratio']}（比例，{summary['imperfection_source']}）",
            f"- 用户指定几何：{self._field_text(task_payload.get('user_input_facts', {}).get('fixed_geometry'))}",
            f"- 优化目标：{task_payload['design_targets']['primary_objective']}",
            "- 计算模型：逐层复合材料圆柱壳、初始几何缺陷、外压载荷及任务指定的端部边界条件。",
            "- 分析内容：线性屈曲、工作压力下的首层失效检查、含场变量损伤退化的 Riks 容量分析。",
            "- 未建模项：金属封头、法兰连接、层间分层与制造过程。",
            "- 结果类型：代理预筛估计与有限元数值校核；工艺验收及试验认证结果未提供。",
            "", "## 全部候选方案与生成依据", "",
            f"- 有效候选总数：{len(candidates)}。候选编号保留会话生成时的编号，不因预筛排序重编。",
        ]
        for candidate in candidates:
            geometry = active_geometry(candidate)
            material = candidate.get("material_system") or {}
            layup = candidate.get("layup") or {}
            candidate_id = str(candidate.get("session_candidate_id") or candidate.get("candidate_id") or "-")
            proposed_defect = (candidate.get("provenance") or {}).get("proposed_imperfection_ratio")
            lines.extend([
                "", f"### 候选 {candidate_id}",
                f"- 来源：{candidate.get('source') or '-'}",
                f"- 材料体系：{material.get('name') or material.get('display_name') or material.get('material_key') or '-'}",
                f"- 几何：长度 {format_number(geometry.get('length_mm'))} mm，半径 {format_number(geometry.get('radius_mm'))} mm，厚度 {format_number(geometry.get('thickness_mm'), None)} mm",
                f"- 铺层：{layup.get('layup') or layup.get('angles_deg') or '-'}",
                *([] if uses_task_angles(layup) else [f"- 铺层参数：alpha={format_number(geometry.get('alpha_deg'), None)} deg，beta={format_number(geometry.get('beta_deg'), None)} deg"]),
                f"- 逐层属性核查：对称性={self._field_text(layup.get('symmetric'))}，平衡性={self._field_text(layup.get('balanced'))}",
                f"- 初始几何缺陷比：{geometry.get('imperfection_ratio')}",
                f"- 候选缺陷条件与任务：{'未记录' if geometry.get('imperfection_ratio') is None else '一致' if geometry['imperfection_ratio'] == summary['imperfection_ratio'] else '不一致'}",
                f"- 生成提案理由（原文）：{candidate.get('rationale') or '未提供'}",
                f"- 来源追踪：{candidate.get('origin_summary') or '见候选生成记录。'}",
                *([f"- 来源提案缺陷比：{proposed_defect}"]
                  if proposed_defect is not None and proposed_defect != geometry.get("imperfection_ratio") else []),
            ])
        lines.extend(["", "## 代理预筛方案与筛选理由", ""])
        screened = [item for item in candidates if item.get("screening_rank") is not None]
        if not screened:
            lines.append("- 未执行代理预筛或未提供预筛记录。")
        for candidate in sorted(screened, key=lambda item: item["screening_rank"]):
            lines.extend([
                "", f"### 排名 {candidate['screening_rank']}：{candidate.get('session_candidate_id') or candidate.get('candidate_id')}",
                f"- 默认送检：{'是' if candidate.get('screening_selected') else '否'}",
                f"- 预筛估计承载压力：{format_number(candidate.get('surrogate_ultimate_pressure_MPa'))} MPa",
                f"- 面密度：{format_number(candidate.get('surrogate_weight') or candidate.get('weight_kg_per_m2'))} kg/m^2",
                f"- 综合得分：{format_number(candidate.get('rank_score'))}",
                f"- 筛选依据：{candidate.get('screening_summary') or '-'}",
                f"- 入选或未入选原因：{candidate.get('selection_reason') or '-'}",
            ])
        lines.extend(["", "## 有限元校核结果", ""])
        if not results:
            lines.append("- 当前没有有限元结果，不能作出最终通过或推荐结论。")
        for result in results:
            capacity = result.get("ultimate_pressure_MPa")
            solved_defect = ((result.get("solved_design") or {}).get("geometry") or {}).get("imperfection_ratio")
            confirmed = not complete_case_result_errors(result) and verified_capacity_pressure(result) is not None
            capacity_check = (
                "满足" if float(capacity) >= working_pressure else "不满足"
            ) if capacity is not None and confirmed else "未确认容量，不作容量通过判定"
            lines.extend([
                "", f"### {result.get('session_candidate_id') or '-'} / {result.get('candidate_id')}",
                f"- 作业状态：{result.get('status') or '-'}",
                *(["- 实际求解几何：" + "，".join(f"{key}={format_parameter(key, value)}" for key, value in active_geometry(result['solved_design']).items())]
                  if (result.get("solved_design") or {}).get("geometry") else []),
                f"- 实际求解缺陷比：{self._field_text(solved_defect, '未记录')}",
                f"- 实际缺陷幅值：{format_number(result.get('imperfection_amplitude_mm'), missing='未记录')} mm；缺陷比按中面半径归一化。",
                f"- 求解缺陷条件与任务：{'未记录' if solved_defect is None else '一致' if solved_defect == summary['imperfection_ratio'] else '不一致'}",
                f"- 工作压力校核：{result.get('service_pressure_check_status') or '-'}",
                f"- 工作压力最大 Hashin 指数：{self._field_text(result.get('service_hashin_index_max'))}",
                f"- 线性屈曲压力：{format_number(result.get('linear_buckling_pressure_MPa'))} MPa",
                f"- {'确认渐进损伤容量' if confirmed else '容量路径峰值（未确认）'}：{format_number(capacity)} MPa",
                f"- 容量与工作压力比较：{capacity_check}",
                f"- 容量依据：{result.get('ultimate_pressure_basis') or '-'}",
                f"- Riks 最大 LPF：{self._field_text(result.get('riks_lpf_max'))}",
                f"- 已确认极限点：{self._field_text(result.get('riks_limit_point_confirmed'))}",
                f"- 损伤分析完整：{self._field_text(result.get('progressive_damage_complete'))}",
                f"- 损伤模型：{result.get('progressive_damage_model') or '-'}",
                f"- 损伤状态变量：{self._field_text(result.get('damage_state_maxima'))}",
                f"- 工作压力应力覆盖：{self._field_text(result.get('service_stress_coverage'))}",
                f"- 后峰终止依据：{result.get('riks_termination_reason') or '-'}",
                f"- 结论：{result.get('verdict') or '未判定'}",
                f"- 诊断说明：{self._field_text(result.get('diagnosis_summary') or result.get('error_log'))}",
                f"- 模态云图数据：{result.get('visualization_json') or '-'}",
            ])
        lines.extend(["", "## 最终推荐设计方案", ""])
        recommendation = summary["recommendation"]
        best = recommendation["selected"]
        if best:
            lines.extend([
                f"- 推荐：{best.get('session_candidate_id') or '-'} / {best['candidate_id']}。",
                f"- 推荐依据：在完成真实校核、容量证据完整且满足任务压力要求的方案中，按“{recommendation['objective']}”比较。",
                f"- 确认容量：{format_number(best['capacity_MPa'])} MPa；工作压力：{format_number(working_pressure)} MPa。",
            ])
        else:
            lines.append("- 当前没有同时具备完整通过证据及目标比较数据的方案，不给出最终推荐。")
        if recommendation["ranked"]:
            unit = {"最大极限压力": "MPa", "最小厚度": "mm", "最小壳体质量": "kg"}.get(recommendation["objective"], "kg/m^2")
            lines.extend(["", f"| 校核方案 | 目标比较值 {unit} | 确认容量 MPa | 相对工作压力余量 % |",
                          "| --- | --- | --- | --- |"])
            for row in recommendation["ranked"]:
                margin = (row["capacity_MPa"] / working_pressure - 1) * 100
                lines.append(f"| {row.get('session_candidate_id') or '-'} / {row['candidate_id']} | "
                             f"{format_number(row['objective_value'], 4)} | {format_number(row['capacity_MPa'])} | {format_number(margin, 2)} |")
            lines.extend(["", "余量按“确认容量 / 工作压力 - 1”计算，不是规范安全系数。比较范围只包含本任务完成完整校核的方案。"])
        for row in recommendation["excluded"]:
            lines.append(f"- {row['candidate_id']} 未参与推荐：{'；'.join(row['reasons'])}。")
        lines.extend(["", self._render_engineering_explanation(summary)])
        return "\n".join(lines)

    def _reportlab(self):
        from reportlab.lib.enums import TA_LEFT
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.cidfonts import UnicodeCIDFont
        from reportlab.pdfbase.ttfonts import TTFont
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

        return {
            "TA_LEFT": TA_LEFT,
            "A4": A4,
            "ParagraphStyle": ParagraphStyle,
            "getSampleStyleSheet": getSampleStyleSheet,
            "pdfmetrics": pdfmetrics,
            "UnicodeCIDFont": UnicodeCIDFont,
            "TTFont": TTFont,
            "Paragraph": Paragraph,
            "SimpleDocTemplate": SimpleDocTemplate,
            "Spacer": Spacer,
            "Table": Table,
            "TableStyle": TableStyle,
        }

    def _register_font(self) -> str:
        rl = self._reportlab()
        preferred_fonts = [
            ("CSAgent_SimSun", Path("C:/Windows/Fonts/simsun.ttc")),
            ("CSAgent_MSYH", Path("C:/Windows/Fonts/msyh.ttc")),
            ("CSAgent_SimHei", Path("C:/Windows/Fonts/simhei.ttf")),
        ]
        for font_name, font_path in preferred_fonts:
            try:
                if font_path.exists():
                    rl["pdfmetrics"].registerFont(rl["TTFont"](font_name, str(font_path)))
                    return font_name
            except Exception:
                continue

        fallback_font = "STSong-Light"
        rl["pdfmetrics"].registerFont(rl["UnicodeCIDFont"](fallback_font))
        return fallback_font

    def _pdf_styles(self, font_name: str) -> Dict[str, object]:
        rl = self._reportlab()
        stylesheet = rl["getSampleStyleSheet"]()
        body = rl["ParagraphStyle"](
            name="CSAgentBody",
            parent=stylesheet["BodyText"],
            fontName=font_name,
            fontSize=10.5,
            leading=15,
            alignment=rl["TA_LEFT"],
            wordWrap="CJK",
            spaceAfter=4,
        )
        return {
            "title": rl["ParagraphStyle"](
                name="CSAgentTitle",
                parent=stylesheet["Title"],
                fontName=font_name,
                fontSize=18,
                leading=24,
                alignment=rl["TA_LEFT"],
                wordWrap="CJK",
                spaceAfter=12,
                keepWithNext=True,
            ),
            "heading2": rl["ParagraphStyle"](
                name="CSAgentHeading2",
                parent=stylesheet["Heading2"],
                fontName=font_name,
                fontSize=14,
                leading=20,
                alignment=rl["TA_LEFT"],
                wordWrap="CJK",
                spaceBefore=10,
                spaceAfter=6,
                keepWithNext=True,
            ),
            "heading3": rl["ParagraphStyle"](
                name="CSAgentHeading3",
                parent=stylesheet["Heading3"],
                fontName=font_name,
                fontSize=12,
                leading=18,
                alignment=rl["TA_LEFT"],
                wordWrap="CJK",
                spaceBefore=8,
                spaceAfter=4,
                keepWithNext=True,
            ),
            "body": body,
            "bullet": rl["ParagraphStyle"](
                name="CSAgentBullet",
                parent=body,
                leftIndent=14,
                firstLineIndent=0,
                bulletIndent=0,
                spaceAfter=3,
            ),
        }

    def _paragraph_text_for_pdf(self, text: str) -> str:
        from markdown_it import MarkdownIt
        tokens = MarkdownIt().parseInline(text.replace("\t", "    ").strip())
        return self._pdf_inline_text(tokens[0].children or []) if tokens else ""

    def _pdf_inline_text(self, tokens) -> str:
        return "".join(
            "<br/>" if token.type == "hardbreak" else " " if token.type == "softbreak"
            else escape(token.content) if token.type in {"text", "code_inline", "html_inline"} else ""
            for token in tokens
        )

    def _build_pdf_story(self, markdown_text: str, font_name: str) -> List[object]:
        rl = self._reportlab()
        styles = self._pdf_styles(font_name)
        story: List[object] = []
        from markdown_it import MarkdownIt
        tokens = MarkdownIt("commonmark").enable("table").parse(markdown_text)
        heading = None
        list_depth = 0
        table_rows = None
        row = None
        for token in tokens:
            if token.type == "heading_open":
                heading = "title" if token.tag == "h1" else "heading2" if token.tag == "h2" else "heading3"
            elif token.type == "heading_close":
                heading = None
            elif token.type in {"bullet_list_open", "ordered_list_open"}:
                list_depth += 1
            elif token.type in {"bullet_list_close", "ordered_list_close"}:
                list_depth -= 1
            elif token.type == "table_open":
                table_rows = []
            elif token.type == "tr_open":
                row = []
            elif token.type == "tr_close":
                table_rows.append(row)
                row = None
            elif token.type == "table_close":
                if table_rows:
                    columns = max(len(row) for row in table_rows)
                    table = rl["Table"](table_rows, colWidths=[(rl["A4"][0] - 80) / columns] * columns,
                                        repeatRows=1, hAlign="LEFT")
                    table.setStyle(rl["TableStyle"]([
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("LINEBELOW", (0, 0), (-1, 0), 0.6, "#888888"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 4),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                        ("TOPPADDING", (0, 0), (-1, -1), 5),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                    ]))
                    story.extend([table, rl["Spacer"](1, 6)])
                table_rows = None
            elif token.type == "inline":
                text = self._pdf_inline_text(token.children or [])
                style = styles[heading or ("bullet" if list_depth else "body")]
                paragraph = rl["Paragraph"](text, style, bulletText="•" if list_depth and row is None else None)
                if row is not None:
                    row.append(paragraph)
                else:
                    story.append(paragraph)
            elif token.type in {"fence", "code_block"}:
                story.append(rl["Paragraph"](escape(token.content).replace("\n", "<br/>"), styles["body"]))

        if not story:
            story.append(rl["Paragraph"]("CSAgent 耐压壳设计报告内容为空。", styles["body"]))
        return story

    def _write_pdf(self, markdown_text: str, pdf_path: Path) -> None:
        rl = self._reportlab()
        pdf_path.parent.mkdir(parents=True, exist_ok=True)
        font_name = self._register_font()
        document = rl["SimpleDocTemplate"](
            str(pdf_path),
            pagesize=rl["A4"],
            leftMargin=40,
            rightMargin=40,
            topMargin=48,
            bottomMargin=48,
            title="CSAgent 耐压壳设计报告",
            author="CSAgent",
        )
        document.build(self._build_pdf_story(markdown_text, font_name))

    def _output_dir(self, value: Any) -> Path:
        if value:
            output_dir = Path(str(value)).expanduser()
        else:
            output_dir = RESULTS_DIR
        output_dir.mkdir(parents=True, exist_ok=True)
        return output_dir

    def run(self, input_data: Dict) -> Dict:
        task = input_data["task"]
        candidates = input_data.get("candidates", [])
        results = self._enrich_results_with_candidate_context(input_data.get("results", []), candidates)
        output_value = input_data.get("output_dir")
        if not output_value and task.get("run_id"):
            run_id = str(task["run_id"])
            if not re.fullmatch(r"RUN_[A-Za-z0-9_]+", run_id):
                raise ValueError("报告会话编号无效")
            output_value = RESULTS_DIR / run_id
        output_dir = self._output_dir(output_value)
        stem, title = self.REPORT_ARTIFACTS["overall"]
        markdown_path = output_dir / f"{stem}.md"
        pdf_path = output_dir / f"{stem}.pdf"
        facts_path = output_dir / f"{stem}_facts.json"
        self._last_llm_explanation_used = False
        summary = self._build_structured_summary(task, results, candidates)
        markdown_text = self._render_markdown(task, results, candidates, summary)
        audit = {"summary": summary, "facts": build_report_facts(summary),
                 "llm_explanation_used": self._last_llm_explanation_used,
                 "llm_explanation_audit": self._last_llm_explanation_audit}
        # 正文、PDF 和事实审计成组发布，生成失败不覆盖已有完整报告。
        with tempfile.TemporaryDirectory(prefix="report_", dir=output_dir) as folder:
            temporary = Path(folder)
            write_text(temporary / markdown_path.name, markdown_text)
            self._write_pdf(markdown_text, temporary / pdf_path.name)
            write_json(temporary / facts_path.name, audit)
            for path in (markdown_path, pdf_path, facts_path):
                (temporary / path.name).replace(path)
        artifact = {
            "markdown_path": str(markdown_path),
            "pdf_path": str(pdf_path),
            "facts_path": str(facts_path),
            "title": title,
            "report_kind": "overall",
            "llm_explanation_used": self._last_llm_explanation_used,
            "markdown_generated": True,
            "pdf_generated": True,
        }
        self.emit("总体设计方案报告已生成")
        return {
            **artifact, "content": markdown_text, "output_dir": str(output_dir),
            "llm_explanation_audit": dict(self._last_llm_explanation_audit),
            "report_outputs": {"overall": artifact},
            "generated_output_keys": ["overall"],
        }

"""快速筛选智能体。"""

from __future__ import annotations

from typing import Dict, List

from agents.base import BaseAgent
from core.config_loader import load_app_config
from core.pressure_hull_profile import estimate_areal_density_kg_per_m2
from core.surrogate_model import SurrogateModelManager
from core.task_contract import effective_screen_top_k


class ScreenerAgent(BaseAgent):
    agent_name = "SCREENER"

    def __init__(self, progress_callback=None) -> None:
        super().__init__(progress_callback=progress_callback)
        self.config = load_app_config()
        self.model_manager = SurrogateModelManager()
        score_config = dict(self.config["pipeline"].get("screening_score", {}))
        self.pressure_weight = float(score_config.get("pressure_weight", 1.0))
        self.weight_penalty = float(score_config.get("weight_penalty", 0.12))

    @property
    def score_formula_text(self) -> str:
        return (
            f"score = {self.pressure_weight:.2f} × P_ult "
            f"- {self.weight_penalty:.2f} × 面密度"
        )

    def _estimate_weight(self, candidate: Dict) -> float:
        return estimate_areal_density_kg_per_m2(
            candidate.get("geometry", {}),
            candidate.get("material_system", {}),
        )

    def rank_candidates(self, task: Dict, candidates: List[Dict]) -> List[Dict]:
        """返回全量候选，仅让正值估计参与排名和默认 Top-K。"""
        requested_top_k = effective_screen_top_k(task, len(candidates))
        if requested_top_k <= 0:
            raise ValueError("代理模型初筛缺少有效 Top-K 数量或候选池为空。")

        enriched: List[Dict] = []
        for candidate in candidates:
            updated = dict(candidate)
            prediction = self.model_manager.predict_candidate_payload(candidate)
            ultimate_pressure = float(prediction["ultimate_pressure_MPa"])
            areal_density = self._estimate_weight(candidate)
            updated["surrogate_ultimate_pressure_MPa"] = round(ultimate_pressure, 3)
            updated["surrogate_PBIPF_MPa"] = round(float(prediction["PBIPF_MPa"]), 3)
            updated["surrogate_uncertainty_MPa"] = prediction["uncertainty_MPa"]
            updated["surrogate_calibration_status"] = prediction["calibration_status"]
            updated["surrogate_prediction_status"] = prediction["prediction_status"]
            eligible = prediction["prediction_status"] == "positive"
            updated["asme_linear_buckling_pressure_MPa"] = round(
                float(prediction["asme_linear_buckling_pressure_MPa"]), 3
            )
            updated["linear_buckling_feature_Q"] = prediction["linear_buckling_feature_Q"]
            updated["linear_buckling_source"] = prediction.get("linear_buckling_source")
            updated["surrogate_weight"] = round(float(areal_density), 3)
            updated["rank_score"] = round(
                float(
                    self.pressure_weight * updated["surrogate_ultimate_pressure_MPa"]
                    - self.weight_penalty * updated["surrogate_weight"]
                ),
                4,
            ) if eligible else None
            updated["screening_breakdown"] = {
                "formula": self.score_formula_text,
                "pressure_component": round(self.pressure_weight * updated["surrogate_ultimate_pressure_MPa"], 4) if eligible else None,
                "weight_component": round(self.weight_penalty * updated["surrogate_weight"], 4),
                "surrogate_detail": prediction,
            }
            validation_error = prediction["uncertainty_MPa"]
            validation_text = f"{validation_error} MPa" if validation_error is not None else "未提供"
            updated["screening_summary"] = (
                f"描述符回归压力估计={updated['surrogate_ultimate_pressure_MPa']} MPa，"
                f"ASME RD-1172线性屈曲压力={updated['asme_linear_buckling_pressure_MPa']} MPa，"
                f"公式测试 RMSE={prediction['model_validation']['regression_testing_rmse_MPa']:.3f} MPa，"
                f"ASME代入评估 RMSE={prediction['model_validation']['deployment_rmse_MPa']:.3f} MPa，"
                f"校准留一验证 RMSE={validation_text}，"
                f"校准状态={updated['surrogate_calibration_status']}，"
                f"面密度={updated['surrogate_weight']} kg/m^2。"
            )
            if eligible:
                updated["screening_summary"] += f" 按 {self.score_formula_text} 得分 {updated['rank_score']}。"
            else:
                updated["screening_summary"] += " 线性估计非正，不参与预筛排名，可人工选择有限元校核。"
            if prediction["model_validation"]["outside_descriptor_range"]:
                updated["screening_summary"] += " 描述符超出拟合训练范围，估计属于外推。"
            enriched.append(updated)

        enriched.sort(key=lambda item: (item["rank_score"] is not None, item["rank_score"] if item["rank_score"] is not None else 0), reverse=True)
        eligible_candidates = [candidate for candidate in enriched if candidate["rank_score"] is not None]
        selected_ids = {str(candidate.get("candidate_id")) for candidate in eligible_candidates[:requested_top_k]}
        for index, candidate in enumerate(enriched, start=1):
            candidate["screening_rank"] = index if candidate["rank_score"] is not None else None
            candidate["screening_selected"] = str(candidate.get("candidate_id")) in selected_ids
            if candidate["rank_score"] is None:
                candidate["selection_reason"] = candidate["screening_summary"]
            elif candidate["screening_selected"]:
                candidate["selection_reason"] = (
                    f"Top-{index} 入选：{candidate['screening_summary']} "
                    "当前排序靠前，适合优先进入真实有限元校核。"
                )
            else:
                candidate["selection_reason"] = (
                    f"排序第 {index}：{candidate['screening_summary']} "
                    "未进入默认 Top-K 校核队列，但仍可由人工选择进入有限元校核。"
                )
        return enriched

    def run(self, input_data: Dict) -> List[Dict]:
        task = input_data["task"]
        candidates = input_data["candidates"]
        requested_top_k = effective_screen_top_k(task, len(candidates))
        ranked = self.rank_candidates(task, candidates)
        selected = [candidate for candidate in ranked if candidate.get("screening_selected")]
        self.emit(
            f"已完成 {len(candidates)} 个候选的批量评分，请求保留 Top-{requested_top_k}，实际返回 {len(selected)} 个。"
        )
        return selected

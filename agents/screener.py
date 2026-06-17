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
        self.uncertainty_penalty = float(score_config.get("uncertainty_penalty", 2.0))

    @property
    def score_formula_text(self) -> str:
        return (
            f"score = {self.pressure_weight:.2f} × P_ult "
            f"- {self.weight_penalty:.2f} × 面密度 "
            f"- {self.uncertainty_penalty:.2f} × 公式不确定度"
        )

    def _estimate_weight(self, candidate: Dict) -> float:
        return estimate_areal_density_kg_per_m2(
            candidate.get("geometry", {}),
            candidate.get("material_system", {}),
        )

    def rank_candidates(self, task: Dict, candidates: List[Dict]) -> List[Dict]:
        requested_top_k = effective_screen_top_k(task, len(candidates))
        if requested_top_k <= 0:
            raise ValueError("代理模型初筛缺少有效 Top-K 数量或候选池为空。")

        enriched: List[Dict] = []
        for candidate in candidates:
            updated = dict(candidate)
            prediction = self.model_manager.predict_candidate_payload(candidate)
            ultimate_pressure = float(prediction["ultimate_pressure_MPa"])
            uncertainty = float(prediction["uncertainty_MPa"])
            areal_density = self._estimate_weight(candidate)
            updated["surrogate_ultimate_pressure_MPa"] = round(ultimate_pressure, 3)
            updated["surrogate_PBIPF_MPa"] = round(float(prediction["PBIPF_MPa"]), 3)
            updated["surrogate_uncertainty_MPa"] = round(uncertainty, 3)
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
                    - self.uncertainty_penalty * updated["surrogate_uncertainty_MPa"]
                ),
                4,
            )
            updated["screening_breakdown"] = {
                "formula": self.score_formula_text,
                "pressure_component": round(self.pressure_weight * updated["surrogate_ultimate_pressure_MPa"], 4),
                "weight_component": round(self.weight_penalty * updated["surrogate_weight"], 4),
                "uncertainty_component": round(self.uncertainty_penalty * updated["surrogate_uncertainty_MPa"], 4),
                "surrogate_detail": prediction,
            }
            updated["screening_summary"] = (
                f"代理预测极限压力={updated['surrogate_ultimate_pressure_MPa']} MPa，"
                f"ASME RD-1172线性屈曲压力={updated['asme_linear_buckling_pressure_MPa']} MPa，"
                f"PBIPF 预测极限压力为 {updated['surrogate_PBIPF_MPa']} MPa，"
                f"面密度={updated['surrogate_weight']} kg/m^2，"
                f"按 {self.score_formula_text} 得分 {updated['rank_score']}。"
            )
            enriched.append(updated)

        enriched.sort(key=lambda item: item["rank_score"], reverse=True)
        selected_ids = {str(candidate.get("candidate_id")) for candidate in enriched[:requested_top_k]}
        for index, candidate in enumerate(enriched, start=1):
            candidate["screening_rank"] = index
            candidate["screening_selected"] = str(candidate.get("candidate_id")) in selected_ids
            if candidate["screening_selected"]:
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

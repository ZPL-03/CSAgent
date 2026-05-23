"""耐压壳 DOE 候选采样器。"""

from __future__ import annotations

from typing import Any, Dict, List

import numpy as np

from core.config_loader import load_app_config, load_material_db, load_param_ranges
from core.id_utils import format_candidate_id
from core.pressure_hull_profile import (
    layup_pattern,
    load_param_ranges_for_type,
    normalize_geometry,
    normalize_layup,
    required_geometry_params,
    resolve_hull_type,
)
from core.rule_checker import RuleChecker
from core.task_contract import task_payload_from_request


class DOESampler:
    """使用拉丁超立方采样生成耐压壳几何、铺层与材料组合。"""

    def __init__(self) -> None:
        app_config = load_app_config()
        self.random_seed = int(app_config["pipeline"]["random_seed"])
        self.param_ranges = load_param_ranges()
        self.material_db = load_material_db()
        self.rule_checker = RuleChecker()
        self.layup_templates = list(self.param_ranges.get("layup_templates", []))
        if not self.layup_templates:
            self.layup_templates = [{"name": "BASE_90_AB", "pattern": "[90_4/(±alpha/±beta)_8/90_4]"}]
        self.material_catalog = self._build_material_catalog()

    def _build_material_catalog(self) -> List[Dict[str, Any]]:
        catalog: List[Dict[str, Any]] = []
        for material_key, payload in self.material_db.items():
            catalog.append(
                {
                    "name": payload.get("display_name", material_key),
                    "density_kg_per_m3": float(payload.get("density_kg_per_m3", 1550.0)),
                    "E1_GPa": float(payload.get("E1_GPa", 102.0)),
                    "E2_GPa": float(payload.get("E2_GPa", 7.0)),
                    "G12_GPa": float(payload.get("G12_GPa", 3.35)),
                    "nu12": float(payload.get("nu12", 0.16)),
                    "Xt_MPa": float(payload.get("Xt_MPa", 0.0)),
                    "Xc_MPa": float(payload.get("Xc_MPa", 0.0)),
                    "Yt_MPa": float(payload.get("Yt_MPa", 0.0)),
                    "Yc_MPa": float(payload.get("Yc_MPa", 0.0)),
                    "S_MPa": float(payload.get("S_MPa", 0.0)),
                    "material_key": material_key,
                }
            )
        return catalog

    def _task_payload(self, task: Dict[str, Any]) -> Dict[str, Any]:
        return task_payload_from_request(task)

    def _material_candidates(self, task: Dict[str, Any]) -> List[Dict[str, Any]]:
        material = dict(self._task_payload(task).get("material_system", {}))
        if material.get("is_user_specified", False):
            return [material]
        return [dict(item) for item in self.material_catalog] or [material]

    def _select_material(self, task: Dict[str, Any], ordinal_index: int) -> Dict[str, Any]:
        options = self._material_candidates(task)
        if not options:
            return dict(self._task_payload(task).get("material_system", {}))
        return dict(options[(max(ordinal_index, 1) - 1) % len(options)])

    def _feature_bounds(
        self,
        task: Dict[str, Any],
        htype: str,
        feature_order: List[str],
    ) -> Dict[str, Dict[str, float]]:
        type_ranges = load_param_ranges_for_type(htype)
        task_ranges = dict(self._task_payload(task).get("geometry_envelope", {}))
        bounds_by_feature: Dict[str, Dict[str, float]] = {}
        for feature in feature_order:
            base = type_ranges.get(feature) or {"min": 0.0, "max": 1.0}
            low = float(base["min"])
            high = float(base["max"])
            task_value = task_ranges.get(feature)
            if isinstance(task_value, (list, tuple)) and len(task_value) >= 2:
                task_low = float(task_value[0])
                task_high = float(task_value[1])
                low = max(low, min(task_low, task_high))
                high = min(high, max(task_low, task_high))
            if low > high:
                low = float(base["min"])
                high = float(base["max"])
            bounds_by_feature[feature] = {"min": low, "max": high}
        return bounds_by_feature

    def _lhs(self, dimensions: int, samples: int, seed_offset: int = 0) -> np.ndarray:
        rng = np.random.default_rng(self.random_seed + seed_offset)
        result = np.zeros((samples, dimensions))
        for dim in range(dimensions):
            cut = np.linspace(0, 1, samples + 1)
            points = cut[:-1] + rng.random(samples) * (cut[1:] - cut[:-1])
            rng.shuffle(points)
            result[:, dim] = points
        return result

    def _layup_payload(self, rng: np.random.Generator, geometry: Dict[str, Any]) -> Dict[str, Any]:
        template = self.layup_templates[int(rng.integers(0, len(self.layup_templates)))]
        template_name = str(template.get("name") or "BASE_90_AB")
        pattern = str(template.get("pattern") or layup_pattern(geometry["alpha_deg"], geometry["beta_deg"], template_name))
        text = (
            pattern.replace("alpha", str(round(float(geometry["alpha_deg"]), 3)))
            .replace("beta", str(round(float(geometry["beta_deg"]), 3)))
            .replace("α", str(round(float(geometry["alpha_deg"]), 3)))
            .replace("β", str(round(float(geometry["beta_deg"]), 3)))
        )
        return normalize_layup({"template_name": template_name, "layup": text}, geometry)

    def _estimate_rationale(self, material_name: str, layup_name: str) -> str:
        return f"DOE 拉丁超立方探索生成 | 材料={material_name} | 铺层模板={layup_name}"

    def sample_candidates(
        self,
        task: Dict[str, Any],
        n_samples: int,
        start_index: int = 1,
        strict_solver_window: bool = False,
        hull_type: str | None = None,
        id_factory=None,
        batch_multiplier: int | None = None,
    ) -> List[Dict[str, Any]]:
        valid_candidates: List[Dict[str, Any]] = []
        generation_round = 0
        candidate_id_factory = id_factory or format_candidate_id
        htype = resolve_hull_type(hull_type)
        feature_order = required_geometry_params(htype)
        type_ranges = self._feature_bounds(task, htype, feature_order)

        while len(valid_candidates) < n_samples and generation_round < 12:
            active_batch_multiplier = max(int(batch_multiplier), 1) if batch_multiplier is not None else (8 if strict_solver_window else 3)
            remaining = n_samples - len(valid_candidates)
            lhs_values = self._lhs(
                len(feature_order),
                max(remaining * active_batch_multiplier, remaining),
                seed_offset=generation_round,
            )
            rng = np.random.default_rng(self.random_seed + 1000 + generation_round)

            for row in lhs_values:
                geometry: Dict[str, float] = {}
                for idx, feature in enumerate(feature_order):
                    bounds = type_ranges.get(feature) or {"min": 0.0, "max": 1.0}
                    value = float(bounds["min"]) + row[idx] * (float(bounds["max"]) - float(bounds["min"]))
                    geometry[feature] = round(float(value), 6 if feature == "imperfection_ratio" else 3)
                geometry = normalize_geometry(htype, geometry)

                layup = self._layup_payload(rng, geometry)
                candidate_index = start_index + len(valid_candidates)
                material_system = self._select_material(task, candidate_index)
                task_payload = self._task_payload(task)
                candidate_id = candidate_id_factory(candidate_index)
                candidate = {
                    "candidate_id": candidate_id,
                    "display_name": candidate_id,
                    "source": "DOE",
                    "hull_type": htype,
                    "geometry": geometry,
                    "layup": layup,
                    "rule_check": {},
                    "surrogate_ultimate_pressure_MPa": None,
                    "surrogate_PBIPF_MPa": None,
                    "surrogate_uncertainty_MPa": None,
                    "asme_linear_buckling_pressure_MPa": None,
                    "linear_buckling_source": None,
                    "surrogate_weight": None,
                    "rank_score": None,
                    "rationale": self._estimate_rationale(
                        material_system.get("name", "Unknown"),
                        layup.get("template_name", "LAYUP"),
                    ),
                    "material_system": material_system,
                    "load_conditions": task_payload["load_conditions"],
                    "boundary_conditions": task_payload["boundary_conditions"],
                    "design_targets": task_payload["design_targets"],
                }
                rule_check = self.rule_checker.run(
                    candidate,
                    strict_solver_window=strict_solver_window,
                    hull_type=htype,
                )
                candidate["rule_check"] = rule_check
                if rule_check["is_valid"]:
                    valid_candidates.append(candidate)
                if len(valid_candidates) >= n_samples:
                    break

            generation_round += 1

        return valid_candidates

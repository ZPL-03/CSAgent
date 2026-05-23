"""任务解析器：规则抽取与任务契约归一化。"""

from __future__ import annotations

import re
from typing import Any, Dict

from core.config_loader import load_material_db
from core.id_utils import next_task_id
from core.schema_validator import validate_or_raise
from core.task_contract import (
    DEFAULT_DESIGN_TARGETS,
    DEFAULT_GEOMETRY_ENVELOPE,
    DEFAULT_LAYUP_CONSTRAINTS,
    build_task_request_record,
    describe_boundary_conditions,
    describe_load_conditions,
    normalize_boundary_conditions,
    normalize_geometry_envelope,
    normalize_load_conditions,
    normalize_task_payload,
    task_payload_from_request,
)


class TaskParser:
    """负责把自然语言耐压壳设计需求解析成结构化任务 JSON。"""

    def __init__(self) -> None:
        self.material_db = load_material_db()

    def _extract_float(self, pattern: str, text: str) -> float | None:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if not match:
            return None
        try:
            return float(match.group(1))
        except (TypeError, ValueError):
            return None

    def _extract_material(self, text: str) -> tuple[Dict[str, Any], bool]:
        lowered = text.lower()
        for material_key, payload in self.material_db.items():
            display_name = str(payload.get("display_name", ""))
            if material_key.lower() in lowered or display_name.lower() in lowered:
                material = dict(payload)
                material["name"] = material.get("display_name", material_key)
                material["material_key"] = material_key
                material["is_user_specified"] = True
                return material, True
        default_key = "T700_Epoxy" if "T700_Epoxy" in self.material_db else next(iter(self.material_db))
        material = dict(self.material_db[default_key])
        material["name"] = material.get("display_name", default_key)
        material["material_key"] = default_key
        material["is_user_specified"] = False
        return material, False

    def _external_pressure_value(self, text: str) -> float | None:
        patterns = [
            r"(?:外压|外部压力|静水压力|压力|p)\s*(?:为|是|=|:|：)?\s*([0-9]+(?:\.[0-9]+)?)\s*(?:MPa|兆帕)",
            r"([0-9]+(?:\.[0-9]+)?)\s*(?:MPa|兆帕)\s*(?:外压|外部压力|静水压力|压力)",
            r"(?:external\s+pressure|hydrostatic\s+pressure|pressure)\s*(?:=|:)?\s*([0-9]+(?:\.[0-9]+)?)\s*MPa",
        ]
        for pattern in patterns:
            value = self._extract_float(pattern, text)
            if value is not None:
                return value
        return None

    def _extract_application(self, text: str) -> str:
        if "潜器" in text or "水下" in text or "深海" in text:
            return "水下航行器复合材料耐压壳"
        if "舱段" in text:
            return "复合材料耐压舱段"
        return "复合材料外压圆柱耐压壳"

    def _extract_load_conditions(self, text: str) -> Dict[str, Any]:
        pressure = self._external_pressure_value(text)
        return normalize_load_conditions({"type": "external_pressure", "external_pressure_MPa": pressure or 30.0})

    def _extract_boundary_conditions(self, text: str) -> Dict[str, Any]:
        return normalize_boundary_conditions(text)

    def _geometry_patterns(self) -> Dict[str, list[str]]:
        return {
            "length_mm": [
                r"(?:长度|壳长|筒长|length|L)\s*(?:为|是|=|:|：)?\s*([0-9]+(?:\.[0-9]+)?)\s*mm",
            ],
            "radius_mm": [
                r"(?:半径|壳半径|内半径|radius|R)\s*(?:为|是|=|:|：)?\s*([0-9]+(?:\.[0-9]+)?)\s*mm",
            ],
            "thickness_mm": [
                r"(?:厚度|壁厚|壳厚|thickness|t)\s*(?:为|是|=|:|：)?\s*([0-9]+(?:\.[0-9]+)?)\s*mm",
            ],
            "alpha_deg": [
                r"(?:alpha|α|铺层角\s*α|角度\s*α)\s*(?:为|是|=|:|：)?\s*([0-9]+(?:\.[0-9]+)?)",
            ],
            "beta_deg": [
                r"(?:beta|β|铺层角\s*β|角度\s*β)\s*(?:为|是|=|:|：)?\s*([0-9]+(?:\.[0-9]+)?)",
            ],
            "imperfection_ratio": [
                r"(?:初始缺陷比|缺陷比|初始缺陷|缺陷幅值|imperfection|Ir)\s*(?:为|是|=|:|：)?\s*([0-9]+(?:\.[0-9]+)?)\s*(%|‰|permille|per\s*mille)?",
            ],
        }

    def _extract_geometry_values(self, text: str) -> Dict[str, float]:
        geometry: Dict[str, float] = {}
        for key, candidates in self._geometry_patterns().items():
            for pattern in candidates:
                match = re.search(pattern, text, flags=re.IGNORECASE)
                if not match:
                    continue
                try:
                    value = float(match.group(1))
                except (TypeError, ValueError):
                    continue
                if key == "imperfection_ratio":
                    unit = (match.group(2) or "").lower() if len(match.groups()) >= 2 else ""
                    if unit in {"‰", "permille", "per mille"}:
                        value = value / 1000.0
                    elif unit == "%" or 0.05 < value <= 1.0:
                        value = value / 100.0
                    elif value > 1.0:
                        value = value / 1000.0
                geometry[key] = value
                break
        return geometry

    def _extract_geometry_envelope(self, text: str) -> Dict[str, Any]:
        geometry = dict(DEFAULT_GEOMETRY_ENVELOPE)
        values = self._extract_geometry_values(text)
        for key, value in values.items():
            width = {
                "length_mm": 60.0,
                "radius_mm": 20.0,
                "thickness_mm": 3.0,
                "alpha_deg": 10.0,
                "beta_deg": 10.0,
                "imperfection_ratio": 0.001,
            }[key]
            if key == "imperfection_ratio":
                geometry[key] = [max(0.001, value - width), min(0.01, value + width)]
            else:
                geometry[key] = [value - width, value + width]
        return normalize_geometry_envelope(geometry)

    def _ultimate_pressure_target_value(self, text: str) -> float | None:
        patterns = [
            r"(?:极限压力|极限强度|失效压力|承压|耐压|P_?ult)\s*(?:不低于|至少|>=|≥|为|是|=|:|：)?\s*([0-9]+(?:\.[0-9]+)?)\s*(?:MPa|兆帕)?",
            r"([0-9]+(?:\.[0-9]+)?)\s*(?:MPa|兆帕)\s*(?:以上|承压|耐压|极限压力|极限强度)",
            r"(?:ultimate\s+pressure|failure\s+pressure|collapse\s+pressure|P_?ult)[^\n\r,;]{0,40}?(?:not\s+less\s+than|at\s+least|>=|=|:)?\s*([0-9]+(?:\.[0-9]+)?)\s*MPa",
            r"(?:ultimate\s+pressure|failure\s+pressure|collapse\s+pressure|P_?ult)\s*(?:>=|=|:)?\s*([0-9]+(?:\.[0-9]+)?)\s*MPa",
        ]
        for pattern in patterns:
            value = self._extract_float(pattern, text)
            if value is not None:
                return value
        return None

    def _objective_from_text(self, text: str) -> tuple[str, bool]:
        objective = "最小壳体质量"
        if "最小厚度" in text:
            return "最小厚度", True
        elif "最小面密度" in text:
            return "最小面密度", True
        elif "承压优先" in text or "压力优先" in text:
            return "最大极限压力", True
        return objective, False

    def _extract_design_targets(self, text: str) -> Dict[str, Any]:
        pressure_value = self._ultimate_pressure_target_value(text)
        objective, _objective_specified = self._objective_from_text(text)
        return {
            "ultimate_pressure_min_MPa": pressure_value or DEFAULT_DESIGN_TARGETS["ultimate_pressure_min_MPa"],
            "primary_objective": objective,
        }

    def _extract_top_k_candidates(self, text: str) -> int:
        patterns = [
            r"(?:初筛保留|筛选后保留|初步保留)\s*([1-9][0-9]?)\s*(?:个)?(?:候选|样本|方案)?",
            r"(?:初筛数量|筛选数量|TopK|Top-K)\D{0,4}([1-9][0-9]?)",
            r"(?:初筛|筛选)\D{0,8}(?:Top[- ]?|TOP[- ]?|top[- ]?)\s*([1-9][0-9]?)",
            r"(?:screen|select|top[- ]?k|top)\D{0,8}([1-9][0-9]?)",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, flags=re.IGNORECASE)
            if match:
                return int(max(1, min(float(match.group(1)), 30.0)))
        raise ValueError("任务缺少初筛保留数量，请在自然语言需求中明确指定。")

    def _extract_total_candidates(self, text: str) -> int:
        patterns = [
            r"(?:总候选|候选总数|候选池|初始候选)\D{0,6}([1-9][0-9]?)\s*(?:个)?(?:候选|样本|方案)?",
            r"(?:生成|给出|提供|输出)\s*([1-9][0-9]?)\s*(?:个)?(?:候选|样本|方案)?",
            r"(?:generate|create|produce)\s*([1-9][0-9]?)\s*(?:candidates|designs|samples)?",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, flags=re.IGNORECASE)
            if match:
                return int(max(1, min(float(match.group(1)), 60.0)))
        raise ValueError("任务缺少候选池总数，请在自然语言需求中明确指定。")

    def _extract_candidate_generation_preferences(self, text: str) -> Dict[str, Any]:
        total_candidates = self._extract_total_candidates(text)
        return {
            "total_candidates": total_candidates,
            "source_allocation_mode": "ratio_2_1_1",
        }

    def _user_boundary_conditions(self, text: str) -> Dict[str, Any] | None:
        lowered = text.lower()
        keywords = ["固支", "固定", "简支", "法兰", "夹持", "clamped", "simply", "flange", "ssss", "cccc"]
        if not any(keyword in text or keyword in lowered for keyword in keywords):
            return None
        return normalize_boundary_conditions(text)

    def _extract_user_input_facts(self, text: str, hints: Dict[str, Any]) -> Dict[str, Any]:
        material, is_user_specified = self._extract_material(text)
        facts: Dict[str, Any] = {
            "candidate_generation": {
                "total_candidates": int(hints["candidate_generation_preferences"]["total_candidates"]),
                "top_k_candidates": int(hints["screening_preferences"]["top_k_candidates"]),
            }
        }

        application = self._extract_application(text)
        if any(keyword in text for keyword in ["潜器", "水下", "深海", "舱段", "耐压壳", "压力壳", "圆柱"]):
            facts["application"] = application

        pressure = self._external_pressure_value(text)
        if pressure is not None:
            facts["load_conditions"] = {
                "type": "external_pressure",
                "external_pressure_MPa": pressure,
            }

        boundary = self._user_boundary_conditions(text)
        if boundary is not None:
            facts["boundary_conditions"] = {
                "type": boundary.get("type"),
                "label": boundary.get("label"),
            }

        geometry_values = self._extract_geometry_values(text)
        if geometry_values:
            facts["geometry"] = geometry_values

        if is_user_specified:
            facts["material_system"] = {
                "name": material.get("name"),
                "material_key": material.get("material_key"),
            }

        design_targets: Dict[str, Any] = {}
        pressure_target = self._ultimate_pressure_target_value(text)
        if pressure_target is not None:
            design_targets["ultimate_pressure_min_MPa"] = pressure_target
        objective, objective_specified = self._objective_from_text(text)
        if objective_specified:
            design_targets["primary_objective"] = objective
        if design_targets:
            facts["design_targets"] = design_targets
        return facts

    def _rule_hints(self, text: str) -> Dict[str, Any]:
        material, is_user_specified = self._extract_material(text)
        hints = {
            "application": self._extract_application(text),
            "load_conditions": self._extract_load_conditions(text),
            "boundary_conditions": self._extract_boundary_conditions(text),
            "geometry_envelope": self._extract_geometry_envelope(text),
            "candidate_generation_preferences": self._extract_candidate_generation_preferences(text),
            "screening_preferences": {"top_k_candidates": self._extract_top_k_candidates(text)},
            "material_system": {
                "name": material["name"],
                "density_kg_per_m3": material["density_kg_per_m3"],
                "E1_GPa": material["E1_GPa"],
                "E2_GPa": material["E2_GPa"],
                "G12_GPa": material["G12_GPa"],
                "nu12": material["nu12"],
                "Xt_MPa": material.get("Xt_MPa"),
                "Xc_MPa": material.get("Xc_MPa"),
                "Yt_MPa": material.get("Yt_MPa"),
                "Yc_MPa": material.get("Yc_MPa"),
                "S_MPa": material.get("S_MPa"),
                "material_key": material.get("material_key"),
                "is_user_specified": is_user_specified,
            },
            "layup_constraints": dict(DEFAULT_LAYUP_CONSTRAINTS),
            "hull_type": "CYLINDRICAL",
            "design_targets": self._extract_design_targets(text),
        }
        hints["user_input_facts"] = self._extract_user_input_facts(text, hints)
        return hints

    def _apply_user_overrides(self, hints: Dict[str, Any], overrides: Dict[str, Any] | None) -> Dict[str, Any]:
        if not isinstance(overrides, dict):
            return hints
        updated = dict(hints)
        generation = dict(updated.get("candidate_generation_preferences", {}))
        screening = dict(updated.get("screening_preferences", {}))
        if overrides.get("total_candidates") is not None:
            generation["total_candidates"] = int(max(1, min(float(overrides["total_candidates"]), 60.0)))
        if overrides.get("top_k_candidates") is not None:
            screening["top_k_candidates"] = int(max(1, min(float(overrides["top_k_candidates"]), 30.0)))
        updated["candidate_generation_preferences"] = generation
        updated["screening_preferences"] = screening
        return updated

    def _text_with_overrides(self, text: str, overrides: Dict[str, Any] | None) -> str:
        if not isinstance(overrides, dict):
            return text
        parts = [text]
        if overrides.get("total_candidates") is not None:
            parts.append(f"生成 {int(overrides['total_candidates'])} 个候选")
        if overrides.get("top_k_candidates") is not None:
            parts.append(f"初筛保留 {int(overrides['top_k_candidates'])} 个候选")
        return "，".join(part for part in parts if str(part).strip())

    def parse_instruction(self, text: str, overrides: Dict[str, Any] | None = None) -> Dict[str, Any]:
        parse_text = self._text_with_overrides(text, overrides)
        hints = self._rule_hints(parse_text)
        hints = self._apply_user_overrides(hints, overrides)
        task = normalize_task_payload(hints)
        validate_or_raise("task.schema.json", task)
        return build_task_request_record(
            task,
            task_id=next_task_id(),
            source="gui_instruction",
        )

    def describe_parse_result(self, task: Dict[str, Any]) -> str:
        normalized = task_payload_from_request(task)
        return (
            f"已解析任务：{normalized['application']} | "
            f"{describe_load_conditions(normalized['load_conditions'])} | "
            f"{describe_boundary_conditions(normalized['boundary_conditions'])} | "
            f"候选池目标 {normalized['candidate_generation_preferences']['total_candidates']} 个 | "
            f"初筛保留 Top-{normalized['screening_preferences']['top_k_candidates']}"
        )

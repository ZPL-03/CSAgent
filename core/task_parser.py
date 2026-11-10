"""任务解析器：规则抽取与任务契约归一化。"""

from __future__ import annotations

import re
from typing import Any, Dict

from core.config_loader import fixed_imperfection_ratio, load_material_db
from core.id_utils import next_task_id
from core.schema_validator import validate_or_raise
from core.task_contract import (
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
    validate_quantity,
)


DEFAULT_SEAWATER_DENSITY_KG_PER_M3 = 1025.0
DEFAULT_GRAVITY_M_PER_S2 = 9.80665
QUANTITY_PATTERN = r"([+-]?\s*(?:[0-9]+(?:\.[0-9]+)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?)(?![0-9.])"


def quantity_request_message(confirmation: str, candidate_count: int = 0) -> str:
    if confirmation == "candidate_count":
        return "需要生成多少个候选方案？请回复 1 至 60 的整数，例如“12 个方案”。"
    return f"候选池共有 {candidate_count} 个方案，代理预筛需要保留多少个？请回复 1 至 {min(30, candidate_count)} 的整数。"


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
            r"([0-9]+(?:\.[0-9]+)?)\s*MPa\s*(?:external\s+pressure|hydrostatic\s+pressure)",
        ]
        for pattern in patterns:
            value = self._extract_float(pattern, text)
            if value is not None:
                return value
        return None

    def _service_depth_value(self, text: str) -> float | None:
        patterns = [
            r"(?:水深|下潜深度|工作深度|设计深度)\s*(?:为|是|=|:|：|达到|约)?\s*([0-9]+(?:\.[0-9]+)?)\s*(?:m|米)(?!m)",
            r"([0-9]+(?:\.[0-9]+)?)\s*(?:m|米)(?:水深|下潜深度|工作深度|设计深度)",
            r"(?:service\s+depth|water\s+depth|diving\s+depth)\s*(?:=|:)?\s*([0-9]+(?:\.[0-9]+)?)\s*m\b",
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
        if pressure is not None:
            return normalize_load_conditions({"type": "external_pressure", "external_pressure_MPa": pressure})
        service_depth = self._service_depth_value(text)
        if service_depth is None:
            raise ValueError("任务缺少外部静水压力或工作水深，请在自然语言需求中明确指定。")
        pressure = DEFAULT_SEAWATER_DENSITY_KG_PER_M3 * DEFAULT_GRAVITY_M_PER_S2 * service_depth / 1_000_000.0
        normalized = normalize_load_conditions(
            {"type": "external_pressure", "external_pressure_MPa": pressure}
        )
        normalized.update(
            {
                "service_depth_m": round(service_depth, 6),
                "seawater_density_kg_per_m3": DEFAULT_SEAWATER_DENSITY_KG_PER_M3,
                "gravity_m_per_s2": DEFAULT_GRAVITY_M_PER_S2,
                "pressure_basis": "rho_g_h_gauge_differential",
            }
        )
        return normalized

    def _extract_boundary_conditions(self, text: str) -> Dict[str, Any]:
        return normalize_boundary_conditions(text)

    def _geometry_patterns(self) -> Dict[str, list[str]]:
        connector = (
            r"(?:\s*(?:为|是|=|:|：|固定|保持|限定|锁定|指定|严格采用|必须|等于|不变|"
            r"参考|建议|中心|基准|附近|左右|约|大约|around|about|reference))*"
        )
        return {
            "length_mm": [
                rf"(?:长度|壳长|筒长|length|L){connector}\s*([0-9]+(?:\.[0-9]+)?)\s*mm",
            ],
            "radius_mm": [
                rf"(?:半径|壳半径|内半径|radius|R){connector}\s*([0-9]+(?:\.[0-9]+)?)\s*mm",
            ],
            "thickness_mm": [
                rf"(?:厚度|壁厚|壳厚|thickness|t){connector}\s*([0-9]+(?:\.[0-9]+)?)\s*mm",
            ],
            "alpha_deg": [
                rf"(?:alpha|α|铺层角\s*α|角度\s*α){connector}\s*([0-9]+(?:\.[0-9]+)?)",
            ],
            "beta_deg": [
                rf"(?:beta|β|铺层角\s*β|角度\s*β){connector}\s*([0-9]+(?:\.[0-9]+)?)",
            ],
            "imperfection_ratio": [
                rf"(?:初始缺陷比|缺陷比|初始缺陷|缺陷幅值|imperfection|Ir){connector}\s*([0-9]+(?:\.[0-9]+)?)\s*(%|‰|permille|per\s*mille)?",
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

    def _extract_fixed_geometry_values(self, text: str, geometry_values: Dict[str, float]) -> Dict[str, float]:
        if not geometry_values:
            return {}

        reference_terms = r"(?:参考|建议|中心|基准|附近|左右|约|大约|around|about|reference)"
        fixed_terms = r"(?:固定|保持|限定|锁定|指定|严格采用|必须|等于|不变)"
        gap = r"[^，。；,;\n]{0,24}"
        whole_reference_patterns = [
            rf"(?:几何|尺寸|结构尺寸){gap}{reference_terms}",
            rf"{reference_terms}{gap}(?:几何|尺寸|结构尺寸)",
        ]
        if any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in whole_reference_patterns):
            return {}

        whole_geometry_patterns = [
            rf"(?:几何|尺寸|结构尺寸){gap}{fixed_terms}",
            rf"{fixed_terms}{gap}(?:几何|尺寸|结构尺寸)",
        ]
        if any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in whole_geometry_patterns):
            return dict(geometry_values)

        labels = {
            "length_mm": r"(?:长度|壳长|筒长|length|\bL\b)",
            "radius_mm": r"(?:半径|壳半径|内半径|radius|\bR\b)",
            "thickness_mm": r"(?:厚度|壁厚|壳厚|thickness|\bt\b)",
            "alpha_deg": r"(?:alpha|α|铺层角\s*α|角度\s*α)",
            "beta_deg": r"(?:beta|β|铺层角\s*β|角度\s*β)",
            "imperfection_ratio": r"(?:初始缺陷比|缺陷比|初始缺陷|缺陷幅值|imperfection|Ir)",
        }
        fixed: Dict[str, float] = {}
        for key, value in geometry_values.items():
            label = labels[key]
            reference_patterns = [
                rf"{reference_terms}{gap}{label}",
                rf"{label}{gap}{reference_terms}",
            ]
            if any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in reference_patterns):
                continue
            fixed[key] = value
        return fixed

    def _extract_geometry_envelope(self, text: str) -> Dict[str, Any]:
        geometry = dict(DEFAULT_GEOMETRY_ENVELOPE)
        values = self._extract_geometry_values(text)
        fixed_values = self._extract_fixed_geometry_values(text, values)
        for key, value in values.items():
            if key == "imperfection_ratio":
                continue
            if key in fixed_values:
                geometry[key] = [value, value]
                continue
            width = {
                "length_mm": 60.0,
                "radius_mm": 20.0,
                "thickness_mm": 3.0,
                "alpha_deg": 10.0,
                "beta_deg": 10.0,
            }[key]
            geometry[key] = [value - width, value + width]
        fixed_defect = fixed_imperfection_ratio()
        specified_defect = values.get("imperfection_ratio")
        if specified_defect is not None and abs(specified_defect - fixed_defect) > 1e-9:
            raise ValueError(f"初始几何缺陷比统一采用 {fixed_defect:g}（{fixed_defect * 1000:g}‰）。")
        geometry["imperfection_ratio"] = [fixed_defect, fixed_defect]
        return normalize_geometry_envelope(geometry)

    def _ultimate_pressure_target_value(self, text: str) -> float | None:
        patterns = [
            r"(?:极限压力|极限强度|失效压力|承压|耐压|P_?ult)[^，。；,;\n]{0,24}?(?:不低于|不少于|不小于|至少|>=|≥|为|是|=|:|：)\s*([0-9]+(?:\.[0-9]+)?)\s*(?:MPa|兆帕)?",
            r"(?:极限压力|极限强度|失效压力|承压|耐压|P_?ult)\s*(?:不低于|不少于|不小于|至少|>=|≥|为|是|=|:|：)?\s*([0-9]+(?:\.[0-9]+)?)\s*(?:MPa|兆帕)?",
            r"([0-9]+(?:\.[0-9]+)?)\s*(?:MPa|兆帕)\s*(?:以上|承压|耐压|极限压力|极限强度)",
            r"(?:ultimate\s+pressure|failure\s+pressure|collapse\s+pressure|P_?ult)[^\n\r,;]{0,40}?(?:not\s+less\s+than|no\s+less\s+than|at\s+least|not\s+below|>=|=|:)?\s*([0-9]+(?:\.[0-9]+)?)\s*MPa",
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

    def _extract_design_targets(self, text: str, service_pressure_MPa: float) -> Dict[str, Any]:
        pressure_value = self._ultimate_pressure_target_value(text)
        objective, _objective_specified = self._objective_from_text(text)
        return {
            "ultimate_pressure_min_MPa": pressure_value or service_pressure_MPa,
            "primary_objective": objective,
        }

    def _extract_top_k_candidates(self, text: str) -> int | None:
        patterns = [
            rf"(?:初筛保留|筛选后保留|初步保留)\s*{QUANTITY_PATTERN}\s*(?:个)?(?:候选|样本|方案)?",
            rf"(?:初筛|筛选|预筛|预选|预筛选)\s*{QUANTITY_PATTERN}\s*(?:个)?(?:候选|样本|方案)?",
            rf"(?:初筛|筛选|预筛|预选|预筛选)[^0-9.+\-，。；,;\n]{{0,8}}?(?:top[- ]?)\s*{QUANTITY_PATTERN}",
            rf"(?:预筛|预选|预筛选|预筛保留|预筛数量)[^0-9.+\-，。；,;\n]{{0,10}}?{QUANTITY_PATTERN}",
            rf"(?<![0-9.+-]){QUANTITY_PATTERN}\s*(?:个)?(?:候选|样本|方案)?[^0-9.+\-，。；,;\n]{{0,8}}?(?:进入|送入|用于|参加)(?:校核|有限元|FEM)",
            rf"(?:初筛数量|筛选数量|TopK|Top-K)[^0-9.+\-，。；,;\n]{{0,4}}?{QUANTITY_PATTERN}",
            rf"(?:keep|retain|reserve)\s*{QUANTITY_PATTERN}\s*(?:screened\s+)?(?:candidates|designs|samples)",
            rf"(?:keep|retain|reserve)\s*{QUANTITY_PATTERN}\s*(?:candidates|designs|samples)?\s*(?:after|following)\s*(?:screening|prescreening|pre[- ]?screening)",
            rf"(?:screen|select|top[- ]?k|top[- ]?)[^0-9.+\-，。；,;\n]{{0,8}}?{QUANTITY_PATTERN}",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, flags=re.IGNORECASE)
            if match:
                return self.validate_quantity(match.group(1), "top_k_candidates")
        return None

    def _extract_total_candidates(self, text: str) -> int | None:
        patterns = [
            rf"(?:总候选|候选总数|候选池|初始候选)[^0-9.+\-，。；,;\n]{{0,6}}?{QUANTITY_PATTERN}\s*(?:个)?(?:候选|样本|方案)?",
            rf"(?:生成|给出|提供|输出)\s*{QUANTITY_PATTERN}\s*(?:个)?(?:候选|样本|方案)?",
            rf"(?:generate|create|produce)\s*{QUANTITY_PATTERN}\s*(?:candidates|designs|samples)?",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, flags=re.IGNORECASE)
            if match:
                return self.validate_quantity(match.group(1), "total_candidates")
        return None

    @staticmethod
    def validate_quantity(value: Any, field: str, available: int | None = None) -> int:
        return validate_quantity(value, field, available)

    def quantity_from_reply(self, text: str, field: str, available: int | None = None) -> int:
        """从当前数量问题的回答中提取单一明确整数。"""
        match = re.fullmatch(rf"\s*(?:请|先|就|需要|生成|保留|筛选|预筛|初筛|方案|候选|数量|共|个|[，。,:：!！\s])*{QUANTITY_PATTERN}\s*(?:个|份)?\s*(?:候选方案|候选|样本|方案)?\s*[。.!！]?\s*", text)
        if match:
            return self.validate_quantity(match.group(1), field, available)
        extractor = self._extract_total_candidates if field == "total_candidates" else self._extract_top_k_candidates
        number = extractor(text)
        if number is None or len(re.findall(r"[0-9]+(?:\.[0-9]+)?", text)) != 1:
            raise ValueError("请直接回复本阶段需要的方案数量，例如“6 个方案”。")
        return self.validate_quantity(number, field, available)

    def _extract_candidate_generation_preferences(self, text: str) -> Dict[str, Any]:
        total_candidates = self._extract_total_candidates(text)
        return {
            "total_candidates": total_candidates,
            "source_allocation_mode": "ratio_2_1_1",
        }

    def _user_boundary_conditions(self, text: str) -> Dict[str, Any] | None:
        lowered = text.lower()
        keywords = ["固支", "简支", "法兰", "夹持", "clamped", "simply", "flange", "ssss", "cccc"]
        fixed_boundary_patterns = [
            r"(?:两端|端部|端面|边界|约束)[^，。；,;\n]{0,8}固定",
            r"固定[^，。；,;\n]{0,8}(?:两端|端部|端面|边界|约束)",
        ]
        has_fixed_boundary = any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in fixed_boundary_patterns)
        if not any(keyword in text or keyword in lowered for keyword in keywords) and not has_fixed_boundary:
            return None
        return normalize_boundary_conditions(text)

    def _extract_user_input_facts(self, text: str, hints: Dict[str, Any]) -> Dict[str, Any]:
        material, is_user_specified = self._extract_material(text)
        facts: Dict[str, Any] = {"candidate_generation": {}}
        for field, preferences in (("total_candidates", "candidate_generation_preferences"),
                                   ("top_k_candidates", "screening_preferences")):
            if hints[preferences].get(field) is not None:
                facts["candidate_generation"][field] = hints[preferences][field]

        application = self._extract_application(text)
        if any(keyword in text for keyword in ["潜器", "水下", "深海", "舱段", "耐压壳", "压力壳", "圆柱"]):
            facts["application"] = application

        pressure = self._external_pressure_value(text)
        if pressure is not None:
            facts["load_conditions"] = {
                "type": "external_pressure",
                "external_pressure_MPa": pressure,
            }
        else:
            service_depth = self._service_depth_value(text)
            if service_depth is not None:
                facts["load_conditions"] = {
                    "type": "external_pressure",
                    "service_depth_m": service_depth,
                    "external_pressure_MPa": round(
                        DEFAULT_SEAWATER_DENSITY_KG_PER_M3
                        * DEFAULT_GRAVITY_M_PER_S2
                        * service_depth
                        / 1_000_000.0,
                        6,
                    ),
                    "pressure_basis": "rho_g_h_gauge_differential",
                }

        boundary = self._user_boundary_conditions(text)
        if boundary is not None:
            facts["boundary_conditions"] = {
                "type": boundary.get("type"),
                "label": boundary.get("label"),
            }

        geometry_values = self._extract_geometry_values(text)
        if geometry_values:
            fixed_geometry = self._extract_fixed_geometry_values(text, geometry_values)
            reference_geometry = {
                key: value
                for key, value in geometry_values.items()
                if key not in fixed_geometry
            }
            if reference_geometry:
                facts["geometry_reference"] = reference_geometry
            if fixed_geometry:
                facts["fixed_geometry"] = fixed_geometry

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
        load_conditions = self._extract_load_conditions(text)
        hints = {
            "application": self._extract_application(text),
            "load_conditions": load_conditions,
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
            "design_targets": self._extract_design_targets(
                text,
                float(load_conditions["external_pressure_MPa"]),
            ),
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
            generation["total_candidates"] = self.validate_quantity(overrides["total_candidates"], "total_candidates")
        if overrides.get("top_k_candidates") is not None:
            screening["top_k_candidates"] = self.validate_quantity(overrides["top_k_candidates"], "top_k_candidates")
        updated["candidate_generation_preferences"] = generation
        updated["screening_preferences"] = screening
        facts = dict(updated.get("user_input_facts") or {})
        quantities = dict(facts.get("candidate_generation") or {})
        for field, values in (("total_candidates", generation), ("top_k_candidates", screening)):
            if overrides.get(field) is not None:
                quantities[field] = values[field]
        facts["candidate_generation"] = quantities
        updated["user_input_facts"] = facts
        return updated

    def _text_with_overrides(self, text: str, overrides: Dict[str, Any] | None) -> str:
        if not isinstance(overrides, dict):
            return text
        parts = [text]
        if overrides.get("total_candidates") is not None:
            total = self.validate_quantity(overrides["total_candidates"], "total_candidates")
            parts.append(f"生成 {total} 个候选")
        if overrides.get("top_k_candidates") is not None:
            top_k = self.validate_quantity(overrides["top_k_candidates"], "top_k_candidates")
            parts.append(f"初筛保留 {top_k} 个候选")
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

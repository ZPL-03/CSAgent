from __future__ import annotations

import re
from typing import Any, Dict, List

from agents.base import BaseAgent
from core.case_retriever import CaseRetriever
from core.config_loader import load_app_config, load_llm_config, load_material_db
from core.domain_knowledge import DomainKnowledgeBase
from core.doe_sampler import DOESampler
from core.id_utils import format_temp_candidate_id
from core.llm_backend import LLMBackend, auto_llm_enabled
from core.pressure_hull_profile import (
    TYPE_DISPLAY_NAMES,
    layup_pattern,
    load_param_ranges_for_type,
    missing_geometry_params,
    normalize_geometry,
    normalize_layup,
    resolve_hull_type,
)
from core.rule_checker import RuleChecker
from core.schema_validator import SchemaValidationError, validate_or_raise
from core.task_contract import (
    requested_candidate_pool_size,
    task_payload_from_request,
)

class CandidateGenAgent(BaseAgent):
    """候选生成编排器，统一调度 LLM、案例迁移与 DOE 三条路径。"""

    agent_name = "CANDIDATE_GEN"

    def __init__(self, progress_callback=None) -> None:
        super().__init__(progress_callback=progress_callback)
        self.app_config = load_app_config()
        self.llm_config = load_llm_config()
        self.material_db = load_material_db()
        self.doe_sampler = DOESampler()
        self.rule_checker = RuleChecker()
        self.case_retriever = CaseRetriever()
        self.knowledge_base = DomainKnowledgeBase()
        self.material_catalog = self._build_material_catalog()
        self.llm_backend: LLMBackend | None = None
        self.last_generation_audit: Dict[str, Any] = {}
        if auto_llm_enabled():
            try:
                self.llm_backend = LLMBackend(self.llm_config)
            except Exception as exc:
                self.emit(f"LLM 后端初始化失败，候选池将由可用来源继续生成：{exc}")

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

    def _material_options(self, task: Dict[str, Any]) -> List[Dict[str, Any]]:
        task_payload = self._task_payload(task)
        task_material = dict(task_payload.get("material_system", {}))
        if task_material.get("is_user_specified", False):
            return [task_material]
        return [dict(item) for item in self.material_catalog] or [task_material]

    def _resolve_material_system(self, task: Dict[str, Any], raw_material: Any, index: int) -> Dict[str, Any]:
        task_payload = self._task_payload(task)
        task_material = dict(task_payload.get("material_system", {}))
        if task_material.get("is_user_specified", False):
            return task_material

        if isinstance(raw_material, dict) and raw_material:
            raw_name = str(raw_material.get("name") or raw_material.get("display_name") or "").strip().lower()
            raw_key = str(raw_material.get("material_key") or "").strip()
            for material in self.material_catalog:
                if raw_key and raw_key == material.get("material_key"):
                    return dict(material)
                if raw_name and raw_name == str(material.get("name", "")).strip().lower():
                    return dict(material)
            raise SchemaValidationError(f"候选材料体系未在项目材料库登记：{raw_material.get('name') or raw_material}")

        options = self._material_options(task)
        if not options:
            return task_material
        return dict(options[(max(index, 1) - 1) % len(options)])

    def _material_is_catalog_registered(self, raw_material: Any) -> bool:
        if not isinstance(raw_material, dict) or not raw_material:
            return False
        raw_name = str(raw_material.get("name") or raw_material.get("display_name") or "").strip().lower()
        raw_key = str(raw_material.get("material_key") or "").strip()
        for material in self.material_catalog:
            if raw_key and raw_key == material.get("material_key"):
                return True
            if raw_name and raw_name == str(material.get("name", "")).strip().lower():
                return True
        return False

    def _user_fact_lines(self, facts: Dict[str, Any]) -> List[str]:
        lines: List[str] = []
        candidate_generation = facts.get("candidate_generation", {})
        if isinstance(candidate_generation, dict):
            if candidate_generation.get("total_candidates") is not None:
                lines.append(f"候选池总数：{candidate_generation['total_candidates']}")
            if candidate_generation.get("top_k_candidates") is not None:
                lines.append(f"初筛保留：{candidate_generation['top_k_candidates']}")
        if facts.get("application"):
            lines.append(f"设计对象：{facts['application']}")
        load_conditions = facts.get("load_conditions", {})
        if isinstance(load_conditions, dict) and load_conditions.get("external_pressure_MPa") is not None:
            lines.append(f"外压：{load_conditions['external_pressure_MPa']} MPa")
        boundary_conditions = facts.get("boundary_conditions", {})
        if isinstance(boundary_conditions, dict) and boundary_conditions.get("label"):
            lines.append(f"边界条件：{boundary_conditions['label']}")
        geometry_reference = facts.get("geometry_reference", {})
        fixed_geometry = facts.get("fixed_geometry", {})
        geometry_labels = {
            "length_mm": "长度",
            "radius_mm": "半径",
            "thickness_mm": "厚度",
            "alpha_deg": "alpha",
            "beta_deg": "beta",
            "imperfection_ratio": "缺陷比",
        }
        if isinstance(geometry_reference, dict) and geometry_reference:
            values = []
            for key in ["length_mm", "radius_mm", "thickness_mm", "alpha_deg", "beta_deg", "imperfection_ratio"]:
                if geometry_reference.get(key) is not None:
                    values.append(f"{geometry_labels[key]}={geometry_reference[key]}")
            if values:
                lines.append("参考几何尺寸（设计中心，非固定约束）：" + "，".join(values))
        if isinstance(fixed_geometry, dict) and fixed_geometry:
            values = []
            for key in ["length_mm", "radius_mm", "thickness_mm", "alpha_deg", "beta_deg", "imperfection_ratio"]:
                if fixed_geometry.get(key) is not None:
                    values.append(f"{geometry_labels[key]}={fixed_geometry[key]}")
            if values:
                lines.append("固定几何约束：" + "，".join(values))
        material = facts.get("material_system", {})
        if isinstance(material, dict) and material.get("name"):
            lines.append(f"材料：{material['name']}")
        design_targets = facts.get("design_targets", {})
        if isinstance(design_targets, dict):
            if design_targets.get("ultimate_pressure_min_MPa") is not None:
                lines.append(f"极限压力目标：不低于 {design_targets['ultimate_pressure_min_MPa']} MPa")
            if design_targets.get("primary_objective"):
                lines.append(f"优化目标：{design_targets['primary_objective']}")
        return lines

    def _knowledge_guidance(self, task: Dict[str, Any], top_k: int) -> List[str]:
        """仅为 LLM 路径检索外部知识库/知识图谱片段，避免与历史案例迁移职责混用。"""
        return self.knowledge_base.format_snippets(task, top_k=max(1, min(3, top_k)))

    def _build_prompt(
        self,
        task: Dict[str, Any],
        desired_count: int,
        knowledge_guidance: List[str] | None = None,
    ) -> tuple[str, str]:
        task_payload = self._task_payload(task)
        hull_type = task_payload.get("hull_type", "CYLINDRICAL")
        type_display = TYPE_DISPLAY_NAMES.get(hull_type, hull_type)
        user_facts = dict(task_payload.get("user_input_facts") or {})
        fact_lines = self._user_fact_lines(user_facts)
        fact_text = "\n".join(f"- {line}" for line in fact_lines)
        constraint_text = "\n".join(f"- {line}" for line in self._candidate_field_constraint_lines(hull_type))
        knowledge_text = (
            "\n\n".join(knowledge_guidance)
            if knowledge_guidance
            else "当前没有可用外部知识库/知识图谱片段，请仅依据任务约束生成。"
        )
        system_prompt = (
            "你是 csllm 领域微调模型中的复合材料耐压壳候选方案生成助手。"
            "本轮输入是系统整理后的工程任务书，不是原始用户自然语言，也不是 JSON 任务契约。"
            "请按自然语言工程回答风格输出，候选方案表是主体，表外说明保持简洁。"
            "候选方案必须用 Markdown 表格表达，列名中直接写出编号、材料、长度、半径或内径、厚度、alpha、beta、铺层形式、缺陷比和推荐理由。"
            "表格中的推荐理由必须用一句话同时包含结构性能依据和制造/缺陷风险依据，不要只写泛化结论。"
            "只能把“用户已给信息”中列出的内容写成用户事实；用户没有给出的工况、材料、几何、目标或边界，不要当成用户事实写入回答。"
            "为了形成候选而提出的材料、铺层角或缺陷比必须写成候选建议值，不能写成用户已给条件。"
            "不要输出 JSON，不要输出 XML 标签，不要展开长篇推理过程。"
        )
        user_prompt = (
            "工程任务：批量生成复合材料耐压壳初始候选方案。\n"
            f"设计对象：{type_display}\n"
            f"需要生成的 LLM 来源候选数量：{desired_count}\n\n"
            f"用户已给信息：\n{fact_text if fact_text else '- 仅给出候选数量和初筛数量'}\n\n"
            f"系统候选字段约束（用于保证候选可解析和可校核，不代表用户已给事实）：\n{constraint_text}\n\n"
            f"外部知识库/知识图谱依据：\n{knowledge_text}\n\n"
            "回答要求：\n"
            f"1. 候选表给出 {desired_count} 行；每行必须包含可解析的材料、长度、半径、厚度、alpha、beta、缺陷比、铺层形式。\n"
            "2. 表格列使用：编号 | 材料 | 长度(mm) | 半径(mm) | 厚度(mm) | alpha(deg) | beta(deg) | 缺陷比 | 铺层形式 | 推荐理由。\n"
            "3. 推荐理由必须说明结构性能依据和制造/缺陷风险依据，例如屈曲稳定性、环向/轴向刚度折中、缠绕或铺放可实现性、铺层角偏差敏感性、缺陷控制风险。\n"
            "4. 未给出的用户事实不要补写为输入条件；如果为了形成候选而提出建议值，请在回答中表明这是候选建议值。\n"
            "5. 表格后最多保留 3 条简短工程说明，不要输出完整报告。"
        )
        return system_prompt, user_prompt

    def _candidate_field_constraint_lines(self, hull_type: str) -> List[str]:
        ranges = load_param_ranges_for_type(hull_type)

        def range_text(key: str) -> str:
            value = ranges.get(key) or {}
            return f"{float(value.get('min', 0.0)):g}-{float(value.get('max', 0.0)):g}"

        material_names = "、".join(str(item.get("name")) for item in self.material_catalog if item.get("name"))
        return [
            f"材料必须从项目材料库选择：{material_names}",
            f"长度 L(mm) 必须为数值；参考尺寸只表示设计中心，候选值仍需在 {range_text('length_mm')} 内提出；只有固定几何约束才必须沿用",
            f"半径 R(mm) 必须为数值；参考尺寸只表示设计中心，候选值仍需在 {range_text('radius_mm')} 内提出；只有固定几何约束才必须沿用",
            f"厚度 t(mm) 必须为数值；参考尺寸只表示设计中心，候选值仍需在 {range_text('thickness_mm')} 内提出；只有固定几何约束才必须沿用",
            f"alpha(deg) 与 beta(deg) 必须为 {range_text('alpha_deg')} 内的两个铺层角建议值",
            f"缺陷比必须为无量纲小数 {range_text('imperfection_ratio')}，也可以写成 1-10‰；不要用 0.05 或 0.07 表示缺陷比",
            "铺层形式使用 [90_4/(±alpha/±beta)_8/90_4] 或 [(±alpha/±beta)_10] 这一类可解析格式",
        ]

    def _split_markdown_row(self, line: str) -> List[str]:
        return [cell.strip() for cell in line.strip().strip("|").split("|")]

    def _is_markdown_separator(self, line: str) -> bool:
        cells = self._split_markdown_row(line)
        return bool(cells) and all(re.fullmatch(r":?-{3,}:?", cell.replace(" ", "")) for cell in cells)

    def _first_number(self, text: str) -> float | None:
        match = re.search(r"[-+]?[0-9]+(?:\.[0-9]+)?", str(text))
        if not match:
            return None
        try:
            return float(match.group(0))
        except ValueError:
            return None

    def _number_midpoint(self, text: str) -> float | None:
        numbers = [float(item) for item in re.findall(r"[-+]?[0-9]+(?:\.[0-9]+)?", str(text))]
        if not numbers:
            return None
        if len(numbers) >= 2 and any(mark in str(text) for mark in ["~", "-", "－", "–", "—", "至", "到"]):
            return (numbers[0] + numbers[1]) / 2.0
        return numbers[0]

    def _parse_imperfection_ratio(self, text: str) -> float | None:
        value = self._first_number(text)
        if value is None:
            return None
        lowered = str(text).lower()
        if "‰" in lowered or "permille" in lowered or value > 1.0:
            return value / 1000.0
        if "%" in lowered or 0.05 < value <= 1.0:
            return value / 100.0
        return value

    def _parse_angles(self, text: str) -> tuple[float | None, float | None]:
        cleaned = str(text).replace("−", "-").replace("－", "-")
        paired_matches = re.findall(r"(?:±|\+/-|\+-)\s*([0-9]+(?:\.[0-9]+)?)\s*(?:°|deg)?", cleaned, flags=re.IGNORECASE)
        paired_values = [float(value) for value in paired_matches if 0.0 <= float(value) <= 180.0]
        if len(paired_values) >= 2:
            return paired_values[0], paired_values[1]
        angle_matches = re.findall(r"\b([0-9]+(?:\.[0-9]+)?)\s*(?:°|deg)?", cleaned, flags=re.IGNORECASE)
        values = [float(value) for value in angle_matches if 0.0 <= float(value) <= 180.0]
        if len(values) >= 2:
            return values[0], values[1]
        return None, None

    def _looks_like_material_text(self, text: str) -> bool:
        stripped = str(text or "").strip()
        if not stripped or re.fullmatch(r"[A-Za-z]?[0-9]+", stripped):
            return False
        lowered = stripped.lower()
        material_tokens = [
            "t700",
            "t800",
            "m40j",
            "epoxy",
            "5228",
            "tde",
            "碳纤维",
            "环氧",
            "树脂",
            "复合材料",
        ]
        return any(token in lowered or token in stripped for token in material_tokens)

    def _material_from_text(self, text: str) -> Dict[str, Any]:
        lowered = str(text).strip().lower()
        for material in self.material_catalog:
            name = str(material.get("name") or "")
            key = str(material.get("material_key") or "")
            if (name and name.lower() in lowered) or (key and key.lower() in lowered):
                return dict(material)
        if self._looks_like_material_text(text):
            return {"name": str(text).strip()}
        return {}

    def _is_identifier_header(self, header: str) -> bool:
        lowered = str(header or "").strip().lower()
        return any(token in lowered for token in ["编号", "序号", "id", "no.", "候选方案"])

    def _parse_candidate_text(self, text: str, headers: List[str] | None = None) -> Dict[str, Any] | None:
        headers = headers or []
        cells = self._split_markdown_row(text) if headers else [str(text)]
        raw: Dict[str, Any] = {
            "geometry": {},
            "layup": {},
            "material_system": {},
            "rationale": "",
            "source_text": str(text).strip(),
        }
        if headers and len(cells) < len(headers):
            return None

        pairs = list(zip(headers, cells)) if headers else [("", cells[0])]
        rationale_parts: List[str] = []
        for header, cell in pairs:
            h = header.lower()
            cell_text = str(cell).strip()
            combined = f"{header} {cell_text}"

            if ("材料" in header or "material" in h) and not self._is_identifier_header(header):
                raw["material_system"] = self._material_from_text(cell_text)
            if ("长度" in header or re.search(r"\bL\b", header, flags=re.IGNORECASE)) and "长径" not in header:
                value = self._number_midpoint(cell_text)
                if value is not None:
                    raw["geometry"]["length_mm"] = value
            if "半径" in header or re.search(r"\bR\b", header, flags=re.IGNORECASE):
                value = self._number_midpoint(cell_text)
                if value is not None:
                    raw["geometry"]["radius_mm"] = value
            if "内径" in header or "直径" in header or "diameter" in h:
                value = self._number_midpoint(cell_text)
                if value is not None:
                    raw["geometry"]["radius_mm"] = value / 2.0
            if "厚" in header or "thickness" in h:
                value = self._number_midpoint(cell_text)
                if value is not None:
                    raw["geometry"]["thickness_mm"] = value
            if "缺陷" in header or "imperfection" in h:
                value = self._parse_imperfection_ratio(cell_text)
                if value is not None:
                    raw["geometry"]["imperfection_ratio"] = value
            if any(token in h for token in ["alpha", "α"]):
                value = self._number_midpoint(cell_text)
                if value is not None:
                    raw["geometry"]["alpha_deg"] = value
            if any(token in h for token in ["beta", "β"]):
                value = self._number_midpoint(cell_text)
                if value is not None:
                    raw["geometry"]["beta_deg"] = value
            if "角" in header or "铺层" in header or "layup" in h:
                alpha, beta = self._parse_angles(cell_text)
                if alpha is not None and beta is not None:
                    if raw["geometry"].get("alpha_deg") is None:
                        raw["geometry"]["alpha_deg"] = alpha
                    if raw["geometry"].get("beta_deg") is None:
                        raw["geometry"]["beta_deg"] = beta
                if "[" in cell_text or "±" in cell_text:
                    raw["layup"]["layup"] = cell_text
            if any(keyword in header for keyword in ["提示", "理由", "优势", "风险", "推荐", "说明"]):
                rationale_parts.append(cell_text)

            radius_match = re.search(r"\bR\s*=\s*([0-9]+(?:\.[0-9]+)?)", combined, flags=re.IGNORECASE)
            if radius_match:
                raw["geometry"]["radius_mm"] = float(radius_match.group(1))
            length_match = re.search(r"\bL\s*=\s*([0-9]+(?:\.[0-9]+)?)", combined, flags=re.IGNORECASE)
            if length_match:
                raw["geometry"]["length_mm"] = float(length_match.group(1))
            thickness_match = re.search(r"\bt\s*=\s*([0-9]+(?:\.[0-9]+)?)", combined, flags=re.IGNORECASE)
            if thickness_match:
                raw["geometry"]["thickness_mm"] = float(thickness_match.group(1))

            if not raw.get("material_system") and self._looks_like_material_text(cell_text):
                material = self._material_from_text(cell_text)
                if material:
                    raw["material_system"] = material

        if not raw["layup"] and raw["geometry"].get("alpha_deg") is not None and raw["geometry"].get("beta_deg") is not None:
            raw["layup"] = {
                "layup": layup_pattern(raw["geometry"]["alpha_deg"], raw["geometry"]["beta_deg"]),
            }
        if rationale_parts:
            raw["rationale"] = "；".join(part for part in rationale_parts if part)
        elif not headers:
            raw["rationale"] = str(text).strip()
        return raw if raw["geometry"] or raw["material_system"] or raw["layup"] else None

    def _parse_markdown_tables(self, text: str) -> List[Dict[str, Any]]:
        lines = str(text or "").splitlines()
        candidates: List[Dict[str, Any]] = []
        index = 0
        while index < len(lines):
            if "|" not in lines[index] or index + 1 >= len(lines) or not self._is_markdown_separator(lines[index + 1]):
                index += 1
                continue
            headers = self._split_markdown_row(lines[index])
            index += 2
            while index < len(lines) and "|" in lines[index]:
                if self._is_markdown_separator(lines[index]):
                    index += 1
                    continue
                raw = self._parse_candidate_text(lines[index], headers)
                if raw is not None:
                    candidates.append(raw)
                index += 1
        return candidates

    def _parse_numbered_candidates(self, text: str) -> List[Dict[str, Any]]:
        candidates: List[Dict[str, Any]] = []
        for line in str(text or "").splitlines():
            stripped = line.strip()
            if not re.search(r"(方案|S[0-9]{1,2}|A[0-9]{1,2}|候选)", stripped, flags=re.IGNORECASE):
                continue
            if not any(term in stripped for term in ["材料", "T700", "T800", "M40J", "±", "R=", "L=", "厚"]):
                continue
            raw = self._parse_candidate_text(stripped)
            if raw is not None:
                candidates.append(raw)
        return candidates

    def _extract_candidates_from_natural_answer(self, text: str) -> List[Dict[str, Any]]:
        candidates = self._parse_markdown_tables(text)
        if not candidates:
            candidates = self._parse_numbered_candidates(text)
        return candidates

    def _merge_user_facts_into_raw_candidate(self, task: Dict[str, Any], raw: Dict[str, Any]) -> Dict[str, Any]:
        task_payload = self._task_payload(task)
        facts = dict(task_payload.get("user_input_facts") or {})
        merged = dict(raw)
        raw_geometry = dict(raw.get("geometry") or {})
        user_geometry = dict(
            (facts.get("fixed_geometry") or {}) if isinstance(facts.get("fixed_geometry"), dict) else {}
        )
        geometry = dict(raw_geometry)
        geometry.update({key: value for key, value in user_geometry.items() if value is not None})
        if geometry:
            merged["geometry"] = geometry

        if isinstance(facts.get("material_system"), dict) and facts["material_system"].get("name"):
            merged["material_system"] = dict(facts["material_system"])
        return merged

    def _llm_raw_candidate_is_usable(self, raw: Dict[str, Any]) -> bool:
        geometry = raw.get("geometry", {})
        if not isinstance(geometry, dict):
            return False
        required = ["length_mm", "radius_mm", "thickness_mm", "alpha_deg", "beta_deg", "imperfection_ratio"]
        if any(geometry.get(key) is None for key in required):
            return False
        if not self._material_is_catalog_registered(raw.get("material_system")):
            return False
        return True

    def _llm_generation_token_budget(self, desired_count: int) -> int:
        if self.llm_backend is None:
            return 1200
        configured_budget = max(
            int(getattr(self.llm_backend, "json_output_tokens", 0) or 0),
            int(getattr(self.llm_backend, "max_tokens", 0) or 0),
            900,
        )
        estimated_budget = max(3000, 1400 + max(int(desired_count), 1) * 500)
        return min(configured_budget, estimated_budget)

    def _repair_geometry_by_task(
        self,
        task: Dict[str, Any],
        hull_type: str,
        geometry: Dict[str, float],
        index: int | None = None,
    ) -> Dict[str, float]:
        _ = task, index
        return normalize_geometry(hull_type, geometry)

    def _repair_layup_if_needed(self, layup: Dict[str, Any], geometry: Dict[str, float]) -> Dict[str, Any]:
        candidate = {
            "geometry": geometry,
            "layup": layup,
            "hull_type": "CYLINDRICAL",
        }
        rule_check = self.rule_checker.run(candidate, strict_solver_window=False, hull_type="CYLINDRICAL")
        details = rule_check.get("details", {})
        if (
            details.get("layup_defined", True)
            and details.get("ply_count_ok", True)
            and details.get("balanced", True)
            and details.get("angle_range_ok", True)
        ):
            return layup
        template_name = str(layup.get("template_name") or "BASE_90_AB")
        if template_name not in {"BASE_90_AB", "NO_OUTER_90", "BENCHMARK_A"}:
            template_name = "BASE_90_AB"
        return normalize_layup(
            {
                "template_name": template_name,
                "layup": layup_pattern(geometry["alpha_deg"], geometry["beta_deg"], template_name),
            },
            geometry,
        )

    def _normalize_candidate(self, task: Dict[str, Any], raw: Dict[str, Any], index: int, source: str) -> Dict[str, Any]:
        task_payload = self._task_payload(task)
        hull_type = resolve_hull_type(raw.get("hull_type") or task_payload.get("hull_type"))
        missing_geometry = missing_geometry_params(raw.get("geometry"), hull_type)
        if missing_geometry:
            raise SchemaValidationError(
                f"{source} 候选缺少必要几何字段：{', '.join(missing_geometry)}"
            )
        geometry = normalize_geometry(hull_type, raw.get("geometry"))
        geometry = self._repair_geometry_by_task(task, hull_type, geometry, index)
        raw_layup = raw.get("layup", {})
        if not raw_layup:
            raw_layup = {"layup": layup_pattern(geometry["alpha_deg"], geometry["beta_deg"])}
        layup = normalize_layup(raw_layup, geometry)
        layup = self._repair_layup_if_needed(layup, geometry)
        material_system = self._resolve_material_system(task, raw.get("material_system"), index)

        candidate_id = format_temp_candidate_id(index)
        candidate = {
            "candidate_id": candidate_id,
            "display_name": candidate_id,
            "source": source,
            "hull_type": hull_type,
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
            "rationale": str(raw.get("rationale", f"{source} 生成候选")),
            "origin_summary": str(raw.get("origin_summary") or raw.get("source_text") or ""),
            "llm_output_excerpt": raw.get("llm_output_excerpt"),
            "material_system": material_system,
            "load_conditions": task_payload["load_conditions"],
            "boundary_conditions": task_payload["boundary_conditions"],
            "design_targets": task_payload["design_targets"],
        }
        candidate["rule_check"] = self.rule_checker.run(
            candidate,
            strict_solver_window=True,
            hull_type=hull_type,
        )
        validate_or_raise("candidate.schema.json", candidate)
        return candidate

    def _llm_candidates(self, task: Dict[str, Any], start_index: int, desired_count: int) -> List[Dict[str, Any]]:
        if self.llm_backend is None or desired_count <= 0:
            return []

        knowledge_guidance = self._knowledge_guidance(task, top_k=max(3, desired_count))
        system_prompt, user_prompt = self._build_prompt(task, desired_count, knowledge_guidance)
        excluded_backend_names: set[str] = set()
        backend_count = len(getattr(self.llm_backend, "backends", []) or [None])

        while len(excluded_backend_names) < backend_count:
            retry_hint = ""
            last_schema_error: Exception | None = None
            for _ in range(int(self.llm_config["fallback"]["max_format_retries"])):
                try:
                    answer = self.llm_backend.chat(
                        system_prompt,
                        user_prompt + retry_hint,
                        max_tokens_override=self._llm_generation_token_budget(desired_count),
                        json_mode=False,
                        excluded_backend_names=excluded_backend_names,
                    )
                    self.emit_llm_trace(
                        self.llm_backend,
                        {"purpose": "candidate_generation", "desired_count": desired_count},
                    )
                    items = self._extract_candidates_from_natural_answer(answer)
                    if not items:
                        raise SchemaValidationError("LLM 自然语言回答中没有可解析的候选表或编号方案")
                    usable_items = []
                    for raw in items:
                        if isinstance(raw, dict):
                            raw["llm_output_excerpt"] = answer
                        merged_raw = self._merge_user_facts_into_raw_candidate(task, raw)
                        if self._llm_raw_candidate_is_usable(merged_raw):
                            usable_items.append(merged_raw)
                    if not usable_items:
                        raise SchemaValidationError("LLM 自然语言回答中没有可解析的完整候选参数")
                    normalized = [
                        self._normalize_candidate(task, raw, start_index + offset, "LLM")
                        for offset, raw in enumerate(usable_items)
                    ]
                    valid_normalized = [candidate for candidate in normalized if candidate["rule_check"]["is_valid"]]
                    if not valid_normalized:
                        reasons = "；".join(
                            "、".join(candidate["rule_check"].get("errors", [])[:3])
                            for candidate in normalized[:3]
                        )
                        retry_hint = (
                            "\n\n上一轮候选未通过项目参数域规则，原因："
                            f"{reasons or '未给出有效规则诊断'}。"
                            "请重新输出候选表，确保长度、半径、厚度、alpha、beta 和缺陷比均在系统候选字段约束范围内。"
                        )
                        raise SchemaValidationError("LLM 候选均未通过参数域规则")
                    return normalized[:desired_count]
                except SchemaValidationError as exc:
                    last_schema_error = exc
                    self.emit(f"LLM 生成失败，准备重试：{exc}")
                except Exception as exc:
                    self.emit_llm_trace(
                        self.llm_backend,
                        {"purpose": "candidate_generation", "desired_count": desired_count, "failed": True},
                    )
                    self.emit(f"LLM 生成失败，准备重试：{exc}")
                    return []

            active_name = str(getattr(getattr(self.llm_backend, "active_backend", None), "name", "") or "")
            if not active_name or active_name in excluded_backend_names:
                break
            excluded_backend_names.add(active_name)
            self.emit(f"LLM 后端 {active_name} 输出不合规，尝试下一个后端：{last_schema_error}")
        return []

    def _case_transfer_candidates(self, task: Dict[str, Any], start_index: int, desired_count: int) -> List[Dict[str, Any]]:
        if desired_count <= 0:
            return []
        transferred: List[Dict[str, Any]] = []
        for offset, case in enumerate(self.case_retriever.retrieve_transferable_cases(self._task_payload(task), top_k=desired_count)):
            raw_design = case.get("design", {})
            if not isinstance(raw_design, dict) or not raw_design:
                continue
            try:
                candidate = self._normalize_candidate(task, raw_design, start_index + offset, "CASE_TRANSFER")
            except SchemaValidationError as exc:
                self.emit(f"案例 {case.get('case_id', 'UNKNOWN')} 迁移失败，已跳过：{exc}")
                continue
            candidate["rationale"] = f"参考历史案例 {case.get('case_id', 'UNKNOWN')} 并按当前任务约束迁移"
            transferred.append(candidate)
            if len(transferred) >= desired_count:
                break
        return transferred

    def _resolve_source_targets(self, task: Dict[str, Any]) -> Dict[str, int]:
        target_total = requested_candidate_pool_size(task)
        preferences = task_payload_from_request(task).get("candidate_generation_preferences", {})
        counts = {
            "llm": preferences.get("llm_candidates"),
            "case_transfer": preferences.get("case_transfer_candidates"),
            "doe": preferences.get("doe_candidates"),
        }
        if all(value is not None for value in counts.values()):
            resolved = {key: int(max(0, min(float(value), 60.0))) for key, value in counts.items()}
        elif any(value is not None for value in counts.values()):
            raise ValueError("显式指定候选来源数量时，需要同时给出 LLM、案例迁移和 DOE 三路数量。")
        else:
            ratio = dict(self.app_config.get("pipeline", {}).get("candidate_source_ratio", {}))
            resolved = self._allocate_source_counts(
                target_total,
                {
                    "llm": int(ratio.get("llm", 2)),
                    "case_transfer": int(ratio.get("case_transfer", 1)),
                    "doe": int(ratio.get("doe", 1)),
                },
            )
        source_total = resolved["llm"] + resolved["case_transfer"] + resolved["doe"]
        if source_total != target_total:
            raise ValueError(f"候选来源数量之和必须等于候选池总数：当前 {source_total} != {target_total}")
        return {
            "total": target_total,
            "llm": resolved["llm"],
            "case_transfer": resolved["case_transfer"],
            "doe": resolved["doe"],
        }

    def _allocate_source_counts(self, total: int, weights: Dict[str, int]) -> Dict[str, int]:
        keys = ["llm", "case_transfer", "doe"]
        positive_weights = {key: max(int(weights.get(key, 0)), 0) for key in keys}
        weight_sum = sum(positive_weights.values())
        if total <= 0 or weight_sum <= 0:
            raise ValueError("候选来源比例无效。")

        raw = {key: total * positive_weights[key] / weight_sum for key in keys}
        counts = {key: int(raw[key]) for key in keys}
        positive_count = sum(1 for value in positive_weights.values() if value > 0)
        if total >= positive_count:
            for key in keys:
                if positive_weights[key] > 0 and counts[key] == 0:
                    counts[key] = 1

        while sum(counts.values()) > total:
            removable = [
                (counts[key] - raw[key], key)
                for key in keys
                if counts[key] > (1 if total >= positive_count and positive_weights[key] > 0 else 0)
            ]
            if not removable:
                break
            _, key = max(removable)
            counts[key] -= 1

        remainder = total - sum(counts.values())
        order = sorted(keys, key=lambda key: raw[key] - int(raw[key]), reverse=True)
        while remainder > 0:
            for key in order:
                if positive_weights[key] <= 0:
                    continue
                counts[key] += 1
                remainder -= 1
                if remainder == 0:
                    break
        return counts

    def _signature_value(self, value: Any, digits: int = 6) -> Any:
        try:
            return round(float(value), digits)
        except (TypeError, ValueError):
            return str(value or "").strip()

    def _candidate_signature(self, candidate: Dict[str, Any]) -> tuple:
        geometry = dict(candidate.get("geometry") or {})
        material = dict(candidate.get("material_system") or {})
        layup = dict(candidate.get("layup") or {})
        geometry_signature = tuple(
            (key, self._signature_value(value, 6 if key == "imperfection_ratio" else 3))
            for key, value in sorted(geometry.items())
            if value is not None
        )
        layup_signature = (
            str(layup.get("template_name") or "").strip(),
            str(layup.get("layup") or "").strip(),
        )
        return (
            str(candidate.get("hull_type") or "CYLINDRICAL").strip(),
            str(material.get("material_key") or material.get("name") or "").strip().lower(),
            geometry_signature,
            layup_signature,
        )

    def _add_unique_candidates(
        self,
        pool: List[Dict[str, Any]],
        incoming: List[Dict[str, Any]],
        seen: set[tuple],
    ) -> tuple[int, int]:
        added = 0
        duplicate = 0
        for candidate in incoming:
            signature = self._candidate_signature(candidate)
            if signature in seen:
                duplicate += 1
                continue
            seen.add(signature)
            pool.append(candidate)
            added += 1
        return added, duplicate

    def _invalid_candidate_reasons(self, candidates: List[Dict[str, Any]], limit: int = 5) -> List[str]:
        reasons: List[str] = []
        for candidate in candidates[:limit]:
            errors = candidate.get("rule_check", {}).get("errors", [])
            joined = "、".join(str(item) for item in errors[:3]) if errors else "规则检查未通过"
            reasons.append(f"{candidate.get('candidate_id', '-')}: {joined}")
        return reasons

    def _build_generation_audit(
        self,
        source_targets: Dict[str, int],
        llm_candidates: List[Dict[str, Any]],
        valid_llm_candidates: List[Dict[str, Any]],
        invalid_llm_candidates: List[Dict[str, Any]],
        llm_added: int,
        llm_duplicates: int,
        transfer_candidates: List[Dict[str, Any]],
        valid_transfer_candidates: List[Dict[str, Any]],
        invalid_transfer_candidates: List[Dict[str, Any]],
        transfer_added: int,
        transfer_duplicates: int,
        doe_candidates: List[Dict[str, Any]],
        doe_added: int,
        doe_duplicates: int,
        doe_round: int,
    ) -> Dict[str, Any]:
        duplicate_total = llm_duplicates + transfer_duplicates + doe_duplicates
        audit = {
            "source_targets": {
                "total": source_targets["total"],
                "LLM": source_targets["llm"],
                "CASE_TRANSFER": source_targets["case_transfer"],
                "DOE": source_targets["doe"],
            },
            "raw_counts": {
                "LLM": len(llm_candidates),
                "CASE_TRANSFER": len(transfer_candidates),
                "DOE": len(doe_candidates),
            },
            "valid_counts": {
                "LLM": len(valid_llm_candidates),
                "CASE_TRANSFER": len(valid_transfer_candidates),
                "DOE": len(doe_candidates),
            },
            "invalid_counts": {
                "LLM": len(invalid_llm_candidates),
                "CASE_TRANSFER": len(invalid_transfer_candidates),
                "DOE": 0,
            },
            "added_counts": {
                "LLM": llm_added,
                "CASE_TRANSFER": transfer_added,
                "DOE": doe_added,
            },
            "duplicate_counts": {
                "LLM": llm_duplicates,
                "CASE_TRANSFER": transfer_duplicates,
                "DOE": doe_duplicates,
                "total": duplicate_total,
            },
            "filter_reasons": {
                "LLM": self._invalid_candidate_reasons(invalid_llm_candidates),
                "CASE_TRANSFER": self._invalid_candidate_reasons(invalid_transfer_candidates),
                "DOE": [],
            },
            "doe_rounds": doe_round,
            "doe_fill_count": doe_added,
        }
        audit["summary"] = (
            f"初始配额 LLM={source_targets['llm']} / 案例迁移={source_targets['case_transfer']} / DOE={source_targets['doe']}；"
            f"有效进入候选池 LLM={llm_added}，案例迁移={transfer_added}，DOE补足={doe_added}；"
            f"规则过滤 LLM={len(invalid_llm_candidates)}，案例迁移={len(invalid_transfer_candidates)}；"
            f"结构去重={duplicate_total}"
        )
        return audit

    def _renumber_session_candidates(self, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        renumbered: List[Dict[str, Any]] = []
        for index, candidate in enumerate(candidates, start=1):
            updated = dict(candidate)
            candidate_id = format_temp_candidate_id(index)
            updated["candidate_id"] = candidate_id
            updated["display_name"] = candidate_id
            updated.pop("persistent_candidate_id", None)
            validate_or_raise("candidate.schema.json", updated)
            renumbered.append(updated)
        return renumbered

    def run(self, task: Dict[str, Any]) -> List[Dict[str, Any]]:
        candidates: List[Dict[str, Any]] = []
        seen_signatures: set[tuple] = set()
        next_index = 1
        source_targets = self._resolve_source_targets(task)

        llm_candidates = self._llm_candidates(task, next_index, source_targets["llm"])
        valid_llm_candidates = [candidate for candidate in llm_candidates if candidate["rule_check"]["is_valid"]]
        invalid_llm_candidates = [candidate for candidate in llm_candidates if not candidate["rule_check"]["is_valid"]]
        if invalid_llm_candidates:
            reasons = "；".join(
                f"{candidate['candidate_id']}：{'、'.join(candidate['rule_check'].get('errors', [])[:3])}"
                for candidate in invalid_llm_candidates[:3]
            )
            self.emit(f"LLM 候选规则过滤 {len(invalid_llm_candidates)} 个：{reasons}")
        llm_added, llm_duplicates = self._add_unique_candidates(candidates, valid_llm_candidates, seen_signatures)
        next_index += len(llm_candidates)

        transfer_candidates = self._case_transfer_candidates(task, next_index, source_targets["case_transfer"])
        valid_transfer_candidates = [candidate for candidate in transfer_candidates if candidate["rule_check"]["is_valid"]]
        invalid_transfer_candidates = [candidate for candidate in transfer_candidates if not candidate["rule_check"]["is_valid"]]
        if invalid_transfer_candidates:
            reasons = "；".join(
                f"{candidate['candidate_id']}：{'、'.join(candidate['rule_check'].get('errors', [])[:3])}"
                for candidate in invalid_transfer_candidates[:3]
            )
            self.emit(f"案例迁移候选规则过滤 {len(invalid_transfer_candidates)} 个：{reasons}")
        transfer_added, transfer_duplicates = self._add_unique_candidates(
            candidates,
            valid_transfer_candidates,
            seen_signatures,
        )
        next_index += len(transfer_candidates)

        hull_type = task_payload_from_request(task).get("hull_type", "CYLINDRICAL")
        doe_candidates: List[Dict[str, Any]] = []
        doe_added = 0
        doe_duplicates = 0
        doe_round = 0
        while len(candidates) < source_targets["total"] and doe_round < 8:
            requested = max(source_targets["total"] - len(candidates), source_targets["doe"] if doe_round == 0 else 1)
            batch = self.doe_sampler.sample_candidates(
                task,
                n_samples=requested,
                start_index=next_index,
                strict_solver_window=True,
                hull_type=hull_type,
                id_factory=format_temp_candidate_id,
            )
            next_index += len(batch)
            doe_candidates.extend(batch)
            added, duplicate = self._add_unique_candidates(candidates, batch, seen_signatures)
            doe_added += added
            doe_duplicates += duplicate
            if not batch:
                break
            doe_round += 1
        candidates = self._renumber_session_candidates(candidates[: source_targets["total"]])
        if len(candidates) != source_targets["total"]:
            raise RuntimeError(f"候选池数量不一致：目标 {source_targets['total']}，实际 {len(candidates)}。")
        generation_audit = self._build_generation_audit(
            source_targets,
            llm_candidates,
            valid_llm_candidates,
            invalid_llm_candidates,
            llm_added,
            llm_duplicates,
            transfer_candidates,
            valid_transfer_candidates,
            invalid_transfer_candidates,
            transfer_added,
            transfer_duplicates,
            doe_candidates,
            doe_added,
            doe_duplicates,
            doe_round,
        )
        self.last_generation_audit = generation_audit
        for candidate in candidates:
            candidate["generation_audit"] = generation_audit
        duplicate_total = llm_duplicates + transfer_duplicates + doe_duplicates
        if duplicate_total:
            self.emit(f"候选去重过滤 {duplicate_total} 个结构等价方案")
        self.emit_event("candidate_generation_audit", "候选来源、过滤、去重与 DOE 补足审计已生成", generation_audit)
        self.emit(
            "候选生成完成："
            f"目标总数 {source_targets['total']}，"
            f"初始配额 LLM={source_targets['llm']} / 案例迁移={source_targets['case_transfer']} / DOE={source_targets['doe']}；"
            f"有效进入候选池 LLM={llm_added}，"
            f"案例迁移={transfer_added}，"
            f"DOE补足={doe_added}"
        )
        return candidates

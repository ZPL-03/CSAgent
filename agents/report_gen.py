"""报告生成智能体。"""

from __future__ import annotations

import json
import re
import unicodedata
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List
from xml.sax.saxutils import escape

from agents.base import BaseAgent
from core.config_loader import load_llm_config
from core.io_utils import write_text
from core.llm_backend import LLMBackend, auto_llm_enabled
from core.paths import RESULTS_DIR
from core.task_contract import describe_boundary_conditions, describe_load_conditions, task_payload_from_request


class ReportGenAgent(BaseAgent):
    agent_name = "REPORT_GEN"
    REPORT_ARTIFACTS = {
        "overall": ("overall_design_report", "CSAgent 总体设计报告"),
        "fem": ("fem_verification_report", "CSAgent FEM 校核报告"),
        "design_solution": ("recommended_design_solution", "CSAgent 推荐设计方案"),
    }

    def __init__(self, progress_callback=None) -> None:
        super().__init__(progress_callback=progress_callback)
        self.llm_config = load_llm_config()
        self.llm_backend: LLMBackend | None = None
        self._last_llm_explanation_used = False
        if auto_llm_enabled():
            try:
                self.llm_backend = LLMBackend(self.llm_config)
            except Exception as exc:
                self.emit(f"报告解释 LLM 后端初始化失败，将使用确定性工程解释：{exc}")

    def _compact_candidate_record(self, candidate: Dict[str, Any]) -> Dict[str, Any]:
        geometry = dict(candidate.get("geometry") or {})
        layup = dict(candidate.get("layup") or {})
        material = dict(candidate.get("material_system") or {})
        return {
            "candidate_id": candidate.get("candidate_id"),
            "session_candidate_id": candidate.get("session_candidate_id") or candidate.get("candidate_id"),
            "display_name": candidate.get("display_name"),
            "source": candidate.get("source"),
            "material": material.get("name") or material.get("display_name") or material.get("material_key"),
            "length_mm": geometry.get("length_mm"),
            "radius_mm": geometry.get("radius_mm"),
            "thickness_mm": geometry.get("thickness_mm"),
            "alpha_deg": geometry.get("alpha_deg"),
            "beta_deg": geometry.get("beta_deg"),
            "imperfection_ratio": geometry.get("imperfection_ratio"),
            "layup": layup.get("layup"),
            "layup_template": layup.get("template_name"),
            "ply_count": layup.get("ply_count"),
            "balanced": layup.get("balanced"),
            "symmetric": layup.get("symmetric"),
            "rationale": candidate.get("rationale"),
            "screening_summary": candidate.get("screening_summary"),
            "selection_reason": candidate.get("selection_reason"),
            "surrogate_ultimate_pressure_MPa": candidate.get("surrogate_ultimate_pressure_MPa"),
            "asme_linear_buckling_pressure_MPa": candidate.get("asme_linear_buckling_pressure_MPa"),
            "rank_score": candidate.get("rank_score"),
            "weight_kg_per_m2": candidate.get("surrogate_weight") or candidate.get("weight_kg_per_m2"),
        }

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
        target_pressure = float(design_targets.get("ultimate_pressure_min_MPa") or 0.0)
        passed = [result for result in results if result.get("verdict") == "通过"]
        confirmed_ultimate_results = [
            result for result in results if result.get("ultimate_pressure_MPa") is not None
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
            "boundary_conditions": describe_boundary_conditions(task_payload["boundary_conditions"]),
            "ultimate_pressure_min_MPa": target_pressure,
            "primary_objective": design_targets.get("primary_objective"),
            "result_count": len(results),
            "passed_count": len(passed),
            "best_pressure_candidate": best_pressure.get("candidate_id") if best_pressure else None,
            "best_pressure_MPa": best_pressure.get("ultimate_pressure_MPa") if best_pressure else None,
            "lightest_candidate": lightest.get("candidate_id") if lightest else None,
            "lightest_weight_kg_per_m2": lightest.get("weight_kg_per_m2") if lightest else None,
            "screened_candidates": [
                self._compact_candidate_record(candidate)
                for candidate in candidates
            ],
            "results": [
                {
                    "candidate_id": result.get("candidate_id"),
                    "session_candidate_id": result.get("session_candidate_id"),
                    "display_name": result.get("display_name"),
                    "status": result.get("status"),
                    "ultimate_pressure_MPa": result.get("ultimate_pressure_MPa"),
                    "linear_buckling_pressure_MPa": result.get("linear_buckling_pressure_MPa"),
                    "ultimate_pressure_basis": result.get("ultimate_pressure_basis"),
                    "riks_lpf_max": result.get("riks_lpf_max"),
                    "imperfection_amplitude_mm": result.get("imperfection_amplitude_mm"),
                    "weight_kg_per_m2": result.get("weight_kg_per_m2"),
                    "verdict": result.get("verdict"),
                    "failure_mode": result.get("failure_mode"),
                    "target_pressure_checked_MPa": result.get("target_pressure_checked_MPa"),
                    "target_hashin_index_max": result.get("target_hashin_index_max"),
                    "target_pressure_check_status": result.get("target_pressure_check_status"),
                    "service_pressure_checked_MPa": result.get("service_pressure_checked_MPa"),
                    "service_hashin_index_max": result.get("service_hashin_index_max"),
                    "service_pressure_check_status": result.get("service_pressure_check_status"),
                    "riks_increment_count": result.get("riks_increment_count"),
                    "riks_limit_point_confirmed": result.get("riks_limit_point_confirmed"),
                    "progressive_damage_complete": result.get("progressive_damage_complete"),
                    "progressive_damage_model": result.get("progressive_damage_model"),
                    "damage_state_maxima": result.get("damage_state_maxima"),
                    "damage_observed": result.get("damage_observed"),
                    "target_stress_coverage": result.get("target_stress_coverage"),
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

    def _render_narrative(self, summary: Dict) -> str:
        target = float(summary.get("ultimate_pressure_min_MPa") or 0.0)
        if summary["passed_count"] > 0:
            overall = (
                f"本轮共完成 {summary['result_count']} 个样本校核，其中 {summary['passed_count']} 个满足"
                f"精确 {target:.3f} MPa 目标压力下的线性屈曲与首层失效联合判据。"
            )
        else:
            overall = (
                f"本轮共完成 {summary['result_count']} 个样本校核，当前没有样本满足"
                f"精确 {target:.3f} MPa 目标压力下的线性屈曲与首层失效联合判据，需要继续迭代。"
            )
        compare = (
            f"已确认渐进损伤极限压力最高样本为 {summary.get('best_pressure_candidate') or '-'}，"
            f"对应极限压力为 {summary.get('best_pressure_MPa') or '-'} MPa；"
            f"面密度最低样本为 {summary.get('lightest_candidate') or '-'}，"
            f"面密度为 {summary.get('lightest_weight_kg_per_m2') or '-'} kg/m^2。"
        )
        suggestion = (
            "建议优先围绕通过样本开展缺陷敏感性、制造偏差和静水压试验复核；"
            "若后续目标提高或面密度约束收紧，再继续调整壁厚、铺层角和铺层模板。"
        )
        return "\n\n".join([overall, compare, suggestion])

    def _field_text(self, value: Any, default: str = "-") -> str:
        if value is None:
            return default
        text = str(value).strip()
        if not text or text.lower() == "none":
            return default
        return text

    def _failure_mode_text(self, value: Any) -> str:
        text = self._field_text(value)
        mapping = {
            "acceptance_adapter": "快速验收校核",
            "deterministic_acceptance_adapter": "快速验收校核",
        }
        return mapping.get(text, text)

    def _render_deterministic_engineering_explanation(self, summary: Dict[str, Any]) -> str:
        candidates = summary.get("screened_candidates") or []
        results = summary.get("results") or []
        materials = sorted({str(item.get("material")) for item in candidates if item.get("material")})
        layups = [str(item.get("layup")) for item in candidates if item.get("layup")]
        passed = [item for item in results if item.get("verdict") == "通过"]
        failed = [item for item in results if item.get("verdict") and item.get("verdict") != "通过"]
        result_notes = [str(item.get("diagnosis_summary")) for item in results if item.get("diagnosis_summary")]

        material_text = "、".join(materials) if materials else "当前结构化数据未提供材料体系"
        layup_text = "；".join(layups[:3]) if layups else "当前结构化数据未提供铺层表达式"
        verdict_text = (
            f"有限元校核中通过 {len(passed)} 个、未通过 {len(failed)} 个。"
            if results
            else "当前结构化数据未提供有限元校核结果。"
        )
        diagnosis_text = "；".join(result_notes[:3]) if result_notes else "当前结构化数据未提供详细失效诊断。"

        return "\n\n".join(
            [
                "### 制造工艺适配性\n"
                f"- 候选材料体系为 {material_text}。圆柱耐压壳可按纤维缠绕或预浸带铺放思路组织制造评审，重点检查铺层角、壁厚和端部约束区域的成型连续性。\n"
                "- 报告中的制造建议不引入新的工艺参数；具体张力、固化制度和检验阈值需要由后续工艺文件或试验件确认。",
                "### 铺层与材料原因\n"
                f"- 入选候选的铺层表达式包括 {layup_text}。实际铺层角与顺序以求解输入中的逐层记录为准，可用于解释环向刚度、轴向刚度和屈曲稳定性的折中关系。\n"
                "- 若后续目标转向更低面密度，应优先比较同一材料体系下的角度组合与厚度变化，避免把材料替换和几何减薄同时混在一次迭代里。",
                "### 缺陷与质量控制\n"
                "- 外压圆柱壳对初始几何缺陷敏感，缺陷幅值会影响非线性屈曲和极限压力判断。建议把圆度、壁厚均匀性、铺层角偏差和分层缺陷作为制造质量控制的核心检查项。\n"
                "- 对通过样本仍需要做缺陷敏感性复核；对未通过样本应优先定位是线性屈曲裕度、Riks 极限点还是局部失效模式导致不满足目标。",
                "### 有限元结果解读与验证\n"
                f"- {verdict_text} {diagnosis_text}\n"
                "- 后续验证应保持代理模型、线性屈曲和非线性后屈曲结果的编号一致，再结合静水压试验或缩比件试验校核安全裕度。",
            ]
        )

    def _build_llm_explanation_payload(self, summary: Dict[str, Any]) -> Dict[str, Any]:
        passed_count = int(summary.get("passed_count") or 0)
        result_count = int(summary.get("result_count") or 0)
        if result_count <= 0:
            overall = "当前未提供有限元校核结果"
        elif passed_count <= 0:
            overall = "当前校核样本未满足设计目标"
        elif passed_count == result_count:
            overall = "当前校核样本均满足设计目标"
        else:
            overall = "当前校核样本中存在满足设计目标的方案"

        return {
            "task": {
                "application": summary.get("application"),
                "load_case": summary.get("load_conditions"),
                "boundary_conditions": summary.get("boundary_conditions"),
                "ultimate_pressure_min_MPa": summary.get("ultimate_pressure_min_MPa"),
                "primary_objective": summary.get("primary_objective"),
            },
            "screened_candidates": [dict(candidate) for candidate in summary.get("screened_candidates", [])],
            "results": [{key: value for key, value in result.items() if key != "design_verdict_basis"}
                        for result in summary.get("results", [])],
            "aggregate": {"overall": overall, "result_count": result_count, "passed_count": passed_count},
            "interpretation_constraints": [
                "数值由报告模板输出；解释不复述数值不代表原始数据缺失。",
                "只有缺失或为null的字段才能描述为未提供，不得把已完成的校核描述为尚未执行。",
                "目标压力通过不等于已确认极限承载力；Riks未确认极限点时不能用线性屈曲压力替代。",
                "各候选铺层分别读取，不得把一份候选的外侧直角层推广到所有候选。",
                "没有试验或性能字段支持时，不比较材料韧性、固化残余应力和层间损伤性能。",
                "progressive_damage_complete为true表示容量分析包含场变量损伤退化，不能写成没有渐进损伤。",
                "damage_state_maxima只表示局部触发标志的最大值，不能据此断言整体损伤已完全发展。",
                "riks_lpf_max是载荷比例系数，不是增量步数或增量大小。",
                "目标压力的弹性起始失效检查与含损伤的Riks容量分析属于不同阶段，不得混淆范围。",
                "post_peak_drop_20_percent表示峰后受控终止，不是异常中断，也不能说作业没有终止或全部正常结束。",
                "symmetric或balanced为false表示该属性不满足，不表示铺层或属性数据缺失。",
                "铺层模板名称不决定对称性，必须读取screened_candidates中的symmetric与balanced布尔属性。",
                "制造工艺尚未指定；只能提出工艺评审建议，不能写成候选已经采用某种工艺。",
                "面密度和承载力分别描述，不在没有效率定义或试验时推断质量效率、刚度优劣或缺陷可接受性。",
                "未显式建模的范围为金属封头、法兰、连接及层间分层；试验认证未执行。",
            ],
        }

    def _numeric_tokens(self, text: str) -> List[float]:
        values: List[float] = []
        for token in re.findall(r"[-+]?[0-9]+(?:\.[0-9]+)?", text):
            try:
                values.append(float(token))
            except ValueError:
                continue
        return values

    def _engineering_numeric_texts(self, text: str) -> List[str]:
        pattern = (
            r"([-+]?[0-9]+(?:\.[0-9]+)?)\s*"
            r"(?:MPa|mm|kg\s*/\s*m\^?2|kg/m²|kg/m2|%|‰|deg|°|LPF|GPa)"
        )
        return [match.group(1) for match in re.finditer(pattern, text, flags=re.IGNORECASE)]

    def _engineering_numeric_tokens(self, text: str) -> List[float]:
        return [float(value) for value in self._engineering_numeric_texts(text)]

    def _llm_text_uses_only_known_numbers(self, text: str, payload: Dict[str, Any]) -> bool:
        serialized_payload = json.dumps(payload, ensure_ascii=False, default=str)
        allowed_values = self._engineering_numeric_tokens(serialized_payload) + self._numeric_tokens(
            serialized_payload
        )
        if not allowed_values:
            return not self._engineering_numeric_tokens(text)
        for token in self._engineering_numeric_texts(text):
            value = Decimal(token)
            # 仅允许显示精度内的舍入误差，保留尾随零所表达的小数位约束。
            rounding_bound = Decimal(1).scaleb(value.as_tuple().exponent) / 2
            if not any(abs(value - Decimal(str(allowed))) <= rounding_bound for allowed in allowed_values):
                return False
        return True

    def _material_codes(self, text: str) -> set[str]:
        text = re.sub(r"\b(?:kg|g)\s*/\s*m2\b", "", text, flags=re.IGNORECASE)
        codes = re.findall(r"\b(?:T|M)[0-9]+[A-Z0-9-]*\b", text, flags=re.IGNORECASE)
        return {code.upper() for code in codes}

    def _llm_text_uses_only_known_material_codes(self, text: str, payload: Dict[str, Any]) -> bool:
        known_codes = self._material_codes(json.dumps(payload, ensure_ascii=False, default=str))
        return self._material_codes(text).issubset(known_codes)

    def _validate_llm_engineering_text(self, text: str, payload: Dict[str, Any]) -> None:
        if "<think" in text.lower() or "</think>" in text.lower():
            raise ValueError("LLM 报告解释包含推理标签")
        if any(term in text for term in ["结构化结果", "对应工程量", "__MAT_CODE"]):
            raise ValueError("LLM 报告解释包含占位式表达")
        if not self._llm_text_uses_only_known_numbers(text, payload):
            raise ValueError("LLM 报告解释包含结构化数据之外的数值")
        if not self._llm_text_uses_only_known_material_codes(text, payload):
            raise ValueError("LLM 报告解释包含结构化数据之外的材料牌号")
        forbidden_structure_terms = ["加强筋", "加筋", "夹芯", "金属衬套"]
        if any(term in text for term in forbidden_structure_terms):
            raise ValueError("LLM 报告解释包含当前设计变量域之外的结构型式")
        candidates = payload.get("screened_candidates") or []
        if candidates and all(candidate.get("symmetric") is False for candidate in candidates):
            if re.search(
                r"(?<!不)(?<!未)(?:采用|属于|代表|具有|为|是|呈)[^。；，,\n]{0,8}"
                r"(?<!非)对称(?:铺层|形式|结构|布置|构型|层合板|性)",
                text,
            ):
                raise ValueError("候选均为非对称铺层，解释不能断言采用对称铺层")
        if "质量效率" in text:
            raise ValueError("未定义质量效率指标，不能把较低面密度等同于较高质量效率")
        if re.search(r"损伤已(?:经)?(?:完全|充分)发展", text):
            raise ValueError("损伤标志最大值不能证明整体损伤已完全发展")
        if re.search(r"Riks\s*最大增量(?:为|是)", text, flags=re.IGNORECASE):
            raise ValueError("Riks 载荷比例系数不能描述为最大增量")
        if re.search(r"已(?:经)?[^。；\n]{0,12}(?:考虑缺陷敏感性|完成缺陷敏感性分析)", text):
            raise ValueError("单一初始缺陷工况不构成已完成缺陷敏感性分析")
        if any(result.get("riks_termination_reason") == "post_peak_drop_20_percent"
               for result in payload.get("results") or []):
            if "未报告校核终止" in text or "作业均正常完成" in text:
                raise ValueError("峰后受控终止不能描述为作业未终止或均正常完成")

    def _normalize_llm_math(self, text: str) -> str:
        from pylatexenc.latex2text import LatexNodes2Text
        from pylatexenc.latexwalker import LatexMathNode, LatexWalker, LatexWalkerParseError

        marker = re.compile(r"(?<!\\)(?:\${1,2}|\\\(|\\\[)")
        converter = LatexNodes2Text()
        walker = LatexWalker(text, tolerant_parsing=False)
        parts: List[str] = []
        offset = 0
        while match := marker.search(text, offset):
            try:
                nodes, _, length = walker.get_latex_nodes(pos=match.start(), read_max_nodes=1)
            except LatexWalkerParseError as exc:
                raise ValueError("报告数学表达式未闭合或无法解析") from exc
            if len(nodes) != 1 or not isinstance(nodes[0], LatexMathNode):
                raise ValueError("报告数学表达式无法识别")
            math_node = nodes[0]

            def check_supported(node) -> None:
                macro = getattr(node, "macroname", None)
                if macro and converter.latex_context.get_macro_spec(macro) is None:
                    raise ValueError(f"报告数学命令不支持转换：{macro}")
                environment = getattr(node, "environmentname", None)
                if environment and converter.latex_context.get_environment_spec(environment) is None:
                    raise ValueError(f"报告数学环境不支持转换：{environment}")
                children = list(getattr(node, "nodelist", None) or [])
                arguments = getattr(getattr(node, "nodeargd", None), "argnlist", None) or []
                for child in [*children, *arguments]:
                    if child is not None:
                        check_supported(child)

            check_supported(math_node)
            converted = converter.nodelist_to_text(math_node.nodelist).strip()
            if not converted:
                raise ValueError("报告数学表达式转换结果为空")
            parts.extend([text[offset:match.start()], converted])
            offset = match.start() + length
        parts.append(text[offset:])
        return "".join(parts)

    def _strip_llm_reasoning_blocks(self, text: str) -> str:
        cleaned = str(text or "")
        cleaned = re.sub(r"(?is)<think\b[^>]*>.*?</think>", "", cleaned)
        cleaned = re.sub(r"(?is)<think\b[^>]*>.*", "", cleaned)
        cleaned = re.sub(r"(?is).*?</think>", "", cleaned)
        cleaned_lines: List[str] = []
        reasoning_heading = re.compile(
            r"^\s*(?:reasoning|analysis|chain\s*of\s*thought|思考过程|推理过程|分析过程)\s*[:：]",
            flags=re.IGNORECASE,
        )
        for raw_line in cleaned.splitlines():
            stripped = raw_line.strip()
            if not stripped:
                cleaned_lines.append("")
                continue
            if reasoning_heading.match(stripped):
                continue
            if re.fullmatch(r"</?think\b[^>]*>", stripped, flags=re.IGNORECASE):
                continue
            cleaned_lines.append(raw_line)
        return "\n".join(cleaned_lines).strip()

    def _deterministic_clean_llm_engineering_text(self, text: str, payload: Dict[str, Any]) -> str:
        text = self._strip_llm_reasoning_blocks(text)
        known_codes = self._material_codes(json.dumps(payload, ensure_ascii=False, default=str))
        forbidden_structure_terms = ["加强筋", "加筋", "夹芯", "金属衬套"]
        cleaned_lines: List[str] = []
        for raw_line in text.splitlines():
            line = raw_line.strip()
            if not line:
                cleaned_lines.append("")
                continue
            if any(term in line for term in forbidden_structure_terms):
                continue
            line_codes = self._material_codes(line)
            if not line_codes.issubset(known_codes):
                continue
            line = re.sub(r"^\s*[0-9]+[.、]\s*", "", line)
            cleaned_lines.append(line)
        cleaned = "\n".join(cleaned_lines).strip()
        return cleaned

    def _sanitize_llm_engineering_text(self, text: str, payload: Dict[str, Any]) -> str:
        if self.llm_backend is None:
            return text
        known_material_codes = sorted(self._material_codes(json.dumps(payload, ensure_ascii=False, default=str)))
        system_prompt = (
            "你是报告解释文本约束清理器。只改写用户给出的中文说明，不新增事实。"
            "删除所有数字、单位、阈值、候选编号、排序编号、替代材料牌号和具体设备参数；"
            "可以保留允许材料牌号列表中的材料牌号。"
            "优化建议只保留材料、铺层、厚度、缺陷质量控制、有限元和试验复核，不保留新增结构型式建议。"
            "保留制造工艺适配性、铺层/材料原因、缺陷与质量控制、有限元结果解读、后续验证建议五类定性内容。"
            "输出 Markdown，只使用三级标题和短横线项目；不要输出表格、JSON、编号列表或代码块。"
            "必须按结构化事实纠正范围和缺失性陈述；已完成的场变量损伤分析不能说成未提供或未执行。"
            "不输出 LaTeX 数学标记。"
            "解释只给出有条件的复核建议，不断言制造工艺已确定，也不推断铺层对称性、质量效率或刚度优劣。"
        )
        user_prompt = (
            f"允许保留的材料牌号：{', '.join(known_material_codes) if known_material_codes else '无'}\n\n"
            f"结构化事实 JSON：{json.dumps(payload, ensure_ascii=False, default=str)}\n\n"
            "请清理以下报告解释文本：\n"
            f"{text}"
        )
        answer = self.llm_backend.chat(
            system_prompt,
            user_prompt,
            max_tokens_override=min(max(int(self.llm_backend.max_tokens), 1800), 2400),
            json_mode=False,
        ).strip()
        self.emit_llm_trace(self.llm_backend, {"purpose": "report_explanation_sanitize"})
        return self._normalize_llm_math(self._strip_llm_reasoning_blocks(answer))

    def _render_llm_engineering_explanation(self, summary: Dict[str, Any]) -> str:
        if self.llm_backend is None:
            return ""
        payload = self._build_llm_explanation_payload(summary)
        system_prompt = (
            "你是复合材料外压圆柱耐压壳设计报告解释助手。"
            "只能基于用户提供的 JSON 结构化事实撰写中文工程解释。"
            "不得新增候选编号、数值、材料名、工况或有限元结论；不得改写 verdict、压力、面密度和排序。"
            "可以从复合材料圆柱壳常用制造评审角度讨论纤维缠绕、预浸带铺放、固化、圆度控制和无损检测，"
            "但不能把 JSON 中没有的设备、厂家、具体张力、固化温度、检验阈值或替代材料牌号写成事实。"
            "优化建议限定在当前候选变量域内，只讨论材料、铺层、厚度、缺陷质量控制、有限元和试验复核，"
            "不要引入加强筋、夹芯、金属衬套或其他未在输入中出现的结构型式。"
            "数值事实已经由报告模板输出，解释段禁止出现数字、角度、单位、阈值和候选编号，只做定性解释。"
            "解释只给出有条件的制造和验证建议，不断言候选已经采用某种工艺，"
            "不从模板名称推断对称性，不推断质量效率、初始刚度优劣或制造缺陷已被验收。"
            "必须遵循 interpretation_constraints；不复述数据不代表缺少数据，不重复建议执行已经完成的相同校核。"
            "输出 Markdown，只使用三级标题和短横线项目；不要输出表格、JSON、编号列表或代码块。"
        )
        user_prompt = (
            "请生成报告中的“工程解释与制造建议”段落，必须覆盖：制造工艺适配性、铺层/材料原因、缺陷与质量控制、"
            "有限元结果解读、后续验证建议。只做定性解释，不要复述 JSON 中的数字，不要给出新的数字、阈值、候选编号或替代材料牌号；"
            "如果结构化数据缺少某项，请明确说明当前结构化数据未提供。\n\n"
            f"结构化事实 JSON：\n{json.dumps(payload, ensure_ascii=False, indent=2, default=str)}"
        )
        answer = self.llm_backend.chat(
            system_prompt,
            user_prompt,
            max_tokens_override=min(max(int(self.llm_backend.max_tokens), 1800), 2600),
            json_mode=False,
        ).strip()
        self.emit_llm_trace(self.llm_backend, {"purpose": "report_engineering_explanation"})
        if not answer:
            return ""
        answer = self._normalize_llm_math(self._strip_llm_reasoning_blocks(answer))
        if not answer:
            return ""
        try:
            self._validate_llm_engineering_text(answer, payload)
        except ValueError:
            answer = self._sanitize_llm_engineering_text(answer, payload)
            try:
                self._validate_llm_engineering_text(answer, payload)
            except ValueError:
                answer = self._deterministic_clean_llm_engineering_text(answer, payload)
                self._validate_llm_engineering_text(answer, payload)
        return self._postprocess_engineering_explanation(answer)

    def _postprocess_engineering_explanation(self, text: str) -> str:
        """清理报告解释段的标题层级和数值占位语，避免与模板标题重复。"""
        text = re.sub(r"(?is)<think>.*?</think>", "", str(text or ""))
        cleaned_lines: List[str] = []
        for raw_line in text.splitlines():
            line = unicodedata.normalize("NFKC", raw_line.rstrip())
            stripped = line.strip()
            if not stripped:
                cleaned_lines.append("")
                continue
            if stripped.lower().startswith("<think") or stripped.lower().endswith("</think>"):
                continue
            if re.fullmatch(r"#{1,6}\s*工程解释与制造建议", stripped) or stripped == "工程解释与制造建议":
                continue
            if stripped.startswith("# ") or stripped.startswith("## "):
                stripped = re.sub(r"^#+\s*", "", stripped)
                line = f"### {stripped}"
            elif re.match(r"^\s*\d+[.、]\s+", stripped):
                line = "- " + re.sub(r"^\s*\d+[.、]\s+", "", stripped)
            line = re.sub(r"[Vv]erd[Dd]?ict", "结论", line)
            line = line.replace("为对应工程量", "由已记录指标给出")
            line = line.replace("为结构化结果中的对应工程量", "由已记录指标给出")
            line = line.replace("对应工程量", "已记录指标")
            cleaned_lines.append(line)
        cleaned = "\n".join(cleaned_lines).strip()
        while "\n\n\n" in cleaned:
            cleaned = cleaned.replace("\n\n\n", "\n\n")
        return cleaned

    def _render_engineering_explanation(self, summary: Dict[str, Any]) -> str:
        self._last_llm_explanation_used = False
        if self.llm_backend is not None:
            try:
                llm_text = self._render_llm_engineering_explanation(summary)
                if llm_text:
                    self._last_llm_explanation_used = True
                    return llm_text
            except ValueError as exc:
                self.emit_event("report_explanation_rejected",
                                f"总体报告解释未通过事实或格式校验，已使用结构化说明：{exc}",
                                {"report_kind": "overall", "reason": str(exc)})
            except Exception as exc:
                self.emit_llm_trace(self.llm_backend, {"purpose": "report_engineering_explanation", "failed": True})
                self.emit(f"报告 LLM 工程解释生成失败，已使用确定性解释：{exc}")
        return self._render_deterministic_engineering_explanation(summary)

    def _deterministic_artifact_explanation(self, report_kind: str, summary: Dict[str, Any]) -> str:
        if report_kind == "fem":
            return "\n".join(
                [
                    "- FEM 校核报告以 FEM_AGENT 返回的结果记录为准，报告生成智能体只解释校核链路、失效模式和复核建议。",
                    "- 线性屈曲、非线性后屈曲、缺陷幅值和云图路径都来自有限元结果字段，不由 LLM 改写。",
                    "- 后续复核应保持正式 C 编号、会话 TMP 编号和案例回流编号一致，便于追踪每个校核样本。",
                ]
            )
        if report_kind == "design_solution":
            return "\n".join(
                [
                    "- 推荐设计方案报告汇总候选生成、代理初筛和正式 FEM 编号之间的追踪关系。",
                    "- 候选来源以各候选的 source 和 provenance 为准，不把系统支持的来源视为该任务已执行的来源。",
                    "- 方案是否进入工程冻结，应结合 FEM 校核结果、制造工艺评审和后续试验验证共同确认。",
                ]
            )
        return "\n".join(
            [
                "- 总体设计报告综合任务、候选、代理初筛、FEM 校核、知识证据和报告建议。",
                "- 数值、编号、排序和结论来自结构化流程数据；LLM 只补充定性工程解释。",
            ]
        )

    def _render_report_artifact_explanation(self, report_kind: str, summary: Dict[str, Any]) -> str:
        fallback = self._deterministic_artifact_explanation(report_kind, summary)
        if self.llm_backend is None:
            return fallback
        payload = self._build_llm_explanation_payload(summary)
        purpose_map = {
            "overall": "总体设计报告",
            "fem": "FEM 校核报告",
            "design_solution": "推荐设计方案",
        }
        purpose = purpose_map.get(report_kind, "设计报告")
        system_prompt = (
            "你是复合材料外压圆柱耐压壳设计报告解释助手。"
            "只基于结构化 JSON 事实，为指定报告类型写一段中文工程说明。"
            "禁止新增候选编号、数值、单位、材料牌号、工况、设备参数或结构型式。"
            "数值事实由模板输出，解释段只做定性归纳。"
            "必须遵循 interpretation_constraints；不得把已提供的数值说成缺失，也不得把已执行的校核说成尚未执行。"
            "输出 Markdown 短横线条目，不输出表格、JSON 或代码块。"
        )
        user_prompt = (
            f"报告类型：{purpose}\n"
            "说明内容需要覆盖该报告类型对应的用途、可追溯性和后续复核建议。"
            "如果结构化数据缺少某项事实，只能说明当前结构化数据未提供。\n\n"
            f"结构化事实 JSON：\n{json.dumps(payload, ensure_ascii=False, indent=2, default=str)}"
        )
        try:
            answer = self.llm_backend.chat(
                system_prompt,
                user_prompt,
                max_tokens_override=min(max(int(self.llm_backend.max_tokens), 900), 1600),
                json_mode=False,
            ).strip()
            self.emit_llm_trace(self.llm_backend, {"purpose": f"report_{report_kind}_explanation"})
            if not answer:
                return fallback
            answer = self._normalize_llm_math(self._strip_llm_reasoning_blocks(answer))
            if not answer:
                return fallback
            try:
                self._validate_llm_engineering_text(answer, payload)
            except ValueError:
                answer = self._sanitize_llm_engineering_text(answer, payload)
                self._validate_llm_engineering_text(answer, payload)
            self._last_llm_explanation_used = True
            return self._postprocess_engineering_explanation(answer)
        except ValueError as exc:
            self.emit_event("report_explanation_rejected",
                            f"{purpose}解释未通过事实或格式校验，已使用结构化说明：{exc}",
                            {"report_kind": report_kind, "reason": str(exc)})
            return fallback
        except Exception as exc:
            if self.llm_backend is not None:
                self.emit_llm_trace(self.llm_backend, {"purpose": f"report_{report_kind}_explanation", "failed": True})
            self.emit(f"{purpose} LLM 解释生成失败，已使用确定性解释：{exc}")
            return fallback

    def _render_markdown(self, task: Dict, results: List[Dict], candidates: List[Dict]) -> str:
        task_payload = task_payload_from_request(task)
        summary = self._build_structured_summary(task, results, candidates)
        narrative = self._render_narrative(summary)
        engineering_explanation = self._render_engineering_explanation(summary)
        results_by_session_id = {
            str(result.get("session_candidate_id")): result
            for result in results
            if str(result.get("session_candidate_id") or "").strip()
        }
        results_by_candidate_id = {
            str(result.get("candidate_id")): result
            for result in results
            if str(result.get("candidate_id") or "").strip()
        }
        lines = [
            "# CSAgent 耐压壳设计报告",
            "",
            f"- 会话任务编号：`{task.get('task_id') or '-'}`",
            f"- 应用场景：{task_payload['application']}",
            f"- 工况：{describe_load_conditions(task_payload['load_conditions'])}",
            f"- 边界条件：{describe_boundary_conditions(task_payload['boundary_conditions'])}",
            f"- 极限压力目标：不低于 {task_payload['design_targets']['ultimate_pressure_min_MPa']} MPa",
            f"- 优化目标：{task_payload['design_targets']['primary_objective']}",
            "",
            "## 工程摘要",
            "",
            narrative,
            "",
            "## 代理模型初筛说明",
        ]
        if candidates:
            for candidate in candidates:
                linked_result = (
                    results_by_session_id.get(str(candidate.get("candidate_id") or ""))
                    or results_by_candidate_id.get(str(candidate.get("candidate_id") or ""))
                    or {}
                )
                official_candidate_id = linked_result.get("candidate_id") or "-"
                lines.extend(
                    [
                        "",
                        f"### {candidate.get('display_name', candidate.get('candidate_id'))}",
                        f"- 会话编号：{candidate.get('candidate_id')}",
                        f"- 正式编号：{official_candidate_id}",
                        f"- 初筛摘要：{candidate.get('screening_summary') or '暂无'}",
                        f"- 入选理由：{candidate.get('selection_reason') or '尚未进入 Top-K'}",
                    ]
                )
        else:
            lines.extend(["", "- 本轮未提供代理模型初筛上下文。"])

        lines.extend(
            [
                "",
                "## 有限元校核结果",
            ]
        )
        for result in results:
            lines.extend(
                [
                    "",
                    f"### {result.get('display_name', result['candidate_id'])} / {result['candidate_id']}",
                    f"- 状态：{result['status']}",
                    f"- 极限压力：{self._field_text(result.get('ultimate_pressure_MPa'))} MPa",
                    f"- 线性屈曲压力：{self._field_text(result.get('linear_buckling_pressure_MPa'))} MPa",
                    f"- 极限压力依据：{result.get('ultimate_pressure_basis') or '-'}",
                    f"- Riks 最大 LPF：{self._field_text(result.get('riks_lpf_max'))}",
                    f"- 缺陷幅值：{self._field_text(result.get('imperfection_amplitude_mm'))} mm",
                    f"- 面密度：{self._field_text(result.get('weight_kg_per_m2'))}",
                    f"- 失效模式：{self._failure_mode_text(result.get('failure_mode'))}",
                    f"- 结论：{result.get('verdict')}",
                    f"- 工程说明：{self._field_text(result.get('diagnosis_summary'))}",
                    f"- 模态云图数据：{result.get('visualization_json') or '-'}",
                ]
            )
        lines.extend(
            [
                "",
                "## 工程解释与制造建议",
                "",
                engineering_explanation,
            ]
        )
        return "\n".join(lines)

    def _candidate_result_maps(self, results: List[Dict]) -> tuple[Dict[str, Dict], Dict[str, Dict]]:
        by_session_id = {
            str(result.get("session_candidate_id")): result
            for result in results
            if str(result.get("session_candidate_id") or "").strip()
        }
        by_candidate_id = {
            str(result.get("candidate_id")): result
            for result in results
            if str(result.get("candidate_id") or "").strip()
        }
        return by_session_id, by_candidate_id

    def _render_fem_report_markdown(self, task: Dict, results: List[Dict], candidates: List[Dict] | None = None) -> str:
        task_payload = task_payload_from_request(task)
        candidates = candidates or []
        summary = self._build_structured_summary(task, results, candidates)
        explanation = self._render_report_artifact_explanation("fem", summary)
        lines = [
            "# CSAgent FEM 校核报告",
            "",
            f"- 会话任务编号：`{task.get('task_id') or '-'}`",
            f"- 工况：{describe_load_conditions(task_payload['load_conditions'])}",
            f"- 边界条件：{describe_boundary_conditions(task_payload['boundary_conditions'])}",
            f"- 极限压力目标：不低于 {task_payload['design_targets']['ultimate_pressure_min_MPa']} MPa",
            f"- 校核样本数量：{len(results)}",
            "",
            "## 校核结论摘要",
        ]
        passed = [result for result in results if result.get("verdict") == "通过"]
        lines.extend(
            [
                "",
                f"- 通过样本：{len(passed)} / {len(results)}",
                "- 有限元结果由 FEM_AGENT 写入结果记录，报告生成智能体只读取并归纳，不改写压力、编号和结论。",
                "- 模型范围：复合材料圆柱壳；金属封头、法兰、连接、层间分层和试验认证不在校核范围内。",
            ]
        )
        for result in results:
            lines.extend(
                [
                    "",
                    f"## {result.get('display_name', result.get('candidate_id'))} / {result.get('candidate_id')}",
                    f"- 会话候选编号：{result.get('session_candidate_id') or '-'}",
                    f"- 作业状态：{result.get('status') or '-'}",
                    f"- 线性屈曲压力：{result.get('linear_buckling_pressure_MPa') or '-'} MPa",
                    f"- 极限压力：{result.get('ultimate_pressure_MPa') or '-'} MPa",
                    f"- 极限压力依据：{result.get('ultimate_pressure_basis') or '-'}",
                    f"- Riks 最大 LPF：{result.get('riks_lpf_max') or '-'}",
                    f"- 缺陷幅值：{result.get('imperfection_amplitude_mm') or '-'} mm",
                    f"- 面密度：{result.get('weight_kg_per_m2') or '-'}",
                    f"- 失效模式：{self._failure_mode_text(result.get('failure_mode'))}",
                    f"- 校核结论：{result.get('verdict') or '-'}",
                    f"- 诊断摘要：{result.get('diagnosis_summary') or '-'}",
                    f"- 目标压力应力覆盖：{self._field_text(result.get('target_stress_coverage'))}",
                    f"- 损伤模型：{result.get('progressive_damage_model') or '未执行或未形成证据'}",
                    f"- 损伤状态变量：{self._field_text(result.get('damage_state_maxima'))}",
                    f"- 后峰终止依据：{result.get('riks_termination_reason') or '-'}",
                    f"- 云图或模态数据：{result.get('visualization_json') or '-'}",
                ]
            )
        if not results:
            lines.extend(["", "- 当前没有可写入 FEM 校核报告的有限元结果。"])
        lines.extend(["", "## FEM 校核解释与复核建议", "", explanation])
        return "\n".join(lines)

    def _render_design_solution_markdown(self, task: Dict, candidates: List[Dict], results: List[Dict]) -> str:
        task_payload = task_payload_from_request(task)
        summary = self._build_structured_summary(task, results, candidates)
        explanation = self._render_report_artifact_explanation("design_solution", summary)
        by_session_id, by_candidate_id = self._candidate_result_maps(results)
        lines = [
            "# CSAgent 推荐设计方案",
            "",
            f"- 会话任务编号：`{task.get('task_id') or '-'}`",
            f"- 工况：{describe_load_conditions(task_payload['load_conditions'])}",
            f"- 极限压力目标：不低于 {task_payload['design_targets']['ultimate_pressure_min_MPa']} MPa",
            "- 候选来源比例：LLM / 案例迁移 / DOE 由任务配置和有效候选去重结果共同确定。",
            "",
            "## 入选候选与正式编号",
        ]
        if candidates:
            for candidate in candidates:
                result = (
                    by_session_id.get(str(candidate.get("candidate_id") or ""))
                    or by_candidate_id.get(str(candidate.get("candidate_id") or ""))
                    or {}
                )
                geometry = candidate.get("geometry") or {}
                material = candidate.get("material_system") or {}
                layup = candidate.get("layup") or {}
                lines.extend(
                    [
                        "",
                        f"### {candidate.get('display_name', candidate.get('candidate_id'))}",
                        f"- 会话候选编号：{candidate.get('candidate_id') or '-'}",
                        f"- 正式校核编号：{result.get('candidate_id') or '-'}",
                        f"- 来源：{candidate.get('source') or '-'}",
                        f"- 材料体系：{material.get('name') or material.get('display_name') or material.get('material_key') or '-'}",
                        (
                            f"- 几何参数：L={geometry.get('length_mm') or '-'} mm，"
                            f"R={geometry.get('radius_mm') or '-'} mm，"
                            f"t={geometry.get('thickness_mm') or '-'} mm"
                        ),
                        (
                            f"- 铺层角与缺陷：alpha={geometry.get('alpha_deg') or '-'} deg，"
                            f"beta={geometry.get('beta_deg') or '-'} deg，"
                            f"imperfection={geometry.get('imperfection_ratio') or '-'}"
                        ),
                        f"- 铺层形式：{layup.get('layup') or '-'}",
                        f"- 代理预测极限压力：{candidate.get('surrogate_ultimate_pressure_MPa') or '-'} MPa",
                        f"- ASME RD-1172 线性屈曲压力：{candidate.get('asme_linear_buckling_pressure_MPa') or '-'} MPa",
                        f"- 面密度：{candidate.get('surrogate_weight') or candidate.get('weight_kg_per_m2') or '-'}",
                        f"- 入选理由：{candidate.get('selection_reason') or candidate.get('screening_summary') or '-'}",
                        f"- FEM 校核结论：{result.get('verdict') or '尚未校核'}",
                    ]
                )
        else:
            lines.extend(["", "- 当前没有可写入推荐方案报告的候选记录。"])
        lines.extend(
            [
                "",
                "## 交付说明",
                "",
                "- 推荐方案报告只汇总候选生成、代理初筛和正式 FEM 编号之间的追踪关系。",
                "- 最终是否进入工程冻结状态，应结合 FEM 校核报告、制造工艺评审和试验验证计划共同确认。",
                "",
                "## 方案解释与后续设计建议",
                "",
                explanation,
            ]
        )
        return "\n".join(lines)

    def _write_markdown_pdf_pair(self, markdown_text: str, markdown_path: Path, pdf_path: Path) -> bool:
        write_text(markdown_path, markdown_text)
        try:
            self._write_pdf(markdown_text, pdf_path)
            return True
        except ModuleNotFoundError as exc:
            self.emit(f"PDF 依赖缺失，已跳过 PDF 导出：{exc}")
            return False

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

    def _normalize_report_kind(self, value: Any) -> str:
        report_kind = str(value or "all").strip().lower()
        aliases = {
            "latest": "all",
            "all_reports": "all",
            "overall_design": "overall",
            "design": "design_solution",
            "solution": "design_solution",
            "recommended": "design_solution",
            "fem_verification": "fem",
        }
        report_kind = aliases.get(report_kind, report_kind)
        if report_kind not in {"all", "overall", "fem", "design_solution"}:
            raise ValueError(f"未知报告类型：{value}")
        return report_kind

    def _output_dir(self, value: Any) -> Path:
        if value:
            output_dir = Path(str(value)).expanduser()
        else:
            output_dir = RESULTS_DIR
        output_dir.mkdir(parents=True, exist_ok=True)
        return output_dir

    def _artifact_paths(self, output_dir: Path, report_kind: str) -> tuple[Path, Path, str]:
        stem, title = self.REPORT_ARTIFACTS[report_kind]
        return output_dir / f"{stem}.md", output_dir / f"{stem}.pdf", title

    def run(self, input_data: Dict) -> Dict:
        task = input_data["task"]
        raw_results = input_data.get("results", [])
        candidates = input_data.get("candidates", [])
        results = self._enrich_results_with_candidate_context(raw_results, candidates)
        report_kind = self._normalize_report_kind(input_data.get("report_kind"))
        output_value = input_data.get("output_dir")
        if not output_value and task.get("run_id"):
            run_id = str(task["run_id"])
            if not re.fullmatch(r"RUN_[A-Za-z0-9_]+", run_id):
                raise ValueError("报告会话编号无效")
            output_value = RESULTS_DIR / run_id
        output_dir = self._output_dir(output_value)
        self._last_llm_explanation_used = False
        selected_keys = list(self.REPORT_ARTIFACTS) if report_kind == "all" else [report_kind]

        selected_texts: Dict[str, str] = {}
        selected_llm_usage: Dict[str, bool] = {}
        base_markdown_text: str | None = None
        if "overall" in selected_keys:
            base_markdown_text = self._render_markdown(task, results, candidates)
            selected_llm_usage["overall"] = self._last_llm_explanation_used
            selected_texts["overall"] = base_markdown_text.replace(
                "# CSAgent 耐压壳设计报告",
                "# CSAgent 总体设计报告",
                1,
            )
        if "fem" in selected_keys:
            self._last_llm_explanation_used = False
            selected_texts["fem"] = self._render_fem_report_markdown(task, results, candidates)
            selected_llm_usage["fem"] = self._last_llm_explanation_used
        if "design_solution" in selected_keys:
            self._last_llm_explanation_used = False
            selected_texts["design_solution"] = self._render_design_solution_markdown(task, candidates, results)
            selected_llm_usage["design_solution"] = self._last_llm_explanation_used

        markdown_text = selected_texts.get("overall") or next(iter(selected_texts.values()), "")
        markdown_path = output_dir / "latest_report.md"
        pdf_path = output_dir / "latest_report.pdf"
        pdf_generated = False
        if report_kind == "all":
            latest_text = base_markdown_text or self._render_markdown(task, results, candidates)
            markdown_text = latest_text
            pdf_generated = self._write_markdown_pdf_pair(latest_text, markdown_path, pdf_path)

        report_outputs = {}
        generated_output_keys: List[str] = []
        for key in selected_keys:
            artifact_markdown_path, artifact_pdf_path, title = self._artifact_paths(output_dir, key)
            payload = {
                "markdown_path": str(artifact_markdown_path),
                "pdf_path": str(artifact_pdf_path),
                "title": title,
                "report_kind": key,
                "llm_explanation_used": selected_llm_usage[key],
            }
            text = selected_texts[key]
            generated = self._write_markdown_pdf_pair(
                text,
                artifact_markdown_path,
                artifact_pdf_path,
            )
            payload["pdf_generated"] = generated
            payload["markdown_generated"] = True
            if generated:
                generated_output_keys.append(key)
            else:
                payload["pdf_path"] = None
            report_outputs[key] = payload

        if report_kind != "all":
            selected_payload = report_outputs[report_kind]
            markdown_path = Path(selected_payload["markdown_path"])
            pdf_path_value = selected_payload.get("pdf_path")
            pdf_path = Path(pdf_path_value) if pdf_path_value else pdf_path
            pdf_generated = bool(selected_payload.get("pdf_generated"))
            markdown_text = selected_texts[report_kind]

        self.emit("Markdown/PDF 报告已生成" if pdf_generated else "Markdown 报告已生成")
        return {
            "markdown_path": str(markdown_path),
            "pdf_path": str(pdf_path) if pdf_generated else None,
            "content": markdown_text,
            "llm_explanation_used": any(selected_llm_usage.values()),
            "report_kind": report_kind,
            "output_dir": str(output_dir),
            "report_outputs": report_outputs,
            "generated_output_keys": generated_output_keys,
        }

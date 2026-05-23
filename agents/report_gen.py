"""报告生成智能体。"""

from __future__ import annotations

import json
import re
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
            "rationale": candidate.get("rationale"),
            "screening_summary": candidate.get("screening_summary"),
            "selection_reason": candidate.get("selection_reason"),
            "surrogate_ultimate_pressure_MPa": candidate.get("surrogate_ultimate_pressure_MPa"),
            "asme_linear_buckling_pressure_MPa": candidate.get("asme_linear_buckling_pressure_MPa"),
            "rank_score": candidate.get("rank_score"),
            "weight_kg_per_m2": candidate.get("surrogate_weight") or candidate.get("weight_kg_per_m2"),
        }

    def _build_structured_summary(self, task: Dict, results: List[Dict], candidates: List[Dict]) -> Dict:
        task_payload = task_payload_from_request(task)
        design_targets = dict(task_payload.get("design_targets", {}))
        target_pressure = float(design_targets.get("ultimate_pressure_min_MPa") or 0.0)
        passed = [result for result in results if result.get("verdict") == "通过"]
        best_pressure = max(results, key=lambda item: float(item.get("ultimate_pressure_MPa") or 0.0), default=None)
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
                    "display_name": result.get("display_name"),
                    "ultimate_pressure_MPa": result.get("ultimate_pressure_MPa"),
                    "linear_buckling_pressure_MPa": result.get("linear_buckling_pressure_MPa"),
                    "ultimate_pressure_basis": result.get("ultimate_pressure_basis"),
                    "riks_lpf_max": result.get("riks_lpf_max"),
                    "imperfection_amplitude_mm": result.get("imperfection_amplitude_mm"),
                    "weight_kg_per_m2": result.get("weight_kg_per_m2"),
                    "verdict": result.get("verdict"),
                    "failure_mode": result.get("failure_mode"),
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
                f"极限压力不低于 {target:.3f} MPa 的目标。"
            )
        else:
            overall = (
                f"本轮共完成 {summary['result_count']} 个样本校核，当前没有样本满足"
                f"极限压力不低于 {target:.3f} MPa 的目标，需要继续迭代。"
            )
        compare = (
            f"极限压力最高样本为 {summary.get('best_pressure_candidate') or '-'}，"
            f"极限压力为 {summary.get('best_pressure_MPa') or '-'} MPa；"
            f"面密度最低样本为 {summary.get('lightest_candidate') or '-'}，"
            f"面密度为 {summary.get('lightest_weight_kg_per_m2') or '-'} kg/m^2。"
        )
        suggestion = (
            "建议优先围绕通过样本开展缺陷敏感性、制造偏差和静水压试验复核；"
            "若后续目标提高或面密度约束收紧，再继续调整壁厚、铺层角和铺层模板。"
        )
        return "\n\n".join([overall, compare, suggestion])

    def _render_deterministic_engineering_explanation(self, summary: Dict[str, Any]) -> str:
        candidates = summary.get("screened_candidates") or []
        results = summary.get("results") or []
        materials = sorted({str(item.get("material")) for item in candidates if item.get("material")})
        layups = [str(item.get("layup")) for item in candidates if item.get("layup")]
        angles = [
            f"±{item.get('alpha_deg')}/±{item.get('beta_deg')}"
            for item in candidates
            if item.get("alpha_deg") is not None and item.get("beta_deg") is not None
        ]
        passed = [item for item in results if item.get("verdict") == "通过"]
        failed = [item for item in results if item.get("verdict") and item.get("verdict") != "通过"]
        result_notes = [str(item.get("diagnosis_summary")) for item in results if item.get("diagnosis_summary")]

        material_text = "、".join(materials) if materials else "当前结构化数据未提供材料体系"
        angle_text = "、".join(angles[:5]) if angles else "当前结构化数据未提供铺层角"
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
                f"- 入选候选的主要角度组合为 {angle_text}，铺层表达式包括 {layup_text}。这些字段来自候选结构化数据，可用于解释环向刚度、轴向刚度和屈曲稳定性的折中关系。\n"
                "- 若后续目标转向更低面密度，应优先比较同一材料体系下的角度组合与厚度变化，避免把材料替换和几何减薄同时混在一次迭代里。",
                "### 缺陷与质量控制\n"
                "- 外压圆柱壳对初始几何缺陷敏感，缺陷幅值会影响非线性屈曲和极限压力判断。建议把圆度、壁厚均匀性、铺层角偏差和分层缺陷作为制造质量控制的核心检查项。\n"
                "- 对通过样本仍需要做缺陷敏感性复核；对未通过样本应优先定位是线性屈曲裕度、Riks 极限点还是局部失效模式导致不满足目标。",
                "### 有限元结果解读与验证\n"
                f"- {verdict_text} {diagnosis_text}\n"
                "- 后续验证应保持代理模型、线性屈曲和非线性后屈曲结果的编号一致，再结合静水压试验或缩比件试验校核安全裕度。",
            ]
        )

    def _qualitative_text(self, value: Any) -> str:
        text = str(value or "").strip()
        if not text:
            return ""
        material_codes = sorted(self._material_codes(text))
        placeholders: Dict[str, str] = {}
        for index, code in enumerate(material_codes):
            placeholder = f"__MAT_CODE_{chr(65 + index)}__"
            placeholders[placeholder] = code
            text = re.sub(re.escape(code), placeholder, text, flags=re.IGNORECASE)

        text = re.sub(r"\b(?:CASE|TMP|CAND|C)\s*[_-]?\d+\b", "候选", text, flags=re.IGNORECASE)
        text = re.sub(
            r"[-+]?[0-9]+(?:\.[0-9]+)?\s*(?:MPa|mm|kg\s*/\s*m\^?2|kg/m²|kg/m2|%|‰|deg|°|LPF|GPa)",
            "对应工程量",
            text,
            flags=re.IGNORECASE,
        )
        text = re.sub(r"[-+]?[0-9]+(?:\.[0-9]+)?", "", text)
        text = re.sub(r"\s+", " ", text).strip()

        for placeholder, code in placeholders.items():
            text = text.replace(placeholder, code)
        return text

    def _layup_qualitative_description(self, layup: Any) -> str:
        text = str(layup or "")
        if not text:
            return "当前结构化数据未提供铺层表达式"
        if "90" in text:
            return "含外侧直角约束层的均衡正负角铺层"
        if "±" in text or "+/-" in text:
            return "均衡正负角铺层"
        return "结构化候选提供的复合材料铺层"

    def _build_llm_explanation_payload(self, summary: Dict[str, Any]) -> Dict[str, Any]:
        candidates = []
        for candidate in summary.get("screened_candidates", []):
            candidates.append(
                {
                    "source": candidate.get("source"),
                    "material": candidate.get("material"),
                    "layup_family": self._layup_qualitative_description(candidate.get("layup")),
                    "rationale": self._qualitative_text(candidate.get("rationale")),
                    "screening_summary": self._qualitative_text(candidate.get("screening_summary")),
                    "selection_reason": self._qualitative_text(candidate.get("selection_reason")),
                }
            )

        results = []
        for result in summary.get("results", []):
            results.append(
                {
                    "verdict": result.get("verdict"),
                    "failure_mode": result.get("failure_mode"),
                    "ultimate_pressure_basis": self._qualitative_text(result.get("ultimate_pressure_basis")),
                    "diagnosis_summary": self._qualitative_text(result.get("diagnosis_summary")),
                }
            )

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
                "load_case": "外部静水压力",
                "boundary_conditions": self._qualitative_text(summary.get("boundary_conditions")),
                "primary_objective": summary.get("primary_objective"),
            },
            "screened_candidates": candidates,
            "results": results,
            "aggregate": {"overall": overall},
        }

    def _numeric_tokens(self, text: str) -> List[float]:
        values: List[float] = []
        for token in re.findall(r"[-+]?[0-9]+(?:\.[0-9]+)?", text):
            try:
                values.append(float(token))
            except ValueError:
                continue
        return values

    def _engineering_numeric_tokens(self, text: str) -> List[float]:
        values: List[float] = []
        pattern = (
            r"([-+]?[0-9]+(?:\.[0-9]+)?)\s*"
            r"(?:MPa|mm|kg\s*/\s*m\^?2|kg/m²|kg/m2|%|‰|deg|°|LPF|GPa)"
        )
        for match in re.finditer(pattern, text, flags=re.IGNORECASE):
            try:
                values.append(float(match.group(1)))
            except ValueError:
                continue
        return values

    def _llm_text_uses_only_known_numbers(self, text: str, payload: Dict[str, Any]) -> bool:
        serialized_payload = json.dumps(payload, ensure_ascii=False, default=str)
        allowed_values = self._engineering_numeric_tokens(serialized_payload) + self._numeric_tokens(
            serialized_payload
        )
        if not allowed_values:
            return not self._engineering_numeric_tokens(text)
        for value in self._engineering_numeric_tokens(text):
            if not any(abs(value - allowed) <= max(1e-6, abs(allowed) * 1e-6) for allowed in allowed_values):
                return False
        return True

    def _material_codes(self, text: str) -> set[str]:
        codes = re.findall(r"\b(?:T|M)[0-9]+[A-Z0-9-]*\b", text, flags=re.IGNORECASE)
        return {code.upper() for code in codes}

    def _llm_text_uses_only_known_material_codes(self, text: str, payload: Dict[str, Any]) -> bool:
        known_codes = self._material_codes(json.dumps(payload, ensure_ascii=False, default=str))
        return self._material_codes(text).issubset(known_codes)

    def _validate_llm_engineering_text(self, text: str, payload: Dict[str, Any]) -> None:
        if not self._llm_text_uses_only_known_numbers(text, payload):
            raise ValueError("LLM 报告解释包含结构化数据之外的数值")
        if not self._llm_text_uses_only_known_material_codes(text, payload):
            raise ValueError("LLM 报告解释包含结构化数据之外的材料牌号")
        forbidden_structure_terms = ["加强筋", "加筋", "夹芯", "金属衬套"]
        if any(term in text for term in forbidden_structure_terms):
            raise ValueError("LLM 报告解释包含当前设计变量域之外的结构型式")

    def _deterministic_clean_llm_engineering_text(self, text: str, payload: Dict[str, Any]) -> str:
        known_codes = self._material_codes(json.dumps(payload, ensure_ascii=False, default=str))
        forbidden_structure_terms = ["加强筋", "加筋", "夹芯", "金属衬套"]
        cleaned_lines: List[str] = []
        measurement_pattern = (
            r"[-+]?[0-9]+(?:\.[0-9]+)?\s*"
            r"(?:MPa|mm|kg\s*/\s*m\^?2|kg/m²|kg/m2|%|‰|deg|°|LPF|GPa)"
        )
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
            line = re.sub(measurement_pattern, "结构化结果中的对应工程量", line, flags=re.IGNORECASE)
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
        )
        user_prompt = (
            f"允许保留的材料牌号：{', '.join(known_material_codes) if known_material_codes else '无'}\n\n"
            "请清理以下报告解释文本：\n"
            f"{text}"
        )
        return self.llm_backend.chat(
            system_prompt,
            user_prompt,
            max_tokens_override=min(max(int(self.llm_backend.max_tokens), 1800), 2400),
            json_mode=False,
        ).strip()

    def _render_llm_engineering_explanation(self, summary: Dict[str, Any]) -> str:
        if self.llm_backend is None:
            return ""
        payload = self._build_llm_explanation_payload(summary)
        system_prompt = (
            "你是复合材料外压圆柱耐压壳设计报告解释助手。"
            "只能基于用户提供的 JSON 定性结构化数据撰写中文工程解释。"
            "不得新增候选编号、数值、材料名、工况或有限元结论；不得改写 verdict、压力、面密度和排序。"
            "可以从复合材料圆柱壳常用制造评审角度讨论纤维缠绕、预浸带铺放、固化、圆度控制和无损检测，"
            "但不能把 JSON 中没有的设备、厂家、具体张力、固化温度、检验阈值或替代材料牌号写成事实。"
            "优化建议限定在当前候选变量域内，只讨论材料、铺层、厚度、缺陷质量控制、有限元和试验复核，"
            "不要引入加强筋、夹芯、金属衬套或其他未在输入中出现的结构型式。"
            "数值事实已经由报告模板输出，解释段禁止出现数字、角度、单位、阈值和候选编号，只做定性解释。"
            "输出 Markdown，只使用三级标题和短横线项目；不要输出表格、JSON、编号列表或代码块。"
        )
        user_prompt = (
            "请生成报告中的“工程解释与制造建议”段落，必须覆盖：制造工艺适配性、铺层/材料原因、缺陷与质量控制、"
            "有限元结果解读、后续验证建议。只做定性解释，不要复述 JSON 中的数字，不要给出新的数字、阈值、候选编号或替代材料牌号；"
            "如果结构化数据缺少某项，请明确说明当前结构化数据未提供。\n\n"
            f"结构化定性数据 JSON：\n{json.dumps(payload, ensure_ascii=False, indent=2, default=str)}"
        )
        answer = self.llm_backend.chat(
            system_prompt,
            user_prompt,
            max_tokens_override=min(max(int(self.llm_backend.max_tokens), 1800), 2600),
            json_mode=False,
        ).strip()
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
        return answer

    def _render_engineering_explanation(self, summary: Dict[str, Any]) -> str:
        self._last_llm_explanation_used = False
        if self.llm_backend is not None:
            try:
                llm_text = self._render_llm_engineering_explanation(summary)
                if llm_text:
                    self._last_llm_explanation_used = True
                    return llm_text
            except Exception as exc:
                self.emit(f"报告 LLM 工程解释生成失败，已使用确定性解释：{exc}")
        return self._render_deterministic_engineering_explanation(summary)

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
        lines = [
            "# CSDM_cph 耐压壳设计报告",
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
            "## 工程解释与制造建议",
            "",
            engineering_explanation,
            "",
            "## 代理模型初筛说明",
        ]
        if candidates:
            for candidate in candidates:
                official_candidate_id = (
                    results_by_session_id.get(str(candidate.get("candidate_id") or ""), {}).get("candidate_id")
                    or "-"
                )
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
                    f"- 极限压力：{result.get('ultimate_pressure_MPa')} MPa",
                    f"- 线性屈曲压力：{result.get('linear_buckling_pressure_MPa')} MPa",
                    f"- 极限压力依据：{result.get('ultimate_pressure_basis') or '-'}",
                    f"- Riks 最大 LPF：{result.get('riks_lpf_max')}",
                    f"- 缺陷幅值：{result.get('imperfection_amplitude_mm')} mm",
                    f"- 面密度：{result.get('weight_kg_per_m2')}",
                    f"- 失效模式：{result.get('failure_mode')}",
                    f"- 结论：{result.get('verdict')}",
                    f"- 工程说明：{result.get('diagnosis_summary')}",
                    f"- 模态云图数据：{result.get('visualization_json') or '-'}",
                ]
            )
        return "\n".join(lines)

    def _reportlab(self):
        from reportlab.lib.enums import TA_LEFT
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.cidfonts import UnicodeCIDFont
        from reportlab.pdfbase.ttfonts import TTFont
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

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
        }

    def _register_font(self) -> str:
        rl = self._reportlab()
        preferred_fonts = [
            ("CSDM_cph_SimSun", Path("C:/Windows/Fonts/simsun.ttc")),
            ("CSDM_cph_MSYH", Path("C:/Windows/Fonts/msyh.ttc")),
            ("CSDM_cph_SimHei", Path("C:/Windows/Fonts/simhei.ttf")),
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
            name="CSDM_cphBody",
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
                name="CSDM_cphTitle",
                parent=stylesheet["Title"],
                fontName=font_name,
                fontSize=18,
                leading=24,
                alignment=rl["TA_LEFT"],
                wordWrap="CJK",
                spaceAfter=12,
            ),
            "heading2": rl["ParagraphStyle"](
                name="CSDM_cphHeading2",
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
                name="CSDM_cphHeading3",
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
                name="CSDM_cphBullet",
                parent=body,
                leftIndent=14,
                firstLineIndent=0,
                bulletIndent=0,
                spaceAfter=3,
            ),
        }

    def _paragraph_text_for_pdf(self, text: str) -> str:
        normalized = text.replace("\t", "    ").strip()
        return escape(normalized)

    def _build_pdf_story(self, markdown_text: str, font_name: str) -> List[object]:
        rl = self._reportlab()
        styles = self._pdf_styles(font_name)
        story: List[object] = []

        for raw_line in markdown_text.splitlines():
            stripped = raw_line.strip()
            if not stripped:
                if story:
                    story.append(rl["Spacer"](1, 6))
                continue

            if stripped.startswith("# "):
                story.append(rl["Paragraph"](self._paragraph_text_for_pdf(stripped[2:]), styles["title"]))
                continue
            if stripped.startswith("## "):
                story.append(rl["Paragraph"](self._paragraph_text_for_pdf(stripped[3:]), styles["heading2"]))
                continue
            if stripped.startswith("### "):
                story.append(rl["Paragraph"](self._paragraph_text_for_pdf(stripped[4:]), styles["heading3"]))
                continue
            if stripped.startswith("- "):
                story.append(
                    rl["Paragraph"](
                        self._paragraph_text_for_pdf(stripped[2:]),
                        styles["bullet"],
                        bulletText="•",
                    )
                )
                continue

            story.append(rl["Paragraph"](self._paragraph_text_for_pdf(stripped), styles["body"]))

        if not story:
            story.append(rl["Paragraph"]("CSDM_cph 耐压壳设计报告内容为空。", styles["body"]))
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
            title="CSDM_cph 耐压壳设计报告",
            author="CSDM_cph",
        )
        document.build(self._build_pdf_story(markdown_text, font_name))

    def run(self, input_data: Dict) -> Dict:
        markdown_text = self._render_markdown(
            input_data["task"],
            input_data["results"],
            input_data.get("candidates", []),
        )
        markdown_path = RESULTS_DIR / "latest_report.md"
        pdf_path = RESULTS_DIR / "latest_report.pdf"
        write_text(markdown_path, markdown_text)
        pdf_generated = False
        try:
            self._write_pdf(markdown_text, pdf_path)
            pdf_generated = True
        except ModuleNotFoundError as exc:
            self.emit(f"PDF 依赖缺失，已跳过 PDF 导出：{exc}")
        self.emit("Markdown/PDF 报告已生成" if pdf_generated else "Markdown 报告已生成")
        return {
            "markdown_path": str(markdown_path),
            "pdf_path": str(pdf_path) if pdf_generated else None,
            "content": markdown_text,
            "llm_explanation_used": self._last_llm_explanation_used,
        }

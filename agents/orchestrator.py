"""主控智能体，支持整链路运行与分阶段调用。"""

from __future__ import annotations

from copy import deepcopy
from typing import Callable, Dict, List

from agents.base import BaseAgent
from agents.candidate_gen import CandidateGenAgent
from agents.fem_agent import FEMAgent
from agents.knowledge_agent import KnowledgeAgent
from agents.report_gen import ReportGenAgent
from agents.screener import ScreenerAgent
from core.config_loader import fixed_imperfection_ratio
from core.id_utils import reserve_candidate_ids, task_file_name
from core.fem_input_contract import attach_design_revision, validate_fem_input_or_raise
from core.io_utils import write_json
from core.paths import IO_DIR, TASKS_DIR
from core.task_contract import (
    describe_boundary_conditions,
    describe_load_conditions,
    effective_screen_top_k,
    requested_candidate_pool_size,
    requested_screen_top_k,
    summarize_task,
    task_payload_from_request,
)
from core.task_parser import TaskParser
from core.pressure_hull_profile import expand_layup_for_fem


class OrchestratorAgent(BaseAgent):
    agent_name = "ORCHESTRATOR"

    def __init__(self, progress_callback: Callable[[str, str], None] | None = None) -> None:
        super().__init__(progress_callback=progress_callback)
        self.task_parser = TaskParser()
        self.candidate_gen = CandidateGenAgent(progress_callback)
        self.screener = ScreenerAgent(progress_callback)
        self.fem_agent = FEMAgent(progress_callback)
        self.knowledge_agent = KnowledgeAgent(progress_callback)
        self.report_gen = ReportGenAgent(progress_callback)
        self.last_ranked_candidates: List[Dict] = []

    def _task_payload(self, task: Dict) -> Dict:
        return task_payload_from_request(task)

    def _task_event_context(self, task: Dict) -> Dict:
        return {
            "task_id": task.get("task_id"),
            "run_id": task.get("run_id"),
            "created_at": task.get("created_at"),
            "source": task.get("source"),
        }

    def _attach_task_context(self, task: Dict, candidate: Dict) -> Dict:
        task_payload = self._task_payload(task)
        enriched = dict(candidate)
        enriched.pop("task_id", None)
        if not str(enriched.get("display_name") or "").strip():
            enriched["display_name"] = str(enriched.get("candidate_id") or "").strip()
        if not str(enriched.get("persistent_candidate_id") or "").strip():
            enriched.pop("persistent_candidate_id", None)
        enriched["design_targets"] = dict(candidate.get("design_targets") or task_payload["design_targets"])
        enriched["load_conditions"] = dict(candidate.get("load_conditions") or task_payload["load_conditions"])
        enriched["boundary_conditions"] = dict(candidate.get("boundary_conditions") or task_payload["boundary_conditions"])
        enriched["material_system"] = dict(candidate.get("material_system") or task_payload["material_system"])
        return enriched

    def _promote_candidate_for_fem(self, task: Dict, candidate: Dict, formal_candidate_id: str | None = None) -> Dict:
        self._validate_analysis_conditions(candidate)
        enriched_candidate = self._attach_task_context(task, candidate)
        formal_candidate_id = formal_candidate_id or reserve_candidate_ids(1)[0]
        session_candidate_id = enriched_candidate.get("candidate_id")
        promoted = dict(enriched_candidate)
        source_layup = deepcopy(enriched_candidate.get("layup"))
        promoted["layup"] = expand_layup_for_fem(source_layup, promoted.get("geometry"))
        provenance = dict(promoted.get("provenance") or {})
        if source_layup is not None:
            provenance.setdefault("source_layup", source_layup)
        provenance["fem_input_layup"] = "explicit_physical_plies"
        promoted["provenance"] = provenance
        fem_readiness = dict(promoted.get("fem_readiness") or {})
        fem_readiness.update(
            {
                "status": "ready_for_cylindrical_shell_screening",
                "layup_expanded": True,
                "input_contract": "explicit_physical_plies",
            }
        )
        promoted["fem_readiness"] = fem_readiness
        promoted.pop("persistent_candidate_id", None)
        promoted["session_candidate_id"] = session_candidate_id
        promoted["candidate_id"] = formal_candidate_id
        promoted["display_name"] = formal_candidate_id
        for field in ("run_id", "task_id"):
            if task.get(field):
                promoted[field] = task[field]
        promoted = attach_design_revision(promoted)
        validate_fem_input_or_raise(promoted)
        return promoted

    @staticmethod
    def _validate_analysis_conditions(candidate: Dict) -> None:
        expected = fixed_imperfection_ratio()
        if (candidate.get("geometry") or {}).get("imperfection_ratio") != expected:
            raise ValueError(f"初始几何缺陷比必须为 {expected:g}；请按固定分析条件生成候选，不能直接改写已求解案例。")

    def prepare_candidates_for_fem(self, task: Dict, candidates: List[Dict]) -> List[Dict]:
        """为同一批有限元样本生成互不重复的正式编号。"""

        for candidate in candidates:
            self._validate_analysis_conditions(candidate)
        formal_candidate_ids = reserve_candidate_ids(len(candidates))
        return [
            self._promote_candidate_for_fem(task, candidate, formal_candidate_ids[index])
            for index, candidate in enumerate(candidates)
        ]

    def parse_instruction(self, text: str, overrides: Dict | None = None, *, run_id: str | None = None) -> Dict:
        task = self.task_parser.parse_instruction(text, overrides=overrides)
        if run_id:
            task["run_id"] = run_id

        # 写入任务台账
        task_path = TASKS_DIR / task_file_name(task["task_id"])
        write_json(task_path, task)

        summary = summarize_task(task)
        self.emit_event(
            "task_parsed",
            (
                f"任务已结构化：{summary['application']} | "
                f"{summary['load_conditions']} | "
                f"{summary['boundary_conditions']} | "
                f"{summary['candidate_pool']} | "
                f"{summary['top_k']}"
            ),
            {"task": task, "summary": summary, **self._task_event_context(task)},
        )
        return task

    def generate_candidates(self, task: Dict) -> List[Dict]:
        task_payload = self._task_payload(task)
        target_total = requested_candidate_pool_size(task)
        if target_total is None:
            raise ValueError("生成候选前需要用户确认候选方案数量。")
        self.emit_event(
            "candidate_generation_started",
            (
                f"开始生成候选方案：{describe_load_conditions(task_payload['load_conditions'])} / "
                f"{describe_boundary_conditions(task_payload['boundary_conditions'])} / "
                f"候选池目标 {target_total} 个"
            ),
            {**self._task_event_context(task), "target_total_candidates": target_total},
        )
        candidates = [self._attach_task_context(task, candidate) for candidate in self.candidate_gen.run(task)]
        generation_audit = dict(getattr(self.candidate_gen, "last_generation_audit", {}) or {})
        source_counter: Dict[str, int] = {}
        for candidate in candidates:
            source = str(candidate.get("source", "UNKNOWN"))
            source_counter[source] = source_counter.get(source, 0) + 1
        self.emit_event(
            "candidate_generation_completed",
            f"候选生成完成，目标 {target_total} 个，实际 {len(candidates)} 个："
            + " / ".join(f"{key}={value}" for key, value in sorted(source_counter.items())),
            {
                **self._task_event_context(task),
                "candidate_count": len(candidates),
                "target_total_candidates": target_total,
                "source_counter": source_counter,
                "generation_audit": generation_audit,
            },
        )
        return candidates

    def update_task_quantity(self, task: Dict, field: str, value: int) -> Dict:
        """将用户补充的流程数量写回同一任务，不分配新任务号。"""
        payload = self._task_payload(task)
        preferences = "candidate_generation_preferences" if field == "total_candidates" else "screening_preferences"
        payload[preferences] = {**payload[preferences], field: value}
        facts = dict(payload.get("user_input_facts") or {})
        facts["candidate_generation"] = {**facts.get("candidate_generation", {}), field: value}
        payload["user_input_facts"] = facts
        updated = {**task, "task": payload} if isinstance(task.get("task"), dict) else {**task, **payload}
        write_json(TASKS_DIR / task_file_name(updated["task_id"]), updated)
        return updated

    def screen_candidates(self, task: Dict, candidates: List[Dict]) -> List[Dict]:
        score_formula = self.screener.score_formula_text
        requested_top_k = requested_screen_top_k(task)
        if requested_top_k is None:
            raise ValueError("代理预筛前需要用户确认保留数量。")
        TaskParser.validate_quantity(requested_top_k, "top_k_candidates", len(candidates))
        effective_top_k = effective_screen_top_k(task, len(candidates))
        self.emit_event(
            "screening_started",
            (
                f"开始执行代理模型初筛，输入候选 {len(candidates)} 个，"
                f"目标保留 Top-{requested_top_k}，"
                f"当前最多保留 {effective_top_k} 个，"
                f"评分公式：{score_formula}"
            ),
            {
                **self._task_event_context(task),
                "input_count": len(candidates),
                "score_formula": score_formula,
                "requested_top_k_candidates": requested_top_k,
                "effective_top_k_candidates": effective_top_k,
            },
        )
        ranked_candidates = [self._attach_task_context(task, candidate) for candidate in self.screener.rank_candidates(task, candidates)]
        screened = [candidate for candidate in ranked_candidates if candidate.get("screening_selected")]
        self.last_ranked_candidates = ranked_candidates
        self.screener.emit(
            f"已完成 {len(candidates)} 个候选的批量评分，请求保留 Top-{effective_top_k}，实际返回 {len(screened)} 个。"
        )
        self.emit_event(
            "screening_completed",
            f"代理模型初筛完成，请求 Top-{requested_top_k}，实际输出 {len(screened)} 个。",
            {
                **self._task_event_context(task),
                "input_count": len(candidates),
                "output_count": len(screened),
                "score_formula": score_formula,
                "requested_top_k_candidates": requested_top_k,
                "effective_top_k_candidates": effective_top_k,
                "selected_candidates": screened,
                "ranked_candidates": ranked_candidates,
            },
        )
        return screened

    def prepare_candidate_for_fem(self, task: Dict, candidate: Dict) -> Dict:
        """生成正式有限元输入候选。"""

        return self._promote_candidate_for_fem(task, candidate)

    def evaluate_prepared_candidate(self, task: Dict, fem_candidate: Dict) -> Dict:
        """执行已经晋级为正式编号的有限元候选。"""

        self.emit_event(
            "fem_started",
            f"开始校核 {fem_candidate.get('session_candidate_id', fem_candidate.get('display_name', '候选样本'))} "
            f"-> {fem_candidate['candidate_id']}",
            {**self._task_event_context(task), "candidate": fem_candidate},
        )
        result = self.fem_agent.run(fem_candidate)
        for field in ("run_id", "task_id"):
            if fem_candidate.get(field):
                result[field] = fem_candidate[field]
        result["session_candidate_id"] = fem_candidate.get("session_candidate_id")
        result["display_name"] = fem_candidate.get("display_name")
        write_json(IO_DIR / f"result_{result['candidate_id']}.json", result)
        return result

    def persist_knowledge_records(self, task: Dict, designs: List[Dict], results: List[Dict]) -> List[Dict]:
        """把有限元结果回流到案例库和案例记忆。"""

        results_by_candidate_id: Dict[str, Dict] = {}
        for result in results:
            candidate_id = str(result.get("candidate_id") or "").strip()
            if candidate_id:
                if candidate_id in results_by_candidate_id:
                    raise ValueError(f"有限元结果包含重复求解编号：{candidate_id}")
                results_by_candidate_id[candidate_id] = result

        updates: List[Dict] = []
        for design in designs:
            design_candidate_id = str(design.get("candidate_id") or "").strip()
            design_session_id = str(design.get("session_candidate_id") or "").strip()
            result = results_by_candidate_id.get(design_candidate_id)
            if result:
                result_session_id = str(result.get("session_candidate_id") or "").strip()
                design_run_id = str(design.get("run_id") or task.get("run_id") or "").strip()
                result_run_id = str(result.get("run_id") or "").strip()
                if ((design_session_id and result_session_id and result_session_id != design_session_id)
                        or (design_run_id and result_run_id and result_run_id != design_run_id)):
                    result = None
            if not result:
                update = {
                    "status": "missing_result",
                    "candidate_id": design.get("candidate_id"),
                    "session_candidate_id": design.get("session_candidate_id"),
                    "error": "未找到匹配的有限元结果",
                }
                updates.append(update)
                self.emit_event("knowledge_update_failed", "知识回流缺少匹配有限元结果", update)
                continue
            try:
                solved_design = {**design, **deepcopy(result.get("solved_design") or {})}
                update = self.knowledge_agent.run({"task": task, "design": solved_design, "abaqus_results": result})
                update["candidate_id"] = design.get("candidate_id")
                update["session_candidate_id"] = design.get("session_candidate_id")
                updates.append(update)
                if update.get("status") == "not_stored_incomplete":
                    self.emit_event("knowledge_update_skipped", f"结果证据不完整，未入案例库：{update.get('reason')}", update)
                else:
                    self.emit_event("knowledge_update_completed", f"知识回流完成：{update.get('case_id')}", update)
            except Exception as exc:
                update = {
                    "status": "failed",
                    "candidate_id": design.get("candidate_id"),
                    "session_candidate_id": design.get("session_candidate_id"),
                    "error": str(exc),
                }
                updates.append(update)
                self.emit_event("knowledge_update_failed", f"知识回流失败：{exc}", update)
        return updates

    def evaluate_candidate(self, task: Dict, candidate: Dict, persist_knowledge: bool = True) -> Dict:
        fem_candidate = self.prepare_candidate_for_fem(task, candidate)
        result = self.evaluate_prepared_candidate(task, fem_candidate)
        if persist_knowledge:
            self.persist_knowledge_records(task, [fem_candidate], [result])
        return result

    def generate_report(
        self,
        task: Dict,
        results: List[Dict],
        candidates: List[Dict] | None = None,
        output_dir: str | None = None,
    ) -> Dict:
        self.emit_event(
            "report_started",
            "开始生成设计报告",
            {**self._task_event_context(task), "result_count": len(results)},
        )
        return self.report_gen.run(
            {
                "task": task,
                "results": results,
                "candidates": candidates or [],
                "output_dir": output_dir,
            }
        )

    def run(self, user_instruction: str, overrides: Dict | None = None) -> Dict:
        self.emit("正在解析用户需求")
        task = self.parse_instruction(user_instruction, overrides=overrides)
        candidates = self.generate_candidates(task)
        top_candidates = self.screen_candidates(task, candidates)

        fem_candidates = self.prepare_candidates_for_fem(task, top_candidates)
        results = [self.evaluate_prepared_candidate(task, candidate) for candidate in fem_candidates]
        knowledge_updates = self.persist_knowledge_records(task, fem_candidates, results)

        report = self.generate_report(task, results, self.last_ranked_candidates or candidates)
        return {
            "task": task,
            "candidates": candidates,
            "top_candidates": top_candidates,
            "fem_candidates": fem_candidates,
            "results": results,
            "knowledge_updates": knowledge_updates,
            "report": report,
        }

"""UI 无关的对话流程控制层。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

from agents.orchestrator import OrchestratorAgent
from core.task_contract import (
    describe_boundary_conditions,
    describe_load_conditions,
    effective_screen_top_k,
    requested_candidate_pool_size,
    requested_screen_top_k,
    task_payload_from_request,
)
from workflow.runtime import DesignWorkflowRuntime
from workflow.event_store import WorkflowEventStore


ConversationEventCallback = Optional[Callable[[str, str, Dict], None]]


def _source_counter(candidates: List[Dict]) -> Dict[str, int]:
    counter: Dict[str, int] = {}
    for candidate in candidates:
        source = str(candidate.get("source", "UNKNOWN"))
        counter[source] = counter.get(source, 0) + 1
    return counter


@dataclass
class ConversationState:
    instruction: str = ""
    workflow_run_id: str | None = None
    task: Dict | None = None
    candidates: List[Dict] = field(default_factory=list)
    screened_candidates: List[Dict] = field(default_factory=list)
    evaluated_candidates: List[Dict] = field(default_factory=list)
    results: List[Dict] = field(default_factory=list)
    knowledge_updates: List[Dict] = field(default_factory=list)
    report: Dict | None = None
    pending_confirmation: str | None = None
    stage: str = "idle"
    screen_skipped: bool = False


class ConversationFlowController:
    """把主流程组织成带关键确认节点的对话状态机。"""

    def __init__(
        self,
        orchestrator: OrchestratorAgent,
        event_callback: ConversationEventCallback = None,
        event_store: WorkflowEventStore | None = None,
    ) -> None:
        self.orchestrator = orchestrator
        self.event_callback = event_callback
        self.event_store = event_store

    def _emit(self, event_type: str, message: str, payload: Dict | None = None) -> None:
        if self.event_callback:
            self.event_callback(event_type, message, payload or {})

    def _target_counts(self, task: Dict | None, candidate_count: int) -> Dict[str, int]:
        return {
            "candidate_pool_target": requested_candidate_pool_size(task),
            "requested_top_k": requested_screen_top_k(task),
            "effective_top_k": effective_screen_top_k(task, candidate_count),
        }

    def _render_commentary(self, stage: str, payload: Dict) -> str:
        if stage == "task_summary":
            task = payload.get("task", {})
            task_payload = task_payload_from_request(task)
            target_total = requested_candidate_pool_size(task)
            top_k = requested_screen_top_k(task)
            return (
                f"我已经把你的需求整理成结构化任务了，当前按 {describe_load_conditions(task_payload.get('load_conditions', {}))} "
                f"和 {describe_boundary_conditions(task_payload.get('boundary_conditions', {}))} 来生成方案，候选池先按 {target_total} 个目标展开，后续初筛会保留 Top-{top_k}。"
            )
        if stage == "candidate_summary":
            return "我先按默认来源比例铺开初始方案池，再用代理模型做一轮便宜但有解释性的预筛选；来源拆分以有效候选统计为准。"
        if stage == "screening_summary":
            return "代理模型初筛已经把候选范围收紧了，接下来更值得把有限元预算用在当前排序靠前、解释更充分的耐压壳样本上。"
        if stage == "fem_summary":
            return "有限元结果已经回来，现在可以根据极限压力、失效模式和面密度表现来决定是否直接导出报告，或者继续迭代约束。"
        if stage == "report_summary":
            return "报告部分已经收尾完成，你现在可以直接查看最新导出的 Markdown 或 PDF。"
        if stage == "conversation_paused":
            return "我先把当前状态停在这里，后面的候选和结果都还保留着，你随时可以继续往下推。"
        return ""

    def _emit_commentary(self, stage: str, payload: Dict) -> None:
        commentary = self._render_commentary(stage, payload)
        if commentary:
            self._emit("assistant_commentary", commentary, {"stage": stage, **payload})

    def _emit_runtime_event(self, event_type: str, message: str, payload: Dict | None = None) -> None:
        record = payload or {}
        self._emit(
            "workflow_runtime_event",
            message,
            {
                "runtime_event_type": event_type,
                "runtime_agent": record.get("agent") or "WorkflowRuntime",
                "runtime_stage": record.get("stage") or "",
                "record": record,
            },
        )

    def _runtime(self) -> DesignWorkflowRuntime:
        return DesignWorkflowRuntime(
            orchestrator=self.orchestrator,
            event_store=self.event_store,
            event_callback=self._emit_runtime_event,
        )

    def start(self, instruction: str, overrides: Dict | None = None) -> ConversationState:
        state = ConversationState(instruction=instruction, stage="parsing")
        self._emit("conversation_started", "已接收设计需求，正在解析任务并生成初始候选。", {"instruction": instruction})

        workflow_state = self._runtime().start(instruction, overrides=overrides)
        task = workflow_state["task"]
        task_payload = task_payload_from_request(task)
        candidates = workflow_state.get("candidates", [])

        state.workflow_run_id = workflow_state["run_id"]
        state.task = task
        state.candidates = candidates
        state.stage = workflow_state.get("stage", "awaiting_screen_confirmation")
        state.pending_confirmation = workflow_state.get("pending_confirmation", "screen_candidates")

        source_counter = _source_counter(candidates)
        target_counts = self._target_counts(task, len(candidates))
        self._emit(
            "task_summary",
            (
                f"任务摘要：{task_payload['application']} | "
                f"{describe_load_conditions(task_payload['load_conditions'])} | "
                f"{describe_boundary_conditions(task_payload['boundary_conditions'])} | "
                f"候选池目标 {target_counts['candidate_pool_target']} 个 | "
                f"初筛保留 Top-{target_counts['requested_top_k']}"
            ),
            {"task": task},
        )
        self._emit_commentary("task_summary", {"task": task})
        self._emit(
            "candidate_summary",
            (
                f"初始候选目标 {target_counts['candidate_pool_target']} 个，实际生成 {len(candidates)} 个，来源拆分："
                + " / ".join(f"{key}={value}" for key, value in sorted(source_counter.items()))
            ),
            {
                "candidates": candidates,
                "source_counter": source_counter,
                **target_counts,
            },
        )
        self._emit_commentary(
            "candidate_summary",
            {
                "candidate_count": len(candidates),
                "source_counter": source_counter,
                **target_counts,
            },
        )
        screen_note = ""
        if target_counts["effective_top_k"] < target_counts["requested_top_k"]:
            screen_note = f" 当前只有 {len(candidates)} 个候选，因此最多保留 {target_counts['effective_top_k']} 个。"
        self._emit(
            "confirmation_requested",
            (
                f"是否进行代理模型初筛？系统将按 {self.orchestrator.screener.score_formula_text} 对候选排序，"
                f"目标保留 Top-{target_counts['requested_top_k']}。"
                f"{screen_note}"
            ),
            {
                "confirmation_id": "screen_candidates",
                "default": True,
                "score_formula": self.orchestrator.screener.score_formula_text,
                **target_counts,
            },
        )
        return state

    def continue_after_confirmation(self, state: ConversationState, approved: bool) -> ConversationState:
        if state.workflow_run_id:
            return self._continue_with_workflow_runtime(state, approved)
        if state.pending_confirmation == "screen_candidates":
            return self._handle_screen_confirmation(state, approved)
        if state.pending_confirmation == "fem_evaluation":
            return self._handle_fem_confirmation(state, approved)
        if state.pending_confirmation == "export_report":
            return self._handle_report_confirmation(state, approved)
        return state

    def _continue_with_workflow_runtime(self, state: ConversationState, approved: bool) -> ConversationState:
        if state.task is None:
            return state
        confirmation = state.pending_confirmation
        workflow_state = self._runtime().continue_after_confirmation(state.workflow_run_id, approved)
        state.workflow_run_id = workflow_state["run_id"]
        state.task = workflow_state.get("task", state.task)
        state.candidates = workflow_state.get("candidates", state.candidates)
        state.screened_candidates = workflow_state.get("screened_candidates", state.screened_candidates)
        state.evaluated_candidates = workflow_state.get("evaluated_candidates", state.evaluated_candidates)
        state.results = workflow_state.get("results", state.results)
        state.knowledge_updates = workflow_state.get("knowledge_updates", state.knowledge_updates)
        state.report = workflow_state.get("report", state.report)
        state.pending_confirmation = workflow_state.get("pending_confirmation")
        state.stage = workflow_state.get("stage", state.stage)
        state.screen_skipped = bool(workflow_state.get("screen_skipped", state.screen_skipped))

        if confirmation == "screen_candidates":
            return self._emit_runtime_screen_summary(state, approved)
        if confirmation == "fem_evaluation":
            return self._emit_runtime_fem_summary(state, approved)
        if confirmation == "export_report":
            return self._emit_runtime_report_summary(state, approved)
        return state

    def _emit_runtime_screen_summary(self, state: ConversationState, approved: bool) -> ConversationState:
        target_counts = self._target_counts(state.task, len(state.candidates))
        if approved:
            self._emit(
                "screening_summary",
                (
                    f"代理模型初筛已完成：{len(state.candidates)} -> {len(state.evaluated_candidates)}，"
                    f"请求 Top-{target_counts['requested_top_k']}。"
                ),
                {
                    "screened_candidates": state.evaluated_candidates,
                    **target_counts,
                },
            )
            self._emit_commentary(
                "screening_summary",
                {
                    "input_count": len(state.candidates),
                    "output_count": len(state.evaluated_candidates),
                    "selected_candidates": state.evaluated_candidates[:3],
                    **target_counts,
                },
            )
        else:
            self._emit(
                "screening_summary",
                f"已跳过代理模型初筛，将直接对全部 {len(state.candidates)} 个候选进入有限元校核。",
                {"screened_candidates": state.candidates, "screen_skipped": True, **target_counts},
            )
            self._emit_commentary(
                "screening_summary",
                {
                    "input_count": len(state.candidates),
                    "output_count": len(state.candidates),
                    "screen_skipped": True,
                    **target_counts,
                },
            )

        fem_targets = state.evaluated_candidates
        preview_reasons = [candidate.get("selection_reason") for candidate in fem_targets[:3] if candidate.get("selection_reason")]
        detail_suffix = f" 重点入选原因：{' | '.join(preview_reasons)}" if preview_reasons else ""
        self._emit(
            "confirmation_requested",
            f"是否进行有限元校核？当前待校核样本 {len(fem_targets)} 个。{detail_suffix}",
            {"confirmation_id": "fem_evaluation", "default": True, "candidate_count": len(fem_targets)},
        )
        return state

    def _emit_runtime_fem_summary(self, state: ConversationState, approved: bool) -> ConversationState:
        if not approved:
            self._emit(
                "conversation_paused",
                "已暂停在有限元校核前。当前候选和初筛结果已保留，可稍后继续。",
                {"stage": state.stage},
            )
            self._emit_commentary("conversation_paused", {"stage": state.stage})
            return state

        passed_count = sum(1 for result in state.results if result.get("verdict") == "通过")
        self._emit(
            "fem_summary",
            f"有限元校核完成：共 {len(state.results)} 个样本，其中通过 {passed_count} 个。",
            {"results": state.results, "passed_count": passed_count},
        )
        self._emit_commentary(
            "fem_summary",
            {
                "result_count": len(state.results),
                "passed_count": passed_count,
                "results": state.results[:3],
            },
        )
        self._emit(
            "confirmation_requested",
            "是否导出设计报告？报告将包含工况摘要、代理模型选择理由、有限元结果解读和工程建议。",
            {"confirmation_id": "export_report", "default": True},
        )
        return state

    def _emit_runtime_report_summary(self, state: ConversationState, approved: bool) -> ConversationState:
        if approved and state.report:
            self._emit(
                "report_summary",
                (
                    f"报告已导出：{state.report.get('markdown_path')} / "
                    f"{state.report.get('pdf_path')}"
                ),
                {"report": state.report},
            )
            self._emit_commentary("report_summary", {"report": state.report})
        else:
            self._emit("report_summary", "已跳过报告导出。", {"report": None})
            self._emit_commentary("report_summary", {"report": None, "skipped": True})
        return state

    def _handle_screen_confirmation(self, state: ConversationState, approved: bool) -> ConversationState:
        if state.task is None:
            return state
        target_counts = self._target_counts(state.task, len(state.candidates))

        if approved:
            screened_candidates = self.orchestrator.screen_candidates(state.task, state.candidates)
            state.screened_candidates = screened_candidates
            state.evaluated_candidates = screened_candidates
            self._emit(
                "screening_summary",
                (
                    f"代理模型初筛已完成：{len(state.candidates)} -> {len(screened_candidates)}，"
                    f"请求 Top-{target_counts['requested_top_k']}。"
                ),
                {
                    "screened_candidates": screened_candidates,
                    **target_counts,
                },
            )
            self._emit_commentary(
                "screening_summary",
                {
                    "input_count": len(state.candidates),
                    "output_count": len(screened_candidates),
                    "selected_candidates": screened_candidates[:3],
                    **target_counts,
                },
            )
        else:
            state.screen_skipped = True
            state.screened_candidates = []
            state.evaluated_candidates = list(state.candidates)
            self._emit(
                "screening_summary",
                f"已跳过代理模型初筛，将直接对全部 {len(state.candidates)} 个候选进入有限元校核。",
                {"screened_candidates": state.candidates, "screen_skipped": True, **target_counts},
            )
            self._emit_commentary(
                "screening_summary",
                {
                    "input_count": len(state.candidates),
                    "output_count": len(state.candidates),
                    "screen_skipped": True,
                    **target_counts,
                },
            )

        state.pending_confirmation = "fem_evaluation"
        state.stage = "awaiting_fem_confirmation"
        fem_targets = state.evaluated_candidates
        preview_reasons = [candidate.get("selection_reason") for candidate in fem_targets[:3] if candidate.get("selection_reason")]
        detail_suffix = f" 重点入选原因：{' | '.join(preview_reasons)}" if preview_reasons else ""
        self._emit(
            "confirmation_requested",
            f"是否进行有限元校核？当前待校核样本 {len(fem_targets)} 个。{detail_suffix}",
            {"confirmation_id": "fem_evaluation", "default": True, "candidate_count": len(fem_targets)},
        )
        return state

    def _handle_fem_confirmation(self, state: ConversationState, approved: bool) -> ConversationState:
        if state.task is None:
            return state

        if not approved:
            state.pending_confirmation = None
            state.stage = "paused_before_fem"
            self._emit(
                "conversation_paused",
                "已暂停在有限元校核前。当前候选和初筛结果已保留，可稍后继续。",
                {"stage": state.stage},
            )
            self._emit_commentary("conversation_paused", {"stage": state.stage})
            return state

        results = [self.orchestrator.evaluate_candidate(state.task, candidate) for candidate in state.evaluated_candidates]
        state.results = results
        passed_count = sum(1 for result in results if result.get("verdict") == "通过")
        state.pending_confirmation = "export_report"
        state.stage = "awaiting_report_confirmation"

        self._emit(
            "fem_summary",
            f"有限元校核完成：共 {len(results)} 个样本，其中通过 {passed_count} 个。",
            {"results": results, "passed_count": passed_count},
        )
        self._emit_commentary(
            "fem_summary",
            {
                "result_count": len(results),
                "passed_count": passed_count,
                "results": results[:3],
            },
        )
        self._emit(
            "confirmation_requested",
            "是否导出设计报告？报告将包含工况摘要、代理模型选择理由、有限元结果解读和工程建议。",
            {"confirmation_id": "export_report", "default": True},
        )
        return state

    def _handle_report_confirmation(self, state: ConversationState, approved: bool) -> ConversationState:
        if state.task is None:
            return state

        if approved:
            state.report = self.orchestrator.generate_report(state.task, state.results, state.evaluated_candidates)
            self._emit(
                "report_summary",
                (
                    f"报告已导出：{state.report.get('markdown_path')} / "
                    f"{state.report.get('pdf_path')}"
                ),
                {"report": state.report},
            )
            self._emit_commentary("report_summary", {"report": state.report})
        else:
            self._emit("report_summary", "已跳过报告导出。", {"report": None})
            self._emit_commentary("report_summary", {"report": None, "skipped": True})

        state.pending_confirmation = None
        state.stage = "completed"
        return state

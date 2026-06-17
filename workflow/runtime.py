"""LangGraph 多智能体设计工作流运行时。"""

from __future__ import annotations

import uuid
from typing import Any, Callable, Dict

from langgraph.graph import END, START, StateGraph

from agents.orchestrator import OrchestratorAgent
from workflow.agent_contracts import contract_by_node
from workflow.event_store import WorkflowEventStore
from workflow.events import WorkflowEvent
from workflow.simulation_queue import SimulationJobQueue
from workflow.state import DesignWorkflowState, initial_state, source_counter
from workflow.tool_registry import ToolRegistry, ToolSpec


WorkflowCallback = Callable[[str, str, Dict[str, Any]], None]


def new_run_id() -> str:
    return f"RUN_{uuid.uuid4().hex[:12].upper()}"


class DesignWorkflowRuntime:
    """面向耐压壳设计主流程的可恢复状态图运行时。"""

    def __init__(
        self,
        orchestrator: OrchestratorAgent | None = None,
        event_store: WorkflowEventStore | None = None,
        event_callback: WorkflowCallback | None = None,
    ) -> None:
        self.event_store = event_store or WorkflowEventStore()
        self.simulation_queue = SimulationJobQueue(self.event_store.db_path)
        self.event_callback = event_callback
        self._active_run_id: str | None = None
        self._active_stage = ""
        self._external_agent_callback = getattr(orchestrator, "progress_callback", None) if orchestrator is not None else None
        self.orchestrator = orchestrator or OrchestratorAgent(progress_callback=self._agent_event)
        self._bind_agent_event_callbacks()
        self.tools = self._build_tools()
        self.graph = self._build_graph()

    def _bind_agent_event_callbacks(self) -> None:
        """让运行时接管主智能体和子智能体事件，保证 GUI 与事件库可见完整轨迹。"""

        self.orchestrator.progress_callback = self._agent_event
        for attribute in ("candidate_gen", "screener", "fem_agent", "knowledge_agent", "report_gen"):
            agent = getattr(self.orchestrator, attribute, None)
            if agent is not None:
                agent.progress_callback = self._agent_event

    def _agent_event(self, sender: str, message: str, event: Dict[str, Any] | None = None) -> None:
        if not self._active_run_id:
            return
        payload = event if isinstance(event, dict) else {}
        event_type = str(payload.get("event_type") or "agent_info")
        self._emit_event(event_type, sender, message, payload.get("payload") if isinstance(payload.get("payload"), dict) else payload)
        if self._external_agent_callback:
            try:
                self._external_agent_callback(sender, message, event or {})
            except TypeError:
                self._external_agent_callback(sender, message)

    def _emit_event(self, event_type: str, agent: str, message: str, payload: Dict[str, Any] | None = None) -> None:
        if not self._active_run_id:
            return
        event = WorkflowEvent(
            run_id=self._active_run_id,
            event_type=event_type,
            agent=agent,
            message=message,
            stage=self._active_stage,
            payload=payload or {},
        )
        self.event_store.append_event(event)
        if self.event_callback:
            self.event_callback(event_type, message, event.to_record())

    def _build_tools(self) -> ToolRegistry:
        registry = ToolRegistry(event_sink=self._emit_event)
        contracts = contract_by_node()
        registry.register(
            ToolSpec(
                name="parse_task",
                agent=contracts["parse_task"].runtime_agent,
                description=contracts["parse_task"].responsibility,
                input_schema={"instruction": "str", "overrides": "dict"},
                output_schema={"task": "dict"},
                handler=lambda payload: {
                    "task": self.orchestrator.parse_instruction(
                        str(payload.get("instruction") or ""),
                        overrides=payload.get("overrides") or None,
                    )
                },
            )
        )
        registry.register(
            ToolSpec(
                name="generate_candidates",
                agent=contracts["generate_candidates"].runtime_agent,
                description=contracts["generate_candidates"].responsibility,
                input_schema={"task": "dict"},
                output_schema={"candidates": "list"},
                handler=lambda payload: {"candidates": self.orchestrator.generate_candidates(payload["task"])},
            )
        )
        registry.register(
            ToolSpec(
                name="screen_candidates",
                agent=contracts["screen_candidates"].runtime_agent,
                description=contracts["screen_candidates"].responsibility,
                input_schema={"task": "dict", "candidates": "list"},
                output_schema={"screened_candidates": "list", "ranked_candidates": "list"},
                handler=lambda payload: {
                    "screened_candidates": self.orchestrator.screen_candidates(
                        payload["task"],
                        payload["candidates"],
                    ),
                    "ranked_candidates": getattr(self.orchestrator, "last_ranked_candidates", []),
                },
            )
        )
        registry.register(
            ToolSpec(
                name="evaluate_candidates",
                agent=contracts["evaluate_candidates"].runtime_agent,
                description=contracts["evaluate_candidates"].responsibility,
                input_schema={"task": "dict", "candidates": "list"},
                output_schema={"results": "list", "fem_designs": "list"},
                handler=self._evaluate_candidates_with_queue,
            )
        )
        registry.register(
            ToolSpec(
                name="persist_knowledge",
                agent=contracts["persist_knowledge"].runtime_agent,
                description=contracts["persist_knowledge"].responsibility,
                input_schema={"task": "dict", "fem_designs": "list", "results": "list"},
                output_schema={"knowledge_updates": "list"},
                handler=lambda payload: {
                    "knowledge_updates": self.orchestrator.persist_knowledge_records(
                        payload["task"],
                        payload.get("fem_designs") or [],
                        payload.get("results") or [],
                    )
                },
            )
        )
        registry.register(
            ToolSpec(
                name="generate_report",
                agent=contracts["generate_report"].runtime_agent,
                description=contracts["generate_report"].responsibility,
                input_schema={"task": "dict", "results": "list", "candidates": "list"},
                output_schema={"report": "dict"},
                handler=lambda payload: {
                    "report": self.orchestrator.generate_report(
                        payload["task"],
                        payload["results"],
                        payload.get("candidates") or [],
                    )
                },
            )
        )
        return registry

    def _evaluate_candidates_with_queue(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        if not self._active_run_id:
            raise RuntimeError("仿真队列缺少当前工作流运行编号")
        task = payload["task"]
        candidates = list(payload.get("candidates") or [])
        results = []
        fem_designs = []
        for candidate in candidates:
            fem_candidate = self.orchestrator.prepare_candidate_for_fem(task, candidate)
            fem_designs.append(fem_candidate)
            job_id = self.simulation_queue.enqueue(self._active_run_id, fem_candidate)
            self._emit_event(
                "simulation_job_queued",
                "FEM_AGENT",
                f"有限元作业入队：{job_id}",
                {
                    "job_id": job_id,
                    "source": "SimulationQueue",
                    "candidate_id": fem_candidate.get("candidate_id"),
                    "session_candidate_id": fem_candidate.get("session_candidate_id"),
                },
            )
            self.simulation_queue.mark_running(job_id)
            self._emit_event(
                "simulation_job_started",
                "FEM_AGENT",
                f"有限元作业开始：{job_id}",
                {
                    "job_id": job_id,
                    "source": "SimulationQueue",
                    "candidate_id": fem_candidate.get("candidate_id"),
                    "session_candidate_id": fem_candidate.get("session_candidate_id"),
                },
            )
            try:
                result = self.orchestrator.evaluate_prepared_candidate(task, fem_candidate)
            except Exception as exc:
                self.simulation_queue.mark_failed(job_id, str(exc))
                self._emit_event(
                    "simulation_job_failed",
                    "FEM_AGENT",
                    f"有限元作业失败：{job_id}：{exc}",
                    {"job_id": job_id, "source": "SimulationQueue", "error": str(exc)},
                )
                raise
            self.simulation_queue.mark_success(job_id, result)
            self._emit_event(
                "simulation_job_completed",
                "FEM_AGENT",
                f"有限元作业完成：{job_id}",
                {
                    "job_id": job_id,
                    "source": "SimulationQueue",
                    "candidate_id": result.get("candidate_id"),
                    "session_candidate_id": result.get("session_candidate_id"),
                    "status": result.get("status"),
                    "verdict": result.get("verdict"),
                    "ultimate_pressure_MPa": result.get("ultimate_pressure_MPa"),
                },
            )
            results.append(result)
        return {"results": results, "fem_designs": fem_designs}

    def _node(self, node_name: str, state: DesignWorkflowState, fn) -> Dict[str, Any]:
        run_id = state["run_id"]
        self._active_run_id = run_id
        self._active_stage = node_name
        self._emit_event("node_started", node_name, f"节点开始：{node_name}")
        try:
            update = fn(state)
            merged = {**state, **update}
            self.event_store.save_snapshot(run_id, merged)
            self._emit_event("node_completed", node_name, f"节点完成：{node_name}", {"stage": merged.get("stage")})
            return update
        except Exception as exc:
            failed_state = {**state, "stage": f"{node_name}_failed", "error": str(exc)}
            self.event_store.save_snapshot(run_id, failed_state)
            self._emit_event("node_failed", node_name, f"节点失败：{node_name}：{exc}", {"error": str(exc)})
            raise
        finally:
            self._active_stage = ""

    def _build_graph(self):
        graph = StateGraph(DesignWorkflowState)
        graph.add_node("route", lambda state: {})
        graph.add_node("parse_task", lambda state: self._node("parse_task", state, self._parse_task))
        graph.add_node("generate_candidates", lambda state: self._node("generate_candidates", state, self._generate_candidates))
        graph.add_node("wait_screen", lambda state: self._node("wait_screen", state, self._wait_screen))
        graph.add_node("screen_candidates", lambda state: self._node("screen_candidates", state, self._screen_candidates))
        graph.add_node("skip_screen", lambda state: self._node("skip_screen", state, self._skip_screen))
        graph.add_node("wait_fem", lambda state: self._node("wait_fem", state, self._wait_fem))
        graph.add_node("evaluate_candidates", lambda state: self._node("evaluate_candidates", state, self._evaluate_candidates))
        graph.add_node("persist_knowledge", lambda state: self._node("persist_knowledge", state, self._persist_knowledge))
        graph.add_node("pause_before_fem", lambda state: self._node("pause_before_fem", state, self._pause_before_fem))
        graph.add_node("wait_report", lambda state: self._node("wait_report", state, self._wait_report))
        graph.add_node("generate_report", lambda state: self._node("generate_report", state, self._generate_report))
        graph.add_node("skip_report", lambda state: self._node("skip_report", state, self._skip_report))

        graph.add_edge(START, "route")
        graph.add_conditional_edges(
            "route",
            self._route_entry,
            {
                "parse_task": "parse_task",
                "generate_candidates": "generate_candidates",
                "wait_screen": "wait_screen",
                "screen_candidates": "screen_candidates",
                "skip_screen": "skip_screen",
                "wait_fem": "wait_fem",
                "evaluate_candidates": "evaluate_candidates",
                "persist_knowledge": "persist_knowledge",
                "pause_before_fem": "pause_before_fem",
                "wait_report": "wait_report",
                "generate_report": "generate_report",
                "skip_report": "skip_report",
                "end": END,
            },
        )
        graph.add_edge("parse_task", "generate_candidates")
        graph.add_conditional_edges(
            "generate_candidates",
            self._route_screen,
            {
                "wait_screen": "wait_screen",
                "screen_candidates": "screen_candidates",
                "skip_screen": "skip_screen",
            },
        )
        graph.add_edge("wait_screen", END)
        graph.add_edge("screen_candidates", "wait_fem")
        graph.add_edge("skip_screen", "wait_fem")
        graph.add_conditional_edges(
            "wait_fem",
            self._route_fem,
            {
                "wait_fem": END,
                "evaluate_candidates": "evaluate_candidates",
                "pause_before_fem": "pause_before_fem",
            },
        )
        graph.add_edge("pause_before_fem", END)
        graph.add_edge("evaluate_candidates", "persist_knowledge")
        graph.add_conditional_edges("persist_knowledge", self._route_report, {
            "wait_report": "wait_report",
            "generate_report": "generate_report",
            "skip_report": "skip_report",
        })
        graph.add_conditional_edges(
            "wait_report",
            self._route_report,
            {
                "wait_report": END,
                "generate_report": "generate_report",
                "skip_report": "skip_report",
            },
        )
        graph.add_edge("generate_report", END)
        graph.add_edge("skip_report", END)
        return graph.compile()

    def _parse_task(self, state: DesignWorkflowState) -> Dict[str, Any]:
        result = self.tools.run(
            "parse_task",
            {"instruction": state.get("instruction", ""), "overrides": state.get("overrides") or {}},
        )
        return {"task": result["task"], "stage": "task_parsed", "error": None}

    def _generate_candidates(self, state: DesignWorkflowState) -> Dict[str, Any]:
        result = self.tools.run("generate_candidates", {"task": state["task"]})
        candidates = result["candidates"]
        return {
            "candidates": candidates,
            "source_counter": source_counter(candidates),
            "stage": "candidates_generated",
            "error": None,
        }

    def _wait_screen(self, state: DesignWorkflowState) -> Dict[str, Any]:
        return {"stage": "awaiting_screen_confirmation", "pending_confirmation": "screen_candidates"}

    def _screen_candidates(self, state: DesignWorkflowState) -> Dict[str, Any]:
        result = self.tools.run(
            "screen_candidates",
            {"task": state["task"], "candidates": state.get("candidates", [])},
        )
        screened = result["screened_candidates"]
        ranked = result.get("ranked_candidates") or state.get("candidates", [])
        return {
            "candidates": ranked,
            "screened_candidates": screened,
            "evaluated_candidates": screened,
            "stage": "screened",
            "pending_confirmation": None,
            "error": None,
        }

    def _skip_screen(self, state: DesignWorkflowState) -> Dict[str, Any]:
        candidates = list(state.get("candidates", []))
        return {
            "screen_skipped": True,
            "screened_candidates": [],
            "evaluated_candidates": candidates,
            "stage": "screen_skipped",
            "pending_confirmation": None,
        }

    def _wait_fem(self, state: DesignWorkflowState) -> Dict[str, Any]:
        if state.get("fem_approved") is None:
            return {"stage": "awaiting_fem_confirmation", "pending_confirmation": "fem_evaluation"}
        return {"pending_confirmation": None}

    def _evaluate_candidates(self, state: DesignWorkflowState) -> Dict[str, Any]:
        result = self.tools.run(
            "evaluate_candidates",
            {"task": state["task"], "candidates": state.get("evaluated_candidates", [])},
        )
        return {
            "results": result["results"],
            "fem_designs": result.get("fem_designs", []),
            "stage": "fem_evaluated",
            "pending_confirmation": None,
            "error": None,
        }

    def _persist_knowledge(self, state: DesignWorkflowState) -> Dict[str, Any]:
        result = self.tools.run(
            "persist_knowledge",
            {
                "task": state["task"],
                "fem_designs": state.get("fem_designs", []),
                "results": state.get("results", []),
            },
        )
        return {
            "knowledge_updates": result["knowledge_updates"],
            "stage": "knowledge_updated",
            "error": None,
        }

    def _pause_before_fem(self, state: DesignWorkflowState) -> Dict[str, Any]:
        return {"stage": "paused_before_fem", "pending_confirmation": None}

    def _wait_report(self, state: DesignWorkflowState) -> Dict[str, Any]:
        return {"stage": "awaiting_report_confirmation", "pending_confirmation": "export_report"}

    def _generate_report(self, state: DesignWorkflowState) -> Dict[str, Any]:
        result = self.tools.run(
            "generate_report",
            {
                "task": state["task"],
                "results": state.get("results", []),
                "candidates": state.get("evaluated_candidates", []),
            },
        )
        return {"report": result["report"], "stage": "completed", "pending_confirmation": None, "error": None}

    def _skip_report(self, state: DesignWorkflowState) -> Dict[str, Any]:
        return {"stage": "completed", "pending_confirmation": None}

    def _route_screen(self, state: DesignWorkflowState) -> str:
        approved = state.get("screen_approved")
        if approved is None:
            return "wait_screen"
        return "screen_candidates" if approved else "skip_screen"

    def _route_fem(self, state: DesignWorkflowState) -> str:
        approved = state.get("fem_approved")
        if approved is None:
            return "wait_fem"
        return "evaluate_candidates" if approved else "pause_before_fem"

    def _route_report(self, state: DesignWorkflowState) -> str:
        approved = state.get("report_approved")
        if approved is None:
            return "wait_report"
        return "generate_report" if approved else "skip_report"

    def _route_entry(self, state: DesignWorkflowState) -> str:
        if state.get("stage") == "completed":
            return "end"
        if not state.get("task"):
            return "parse_task"
        if not state.get("candidates"):
            return "generate_candidates"
        if state.get("pending_confirmation") == "screen_candidates" or state.get("stage") in {
            "candidates_generated",
            "awaiting_screen_confirmation",
        }:
            return self._route_screen(state)
        if state.get("pending_confirmation") == "fem_evaluation" or state.get("stage") in {
            "screened",
            "screen_skipped",
            "awaiting_fem_confirmation",
        }:
            return self._route_fem(state)
        if state.get("pending_confirmation") == "export_report" or state.get("stage") in {
            "fem_evaluated",
            "knowledge_updated",
            "awaiting_report_confirmation",
        }:
            if state.get("stage") == "fem_evaluated" and not state.get("knowledge_updates"):
                return "persist_knowledge"
            return self._route_report(state)
        return "end"

    def _invoke(self, state: DesignWorkflowState) -> DesignWorkflowState:
        self._active_run_id = state["run_id"]
        try:
            result = self.graph.invoke(state)
            self.event_store.save_snapshot(result["run_id"], result)
            return result
        finally:
            self._active_run_id = None
            self._active_stage = ""

    def start(self, instruction: str, overrides: Dict[str, Any] | None = None, run_id: str | None = None) -> DesignWorkflowState:
        """启动工作流并运行到第一个人工确认点。"""

        workflow_run_id = run_id or new_run_id()
        state = initial_state(workflow_run_id, instruction, overrides)
        self.event_store.create_run(workflow_run_id, instruction)
        self.event_store.save_snapshot(workflow_run_id, state)
        self._active_run_id = workflow_run_id
        self._emit_event("workflow_started", "WorkflowRuntime", "设计工作流已启动", {"instruction": instruction})
        return self._invoke(state)

    def resume(self, run_id: str) -> DesignWorkflowState:
        """读取最近一次持久化快照。"""

        return self.event_store.load_snapshot(run_id)

    def continue_after_confirmation(self, state_or_run_id: DesignWorkflowState | str, approved: bool) -> DesignWorkflowState:
        """根据当前等待的人工确认继续推进工作流。"""

        state = self.resume(state_or_run_id) if isinstance(state_or_run_id, str) else dict(state_or_run_id)
        confirmation = state.get("pending_confirmation")
        if confirmation == "screen_candidates":
            state["screen_approved"] = bool(approved)
        elif confirmation == "fem_evaluation":
            state["fem_approved"] = bool(approved)
        elif confirmation == "export_report":
            state["report_approved"] = bool(approved)
        else:
            raise ValueError("当前工作流没有等待人工确认")
        state["pending_confirmation"] = None
        self._active_run_id = state["run_id"]
        self._emit_event(
            "human_confirmation",
            "HumanOperator",
            f"人工确认：{confirmation}={approved}",
            {"confirmation_id": confirmation, "approved": bool(approved)},
        )
        return self._invoke(state)

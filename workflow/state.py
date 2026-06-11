"""设计工作流状态契约。"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, TypedDict


class DesignWorkflowState(TypedDict, total=False):
    """LangGraph 节点之间传递的可序列化状态。"""

    run_id: str
    instruction: str
    overrides: Dict[str, Any]
    task: Dict[str, Any]
    candidates: List[Dict[str, Any]]
    screened_candidates: List[Dict[str, Any]]
    evaluated_candidates: List[Dict[str, Any]]
    fem_designs: List[Dict[str, Any]]
    results: List[Dict[str, Any]]
    knowledge_updates: List[Dict[str, Any]]
    report: Dict[str, Any]
    stage: str
    pending_confirmation: Optional[str]
    screen_skipped: bool
    screen_approved: Optional[bool]
    fem_approved: Optional[bool]
    report_approved: Optional[bool]
    source_counter: Dict[str, int]
    error: Optional[str]


def initial_state(run_id: str, instruction: str, overrides: Dict[str, Any] | None = None) -> DesignWorkflowState:
    """生成新的工作流初始状态。"""

    return {
        "run_id": run_id,
        "instruction": instruction,
        "overrides": dict(overrides or {}),
        "candidates": [],
        "screened_candidates": [],
        "evaluated_candidates": [],
        "fem_designs": [],
        "results": [],
        "knowledge_updates": [],
        "stage": "created",
        "pending_confirmation": None,
        "screen_skipped": False,
        "screen_approved": None,
        "fem_approved": None,
        "report_approved": None,
        "source_counter": {},
        "error": None,
    }


def source_counter(candidates: List[Dict[str, Any]]) -> Dict[str, int]:
    """统计候选来源。"""

    counter: Dict[str, int] = {}
    for candidate in candidates:
        source = str(candidate.get("source", "UNKNOWN"))
        counter[source] = counter.get(source, 0) + 1
    return counter

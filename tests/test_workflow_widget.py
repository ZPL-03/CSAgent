import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication

from gui.workflow_widget import WorkflowWidget
from workflow.event_store import WorkflowEventStore
from workflow.events import WorkflowEvent
from workflow.simulation_queue import SimulationJobQueue


def _app() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_workflow_widget_renders_runtime_events(tmp_path) -> None:
    app = _app()
    store = WorkflowEventStore(tmp_path / "workflow.sqlite3")
    store.create_run("RUN_TEST", "生成 2 个候选，初筛保留 1 个候选")
    store.save_snapshot(
        "RUN_TEST",
        {
            "run_id": "RUN_TEST",
            "instruction": "生成 2 个候选，初筛保留 1 个候选",
            "stage": "awaiting_screen_confirmation",
            "pending_confirmation": "screen_candidates",
            "task": {
                "task_id": "TASK_1",
                "application": "复合材料外压圆柱耐压壳",
                "load_conditions": {"external_pressure_MPa": 30.0},
                "design_targets": {"ultimate_pressure_min_MPa": 35.0},
            },
            "candidates": [
                {"candidate_id": "TMP_1", "source": "DOE"},
                {"candidate_id": "TMP_2", "source": "LLM"},
            ],
            "screened_candidates": [{"candidate_id": "TMP_1", "source": "DOE"}],
            "results": [{"candidate_id": "C1", "verdict": "通过"}],
            "report": {"markdown_path": str(tmp_path / "latest_report.md")},
            "source_counter": {"DOE": 1, "LLM": 1},
            "error": None,
        },
    )
    store.append_event(
        WorkflowEvent(
            run_id="RUN_TEST",
            event_type="node_completed",
            agent="parse_task",
            message="节点完成：parse_task",
            stage="parse_task",
        )
    )
    store.append_event(
        WorkflowEvent(
            run_id="RUN_TEST",
            event_type="tool_completed",
            agent="RequirementAgent",
            message="工具 parse_task 调用完成",
            stage="parse_task",
        )
    )
    store.append_event(
        WorkflowEvent(
            run_id="RUN_TEST",
            event_type="llm_call_trace",
            agent="CandidateGenAgent",
            message="LLM 调用完成：使用 fallback / fallback-model，后端尝试 2 次",
            stage="generate_candidates",
            payload={
                "context": {"purpose": "candidate_generation", "desired_count": 6},
                "selected_backend": "fallback",
                "selected_model": "fallback-model",
                "fallback_used": True,
                "trace": [
                    {"backend": "primary", "model": "primary-model", "status": "failed"},
                    {"backend": "fallback", "model": "fallback-model", "status": "success"},
                ],
            },
        )
    )
    queue = SimulationJobQueue(tmp_path / "workflow.sqlite3")
    job_id = queue.enqueue("RUN_TEST", {"candidate_id": "TMP_1"})
    queue.mark_running(job_id)
    queue.mark_success(job_id, {"candidate_id": "C1", "ultimate_pressure_MPa": 45.0, "verdict": "通过"})
    failed_job_id = queue.enqueue("RUN_TEST", {"candidate_id": "TMP_2"})
    queue.mark_failed(failed_job_id, "Abaqus 输入文件缺少厚度字段")

    widget = WorkflowWidget(event_store=store, simulation_queue=queue)
    try:
        widget.refresh("RUN_TEST", "awaiting_screen_confirmation", "screen_candidates")
        html = widget.browser.toHtml()

        assert "智能体流程" in html
        assert "RUN_TEST" in html
        assert "任务解析" in html
        assert "完成" in html
        assert "screen_candidates" in html
        assert "工具 parse_task 调用完成" in html
        assert "有限元队列" in html
        assert "运行摘要" in html
        assert "状态图" in html
        assert "诊断" in html
        assert "任务契约" in html
        assert "候选池" in html
        assert "DOE=1" in html
        assert "LLM=1" in html
        assert "latest_report.md" in html
        assert "TMP_1" in html
        assert "TMP_2" in html
        assert "C1" in html
        assert "45.0" in html
        assert "Abaqus 输入文件缺少厚度字段" in html
        assert "LLM 已使用回退后端" in html
        assert "LLM 后端" in html
        assert "candidate_generation" in html
        assert "primary-model" in html
        assert "fallback-model" in html
    finally:
        widget.close()
        app.processEvents()


def test_workflow_widget_renders_manual_llm_health_check(monkeypatch) -> None:
    app = _app()

    def fake_probe(timeout_seconds=12):
        return [
            {
                "role": "primary",
                "name": "domain_finetuned_primary",
                "model": "csllm",
                "base_url_configured": True,
                "api_key_configured": True,
                "available_for_call": True,
                "health_status": "failed",
                "health_message": "调用失败",
                "latency_ms": 12.3,
                "error": "connection refused",
            },
            {
                "role": "fallback",
                "name": "configured_fallback",
                "model": "deepseek-v4-pro",
                "base_url_configured": True,
                "api_key_configured": True,
                "available_for_call": True,
                "health_status": "success",
                "health_message": "可用",
                "latency_ms": 8.1,
                "error": "",
            },
        ]

    monkeypatch.setattr("gui.workflow_widget.probe_llm_backends", fake_probe)
    widget = WorkflowWidget()
    try:
        widget._run_llm_health_check()
        html = widget.browser.toHtml()

        assert "实时检测" in html
        assert "domain_finetuned_primary" in html
        assert "deepseek-v4-pro" in html
        assert "调用失败" in html
        assert "connection refused" in html
        assert "可用" in html
        assert "8.1 ms" in html
    finally:
        widget.close()
        app.processEvents()

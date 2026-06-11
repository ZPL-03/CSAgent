"""PyQt6 主界面。"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from PyQt6 import sip
from PyQt6.QtCore import QObject, QThread, QUrl, pyqtSignal
from PyQt6.QtGui import QCloseEvent, QDesktopServices
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QTabWidget,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from agents.orchestrator import OrchestratorAgent
from core.conversation_flow import ConversationFlowController, ConversationState
from core.paths import RESULTS_DIR, ensure_project_dirs
from core.task_contract import (
    describe_boundary_conditions,
    describe_load_conditions,
    effective_screen_top_k,
    requested_candidate_pool_size,
    requested_screen_top_k,
    task_payload_from_request,
)
from gui.abaqus_widget import AbaqusWidget
from gui.candidate_widget import CandidateWidget
from gui.chat_widget import ChatWidget
from gui.knowledge_widget import KnowledgeWidget
from gui.log_widget import LogWidget
from gui.report_widget import ReportWidget
from gui.result_trace_widget import ResultTraceWidget
from gui.task_config_widget import TaskConfigWidget
from gui.workflow_widget import WorkflowWidget
from workflow.event_store import WorkflowEventStore


@dataclass
class PipelineSession:
    task: dict | None = None
    workflow_run_id: str | None = None
    instruction: str = ""
    candidates: list[dict] = field(default_factory=list)
    screened_candidates: list[dict] = field(default_factory=list)
    evaluated_candidates: list[dict] = field(default_factory=list)
    results_by_session_id: dict[str, dict] = field(default_factory=dict)
    knowledge_updates: list[dict] = field(default_factory=list)
    report: dict | None = None
    pending_confirmation: str | None = None
    stage: str = "idle"
    screen_skipped: bool = False

    @property
    def current_candidates(self) -> list[dict]:
        if self.evaluated_candidates:
            return self.evaluated_candidates
        if self.screened_candidates:
            return self.screened_candidates
        return self.candidates

    def to_flow_state(self) -> ConversationState:
        return ConversationState(
            instruction=self.instruction,
            workflow_run_id=self.workflow_run_id,
            task=self.task,
            candidates=list(self.candidates),
            screened_candidates=list(self.screened_candidates),
            evaluated_candidates=list(self.evaluated_candidates),
            results=list(self.results_by_session_id.values()),
            knowledge_updates=list(self.knowledge_updates),
            report=self.report,
            pending_confirmation=self.pending_confirmation,
            stage=self.stage,
            screen_skipped=self.screen_skipped,
        )

    @classmethod
    def from_flow_state(cls, state: ConversationState) -> "PipelineSession":
        results_by_session_id: dict[str, dict] = {}
        for result in state.results:
            session_candidate_id = result.get("session_candidate_id", result.get("candidate_id"))
            if session_candidate_id:
                results_by_session_id[str(session_candidate_id)] = result
        return cls(
            task=state.task,
            workflow_run_id=state.workflow_run_id,
            instruction=state.instruction,
            candidates=list(state.candidates),
            screened_candidates=list(state.screened_candidates),
            evaluated_candidates=list(state.evaluated_candidates),
            results_by_session_id=results_by_session_id,
            knowledge_updates=list(state.knowledge_updates),
            report=state.report,
            pending_confirmation=state.pending_confirmation,
            stage=state.stage,
            screen_skipped=state.screen_skipped,
        )


class PipelineWorker(QObject):
    message = pyqtSignal(str, str, object)
    finished = pyqtSignal(str, dict)
    failed = pyqtSignal(str)

    def __init__(self, action: str, payload: dict) -> None:
        super().__init__()
        self.action = action
        self.payload = payload

    def run(self) -> None:
        try:
            orchestrator = OrchestratorAgent(progress_callback=self._emit_agent)
            controller = ConversationFlowController(orchestrator, event_callback=self._emit_flow)

            if self.action == "conversation_start":
                state = controller.start(self.payload["instruction"], overrides=self.payload.get("overrides"))
                self.finished.emit(self.action, {"state": state})
                return

            if self.action == "conversation_continue":
                state = self.payload["state"]
                updated = controller.continue_after_confirmation(state, bool(self.payload["approved"]))
                self.finished.emit(self.action, {"state": updated})
                return

            if self.action == "generate":
                instruction = self.payload["instruction"]
                task = orchestrator.parse_instruction(instruction, overrides=self.payload.get("overrides"))
                candidates = orchestrator.generate_candidates(task)
                self.finished.emit(self.action, {"task": task, "candidates": candidates})
                return

            if self.action == "screen":
                task = self.payload["task"]
                candidates = self.payload["candidates"]
                screened = orchestrator.screen_candidates(task, candidates)
                self.finished.emit(self.action, {"screened_candidates": screened})
                return

            if self.action == "evaluate":
                task = self.payload["task"]
                candidates = self.payload["candidates"]
                fem_designs = []
                results = []
                for candidate in candidates:
                    fem_candidate = orchestrator.prepare_candidate_for_fem(task, candidate)
                    fem_designs.append(fem_candidate)
                    results.append(orchestrator.evaluate_prepared_candidate(task, fem_candidate))
                knowledge_updates = orchestrator.persist_knowledge_records(task, fem_designs, results)
                self.finished.emit(
                    self.action,
                    {
                        "results": results,
                        "candidates": candidates,
                        "fem_designs": fem_designs,
                        "knowledge_updates": knowledge_updates,
                    },
                )
                return

            if self.action == "report":
                task = self.payload["task"]
                results = self.payload["results"]
                candidates = self.payload.get("candidates", [])
                report = orchestrator.generate_report(task, results, candidates)
                self.finished.emit(self.action, {"report": report})
                return

            raise RuntimeError(f"未知动作: {self.action}")
        except Exception as exc:
            self.failed.emit(str(exc))

    def _emit_agent(self, sender: str, message: str, event: dict | None = None) -> None:
        self.message.emit(sender, message, event or {})

    def _emit_flow(self, event_type: str, message: str, payload: dict | None = None) -> None:
        sender_name = "ASSISTANT" if event_type == "assistant_commentary" else "FLOW"
        self.message.emit(
            sender_name,
            message,
            {
                "agent": sender_name,
                "event_type": event_type,
                "message": message,
                "payload": payload or {},
            },
        )


class MainWindow(QMainWindow):
    """CSDM_cph 对话主导交互界面。"""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("CSDM_cph - 复合材料耐压壳智能设计系统")
        self.resize(1680, 980)
        self.session = PipelineSession()
        self.worker_thread: QThread | None = None
        self.worker: PipelineWorker | None = None
        self.workflow_event_store = WorkflowEventStore()

        self.chat_widget = ChatWidget()
        self.task_browser = QTextBrowser()
        self.task_browser.setHtml(self._initial_task_html())
        self.workflow_browser = QTextBrowser()
        self.workflow_browser.setHtml(self._workflow_html())
        self.status_label = QLabel("状态：等待输入设计需求")
        self.status_label.setWordWrap(True)
        self.status_label.setObjectName("statusLabel")

        self.input_line = QLineEdit()
        self.input_line.setPlaceholderText(
            "例如：请为复合材料外压圆柱耐压壳设计方案，外压 30 MPa，极限压力不低于 35 MPa，生成 12 个候选，初筛保留 5 个候选"
        )

        self.generate_button = QPushButton("开始对话设计")
        self.confirm_yes_button = QPushButton("确认继续")
        self.confirm_no_button = QPushButton("跳过/暂停")

        self.example_button = QPushButton("载入示例需求")
        self.refresh_button = QPushButton("刷新知识库")
        self.open_report_button = QPushButton("打开最新报告")
        self.run_selector = QComboBox()
        self.run_selector.setMinimumHeight(42)
        self.refresh_runs_button = QPushButton("刷新运行记录")
        self.restore_run_button = QPushButton("载入运行快照")

        self.screen_button = QPushButton("手动：代理初筛")
        self.evaluate_selected_button = QPushButton("手动：校核所选样本")
        self.evaluate_all_button = QPushButton("手动：校核当前候选")
        self.report_button = QPushButton("手动：导出报告")
        self.reset_button = QPushButton("重置会话")

        self.stage_card = QLabel("阶段：idle")
        self.candidate_card = QLabel("候选：0")
        self.pending_card = QLabel("待校核：0")
        self.pass_card = QLabel("通过：0")

        self.candidate_widget = CandidateWidget()
        self.abaqus_widget = AbaqusWidget()
        self.knowledge_widget = KnowledgeWidget()
        self.report_widget = ReportWidget()
        self.result_trace_widget = ResultTraceWidget()
        self.log_widget = LogWidget()
        self.task_config_widget = TaskConfigWidget()
        self.workflow_widget = WorkflowWidget(event_store=self.workflow_event_store)

        self.tabs = QTabWidget()
        self.tabs.addTab(self.task_config_widget, "任务配置")
        self.tabs.addTab(self.workflow_widget, "智能体流程")
        self.tabs.addTab(self.candidate_widget, "候选方案")
        self.tabs.addTab(self.abaqus_widget, "ABAQUS结果")
        self.tabs.addTab(self.result_trace_widget, "结果追踪")
        self.tabs.addTab(self.report_widget, "报告预览")
        self.tabs.addTab(self.knowledge_widget, "知识库")
        self.tabs.addTab(self.log_widget, "日志")

        self._build_layout()
        self._apply_styles()
        self._connect_signals()
        self._update_button_states()
        self._update_overview_cards()
        self._refresh_run_selector()
        self.knowledge_widget.refresh(load_evidence=False)

    def _build_layout(self) -> None:
        primary_header = QLabel("主流程")
        primary_header.setObjectName("sectionTitle")
        primary_button_layout = QGridLayout()
        primary_button_layout.setHorizontalSpacing(10)
        primary_button_layout.setVerticalSpacing(10)
        primary_button_layout.addWidget(self.generate_button, 0, 0)
        primary_button_layout.addWidget(self.confirm_yes_button, 0, 1)
        primary_button_layout.addWidget(self.confirm_no_button, 0, 2)

        utility_header = QLabel("辅助入口")
        utility_header.setObjectName("sectionTitle")
        utility_button_layout = QGridLayout()
        utility_button_layout.setHorizontalSpacing(10)
        utility_button_layout.setVerticalSpacing(10)
        utility_button_layout.addWidget(self.example_button, 0, 0)
        utility_button_layout.addWidget(self.refresh_button, 0, 1)
        utility_button_layout.addWidget(self.open_report_button, 0, 2)
        utility_button_layout.addWidget(self.run_selector, 1, 0, 1, 3)
        utility_button_layout.addWidget(self.refresh_runs_button, 2, 0)
        utility_button_layout.addWidget(self.restore_run_button, 2, 1, 1, 2)

        stats_header = QLabel("当前会话")
        stats_header.setObjectName("sectionTitle")
        stats_layout = QGridLayout()
        stats_layout.setHorizontalSpacing(10)
        stats_layout.setVerticalSpacing(10)
        stats_layout.addWidget(self.stage_card, 0, 0)
        stats_layout.addWidget(self.candidate_card, 0, 1)
        stats_layout.addWidget(self.pending_card, 1, 0)
        stats_layout.addWidget(self.pass_card, 1, 1)

        manual_header = QLabel("人工操作")
        manual_header.setObjectName("sectionTitle")
        manual_button_layout = QGridLayout()
        manual_button_layout.setHorizontalSpacing(10)
        manual_button_layout.setVerticalSpacing(10)
        manual_button_layout.addWidget(self.screen_button, 0, 0)
        manual_button_layout.addWidget(self.evaluate_selected_button, 0, 1)
        manual_button_layout.addWidget(self.evaluate_all_button, 0, 2)
        manual_button_layout.addWidget(self.report_button, 1, 0)
        manual_button_layout.addWidget(self.reset_button, 1, 1, 1, 2)

        left_layout = QVBoxLayout()
        left_layout.setSpacing(10)
        left_layout.addWidget(self.task_browser, 2)
        left_layout.addWidget(self.workflow_browser, 2)
        left_layout.addWidget(self.chat_widget, 6)
        left_layout.addWidget(self.status_label)
        left_layout.addWidget(self.input_line)
        left_layout.addWidget(primary_header)
        left_layout.addLayout(primary_button_layout)
        left_layout.addWidget(utility_header)
        left_layout.addLayout(utility_button_layout)
        left_layout.addWidget(stats_header)
        left_layout.addLayout(stats_layout)
        left_layout.addWidget(manual_header)
        left_layout.addLayout(manual_button_layout)

        right_layout = QVBoxLayout()
        right_layout.addWidget(self.tabs)

        main_layout = QHBoxLayout()
        main_layout.setSpacing(12)
        left_container = QWidget()
        right_container = QWidget()
        left_container.setLayout(left_layout)
        right_container.setLayout(right_layout)
        main_layout.addWidget(left_container, 2)
        main_layout.addWidget(right_container, 3)

        root = QWidget()
        root.setLayout(main_layout)
        self.setCentralWidget(root)

    def _decorate_button(self, button: QPushButton, background: str, border: str, color: str = "#1f2937") -> None:
        button.setMinimumHeight(42)
        button.setStyleSheet(
            f"""
            QPushButton {{
                background: {background};
                border: 1px solid {border};
                color: {color};
                border-radius: 10px;
                padding: 8px 14px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background: #eef4fb;
            }}
            QPushButton:disabled {{
                background: #f4f6f8;
                color: #9aa6b6;
                border: 1px solid #d9e0e8;
            }}
            """
        )

    def _apply_styles(self) -> None:
        self.setStyleSheet(
            """
            QMainWindow, QWidget {
                background: #f3f6fb;
                color: #1f2937;
            }
            QTextBrowser, QTableWidget, QLineEdit, QComboBox {
                background: white;
                border: 1px solid #d8e1ee;
                border-radius: 10px;
            }
            QLineEdit, QComboBox {
                padding: 10px 12px;
                font-size: 15px;
            }
            QLabel#sectionTitle {
                font-size: 13px;
                font-weight: 700;
                color: #31435c;
                padding: 4px 2px 0 2px;
            }
            QLabel#statusLabel {
                background: #eaf1fb;
                border: 1px solid #cfdbef;
                border-radius: 10px;
                padding: 10px 12px;
            }
            """
        )
        for card in [self.stage_card, self.candidate_card, self.pending_card, self.pass_card]:
            card.setStyleSheet(
                "background:#ffffff;border:1px solid #d8e1ee;border-radius:10px;padding:12px 14px;font-weight:600;"
            )
        self._decorate_button(self.generate_button, "#dbeafe", "#93c5fd", "#1e3a8a")
        self._decorate_button(self.confirm_yes_button, "#dcfce7", "#86efac", "#166534")
        self._decorate_button(self.confirm_no_button, "#fef3c7", "#fcd34d", "#92400e")
        self._decorate_button(self.example_button, "#ffffff", "#cfd8e6")
        self._decorate_button(self.refresh_button, "#ffffff", "#cfd8e6")
        self._decorate_button(self.open_report_button, "#ffffff", "#cfd8e6")
        self._decorate_button(self.refresh_runs_button, "#ffffff", "#cfd8e6")
        self._decorate_button(self.restore_run_button, "#eef2ff", "#c7d2fe", "#3730a3")
        self._decorate_button(self.screen_button, "#ffffff", "#cfd8e6")
        self._decorate_button(self.evaluate_selected_button, "#ffffff", "#cfd8e6")
        self._decorate_button(self.evaluate_all_button, "#ffffff", "#cfd8e6")
        self._decorate_button(self.report_button, "#ffffff", "#cfd8e6")
        self._decorate_button(self.reset_button, "#fff1f2", "#fecdd3", "#9f1239")

    def _connect_signals(self) -> None:
        self.generate_button.clicked.connect(self._start_conversation)
        self.input_line.returnPressed.connect(self._start_conversation)
        self.confirm_yes_button.clicked.connect(lambda: self._respond_confirmation(True))
        self.confirm_no_button.clicked.connect(lambda: self._respond_confirmation(False))
        self.example_button.clicked.connect(self._load_example_prompt)
        self.refresh_button.clicked.connect(self._refresh_knowledge_view)
        self.open_report_button.clicked.connect(self._open_latest_report)
        self.refresh_runs_button.clicked.connect(self._refresh_run_selector)
        self.restore_run_button.clicked.connect(self._restore_selected_run)
        self.run_selector.currentIndexChanged.connect(lambda: self._update_button_states())

        self.screen_button.clicked.connect(self._start_screen)
        self.evaluate_selected_button.clicked.connect(self._start_evaluate_selected)
        self.evaluate_all_button.clicked.connect(self._start_evaluate_all)
        self.report_button.clicked.connect(self._start_report)
        self.reset_button.clicked.connect(self._reset_session)

    def _set_busy(self, busy: bool, status_text: str) -> None:
        self.status_label.setText(f"状态：{status_text}")
        self.generate_button.setEnabled(not busy)
        self.input_line.setEnabled(not busy)
        self.run_selector.setEnabled(not busy)
        self.confirm_yes_button.setEnabled(not busy and self.session.pending_confirmation is not None)
        self.confirm_no_button.setEnabled(not busy and self.session.pending_confirmation is not None)
        for button in [
            self.example_button,
            self.refresh_button,
            self.open_report_button,
            self.refresh_runs_button,
            self.restore_run_button,
            self.screen_button,
            self.evaluate_selected_button,
            self.evaluate_all_button,
            self.report_button,
            self.reset_button,
        ]:
            button.setEnabled(not busy)
        if not busy:
            self._update_button_states()

    def _update_button_states(self) -> None:
        has_candidates = bool(self.session.candidates)
        has_results = bool(self.session.results_by_session_id)
        has_pending_current = bool(self._pending_candidates(self.session.current_candidates)) if has_candidates else False

        self.confirm_yes_button.setEnabled(self.session.pending_confirmation is not None)
        self.confirm_no_button.setEnabled(self.session.pending_confirmation is not None)
        self.screen_button.setEnabled(has_candidates and self.session.pending_confirmation is None)
        self.evaluate_selected_button.setEnabled(has_pending_current and self.session.pending_confirmation is None)
        self.evaluate_all_button.setEnabled(has_pending_current and self.session.pending_confirmation is None)
        self.report_button.setEnabled(has_results and self.session.pending_confirmation is None)
        self.reset_button.setEnabled(True)
        self.example_button.setEnabled(self.session.pending_confirmation is None)
        self.refresh_button.setEnabled(True)
        self.open_report_button.setEnabled((RESULTS_DIR / "latest_report.md").exists() or (RESULTS_DIR / "latest_report.pdf").exists())
        self.refresh_runs_button.setEnabled(True)
        self.restore_run_button.setEnabled(bool(self.run_selector.currentData()))
        self._update_overview_cards()

    def _update_overview_cards(self) -> None:
        generated_count = len(self.session.candidates)
        pending_count = len(self._pending_candidates(self.session.current_candidates)) if self.session.current_candidates else 0
        passed_count = sum(1 for result in self.session.results_by_session_id.values() if result.get("verdict") == "通过")
        candidate_pool_target = requested_candidate_pool_size(self.session.task) if self.session.task else 0
        requested_top_k = requested_screen_top_k(self.session.task) if self.session.task else 0
        self.stage_card.setText(f"阶段：{self.session.stage or 'idle'}")
        self.candidate_card.setText(f"候选池：{generated_count} / 目标 {candidate_pool_target}" if self.session.task else "候选池：0")
        self.pending_card.setText(
            f"待校核：{pending_count} / 初筛目标 {requested_top_k}" if self.session.task else "待校核：0"
        )
        self.pass_card.setText(f"通过：{passed_count}")

    def _run_action(self, action: str, payload: dict, status_text: str) -> None:
        self._set_busy(True, status_text)
        self.worker_thread = QThread(self)
        self.worker = PipelineWorker(action, payload)
        self.worker.moveToThread(self.worker_thread)
        self.worker_thread.started.connect(self.worker.run)
        self.worker.message.connect(self._handle_message)
        self.worker.finished.connect(self._handle_finished)
        self.worker.failed.connect(self._handle_failed)
        self.worker.finished.connect(self.worker_thread.quit)
        self.worker.failed.connect(self.worker_thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker.failed.connect(self.worker.deleteLater)
        self.worker_thread.finished.connect(self.worker_thread.deleteLater)
        self.worker_thread.finished.connect(self._clear_worker_refs)
        self.worker_thread.finished.connect(lambda: self._set_busy(False, "等待下一步操作"))
        self.worker_thread.start()

    def _clear_worker_refs(self) -> None:
        self.worker = None
        self.worker_thread = None

    def _run_selector_label(self, run: dict) -> str:
        updated_at = str(run.get("updated_at") or "-")
        stage = str(run.get("stage") or run.get("status") or "-")
        run_id = str(run.get("run_id") or "-")
        instruction = " ".join(str(run.get("instruction") or "").split())
        if len(instruction) > 42:
            instruction = instruction[:42].rstrip() + "..."
        return f"{updated_at} | {stage} | {run_id} | {instruction}"

    def _refresh_run_selector(self) -> None:
        current_run_id = self.run_selector.currentData()
        self.run_selector.blockSignals(True)
        self.run_selector.clear()
        runs = self.workflow_event_store.list_runs(limit=20)
        if not runs:
            self.run_selector.addItem("暂无可恢复运行", "")
        else:
            for run in runs:
                self.run_selector.addItem(self._run_selector_label(run), run.get("run_id") or "")
            if current_run_id:
                index = self.run_selector.findData(current_run_id)
                if index >= 0:
                    self.run_selector.setCurrentIndex(index)
        self.run_selector.blockSignals(False)
        self._update_button_states()

    def _session_from_workflow_state(self, state: dict) -> PipelineSession:
        results_by_session_id: dict[str, dict] = {}
        for result in state.get("results") or []:
            if not isinstance(result, dict):
                continue
            key = result.get("session_candidate_id") or result.get("candidate_id")
            if key:
                results_by_session_id[str(key)] = result
        return PipelineSession(
            task=state.get("task"),
            workflow_run_id=state.get("run_id"),
            instruction=str(state.get("instruction") or ""),
            candidates=list(state.get("candidates") or []),
            screened_candidates=list(state.get("screened_candidates") or []),
            evaluated_candidates=list(state.get("evaluated_candidates") or []),
            results_by_session_id=results_by_session_id,
            knowledge_updates=list(state.get("knowledge_updates") or []),
            report=state.get("report") if isinstance(state.get("report"), dict) else None,
            pending_confirmation=state.get("pending_confirmation"),
            stage=str(state.get("stage") or "idle"),
            screen_skipped=bool(state.get("screen_skipped")),
        )

    def _restore_selected_run(self) -> None:
        run_id = str(self.run_selector.currentData() or "").strip()
        if not run_id:
            self.status_label.setText("状态：没有可载入的运行快照")
            return
        try:
            snapshot = self.workflow_event_store.load_snapshot(run_id)
        except Exception as exc:
            self.status_label.setText(f"状态：运行快照载入失败：{exc}")
            self.log_widget.append_log("SYSTEM", f"运行快照载入失败：{run_id} | {exc}")
            return

        self.chat_widget.clear()
        self.log_widget.clear()
        self.session = self._session_from_workflow_state(snapshot)
        self.input_line.setText(self.session.instruction)
        self._apply_session(self.session)
        self.tabs.setCurrentWidget(self.workflow_widget)
        self.chat_widget.add_message(
            "SYSTEM",
            f"已载入运行快照：{run_id}，当前阶段：{self.session.stage}",
        )
        self.log_widget.append_log("SYSTEM", f"已载入运行快照：{run_id}")
        self.status_label.setText(f"状态：已载入运行快照 {run_id}")
        self._update_button_states()

    def _apply_session(self, session: PipelineSession) -> None:
        self.session = session
        self.task_browser.setHtml(self._task_summary_html())
        self.task_config_widget.update_task(self.session.task)
        self.candidate_widget.update_candidates(self.session.current_candidates, self.session.results_by_session_id)
        self.abaqus_widget.update_results(list(self.session.results_by_session_id.values()))
        self.result_trace_widget.update_trace(
            self.session.current_candidates,
            self.session.results_by_session_id,
            self.session.knowledge_updates,
            self.session.report,
        )
        self.report_widget.update_report(self.session.report)
        self.workflow_widget.refresh(
            self.session.workflow_run_id,
            self.session.stage,
            self.session.pending_confirmation,
        )
        self.knowledge_widget.refresh(self.session.task)
        self._update_overview_cards()

    def _refresh_design_views(self) -> None:
        self.task_browser.setHtml(self._task_summary_html())
        self.task_config_widget.update_task(self.session.task)
        self.candidate_widget.update_candidates(self.session.current_candidates, self.session.results_by_session_id)
        self.abaqus_widget.update_results(list(self.session.results_by_session_id.values()))
        self.result_trace_widget.update_trace(
            self.session.current_candidates,
            self.session.results_by_session_id,
            self.session.knowledge_updates,
            self.session.report,
        )
        self.report_widget.update_report(self.session.report)
        self.workflow_widget.refresh(
            self.session.workflow_run_id,
            self.session.stage,
            self.session.pending_confirmation,
        )
        self.knowledge_widget.refresh(self.session.task)
        self._update_overview_cards()

    def _start_conversation(self) -> None:
        instruction = self.input_line.text().strip()
        if not instruction:
            return
        self.session = PipelineSession(instruction=instruction)
        self.chat_widget.add_message("USER", instruction)
        self.tabs.setCurrentWidget(self.candidate_widget)
        self._run_action(
            "conversation_start",
            {"instruction": instruction},
            "正在生成候选方案并准备对话流程",
        )

    def _load_example_prompt(self) -> None:
        self.input_line.setText(
            "请为复合材料外压圆柱耐压壳设计方案，外压 30 MPa，极限压力不低于 35 MPa，生成 12 个候选，初筛保留 5 个候选"
        )
        self.input_line.setFocus()

    def _refresh_knowledge_view(self) -> None:
        self.knowledge_widget.refresh(self.session.task)
        self.status_label.setText("状态：知识库视图已刷新")

    def _open_latest_report(self) -> None:
        self.report_widget.refresh_latest()
        for path in [RESULTS_DIR / "latest_report.pdf", RESULTS_DIR / "latest_report.md"]:
            if path.exists():
                QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))
                self.chat_widget.add_message("SYSTEM", f"已尝试打开报告：{path}")
                return
        self.chat_widget.add_message("SYSTEM", "当前还没有可打开的报告文件。")

    def _respond_confirmation(self, approved: bool) -> None:
        if self.session.pending_confirmation is None:
            return
        label = "继续" if approved else "跳过/暂停"
        self.chat_widget.add_message("USER", label)
        self._run_action(
            "conversation_continue",
            {"state": self.session.to_flow_state(), "approved": approved},
            "正在推进对话流程",
        )

    def _pending_candidates(self, candidates: list[dict]) -> list[dict]:
        evaluated = set(self.session.results_by_session_id.keys())
        return [candidate for candidate in candidates if candidate.get("candidate_id") not in evaluated]

    def _report_candidate_set(self) -> list[dict]:
        evaluated = set(self.session.results_by_session_id.keys())
        return [
            candidate
            for candidate in self.session.current_candidates
            if str(candidate.get("candidate_id")) in evaluated
        ]

    def _ordered_report_results(self) -> list[dict]:
        ordered_results: list[dict] = []
        used_keys: set[str] = set()
        for candidate in self.session.current_candidates:
            candidate_id = str(candidate.get("candidate_id") or "")
            if candidate_id in self.session.results_by_session_id:
                ordered_results.append(self.session.results_by_session_id[candidate_id])
                used_keys.add(candidate_id)
        for key, result in self.session.results_by_session_id.items():
            if key not in used_keys:
                ordered_results.append(result)
        return ordered_results

    def _start_screen(self) -> None:
        if not self.session.task or not self.session.candidates:
            return
        self.tabs.setCurrentWidget(self.candidate_widget)
        self._run_action(
            "screen",
            {"task": self.session.task, "candidates": self.session.candidates},
            "正在执行代理模型初筛",
        )

    def _start_evaluate_selected(self) -> None:
        if not self.session.task or not self.session.current_candidates:
            return
        selected = self._pending_candidates(self.candidate_widget.selected_candidates())
        if not selected:
            self.chat_widget.add_message("SYSTEM", "所选候选样本均已完成 ABAQUS 校核，无需重复提交。")
            return
        self.tabs.setCurrentWidget(self.abaqus_widget)
        self._run_action(
            "evaluate",
            {"task": self.session.task, "candidates": selected},
            f"正在校核所选 {len(selected)} 个样本",
        )

    def _start_evaluate_all(self) -> None:
        if not self.session.task or not self.session.current_candidates:
            return
        pending = self._pending_candidates(self.session.current_candidates)
        if not pending:
            self.chat_widget.add_message("SYSTEM", "当前候选样本都已完成 ABAQUS 校核，无需重复提交。")
            return
        self.tabs.setCurrentWidget(self.abaqus_widget)
        self._run_action(
            "evaluate",
            {"task": self.session.task, "candidates": pending},
            f"正在校核全部 {len(pending)} 个当前候选",
        )

    def _start_report(self) -> None:
        if not self.session.task or not self.session.results_by_session_id:
            return
        report_candidates = self._report_candidate_set()
        ordered_results = self._ordered_report_results()
        if not ordered_results:
            return
        self.tabs.setCurrentWidget(self.report_widget)
        self._run_action(
            "report",
            {
                "task": self.session.task,
                "results": ordered_results,
                "candidates": report_candidates,
            },
            "正在生成报告",
        )

    def _reset_session(self) -> None:
        self.session = PipelineSession()
        self.chat_widget.clear()
        self.log_widget.clear()
        self.task_browser.setHtml(self._initial_task_html())
        self.workflow_browser.setHtml(self._workflow_html())
        self.candidate_widget.update_candidates([])
        self.abaqus_widget.update_results([])
        self.result_trace_widget.update_trace([])
        self.candidate_widget.reset_view()
        self.abaqus_widget.reset_view()
        self.result_trace_widget.reset_view()
        self.report_widget.reset_view()
        self.task_config_widget.reset_view()
        self.workflow_widget.reset_view()
        self.knowledge_widget.refresh(load_evidence=False)
        self.status_label.setText("状态：会话已重置")
        self.input_line.clear()
        self._update_overview_cards()
        self._update_button_states()

    def _handle_message(self, sender: str, message: str, event: object) -> None:
        event_payload = event if isinstance(event, dict) else {}
        event_type = str(event_payload.get("event_type", "info"))
        payload = event_payload.get("payload")
        if not isinstance(payload, dict):
            payload = {}
        if sender == "FLOW":
            sender_label = "SYSTEM"
        elif sender == "ASSISTANT":
            sender_label = "助手"
        else:
            sender_label = sender
        self.chat_widget.add_message(sender_label, message)
        self.log_widget.append_log(sender_label, f"[{event_type}] {message}")

        if sender == "FLOW" and event_type == "task_summary":
            task = payload.get("task")
            if isinstance(task, dict):
                self.session.task = task
                self._refresh_design_views()

        elif sender == "FLOW" and event_type == "candidate_summary":
            candidates = payload.get("candidates")
            if isinstance(candidates, list):
                self.session.candidates = candidates
                self.session.screened_candidates = []
                self.session.evaluated_candidates = []
                self.session.results_by_session_id = {}
                self.session.knowledge_updates = []
                self.session.report = None
                self.session.stage = "awaiting_screen_confirmation"
                self.session.pending_confirmation = "screen_candidates"
                self._refresh_design_views()
            self.tabs.setCurrentWidget(self.candidate_widget)

        elif sender == "FLOW" and event_type == "screening_summary":
            screened_candidates = payload.get("screened_candidates")
            if isinstance(screened_candidates, list):
                self.session.screened_candidates = screened_candidates
                self.session.evaluated_candidates = screened_candidates
                self.session.stage = "awaiting_fem_confirmation"
                self.session.pending_confirmation = "fem_evaluation"
                self._refresh_design_views()
            self.tabs.setCurrentWidget(self.candidate_widget)

        elif sender == "FLOW" and event_type == "fem_summary":
            results = payload.get("results")
            if isinstance(results, list):
                for result in results:
                    if not isinstance(result, dict):
                        continue
                    session_candidate_id = result.get("session_candidate_id", result.get("candidate_id"))
                    if session_candidate_id:
                        self.session.results_by_session_id[str(session_candidate_id)] = result
                updates = payload.get("knowledge_updates")
                if isinstance(updates, list):
                    self.session.knowledge_updates = updates
                self.session.stage = "awaiting_report_confirmation"
                self.session.pending_confirmation = "export_report"
                self._refresh_design_views()
            self.tabs.setCurrentWidget(self.abaqus_widget)

        elif sender == "FLOW" and event_type == "report_summary":
            report = payload.get("report")
            if isinstance(report, dict):
                self.session.report = report
            self.session.stage = "completed"
            self.session.pending_confirmation = None
            self._refresh_design_views()
            self.tabs.setCurrentWidget(self.report_widget)

    def _handle_finished(self, action: str, payload: dict) -> None:
        if action in {"conversation_start", "conversation_continue"}:
            session = PipelineSession.from_flow_state(payload["state"])
            self._apply_session(session)
            self._refresh_run_selector()

        elif action == "generate":
            self.session.task = payload["task"]
            self.session.candidates = payload["candidates"]
            self.session.screened_candidates = []
            self.session.evaluated_candidates = []
            self.session.results_by_session_id = {}
            self.session.knowledge_updates = []
            self.session.report = None
            self._apply_session(self.session)
            target_total = requested_candidate_pool_size(self.session.task)
            self.chat_widget.add_message(
                "SYSTEM",
                f"手动入口：候选池目标 {target_total} 个，当前实际生成 {len(self.session.candidates)} 个候选样本。",
            )

        elif action == "screen":
            self.session.screened_candidates = payload["screened_candidates"]
            self.session.evaluated_candidates = payload["screened_candidates"]
            self._apply_session(self.session)
            requested_top_k = requested_screen_top_k(self.session.task)
            self.chat_widget.add_message(
                "SYSTEM",
                f"手动入口：代理模型初筛完成，请求 Top-{requested_top_k}，当前实际展示 {len(self.session.screened_candidates)} 个候选。",
            )

        elif action == "evaluate":
            for result in payload["results"]:
                session_candidate_id = result.get("session_candidate_id", result["candidate_id"])
                self.session.results_by_session_id[session_candidate_id] = result
                self.abaqus_widget.append_or_update_result(result)
            self.session.knowledge_updates = list(payload.get("knowledge_updates") or self.session.knowledge_updates)
            self._apply_session(self.session)
            passed_count = sum(1 for item in payload["results"] if item.get("verdict") == "通过")
            self.chat_widget.add_message(
                "SYSTEM",
                f"手动入口：本轮 ABAQUS 校核完成，新增结果 {len(payload['results'])} 个，其中通过 {passed_count} 个。",
            )

        elif action == "report":
            self.session.report = payload["report"]
            self._apply_session(self.session)
            self.tabs.setCurrentWidget(self.report_widget)
            self.chat_widget.add_message(
                "SYSTEM",
                f"手动入口：报告已生成：{payload['report'].get('markdown_path')} / {payload['report'].get('pdf_path')}",
            )

        self._update_button_states()

    def _handle_failed(self, error_message: str) -> None:
        self.chat_widget.add_message("SYSTEM", f"执行失败：{error_message}")
        self.log_widget.append_log("SYSTEM", error_message)
        self._update_button_states()

    def _initial_task_html(self) -> str:
        return (
            "<h3>当前任务</h3>"
            "<p>输入自然语言需求后，系统会自动解析任务、生成候选，并在关键节点引导你确认是否继续。</p>"
        )

    def _workflow_html(self) -> str:
        return (
            "<h3>对话流程</h3>"
            "<p>1. 输入一句自然语言需求，系统解析候选池总数和初筛保留数并生成初始候选</p>"
            "<p>2. 系统询问是否进行代理模型初筛，并解释当前评分机制、候选池目标和 Top-K 目标</p>"
            "<p>3. 系统询问是否进行有限元校核，并展示入选原因</p>"
            "<p>4. 校核完成后展示极限压力、失效模式、结论，并询问是否导出报告</p>"
            "<p>5. 聊天区会同时显示结构化进度和助手说明；辅助与手动入口可随时介入</p>"
        )

    def _task_summary_html(self) -> str:
        if not self.session.task:
            return self._initial_task_html()
        task = self.session.task
        task_payload = task_payload_from_request(task)
        material = task_payload.get("material_system", {})
        generated_count = len(self.session.candidates)
        candidate_pool_target = requested_candidate_pool_size(task)
        requested_top_k = requested_screen_top_k(task)
        effective_top_k = effective_screen_top_k(task, generated_count)
        return (
            "<h3>当前任务</h3>"
            f"<p><b>会话任务编号：</b>{task.get('task_id')}</p>"
            f"<p><b>应用场景：</b>{task_payload.get('application')}</p>"
            f"<p><b>工况：</b>{describe_load_conditions(task_payload.get('load_conditions', {}))}</p>"
            f"<p><b>边界条件：</b>{describe_boundary_conditions(task_payload.get('boundary_conditions', {}))}</p>"
            f"<p><b>候选池：</b>{generated_count} / 目标 {candidate_pool_target}</p>"
            f"<p><b>初筛目标：</b>Top-{requested_top_k}（当前最多 {effective_top_k}）</p>"
            f"<p><b>材料：</b>{material.get('name')} | E1={material.get('E1_GPa')} GPa | 密度={material.get('density_kg_per_m3')} kg/m^3</p>"
            f"<p><b>目标：</b>P_ult >= {task_payload.get('design_targets', {}).get('ultimate_pressure_min_MPa')} MPa，{task_payload.get('design_targets', {}).get('primary_objective')}</p>"
            f"<p><b>阶段：</b>{self.session.stage}</p>"
        )

    def closeEvent(self, event: QCloseEvent) -> None:
        try:
            self.candidate_widget.reset_view()
            self.abaqus_widget.reset_view()
        finally:
            thread = self.worker_thread
            if thread is not None and not sip.isdeleted(thread):
                if thread.isRunning():
                    thread.quit()
                    thread.wait(3000)
            self._clear_worker_refs()
            super().closeEvent(event)


def main() -> int:
    ensure_project_dirs()
    app = QApplication(sys.argv)
    window = MainWindow()
    window.showMaximized()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())

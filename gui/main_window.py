"""PyQt6 主界面。"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from PyQt6 import sip
from PyQt6.QtCore import QObject, Qt, QThread, QUrl, pyqtSignal
from PyQt6.QtGui import QCloseEvent, QDesktopServices
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QFrame,
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
from gui.i18n import LANGUAGE_OPTIONS, LocaleManager
from gui.knowledge_widget import KnowledgeWidget
from gui.log_widget import LogWidget
from gui.report_widget import ReportWidget
from gui.result_trace_widget import ResultTraceWidget
from gui.task_config_widget import TaskConfigWidget
from gui.theme import application_stylesheet, install_application_font
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
        self.locale = LocaleManager()
        self.font_family = install_application_font(QApplication.instance())
        self.setWindowTitle(self.locale.text("app.title"))
        self.resize(1680, 980)
        self.session = PipelineSession()
        self.worker_thread: QThread | None = None
        self.worker: PipelineWorker | None = None
        self.workflow_event_store = WorkflowEventStore()

        self.app_title_label = QLabel(self.locale.text("app.title"))
        self.app_title_label.setObjectName("appTitle")
        self.app_subtitle_label = QLabel(self.locale.text("app.subtitle"))
        self.app_subtitle_label.setObjectName("appSubtitle")
        self.language_label = QLabel(self.locale.text("section.language"))
        self.language_label.setObjectName("appSubtitle")
        self.language_selector = QComboBox()
        for language, label in LANGUAGE_OPTIONS.items():
            self.language_selector.addItem(label, language)
        current_language_index = self.language_selector.findData(self.locale.language)
        if current_language_index >= 0:
            self.language_selector.setCurrentIndex(current_language_index)

        self.chat_widget = ChatWidget()
        self.task_browser = QTextBrowser()
        self.task_browser.setHtml(self._initial_task_html())
        self.task_browser.setMinimumHeight(96)
        self.task_browser.setMaximumHeight(138)
        self.workflow_browser = QTextBrowser()
        self.workflow_browser.setHtml(self._workflow_html())
        self.workflow_browser.setMinimumHeight(112)
        self.workflow_browser.setMaximumHeight(156)
        self.workflow_browser.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.status_label = QLabel(self.locale.text("status.waiting"))
        self.status_label.setWordWrap(True)
        self.status_label.setObjectName("statusLabel")

        self.input_line = QLineEdit()
        self.input_line.setPlaceholderText(self.locale.text("input.placeholder"))

        self.generate_button = QPushButton(self.locale.text("button.start"))
        self.confirm_yes_button = QPushButton(self.locale.text("button.confirm"))
        self.confirm_no_button = QPushButton(self.locale.text("button.pause"))

        self.example_button = QPushButton(self.locale.text("button.example"))
        self.refresh_button = QPushButton(self.locale.text("button.refresh_knowledge"))
        self.open_report_button = QPushButton(self.locale.text("button.open_report"))
        self.run_selector = QComboBox()
        self.run_selector.setMinimumHeight(42)
        self.refresh_runs_button = QPushButton(self.locale.text("button.refresh_runs"))
        self.restore_run_button = QPushButton(self.locale.text("button.restore_run"))

        self.screen_button = QPushButton(self.locale.text("button.screen"))
        self.evaluate_selected_button = QPushButton(self.locale.text("button.evaluate_selected"))
        self.evaluate_all_button = QPushButton(self.locale.text("button.evaluate_all"))
        self.report_button = QPushButton(self.locale.text("button.report"))
        self.reset_button = QPushButton(self.locale.text("button.reset"))

        self.stage_card = QLabel(self.locale.text("metric.stage", value="idle"))
        self.candidate_card = QLabel(self.locale.text("metric.candidate_zero"))
        self.pending_card = QLabel(self.locale.text("metric.pending_zero"))
        self.pass_card = QLabel(self.locale.text("metric.pass", count=0))

        self.candidate_widget = CandidateWidget(language=self.locale.language)
        self.abaqus_widget = AbaqusWidget(language=self.locale.language)
        self.knowledge_widget = KnowledgeWidget()
        self.report_widget = ReportWidget()
        self.result_trace_widget = ResultTraceWidget()
        self.log_widget = LogWidget()
        self.task_config_widget = TaskConfigWidget(language=self.locale.language)
        self.workflow_widget = WorkflowWidget(event_store=self.workflow_event_store)

        self.tabs = QTabWidget()
        self.tabs.addTab(self.task_config_widget, self.locale.text("tab.task"))
        self.tabs.addTab(self.workflow_widget, self.locale.text("tab.workflow"))
        self.tabs.addTab(self.candidate_widget, self.locale.text("tab.candidates"))
        self.tabs.addTab(self.abaqus_widget, self.locale.text("tab.abaqus"))
        self.tabs.addTab(self.result_trace_widget, self.locale.text("tab.trace"))
        self.tabs.addTab(self.report_widget, self.locale.text("tab.report"))
        self.tabs.addTab(self.knowledge_widget, self.locale.text("tab.knowledge"))
        self.tabs.addTab(self.log_widget, self.locale.text("tab.log"))

        self._build_layout()
        self._apply_styles()
        self._connect_signals()
        self._update_button_states()
        self._update_overview_cards()
        self._refresh_run_selector()
        self.knowledge_widget.refresh(load_evidence=False)

    def _build_layout(self) -> None:
        self.primary_header = QLabel(self.locale.text("section.primary"))
        self.primary_header.setObjectName("sectionTitle")
        primary_button_layout = QGridLayout()
        primary_button_layout.setHorizontalSpacing(10)
        primary_button_layout.setVerticalSpacing(10)
        primary_button_layout.addWidget(self.generate_button, 0, 0)
        primary_button_layout.addWidget(self.confirm_yes_button, 0, 1)
        primary_button_layout.addWidget(self.confirm_no_button, 0, 2)

        self.utility_header = QLabel(self.locale.text("section.utility"))
        self.utility_header.setObjectName("sectionTitle")
        utility_button_layout = QGridLayout()
        utility_button_layout.setHorizontalSpacing(10)
        utility_button_layout.setVerticalSpacing(10)
        utility_button_layout.addWidget(self.example_button, 0, 0)
        utility_button_layout.addWidget(self.refresh_button, 0, 1)
        utility_button_layout.addWidget(self.open_report_button, 0, 2)
        utility_button_layout.addWidget(self.run_selector, 1, 0, 1, 3)
        utility_button_layout.addWidget(self.refresh_runs_button, 2, 0)
        utility_button_layout.addWidget(self.restore_run_button, 2, 1, 1, 2)

        self.stats_header = QLabel(self.locale.text("section.session"))
        self.stats_header.setObjectName("sectionTitle")
        stats_layout = QGridLayout()
        stats_layout.setHorizontalSpacing(10)
        stats_layout.setVerticalSpacing(10)
        stats_layout.addWidget(self.stage_card, 0, 0)
        stats_layout.addWidget(self.candidate_card, 0, 1)
        stats_layout.addWidget(self.pending_card, 1, 0)
        stats_layout.addWidget(self.pass_card, 1, 1)

        self.manual_header = QLabel(self.locale.text("section.manual"))
        self.manual_header.setObjectName("sectionTitle")
        manual_button_layout = QGridLayout()
        manual_button_layout.setHorizontalSpacing(10)
        manual_button_layout.setVerticalSpacing(10)
        manual_button_layout.addWidget(self.screen_button, 0, 0)
        manual_button_layout.addWidget(self.evaluate_selected_button, 0, 1)
        manual_button_layout.addWidget(self.evaluate_all_button, 0, 2)
        manual_button_layout.addWidget(self.report_button, 1, 0)
        manual_button_layout.addWidget(self.reset_button, 1, 1, 1, 2)

        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(14, 14, 14, 14)
        left_layout.setSpacing(9)
        left_layout.addWidget(self.task_browser)
        left_layout.addWidget(self.workflow_browser)
        left_layout.addWidget(self.chat_widget, 1)
        left_layout.addWidget(self.status_label)
        left_layout.addWidget(self.input_line)
        left_layout.addWidget(self.primary_header)
        left_layout.addLayout(primary_button_layout)
        left_layout.addWidget(self.utility_header)
        left_layout.addLayout(utility_button_layout)
        left_layout.addWidget(self.stats_header)
        left_layout.addLayout(stats_layout)
        left_layout.addWidget(self.manual_header)
        left_layout.addLayout(manual_button_layout)

        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(10, 10, 10, 10)
        right_layout.addWidget(self.tabs)

        top_bar = QFrame()
        top_bar.setObjectName("topBar")
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(18, 12, 18, 12)
        title_layout = QVBoxLayout()
        title_layout.setSpacing(2)
        title_layout.addWidget(self.app_title_label)
        title_layout.addWidget(self.app_subtitle_label)
        top_layout.addLayout(title_layout, 1)
        top_layout.addWidget(self.language_label)
        top_layout.addWidget(self.language_selector)

        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(12)
        left_container = QWidget()
        right_container = QWidget()
        left_container.setObjectName("leftRail")
        right_container.setObjectName("workbenchPane")
        left_container.setLayout(left_layout)
        right_container.setLayout(right_layout)
        main_layout.addWidget(left_container, 4)
        main_layout.addWidget(right_container, 6)

        root_layout = QVBoxLayout()
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)
        root_layout.addWidget(top_bar)
        root_layout.addLayout(main_layout, 1)
        root = QWidget()
        root.setLayout(root_layout)
        self.setCentralWidget(root)

    def _set_button_variant(self, button: QPushButton, variant: str = "default") -> None:
        button.setMinimumHeight(38)
        button.setProperty("variant", variant)

    def _apply_styles(self) -> None:
        for card in [self.stage_card, self.candidate_card, self.pending_card, self.pass_card]:
            card.setProperty("role", "metricCard")
        self._set_button_variant(self.generate_button, "primary")
        self._set_button_variant(self.confirm_yes_button, "success")
        self._set_button_variant(self.confirm_no_button, "warning")
        self._set_button_variant(self.example_button)
        self._set_button_variant(self.refresh_button)
        self._set_button_variant(self.open_report_button)
        self._set_button_variant(self.refresh_runs_button)
        self._set_button_variant(self.restore_run_button, "secondary")
        self._set_button_variant(self.screen_button)
        self._set_button_variant(self.evaluate_selected_button)
        self._set_button_variant(self.evaluate_all_button)
        self._set_button_variant(self.report_button)
        self._set_button_variant(self.reset_button, "danger")
        self.setStyleSheet(application_stylesheet(self.font_family))

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
        self.language_selector.currentIndexChanged.connect(self._change_language)

        self.screen_button.clicked.connect(self._start_screen)
        self.evaluate_selected_button.clicked.connect(self._start_evaluate_selected)
        self.evaluate_all_button.clicked.connect(self._start_evaluate_all)
        self.report_button.clicked.connect(self._start_report)
        self.reset_button.clicked.connect(self._reset_session)

    def _change_language(self) -> None:
        language = str(self.language_selector.currentData() or self.locale.language)
        if language == self.locale.language:
            return
        self.locale.set_language(language)
        self._apply_language()

    def _apply_language(self) -> None:
        self.setWindowTitle(self.locale.text("app.title"))
        self.app_title_label.setText(self.locale.text("app.title"))
        self.app_subtitle_label.setText(self.locale.text("app.subtitle"))
        self.language_label.setText(self.locale.text("section.language"))
        self.input_line.setPlaceholderText(self.locale.text("input.placeholder"))
        self.generate_button.setText(self.locale.text("button.start"))
        self.confirm_yes_button.setText(self.locale.text("button.confirm"))
        self.confirm_no_button.setText(self.locale.text("button.pause"))
        self.example_button.setText(self.locale.text("button.example"))
        self.refresh_button.setText(self.locale.text("button.refresh_knowledge"))
        self.open_report_button.setText(self.locale.text("button.open_report"))
        self.refresh_runs_button.setText(self.locale.text("button.refresh_runs"))
        self.restore_run_button.setText(self.locale.text("button.restore_run"))
        self.screen_button.setText(self.locale.text("button.screen"))
        self.evaluate_selected_button.setText(self.locale.text("button.evaluate_selected"))
        self.evaluate_all_button.setText(self.locale.text("button.evaluate_all"))
        self.report_button.setText(self.locale.text("button.report"))
        self.reset_button.setText(self.locale.text("button.reset"))
        self.primary_header.setText(self.locale.text("section.primary"))
        self.utility_header.setText(self.locale.text("section.utility"))
        self.stats_header.setText(self.locale.text("section.session"))
        self.manual_header.setText(self.locale.text("section.manual"))
        tab_texts = [
            self.locale.text("tab.task"),
            self.locale.text("tab.workflow"),
            self.locale.text("tab.candidates"),
            self.locale.text("tab.abaqus"),
            self.locale.text("tab.trace"),
            self.locale.text("tab.report"),
            self.locale.text("tab.knowledge"),
            self.locale.text("tab.log"),
        ]
        for index, label in enumerate(tab_texts):
            self.tabs.setTabText(index, label)
        self.candidate_widget.set_language(self.locale.language)
        self.abaqus_widget.set_language(self.locale.language)
        self.task_config_widget.set_language(self.locale.language)
        if not self.session.task:
            self.task_browser.setHtml(self._initial_task_html())
            self.workflow_browser.setHtml(self._workflow_html())
            self.status_label.setText(self.locale.text("status.waiting"))
        self._update_overview_cards()
        self._refresh_run_selector()

    def _set_busy(self, busy: bool, status_text: str) -> None:
        self.status_label.setText(self.locale.text("status.busy", status=status_text))
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
        self.stage_card.setText(self.locale.text("metric.stage", value=self.session.stage or "idle"))
        self.candidate_card.setText(
            self.locale.text("metric.candidate", count=generated_count, target=candidate_pool_target)
            if self.session.task
            else self.locale.text("metric.candidate_zero")
        )
        self.pending_card.setText(
            self.locale.text("metric.pending", count=pending_count, target=requested_top_k)
            if self.session.task
            else self.locale.text("metric.pending_zero")
        )
        self.pass_card.setText(self.locale.text("metric.pass", count=passed_count))

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
        self.worker_thread.finished.connect(lambda: self._set_busy(False, self.locale.text("status.ready_next")))
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
            self.run_selector.addItem(self.locale.text("snapshot.none"), "")
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
            self.status_label.setText(self.locale.text("status.no_snapshot"))
            return
        try:
            snapshot = self.workflow_event_store.load_snapshot(run_id)
        except Exception as exc:
            self.status_label.setText(self.locale.text("status.snapshot_failed", error=exc))
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
        self.status_label.setText(self.locale.text("status.snapshot_loaded", run_id=run_id))
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
        self.status_label.setText(self.locale.text("status.knowledge_refreshed"))

    def _open_latest_report(self) -> None:
        self.report_widget.refresh_latest()
        for path in [RESULTS_DIR / "latest_report.pdf", RESULTS_DIR / "latest_report.md"]:
            if path.exists():
                QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))
                self.chat_widget.add_message("SYSTEM", self.locale.text("message.open_report", path=path))
                return
        self.chat_widget.add_message("SYSTEM", self.locale.text("message.no_report"))

    def _respond_confirmation(self, approved: bool) -> None:
        if self.session.pending_confirmation is None:
            return
        label = self.locale.text("user.continue") if approved else self.locale.text("user.pause")
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
            self.chat_widget.add_message("SYSTEM", self.locale.text("message.selected_done"))
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
            self.chat_widget.add_message("SYSTEM", self.locale.text("message.all_done"))
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
        self.status_label.setText(self.locale.text("status.waiting"))
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
            f"<h3>{self.locale.text('task.initial.title')}</h3>"
            f"<p>{self.locale.text('task.initial.body')}</p>"
        )

    def _workflow_html(self) -> str:
        return (
            f"<h3>{self.locale.text('workflow.initial.title')}</h3>"
            f"<p>{self.locale.text('workflow.initial.body')}</p>"
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
    install_application_font(app)
    window = MainWindow()
    window.showMaximized()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())

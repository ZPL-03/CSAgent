"""PyQt6 主界面。"""

from __future__ import annotations

import csv
import json
import sys
from datetime import datetime
from dataclasses import dataclass, field
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

UI_LAYOUT_VERSION = 3

from PyQt6 import sip
from PyQt6.QtCore import QObject, QRectF, QSettings, QSize, Qt, QThread, QUrl, pyqtSignal
from PyQt6.QtGui import QColor, QCloseEvent, QDesktopServices, QIcon, QPainter, QPen, QPixmap
from PyQt6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QSplitter,
    QStackedWidget,
    QTabWidget,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from agents.orchestrator import OrchestratorAgent
from core.conversation_flow import ConversationFlowController, ConversationState
from core.paths import ASSETS_DIR, RESULTS_DIR, ensure_project_dirs
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
from gui.i18n import LANGUAGE_OPTIONS, THEME_OPTIONS, LocaleManager
from gui.interactive_view import InteractivePlotWidget
from gui.knowledge_widget import KnowledgeWidget
from gui.log_widget import LogWidget
from gui.report_widget import ReportWidget
from gui.result_trace_widget import ResultTraceWidget
from gui.task_config_widget import TaskConfigWidget
from gui.theme import application_stylesheet, install_application_font, resolve_theme
from gui.workbench_widgets import AgentStatusCard, FlowDagWidget, StatusPill
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
            workflow_db_path = self.payload.get("workflow_db_path")
            event_store = WorkflowEventStore(Path(str(workflow_db_path))) if workflow_db_path else None
            controller = ConversationFlowController(
                orchestrator,
                event_callback=self._emit_flow,
                event_store=event_store,
            )

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
    """复合材料耐压壳多智能体工程工作台。"""

    AGENT_DESCRIPTIONS = [
        ("ORCHESTRATOR", "agent.orchestrator"),
        ("CANDIDATE_GEN", "agent.candidate_gen"),
        ("SCREENER", "agent.screener"),
        ("FEM_AGENT", "agent.fem"),
        ("KNOWLEDGE_AGENT", "agent.knowledge"),
        ("REPORT_GEN", "agent.report"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.locale = LocaleManager()
        self.font_family = install_application_font(QApplication.instance())
        self.setWindowTitle(self.locale.text("app.title"))
        self._app_icon_path = ASSETS_DIR / "csagent_icon_256.png"
        self._brand_badge_path = ASSETS_DIR / "csagent_badge.png"
        if self._app_icon_path.exists():
            self.setWindowIcon(QIcon(str(self._app_icon_path)))
        self.resize(1680, 980)
        self.ui_state_settings = QSettings("CSAgent", "Workbench")
        self.session = PipelineSession()
        self.worker_thread: QThread | None = None
        self.worker: PipelineWorker | None = None
        self.workflow_event_store = WorkflowEventStore()
        self.last_llm_trace_payload: dict | None = None
        self.runtime_agent_states: dict[str, str] = {}
        self.runtime_stage_text = ""

        self.app_title_label = QLabel(self.locale.text("app.title"))
        self.app_title_label.setObjectName("appTitle")
        self.app_subtitle_label = QLabel(self.locale.text("app.subtitle"))
        self.app_subtitle_label.setObjectName("appSubtitle")
        self.logo_label = QLabel("CS")
        self.logo_label.setObjectName("logoBadge")
        self.logo_label.setProperty("mode", "text")
        self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.logo_label.setFixedSize(38, 38)
        self._sync_brand_logo()
        self.model_status_label = StatusPill(self.locale.text("model.current"), "success")
        self.language_label = QLabel(self.locale.text("section.language"))
        self.language_label.setObjectName("appSubtitle")
        self.theme_label = QLabel(self.locale.text("section.theme"))
        self.theme_label.setObjectName("appSubtitle")
        self.nav_buttons = [
            QPushButton(self.locale.text("nav.workbench")),
            QPushButton(self.locale.text("nav.project")),
            QPushButton(self.locale.text("nav.knowledge")),
            QPushButton(self.locale.text("nav.monitor")),
            QPushButton(self.locale.text("nav.settings")),
        ]
        self.nav_group = QButtonGroup(self)
        self.nav_group.setExclusive(True)
        for index, button in enumerate(self.nav_buttons):
            button.setObjectName("navButton")
            button.setCheckable(True)
            self.nav_group.addButton(button, index)
        self.nav_buttons[0].setChecked(True)
        self.language_selector = QComboBox()
        for language, label in LANGUAGE_OPTIONS.items():
            self.language_selector.addItem(label, language)
        current_language_index = self.language_selector.findData(self.locale.language)
        if current_language_index >= 0:
            self.language_selector.setCurrentIndex(current_language_index)
        self.theme_selector = QComboBox()
        for theme, label in THEME_OPTIONS[self.locale.language].items():
            self.theme_selector.addItem(label, theme)
        current_theme_index = self.theme_selector.findData(self.locale.theme)
        if current_theme_index >= 0:
            self.theme_selector.setCurrentIndex(current_theme_index)

        self.chat_widget = ChatWidget()
        self.chat_widget.setMinimumHeight(220)
        self.chat_widget.set_empty_text(self.locale.text("chat.empty"))
        self._apply_chat_empty_state()
        self.task_browser = QTextBrowser()
        self.task_browser.setHtml(self._initial_task_html())
        self.task_browser.setMinimumHeight(96)
        self.task_browser.setMaximumHeight(126)
        self.status_label = QLabel(self.locale.text("status.waiting"))
        self.status_label.setWordWrap(True)
        self.status_label.setObjectName("chatStatus")

        self.input_line = QLineEdit()
        self.input_line.setPlaceholderText(self.locale.text("input.placeholder"))

        self.generate_button = QPushButton(self.locale.text("button.start"))
        self.confirm_yes_button = QPushButton(self.locale.text("button.confirm"))
        self.confirm_no_button = QPushButton(self.locale.text("button.pause"))
        self.trace_button = QPushButton(self.locale.text("button.view_trace"))
        self.trace_button.setObjectName("traceLinkButton")
        self.trace_button.setMinimumWidth(132)

        self.example_button = QPushButton(self.locale.text("button.example"))
        self.example_button.setToolTip(self.locale.text("button.example"))
        self.refresh_button = QPushButton(self.locale.text("button.refresh_knowledge"))
        self.open_report_button = QPushButton(self.locale.text("button.open_report"))
        self.export_data_button = QPushButton(self.locale.text("button.export_data"))
        self.reset_view_button = QPushButton()
        self.reset_view_button.setToolTip(self.locale.text("button.reset_view"))
        self.fit_view_button = QPushButton()
        self.fit_view_button.setToolTip(self.locale.text("button.fit_view"))
        self.run_selector = QComboBox()
        self.run_selector.setMinimumHeight(42)
        self.refresh_runs_button = QPushButton(self.locale.text("button.refresh_runs"))
        self.restore_run_button = QPushButton(self.locale.text("button.restore_run"))
        self.restore_run_button.setToolTip(self.locale.text("tooltip.restore_run"))

        self.screen_button = QPushButton(self.locale.text("button.screen"))
        self.evaluate_selected_button = QPushButton(self.locale.text("button.evaluate_selected"))
        self.evaluate_all_button = QPushButton(self.locale.text("button.evaluate_all"))
        self.report_button = QPushButton(self.locale.text("button.report"))
        self.reset_button = QPushButton(self.locale.text("button.reset"))

        self.stage_card = QLabel(self.locale.text("metric.stage", value="idle"))
        self.candidate_card = QLabel(self.locale.text("metric.candidate_zero"))
        self.pending_card = QLabel(self.locale.text("metric.pending_zero"))
        self.pass_card = QLabel(self.locale.text("metric.pass", count=0))
        self.primary_header = QLabel(self.locale.text("section.primary"))
        self.primary_header.setObjectName("sectionTitle")
        self.utility_header = QLabel(self.locale.text("section.utility"))
        self.utility_header.setObjectName("sectionTitle")
        self.stats_header = QLabel(self.locale.text("section.session"))
        self.stats_header.setObjectName("sectionTitle")
        self.log_header = QLabel(self.locale.text("section.runtime_log"))
        self.log_header.setObjectName("sectionTitle")
        self.agent_header = QLabel(self.locale.text("section.agents"))
        self.agent_header.setObjectName("sectionTitle")
        self.queue_header = QLabel(self.locale.text("section.queue"))
        self.queue_header.setObjectName("sectionTitle")
        self.knowledge_status_header = QLabel(self.locale.text("section.knowledge_status"))
        self.knowledge_status_header.setObjectName("sectionTitle")
        self.workbench_header = QLabel(self.locale.text("section.workbench"))
        self.workbench_header.setObjectName("sectionTitle")
        self.dialog_header = QLabel(self.locale.text("section.dialog"))
        self.dialog_header.setObjectName("sectionTitle")
        self.details_header = QLabel(self.locale.text("section.details"))
        self.details_header.setObjectName("sectionTitle")
        self.agent_cards: dict[str, AgentStatusCard] = {}
        self.queue_label = QLabel(self.locale.text("queue.idle"))
        self.queue_label.setObjectName("statusLabel")
        self.queue_label.setWordWrap(True)
        self.queue_progress = QProgressBar()
        self.queue_progress.setRange(0, 100)
        self.queue_progress.setValue(0)
        self.queue_progress.setTextVisible(False)
        self.knowledge_status_label = QLabel("")
        self.knowledge_status_label.setObjectName("statusLabel")
        self.knowledge_status_label.setWordWrap(True)

        self.candidate_widget = CandidateWidget(language=self.locale.language)
        self.abaqus_widget = AbaqusWidget(language=self.locale.language)
        self.knowledge_widget = KnowledgeWidget()
        self.report_widget = ReportWidget()
        self.result_trace_widget = ResultTraceWidget()
        self.log_widget = LogWidget()
        self.monitor_log_widget = LogWidget()
        self.task_config_widget = TaskConfigWidget(language=self.locale.language)
        self.workflow_widget = WorkflowWidget(event_store=self.workflow_event_store)
        self.workflow_widget.setMinimumHeight(300)
        self.flow_dag_widget = FlowDagWidget()
        self.live_result_view = InteractivePlotWidget(
            self.locale.text("live_view.empty"),
            language=self.locale.language,
        )
        self.live_result_view.setMinimumHeight(260)

        self.tabs = QTabWidget()
        self.tabs.addTab(self.candidate_widget, self.locale.text("tab.candidates"))
        self.tabs.addTab(self.abaqus_widget, self.locale.text("tab.abaqus"))
        self.tabs.addTab(self.result_trace_widget, self.locale.text("tab.trace"))
        self.tabs.addTab(self.report_widget, self.locale.text("tab.report"))

        self._build_layout()
        self._apply_styles()
        self._connect_signals()
        self._restore_window_layout()
        self._update_button_states()
        self._update_overview_cards()
        self._refresh_run_selector()
        self.knowledge_widget.refresh(load_evidence=False)
        self.live_result_view.show_reference_hull()

    def _sync_brand_logo(self) -> None:
        if not self._brand_badge_path.exists():
            self.logo_label.setProperty("mode", "text")
            self.logo_label.setText("CS")
            self.logo_label.setPixmap(QPixmap())
            return
        pixmap = QPixmap(str(self._brand_badge_path))
        if pixmap.isNull():
            self.logo_label.setProperty("mode", "text")
            self.logo_label.setText("CS")
            return
        self.logo_label.setProperty("mode", "image")
        self.logo_label.setText("")
        self.logo_label.setPixmap(
            pixmap.scaled(
                self.logo_label.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )

    def _build_layout(self) -> None:
        input_action_layout = QHBoxLayout()
        input_action_layout.setSpacing(10)
        self.example_button.setText("+")
        self.example_button.setFixedWidth(46)
        input_action_layout.addWidget(self.example_button)
        input_action_layout.addWidget(self.input_line, 1)
        input_action_layout.addWidget(self.generate_button)

        hitl_layout = QHBoxLayout()
        hitl_layout.setSpacing(10)
        hitl_layout.addStretch(1)
        hitl_layout.addWidget(self.confirm_yes_button)
        hitl_layout.addWidget(self.confirm_no_button)

        stats_layout = QGridLayout()
        stats_layout.setHorizontalSpacing(10)
        stats_layout.setVerticalSpacing(10)
        stats_layout.addWidget(self.stage_card, 0, 0)
        stats_layout.addWidget(self.candidate_card, 0, 1)
        stats_layout.addWidget(self.pending_card, 1, 0)
        stats_layout.addWidget(self.pass_card, 1, 1)

        agent_layout = QVBoxLayout()
        agent_layout.setContentsMargins(14, 14, 14, 14)
        agent_layout.setSpacing(10)
        agent_layout.addWidget(self.agent_header)
        for agent_name, description_key in self.AGENT_DESCRIPTIONS:
            card = AgentStatusCard()
            card.set_theme(self.locale.theme)
            card.set_content(
                agent_name,
                "waiting",
                self.locale.text("agent.waiting"),
                self.locale.text(description_key),
            )
            self.agent_cards[agent_name] = card
            agent_layout.addWidget(card)
        agent_layout.addStretch(1)

        queue_layout = QVBoxLayout()
        queue_layout.setContentsMargins(14, 14, 14, 14)
        queue_layout.setSpacing(10)
        queue_layout.addWidget(self.queue_header)
        queue_layout.addWidget(self.queue_progress)
        queue_layout.addWidget(self.queue_label)
        queue_layout.addWidget(self.knowledge_status_header)
        queue_layout.addWidget(self.knowledge_status_label)
        queue_layout.addStretch(1)

        workflow_panel = QWidget()
        workflow_panel.setObjectName("centerWorkbench")
        workflow_panel.setMinimumHeight(210)
        workflow_panel.setMaximumHeight(236)
        workflow_layout = QVBoxLayout(workflow_panel)
        workflow_layout.setContentsMargins(0, 0, 0, 0)
        workflow_layout.setSpacing(0)
        workflow_layout.addWidget(self.flow_dag_widget, 1)

        chat_panel = QWidget()
        chat_panel.setObjectName("conversationPanel")
        chat_layout = QVBoxLayout(chat_panel)
        chat_layout.setContentsMargins(12, 12, 12, 12)
        chat_layout.setSpacing(12)
        chat_title_layout = QHBoxLayout()
        chat_title_layout.setSpacing(10)
        chat_title_layout.addWidget(self.dialog_header)
        chat_title_layout.addStretch(1)
        chat_title_layout.addWidget(self.trace_button)
        chat_layout.addLayout(chat_title_layout)
        chat_layout.addWidget(self.chat_widget, 1)
        chat_layout.addWidget(self.status_label)
        chat_layout.addLayout(input_action_layout)
        chat_layout.addLayout(hitl_layout)

        workbench_splitter = QSplitter(Qt.Orientation.Vertical)
        workbench_splitter.addWidget(workflow_panel)
        workbench_splitter.addWidget(chat_panel)
        workbench_splitter.setSizes([236, 780])
        self.workbench_splitter = workbench_splitter

        workbench_page = QWidget()
        workbench_page.setObjectName("centerWorkbench")
        workbench_layout = QVBoxLayout(workbench_page)
        workbench_layout.setContentsMargins(0, 0, 0, 0)
        workbench_layout.addWidget(workbench_splitter)

        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(14, 14, 14, 14)
        right_layout.setSpacing(10)
        live_header_layout = QHBoxLayout()
        live_header_layout.setContentsMargins(0, 0, 0, 0)
        live_header_layout.setSpacing(8)
        live_header_layout.addWidget(self.details_header, 1)
        live_header_layout.addWidget(self.reset_view_button)
        live_header_layout.addWidget(self.fit_view_button)
        right_layout.addLayout(live_header_layout)
        right_layout.addWidget(self.live_result_view, 2)
        right_layout.addWidget(self.stats_header)
        right_layout.addLayout(stats_layout)
        right_layout.addWidget(self.log_header)
        right_layout.addWidget(self.log_widget, 2)
        right_layout.addWidget(self.report_button)
        right_layout.addWidget(self.export_data_button)
        right_layout.addWidget(self.open_report_button)

        top_bar = QFrame()
        top_bar.setObjectName("topBar")
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(18, 12, 18, 12)
        title_layout = QVBoxLayout()
        title_layout.setSpacing(2)
        title_layout.addWidget(self.app_title_label)
        title_layout.addWidget(self.app_subtitle_label)
        top_layout.addWidget(self.logo_label)
        top_layout.addLayout(title_layout, 1)
        for button in self.nav_buttons:
            top_layout.addWidget(button)
        top_layout.addStretch(1)
        top_layout.addWidget(self.model_status_label)
        self.setMenuWidget(top_bar)

        workbench_left = QWidget()
        workbench_left.setObjectName("agentRail")
        left_layout = QVBoxLayout(workbench_left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)
        agent_widget = QWidget()
        agent_widget.setLayout(agent_layout)
        queue_widget = QWidget()
        queue_widget.setLayout(queue_layout)
        left_layout.addWidget(agent_widget, 3)
        left_layout.addWidget(queue_widget, 2)
        workbench_left.setMinimumWidth(248)
        workbench_left.setMaximumWidth(286)

        project_left = self._build_project_left_page()
        knowledge_left = self._build_knowledge_left_page()
        monitor_left = self._build_monitor_left_page()
        settings_left = self._build_settings_left_page()

        workbench_right = QWidget()
        workbench_right.setObjectName("resultRail")
        workbench_right.setLayout(right_layout)
        workbench_right.setMinimumWidth(330)
        workbench_right.setMaximumWidth(430)

        self.stack = QStackedWidget()
        self.stack.addWidget(workbench_page)
        project_page = QSplitter(Qt.Orientation.Vertical)
        project_page.setObjectName("centerWorkbench")
        project_page.addWidget(self.task_config_widget)
        project_page.addWidget(self.tabs)
        project_page.setSizes([260, 620])
        self.stack.addWidget(project_page)
        self.stack.addWidget(self.knowledge_widget)
        self.monitor_page = self._build_monitor_page()
        self.stack.addWidget(self.monitor_page)
        self.settings_page = self._build_settings_page()
        self.stack.addWidget(self.settings_page)

        self.left_stack = QStackedWidget()
        self.left_stack.addWidget(workbench_left)
        self.left_stack.addWidget(project_left)
        self.left_stack.addWidget(knowledge_left)
        self.left_stack.addWidget(monitor_left)
        self.left_stack.addWidget(settings_left)
        self.left_stack.setMinimumWidth(248)
        self.left_stack.setMaximumWidth(286)

        self.right_stack = QStackedWidget()
        self.right_stack.addWidget(workbench_right)
        self.right_stack.addWidget(self._build_project_right_page())
        self.right_stack.addWidget(self._build_knowledge_right_page())
        self.right_stack.addWidget(self._build_monitor_right_page())
        self.right_stack.addWidget(self._build_settings_right_page())
        self.right_stack.setMinimumWidth(330)
        self.right_stack.setMaximumWidth(430)

        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_splitter.setObjectName("mainShell")
        main_splitter.addWidget(self.left_stack)
        main_splitter.addWidget(self.stack)
        main_splitter.addWidget(self.right_stack)
        main_splitter.setChildrenCollapsible(False)
        main_splitter.setSizes([270, 960, 360])
        self.main_splitter = main_splitter
        self.setCentralWidget(main_splitter)

    def _sidebar_page(self, title: str, cards: list[tuple[str, str]], footer: str = "") -> QWidget:
        page = QWidget()
        page.setObjectName("agentRail")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(14, 16, 14, 16)
        layout.setSpacing(12)
        header = QLabel(title)
        header.setObjectName("sectionTitle")
        layout.addWidget(header)
        for primary, secondary in cards:
            card = QLabel(f"<b>{primary}</b><br>{secondary}")
            card.setObjectName("agentCard")
            card.setWordWrap(True)
            card.setProperty("state", "waiting")
            layout.addWidget(card)
        layout.addStretch(1)
        if footer:
            footer_label = QLabel(footer)
            footer_label.setObjectName("statusLabel")
            footer_label.setWordWrap(True)
            layout.addWidget(footer_label)
        return page

    def _right_page(self, title: str, cards: list[tuple[str, str]], footer_buttons: list[QPushButton] | None = None) -> QWidget:
        page = QWidget()
        page.setObjectName("resultRail")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(14, 16, 14, 16)
        layout.setSpacing(12)
        header = QLabel(title)
        header.setObjectName("sectionTitle")
        layout.addWidget(header)
        for primary, secondary in cards:
            card = QLabel(f"<b>{primary}</b><br>{secondary}")
            card.setObjectName("statusLabel")
            card.setWordWrap(True)
            layout.addWidget(card)
        layout.addStretch(1)
        for button in footer_buttons or []:
            layout.addWidget(button)
        return page

    def _build_project_left_page(self) -> QWidget:
        return self._sidebar_page(
            "项目 · DESIGN",
            [
                ("任务契约", "自然语言事实 / 几何参考 / 固定约束"),
                ("候选方案", "LLM / 案例迁移 / DOE 来源审计"),
                ("有限元结果", "线性屈曲 / Riks 后屈曲 / 云图"),
                ("报告输出", "Markdown / PDF / 工程解释"),
            ],
            "正式案例库：按 CASE_<n> 顺序编号\n候选会话编号：TMP_<n>",
        )

    def _build_knowledge_left_page(self) -> QWidget:
        return self._sidebar_page(
            "知识库 · CORPUS",
            [
                ("全部资料", "上传资料 / 解析 / 入库 / 检索"),
                ("设计规范", "标准、手册、工艺约束"),
                ("论文文献", "屈曲、后屈曲与代理模型"),
                ("试验报告", "耐压壳校核与缺陷敏感性"),
                ("项目档案", "案例记忆与运行审计"),
            ],
            "连接：项目运行时 RAG/KG\n检索：文本块 + 图谱关系 + 溯源证据",
        )

    def _build_monitor_left_page(self) -> QWidget:
        return self._sidebar_page(
            "监控 · RUNS",
            [
                ("当前会话", "LangGraph 事件流"),
                ("有限元队列", "ABAQUS 作业状态"),
                ("代理初筛", "PBIPF 预测与排序"),
                ("案例回流", "正式案例与失败原因"),
            ],
            "优化历史在产生多轮运行后显示\n不使用伪造 Pareto 数据",
        )

    def _build_settings_left_page(self) -> QWidget:
        return self._sidebar_page(
            "设置 · SETTINGS",
            [
                ("模型与 API", ".env / llm_config.yaml"),
                ("求解器集成", "ABAQUS 路径与工作目录"),
                ("智能体编排", "LangGraph / HITL / SQLite"),
                ("知识库 / RAG", "top_k / 图谱增强 / 溯源"),
                ("通知与日志", "运行审计与异常记录"),
            ],
            "运行事实源：本项目配置与数据",
        )

    def _build_project_right_page(self) -> QWidget:
        return self._right_page(
            "项目结果 · TRACE",
            [
                ("当前任务", "项目页展示结构化任务、候选、FEM、追踪和报告。"),
                ("编号契约", "候选 TMP_<n>；正式 FEM 输入 C<n>；案例 CASE_<n>。"),
                ("数据回流", "通过 FEM 的样本进入正式案例库，不依赖 task_id 检索。"),
            ],
            [self.screen_button, self.evaluate_selected_button, self.evaluate_all_button, self.reset_button],
        )

    def _build_knowledge_right_page(self) -> QWidget:
        return self._right_page(
            "检索测试 · RETRIEVAL",
            [
                ("混合检索", "RAG 文本块 + 知识图谱路径命中。"),
                ("检索边界", "证据用于上下文和审计，不替代代理公式或 FEM 结果。"),
                ("入库流水线", "MinerU/Docling 解析、token 分块、去重、KG 抽取。"),
            ],
            [self.refresh_button],
        )

    def _build_monitor_right_page(self) -> QWidget:
        page = QWidget()
        page.setObjectName("resultRail")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(14, 16, 14, 16)
        layout.setSpacing(12)
        header = QLabel("运行审计 · CHECKS")
        header.setObjectName("sectionTitle")
        layout.addWidget(header)
        for primary, secondary in [
            ("LLM 后端", "在工作流面板中执行实时健康检测。"),
            ("有限元队列", "记录入队、运行、成功、失败和结果摘要。"),
            ("优化历史", "没有真实多轮优化数据时不绘制假 Pareto。"),
        ]:
            card = QLabel(f"<b>{primary}</b><br>{secondary}")
            card.setObjectName("statusLabel")
            card.setWordWrap(True)
            layout.addWidget(card)
        layout.addStretch(1)
        layout.addWidget(self.run_selector)
        row = QHBoxLayout()
        row.setSpacing(10)
        row.addWidget(self.refresh_runs_button)
        row.addWidget(self.restore_run_button)
        layout.addLayout(row)
        return page

    def _build_settings_right_page(self) -> QWidget:
        return self._right_page(
            "配置状态 · FACTS",
            [
                ("主模型", "默认调用耐压壳领域模型；不可用时走回退模型。"),
                ("知识库", "项目运行时 RAG/KG 支持用户上传资料并实时更新。"),
                ("主题语言", "支持简体中文 / English 和深色 / 亮色工程主题。"),
            ],
        )

    def _switch_workspace_page(self, index: int) -> None:
        button = self.nav_group.button(index)
        if button is not None and not button.isChecked():
            button.setChecked(True)
        self.stack.setCurrentIndex(index)
        self.left_stack.setCurrentIndex(index)
        self.right_stack.setCurrentIndex(index)

    def _settings_label_card(self, title: str, body: str, footer: str = "") -> QLabel:
        footer_html = f"<p style='color:#94a3b8;'>{footer}</p>" if footer else ""
        card = QLabel(f"<h2>{title}</h2><p>{body}</p>{footer_html}")
        card.setObjectName("settingsCard")
        card.setWordWrap(True)
        card.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        card.setMinimumHeight(130)
        card.setMaximumHeight(170)
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        return card

    def _build_settings_page(self) -> QWidget:
        page = QWidget()
        page.setObjectName("centerWorkbench")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(14)

        model_card = self._settings_label_card(
            "模型与 API",
            "主模型和回退模型读取本项目 .env 与 config/llm_config.yaml。候选提案、工程解释和报告补充调用 LLM；代理初筛、FEM、案例回流不调用 LLM。",
            "模型状态灯来自真实调用轨迹，主模型不可用时显示回退模型。",
        )

        solver_card = self._settings_label_card(
            "求解器集成 · ABAQUS",
            "求解器路径、工作目录、用户子程序开关读取 config/app_config.yaml。真实校核包含线性屈曲和 Static Riks 两阶段流程。",
            "有限元队列、作业状态、云图路径和失败诊断写入运行审计。",
        )

        graph_card = self._settings_label_card(
            "智能体编排 · LangGraph",
            "状态图节点覆盖任务解析、候选生成、代理初筛、有限元校核、知识回流和报告导出，人工确认点由 GUI 恢复推进。",
            "SQLite checkpoint 保存运行状态，支持中断后继续和审计复核。",
        )

        rag_card = self._settings_label_card(
            "知识库 / RAG / KG",
            "知识库由本项目运行时维护，支持上传资料、解析、token 分块、overlap、内容去重、检索和实体关系抽取。",
            "检索证据用于上下文和审计，不替代代理公式或 FEM 结果。",
        )

        parsing_card = self._settings_label_card(
            "解析与切块",
            "资料解析优先使用可用的 MinerU / Docling 能力，分块 token 数、overlap 和去重策略由知识库运行配置控制。",
            "入库流水线显示解析、分块、向量索引、KG 抽取和检索验证状态。",
        )

        audit_card = self._settings_label_card(
            "运行审计与恢复",
            "运行事件、工具调用、候选来源、去重、LLM 调用、有限元队列和案例回流结果均写入审计记录。",
            "监控页可检测 LLM 后端、导出运行审计并恢复历史状态。",
        )

        report_card = self._settings_label_card(
            "报告与导出",
            "阶段报告和最终报告读取真实任务、候选、初筛、FEM、知识证据与 LLM 工程解释生成。",
            "会话导出包含 JSON 快照和 TMP-C-CASE 追踪 CSV。",
        )

        ui_card = QWidget()
        ui_card.setObjectName("settingsCard")
        ui_card.setMinimumHeight(130)
        ui_card.setMaximumHeight(170)
        ui_card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        ui_layout = QVBoxLayout(ui_card)
        ui_layout.setContentsMargins(14, 12, 14, 12)
        ui_layout.setSpacing(10)
        title = QLabel("界面语言与主题")
        title.setObjectName("sectionTitle")
        title.setFixedHeight(26)
        description = QLabel("界面语言与主题只影响本地工作台显示，不改变任务、候选、FEM 或报告数据。")
        description.setWordWrap(True)
        description.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        controls = QGridLayout()
        controls.setContentsMargins(0, 0, 0, 0)
        controls.setHorizontalSpacing(14)
        controls.setVerticalSpacing(8)
        controls.addWidget(self.language_label, 0, 0)
        controls.addWidget(self.language_selector, 0, 1)
        controls.addWidget(self.theme_label, 0, 2)
        controls.addWidget(self.theme_selector, 0, 3)
        ui_layout.addWidget(title)
        ui_layout.addWidget(description)
        ui_layout.addLayout(controls)

        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(14)
        cards = [model_card, solver_card, graph_card, rag_card, parsing_card, audit_card, report_card, ui_card]
        for index, card in enumerate(cards):
            row = index // 2
            column = index % 2
            grid.addWidget(card, row, column)
            grid.setRowStretch(row, 0)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        layout.addLayout(grid, 0)
        layout.addStretch(1)
        return page

    def _build_monitor_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)
        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.addWidget(self.workflow_widget)
        splitter.addWidget(self.monitor_log_widget)
        splitter.setSizes([720, 180])
        layout.addWidget(splitter, 1)
        return page

    def _set_button_variant(self, button: QPushButton, variant: str = "default") -> None:
        if variant == "icon":
            button.setFixedSize(30, 28)
        else:
            button.setMinimumHeight(38)
        button.setProperty("variant", variant)

    def _apply_styles(self) -> None:
        for card in [self.stage_card, self.candidate_card, self.pending_card, self.pass_card]:
            card.setProperty("role", "metricCard")
        self._set_button_variant(self.generate_button, "primary")
        self._set_button_variant(self.confirm_yes_button, "success")
        self._set_button_variant(self.confirm_no_button, "warning")
        self._set_button_variant(self.trace_button, "link")
        self._set_button_variant(self.example_button)
        self._set_button_variant(self.refresh_button)
        self._set_button_variant(self.open_report_button, "secondary")
        self._set_button_variant(self.export_data_button, "secondary")
        self._set_button_variant(self.reset_view_button, "icon")
        self._set_button_variant(self.fit_view_button, "icon")
        self._set_button_variant(self.refresh_runs_button)
        self._set_button_variant(self.restore_run_button, "secondary")
        self._set_button_variant(self.screen_button)
        self._set_button_variant(self.evaluate_selected_button)
        self._set_button_variant(self.evaluate_all_button)
        self._set_button_variant(self.report_button, "primary")
        self._set_button_variant(self.reset_button, "danger")
        self.workflow_widget.set_theme(self.locale.theme)
        self.flow_dag_widget.set_theme(self.locale.theme)
        self.flow_dag_widget.set_language(self.locale.language)
        self.model_status_label.set_theme(self.locale.theme)
        for card in self.agent_cards.values():
            card.set_theme(self.locale.theme)
        self.live_result_view.set_theme(self.locale.theme)
        self.knowledge_widget.set_theme(self.locale.theme)
        self.chat_widget.set_theme(self.locale.theme)
        self.setStyleSheet(application_stylesheet(self.font_family, self.locale.theme))
        self._sync_view_button_icons()

    def _sync_view_button_icons(self) -> None:
        self.reset_view_button.setText("")
        self.reset_view_button.setIcon(self._make_view_icon("reset"))
        self.reset_view_button.setIconSize(QSize(14, 14))
        self.fit_view_button.setText("")
        self.fit_view_button.setIcon(self._make_view_icon("fit"))
        self.fit_view_button.setIconSize(QSize(14, 14))

    def _make_view_icon(self, icon_type: str) -> QIcon:
        pixmap = QPixmap(20, 20)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        color = QColor("#2563eb" if resolve_theme(self.locale.theme) == "light" else "#60a5fa")
        pen = QPen(color, 2.0)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        if icon_type == "reset":
            painter.drawArc(QRectF(4, 4, 12, 12), 35 * 16, 285 * 16)
            painter.drawLine(5, 6, 5, 11)
            painter.drawLine(5, 6, 10, 6)
        else:
            painter.drawLine(4, 8, 4, 4)
            painter.drawLine(4, 4, 8, 4)
            painter.drawLine(12, 4, 16, 4)
            painter.drawLine(16, 4, 16, 8)
            painter.drawLine(16, 12, 16, 16)
            painter.drawLine(16, 16, 12, 16)
            painter.drawLine(8, 16, 4, 16)
            painter.drawLine(4, 16, 4, 12)
        painter.end()
        return QIcon(pixmap)

    def _restore_window_layout(self) -> None:
        if int(self.ui_state_settings.value("layout_version", 0) or 0) != UI_LAYOUT_VERSION:
            self.ui_state_settings.clear()
            return
        geometry = self.ui_state_settings.value("window_geometry")
        state = self.ui_state_settings.value("window_state")
        if geometry:
            self.restoreGeometry(geometry)
        if state:
            self.restoreState(state)

    def _save_window_layout(self) -> None:
        self.ui_state_settings.setValue("layout_version", UI_LAYOUT_VERSION)
        self.ui_state_settings.setValue("window_geometry", self.saveGeometry())
        self.ui_state_settings.setValue("window_state", self.saveState())

    def _connect_signals(self) -> None:
        self.generate_button.clicked.connect(self._start_conversation)
        self.input_line.returnPressed.connect(self._start_conversation)
        self.confirm_yes_button.clicked.connect(lambda: self._respond_confirmation(True))
        self.confirm_no_button.clicked.connect(lambda: self._respond_confirmation(False))
        self.example_button.clicked.connect(self._load_example_prompt)
        self.trace_button.clicked.connect(lambda: self._switch_workspace_page(3))
        self.refresh_button.clicked.connect(self._refresh_knowledge_view)
        self.open_report_button.clicked.connect(self._open_latest_report)
        self.export_data_button.clicked.connect(self._export_session_data)
        self.reset_view_button.clicked.connect(self.live_result_view.reset_view)
        self.fit_view_button.clicked.connect(self.live_result_view.fit_view)
        self.refresh_runs_button.clicked.connect(self._refresh_run_selector)
        self.restore_run_button.clicked.connect(self._restore_selected_run)
        self.run_selector.currentIndexChanged.connect(lambda: self._update_button_states())
        self.language_selector.currentIndexChanged.connect(self._change_language)
        self.theme_selector.currentIndexChanged.connect(self._change_theme)
        self.nav_group.idClicked.connect(self._switch_workspace_page)

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

    def _change_theme(self) -> None:
        theme = str(self.theme_selector.currentData() or self.locale.theme)
        if theme == self.locale.theme:
            return
        self.locale.set_theme(theme)
        self._apply_styles()
        self._update_overview_cards()

    def _apply_language(self) -> None:
        self.setWindowTitle(self.locale.text("app.title"))
        self.app_title_label.setText(self.locale.text("app.title"))
        self.app_subtitle_label.setText(self.locale.text("app.subtitle"))
        self.language_label.setText(self.locale.text("section.language"))
        self.theme_label.setText(self.locale.text("section.theme"))
        if self.last_llm_trace_payload:
            self._update_model_status_from_llm_trace(self.last_llm_trace_payload, emit_log=False)
        else:
            self.model_status_label.set_state(self.locale.text("model.current"), "success")
        self.theme_selector.blockSignals(True)
        for index in range(self.theme_selector.count()):
            theme = str(self.theme_selector.itemData(index) or "")
            self.theme_selector.setItemText(index, THEME_OPTIONS[self.locale.language].get(theme, theme))
        theme_index = self.theme_selector.findData(self.locale.theme)
        if theme_index >= 0:
            self.theme_selector.setCurrentIndex(theme_index)
        self.theme_selector.blockSignals(False)
        nav_keys = ["nav.workbench", "nav.project", "nav.knowledge", "nav.monitor", "nav.settings"]
        for button, key in zip(self.nav_buttons, nav_keys):
            button.setText(self.locale.text(key))
        self.input_line.setPlaceholderText(self.locale.text("input.placeholder"))
        self.chat_widget.set_empty_text(self.locale.text("chat.empty"))
        self._apply_chat_empty_state()
        self.generate_button.setText(self.locale.text("button.start"))
        self.confirm_yes_button.setText(self.locale.text("button.confirm"))
        self.confirm_no_button.setText(self.locale.text("button.pause"))
        self.trace_button.setText(self.locale.text("button.view_trace"))
        self.trace_button.setMinimumWidth(max(132, self.trace_button.fontMetrics().horizontalAdvance(self.trace_button.text()) + 24))
        self.example_button.setText("+")
        self.example_button.setToolTip(self.locale.text("button.example"))
        self.refresh_button.setText(self.locale.text("button.refresh_knowledge"))
        self.open_report_button.setText(self.locale.text("button.open_report"))
        self.export_data_button.setText(self.locale.text("button.export_data"))
        self.reset_view_button.setText("")
        self.reset_view_button.setToolTip(self.locale.text("button.reset_view"))
        self.fit_view_button.setText("")
        self.fit_view_button.setToolTip(self.locale.text("button.fit_view"))
        self._sync_view_button_icons()
        self.flow_dag_widget.set_language(self.locale.language)
        self.refresh_runs_button.setText(self.locale.text("button.refresh_runs"))
        self.restore_run_button.setText(self.locale.text("button.restore_run"))
        self.restore_run_button.setToolTip(self.locale.text("tooltip.restore_run"))
        self.screen_button.setText(self.locale.text("button.screen"))
        self.evaluate_selected_button.setText(self.locale.text("button.evaluate_selected"))
        self.evaluate_all_button.setText(self.locale.text("button.evaluate_all"))
        self.report_button.setText(self.locale.text("button.report"))
        self.reset_button.setText(self.locale.text("button.reset"))
        self.primary_header.setText(self.locale.text("section.primary"))
        self.utility_header.setText(self.locale.text("section.utility"))
        self.stats_header.setText(self.locale.text("section.session"))
        self.log_header.setText(self.locale.text("section.runtime_log"))
        self.agent_header.setText(self.locale.text("section.agents"))
        self.queue_header.setText(self.locale.text("section.queue"))
        self.knowledge_status_header.setText(self.locale.text("section.knowledge_status"))
        self.workbench_header.setText(self.locale.text("section.workbench"))
        self.dialog_header.setText(self.locale.text("section.dialog"))
        self.details_header.setText(self.locale.text("section.details"))
        tab_texts = [
            self.locale.text("tab.candidates"),
            self.locale.text("tab.abaqus"),
            self.locale.text("tab.trace"),
            self.locale.text("tab.report"),
        ]
        for index, label in enumerate(tab_texts):
            self.tabs.setTabText(index, label)
        self.candidate_widget.set_language(self.locale.language)
        self.abaqus_widget.set_language(self.locale.language)
        self.live_result_view.set_language(self.locale.language, self.locale.text("live_view.empty"))
        self.task_config_widget.set_language(self.locale.language)
        if not self.session.task:
            self.task_browser.setHtml(self._initial_task_html())
            self.status_label.setText(self.locale.text("status.waiting"))
        self._update_overview_cards()
        self._refresh_run_selector()

    def _apply_chat_empty_state(self) -> None:
        self.chat_widget.set_empty_state(
            title=self.locale.text("chat.empty.title"),
            user_prompt=self.locale.text("chat.empty.user_prompt"),
            agent_title=self.locale.text("chat.empty.agent_title"),
            agent_body=self.locale.text("chat.empty.agent_body"),
            tool_title=self.locale.text("chat.empty.tool_title"),
            tool_body=self.locale.text("chat.empty.tool_body"),
            evidence_a=self.locale.text("chat.empty.evidence_a"),
            evidence_b=self.locale.text("chat.empty.evidence_b"),
        )

    def _set_busy(self, busy: bool, status_text: str) -> None:
        self.status_label.setText(self.locale.text("status.busy", status=status_text))
        self.generate_button.setEnabled(not busy)
        self.input_line.setEnabled(not busy)
        self.run_selector.setEnabled(not busy)
        self.confirm_yes_button.setEnabled(not busy and self.session.pending_confirmation is not None)
        self.confirm_no_button.setEnabled(not busy and self.session.pending_confirmation is not None)
        for button in [
            self.example_button,
            self.trace_button,
            self.refresh_button,
            self.open_report_button,
            self.export_data_button,
            self.reset_view_button,
            self.fit_view_button,
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
        self.export_data_button.setEnabled(
            bool(self.session.task or self.session.candidates or self.session.results_by_session_id or self.session.report)
        )
        self.refresh_runs_button.setEnabled(True)
        self.restore_run_button.setEnabled(bool(self.run_selector.currentData()))
        self._update_overview_cards()

    def _update_overview_cards(self) -> None:
        generated_count = len(self.session.candidates)
        pending_count = len(self._pending_candidates(self.session.current_candidates)) if self.session.current_candidates else 0
        passed_count = sum(1 for result in self.session.results_by_session_id.values() if result.get("verdict") == "通过")
        candidate_pool_target = requested_candidate_pool_size(self.session.task) if self.session.task else 0
        requested_top_k = requested_screen_top_k(self.session.task) if self.session.task else 0
        def metric_html(label: str, value: str) -> str:
            light_theme = resolve_theme(self.locale.theme) == "light"
            value_color = "#172033" if light_theme else "#e5edf7"
            label_color = "#475569" if light_theme else "#94a3b8"
            return (
                f"<span style='color:{label_color};font-size:12px;'>"
                f"{label}</span><br>"
                f"<span style='color:{value_color};font-size:22px;font-weight:800;'>"
                f"{value}</span>"
            )

        if self.locale.language == "en":
            self.stage_card.setText(metric_html("Stage", self.session.stage or "idle"))
            self.candidate_card.setText(
                metric_html("Candidate Pool", f"{generated_count} / {candidate_pool_target}")
                if self.session.task
                else metric_html("Candidate Pool", "0")
            )
            self.pending_card.setText(
                metric_html("Pending FEM", f"{pending_count} / {requested_top_k}")
                if self.session.task
                else metric_html("Pending FEM", "0")
            )
            self.pass_card.setText(metric_html("Passed", str(passed_count)))
        else:
            self.stage_card.setText(metric_html("当前阶段", self.session.stage or "idle"))
            self.candidate_card.setText(
                metric_html("候选池", f"{generated_count} / {candidate_pool_target}")
                if self.session.task
                else metric_html("候选池", "0")
            )
            self.pending_card.setText(
                metric_html("待 FEM 校核", f"{pending_count} / {requested_top_k}")
                if self.session.task
                else metric_html("待 FEM 校核", "0")
            )
            self.pass_card.setText(metric_html("通过", str(passed_count)))
        self._update_runtime_panel()

    def _stage_progress(self) -> int:
        if not self.session.task:
            return 0
        if self.session.stage == "completed":
            return 100
        if self.session.report:
            return 95
        if self.session.pending_confirmation == "export_report" or self.session.results_by_session_id:
            return 78
        if self.session.pending_confirmation == "fem_evaluation" or self.session.screened_candidates:
            return 56
        if self.session.pending_confirmation == "screen_candidates" or self.session.candidates:
            return 34
        if self.session.task:
            return 18
        return 0

    def _agent_state_map(self) -> dict[str, str]:
        states = {agent_name: "waiting" for agent_name, _ in self.AGENT_DESCRIPTIONS}
        stage = self.session.stage or "idle"
        if self.session.task or self.session.candidates or stage not in {"idle", ""}:
            states["ORCHESTRATOR"] = "done"
        if stage in {"parsing"}:
            states["ORCHESTRATOR"] = "active"
        if self.session.candidates:
            states["CANDIDATE_GEN"] = "done"
        if stage in {"generate_candidates", "candidate_generation_started"}:
            states["CANDIDATE_GEN"] = "active"
        if self.session.screened_candidates:
            states["SCREENER"] = "done"
        elif self.session.pending_confirmation == "screen_candidates":
            states["SCREENER"] = "active"
        if self.session.results_by_session_id:
            states["FEM_AGENT"] = "done"
        elif self.session.pending_confirmation == "fem_evaluation":
            states["FEM_AGENT"] = "active"
        if self.session.knowledge_updates:
            states["KNOWLEDGE_AGENT"] = "done"
        elif self.session.results_by_session_id:
            states["KNOWLEDGE_AGENT"] = "active"
        if self.session.report:
            states["REPORT_GEN"] = "done"
        elif self.session.pending_confirmation == "export_report":
            states["REPORT_GEN"] = "active"
        if stage == "completed":
            for key in states:
                states[key] = "done"
        failed_agent = self._failed_agent_for_stage(stage)
        if failed_agent:
            states[failed_agent] = "failed"
        for agent_name, state in self.runtime_agent_states.items():
            if agent_name in states:
                states[agent_name] = state
        return states

    def _ui_agent_for_runtime_stage(self, runtime_stage: str, runtime_agent: str = "") -> str:
        stage = runtime_stage or ""
        agent = runtime_agent or ""
        if stage.startswith("parse_task") or agent in {"ORCHESTRATOR", "parse_task"}:
            return "ORCHESTRATOR"
        if stage.startswith("generate_candidates") or agent in {"CANDIDATE_GEN", "generate_candidates"}:
            return "CANDIDATE_GEN"
        if stage.startswith("screen_candidates") or agent in {"SCREENER", "screen_candidates"}:
            return "SCREENER"
        if stage.startswith("evaluate_candidates") or agent in {"FEM_AGENT", "SimulationQueue", "evaluate_candidates"}:
            return "FEM_AGENT"
        if stage.startswith("persist_knowledge") or agent in {"KNOWLEDGE_AGENT", "persist_knowledge"}:
            return "KNOWLEDGE_AGENT"
        if stage.startswith("generate_report") or agent in {"REPORT_GEN", "generate_report"}:
            return "REPORT_GEN"
        return "ORCHESTRATOR"

    def _handle_runtime_state_event(self, runtime_type: str, runtime_stage: str, runtime_agent: str) -> None:
        ui_agent = self._ui_agent_for_runtime_stage(runtime_stage, runtime_agent)
        if runtime_type in {"node_started", "tool_started", "simulation_job_started", "simulation_job_queued"}:
            self.runtime_agent_states[ui_agent] = "active"
            self.runtime_stage_text = runtime_stage or runtime_type
        elif runtime_type in {"node_completed", "tool_completed", "simulation_job_completed"}:
            self.runtime_agent_states[ui_agent] = "done"
            self.runtime_stage_text = runtime_stage or runtime_type
        elif runtime_type in {"node_failed", "tool_failed", "simulation_job_failed"}:
            self.runtime_agent_states[ui_agent] = "failed"
            self.runtime_stage_text = runtime_stage or runtime_type
        self._update_runtime_panel()

    def _failed_agent_for_stage(self, stage: str) -> str | None:
        if stage == "failed":
            return "ORCHESTRATOR"
        if not stage.endswith("_failed"):
            return None
        if stage.startswith("parse_task"):
            return "ORCHESTRATOR"
        if stage.startswith("generate_candidates"):
            return "CANDIDATE_GEN"
        if stage.startswith("screen_candidates"):
            return "SCREENER"
        if stage.startswith("evaluate_candidates"):
            return "FEM_AGENT"
        if stage.startswith("persist_knowledge"):
            return "KNOWLEDGE_AGENT"
        if stage.startswith("generate_report"):
            return "REPORT_GEN"
        return "ORCHESTRATOR"

    def _agent_status_label(self, state: str) -> str:
        key = {
            "done": "agent.done",
            "active": "agent.active",
            "failed": "agent.failed",
            "waiting": "agent.waiting",
        }.get(state, "agent.waiting")
        return self.locale.text(key)

    def _agent_state_color(self, state: str) -> str:
        if state == "done":
            return "#34d399"
        if state == "active":
            return "#f59e0b"
        return "#64748b"

    def _update_runtime_panel(self) -> None:
        state_map = self._agent_state_map()
        for agent_name, description_key in self.AGENT_DESCRIPTIONS:
            card = self.agent_cards.get(agent_name)
            if card is None:
                continue
            state = state_map.get(agent_name, "waiting")
            card.set_content(
                agent_name,
                state,
                self._agent_status_label(state),
                self.locale.text(description_key),
            )

        percent = self._stage_progress()
        self.queue_progress.setValue(percent)
        self.queue_progress.setVisible(bool(self.session.task))
        if self.session.task:
            self.queue_label.setText(
                self.locale.text("queue.progress", percent=percent)
                + "\n"
                + self.locale.text("queue.stage", stage=self.session.stage or "idle")
            )
        else:
            self.queue_label.setText(self.locale.text("queue.idle"))

        runs = self.workflow_event_store.list_runs(limit=500)
        case_dir = PROJECT_ROOT / "data" / "cases"
        cases = len(list(case_dir.glob("CASE_*.json"))) if case_dir.exists() else 0
        knowledge_payload = self.knowledge_widget.knowledge_base.status()
        knowledge_status = "ready" if knowledge_payload.get("ready") else "pending"
        self.knowledge_status_label.setText(
            self.locale.text("knowledge.status", status=knowledge_status, cases=cases, runs=len(runs))
            + "\n"
            + f"文档 {knowledge_payload.get('document_count', 0)} · "
            + f"Chunks {knowledge_payload.get('rag_chunk_count', 0)} · "
            + f"Relations {knowledge_payload.get('kg_relation_count', 0)}"
        )
        active_stage = self.runtime_stage_text or self.session.stage
        stage_text = (
            f"{self.locale.text('agent.active')} · {active_stage}"
            if self.session.task or self.runtime_stage_text
            else self.locale.text("queue.idle")
        )
        self.flow_dag_widget.update_state(state_map, stage_text)

    def _run_action(self, action: str, payload: dict, status_text: str) -> None:
        self.runtime_agent_states = {}
        self.runtime_stage_text = ""
        self._set_busy(True, status_text)
        self.worker_thread = QThread(self)
        worker_payload = dict(payload)
        worker_payload.setdefault("workflow_db_path", str(self.workflow_event_store.db_path))
        self.worker = PipelineWorker(action, worker_payload)
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
            self.log_widget.append_log("SYSTEM", f"运行状态恢复失败：{run_id} | {exc}")
            self.monitor_log_widget.append_log("SYSTEM", f"运行状态恢复失败：{run_id} | {exc}")
            return

        self.chat_widget.clear()
        self.log_widget.clear()
        self.monitor_log_widget.clear()
        self.session = self._session_from_workflow_state(snapshot)
        self.input_line.setText(self.session.instruction)
        self._apply_session(self.session)
        self.tabs.setCurrentWidget(self.result_trace_widget)
        self.chat_widget.add_message(
            "SYSTEM",
            f"已恢复运行状态：{run_id}，当前阶段：{self.session.stage}",
        )
        self.log_widget.append_log("SYSTEM", f"已恢复运行状态：{run_id}")
        self.monitor_log_widget.append_log("SYSTEM", f"已恢复运行状态：{run_id}")
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
        self._refresh_live_view()
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
        self._refresh_live_view()
        self._update_overview_cards()

    def _refresh_live_view(self) -> None:
        results = list(self.session.results_by_session_id.values())
        if results:
            self.live_result_view.show_mode_shape(results[0])
            return
        if self.session.current_candidates:
            self.live_result_view.show_candidate(self.session.current_candidates[0])
            return
        self.live_result_view.show_reference_hull()

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

    def _export_session_data(self) -> None:
        if not (self.session.task or self.session.candidates or self.session.results_by_session_id or self.session.report):
            self.chat_widget.add_message("SYSTEM", self.locale.text("message.no_export_data"))
            return
        json_path, csv_path = self._write_session_export()
        self.chat_widget.add_message(
            "SYSTEM",
            self.locale.text("message.export_data", json_path=json_path, csv_path=csv_path),
        )
        self.log_widget.append_log("SYSTEM", f"数据导出完成：{json_path} / {csv_path}")
        self.monitor_log_widget.append_log("SYSTEM", f"数据导出完成：{json_path} / {csv_path}")
        self._update_button_states()

    def _session_export_id(self) -> str:
        raw = self.session.workflow_run_id or (self.session.task or {}).get("task_id") or "manual"
        safe = "".join(char if char.isalnum() or char in {"_", "-"} else "_" for char in str(raw))
        return safe or "manual"

    def _session_export_payload(self) -> dict:
        return {
            "exported_at": datetime.utcnow().isoformat(),
            "workflow_run_id": self.session.workflow_run_id,
            "instruction": self.session.instruction,
            "stage": self.session.stage,
            "pending_confirmation": self.session.pending_confirmation,
            "task": self.session.task,
            "candidates": self.session.candidates,
            "screened_candidates": self.session.screened_candidates,
            "evaluated_candidates": self.session.evaluated_candidates,
            "results": list(self.session.results_by_session_id.values()),
            "knowledge_updates": self.session.knowledge_updates,
            "report": self.session.report,
        }

    def _trace_export_rows(self) -> list[dict]:
        results_by_session = {
            str(result.get("session_candidate_id") or result.get("candidate_id") or ""): result
            for result in self.session.results_by_session_id.values()
        }
        updates_by_session: dict[str, dict] = {}
        updates_by_candidate: dict[str, dict] = {}
        for update in self.session.knowledge_updates:
            if update.get("session_candidate_id"):
                updates_by_session[str(update.get("session_candidate_id"))] = update
            if update.get("candidate_id"):
                updates_by_candidate[str(update.get("candidate_id"))] = update

        rows: list[dict] = []
        candidate_pool = self.session.candidates or self.session.current_candidates
        for candidate in candidate_pool:
            session_id = str(candidate.get("candidate_id") or "")
            result = results_by_session.get(session_id) or {}
            formal_id = str(result.get("candidate_id") or candidate.get("persistent_candidate_id") or "")
            update = updates_by_session.get(session_id) or updates_by_candidate.get(formal_id) or {}
            rows.append(
                {
                    "session_candidate_id": session_id,
                    "formal_candidate_id": formal_id,
                    "display_name": candidate.get("display_name") or session_id,
                    "source": candidate.get("source") or "",
                    "surrogate_ultimate_pressure_MPa": candidate.get("surrogate_ultimate_pressure_MPa"),
                    "asme_linear_buckling_pressure_MPa": candidate.get("asme_linear_buckling_pressure_MPa"),
                    "surrogate_PBIPF_MPa": candidate.get("surrogate_PBIPF_MPa"),
                    "rank_score": candidate.get("rank_score"),
                    "fem_ultimate_pressure_MPa": result.get("ultimate_pressure_MPa"),
                    "fem_linear_buckling_pressure_MPa": result.get("linear_buckling_pressure_MPa"),
                    "fem_status": result.get("status") or "",
                    "verdict": result.get("verdict") or "",
                    "case_id": update.get("case_id") or "",
                    "knowledge_status": update.get("status") or "",
                }
            )
        return rows

    def _write_session_export(self) -> tuple[Path, Path]:
        RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        export_id = self._session_export_id()
        json_path = RESULTS_DIR / f"session_export_{export_id}.json"
        csv_path = RESULTS_DIR / f"session_trace_{export_id}.csv"
        payload = self._session_export_payload()
        json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        rows = self._trace_export_rows()
        fieldnames = [
            "session_candidate_id",
            "formal_candidate_id",
            "display_name",
            "source",
            "surrogate_ultimate_pressure_MPa",
            "asme_linear_buckling_pressure_MPa",
            "surrogate_PBIPF_MPa",
            "rank_score",
            "fem_ultimate_pressure_MPa",
            "fem_linear_buckling_pressure_MPa",
            "fem_status",
            "verdict",
            "case_id",
            "knowledge_status",
        ]
        with csv_path.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        return json_path, csv_path

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
        self.last_llm_trace_payload = None
        self.runtime_agent_states = {}
        self.runtime_stage_text = ""
        self.chat_widget.clear()
        self.log_widget.clear()
        self.task_browser.setHtml(self._initial_task_html())
        self.candidate_widget.update_candidates([])
        self.abaqus_widget.update_results([])
        self.result_trace_widget.update_trace([])
        self.candidate_widget.reset_view()
        self.abaqus_widget.reset_view()
        self.live_result_view.reset_plotter(self.locale.text("live_view.empty"))
        self.live_result_view.show_reference_hull()
        self.result_trace_widget.reset_view()
        self.report_widget.reset_view()
        self.task_config_widget.reset_view()
        self.workflow_widget.reset_view()
        self.model_status_label.set_state(self.locale.text("model.current"), "success")
        self.flow_dag_widget.update_state(self._agent_state_map(), self.locale.text("queue.idle"))
        self.knowledge_widget.refresh(load_evidence=False)
        self.status_label.setText(self.locale.text("status.waiting"))
        self.input_line.clear()
        self._update_overview_cards()
        self._update_button_states()

    def _update_model_status_from_llm_trace(self, payload: dict, emit_log: bool = True) -> None:
        selected_model = str(payload.get("selected_model") or "").strip()
        selected_backend = str(payload.get("selected_backend") or "").strip()
        fallback_used = bool(payload.get("fallback_used"))
        trace = payload.get("trace")
        attempts = len(trace) if isinstance(trace, list) else 0
        backend_label = selected_backend or "-"

        if selected_model:
            if fallback_used:
                self.model_status_label.set_state(
                    self.locale.text("model.fallback_active", model=selected_model),
                    "warning",
                )
                log_text = self.locale.text(
                    "model.fallback_log",
                    model=selected_model,
                    backend=backend_label,
                    attempts=attempts,
                )
            else:
                self.model_status_label.set_state(
                    self.locale.text("model.primary_active", model=selected_model),
                    "success",
                )
                log_text = self.locale.text(
                    "model.primary_log",
                    model=selected_model,
                    backend=backend_label,
                    attempts=attempts,
                )
        else:
            self.model_status_label.set_state(self.locale.text("model.failed"), "failed")
            log_text = self.locale.text("model.failed_log", attempts=attempts)

        if emit_log:
            self.log_widget.append_log("LLM", log_text)
            self.monitor_log_widget.append_log("LLM", log_text)

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

        if event_type == "workflow_runtime_event":
            runtime_agent = str(payload.get("runtime_agent") or sender_label)
            runtime_type = str(payload.get("runtime_event_type") or "runtime")
            runtime_stage = str(payload.get("runtime_stage") or "")
            record = payload.get("record") if isinstance(payload.get("record"), dict) else {}
            run_id = str(record.get("run_id") or self.session.workflow_run_id or "")
            suffix = f" @ {runtime_stage}" if runtime_stage else ""
            if run_id and not self.session.workflow_run_id:
                self.session.workflow_run_id = run_id
            self._handle_runtime_state_event(runtime_type, runtime_stage, runtime_agent)
            self.log_widget.append_log(runtime_agent, f"[{runtime_type}{suffix}] {message}")
            self.monitor_log_widget.append_log(runtime_agent, f"[{runtime_type}{suffix}] {message}")
            self._refresh_run_selector()
            if run_id:
                self.workflow_widget.refresh(run_id, runtime_stage, self.session.pending_confirmation)
            return

        self.chat_widget.add_message(sender_label, message)
        self.log_widget.append_log(sender_label, f"[{event_type}] {message}")
        self.monitor_log_widget.append_log(sender_label, f"[{event_type}] {message}")

        if event_type == "llm_call_trace":
            self.last_llm_trace_payload = dict(payload)
            self._update_model_status_from_llm_trace(payload)

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
        self.session.stage = "failed"
        self.session.pending_confirmation = None
        self.chat_widget.add_message("SYSTEM", f"执行失败：{error_message}")
        self.log_widget.append_log("SYSTEM", error_message)
        self.monitor_log_widget.append_log("SYSTEM", error_message)
        self.status_label.setText(self.locale.text("status.busy", status=f"failed: {error_message}"))
        self._update_overview_cards()
        self._update_runtime_panel()
        self._update_button_states()

    def _initial_task_html(self) -> str:
        return (
            f"<h3>{self.locale.text('task.initial.title')}</h3>"
            f"<p>{self.locale.text('task.initial.body')}</p>"
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
            self._save_window_layout()
            self.candidate_widget.reset_view()
            self.abaqus_widget.reset_view()
            self.live_result_view.reset_plotter()
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

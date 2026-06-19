"""PyQt6 主界面。"""

from __future__ import annotations

import csv
import json
import os
import sys
from datetime import datetime
from dataclasses import dataclass, field
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

UI_LAYOUT_VERSION = 10

from PyQt6 import sip
from PyQt6.QtCore import QObject, QRectF, QSettings, QSize, Qt, QThread, QUrl, pyqtSignal
from PyQt6.QtGui import QColor, QCloseEvent, QDesktopServices, QIcon, QPainter, QPen, QPixmap
from PyQt6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QComboBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSplitter,
    QStackedWidget,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from agents.orchestrator import OrchestratorAgent
from core.config_loader import load_app_config, load_llm_config
from core.conversation_flow import ConversationFlowController, ConversationState
from core.paths import ASSETS_DIR, CASE_LIBRARY_DIR, CASES_DIR, CONFIG_DIR, RESULTS_DIR, ensure_project_dirs
from core.task_contract import (
    describe_boundary_conditions,
    describe_load_conditions,
    effective_screen_top_k,
    requested_candidate_pool_size,
    requested_screen_top_k,
    task_payload_from_request,
)
from gui.candidate_widget import CandidateWidget
from gui.chat_widget import ChatWidget
from gui.i18n import LANGUAGE_OPTIONS, THEME_OPTIONS, LocaleManager
from gui.interactive_view import InteractivePlotWidget
from gui.knowledge_widget import KnowledgeWidget
from gui.log_widget import LogWidget
from gui.monitor_widget import MonitorDashboardWidget
from gui.result_trace_widget import ResultTraceWidget
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

    @property
    def display_candidates(self) -> list[dict]:
        return self.candidates or self.current_candidates

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
                self.finished.emit(
                    self.action,
                    {
                        "screened_candidates": screened,
                        "ranked_candidates": getattr(orchestrator, "last_ranked_candidates", []),
                    },
                )
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
                report = orchestrator.generate_report(
                    task,
                    results,
                    candidates,
                    report_kind=str(self.payload.get("report_kind") or "all"),
                    output_dir=self.payload.get("output_dir"),
                )
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


class CenterStackedWidget(QStackedWidget):
    """中心页面栈只向主窗口暴露可控的最小尺寸。"""

    MAX_MINIMUM_WIDTH = 600
    MAX_MINIMUM_HEIGHT = 720

    def minimumSizeHint(self) -> QSize:
        current = self.currentWidget()
        if current is None:
            return QSize(0, 0)
        hint = current.minimumSizeHint()
        return QSize(
            min(hint.width(), self.MAX_MINIMUM_WIDTH),
            min(hint.height(), self.MAX_MINIMUM_HEIGHT),
        )

    def sizeHint(self) -> QSize:
        current = self.currentWidget()
        if current is None:
            return super().sizeHint()
        return current.sizeHint()


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
        self._resize_to_available_work_area()
        self.ui_state_settings = QSettings("CSAgent", "Workbench")
        self.session = PipelineSession()
        self.worker_thread: QThread | None = None
        self.worker: PipelineWorker | None = None
        self.workflow_event_store = WorkflowEventStore()
        self.last_llm_trace_payload: dict | None = None
        self.runtime_agent_states: dict[str, str] = {}
        self.runtime_stage_text = ""
        self.report_output_dir: Path | None = None

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
        self.language_selector.setObjectName("settingsInput")
        for language, label in LANGUAGE_OPTIONS.items():
            self.language_selector.addItem(label, language)
        current_language_index = self.language_selector.findData(self.locale.language)
        if current_language_index >= 0:
            self.language_selector.setCurrentIndex(current_language_index)
        self.theme_selector = QComboBox()
        self.theme_selector.setObjectName("settingsInput")
        for theme, label in THEME_OPTIONS[self.locale.language].items():
            self.theme_selector.addItem(label, theme)
        current_theme_index = self.theme_selector.findData(self.locale.theme)
        if current_theme_index >= 0:
            self.theme_selector.setCurrentIndex(current_theme_index)

        self.chat_widget = ChatWidget()
        self.chat_widget.setMinimumHeight(220)
        self.chat_widget.set_empty_text(self.locale.text("chat.empty"))
        self._apply_chat_empty_state()
        self.status_label = QLabel(self.locale.text("status.waiting"))
        self.status_label.setWordWrap(True)
        self.status_label.setObjectName("chatStatus")

        self.input_line = QLineEdit()
        self.input_line.setPlaceholderText(self.locale.text("input.placeholder"))
        self.input_line.setFixedHeight(44)
        self.input_line.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        self.generate_button = QPushButton(self.locale.text("button.start"))
        self.confirm_yes_button = QPushButton(self.locale.text("button.confirm"))
        self.confirm_no_button = QPushButton(self.locale.text("button.pause"))
        self.generate_button.setFixedWidth(56)
        self.confirm_yes_button.setFixedWidth(88)
        self.confirm_no_button.setFixedWidth(88)
        self.trace_button = QPushButton(self.locale.text("button.view_trace"))
        self.trace_button.setObjectName("traceLinkButton")
        self.trace_button.setMinimumWidth(132)

        self.example_button = QPushButton(self.locale.text("button.example"))
        self.example_button.setToolTip(self.locale.text("button.example"))
        self.refresh_button = QPushButton(self.locale.text("button.refresh_knowledge"))
        self.open_report_button = QPushButton(self.locale.text("button.open_report"))
        self.export_data_button = QPushButton(self.locale.text("button.export_data"))
        self.report_type_selector = QComboBox()
        self._populate_report_type_selector()
        self.report_type_selector.setMinimumHeight(42)
        self.report_dir_button = QPushButton(self.locale.text("button.report_dir"))
        self.report_dir_button.setToolTip(self.locale.text("tooltip.report_dir"))
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
        for metric_card in [self.stage_card, self.candidate_card, self.pending_card, self.pass_card]:
            metric_card.setFixedHeight(64)
            metric_card.setWordWrap(True)
            metric_card.setTextFormat(Qt.TextFormat.RichText)
            metric_card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            metric_card.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
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
        self.run_audit_header = QLabel(self.locale.text("section.run_audit"))
        self.run_audit_header.setObjectName("sectionTitle")
        self.workbench_header = QLabel(self.locale.text("section.workbench"))
        self.workbench_header.setObjectName("sectionTitle")
        self.dialog_header = QLabel(self.locale.text("section.dialog"))
        self.dialog_header.setObjectName("sectionTitle")
        self.details_header = QLabel(self.locale.text("section.details"))
        self.details_header.setObjectName("sectionTitle")
        for header_label in [
            self.stats_header,
            self.log_header,
            self.agent_header,
            self.queue_header,
            self.knowledge_status_header,
            self.run_audit_header,
            self.workbench_header,
            self.dialog_header,
            self.details_header,
        ]:
            header_label.setMinimumWidth(header_label.fontMetrics().horizontalAdvance(header_label.text()) + 18)
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
        self.run_audit_label = QLabel("")
        self.run_audit_label.setObjectName("statusLabel")
        self.run_audit_label.setWordWrap(True)

        self.workbench_candidate_widget = CandidateWidget(language=self.locale.language)
        self.workbench_candidate_widget.setMinimumHeight(270)
        self.knowledge_widget = KnowledgeWidget()
        self.result_trace_widget = ResultTraceWidget()
        self.log_widget = LogWidget()
        self.monitor_log_widget = LogWidget()
        self.monitor_dashboard_widget = MonitorDashboardWidget()
        self.workflow_widget = WorkflowWidget(event_store=self.workflow_event_store)
        self.workflow_widget.setMinimumHeight(300)
        self.flow_dag_widget = FlowDagWidget()
        self.live_result_view = InteractivePlotWidget(
            self.locale.text("live_view.empty"),
            language=self.locale.language,
        )
        self.live_result_view.setMinimumHeight(210)
        self.live_result_view.setMaximumHeight(260)
        self.log_widget.setMinimumHeight(128)

        self._build_layout()
        self._apply_styles()
        self._connect_signals()
        self._restore_window_layout()
        self._update_button_states()
        self._update_overview_cards()
        self._refresh_run_selector()
        self.knowledge_widget.refresh(load_evidence=False)
        self._refresh_knowledge_sidebar()

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

    def _populate_report_type_selector(self) -> None:
        current_kind = None
        if hasattr(self, "report_type_selector"):
            current_kind = self.report_type_selector.currentData()
            self.report_type_selector.blockSignals(True)
            self.report_type_selector.clear()
        report_options = [
            ("report.kind.all", "all"),
            ("report.kind.overall", "overall"),
            ("report.kind.fem", "fem"),
            ("report.kind.design_solution", "design_solution"),
        ]
        for text_key, kind in report_options:
            self.report_type_selector.addItem(self.locale.text(text_key), kind)
        if current_kind:
            index = self.report_type_selector.findData(current_kind)
            if index >= 0:
                self.report_type_selector.setCurrentIndex(index)
        self.report_type_selector.blockSignals(False)

    def _build_layout(self) -> None:
        input_action_layout = QHBoxLayout()
        input_action_layout.setContentsMargins(0, 0, 0, 0)
        input_action_layout.setSpacing(8)
        input_action_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        self.example_button.setText("+")
        self.example_button.setFixedSize(44, 44)
        input_action_layout.addWidget(self.example_button, 0, Qt.AlignmentFlag.AlignVCenter)
        input_action_layout.addWidget(self.input_line, 1, Qt.AlignmentFlag.AlignVCenter)
        input_action_layout.addWidget(self.generate_button, 0, Qt.AlignmentFlag.AlignVCenter)
        input_action_layout.addWidget(self.confirm_yes_button, 0, Qt.AlignmentFlag.AlignVCenter)
        input_action_layout.addWidget(self.confirm_no_button, 0, Qt.AlignmentFlag.AlignVCenter)
        self.input_action_layout = input_action_layout

        stats_layout = QGridLayout()
        stats_layout.setHorizontalSpacing(10)
        stats_layout.setVerticalSpacing(10)
        stats_layout.addWidget(self.stage_card, 0, 0)
        stats_layout.addWidget(self.candidate_card, 0, 1)
        stats_layout.addWidget(self.pending_card, 1, 0)
        stats_layout.addWidget(self.pass_card, 1, 1)
        stats_layout.setColumnMinimumWidth(0, 0)
        stats_layout.setColumnMinimumWidth(1, 0)
        stats_layout.setColumnStretch(0, 1)
        stats_layout.setColumnStretch(1, 1)
        stats_layout.setRowMinimumHeight(0, 64)
        stats_layout.setRowMinimumHeight(1, 64)
        stats_layout.setRowStretch(0, 0)
        stats_layout.setRowStretch(1, 0)

        agent_layout = QVBoxLayout()
        agent_layout.setContentsMargins(14, 14, 12, 10)
        agent_layout.setSpacing(11)
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

        queue_layout = QVBoxLayout()
        queue_layout.setContentsMargins(14, 8, 12, 14)
        queue_layout.setSpacing(10)
        queue_layout.addWidget(self.queue_header)
        queue_layout.addWidget(self.queue_progress)
        queue_layout.addWidget(self.queue_label)
        queue_layout.addWidget(self.knowledge_status_header)
        queue_layout.addWidget(self.knowledge_status_label)
        queue_layout.addWidget(self.run_audit_header)
        queue_layout.addWidget(self.run_audit_label)

        chat_panel = QWidget()
        chat_panel.setObjectName("conversationPanel")
        chat_layout = QVBoxLayout(chat_panel)
        chat_layout.setContentsMargins(10, 10, 10, 10)
        chat_layout.setSpacing(8)
        chat_title_layout = QHBoxLayout()
        chat_title_layout.setSpacing(10)
        chat_title_layout.addWidget(self.dialog_header)
        chat_title_layout.addStretch(1)
        chat_title_layout.addWidget(self.trace_button)
        chat_layout.addLayout(chat_title_layout)
        chat_layout.addWidget(self.chat_widget, 1)
        chat_layout.addWidget(self.status_label)
        chat_layout.addLayout(input_action_layout)

        workbench_splitter = QSplitter(Qt.Orientation.Vertical)
        workbench_splitter.addWidget(self.workbench_candidate_widget)
        workbench_splitter.addWidget(chat_panel)
        workbench_splitter.setSizes([430, 455])
        self.workbench_splitter = workbench_splitter

        workbench_page = QWidget()
        workbench_page.setObjectName("centerWorkbench")
        workbench_layout = QVBoxLayout(workbench_page)
        workbench_layout.setContentsMargins(0, 0, 0, 0)
        workbench_layout.addWidget(workbench_splitter)

        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(12, 14, 12, 14)
        right_layout.setSpacing(8)
        live_header_layout = QHBoxLayout()
        live_header_layout.setContentsMargins(0, 0, 0, 0)
        live_header_layout.setSpacing(8)
        live_header_layout.addWidget(self.details_header, 1)
        live_header_layout.addWidget(self.reset_view_button)
        live_header_layout.addWidget(self.fit_view_button)
        right_layout.addLayout(live_header_layout)
        right_layout.addWidget(self.live_result_view, 1)
        right_layout.addWidget(self.stats_header)
        right_layout.addLayout(stats_layout)
        action_grid = QGridLayout()
        action_grid.setHorizontalSpacing(8)
        action_grid.setVerticalSpacing(8)
        action_grid.addWidget(self.screen_button, 0, 0)
        action_grid.addWidget(self.evaluate_selected_button, 0, 1)
        action_grid.addWidget(self.evaluate_all_button, 1, 0)
        action_grid.addWidget(self.reset_button, 1, 1)
        action_grid.setColumnStretch(0, 1)
        action_grid.setColumnStretch(1, 1)
        right_layout.addLayout(action_grid)
        right_layout.addWidget(self.log_header)
        right_layout.addWidget(self.log_widget, 1)
        right_layout.addWidget(self.report_type_selector)
        right_layout.addWidget(self.report_dir_button)
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
        workbench_left_layout = QVBoxLayout(workbench_left)
        workbench_left_layout.setContentsMargins(0, 0, 0, 0)
        workbench_left_layout.setSpacing(0)
        workbench_left_content = QWidget()
        left_layout = QVBoxLayout(workbench_left_content)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(16)
        left_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        agent_widget = QWidget()
        agent_widget.setLayout(agent_layout)
        agent_widget.setMinimumHeight(480)
        agent_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        queue_widget = QWidget()
        queue_widget.setLayout(queue_layout)
        queue_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        left_layout.addWidget(agent_widget)
        left_layout.addWidget(queue_widget)
        workbench_left_scroll = QScrollArea()
        workbench_left_scroll.setObjectName("railScroll")
        workbench_left_scroll.setFrameShape(QFrame.Shape.NoFrame)
        workbench_left_scroll.setWidgetResizable(True)
        workbench_left_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        workbench_left_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        workbench_left_scroll.setWidget(workbench_left_content)
        workbench_left_layout.addWidget(workbench_left_scroll)
        workbench_left.setMinimumWidth(248)
        workbench_left.setMaximumWidth(286)

        knowledge_left = self._build_knowledge_left_page()
        monitor_left = self._build_monitor_left_page()
        settings_left = self._build_settings_left_page()

        workbench_right_content = QWidget()
        workbench_right_content.setObjectName("resultRailContent")
        workbench_right_content.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        workbench_right_content.setLayout(right_layout)
        workbench_right_scroll = QScrollArea()
        workbench_right_scroll.setObjectName("resultRail")
        workbench_right_scroll.setWidgetResizable(True)
        workbench_right_scroll.setFrameShape(QFrame.Shape.NoFrame)
        workbench_right_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        workbench_right_scroll.setWidget(workbench_right_content)
        self.workbench_right_scroll = workbench_right_scroll
        self.workbench_right_content = workbench_right_content

        workbench_right = QWidget()
        workbench_right.setObjectName("resultRailShell")
        workbench_right_layout = QVBoxLayout(workbench_right)
        workbench_right_layout.setContentsMargins(0, 0, 0, 0)
        workbench_right_layout.setSpacing(0)
        workbench_right_layout.addWidget(workbench_right_scroll)
        workbench_right.setMinimumWidth(330)
        workbench_right.setMaximumWidth(430)

        self.stack = CenterStackedWidget()
        self.stack.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Ignored)
        self.stack.addWidget(workbench_page)
        self.stack.addWidget(self.knowledge_widget)
        self.monitor_page = self._build_monitor_page()
        self.stack.addWidget(self.monitor_page)
        self.settings_page = self._build_settings_page()
        self.stack.addWidget(self.settings_page)

        self.left_stack = QStackedWidget()
        self.left_stack.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Ignored)
        self.left_stack.addWidget(workbench_left)
        self.left_stack.addWidget(knowledge_left)
        self.left_stack.addWidget(monitor_left)
        self.left_stack.addWidget(settings_left)
        self.left_stack.setMinimumWidth(248)
        self.left_stack.setMaximumWidth(286)

        self.right_stack = QStackedWidget()
        self.right_stack.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Ignored)
        self.right_stack.addWidget(workbench_right)
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
        main_splitter.setStretchFactor(0, 0)
        main_splitter.setStretchFactor(1, 1)
        main_splitter.setStretchFactor(2, 0)
        main_splitter.setSizes([270, 980, 370])
        self.main_splitter = main_splitter
        self.setCentralWidget(main_splitter)

    def _sync_main_splitter_sizes(self) -> None:
        if not hasattr(self, "main_splitter"):
            return
        total_width = max(0, self.main_splitter.width())
        if total_width <= 0:
            total_width = max(0, self.width())
        right_width = min(386, max(350, int(total_width * 0.24)))
        left_width = min(286, max(248, int(total_width * 0.18)))
        center_width = max(520, total_width - left_width - right_width)
        self.main_splitter.setSizes([left_width, center_width, right_width])

    def _sidebar_page(self, title: str, cards: list[tuple[str, str]], footer: str = "") -> QWidget:
        page = QWidget()
        page.setObjectName("agentRail")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(14, 14, 0, 14)
        layout.setSpacing(9)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        header = QLabel(title)
        header.setObjectName("sectionTitle")
        layout.addWidget(header)
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 12, 0)
        content_layout.setSpacing(9)
        content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        for primary, secondary in cards:
            card = QLabel(f"<b>{primary}</b><br>{secondary}")
            card.setObjectName("agentCard")
            card.setWordWrap(True)
            card.setProperty("state", "waiting")
            card.setMinimumHeight(56)
            card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
            content_layout.addWidget(card)
        if footer:
            footer_label = QLabel(footer)
            footer_label.setObjectName("statusLabel")
            footer_label.setWordWrap(True)
            footer_label.setMinimumHeight(58)
            footer_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
            content_layout.addWidget(footer_label)
        scroll = QScrollArea()
        scroll.setObjectName("railScroll")
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setWidget(content)
        layout.addWidget(scroll, 1)
        return page

    def _right_page(self, title: str, cards: list[tuple[str, str]], footer_buttons: list[QPushButton] | None = None) -> QWidget:
        page = QWidget()
        page.setObjectName("resultRail")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(14, 14, 0, 14)
        layout.setSpacing(9)
        header = QLabel(title)
        header.setObjectName("sectionTitle")
        layout.addWidget(header)
        for primary, secondary in cards:
            card = QLabel(f"<b>{primary}</b><br>{secondary}")
            card.setObjectName("statusLabel")
            card.setWordWrap(True)
            layout.addWidget(card)
        if footer_buttons:
            layout.addSpacing(8)
            for button in footer_buttons:
                layout.addWidget(button)
            layout.addStretch(1)
        else:
            layout.addStretch(1)
        return page

    def _build_knowledge_left_page(self) -> QWidget:
        page = QWidget()
        page.setObjectName("agentRail")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(14, 14, 0, 14)
        layout.setSpacing(8)

        header = QLabel("知识库 · CORPUS")
        header.setObjectName("sectionTitle")
        layout.addWidget(header)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 12, 0)
        content_layout.setSpacing(8)
        content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.knowledge_sidebar_labels: dict[str, QLabel] = {}
        for key, title, body in [
            ("merged", "合并知识库", "RAG/KG 总量等待刷新"),
            ("builtin", "系统资料", "默认工程知识等待载入"),
            ("runtime", "用户资料", "上传解析后的增量资料"),
            ("cases", "案例记忆", "会话与正式案例等待刷新"),
            ("retrieval", "检索验证", "文本块 + 图谱关系 + 溯源"),
            ("config", "分块参数", "chunk / overlap / top_k"),
        ]:
            card = QLabel(f"<b>{title}</b><br>{body}")
            card.setObjectName("agentCard")
            card.setWordWrap(True)
            card.setProperty("state", "waiting")
            card.setMinimumHeight(72)
            card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
            content_layout.addWidget(card)
            self.knowledge_sidebar_labels[key] = card

        category_header = QLabel("资料分层 · SOURCES")
        category_header.setObjectName("sectionTitle")
        content_layout.addWidget(category_header)
        for primary, secondary in [
            ("规范与手册", "设计准则 / 工艺约束"),
            ("论文与模型", "屈曲 / 后屈曲 / 代理模型"),
            ("试验与仿真", "压力试验 / FEM 结果"),
            ("项目知识", "案例记忆 / 运行审计"),
        ]:
            card = QLabel(f"<b>{primary}</b><br>{secondary}")
            card.setObjectName("statusLabel")
            card.setWordWrap(True)
            card.setMinimumHeight(50)
            card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
            content_layout.addWidget(card)

        service_header = QLabel("索引服务 · INDEX")
        service_header.setObjectName("sectionTitle")
        content_layout.addWidget(service_header)
        self.knowledge_index_labels: dict[str, QLabel] = {}
        for key, title, body in [
            ("vector", "向量索引", "等待刷新"),
            ("graph", "知识图谱", "等待刷新"),
        ]:
            card = QLabel(f"<b>{title}</b><br>{body}")
            card.setObjectName("statusLabel")
            card.setWordWrap(True)
            card.setMinimumHeight(52)
            card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
            content_layout.addWidget(card)
            self.knowledge_index_labels[key] = card

        footer = QLabel("最终检索入口读取合并后的 RAG/KG；数值计算、排序和 FEM 结果不由知识库改写。")
        footer.setObjectName("statusLabel")
        footer.setWordWrap(True)
        footer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        content_layout.addWidget(footer)

        scroll = QScrollArea()
        scroll.setObjectName("railScroll")
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setWidget(content)
        layout.addWidget(scroll, 1)
        return page

    def _refresh_knowledge_sidebar(self) -> None:
        labels = getattr(self, "knowledge_sidebar_labels", None)
        if not labels:
            return
        try:
            status = self.knowledge_widget.knowledge_base.status()
            ingest_status = self.knowledge_widget.ingestion_service.status()
        except Exception:
            return
        merged_status = {**status, **ingest_status}
        builtin_chunks = int(merged_status.get("builtin_rag_chunk_count", 0) or 0)
        builtin_entities = int(merged_status.get("builtin_kg_entity_count", 0) or 0)
        builtin_relations = int(merged_status.get("builtin_kg_relation_count", 0) or 0)
        runtime_docs = int(merged_status.get("runtime_document_count", merged_status.get("document_count", 0)) or 0)
        runtime_chunks = int(merged_status.get("runtime_rag_chunk_count", 0) or 0)
        runtime_relations = int(merged_status.get("runtime_kg_relation_count", 0) or 0)
        archive_cases = len(list(CASES_DIR.glob("CASE_*.json"))) if CASES_DIR.exists() else 0
        formal_cases = len(list(CASE_LIBRARY_DIR.glob("CASE_*.json"))) if CASE_LIBRARY_DIR.exists() else 0
        total_chunks = int(merged_status.get("rag_chunk_count", 0) or 0)
        total_entities = int(merged_status.get("kg_entity_count", 0) or 0)
        total_relations = int(merged_status.get("kg_relation_count", 0) or 0)
        vector_status = str(merged_status.get("vector_status") or "pending")
        chunk_size = merged_status.get("chunk_token_size", "-")
        overlap = merged_status.get("chunk_overlap_tokens", "-")
        top_k = merged_status.get("top_k", "-")
        kg_top_k = merged_status.get("kg_top_k", "-")

        payload = {
            "merged": ("合并知识库", f"RAG {total_chunks} · KG {total_entities}/{total_relations}"),
            "builtin": ("系统资料", f"RAG {builtin_chunks} · KG {builtin_entities}/{builtin_relations}"),
            "runtime": ("用户资料", f"{runtime_docs} 文档 · {runtime_chunks} 块 · {runtime_relations} 关系"),
            "cases": ("案例记忆", f"会话 {archive_cases} · 正式 {formal_cases}"),
            "retrieval": ("检索验证", f"Vector {vector_status} · 联合检索"),
            "config": ("分块参数", f"{chunk_size} / {overlap} · top_k {top_k}/{kg_top_k}"),
        }
        for key, (title, body) in payload.items():
            label = labels.get(key)
            if label is not None:
                label.setText(f"<b>{title}</b><br>{body}")
        index_labels = getattr(self, "knowledge_index_labels", None)
        if index_labels:
            vector_label = index_labels.get("vector")
            if vector_label is not None:
                vector_count = int(merged_status.get("vector_chunk_count", 0) or 0)
                vector_label.setText(f"<b>向量索引</b><br>{vector_status} · {vector_count} 向量块")
            graph_label = index_labels.get("graph")
            if graph_label is not None:
                graph_label.setText(f"<b>知识图谱</b><br>{total_entities} 实体 · {total_relations} 关系")
        right_labels = getattr(self, "knowledge_right_labels", None)
        if right_labels:
            verification = merged_status.get("last_retrieval_verification") if isinstance(merged_status.get("last_retrieval_verification"), dict) else {}
            vector_count = int(merged_status.get("vector_chunk_count", 0) or 0)
            right_payload = {
                "merged": ("合并检索入口", f"RAG {total_chunks} 块 · KG {total_entities}/{total_relations}"),
                "retrieval": ("检索验证", str(verification.get("message") or "等待检索命中")),
                "vector": ("向量索引", f"{vector_status} · {vector_count} 向量块"),
                "graph": ("知识图谱", f"{total_entities} 实体 · {total_relations} 关系"),
                "cases": ("案例记忆", f"会话 {archive_cases} · 正式 {formal_cases}"),
            }
            for key, (title, body) in right_payload.items():
                label = right_labels.get(key)
                if label is not None:
                    label.setText(f"<b>{title}</b><br>{body}")
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
        page = QWidget()
        page.setObjectName("agentRail")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(14, 14, 0, 14)
        layout.setSpacing(9)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        header = QLabel("设置 · SETTINGS")
        header.setObjectName("sectionTitle")
        layout.addWidget(header)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 12, 0)
        content_layout.setSpacing(9)
        content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.settings_sidebar_labels: dict[str, QLabel] = {}
        for key, title, body in [
            ("llm", "模型与 API", "主模型 / 回退模型 / 温度"),
            ("solver", "求解器集成", "ABAQUS 命令 / 用户子程序"),
            ("workflow", "智能体编排", "确认节点 / 运行快照"),
            ("knowledge", "知识库 / RAG", "top_k / 分块 / 向量索引"),
            ("ui", "界面偏好", "语言 / 主题 / 本地偏好"),
            ("files", "配置文件", "YAML 配置与 .env 密钥隔离"),
        ]:
            card = QLabel(f"<b>{title}</b><br>{body}")
            card.setObjectName("agentCard")
            card.setWordWrap(True)
            card.setProperty("state", "waiting")
            card.setMinimumHeight(68)
            card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
            content_layout.addWidget(card)
            self.settings_sidebar_labels[key] = card

        footer = QLabel("运行事实源为本项目 YAML 配置、.env 环境变量和本地运行数据；GUI 不显示密钥正文。")
        footer.setObjectName("statusLabel")
        footer.setWordWrap(True)
        footer.setMinimumHeight(62)
        footer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        content_layout.addWidget(footer)
        scroll = QScrollArea()
        scroll.setObjectName("railScroll")
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setWidget(content)
        layout.addWidget(scroll, 1)
        return page

    def _refresh_settings_sidebar(self) -> None:
        labels = getattr(self, "settings_sidebar_labels", None)
        if not labels:
            return
        app_config = load_app_config()
        llm_config = load_llm_config()
        backends = llm_config.get("backends") if isinstance(llm_config.get("backends"), list) else []
        primary = backends[0] if backends else {}
        fallback = backends[1] if len(backends) > 1 else {}
        abaqus = app_config.get("abaqus") if isinstance(app_config.get("abaqus"), dict) else {}
        pipeline = app_config.get("pipeline") if isinstance(app_config.get("pipeline"), dict) else {}
        ratio = pipeline.get("candidate_source_ratio") if isinstance(pipeline.get("candidate_source_ratio"), dict) else {}
        knowledge = app_config.get("project_knowledge") if isinstance(app_config.get("project_knowledge"), dict) else {}
        conversation = app_config.get("conversation") if isinstance(app_config.get("conversation"), dict) else {}
        confirm_steps = conversation.get("confirmation_steps", [])
        confirm_count = len(confirm_steps) if isinstance(confirm_steps, list) else 0
        values = {
            "llm": ("模型与 API", f"{primary.get('model') or primary.get('model_env') or '-'} / {fallback.get('model') or fallback.get('model_env') or '-'}"),
            "solver": ("求解器集成", f"{abaqus.get('command') or 'abaqus'} · 用户子程序 {'启用' if abaqus.get('use_user_subroutine') else '关闭'}"),
            "workflow": ("智能体编排", f"确认节点 {confirm_count} 个 · 随机种子 {pipeline.get('random_seed', '-')}"),
            "knowledge": ("知识库 / RAG", f"top_k {knowledge.get('top_k', '-')} / KG {knowledge.get('kg_top_k', '-')} · chunk {knowledge.get('chunk_token_size', '-')}"),
            "ui": ("界面偏好", f"{self.locale.language} · {self.locale.theme}"),
            "files": ("配置文件", "config/app_config.yaml · config/llm_config.yaml · .env"),
        }
        values["files"] = (values["files"][0], "YAML 配置 · .env 隔离")
        for key, (title, body) in values.items():
            label = labels.get(key)
            if label is not None:
                label.setText(f"<b>{title}</b><br>{body}")

    def _build_knowledge_right_page(self) -> QWidget:
        page = QWidget()
        page.setObjectName("resultRail")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(9)
        header = QLabel("检索测试 · RETRIEVAL")
        header.setObjectName("sectionTitle")
        layout.addWidget(header)

        self.knowledge_right_labels: dict[str, QLabel] = {}
        for key, title, body in [
            ("merged", "合并检索入口", "等待知识库状态刷新"),
            ("retrieval", "检索验证", "RAG 文本块 + 知识图谱路径命中"),
            ("vector", "向量索引", "等待向量索引状态"),
            ("graph", "知识图谱", "等待实体关系统计"),
            ("cases", "案例记忆", "等待案例库统计"),
        ]:
            card = QLabel(f"<b>{title}</b><br>{body}")
            card.setObjectName("statusLabel")
            card.setWordWrap(True)
            card.setMinimumHeight(62)
            card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
            layout.addWidget(card)
            self.knowledge_right_labels[key] = card

        self.knowledge_right_rebuild_button = QPushButton("重建全部索引")
        self.knowledge_right_snapshot_button = QPushButton("导出图谱快照")
        self._set_button_variant(self.refresh_button, "secondary")
        self._set_button_variant(self.knowledge_right_rebuild_button, "primary")
        self._set_button_variant(self.knowledge_right_snapshot_button, "secondary")
        for button in [self.refresh_button, self.knowledge_right_rebuild_button, self.knowledge_right_snapshot_button]:
            button.setMinimumHeight(44)
            button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            layout.addWidget(button)
        layout.addStretch(1)
        return page

    def _build_monitor_right_page(self) -> QWidget:
        page = QWidget()
        page.setObjectName("resultRail")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(9)
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
        page = QWidget()
        page.setObjectName("resultRail")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(9)
        header = QLabel("配置状态 · HEALTH")
        header.setObjectName("sectionTitle")
        layout.addWidget(header)
        self.settings_health_labels: dict[str, QLabel] = {}
        for key in ["primary", "fallback", "abaqus", "knowledge", "pipeline", "confirm"]:
            card = QLabel()
            card.setObjectName("statusLabel")
            card.setWordWrap(True)
            layout.addWidget(card)
            self.settings_health_labels[key] = card
        layout.addStretch(1)
        self._refresh_settings_health_panel()
        return page

    def _refresh_settings_health_panel(self) -> None:
        labels = getattr(self, "settings_health_labels", None)
        if not labels:
            return
        app_config = load_app_config()
        llm_config = load_llm_config()
        backends = llm_config.get("backends") if isinstance(llm_config.get("backends"), list) else []
        primary = backends[0] if backends else {}
        fallback = backends[1] if len(backends) > 1 else {}
        abaqus = app_config.get("abaqus") if isinstance(app_config.get("abaqus"), dict) else {}
        pipeline = app_config.get("pipeline") if isinstance(app_config.get("pipeline"), dict) else {}
        ratio = pipeline.get("candidate_source_ratio") if isinstance(pipeline.get("candidate_source_ratio"), dict) else {}
        knowledge = app_config.get("project_knowledge") if isinstance(app_config.get("project_knowledge"), dict) else {}
        conversation = app_config.get("conversation") if isinstance(app_config.get("conversation"), dict) else {}

        def env_status(*names: object) -> str:
            valid_names = [str(name).strip() for name in names if str(name or "").strip()]
            if not valid_names:
                return "未配置环境变量名"
            configured = [name for name in valid_names if bool(os.getenv(name))]
            return f"环境变量 {len(configured)}/{len(valid_names)} 已提供"

        primary_env = env_status(primary.get("base_url_env"), primary.get("api_key_env"), primary.get("model_env"))
        fallback_env = env_status(fallback.get("base_url_env"), fallback.get("api_key_env"), fallback.get("model_env"))
        ratio_text = f"LLM:{ratio.get('llm', 0)} / 案例:{ratio.get('case_transfer', 0)} / DOE:{ratio.get('doe', 0)}"
        confirm_steps = conversation.get("confirmation_steps", [])
        if isinstance(confirm_steps, list) and confirm_steps:
            confirm_text = "、".join(str(item) for item in confirm_steps)
        else:
            confirm_text = "未配置人工确认节点"
        cards = {
            "primary": ("主模型", f"{primary.get('model') or primary.get('model_env') or '-'}；{primary_env}"),
            "fallback": ("回退模型", f"{fallback.get('model') or fallback.get('model_env') or '-'}；{fallback_env}"),
            "abaqus": ("ABAQUS", f"{abaqus.get('command') or 'abaqus'}；用户子程序 {'启用' if abaqus.get('use_user_subroutine') else '关闭'}"),
            "knowledge": (
                "知识库",
                f"chunk {knowledge.get('chunk_token_size', 512)} / overlap {knowledge.get('chunk_overlap_tokens', 64)}；"
                f"top_k {knowledge.get('top_k', 5)} / KG {knowledge.get('kg_top_k', 8)}",
            ),
            "pipeline": ("候选来源", ratio_text),
            "confirm": ("人工确认", confirm_text),
        }
        for key, (primary_text, secondary) in cards.items():
            label = labels.get(key)
            if label is not None:
                state_color = "#34d399"
                if key in {"primary", "fallback"} and "0/" in secondary:
                    state_color = "#f59e0b"
                label.setText(
                    f"<span style='color:{state_color};font-size:15px;'>●</span> "
                    f"<b>{primary_text}</b><br>{secondary}"
                )
        self._refresh_settings_sidebar()

    def _switch_workspace_page(self, index: int) -> None:
        button = self.nav_group.button(index)
        if button is not None and not button.isChecked():
            button.setChecked(True)
        self.stack.setCurrentIndex(index)
        self.left_stack.setCurrentIndex(index)
        self.right_stack.setCurrentIndex(index)
        if index == 1:
            self.knowledge_widget.refresh(load_evidence=False)
            self._refresh_knowledge_sidebar()
        if index == 2:
            self.monitor_dashboard_widget.refresh()
        if index == 3:
            self._refresh_settings_sidebar()
            self._refresh_settings_health_panel()

    def _build_settings_page(self) -> QWidget:
        page = QWidget()
        page.setObjectName("centerWorkbench")
        self.settings_fields: dict[str, QLineEdit | QComboBox] = {}
        self.settings_status_label = QLabel("配置来自本项目 YAML 文件；API 密钥继续由 .env 管理。")
        self.settings_status_label.setObjectName("chatStatus")
        self.settings_status_label.setWordWrap(True)
        self.settings_save_button = QPushButton("保存设置")
        self.settings_reload_button = QPushButton("重新载入")
        self._set_button_variant(self.settings_save_button, "primary")
        self._set_button_variant(self.settings_reload_button, "secondary")

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(18, 18, 18, 18)
        content_layout.setSpacing(14)
        content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        header = QLabel("设置")
        header.setObjectName("configTitle")
        subtitle = QLabel("这里调整本地运行参数。密钥和私密凭据不写入 YAML，仍由 .env 和系统环境变量提供。")
        subtitle.setObjectName("configSubtitle")
        subtitle.setWordWrap(True)
        header_text = QWidget()
        header_text_layout = QVBoxLayout(header_text)
        header_text_layout.setContentsMargins(0, 0, 0, 0)
        header_text_layout.setSpacing(5)
        header_text_layout.addWidget(header)
        header_text_layout.addWidget(subtitle)
        header_text_layout.addWidget(self.settings_status_label)
        header_actions = QHBoxLayout()
        header_actions.setContentsMargins(0, 0, 0, 0)
        header_actions.setSpacing(10)
        header_actions.addWidget(self.settings_reload_button)
        header_actions.addWidget(self.settings_save_button)
        header_row = QHBoxLayout()
        header_row.setContentsMargins(0, 0, 0, 0)
        header_row.setSpacing(16)
        header_row.addWidget(header_text, 1)
        header_row.addLayout(header_actions)
        content_layout.addLayout(header_row)

        app_config = load_app_config()
        llm_config = load_llm_config()
        backends = llm_config.get("backends") if isinstance(llm_config.get("backends"), list) else []
        primary = backends[0] if backends else {}
        fallback = backends[1] if len(backends) > 1 else {}
        abaqus = app_config.get("abaqus") if isinstance(app_config.get("abaqus"), dict) else {}
        pipeline = app_config.get("pipeline") if isinstance(app_config.get("pipeline"), dict) else {}
        ratio = pipeline.get("candidate_source_ratio") if isinstance(pipeline.get("candidate_source_ratio"), dict) else {}
        knowledge = app_config.get("project_knowledge") if isinstance(app_config.get("project_knowledge"), dict) else {}
        conversation = app_config.get("conversation") if isinstance(app_config.get("conversation"), dict) else {}

        settings_overview = QGridLayout()
        settings_overview.setContentsMargins(0, 0, 0, 0)
        settings_overview.setHorizontalSpacing(10)
        settings_overview.setVerticalSpacing(10)
        overview_cards = [
            self._settings_summary_card("主模型", str(primary.get("model") or "-"), str(primary.get("base_url_env") or "-")),
            self._settings_summary_card("回退模型", str(fallback.get("model_env") or "-"), str(fallback.get("base_url_env") or "-")),
            self._settings_summary_card("ABAQUS", str(abaqus.get("command") or "abaqus"), f"timeout {abaqus.get('job_timeout_seconds', 3600)} s"),
            self._settings_summary_card(
                "RAG / KG",
                f"top_k {knowledge.get('top_k', 5)} / KG {knowledge.get('kg_top_k', 8)}",
                f"chunk {knowledge.get('chunk_token_size', 512)} / overlap {knowledge.get('chunk_overlap_tokens', 64)}",
            ),
        ]
        for index, card in enumerate(overview_cards):
            settings_overview.addWidget(card, 0, index)
        for column in range(len(overview_cards)):
            settings_overview.setColumnStretch(column, 1)
        content_layout.addLayout(settings_overview)
        content_layout.addWidget(self._settings_preference_bar())

        cards = [
            self._settings_form_card(
                "模型与 API",
                [
                    ("主模型名称", self._settings_line("llm.primary.model", primary.get("model", ""))),
                    ("主模型 URL 环境变量", self._settings_line("llm.primary.base_url_env", primary.get("base_url_env", ""))),
                    ("主模型名称环境变量", self._settings_line("llm.primary.model_env", primary.get("model_env", ""))),
                    ("主模型密钥环境变量", self._settings_line("llm.primary.api_key_env", primary.get("api_key_env", ""))),
                    ("回退模型 URL 环境变量", self._settings_line("llm.fallback.base_url_env", fallback.get("base_url_env", ""))),
                    ("回退模型名称环境变量", self._settings_line("llm.fallback.model_env", fallback.get("model_env", ""))),
                    ("回退模型密钥环境变量", self._settings_line("llm.fallback.api_key_env", fallback.get("api_key_env", ""))),
                    ("温度", self._settings_line("llm.temperature", primary.get("temperature", 0.2))),
                    ("最大输出 token", self._settings_line("llm.max_tokens", primary.get("max_tokens", 1800))),
                    ("超时秒数", self._settings_line("llm.timeout_seconds", primary.get("timeout_seconds", 180))),
                    ("JSON 输出 token", self._settings_line("llm.json_output_tokens", primary.get("json_output_tokens", 4096))),
                ],
            ),
            self._settings_form_card(
                "求解器集成 · ABAQUS",
                [
                    ("命令", self._settings_path_field("abaqus.command", abaqus.get("command", "abaqus"), "file")),
                    ("CAE 参数", self._settings_line("abaqus.cae_args", abaqus.get("cae_args", "cae noGUI="))),
                    ("Python 参数", self._settings_line("abaqus.python_args", abaqus.get("python_args", "python"))),
                    ("用户子程序", self._settings_path_field("abaqus.user_subroutine", abaqus.get("user_subroutine", ""), "file")),
                    ("启用用户子程序", self._settings_combo("abaqus.use_user_subroutine", abaqus.get("use_user_subroutine", False), [("否", "false"), ("是", "true")])),
                    ("作业超时秒数", self._settings_line("abaqus.job_timeout_seconds", abaqus.get("job_timeout_seconds", 3600))),
                    ("最大重试", self._settings_line("abaqus.max_retries", abaqus.get("max_retries", 3))),
                    ("轮询间隔秒数", self._settings_line("abaqus.poll_interval_seconds", abaqus.get("poll_interval_seconds", 5))),
                    ("清理模式", self._settings_line("abaqus.cleanup_patterns", ", ".join(abaqus.get("cleanup_patterns", [])))),
                ],
            ),
            self._settings_form_card(
                "智能体编排",
                [
                    ("LLM 来源比例", self._settings_line("pipeline.ratio.llm", ratio.get("llm", 2))),
                    ("案例迁移比例", self._settings_line("pipeline.ratio.case_transfer", ratio.get("case_transfer", 1))),
                    ("DOE 比例", self._settings_line("pipeline.ratio.doe", ratio.get("doe", 1))),
                    ("随机种子", self._settings_line("pipeline.random_seed", pipeline.get("random_seed", 42))),
                    ("最小回训案例", self._settings_line("pipeline.min_case_records_for_retrain", pipeline.get("min_case_records_for_retrain", 30))),
                    ("压力权重", self._settings_line("pipeline.screening.pressure_weight", (pipeline.get("screening_score") or {}).get("pressure_weight", 1.0))),
                    ("质量惩罚", self._settings_line("pipeline.screening.weight_penalty", (pipeline.get("screening_score") or {}).get("weight_penalty", 0.12))),
                    ("不确定度惩罚", self._settings_line("pipeline.screening.uncertainty_penalty", (pipeline.get("screening_score") or {}).get("uncertainty_penalty", 0.2))),
                    ("确认节点", self._settings_line("conversation.confirmation_steps", ", ".join(conversation.get("confirmation_steps", [])))),
                ],
            ),
            self._settings_form_card(
                "知识库 / RAG / KG",
                [
                    ("RAG top_k", self._settings_line("knowledge.top_k", knowledge.get("top_k", 5))),
                    ("KG top_k", self._settings_line("knowledge.kg_top_k", knowledge.get("kg_top_k", 8))),
                    ("Chunk token", self._settings_line("knowledge.chunk_token_size", knowledge.get("chunk_token_size", 512))),
                    ("Overlap token", self._settings_line("knowledge.chunk_overlap_tokens", knowledge.get("chunk_overlap_tokens", 64))),
                    ("最小 chunk token", self._settings_line("knowledge.min_chunk_tokens", knowledge.get("min_chunk_tokens", 80))),
                    ("最大片段字符", self._settings_line("knowledge.max_snippet_chars", knowledge.get("max_snippet_chars", 1200))),
                    ("向量索引", self._settings_combo("knowledge.vector_enabled", knowledge.get("vector_enabled", True), [("启用", "true"), ("关闭", "false")])),
                    ("向量 top_k 倍率", self._settings_line("knowledge.vector_top_k_multiplier", knowledge.get("vector_top_k_multiplier", 2))),
                    ("向量集合", self._settings_line("knowledge.vector_collection_name", knowledge.get("vector_collection_name", ""))),
                ],
            ),
        ]
        forms_grid = QGridLayout()
        forms_grid.setContentsMargins(0, 0, 0, 0)
        forms_grid.setHorizontalSpacing(12)
        forms_grid.setVerticalSpacing(12)
        forms_grid.addWidget(cards[0], 0, 0, Qt.AlignmentFlag.AlignTop)
        forms_grid.addWidget(cards[1], 0, 1, Qt.AlignmentFlag.AlignTop)
        forms_grid.addWidget(cards[2], 1, 0, Qt.AlignmentFlag.AlignTop)
        forms_grid.addWidget(cards[3], 1, 1, Qt.AlignmentFlag.AlignTop)
        forms_grid.setColumnStretch(0, 1)
        forms_grid.setColumnStretch(1, 1)
        content_layout.addLayout(forms_grid)
        content_layout.addWidget(self._settings_runtime_card())
        content_layout.addWidget(self._settings_validation_card())

        scroll_area.setWidget(content)
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(scroll_area)
        self.settings_save_button.clicked.connect(self._save_settings_from_page)
        self.settings_reload_button.clicked.connect(self._reload_settings_page)
        return page

    def _settings_preference_bar(self) -> QFrame:
        card = QFrame()
        card.setObjectName("configCard")
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        card.setMinimumHeight(74)
        card.setMaximumHeight(74)
        layout = QGridLayout(card)
        layout.setContentsMargins(12, 7, 12, 7)
        layout.setHorizontalSpacing(12)
        layout.setVerticalSpacing(4)
        title = QLabel("界面语言与主题")
        title.setObjectName("configCardTitle")
        layout.addWidget(title, 0, 0, 1, 4)
        for column, (label_text, widget) in enumerate(
            [
                (self.locale.text("section.language"), self.language_selector),
                (self.locale.text("section.theme"), self.theme_selector),
            ]
        ):
            key_label = QLabel(label_text)
            key_label.setObjectName("configKey")
            key_label.setWordWrap(False)
            key_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            key_label.setFixedHeight(30)
            key_label.setMinimumWidth(92)
            widget.setFixedHeight(30)
            layout.addWidget(key_label, 1, column * 2, Qt.AlignmentFlag.AlignVCenter)
            layout.addWidget(widget, 1, column * 2 + 1, Qt.AlignmentFlag.AlignVCenter)
            layout.setColumnStretch(column * 2 + 1, 1)
        layout.setColumnStretch(0, 0)
        layout.setColumnStretch(2, 0)
        return card

    def _settings_runtime_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName("configCard")
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        card.setMinimumHeight(158)
        card.setMaximumHeight(158)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(10)
        title = QLabel("配置文件与运行目录")
        title.setObjectName("configCardTitle")
        layout.addWidget(title)
        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(8)
        items = [
            ("应用配置", "config/app_config.yaml"),
            ("模型配置", "config/llm_config.yaml"),
            ("环境变量", ".env / 系统环境变量"),
            ("内置知识库", "knowledge/csllm"),
            ("增量知识库", "knowledge/runtime"),
            ("向量索引", "knowledge/chroma_db"),
            ("案例库", "data/cases / data/case_library"),
            ("结果输出", "data/results / data/abaqus_runs"),
        ]
        for index, (name, value) in enumerate(items):
            row = index // 2
            col = (index % 2) * 2
            key_label = QLabel(name)
            key_label.setObjectName("configKey")
            key_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            key_label.setFixedHeight(24)
            key_label.setMinimumWidth(88)
            value_label = QLabel(value)
            value_label.setObjectName("configValue")
            value_label.setWordWrap(True)
            value_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            value_label.setFixedHeight(24)
            grid.addWidget(key_label, row, col)
            grid.addWidget(value_label, row, col + 1)
            grid.setColumnStretch(col + 1, 1)
        layout.addLayout(grid)
        return card

    def _settings_validation_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName("configCard")
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        card.setMinimumHeight(128)
        card.setMaximumHeight(128)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(10)
        title = QLabel("配置校验规则")
        title.setObjectName("configCardTitle")
        layout.addWidget(title)
        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(8)
        items = [
            ("候选来源", "LLM / 案例迁移 / DOE 比例至少一路大于 0"),
            ("知识分块", "Overlap token 必须小于 Chunk token"),
            ("最小分块", "最小 chunk token 不大于 Chunk token"),
            ("人工确认", "候选初筛、有限元校核、报告导出可配置"),
            ("密钥管理", "API 密钥只从 .env 或系统环境变量读取"),
            ("生效范围", "保存后由新启动的工作流读取"),
        ]
        for index, (name, value) in enumerate(items):
            row = index // 2
            col = (index % 2) * 2
            key_label = QLabel(name)
            key_label.setObjectName("configKey")
            key_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            key_label.setFixedHeight(24)
            key_label.setMinimumWidth(88)
            value_label = QLabel(value)
            value_label.setObjectName("configValue")
            value_label.setWordWrap(True)
            value_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            value_label.setMinimumHeight(24)
            grid.addWidget(key_label, row, col)
            grid.addWidget(value_label, row, col + 1)
            grid.setColumnStretch(col + 1, 1)
        layout.addLayout(grid)
        return card

    def _settings_summary_card(self, title: str, value: str, detail: str) -> QFrame:
        card = QFrame()
        card.setObjectName("configCard")
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        card.setMinimumHeight(76)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 9, 12, 9)
        layout.setSpacing(3)
        title_label = QLabel(title)
        title_label.setObjectName("configKey")
        value_label = QLabel(value)
        value_label.setObjectName("configCardTitle")
        value_label.setWordWrap(True)
        detail_label = QLabel(detail)
        detail_label.setObjectName("configSubtitle")
        detail_label.setWordWrap(True)
        layout.addWidget(title_label)
        layout.addWidget(value_label)
        layout.addWidget(detail_label)
        return card

    def _settings_line(self, key: str, value: object) -> QLineEdit:
        field = QLineEdit(str(value if value is not None else ""))
        field.setObjectName("settingsInput")
        field.setFixedHeight(38)
        field.setCursorPosition(0)
        self.settings_fields[key] = field
        return field

    def _settings_path_field(self, key: str, value: object, mode: str) -> QWidget:
        wrapper = QWidget()
        wrapper.setObjectName("settingsPathField")
        wrapper.setFixedHeight(38)
        layout = QHBoxLayout(wrapper)
        layout.setContentsMargins(0, 2, 0, 2)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        field = self._settings_line(key, value)
        field.setFixedHeight(34)
        button = QPushButton("…")
        self._set_button_variant(button, "icon")
        button.setFixedSize(34, 34)
        button.setToolTip("选择本地路径")
        button.clicked.connect(lambda _checked=False, line=field, pick_mode=mode: self._browse_settings_path(line, pick_mode))
        layout.addWidget(field, 1, Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(button, 0, Qt.AlignmentFlag.AlignVCenter)
        return wrapper

    def _browse_settings_path(self, field: QLineEdit, mode: str) -> None:
        current = field.text().strip()
        start_dir = str(Path(current).parent) if current and Path(current).parent.exists() else str(PROJECT_ROOT)
        if mode == "directory":
            path = QFileDialog.getExistingDirectory(self, "选择目录", start_dir)
        else:
            path, _ = QFileDialog.getOpenFileName(self, "选择文件", start_dir, "All Files (*)")
        if path:
            field.setText(path)
            field.setCursorPosition(0)

    def _settings_combo(self, key: str, value: object, options: list[tuple[str, str]]) -> QComboBox:
        combo = QComboBox()
        combo.setObjectName("settingsInput")
        combo.setFixedHeight(38)
        for label, data in options:
            combo.addItem(label, data)
        target = str(value).lower()
        index = combo.findData(target)
        if index >= 0:
            combo.setCurrentIndex(index)
        self.settings_fields[key] = combo
        return combo

    def _settings_form_card(self, title: str, rows: list[tuple[str, QWidget]]) -> QFrame:
        card = QFrame()
        card.setObjectName("configCard")
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        row_height = 38
        row_gap = 9
        title_height = 22
        vertical_margins = 24
        title_gap = 10
        form_height = len(rows) * row_height + max(0, len(rows) - 1) * row_gap
        card_height = max(118, vertical_margins + title_height + title_gap + form_height)
        card.setMinimumHeight(card_height)
        card.setMaximumHeight(card_height)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(title_gap)
        title_label = QLabel(title)
        title_label.setObjectName("configCardTitle")
        title_label.setFixedHeight(title_height)
        title_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(title_label)
        form = QGridLayout()
        form.setContentsMargins(0, 0, 0, 0)
        form.setHorizontalSpacing(12)
        form.setVerticalSpacing(9)
        for row_index, (label, widget) in enumerate(rows):
            key_label = QLabel(label)
            key_label.setObjectName("configKey")
            key_label.setWordWrap(True)
            key_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            key_label.setMinimumWidth(132)
            key_label.setFixedHeight(38)
            key_label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
            widget.setFixedHeight(38)
            form.addWidget(key_label, row_index, 0, Qt.AlignmentFlag.AlignVCenter)
            form.addWidget(widget, row_index, 1, Qt.AlignmentFlag.AlignVCenter)
        form.setColumnStretch(0, 0)
        form.setColumnStretch(1, 1)
        form_widget = QWidget()
        form_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        form_widget.setLayout(form)
        form_widget.setFixedHeight(form_height)
        layout.addWidget(form_widget)
        return card

    def _settings_value(self, key: str) -> str:
        widget = self.settings_fields.get(key)
        if isinstance(widget, QComboBox):
            return str(widget.currentData())
        if isinstance(widget, QLineEdit):
            return widget.text().strip()
        return ""

    def _set_settings_value(self, key: str, value: object) -> None:
        widget = self.settings_fields.get(key)
        if isinstance(widget, QComboBox):
            index = widget.findData(str(value).lower())
            if index >= 0:
                widget.setCurrentIndex(index)
            return
        if isinstance(widget, QLineEdit):
            widget.setText(str(value if value is not None else ""))
            widget.setCursorPosition(0)

    def _settings_int(self, key: str, default: int) -> int:
        try:
            return int(float(self._settings_value(key)))
        except ValueError:
            return default

    def _settings_float(self, key: str, default: float) -> float:
        try:
            return float(self._settings_value(key))
        except ValueError:
            return default

    def _settings_bool(self, key: str, default: bool) -> bool:
        value = self._settings_value(key).lower()
        if value in {"true", "1", "yes", "on"}:
            return True
        if value in {"false", "0", "no", "off"}:
            return False
        return default

    def _reload_settings_page(self) -> None:
        load_app_config.cache_clear()
        load_llm_config.cache_clear()
        app_config = load_app_config()
        llm_config = load_llm_config()
        backends = llm_config.get("backends") if isinstance(llm_config.get("backends"), list) else []
        primary = backends[0] if backends else {}
        fallback = backends[1] if len(backends) > 1 else {}
        abaqus = app_config.get("abaqus") if isinstance(app_config.get("abaqus"), dict) else {}
        pipeline = app_config.get("pipeline") if isinstance(app_config.get("pipeline"), dict) else {}
        ratio = pipeline.get("candidate_source_ratio") if isinstance(pipeline.get("candidate_source_ratio"), dict) else {}
        knowledge = app_config.get("project_knowledge") if isinstance(app_config.get("project_knowledge"), dict) else {}
        conversation = app_config.get("conversation") if isinstance(app_config.get("conversation"), dict) else {}
        values = {
            "llm.primary.model": primary.get("model", ""),
            "llm.primary.base_url_env": primary.get("base_url_env", ""),
            "llm.primary.model_env": primary.get("model_env", ""),
            "llm.primary.api_key_env": primary.get("api_key_env", ""),
            "llm.fallback.base_url_env": fallback.get("base_url_env", ""),
            "llm.fallback.model_env": fallback.get("model_env", ""),
            "llm.fallback.api_key_env": fallback.get("api_key_env", ""),
            "llm.temperature": primary.get("temperature", 0.2),
            "llm.max_tokens": primary.get("max_tokens", 1800),
            "llm.timeout_seconds": primary.get("timeout_seconds", 180),
            "llm.json_output_tokens": primary.get("json_output_tokens", 4096),
            "abaqus.command": abaqus.get("command", "abaqus"),
            "abaqus.cae_args": abaqus.get("cae_args", "cae noGUI="),
            "abaqus.python_args": abaqus.get("python_args", "python"),
            "abaqus.user_subroutine": abaqus.get("user_subroutine", ""),
            "abaqus.use_user_subroutine": abaqus.get("use_user_subroutine", False),
            "abaqus.job_timeout_seconds": abaqus.get("job_timeout_seconds", 3600),
            "abaqus.max_retries": abaqus.get("max_retries", 3),
            "abaqus.poll_interval_seconds": abaqus.get("poll_interval_seconds", 5),
            "abaqus.cleanup_patterns": ", ".join(abaqus.get("cleanup_patterns", [])),
            "pipeline.ratio.llm": ratio.get("llm", 2),
            "pipeline.ratio.case_transfer": ratio.get("case_transfer", 1),
            "pipeline.ratio.doe": ratio.get("doe", 1),
            "pipeline.random_seed": pipeline.get("random_seed", 42),
            "pipeline.min_case_records_for_retrain": pipeline.get("min_case_records_for_retrain", 30),
            "pipeline.screening.pressure_weight": (pipeline.get("screening_score") or {}).get("pressure_weight", 1.0),
            "pipeline.screening.weight_penalty": (pipeline.get("screening_score") or {}).get("weight_penalty", 0.12),
            "pipeline.screening.uncertainty_penalty": (pipeline.get("screening_score") or {}).get("uncertainty_penalty", 0.2),
            "conversation.confirmation_steps": ", ".join(conversation.get("confirmation_steps", [])),
            "knowledge.top_k": knowledge.get("top_k", 5),
            "knowledge.kg_top_k": knowledge.get("kg_top_k", 8),
            "knowledge.chunk_token_size": knowledge.get("chunk_token_size", 512),
            "knowledge.chunk_overlap_tokens": knowledge.get("chunk_overlap_tokens", 64),
            "knowledge.min_chunk_tokens": knowledge.get("min_chunk_tokens", 80),
            "knowledge.max_snippet_chars": knowledge.get("max_snippet_chars", 1200),
            "knowledge.vector_enabled": knowledge.get("vector_enabled", True),
            "knowledge.vector_top_k_multiplier": knowledge.get("vector_top_k_multiplier", 2),
            "knowledge.vector_collection_name": knowledge.get("vector_collection_name", ""),
        }
        for key, value in values.items():
            self._set_settings_value(key, value)
        self.settings_status_label.setText("配置已从本项目 YAML 文件重新载入。")
        self._refresh_settings_health_panel()
        self._refresh_settings_sidebar()

    def _save_settings_from_page(self) -> None:
        app_config = load_app_config()
        llm_config = load_llm_config()
        app_config.setdefault("abaqus", {})
        app_config.setdefault("pipeline", {}).setdefault("candidate_source_ratio", {})
        app_config.setdefault("project_knowledge", {})
        app_config.setdefault("conversation", {})
        backends = llm_config.setdefault("backends", [])
        while len(backends) < 2:
            backends.append({})
        primary, fallback = backends[0], backends[1]

        primary["model"] = self._settings_value("llm.primary.model") or primary.get("model", "csllm")
        primary["base_url_env"] = self._settings_value("llm.primary.base_url_env") or primary.get("base_url_env", "LLM_PRIMARY_URL")
        primary["model_env"] = self._settings_value("llm.primary.model_env") or primary.get("model_env", "LLM_PRIMARY_MODEL_NAME")
        primary["api_key_env"] = self._settings_value("llm.primary.api_key_env") or primary.get("api_key_env", "LLM_PRIMARY_API_KEY")
        fallback["base_url_env"] = self._settings_value("llm.fallback.base_url_env") or fallback.get("base_url_env", "URL")
        fallback["model_env"] = self._settings_value("llm.fallback.model_env") or fallback.get("model_env", "MODEL_NAME")
        fallback["api_key_env"] = self._settings_value("llm.fallback.api_key_env") or fallback.get("api_key_env", "API_KEY")
        for backend in backends:
            backend["temperature"] = self._settings_float("llm.temperature", float(backend.get("temperature", 0.2) or 0.2))
            backend["max_tokens"] = self._settings_int("llm.max_tokens", int(backend.get("max_tokens", 1800) or 1800))
            backend["timeout_seconds"] = self._settings_int("llm.timeout_seconds", int(backend.get("timeout_seconds", 180) or 180))
            backend["json_output_tokens"] = self._settings_int("llm.json_output_tokens", int(backend.get("json_output_tokens", 4096) or 4096))

        abaqus = app_config["abaqus"]
        abaqus["command"] = self._settings_value("abaqus.command") or "abaqus"
        abaqus["cae_args"] = self._settings_value("abaqus.cae_args") or abaqus.get("cae_args", "cae noGUI=")
        abaqus["python_args"] = self._settings_value("abaqus.python_args") or abaqus.get("python_args", "python")
        abaqus["user_subroutine"] = self._settings_value("abaqus.user_subroutine")
        abaqus["use_user_subroutine"] = self._settings_bool("abaqus.use_user_subroutine", bool(abaqus.get("use_user_subroutine", False)))
        abaqus["job_timeout_seconds"] = self._settings_int("abaqus.job_timeout_seconds", int(abaqus.get("job_timeout_seconds", 3600) or 3600))
        abaqus["max_retries"] = self._settings_int("abaqus.max_retries", int(abaqus.get("max_retries", 3) or 3))
        abaqus["poll_interval_seconds"] = self._settings_int("abaqus.poll_interval_seconds", int(abaqus.get("poll_interval_seconds", 5) or 5))
        cleanup_patterns = [item.strip() for item in self._settings_value("abaqus.cleanup_patterns").split(",") if item.strip()]
        abaqus["cleanup_patterns"] = cleanup_patterns

        ratio_values = {
            "llm": max(0, self._settings_int("pipeline.ratio.llm", 0)),
            "case_transfer": max(0, self._settings_int("pipeline.ratio.case_transfer", 0)),
            "doe": max(0, self._settings_int("pipeline.ratio.doe", 0)),
        }
        if sum(ratio_values.values()) <= 0:
            self.settings_status_label.setText("设置未保存：候选来源比例至少需要一路大于 0。")
            return

        chunk_token_size = max(32, self._settings_int("knowledge.chunk_token_size", int(app_config["project_knowledge"].get("chunk_token_size", 512) or 512)))
        chunk_overlap_tokens = max(0, self._settings_int("knowledge.chunk_overlap_tokens", int(app_config["project_knowledge"].get("chunk_overlap_tokens", 64) or 64)))
        min_chunk_tokens = max(1, self._settings_int("knowledge.min_chunk_tokens", int(app_config["project_knowledge"].get("min_chunk_tokens", 80) or 80)))
        if chunk_overlap_tokens >= chunk_token_size:
            self.settings_status_label.setText("设置未保存：Overlap token 必须小于 Chunk token。")
            return
        if min_chunk_tokens > chunk_token_size:
            self.settings_status_label.setText("设置未保存：最小 chunk token 不能大于 Chunk token。")
            return

        ratio = app_config["pipeline"]["candidate_source_ratio"]
        ratio.update(ratio_values)
        app_config["pipeline"]["random_seed"] = self._settings_int("pipeline.random_seed", int(app_config["pipeline"].get("random_seed", 42) or 42))
        app_config["pipeline"]["min_case_records_for_retrain"] = max(
            1,
            self._settings_int(
                "pipeline.min_case_records_for_retrain",
                int(app_config["pipeline"].get("min_case_records_for_retrain", 30) or 30),
            ),
        )
        screening_score = app_config["pipeline"].setdefault("screening_score", {})
        screening_score["pressure_weight"] = self._settings_float("pipeline.screening.pressure_weight", float(screening_score.get("pressure_weight", 1.0) or 1.0))
        screening_score["weight_penalty"] = self._settings_float("pipeline.screening.weight_penalty", float(screening_score.get("weight_penalty", 0.12) or 0.12))
        screening_score["uncertainty_penalty"] = self._settings_float(
            "pipeline.screening.uncertainty_penalty",
            float(screening_score.get("uncertainty_penalty", 0.2) or 0.2),
        )
        steps = [item.strip() for item in self._settings_value("conversation.confirmation_steps").split(",") if item.strip()]
        app_config["conversation"]["confirmation_steps"] = steps

        knowledge = app_config["project_knowledge"]
        knowledge["top_k"] = max(1, self._settings_int("knowledge.top_k", int(knowledge.get("top_k", 5) or 5)))
        knowledge["kg_top_k"] = max(1, self._settings_int("knowledge.kg_top_k", int(knowledge.get("kg_top_k", 8) or 8)))
        knowledge["chunk_token_size"] = chunk_token_size
        knowledge["chunk_overlap_tokens"] = chunk_overlap_tokens
        knowledge["min_chunk_tokens"] = min_chunk_tokens
        knowledge["max_snippet_chars"] = max(120, self._settings_int("knowledge.max_snippet_chars", int(knowledge.get("max_snippet_chars", 1200) or 1200)))
        knowledge["vector_enabled"] = self._settings_bool("knowledge.vector_enabled", bool(knowledge.get("vector_enabled", True)))
        knowledge["vector_top_k_multiplier"] = max(
            1,
            self._settings_int(
                "knowledge.vector_top_k_multiplier",
                int(knowledge.get("vector_top_k_multiplier", 2) or 2),
            ),
        )
        collection_name = self._settings_value("knowledge.vector_collection_name")
        if collection_name:
            knowledge["vector_collection_name"] = collection_name

        (CONFIG_DIR / "app_config.yaml").write_text(yaml.safe_dump(app_config, allow_unicode=True, sort_keys=False), encoding="utf-8")
        (CONFIG_DIR / "llm_config.yaml").write_text(yaml.safe_dump(llm_config, allow_unicode=True, sort_keys=False), encoding="utf-8")
        load_app_config.cache_clear()
        load_llm_config.cache_clear()
        self.settings_status_label.setText("设置已保存，新启动的流程会读取当前配置。")
        self._refresh_settings_health_panel()
        self._refresh_settings_sidebar()

    def _build_monitor_page(self) -> QWidget:
        page = QWidget()
        page.setObjectName("centerWorkbench")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(10)
        content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.monitor_dashboard_widget.setMinimumHeight(610)
        self.monitor_dashboard_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.workflow_widget.setMinimumHeight(220)
        self.workflow_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.monitor_log_widget.setMinimumHeight(150)
        self.monitor_log_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        content_layout.addWidget(self.monitor_dashboard_widget)
        content_layout.addWidget(self.workflow_widget)
        content_layout.addWidget(self.monitor_log_widget)
        scroll_area.setWidget(content)
        layout.addWidget(scroll_area, 1)
        return page

    def _set_button_variant(self, button: QPushButton, variant: str = "default") -> None:
        if variant == "icon":
            button.setFixedSize(30, 28)
        else:
            button.setMinimumHeight(40)
            button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
            if variant in {"primary", "success", "warning", "danger"}:
                button.setMinimumWidth(84)
        button.setProperty("variant", variant)

    def _fit_input_action_buttons(self) -> None:
        for button, minimum_width in [
            (self.generate_button, 56),
            (self.confirm_yes_button, 88),
            (self.confirm_no_button, 88),
        ]:
            text_width = button.fontMetrics().horizontalAdvance(button.text())
            button.setFixedWidth(max(minimum_width, text_width + 24))

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
        for button in [self.screen_button, self.evaluate_selected_button, self.evaluate_all_button, self.reset_button]:
            button.setMinimumHeight(44)
            button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        for button in [self.report_dir_button, self.report_button, self.export_data_button, self.open_report_button]:
            button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        for button in [
            self.refresh_button,
            getattr(self, "knowledge_right_rebuild_button", None),
            getattr(self, "knowledge_right_snapshot_button", None),
        ]:
            if button is not None:
                button.setMinimumHeight(44)
                button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._fit_input_action_buttons()
        self.workflow_widget.set_theme(self.locale.theme)
        self.flow_dag_widget.set_theme(self.locale.theme)
        self.flow_dag_widget.set_language(self.locale.language)
        self.model_status_label.set_theme(self.locale.theme)
        for card in self.agent_cards.values():
            card.set_theme(self.locale.theme)
        self.live_result_view.set_theme(self.locale.theme)
        self.knowledge_widget.set_theme(self.locale.theme)
        self.monitor_dashboard_widget.set_theme(self.locale.theme)
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

    def _target_window_size(self) -> QSize:
        screen = QApplication.primaryScreen()
        if screen is None:
            return QSize(1280, 960)
        available = screen.availableGeometry()
        max_width = max(320, available.width() - 32)
        max_height = max(320, available.height() - 40)
        if max_width >= 1360 and max_height >= 1020:
            return QSize(1360, 1020)
        if max_width >= 1280 and max_height >= 960:
            return QSize(1280, 960)
        height = min(max_height, max(560, int(max_width * 3 / 4)))
        width = min(max_width, int(height * 4 / 3))
        if width < 960 and max_width >= 960:
            width = 960
            height = min(max_height, int(width * 3 / 4))
        return QSize(width, height)

    def _resize_to_available_work_area(self) -> None:
        self.resize(self._target_window_size())

    def _ensure_window_within_work_area(self, *, clamp_to_target: bool = False) -> None:
        screen = self.screen() or QApplication.primaryScreen()
        if screen is None:
            return
        available = screen.availableGeometry()
        target = self._target_window_size()
        if clamp_to_target:
            aspect = self.width() / max(1, self.height())
            target_aspect = target.width() / max(1, target.height())
            abnormal_aspect = aspect > max(1.72, target_aspect + 0.18)
            oversized = self.width() > target.width() or self.height() > target.height()
            if self.isMaximized() and (abnormal_aspect or oversized):
                self.setWindowState(self.windowState() & ~Qt.WindowState.WindowMaximized)
            if abnormal_aspect:
                width = min(target.width(), available.width())
                height = min(target.height(), available.height())
                self.resize(width, height)
            else:
                width = min(self.width(), target.width(), available.width())
                height = min(self.height(), target.height(), available.height())
                self.resize(width, height)
        if self.width() > available.width() or self.height() > available.height():
            self.resize(
                min(self.width(), available.width()),
                min(self.height(), available.height()),
            )
        frame = self.frameGeometry()
        if available.contains(frame):
            return
        frame.moveCenter(available.center())
        max_x = available.x() + max(0, available.width() - frame.width())
        max_y = available.y() + max(0, available.height() - frame.height())
        x = min(max(frame.x(), available.x()), max_x)
        y = min(max(frame.y(), available.y()), max_y)
        self.move(x, y)

    def _restore_window_layout(self) -> None:
        if int(self.ui_state_settings.value("layout_version", 0) or 0) != UI_LAYOUT_VERSION:
            self.ui_state_settings.clear()
            self._resize_to_available_work_area()
            self._ensure_window_within_work_area(clamp_to_target=True)
            self._sync_main_splitter_sizes()
            return
        geometry = self.ui_state_settings.value("window_geometry")
        state = self.ui_state_settings.value("window_state")
        geometry_restored = False
        if geometry:
            geometry_restored = self.restoreGeometry(geometry)
        if state:
            self.restoreState(state)
        if not geometry_restored:
            self._resize_to_available_work_area()
        self._ensure_window_within_work_area(clamp_to_target=True)
        self._sync_main_splitter_sizes()

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
        self.trace_button.clicked.connect(lambda: self._switch_workspace_page(2))
        self.refresh_button.clicked.connect(self._refresh_knowledge_view)
        if hasattr(self, "knowledge_right_rebuild_button"):
            self.knowledge_right_rebuild_button.clicked.connect(lambda: self.knowledge_widget._run_maintenance("rebuild"))
        if hasattr(self, "knowledge_right_snapshot_button"):
            self.knowledge_right_snapshot_button.clicked.connect(lambda: self.knowledge_widget._run_maintenance("export"))
        self.open_report_button.clicked.connect(self._open_latest_report)
        self.export_data_button.clicked.connect(self._export_session_data)
        self.report_dir_button.clicked.connect(self._choose_report_output_dir)
        self.report_type_selector.currentIndexChanged.connect(lambda: self._update_button_states())
        self.reset_view_button.clicked.connect(self.live_result_view.reset_view)
        self.fit_view_button.clicked.connect(self.live_result_view.fit_view)
        self.workbench_candidate_widget.candidateSelected.connect(self.live_result_view.show_candidate)
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
        nav_keys = ["nav.workbench", "nav.knowledge", "nav.monitor", "nav.settings"]
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
        self._populate_report_type_selector()
        self.report_dir_button.setText(self.locale.text("button.report_dir"))
        self.report_dir_button.setToolTip(self.locale.text("tooltip.report_dir"))
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
        self.stats_header.setText(self.locale.text("section.session"))
        self.log_header.setText(self.locale.text("section.runtime_log"))
        self.agent_header.setText(self.locale.text("section.agents"))
        self.queue_header.setText(self.locale.text("section.queue"))
        self.knowledge_status_header.setText(self.locale.text("section.knowledge_status"))
        self.run_audit_header.setText(self.locale.text("section.run_audit"))
        self.workbench_header.setText(self.locale.text("section.workbench"))
        self.dialog_header.setText(self.locale.text("section.dialog"))
        self.details_header.setText(self.locale.text("section.details"))
        self.workbench_candidate_widget.set_language(self.locale.language)
        self.live_result_view.set_language(self.locale.language, self.locale.text("live_view.empty"))
        if not self.session.task:
            self.status_label.setText(self.locale.text("status.waiting"))
        self._update_overview_cards()
        self._refresh_run_selector()

    def _apply_chat_empty_state(self) -> None:
        self.chat_widget.set_empty_state(
            title=self.locale.text("chat.empty.title"),
            user_prompt=self.locale.text("chat.empty.user_prompt"),
            agent_title=self.locale.text("chat.empty.agent_title"),
            agent_body=self.locale.text("chat.empty.agent_body"),
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
            self.report_type_selector,
            self.report_dir_button,
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
        has_pending_display = bool(self._pending_candidates(self.session.display_candidates)) if has_candidates else False
        report_kind = str(self.report_type_selector.currentData() or "all")
        if report_kind == "design_solution":
            report_ready = bool(self.session.task and (self.session.candidates or self.session.screened_candidates))
        else:
            report_ready = bool(self.session.task and has_results)

        self.confirm_yes_button.setEnabled(self.session.pending_confirmation is not None)
        self.confirm_no_button.setEnabled(self.session.pending_confirmation is not None)
        self.screen_button.setEnabled(has_candidates and self.session.pending_confirmation is None)
        self.evaluate_selected_button.setEnabled(has_pending_display and self.session.pending_confirmation is None)
        self.evaluate_all_button.setEnabled(has_pending_current and self.session.pending_confirmation is None)
        self.report_button.setEnabled(report_ready and self.session.pending_confirmation is None)
        self.reset_button.setEnabled(True)
        self.example_button.setEnabled(self.session.pending_confirmation is None)
        self.refresh_button.setEnabled(True)
        session_report = self.session.report or {}
        session_report_raw_path = str(session_report.get("pdf_path") or session_report.get("markdown_path") or "").strip()
        self.open_report_button.setEnabled(
            (bool(session_report_raw_path) and Path(session_report_raw_path).exists())
            or (RESULTS_DIR / "latest_report.md").exists()
            or (RESULTS_DIR / "latest_report.pdf").exists()
        )
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
        stage_display = self._display_stage(self.session.stage or "idle")
        pending_label_zh = "待初筛" if self.session.stage == "awaiting_screen_confirmation" else "待 FEM 校核"
        pending_label_en = "Pending Screening" if self.session.stage == "awaiting_screen_confirmation" else "Pending FEM"
        def metric_html(label: str, value: str) -> str:
            light_theme = resolve_theme(self.locale.theme) == "light"
            value_color = "#172033" if light_theme else "#e5edf7"
            label_color = "#475569" if light_theme else "#94a3b8"
            return (
                f"<span style='color:{label_color};font-size:12px;'>"
                f"{label}</span><br>"
                f"<span style='color:{value_color};font-size:15px;font-weight:800;'>"
                f"{value}</span>"
            )

        if self.locale.language == "en":
            self.stage_card.setText(metric_html("Stage", stage_display))
            self.candidate_card.setText(
                metric_html("Candidate Pool", f"{generated_count} / {candidate_pool_target}")
                if self.session.task
                else metric_html("Candidate Pool", "0")
            )
            self.pending_card.setText(
                metric_html(pending_label_en, f"{pending_count} / {requested_top_k}")
                if self.session.task
                else metric_html(pending_label_en, "0")
            )
            self.pass_card.setText(metric_html("Passed", str(passed_count)))
        else:
            self.stage_card.setText(metric_html("当前阶段", stage_display))
            self.candidate_card.setText(
                metric_html("候选池", f"{generated_count} / {candidate_pool_target}")
                if self.session.task
                else metric_html("候选池", "0")
            )
            self.pending_card.setText(
                metric_html(pending_label_zh, f"{pending_count} / {requested_top_k}")
                if self.session.task
                else metric_html(pending_label_zh, "0")
            )
            self.pass_card.setText(metric_html("通过", str(passed_count)))
        self._update_runtime_panel()

    def _display_stage(self, stage: str | None) -> str:
        value = str(stage or "idle")
        zh = {
            "idle": "等待输入",
            "parsing": "任务解析中",
            "generate_candidates": "候选生成中",
            "candidate_generation_started": "候选生成中",
            "awaiting_screen_confirmation": "等待初筛确认",
            "screen_candidates": "代理初筛中",
            "screen_candidates_failed": "初筛失败",
            "awaiting_fem_confirmation": "等待FEM确认",
            "evaluate_candidates": "有限元校核中",
            "evaluate_candidates_failed": "有限元失败",
            "persist_knowledge": "知识回流中",
            "persist_knowledge_failed": "知识回流失败",
            "awaiting_report_confirmation": "等待报告确认",
            "generate_report": "报告生成中",
            "generate_report_failed": "报告失败",
            "completed": "已完成",
            "failed": "失败",
        }
        en = {
            "idle": "Idle",
            "parsing": "Parsing",
            "generate_candidates": "Generating",
            "candidate_generation_started": "Generating",
            "awaiting_screen_confirmation": "Await screening",
            "screen_candidates": "Screening",
            "screen_candidates_failed": "Screening failed",
            "awaiting_fem_confirmation": "Await FEM",
            "evaluate_candidates": "FEM running",
            "evaluate_candidates_failed": "FEM failed",
            "persist_knowledge": "Persisting knowledge",
            "persist_knowledge_failed": "Knowledge failed",
            "awaiting_report_confirmation": "Await report",
            "generate_report": "Reporting",
            "generate_report_failed": "Report failed",
            "completed": "Completed",
            "failed": "Failed",
        }
        mapping = en if self.locale.language == "en" else zh
        if value in mapping:
            return mapping[value]
        if value.startswith("parse_task"):
            return en["parsing"] if self.locale.language == "en" else zh["parsing"]
        if value.startswith("generate_candidates"):
            return en["generate_candidates"] if self.locale.language == "en" else zh["generate_candidates"]
        if value.startswith("screen_candidates"):
            return en["screen_candidates"] if self.locale.language == "en" else zh["screen_candidates"]
        if value.startswith("evaluate_candidates"):
            return en["evaluate_candidates"] if self.locale.language == "en" else zh["evaluate_candidates"]
        if value.startswith("persist_knowledge"):
            return en["persist_knowledge"] if self.locale.language == "en" else zh["persist_knowledge"]
        if value.startswith("generate_report"):
            return en["generate_report"] if self.locale.language == "en" else zh["generate_report"]
        return value.replace("_", " ")

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

    def _display_confirmation_gate(self, gate: str | None) -> str:
        mapping = {
            "screen_candidates": "audit.confirm_screen",
            "fem_evaluation": "audit.confirm_fem",
            "export_report": "audit.confirm_report",
        }
        return self.locale.text(mapping.get(str(gate or ""), "audit.none"))

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
            self.runtime_stage_text = (
                runtime_stage if runtime_stage.endswith("_failed") else f"{runtime_stage}_failed"
            ) if runtime_stage else runtime_type
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
                + self.locale.text("queue.stage", stage=self._display_stage(self.session.stage or "idle"))
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
            + f"块 {knowledge_payload.get('rag_chunk_count', 0)} · "
            + f"关系 {knowledge_payload.get('kg_relation_count', 0)}"
        )
        run_id = self.session.workflow_run_id or self.locale.text("audit.no_run")
        audit_lines = [
            self.locale.text("audit.run", run_id=run_id),
            self.locale.text("audit.stage", stage=self._display_stage(self.session.stage or "idle")),
            self.locale.text(
                "audit.confirmation",
                confirmation=self._display_confirmation_gate(self.session.pending_confirmation),
            ),
            self.locale.text(
                "audit.artifacts",
                candidates=len(self.session.candidates),
                screened=len(self.session.screened_candidates),
                results=len(self.session.results_by_session_id),
                knowledge=len(self.session.knowledge_updates),
            ),
        ]
        self.run_audit_label.setText("\n".join(audit_lines))
        active_stage = self._display_stage(self.runtime_stage_text or self.session.stage)
        if self.session.task or self.runtime_stage_text:
            stage_prefix = (
                self.locale.text("agent.failed")
                if "failed" in state_map.values()
                else self.locale.text("agent.active")
            )
            stage_text = f"{stage_prefix} · {active_stage}"
        else:
            stage_text = self.locale.text("queue.idle")
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
        self.workbench_candidate_widget.update_candidates(self.session.display_candidates, self.session.results_by_session_id)
        self.result_trace_widget.update_trace(
            self.session.display_candidates,
            self.session.results_by_session_id,
            self.session.knowledge_updates,
            self.session.report,
        )
        self.workflow_widget.refresh(
            self.session.workflow_run_id,
            self.session.stage,
            self.session.pending_confirmation,
        )
        self.knowledge_widget.refresh(self.session.task)
        self._refresh_knowledge_sidebar()
        self._refresh_live_view()
        self._update_overview_cards()
        self._sync_status_label_with_session()

    def _refresh_design_views(self) -> None:
        self.workbench_candidate_widget.update_candidates(self.session.display_candidates, self.session.results_by_session_id)
        self.result_trace_widget.update_trace(
            self.session.display_candidates,
            self.session.results_by_session_id,
            self.session.knowledge_updates,
            self.session.report,
        )
        self.workflow_widget.refresh(
            self.session.workflow_run_id,
            self.session.stage,
            self.session.pending_confirmation,
        )
        self.knowledge_widget.refresh(self.session.task)
        self._refresh_knowledge_sidebar()
        self._refresh_live_view()
        self._update_overview_cards()
        self._sync_status_label_with_session()

    def _sync_status_label_with_session(self) -> None:
        if not self.session.task:
            self.status_label.setText(self.locale.text("status.waiting"))
            return
        self.status_label.setText(self.locale.text("queue.stage", stage=self._display_stage(self.session.stage)))

    def _refresh_live_view(self) -> None:
        results = list(self.session.results_by_session_id.values())
        if results:
            self.live_result_view.show_mode_shape(results[0])
            return
        if self.session.display_candidates:
            self.live_result_view.show_candidate(self.session.display_candidates[0])
            return
        self.live_result_view.reset_plotter(self.locale.text("live_view.empty"))

    def _start_conversation(self) -> None:
        instruction = self.input_line.text().strip()
        if not instruction:
            return
        self.session = PipelineSession(instruction=instruction)
        self.chat_widget.add_message("USER", instruction)
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
        self._refresh_knowledge_sidebar()
        self.status_label.setText(self.locale.text("status.knowledge_refreshed"))

    def _choose_report_output_dir(self) -> None:
        initial_dir = str(self.report_output_dir or RESULTS_DIR)
        selected_dir = QFileDialog.getExistingDirectory(self, self.locale.text("dialog.report_dir"), initial_dir)
        if not selected_dir:
            return
        self.report_output_dir = Path(selected_dir)
        self.status_label.setText(self.locale.text("status.report_dir", path=self.report_output_dir))

    def _open_latest_report(self) -> None:
        session_paths = [
            self.session.report.get("pdf_path") if self.session.report else None,
            self.session.report.get("markdown_path") if self.session.report else None,
        ]
        paths = [Path(str(path)) for path in session_paths if str(path or "").strip()]
        paths.extend([RESULTS_DIR / "latest_report.pdf", RESULTS_DIR / "latest_report.md"])
        for path in paths:
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

    def _selected_candidates_for_evaluation(self) -> list[dict]:
        return self.workbench_candidate_widget.selected_candidates()

    def _design_solution_candidate_set(self) -> list[dict]:
        if self.session.screened_candidates:
            return list(self.session.screened_candidates)
        if self.session.candidates:
            return list(self.session.candidates)
        return list(self.session.current_candidates)

    def _report_candidate_set(self) -> list[dict]:
        evaluated = set(self.session.results_by_session_id.keys())
        return [
            candidate
            for candidate in self.session.display_candidates
            if str(candidate.get("candidate_id")) in evaluated
        ]

    def _ordered_report_results(self) -> list[dict]:
        ordered_results: list[dict] = []
        used_keys: set[str] = set()
        for candidate in self.session.display_candidates:
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
        self._run_action(
            "screen",
            {"task": self.session.task, "candidates": self.session.candidates},
            "正在执行代理模型初筛",
        )

    def _start_evaluate_selected(self) -> None:
        if not self.session.task or not self.session.display_candidates:
            return
        selected = self._pending_candidates(self._selected_candidates_for_evaluation())
        if not selected:
            self.chat_widget.add_message("SYSTEM", self.locale.text("message.selected_done"))
            return
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
        self._run_action(
            "evaluate",
            {"task": self.session.task, "candidates": pending},
            f"正在校核全部 {len(pending)} 个当前候选",
        )

    def _start_report(self) -> None:
        if not self.session.task:
            return
        report_kind = str(self.report_type_selector.currentData() or "all")
        ordered_results = self._ordered_report_results()
        if report_kind == "design_solution":
            report_candidates = self._design_solution_candidate_set()
            if not report_candidates:
                return
        else:
            report_candidates = self._report_candidate_set()
            if not ordered_results:
                return
        output_dir = str(self.report_output_dir) if self.report_output_dir else None
        self._run_action(
            "report",
            {
                "task": self.session.task,
                "results": ordered_results,
                "candidates": report_candidates,
                "report_kind": report_kind,
                "output_dir": output_dir,
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
        self.workbench_candidate_widget.update_candidates([])
        self.result_trace_widget.update_trace([])
        self.workbench_candidate_widget.reset_view()
        self.live_result_view.reset_plotter(self.locale.text("live_view.empty"))
        self.result_trace_widget.reset_view()
        self.workflow_widget.reset_view()
        self.model_status_label.set_state(self.locale.text("model.current"), "success")
        self.flow_dag_widget.update_state(self._agent_state_map(), self.locale.text("queue.idle"))
        self.knowledge_widget.refresh(load_evidence=False)
        self._refresh_knowledge_sidebar()
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
            ui_agent = self._ui_agent_for_runtime_stage(runtime_stage, runtime_agent)
            self.log_widget.append_log(ui_agent, f"[{runtime_type}{suffix}] {message}")
            self.monitor_log_widget.append_log(ui_agent, f"[{runtime_type}{suffix}] {message}")
            self._refresh_run_selector()
            if run_id:
                self.workflow_widget.refresh(run_id, runtime_stage, self.session.pending_confirmation)
            return

        display_message = message
        if event_type == "llm_candidate_answer":
            excerpt = str(payload.get("answer_excerpt") or "").strip()
            if excerpt:
                display_message = f"{message}\n\n{excerpt}"

        self.chat_widget.add_message(sender_label, display_message)
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

        elif sender == "FLOW" and event_type == "screening_summary":
            ranked_candidates = payload.get("ranked_candidates")
            if isinstance(ranked_candidates, list) and ranked_candidates:
                self.session.candidates = ranked_candidates
            screened_candidates = payload.get("screened_candidates")
            if isinstance(screened_candidates, list):
                self.session.screened_candidates = screened_candidates
                self.session.evaluated_candidates = screened_candidates
                self.session.stage = "awaiting_fem_confirmation"
                self.session.pending_confirmation = "fem_evaluation"
                self._refresh_design_views()

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

        elif sender == "FLOW" and event_type == "report_summary":
            report = payload.get("report")
            if isinstance(report, dict):
                self.session.report = report
            self.session.stage = "completed"
            self.session.pending_confirmation = None
            self._refresh_design_views()

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
            ranked_candidates = payload.get("ranked_candidates")
            if isinstance(ranked_candidates, list) and ranked_candidates:
                self.session.candidates = ranked_candidates
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
            self.workbench_candidate_widget.reset_view()
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
    window._ensure_window_within_work_area(clamp_to_target=True)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())

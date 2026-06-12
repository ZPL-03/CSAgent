"""知识库上传、入库、检索和证据展示组件。"""

from __future__ import annotations

import json
import math
from dataclasses import asdict
from html import escape
from pathlib import Path
from typing import Any

from PyQt6.QtCore import QObject, QPointF, QRectF, QSize, QThread, Qt, pyqtSignal
from PyQt6.QtGui import QBrush, QColor, QFont, QFontMetrics, QPainter, QPen
from PyQt6.QtWidgets import (
    QFileDialog,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QFrame,
    QSplitter,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from core.case_memory import CaseMemoryIndex
from core.domain_knowledge import DomainKnowledgeBase
from core.knowledge_ingestion import KnowledgeIngestionService, SUPPORTED_QT_FILE_FILTER
from core.paths import ABAQUS_RUNS_DIR, CASES_DIR, CASE_LIBRARY_DIR, MODELS_DIR
from gui.theme import resolve_theme
from gui.workbench_widgets import PipelineStatusWidget, StatusPill


DEFAULT_EVIDENCE_QUERY = "复合材料外压圆柱耐压壳 外部静水压力 线性屈曲 极限压力 初始缺陷 制造质量控制"


class KnowledgeGraphView(QWidget):
    """运行时知识图谱可视化画布。"""

    def __init__(self) -> None:
        super().__init__()
        self.theme = "dark"
        self.entities: list[dict[str, Any]] = []
        self.relations: list[dict[str, Any]] = []
        self.highlight_relations: list[dict[str, Any]] = []
        self.setMinimumHeight(228)
        self.setSizePolicy(self.sizePolicy().horizontalPolicy(), self.sizePolicy().verticalPolicy())

    def sizeHint(self) -> QSize:
        return QSize(380, 248)

    def set_theme(self, theme: str) -> None:
        self.theme = resolve_theme(theme)
        self.update()

    def set_graph(
        self,
        entities: list[dict[str, Any]],
        relations: list[dict[str, Any]],
        highlight_relations: list[dict[str, Any]] | None = None,
    ) -> None:
        self.entities = list(entities)
        self.relations = list(relations)
        self.highlight_relations = list(highlight_relations or [])
        self.update()

    def _colors(self) -> dict[str, QColor]:
        if self.theme == "light":
            return {
                "bg": QColor("#ffffff"),
                "panel": QColor("#f8fbff"),
                "border": QColor("#c3cedd"),
                "text": QColor("#172033"),
                "muted": QColor("#64748b"),
                "edge": QColor("#94a3b8"),
                "highlight": QColor("#8b5cf6"),
            }
        return {
            "bg": QColor("#101821"),
            "panel": QColor("#111a28"),
            "border": QColor("#2b3a52"),
            "text": QColor("#dbe4ef"),
            "muted": QColor("#94a3b8"),
            "edge": QColor("#475569"),
            "highlight": QColor("#a78bfa"),
        }

    def _type_color(self, entity_type: str) -> QColor:
        palette = {
            "Material": "#38bdf8",
            "Structure": "#34d399",
            "FailureMode": "#f59e0b",
            "DesignFormula": "#a78bfa",
            "VerificationMethod": "#60a5fa",
            "ManufacturingProcess": "#fb7185",
        }
        return QColor(palette.get(entity_type, "#64748b"))

    def _node_payload(self) -> tuple[list[tuple[str, str]], list[dict[str, Any]], int, int]:
        node_types: dict[str, str] = {}
        for entity in self.entities:
            name = str(entity.get("name") or "").strip()
            if name:
                node_types[name] = str(entity.get("type") or "Entity")
        for relation in self.relations:
            source = str(relation.get("source") or "").strip()
            target = str(relation.get("target") or "").strip()
            if source:
                node_types.setdefault(source, str(relation.get("source_type") or "Entity"))
            if target:
                node_types.setdefault(target, str(relation.get("target_type") or "Entity"))
        degree: dict[str, int] = {name: 0 for name in node_types}
        for relation in self.relations:
            source = str(relation.get("source") or "").strip()
            target = str(relation.get("target") or "").strip()
            if source in degree:
                degree[source] += 1
            if target in degree:
                degree[target] += 1
        sorted_nodes = sorted(node_types.items(), key=lambda item: (-degree.get(item[0], 0), item[1], item[0]))
        max_nodes = 26
        visible_nodes = sorted_nodes[:max_nodes]
        visible_names = {name for name, _ in visible_nodes}
        visible_relations = [
            relation
            for relation in self.relations
            if str(relation.get("source") or "") in visible_names and str(relation.get("target") or "") in visible_names
        ][:42]
        return visible_nodes, visible_relations, len(node_types), len(self.relations)

    def paintEvent(self, event) -> None:
        colors = self._colors()
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), colors["bg"])

        panel = QRectF(1, 1, self.width() - 2, self.height() - 2)
        painter.setBrush(QBrush(colors["panel"]))
        painter.setPen(QPen(colors["border"], 1.0))
        painter.drawRoundedRect(panel, 12, 12)

        title_font = QFont(self.font())
        title_font.setPointSize(10)
        title_font.setBold(True)
        painter.setFont(title_font)
        painter.setPen(colors["text"])
        painter.drawText(QRectF(16, 12, self.width() - 32, 22), Qt.AlignmentFlag.AlignLeft, "知识图谱 · GRAPH")

        visible_nodes, visible_relations, total_nodes, total_relations = self._node_payload()
        subtitle = f"实体 {total_nodes} · 关系 {total_relations}"
        if total_nodes > len(visible_nodes) or total_relations > len(visible_relations):
            subtitle += f" · 显示核心子图 {len(visible_nodes)} / {len(visible_relations)}"
        small_font = QFont(self.font())
        small_font.setPointSize(8)
        painter.setFont(small_font)
        painter.setPen(colors["muted"])
        painter.drawText(QRectF(16, 35, self.width() - 32, 18), Qt.AlignmentFlag.AlignLeft, subtitle)

        if not visible_nodes:
            painter.drawText(
                QRectF(16, 58, self.width() - 32, self.height() - 80),
                Qt.AlignmentFlag.AlignCenter,
                "知识图谱等待资料入库或检索命中。",
            )
            return

        center = QPointF(self.width() / 2.0, self.height() / 2.0 + 18)
        radius_x = max(80.0, (self.width() - 88) / 2.0)
        radius_y = max(54.0, (self.height() - 120) / 2.0)
        positions: dict[str, QPointF] = {}
        count = len(visible_nodes)
        for index, (name, _entity_type) in enumerate(visible_nodes):
            angle = -math.pi / 2.0 + 2.0 * math.pi * index / max(1, count)
            positions[name] = QPointF(center.x() + radius_x * math.cos(angle), center.y() + radius_y * math.sin(angle))

        highlighted = {
            (
                str(relation.get("source") or ""),
                str(relation.get("relation") or ""),
                str(relation.get("target") or ""),
            )
            for relation in self.highlight_relations
        }
        for relation in visible_relations:
            source = str(relation.get("source") or "")
            target = str(relation.get("target") or "")
            if source not in positions or target not in positions:
                continue
            key = (source, str(relation.get("relation") or ""), target)
            edge_color = colors["highlight"] if key in highlighted else colors["edge"]
            pen = QPen(edge_color, 1.8 if key in highlighted else 1.0)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(pen)
            painter.drawLine(positions[source], positions[target])

        label_font = QFont(self.font())
        label_font.setPointSize(8)
        label_font.setBold(True)
        label_metrics = QFontMetrics(label_font)
        for name, entity_type in visible_nodes:
            point = positions[name]
            color = self._type_color(entity_type)
            painter.setBrush(QBrush(color))
            painter.setPen(QPen(colors["panel"], 1.5))
            painter.drawEllipse(point, 8, 8)
            label = label_metrics.elidedText(name, Qt.TextElideMode.ElideRight, 92)
            label_rect = QRectF(point.x() - 48, point.y() + 11, 96, 18)
            painter.setFont(label_font)
            painter.setPen(colors["text"])
            painter.drawText(label_rect, Qt.AlignmentFlag.AlignCenter, label)


class KnowledgeIngestWorker(QObject):
    """在后台线程执行资料入库。"""

    progress = pyqtSignal(list)
    finished = pyqtSignal(dict)
    failed = pyqtSignal(str)

    def __init__(self, paths: str | list[str]) -> None:
        super().__init__()
        if isinstance(paths, str):
            self.paths = [paths]
        else:
            self.paths = [str(path) for path in paths]

    def run(self) -> None:
        results: list[dict[str, Any]] = []
        failures: list[dict[str, str]] = []
        service = KnowledgeIngestionService(progress_callback=self.progress.emit)
        for path in self.paths:
            if not path:
                continue
            try:
                result = service.ingest_file(path)
            except Exception as exc:
                failures.append({"path": path, "error": str(exc)})
                continue
            payload = asdict(result)
            payload["success"] = result.success
            results.append(payload)
        if not results and failures:
            self.failed.emit("；".join(f"{Path(item['path']).name}: {item['error']}" for item in failures))
            return
        self.finished.emit(
            {
                "success": not failures,
                "results": results,
                "failures": failures,
                "batch_total": len([path for path in self.paths if path]),
                "batch_success_count": len(results),
                "batch_failed_count": len(failures),
            }
        )


class KnowledgeMaintenanceWorker(QObject):
    """在后台线程执行知识库维护操作。"""

    finished = pyqtSignal(dict)
    failed = pyqtSignal(str)

    def __init__(self, operation: str) -> None:
        super().__init__()
        self.operation = operation

    def run(self) -> None:
        try:
            service = KnowledgeIngestionService()
            if self.operation == "rebuild":
                self.finished.emit({"operation": self.operation, "result": service.rebuild_indexes()})
                return
            if self.operation == "export":
                path = service.export_snapshot()
                self.finished.emit({"operation": self.operation, "path": str(path)})
                return
            raise RuntimeError(f"未知知识库维护操作：{self.operation}")
        except Exception as exc:
            self.failed.emit(str(exc))


class KnowledgeWidget(QWidget):
    """管理项目内可更新 RAG/KG 知识库并展示检索证据。"""

    def __init__(self) -> None:
        super().__init__()
        self.knowledge_base = DomainKnowledgeBase()
        self.ingestion_service = KnowledgeIngestionService()
        self.theme = "dark"
        self._last_task: dict[str, Any] | None = None
        self._ingest_thread: QThread | None = None
        self._ingest_worker: KnowledgeIngestWorker | None = None
        self._maintenance_thread: QThread | None = None
        self._maintenance_worker: KnowledgeMaintenanceWorker | None = None

        self.store_pill = StatusPill("知识库待入库", "pending")
        self.rag_pill = StatusPill("RAG 0 chunks", "pending")
        self.vector_pill = StatusPill("Vector 0 chunks", "pending")
        self.kg_pill = StatusPill("KG 0 relations", "pending")
        self.parser_pill = StatusPill("解析器待调用", "pending")

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索知识库：外压圆柱壳 屈曲 缺陷敏感性 制造质量")
        self.search_button = QPushButton("执行混合检索")
        self.upload_button = QPushButton("上传资料并入库")
        self.batch_button = QPushButton("批量解析")
        self.rebuild_button = QPushButton("重建索引")
        self.export_snapshot_button = QPushButton("导出快照")
        self.refresh_button = QPushButton("刷新状态")

        self.document_table = QTableWidget(0, 6)
        self.document_table.setHorizontalHeaderLabels(["文档", "解析器", "Chunk", "SHA256", "入库时间", "路径"])
        self.document_table.setAlternatingRowColors(True)
        self.document_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for section in range(1, 5):
            self.document_table.horizontalHeader().setSectionResizeMode(section, QHeaderView.ResizeMode.ResizeToContents)
        self.document_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        self.document_table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.document_empty_state = QFrame()
        self.document_empty_state.setObjectName("settingsCard")
        empty_layout = QVBoxLayout(self.document_empty_state)
        empty_layout.setContentsMargins(18, 14, 18, 14)
        empty_layout.setSpacing(8)
        empty_title = QLabel("资料库等待入库")
        empty_title.setObjectName("sectionTitle")
        empty_body = QLabel("上传资料并入库后，这里显示解析器、Chunk、SHA256、入库时间和路径。")
        empty_body.setWordWrap(True)
        empty_hint = QLabel("支持解析、token 分块、overlap、内容去重、向量索引和 KG 实体关系抽取。")
        empty_hint.setObjectName("chatStatus")
        empty_hint.setWordWrap(True)
        empty_layout.addWidget(empty_title)
        empty_layout.addWidget(empty_body)
        empty_layout.addWidget(empty_hint)
        self.document_empty_state.setMinimumHeight(130)
        self.document_empty_state.setMaximumHeight(166)
        empty_page = QWidget()
        empty_page_layout = QVBoxLayout(empty_page)
        empty_page_layout.setContentsMargins(0, 0, 0, 0)
        empty_page_layout.setSpacing(0)
        empty_page_layout.addWidget(self.document_empty_state)
        empty_page_layout.addStretch(1)
        self.document_stack = QStackedWidget()
        self.document_stack.addWidget(empty_page)
        self.document_stack.addWidget(self.document_table)

        self.pipeline_widget = PipelineStatusWidget()
        self.graph_view = KnowledgeGraphView()
        self.evidence_browser = QTextBrowser()
        self.evidence_browser.setOpenExternalLinks(True)
        self.summary_browser = QTextBrowser()
        self.summary_browser.setMaximumHeight(210)
        self.summary_browser.setOpenExternalLinks(True)
        self.summary_browser.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.summary_browser.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self._build_layout()
        self._connect_signals()
        self.refresh(load_evidence=False)

    def set_theme(self, theme: str) -> None:
        self.theme = resolve_theme(theme)
        for pill in [self.store_pill, self.rag_pill, self.vector_pill, self.kg_pill, self.parser_pill]:
            pill.set_theme(self.theme)
        self.pipeline_widget.set_theme(self.theme)
        self.graph_view.set_theme(self.theme)
        self.refresh(query_text=self.search_input.text().strip(), load_evidence=bool(self.search_input.text().strip()))

    def _build_layout(self) -> None:
        top_layout = QHBoxLayout()
        top_layout.setSpacing(10)
        top_layout.addWidget(self.search_input, 1)
        top_layout.addWidget(self.search_button)

        action_layout = QHBoxLayout()
        action_layout.setSpacing(10)
        action_layout.addWidget(self.upload_button)
        action_layout.addWidget(self.batch_button)
        action_layout.addWidget(self.rebuild_button)
        action_layout.addWidget(self.export_snapshot_button)
        action_layout.addWidget(self.refresh_button)
        action_layout.addStretch(1)

        pill_layout = QHBoxLayout()
        pill_layout.setSpacing(10)
        for pill in [self.store_pill, self.rag_pill, self.vector_pill, self.kg_pill, self.parser_pill]:
            pill_layout.addWidget(pill)
        pill_layout.addStretch(1)

        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(12)
        left_layout.addWidget(self.summary_browser)
        left_layout.addWidget(QLabel("资料库 · DOCUMENTS"))
        left_layout.addWidget(self.document_stack, 1)

        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(12)
        right_layout.addWidget(self.pipeline_widget)
        right_layout.addWidget(QLabel("知识图谱 · GRAPH"))
        right_layout.addWidget(self.graph_view)
        right_layout.addWidget(QLabel("检索证据 · EVIDENCE"))
        right_layout.addWidget(self.evidence_browser, 1)

        splitter = QSplitter()
        splitter.addWidget(left)
        splitter.addWidget(right)
        splitter.setSizes([700, 390])

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)
        layout.addLayout(top_layout)
        layout.addLayout(action_layout)
        layout.addLayout(pill_layout)
        layout.addWidget(splitter, 1)

    def _connect_signals(self) -> None:
        self.search_button.clicked.connect(self._search_from_input)
        self.search_input.returnPressed.connect(self._search_from_input)
        self.upload_button.clicked.connect(self._select_and_ingest_file)
        self.batch_button.clicked.connect(self._select_and_ingest_files)
        self.rebuild_button.clicked.connect(lambda: self._run_maintenance("rebuild"))
        self.export_snapshot_button.clicked.connect(lambda: self._run_maintenance("export"))
        self.refresh_button.clicked.connect(lambda: self.refresh(load_evidence=False))

    def refresh(
        self,
        task: dict[str, Any] | None = None,
        query_text: str | None = None,
        load_evidence: bool = True,
    ) -> None:
        if task is not None:
            self._last_task = task
        self.knowledge_base = DomainKnowledgeBase()
        status = self.knowledge_base.status()
        ingest_status = self.ingestion_service.status()
        merged_status = {**status, **ingest_status}
        self._update_status_pills(merged_status)
        self._update_summary(merged_status)
        self._update_document_table()
        self._update_pipeline(merged_status)
        evidence_payload = self._retrieve_evidence(task, query_text) if load_evidence else {"query": "", "chunks": [], "relations": []}
        self._update_graph_view(evidence_payload)
        self.evidence_browser.setHtml(self._evidence_html(evidence_payload))

    def toHtml(self) -> str:
        """兼容测试和外部读取当前 HTML 摘要。"""
        return self.summary_browser.toHtml() + self.evidence_browser.toHtml()

    def _select_and_ingest_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "选择需要入库的资料",
            "",
            SUPPORTED_QT_FILE_FILTER,
        )
        if path:
            self.ingest_path(path)

    def _select_and_ingest_files(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(
            self,
            "选择需要批量解析入库的资料",
            "",
            SUPPORTED_QT_FILE_FILTER,
        )
        if paths:
            self.ingest_paths(paths)

    def ingest_path(self, path: str | Path) -> None:
        """供 GUI 和测试直接触发资料入库。"""
        self.ingest_paths([path])

    def ingest_paths(self, paths: list[str | Path]) -> None:
        """批量触发资料入库。"""
        if self._ingest_thread is not None:
            return
        normalized_paths = [str(path) for path in paths if str(path)]
        if not normalized_paths:
            return
        self._set_operation_buttons_enabled(False)
        self.parser_pill.set_state("解析运行中", "running")
        self.pipeline_widget.set_steps(
            [
                {"name": "MinerU / Docling 文档解析", "status": "running", "message": "正在解析上传资料"},
                {"name": "语义分块", "status": "pending", "message": "等待解析输出"},
                {"name": "BGE-M3 向量化索引", "status": "pending", "message": "等待文本块"},
                {"name": "Neo4j 实体/关系抽取", "status": "pending", "message": "等待文本块"},
                {"name": "检索验证 / 证据引用", "status": "pending", "message": "等待索引和关系写入"},
            ]
        )
        self._ingest_thread = QThread(self)
        self._ingest_worker = KnowledgeIngestWorker(normalized_paths)
        self._ingest_worker.moveToThread(self._ingest_thread)
        self._ingest_thread.started.connect(self._ingest_worker.run)
        self._ingest_worker.progress.connect(self._on_ingest_progress)
        self._ingest_worker.finished.connect(self._on_ingest_finished)
        self._ingest_worker.failed.connect(self._on_ingest_failed)
        self._ingest_worker.finished.connect(self._cleanup_ingest_worker)
        self._ingest_worker.failed.connect(self._cleanup_ingest_worker)
        self._ingest_thread.start()

    def _cleanup_ingest_worker(self) -> None:
        if self._ingest_thread is not None:
            self._ingest_thread.quit()
            self._ingest_thread.wait()
        self._ingest_thread = None
        self._ingest_worker = None
        self._set_operation_buttons_enabled(True)

    def _set_operation_buttons_enabled(self, enabled: bool) -> None:
        for button in [
            self.search_button,
            self.upload_button,
            self.batch_button,
            self.rebuild_button,
            self.export_snapshot_button,
            self.refresh_button,
        ]:
            button.setEnabled(enabled)

    def _on_ingest_progress(self, steps: list) -> None:
        self.pipeline_widget.set_steps(steps)
        active_step = next((step for step in steps if isinstance(step, dict) and step.get("status") == "running"), None)
        if isinstance(active_step, dict):
            self.parser_pill.set_state(str(active_step.get("name") or "入库运行中"), "running")

    def _on_ingest_finished(self, payload: dict) -> None:
        results = payload.get("results") if isinstance(payload.get("results"), list) else []
        last_result = results[-1] if results else payload
        steps = last_result.get("steps") if isinstance(last_result.get("steps"), list) else []
        self.pipeline_widget.set_steps(steps)
        success_count = int(payload.get("batch_success_count") or (1 if payload.get("success") else 0))
        failed_count = int(payload.get("batch_failed_count") or 0)
        status = "warning" if failed_count else "success"
        label = f"入库完成 {success_count} / 失败 {failed_count}" if payload.get("batch_total") else f"{payload.get('parser_backend') or '解析'} 完成"
        self.parser_pill.set_state(label, status)
        failure_html = ""
        if failed_count:
            failures = payload.get("failures") if isinstance(payload.get("failures"), list) else []
            detail = "<br>".join(escape(f"{Path(str(item.get('path') or '')).name}: {item.get('error') or ''}") for item in failures)
            failure_html = f"<h3>批量入库部分失败</h3><p>{detail}</p>"
        self.refresh(query_text=self.search_input.text().strip() or DEFAULT_EVIDENCE_QUERY)
        if failure_html:
            self.evidence_browser.setHtml(failure_html)

    def _on_ingest_failed(self, message: str) -> None:
        self.parser_pill.set_state("解析失败", "failed")
        self.pipeline_widget.set_steps(
            [
                {"name": "MinerU / Docling 文档解析", "status": "failed", "message": message},
                {"name": "语义分块", "status": "pending", "message": "解析失败，未生成文本块"},
                {"name": "BGE-M3 向量化索引", "status": "pending", "message": "解析失败，未更新索引"},
                {"name": "Neo4j 实体/关系抽取", "status": "pending", "message": "解析失败，未抽取关系"},
                {"name": "检索验证 / 证据引用", "status": "pending", "message": "解析失败，未生成证据"},
            ]
        )
        self.evidence_browser.setHtml(f"<h3>入库失败</h3><p>{escape(message)}</p>")

    def _run_maintenance(self, operation: str) -> None:
        if self._maintenance_thread is not None or self._ingest_thread is not None:
            return
        self._set_operation_buttons_enabled(False)
        if operation == "rebuild":
            self.parser_pill.set_state("重建索引中", "running")
            self.pipeline_widget.set_steps(
                [
                    {"name": "MinerU / Docling 文档解析", "status": "success", "message": "复用已解析资料"},
                    {"name": "语义分块", "status": "running", "message": "读取并去重文本块"},
                    {"name": "BGE-M3 向量化索引", "status": "pending", "message": "等待重建"},
                    {"name": "Neo4j 实体/关系抽取", "status": "pending", "message": "等待重建"},
                    {"name": "检索验证 / 证据引用", "status": "pending", "message": "等待验证"},
                ]
            )
        else:
            self.parser_pill.set_state("导出快照中", "running")
        self._maintenance_thread = QThread(self)
        self._maintenance_worker = KnowledgeMaintenanceWorker(operation)
        self._maintenance_worker.moveToThread(self._maintenance_thread)
        self._maintenance_thread.started.connect(self._maintenance_worker.run)
        self._maintenance_worker.finished.connect(self._on_maintenance_finished)
        self._maintenance_worker.failed.connect(self._on_maintenance_failed)
        self._maintenance_worker.finished.connect(self._cleanup_maintenance_worker)
        self._maintenance_worker.failed.connect(self._cleanup_maintenance_worker)
        self._maintenance_thread.start()

    def _cleanup_maintenance_worker(self) -> None:
        if self._maintenance_thread is not None:
            self._maintenance_thread.quit()
            self._maintenance_thread.wait()
        self._maintenance_thread = None
        self._maintenance_worker = None
        self._set_operation_buttons_enabled(True)

    def _on_maintenance_finished(self, payload: dict) -> None:
        operation = payload.get("operation")
        if operation == "rebuild":
            result = payload.get("result") if isinstance(payload.get("result"), dict) else {}
            steps = result.get("pipeline") if isinstance(result.get("pipeline"), list) else []
            if steps:
                self.pipeline_widget.set_steps(steps)
            self.refresh(query_text=self.search_input.text().strip() or DEFAULT_EVIDENCE_QUERY)
            self.parser_pill.set_state("索引重建完成", "success")
            return
        if operation == "export":
            path = str(payload.get("path") or "")
            self.refresh(load_evidence=False)
            self.parser_pill.set_state("快照已导出", "success")
            self.evidence_browser.setHtml(f"<h3>知识库快照已导出</h3><p>{escape(path)}</p>")

    def _on_maintenance_failed(self, message: str) -> None:
        self.parser_pill.set_state("维护失败", "failed")
        self.evidence_browser.setHtml(f"<h3>知识库维护失败</h3><p>{escape(message)}</p>")

    def _search_from_input(self) -> None:
        query = self.search_input.text().strip() or DEFAULT_EVIDENCE_QUERY
        self.search_input.setText(query)
        self.refresh(query_text=query)

    def _retrieve_evidence(self, task: dict[str, Any] | None, query_text: str | None) -> dict[str, Any]:
        if query_text is not None:
            query = query_text.strip() or DEFAULT_EVIDENCE_QUERY
            self.search_input.setText(query)
            return self.knowledge_base.retrieve_by_query(query, top_k=5, kg_top_k=8)
        active_task = task if task is not None else self._last_task
        if active_task:
            return self.knowledge_base.retrieve(active_task, top_k=5, kg_top_k=8)
        query = self.search_input.text().strip() or DEFAULT_EVIDENCE_QUERY
        self.search_input.setText(query)
        return self.knowledge_base.retrieve_by_query(query, top_k=5, kg_top_k=8)

    def _load_jsonl_rows(self, path: Path | str | None) -> list[dict[str, Any]]:
        if path is None:
            return []
        target = Path(path)
        if not target.exists():
            return []
        rows: list[dict[str, Any]] = []
        with target.open("r", encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                try:
                    payload = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(payload, dict):
                    rows.append(payload)
        return rows

    def _update_graph_view(self, evidence_payload: dict[str, Any]) -> None:
        entities_path = getattr(self.ingestion_service, "entities_path", None)
        relations_path = getattr(self.ingestion_service, "relations_path", None)
        entities = self._load_jsonl_rows(entities_path)
        relations = self._load_jsonl_rows(relations_path)
        evidence_relations = evidence_payload.get("relations") if isinstance(evidence_payload.get("relations"), list) else []
        if not relations and evidence_relations:
            relations = list(evidence_relations)
            entity_seen: set[tuple[str, str]] = set()
            entities = []
            for relation in relations:
                for name_key, type_key in [("source", "source_type"), ("target", "target_type")]:
                    name = str(relation.get(name_key) or "").strip()
                    entity_type = str(relation.get(type_key) or "Entity")
                    if not name or (entity_type, name) in entity_seen:
                        continue
                    entity_seen.add((entity_type, name))
                    entities.append({"type": entity_type, "name": name})
        self.graph_view.set_graph(entities, relations, evidence_relations)

    def _update_status_pills(self, status: dict[str, Any]) -> None:
        ready = bool(status.get("ready"))
        doc_count = int(status.get("document_count", 0) or status.get("structured_document_count", 0) or 0)
        chunk_count = int(status.get("rag_chunk_count", 0) or 0)
        vector_count = int(status.get("vector_chunk_count", 0) or 0)
        vector_status = str(status.get("vector_status") or "")
        vector_ready = bool(status.get("vector_ready")) and vector_status == "success"
        relation_count = int(status.get("kg_relation_count", 0) or 0)
        parser = (status.get("last_ingestion") or {}).get("parser_backend") if isinstance(status.get("last_ingestion"), dict) else ""
        self.store_pill.set_state(f"知识库 {doc_count} 文档", "success" if ready else "pending")
        self.rag_pill.set_state(f"RAG {chunk_count} chunks", "success" if chunk_count else "pending")
        vector_label = f"Vector {vector_count} chunks" if vector_count else f"Vector {vector_status or 'pending'}"
        vector_state = "success" if vector_ready else ("warning" if vector_status in {"warning", "failed"} else "pending")
        self.vector_pill.set_state(vector_label, vector_state)
        self.kg_pill.set_state(f"KG {relation_count} relations", "success" if relation_count else "pending")
        self.parser_pill.set_state(str(parser or "解析器待调用"), "success" if parser else "pending")

    def _update_summary(self, status: dict[str, Any]) -> None:
        metrics = self._load_metrics()
        archive_cases = sorted(CASES_DIR.glob("CASE_*.json"))
        formal_cases = sorted(CASE_LIBRARY_DIR.glob("CASE_*.json"))
        odb_count, vis_count = self._abaqus_archive_counts()
        chunk_size = status.get("chunk_token_size", "-")
        overlap = status.get("chunk_overlap_tokens", "-")
        last = status.get("last_ingestion") if isinstance(status.get("last_ingestion"), dict) else {}
        verification = status.get("last_retrieval_verification") if isinstance(status.get("last_retrieval_verification"), dict) else {}
        html = [
            "<h2>项目知识库状态</h2>",
            "<p>知识库由本项目运行时维护，用户上传资料后进入解析、分块、索引、实体关系抽取和检索验证流程；检索证据用于 LLM 工程上下文和人工审计，不替代代理公式或 FEM 结果。</p>",
            "<div style='display:grid;grid-template-columns:repeat(2,1fr);gap:8px;'>",
            self._summary_card("资料", f"{status.get('document_count', 0)} 文档"),
            self._summary_card("RAG", f"{status.get('rag_chunk_count', 0)} 文本块"),
            self._summary_card(
                "Vector",
                f"{status.get('vector_chunk_count', 0)} 向量块",
                f"后端 {status.get('vector_backend') or '-'}；状态 {status.get('vector_status') or '-'}",
            ),
            self._summary_card("KG", f"{status.get('kg_entity_count', 0)} 实体 / {status.get('kg_relation_count', 0)} 关系"),
            self._summary_card("分块", f"{chunk_size} token / overlap {overlap}"),
            self._summary_card("案例", f"会话 {len(archive_cases)} / 正式 {len(formal_cases)}"),
            self._summary_card("FEM", f"ODB {odb_count} / 云图 {vis_count}"),
            "</div>",
            f"<p><b>最后入库：</b>{escape(str(last.get('title') or '-'))}；<b>解析器：</b>{escape(str(last.get('parser_backend') or '-'))}</p>",
            f"<p><b>向量索引：</b>{escape(str(status.get('vector_status') or '-'))}；{escape(str(status.get('vector_message') or '-'))}</p>",
            f"<p><b>检索验证：</b>{escape(str(verification.get('message') or '-'))}</p>",
            f"<p><b>Manifest：</b>{escape(str(status.get('manifest_path') or '-'))}</p>",
        ]
        if metrics:
            html.append(
                "<p><b>代理模型：</b>"
                f"{escape(str(metrics.get('selected_model', '-')))}，训练样本 {escape(str(metrics.get('training_size', '-')))}</p>"
            )
        self.summary_browser.setHtml("".join(html))

    def _summary_card(self, title: str, value: str, detail: str = "") -> str:
        if self.theme == "light":
            border = "#c8d2df"
            background = "#f8fafc"
            muted = "#64748b"
            foreground = "#172033"
        else:
            border = "#2b3a52"
            background = "#111a28"
            muted = "#64748b"
            foreground = "#dbe4ef"
        detail_html = f"<br><span style='color:{muted};font-size:11px;'>{escape(detail)}</span>" if detail else ""
        return (
            f"<div style='border:1px solid {border};border-radius:8px;padding:8px 10px;background:{background};'>"
            f"<span style='color:{muted};font-size:12px;'>{escape(title)}</span><br>"
            f"<span style='font-size:18px;font-weight:800;color:{foreground};'>{escape(value)}</span>"
            f"{detail_html}</div>"
        )

    def _html_card_style(self) -> str:
        if self.theme == "light":
            return "border:1px solid #c8d2df;border-radius:10px;padding:10px;margin:8px 0;background:#f8fafc;"
        return "border:1px solid #2b3a52;border-radius:10px;padding:10px;margin:8px 0;background:#111a28;"

    def _update_document_table(self) -> None:
        documents_path = self.ingestion_service.documents_path
        rows = []
        if documents_path.exists():
            with documents_path.open("r", encoding="utf-8") as handle:
                for line in handle:
                    if not line.strip():
                        continue
                    try:
                        payload = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if isinstance(payload, dict):
                        rows.append(payload)
        self.document_table.setRowCount(len(rows))
        if not rows:
            self.document_stack.setCurrentIndex(0)
            return
        self.document_stack.setCurrentIndex(1)
        for row_index, item in enumerate(rows):
            values = [
                item.get("title") or item.get("file_name") or item.get("document_id") or "",
                item.get("parser_backend") or "",
                item.get("chunk_count") or 0,
                str(item.get("file_sha256") or "")[:12],
                item.get("updated_at") or "",
                item.get("stored_path") or "",
            ]
            for col_index, value in enumerate(values):
                self.document_table.setItem(row_index, col_index, QTableWidgetItem(str(value)))
        self.document_table.resizeRowsToContents()

    def _update_pipeline(self, status: dict[str, Any]) -> None:
        pipeline = status.get("pipeline") if isinstance(status.get("pipeline"), list) else []
        if pipeline:
            self.pipeline_widget.set_steps(pipeline)
            return
        self.pipeline_widget.set_steps(
            [
                {"name": "MinerU / Docling 文档解析", "status": "pending", "message": "等待用户上传资料"},
                {"name": "语义分块", "status": "pending", "message": "chunk_token_size / overlap 由配置控制"},
                {"name": "BGE-M3 向量化索引", "status": "pending", "message": "等待文本块写入索引"},
                {"name": "Neo4j 实体/关系抽取", "status": "pending", "message": "等待实体关系抽取"},
                {"name": "检索验证 / 证据引用", "status": "pending", "message": "等待可引用证据"},
            ]
        )

    def _load_metrics(self) -> dict[str, Any]:
        metrics_path = MODELS_DIR / "surrogate_metrics.json"
        if not metrics_path.exists():
            return {}
        try:
            payload = json.loads(metrics_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}
        return payload if isinstance(payload, dict) else {}

    def _abaqus_archive_counts(self) -> tuple[int, int]:
        odb_count = 0
        vis_count = 0
        for run_dir in ABAQUS_RUNS_DIR.glob("C*"):
            if (run_dir / f"{run_dir.name}.odb").exists():
                odb_count += 1
            if (run_dir / f"{run_dir.name}_mode1.json").exists():
                vis_count += 1
        return odb_count, vis_count

    def _case_memory_count(self) -> int:
        try:
            return int(CaseMemoryIndex().engine.count())
        except Exception:
            return 0

    def _evidence_html(self, payload: dict[str, Any]) -> str:
        query = str(payload.get("query") or "").strip()
        chunks = payload.get("chunks") if isinstance(payload.get("chunks"), list) else []
        relations = payload.get("relations") if isinstance(payload.get("relations"), list) else []
        lines = [
            "<h3>混合检索结果</h3>",
            f"<p><b>检索词：</b>{escape(query or '-')}</p>",
        ]
        lines.append("<h4>RAG 文本块</h4>")
        if chunks:
            for index, item in enumerate(chunks, start=1):
                title = item.get("document_title") or item.get("title") or item.get("record_id") or f"资料片段 {index}"
                source_parts = [
                    f"记录 {item.get('record_id')}" if item.get("record_id") else "",
                    f"页码 {self._page_text(item)}" if self._page_text(item) else "",
                    f"DOI {item.get('doi')}" if item.get("doi") else "",
                    str(item.get("source_url") or ""),
                ]
                source_line = " · ".join(escape(str(part)) for part in source_parts if part)
                lines.append(
                    f"<div style='{self._html_card_style()}'>"
                    f"<b>{index}. {escape(str(title))}</b><br>"
                    f"<span style='color:#34d399;'>score {escape(str(item.get('score', '-')))}</span><br>"
                    f"<span style='color:#64748b;'>{source_line}</span>"
                    f"<p>{escape(str(item.get('text') or ''))}</p>"
                    "</div>"
                )
        else:
            lines.append("<p>当前没有命中的 RAG 文本块。上传资料并完成入库后可检索。</p>")

        lines.append("<h4>知识图谱关系</h4>")
        if relations:
            for index, item in enumerate(relations, start=1):
                lines.append(
                    "<p>"
                    f"<b>{index}. {escape(str(item.get('source') or '-'))}({escape(str(item.get('source_type') or '-'))}) "
                    f"-[{escape(str(item.get('relation') or '-'))}]-&gt; "
                    f"{escape(str(item.get('target') or '-'))}({escape(str(item.get('target_type') or '-'))})</b><br>"
                    f"<span style='color:#34d399;'>score {escape(str(item.get('score', '-')))}</span>"
                    "</p>"
                )
        else:
            lines.append("<p>当前没有命中的知识图谱关系。</p>")
        return "".join(lines)

    def _page_text(self, item: dict[str, Any]) -> str:
        page_start = item.get("page_start")
        page_end = item.get("page_end")
        if page_start in (None, "", 0):
            return ""
        if page_end in (None, "", page_start, 0):
            return str(page_start)
        return f"{page_start}-{page_end}"

"""知识库上传、入库、检索和证据展示组件。"""

from __future__ import annotations

import json
from dataclasses import asdict
from html import escape
from pathlib import Path
from typing import Any

from PyQt6.QtCore import QObject, QThread, Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFileDialog,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from core.case_memory import CaseMemoryIndex
from core.domain_knowledge import DomainKnowledgeBase
from core.knowledge_ingestion import KnowledgeIngestionService
from core.paths import ABAQUS_RUNS_DIR, CASES_DIR, CASE_LIBRARY_DIR, MODELS_DIR
from gui.workbench_widgets import PipelineStatusWidget, StatusPill


DEFAULT_EVIDENCE_QUERY = "复合材料外压圆柱耐压壳 外部静水压力 线性屈曲 极限压力 初始缺陷 制造质量控制"


class KnowledgeIngestWorker(QObject):
    """在后台线程执行资料入库。"""

    progress = pyqtSignal(list)
    finished = pyqtSignal(dict)
    failed = pyqtSignal(str)

    def __init__(self, path: str) -> None:
        super().__init__()
        self.path = path

    def run(self) -> None:
        try:
            result = KnowledgeIngestionService(progress_callback=self.progress.emit).ingest_file(self.path)
        except Exception as exc:
            self.failed.emit(str(exc))
            return
        payload = asdict(result)
        payload["success"] = result.success
        self.finished.emit(payload)


class KnowledgeWidget(QWidget):
    """管理项目内可更新 RAG/KG 知识库并展示检索证据。"""

    def __init__(self) -> None:
        super().__init__()
        self.knowledge_base = DomainKnowledgeBase()
        self.ingestion_service = KnowledgeIngestionService()
        self._last_task: dict[str, Any] | None = None
        self._ingest_thread: QThread | None = None
        self._ingest_worker: KnowledgeIngestWorker | None = None

        self.store_pill = StatusPill("知识库待入库", "pending")
        self.rag_pill = StatusPill("RAG 0 chunks", "pending")
        self.vector_pill = StatusPill("Vector 0 chunks", "pending")
        self.kg_pill = StatusPill("KG 0 relations", "pending")
        self.parser_pill = StatusPill("解析器待调用", "pending")

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索知识库：外压圆柱壳 屈曲 缺陷敏感性 制造质量")
        self.search_button = QPushButton("执行混合检索")
        self.upload_button = QPushButton("上传资料并入库")
        self.refresh_button = QPushButton("刷新状态")

        self.document_table = QTableWidget(0, 6)
        self.document_table.setHorizontalHeaderLabels(["文档", "解析器", "Chunk", "SHA256", "入库时间", "路径"])
        self.document_table.setAlternatingRowColors(True)
        self.document_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for section in range(1, 5):
            self.document_table.horizontalHeader().setSectionResizeMode(section, QHeaderView.ResizeMode.ResizeToContents)
        self.document_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        self.document_table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.pipeline_widget = PipelineStatusWidget()
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

    def _build_layout(self) -> None:
        top_layout = QHBoxLayout()
        top_layout.setSpacing(10)
        top_layout.addWidget(self.search_input, 1)
        top_layout.addWidget(self.search_button)
        top_layout.addWidget(self.upload_button)
        top_layout.addWidget(self.refresh_button)

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
        left_layout.addWidget(self.document_table, 1)

        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(12)
        right_layout.addWidget(self.pipeline_widget)
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
        layout.addLayout(pill_layout)
        layout.addWidget(splitter, 1)

    def _connect_signals(self) -> None:
        self.search_button.clicked.connect(self._search_from_input)
        self.search_input.returnPressed.connect(self._search_from_input)
        self.upload_button.clicked.connect(self._select_and_ingest_file)
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
        self.evidence_browser.setHtml(self._evidence_html(evidence_payload))

    def toHtml(self) -> str:
        """兼容测试和外部读取当前 HTML 摘要。"""
        return self.summary_browser.toHtml() + self.evidence_browser.toHtml()

    def _select_and_ingest_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "选择需要入库的资料",
            "",
            "知识资料 (*.pdf *.docx *.pptx *.md *.markdown *.txt *.csv *.tsv *.xlsx *.xlsm *.png *.jpg *.jpeg *.inp *.py *.for *.f90 *.log);;所有文件 (*.*)",
        )
        if path:
            self.ingest_path(path)

    def ingest_path(self, path: str | Path) -> None:
        """供 GUI 和测试直接触发资料入库。"""
        if self._ingest_thread is not None:
            return
        self.upload_button.setEnabled(False)
        self.parser_pill.set_state("解析运行中", "running")
        self.pipeline_widget.set_steps(
            [
                {"name": "MinerU / Docling 文档解析", "status": "running", "message": "正在解析上传资料"},
                {"name": "语义分块", "status": "pending", "message": "等待解析输出"},
                {"name": "BGE-M3 向量化索引", "status": "pending", "message": "等待文本块"},
                {"name": "Neo4j 实体/关系抽取", "status": "pending", "message": "等待文本块"},
            ]
        )
        self._ingest_thread = QThread(self)
        self._ingest_worker = KnowledgeIngestWorker(str(path))
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
        self.upload_button.setEnabled(True)

    def _on_ingest_progress(self, steps: list) -> None:
        self.pipeline_widget.set_steps(steps)
        active_step = next((step for step in steps if isinstance(step, dict) and step.get("status") == "running"), None)
        if isinstance(active_step, dict):
            self.parser_pill.set_state(str(active_step.get("name") or "入库运行中"), "running")

    def _on_ingest_finished(self, payload: dict) -> None:
        steps = payload.get("steps") if isinstance(payload.get("steps"), list) else []
        self.pipeline_widget.set_steps(steps)
        self.parser_pill.set_state(f"{payload.get('parser_backend') or '解析'} 完成", "success")
        self.refresh(query_text=self.search_input.text().strip() or DEFAULT_EVIDENCE_QUERY)

    def _on_ingest_failed(self, message: str) -> None:
        self.parser_pill.set_state("解析失败", "failed")
        self.pipeline_widget.set_steps(
            [
                {"name": "MinerU / Docling 文档解析", "status": "failed", "message": message},
                {"name": "语义分块", "status": "pending", "message": "解析失败，未生成文本块"},
                {"name": "BGE-M3 向量化索引", "status": "pending", "message": "解析失败，未更新索引"},
                {"name": "Neo4j 实体/关系抽取", "status": "pending", "message": "解析失败，未抽取关系"},
            ]
        )
        self.evidence_browser.setHtml(f"<h3>入库失败</h3><p>{escape(message)}</p>")

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

    def _update_status_pills(self, status: dict[str, Any]) -> None:
        ready = bool(status.get("ready"))
        doc_count = int(status.get("document_count", 0) or status.get("structured_document_count", 0) or 0)
        chunk_count = int(status.get("rag_chunk_count", 0) or 0)
        vector_count = int(status.get("vector_chunk_count", 0) or 0)
        vector_ready = bool(status.get("vector_ready") or vector_count)
        relation_count = int(status.get("kg_relation_count", 0) or 0)
        parser = (status.get("last_ingestion") or {}).get("parser_backend") if isinstance(status.get("last_ingestion"), dict) else ""
        self.store_pill.set_state(f"知识库 {doc_count} 文档", "success" if ready else "pending")
        self.rag_pill.set_state(f"RAG {chunk_count} chunks", "success" if chunk_count else "pending")
        self.vector_pill.set_state(f"Vector {vector_count} chunks", "success" if vector_ready else "pending")
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
        html = [
            "<h2>项目知识库状态</h2>",
            "<p>知识库由本项目运行时维护，用户上传资料后进入解析、分块、索引和实体关系抽取流程；检索证据用于 LLM 工程上下文和人工审计，不替代代理公式或 FEM 结果。</p>",
            "<div style='display:grid;grid-template-columns:repeat(2,1fr);gap:8px;'>",
            self._summary_card("资料", f"{status.get('document_count', 0)} 文档"),
            self._summary_card("RAG", f"{status.get('rag_chunk_count', 0)} 文本块"),
            self._summary_card("Vector", f"{status.get('vector_chunk_count', 0)} 向量块"),
            self._summary_card("KG", f"{status.get('kg_entity_count', 0)} 实体 / {status.get('kg_relation_count', 0)} 关系"),
            self._summary_card("分块", f"{chunk_size} token / overlap {overlap}"),
            self._summary_card("案例", f"会话 {len(archive_cases)} / 正式 {len(formal_cases)}"),
            self._summary_card("FEM", f"ODB {odb_count} / 云图 {vis_count}"),
            "</div>",
            f"<p><b>最后入库：</b>{escape(str(last.get('title') or '-'))}；<b>解析器：</b>{escape(str(last.get('parser_backend') or '-'))}</p>",
            f"<p><b>Manifest：</b>{escape(str(status.get('manifest_path') or '-'))}</p>",
        ]
        if metrics:
            html.append(
                "<p><b>代理模型：</b>"
                f"{escape(str(metrics.get('selected_model', '-')))}，训练样本 {escape(str(metrics.get('training_size', '-')))}</p>"
            )
        self.summary_browser.setHtml("".join(html))

    def _summary_card(self, title: str, value: str) -> str:
        return (
            "<div style='border:1px solid #2b3a52;border-radius:8px;padding:8px 10px;background:#111a28;'>"
            f"<span style='color:#64748b;font-size:12px;'>{escape(title)}</span><br>"
            f"<span style='font-size:18px;font-weight:800;color:#dbe4ef;'>{escape(value)}</span>"
            "</div>"
        )

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
                    "<div style='border:1px solid #2b3a52;border-radius:10px;padding:10px;margin:8px 0;background:#111a28;'>"
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

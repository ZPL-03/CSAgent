from __future__ import annotations

import json
import os
import time

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication

from gui.knowledge_widget import KnowledgeWidget


def _app() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


class FakeKnowledge:
    def status(self) -> dict:
        return {
            "ready": True,
            "store_type": "project_runtime_knowledge",
            "document_count": 2,
            "rag_chunk_count": 9,
            "vector_ready": True,
            "vector_chunk_count": 9,
            "vector_status": "success",
            "vector_message": "向量索引写入 9 个文本块",
            "vector_detail": "collection=csdm_cph_project_knowledge，backend=hash_embedding",
            "vector_backend": "hash_embedding",
            "kg_entity_count": 7,
            "kg_relation_count": 12,
            "manifest_path": "knowledge/runtime/manifest.json",
            "chunk_token_size": 512,
            "chunk_overlap_tokens": 64,
            "pipeline": [
                {"name": "MinerU / Docling 文档解析", "status": "success", "message": "解析完成"},
                {"name": "语义分块", "status": "success", "message": "生成 9 个 RAG 文本块"},
                {"name": "BGE-M3 向量化索引", "status": "success", "message": "向量索引写入 9 个文本块"},
                {"name": "Neo4j 实体/关系抽取", "status": "success", "message": "抽取 12 条关系"},
                {"name": "检索验证 / 证据引用", "status": "success", "message": "检索命中 3 个当前文档证据"},
            ],
            "last_retrieval_verification": {"message": "检索命中 3 个当前文档证据"},
            "last_ingestion": {"title": "pressure_hull_notes", "parser_backend": "text"},
        }

    def retrieve_by_query(self, query: str, top_k: int | None = None, kg_top_k: int | None = None) -> dict:
        return self._payload(query)

    def retrieve(self, task: dict, top_k: int | None = None, kg_top_k: int | None = None) -> dict:
        return self._payload("复合材料外压圆柱耐压壳 线性屈曲 极限压力")

    def _payload(self, query: str) -> dict:
        return {
            "query": query,
            "chunks": [
                {
                    "score": 12.5,
                    "record_id": "DOC_1",
                    "source_id": "DOC_1",
                    "document_title": "Composite pressure hull buckling evidence",
                    "text": "外压圆柱壳的屈曲与初始缺陷敏感性需要结合有限元校核。",
                }
            ],
            "relations": [
                {
                    "score": 5.0,
                    "source": "Initial Imperfection",
                    "source_type": "FailureMode",
                    "relation": "CO_OCCURS_WITH",
                    "target": "Buckling",
                    "target_type": "FailureMode",
                    "record_id": "DOC_1",
                }
            ],
        }


class FakeIngestionService:
    def __init__(self, *args, **kwargs) -> None:
        self.documents_path = _DOCS_PATH

    def status(self) -> dict:
        return FakeKnowledge().status()

    def rebuild_indexes(self) -> dict:
        status = FakeKnowledge().status()
        status["last_reindex"] = {
            "document_count": status["document_count"],
            "rag_chunk_count": status["rag_chunk_count"],
            "kg_relation_count": status["kg_relation_count"],
        }
        return status

    def export_snapshot(self):
        path = _DOCS_PATH.parent / "knowledge_snapshot_test.json"
        path.write_text(
            json.dumps({"schema": "csagent_project_knowledge_snapshot_v1", "documents": [1]}, ensure_ascii=False),
            encoding="utf-8",
        )
        return path


def test_knowledge_widget_renders_runtime_pipeline_and_evidence(monkeypatch, tmp_path) -> None:
    global _DOCS_PATH
    _DOCS_PATH = tmp_path / "documents.jsonl"
    _DOCS_PATH.write_text(
        json.dumps(
            {
                "title": "pressure_hull_notes",
                "parser_backend": "text",
                "chunk_count": 9,
                "file_sha256": "abcdef1234567890",
                "updated_at": "2026-06-12T12:00:00+00:00",
                "stored_path": "knowledge/runtime/uploads/DOC_1.md",
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    monkeypatch.setattr("gui.knowledge_widget.DomainKnowledgeBase", FakeKnowledge)
    monkeypatch.setattr("gui.knowledge_widget.KnowledgeIngestionService", FakeIngestionService)

    app = _app()
    widget = KnowledgeWidget()
    try:
        widget.refresh(query_text="外压圆柱壳 屈曲")
        html = widget.toHtml()
        assert "项目知识库状态" in html
        assert "knowledge/runtime/manifest.json" in html
        assert "检索命中 3 个当前文档证据" in html
        assert "Composite pressure hull buckling evidence" in html
        assert "Initial Imperfection" in html
        assert widget.store_pill.text == "知识库 2 文档"
        assert widget.rag_pill.text == "RAG 9 chunks"
        assert widget.vector_pill.text == "Vector 9 chunks"
        assert widget.kg_pill.text == "KG 12 relations"
        assert widget.document_table.rowCount() == 1
        assert len(widget.graph_view.relations) == 1
        assert widget.graph_view.relations[0]["source"] == "Initial Imperfection"
    finally:
        widget.close()
        app.processEvents()


def test_knowledge_widget_vector_pill_follows_actual_vector_status(monkeypatch, tmp_path) -> None:
    global _DOCS_PATH
    _DOCS_PATH = tmp_path / "documents.jsonl"
    _DOCS_PATH.write_text("", encoding="utf-8")

    monkeypatch.setattr("gui.knowledge_widget.DomainKnowledgeBase", FakeKnowledge)
    monkeypatch.setattr("gui.knowledge_widget.KnowledgeIngestionService", FakeIngestionService)

    app = _app()
    widget = KnowledgeWidget()
    try:
        widget._update_status_pills(
            {
                "ready": True,
                "document_count": 1,
                "rag_chunk_count": 4,
                "vector_ready": False,
                "vector_chunk_count": 0,
                "vector_status": "warning",
                "kg_relation_count": 2,
            }
        )

        assert widget.vector_pill.text == "Vector warning"
        assert widget.vector_pill.status == "warning"
    finally:
        widget.close()
        app.processEvents()


def test_knowledge_widget_updates_pipeline_from_ingest_progress(monkeypatch, tmp_path) -> None:
    global _DOCS_PATH
    _DOCS_PATH = tmp_path / "documents.jsonl"
    _DOCS_PATH.write_text("", encoding="utf-8")

    monkeypatch.setattr("gui.knowledge_widget.DomainKnowledgeBase", FakeKnowledge)
    monkeypatch.setattr("gui.knowledge_widget.KnowledgeIngestionService", FakeIngestionService)

    app = _app()
    widget = KnowledgeWidget()
    try:
        widget._on_ingest_progress(
            [
                {"name": "MinerU / Docling 文档解析", "status": "success", "message": "解析完成"},
                {"name": "语义分块", "status": "running", "message": "正在生成文本块"},
                {"name": "BGE-M3 向量化索引", "status": "pending", "message": "等待文本块"},
                {"name": "Neo4j 实体/关系抽取", "status": "pending", "message": "等待文本块"},
                {"name": "检索验证 / 证据引用", "status": "pending", "message": "等待索引和关系写入"},
            ]
        )

        assert widget.pipeline_widget.steps[1].name == "语义分块"
        assert widget.pipeline_widget.steps[1].detail == "正在生成文本块"
        assert widget.pipeline_widget.steps[1].status == "running"
        assert widget.pipeline_widget.steps[4].name == "检索验证 / 证据引用"
        assert widget.parser_pill.text == "语义分块"
    finally:
        widget.close()
        app.processEvents()


def test_knowledge_widget_runs_rebuild_and_snapshot_actions(monkeypatch, tmp_path) -> None:
    global _DOCS_PATH
    _DOCS_PATH = tmp_path / "documents.jsonl"
    _DOCS_PATH.write_text(
        json.dumps(
            {
                "title": "pressure_hull_notes",
                "parser_backend": "text",
                "chunk_count": 9,
                "file_sha256": "abcdef1234567890",
                "updated_at": "2026-06-12T12:00:00+00:00",
                "stored_path": "knowledge/runtime/uploads/DOC_1.md",
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    monkeypatch.setattr("gui.knowledge_widget.DomainKnowledgeBase", FakeKnowledge)
    monkeypatch.setattr("gui.knowledge_widget.KnowledgeIngestionService", FakeIngestionService)

    app = _app()
    widget = KnowledgeWidget()
    try:
        for button in [
            widget.upload_button,
            widget.batch_button,
            widget.rebuild_button,
            widget.export_snapshot_button,
            widget.refresh_button,
        ]:
            assert button.isEnabled() is True

        widget._run_maintenance("rebuild")
        deadline = time.monotonic() + 10
        while widget._maintenance_thread is not None and time.monotonic() < deadline:
            app.processEvents()
            time.sleep(0.02)
        app.processEvents()

        assert widget._maintenance_thread is None
        assert widget.parser_pill.status == "success"
        assert widget.parser_pill.text == "索引重建完成"
        assert widget.pipeline_widget.steps[2].status == "success"

        widget._run_maintenance("export")
        deadline = time.monotonic() + 10
        while widget._maintenance_thread is not None and time.monotonic() < deadline:
            app.processEvents()
            time.sleep(0.02)
        app.processEvents()

        assert widget.parser_pill.text == "快照已导出"
        assert "knowledge_snapshot_test.json" in widget.toHtml()
        assert (_DOCS_PATH.parent / "knowledge_snapshot_test.json").exists()
        assert widget.export_snapshot_button.isEnabled() is True
    finally:
        widget.close()
        app.processEvents()


def test_knowledge_widget_runs_real_ingestion_pipeline(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("CSDM_cph_USE_HASH_EMBEDDING", "1")

    import gui.knowledge_widget as knowledge_module
    from core.domain_knowledge import DomainKnowledgeBase as RealDomainKnowledgeBase
    from core.knowledge_ingestion import KnowledgeIngestionService as RealKnowledgeIngestionService

    base_dir = tmp_path / "runtime_knowledge"
    vector_dir = base_dir / "chroma_db"
    config = {
        "project_knowledge": {
            "enabled": True,
            "base_dir": str(base_dir),
            "upload_dir": str(base_dir / "uploads"),
            "structured_dir": str(base_dir / "structured_text"),
            "manifest_path": str(base_dir / "manifest.json"),
            "rag_chunks_path": str(base_dir / "rag" / "rag_chunks.jsonl"),
            "kg_dir": str(base_dir / "kg"),
            "top_k": 5,
            "kg_top_k": 8,
            "max_snippet_chars": 1200,
            "chunk_token_size": 48,
            "chunk_overlap_tokens": 8,
            "min_chunk_tokens": 20,
            "vector_enabled": True,
            "vector_chroma_dir": str(vector_dir),
            "vector_collection_name": "csdm_cph_project_knowledge_test",
            "vector_top_k_multiplier": 2,
        }
    }

    class TempIngestionService(RealKnowledgeIngestionService):
        def __init__(self, *args, **kwargs) -> None:
            kwargs.setdefault("base_dir", base_dir)
            kwargs.setdefault("chunk_token_size", 48)
            kwargs.setdefault("chunk_overlap_tokens", 8)
            kwargs.setdefault("min_chunk_tokens", 20)
            super().__init__(*args, **kwargs)
            self.vector_chroma_dir = vector_dir
            self.vector_collection_name = "csdm_cph_project_knowledge_test"

    monkeypatch.setattr(knowledge_module, "KnowledgeIngestionService", TempIngestionService)
    monkeypatch.setattr(knowledge_module, "DomainKnowledgeBase", lambda: RealDomainKnowledgeBase(config))

    source = tmp_path / "pressure_hull_upload.md"
    source.write_text(
        "\n\n".join(
            [
                "# pressure_hull_upload",
                "复合材料外压圆柱耐压壳设计需要同时检查 ASME RD-1172 线性屈曲压力、PBIPF 极限压力预测和 ABAQUS 后屈曲校核。",
                "初始缺陷幅值、铺层角 alpha beta、壁厚、半径和长度会影响 buckling 与 ultimate pressure，制造阶段需要控制缠绕角偏差和固化质量。",
                "RAG 证据只用于候选提案上下文和人工审计，不替代代理公式、排序或有限元结果。",
            ]
        ),
        encoding="utf-8",
    )

    app = _app()
    widget = KnowledgeWidget()
    try:
        widget.search_input.setText("外压圆柱壳 ASME PBIPF buckling")
        widget.ingest_path(source)
        deadline = time.monotonic() + 45
        while widget._ingest_thread is not None and time.monotonic() < deadline:
            app.processEvents()
            time.sleep(0.05)
        app.processEvents()

        assert widget._ingest_thread is None
        assert widget.store_pill.text == "知识库 1 文档"
        assert widget.rag_pill.text.startswith("RAG ")
        assert widget.vector_pill.text.startswith("Vector ")
        assert widget.kg_pill.text.startswith("KG ")
        assert widget.parser_pill.status == "success"
        assert widget.document_table.rowCount() == 1
        assert widget.pipeline_widget.steps[0].status == "success"
        assert widget.pipeline_widget.steps[1].status == "success"
        assert widget.pipeline_widget.steps[2].status in {"success", "warning"}
        assert widget.pipeline_widget.steps[4].status in {"success", "warning"}
        assert len(widget.graph_view.entities) >= 1
        assert len(widget.graph_view.relations) >= 1

        manifest = json.loads((base_dir / "manifest.json").read_text(encoding="utf-8"))
        assert manifest["document_count"] == 1
        assert manifest["rag_chunk_count"] >= 1
        assert manifest["last_ingestion"]["title"] == "pressure_hull_upload"
        verification = manifest["last_retrieval_verification"]
        assert verification["hit_count"] >= 1
        assert len(verification["evidence_chunks"]) >= 1

        html = widget.toHtml()
        assert "pressure_hull_upload" in html
        assert "ASME" in html or "PBIPF" in html or "buckling" in html
    finally:
        widget.close()
        app.processEvents()

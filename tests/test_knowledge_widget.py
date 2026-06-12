from __future__ import annotations

import json
import os

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
    def __init__(self) -> None:
        self.documents_path = _DOCS_PATH

    def status(self) -> dict:
        return FakeKnowledge().status()


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

from __future__ import annotations

import json
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication

from core.paths import MODELS_DIR
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
            "rag_chunk_count": 51788,
            "kg_entity_count": 2214,
            "kg_relation_count": 480899,
            "manifest_path": "knowledge/external/manifest.json",
            "provenance_dir": "knowledge/external/provenance",
            "source_registry_count": 1931,
            "source_metadata_count": 1931,
            "structured_document_count": 1931,
            "structured_block_count": 400762,
            "table_record_count": 22800,
            "figure_record_count": 44135,
            "formula_record_count": 108500,
            "markdown_document_count": 1931,
            "updated_at": "2026-06-11T01:22:02",
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
                    "source_id": "SRC_1",
                    "document_title": "Composite pressure hull buckling evidence",
                    "page_start": 3,
                    "page_end": 4,
                    "doi": "10.1000/test",
                    "source_url": "https://example.test/paper",
                    "text": "外压圆柱壳的屈曲与初始缺陷敏感性需要结合有限元校核。",
                }
            ],
            "relations": [
                {
                    "score": 5.0,
                    "source": "Initial Imperfection",
                    "source_type": "Phenomenon",
                    "relation": "affects",
                    "target": "Buckling",
                    "target_type": "FailureMode",
                    "record_id": "DOC_1",
                    "evidence_document_title": "Composite pressure hull buckling evidence",
                }
            ],
        }


def test_knowledge_widget_renders_external_knowledge_status(monkeypatch) -> None:
    app = _app()
    metrics_path = MODELS_DIR / "surrogate_metrics.json"
    original_metrics = metrics_path.read_text(encoding="utf-8") if metrics_path.exists() else None
    try:
        metrics_path.parent.mkdir(parents=True, exist_ok=True)
        metrics_path.write_text(
            json.dumps(
                {
                    "selected_model": "rf",
                    "training_size": 128,
                    "rf": {"mape": 0.12, "rmse": 0.08},
                    "mlp": {"mape": 0.15, "rmse": 0.11},
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        monkeypatch.setattr("gui.knowledge_widget.DomainKnowledgeBase", FakeKnowledge)

        widget = KnowledgeWidget()
        try:
            widget.refresh()
            html = widget.toHtml()

            assert "知识库状态" in html
            assert "外部知识库/知识图谱状态" in html
            assert "知识库文本块数" in html
            assert "51788" in html
            assert "480899" in html
            assert "源元数据记录数" in html
            assert "结构化文本块数" in html
            assert "表格记录数" in html
            assert "图片记录数" in html
            assert "公式记录数" in html
            assert "knowledge/external/provenance" in html
            assert "代理模型指标" in html
            assert "128" in html
            assert "外部知识证据预览" in html
            assert "不作为确定性数值来源" in html
            assert "Composite pressure hull buckling evidence" in html
            assert "外压圆柱壳的屈曲与初始缺陷敏感性" in html
            assert "Initial Imperfection" in html
            assert "Buckling" in html
        finally:
            widget.close()
            app.processEvents()
    finally:
        if original_metrics is None:
            metrics_path.unlink(missing_ok=True)
        else:
            metrics_path.write_text(original_metrics, encoding="utf-8")

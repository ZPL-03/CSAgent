from __future__ import annotations

import gzip
import json
import os
import time

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtCore import QPoint, QPointF, Qt
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication

from gui.knowledge_widget import KnowledgeGraphView, KnowledgeWidget


def _app() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def _wait_until(app: QApplication, predicate, timeout: float = 3.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        app.processEvents()
        if predicate():
            return True
        time.sleep(0.02)
    app.processEvents()
    return predicate()


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
                {"name": "KG 实体/关系抽取", "status": "success", "message": "抽取 12 条关系"},
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
        assert "内置数据" in html
        assert "knowledge/runtime/manifest.json" in html
        assert "检索命中 3 个当前文档证据" in html
        assert "Composite pressure hull buckling evidence" in html
        assert "Initial Imperfection" in html
        assert widget.store_pill.text == "合并 RAG 9 块"
        assert widget.rag_pill.text == "RAG 9 块"
        assert widget.vector_pill.text == "Vector 9 向量块"
        assert widget.kg_pill.text == "KG 12 关系"
        assert widget.case_pill.text.startswith("案例库 ")
        assert widget.document_table.rowCount() == 1
        assert len(widget.graph_view.relations) == 1
        assert widget.graph_view.relations[0]["source"] == "Initial Imperfection"
        assert widget.graph_zoom_in_button.toolTip()
        assert widget.graph_zoom_out_button.toolTip()
        assert widget.graph_label_button.isChecked() is True
        assert widget.graph_relation_button.isChecked() is True
        assert widget.graph_type_filter.count() >= 2
        assert widget.graph_relation_filter.count() >= 2
        assert widget.graph_type_chip_buttons
        assert widget.graph_relation_chip_buttons
        assert widget.pipeline_widget.minimumHeight() >= 170
        assert len(widget.pipeline_widget.steps) == 5
        widget.resize(980, 760)
        widget.show()
        app.processEvents()
        assert widget.kg_pill.y() > widget.store_pill.y()
        assert widget.parser_pill.y() == widget.kg_pill.y()
        assert widget.case_pill.y() == widget.kg_pill.y()
    finally:
        widget.close()
        app.processEvents()


def test_knowledge_widget_graph_search_filters_visible_graph(monkeypatch, tmp_path) -> None:
    global _DOCS_PATH
    _DOCS_PATH = tmp_path / "documents.jsonl"
    _DOCS_PATH.write_text("", encoding="utf-8")

    monkeypatch.setattr("gui.knowledge_widget.DomainKnowledgeBase", FakeKnowledge)
    monkeypatch.setattr("gui.knowledge_widget.KnowledgeIngestionService", FakeIngestionService)

    app = _app()
    widget = KnowledgeWidget()
    try:
        widget.refresh(query_text="外压圆柱壳 屈曲")
        widget.graph_search_input.setText("Initial")
        app.processEvents()

        nodes, relations, total_nodes, total_relations = widget.graph_view._node_payload()

        assert total_nodes >= 2
        assert total_relations == 1
        assert {name for name, _type in nodes} == {"Initial Imperfection", "Buckling"}
        assert len(relations) == 1

        widget.graph_search_input.clear()
        app.processEvents()
        nodes, relations, _total_nodes, _total_relations = widget.graph_view._node_payload()
        assert len(nodes) >= 2
        assert len(relations) == 1

        relation_index = widget.graph_relation_filter.findData("CO_OCCURS_WITH")
        assert relation_index > 0
        widget.graph_relation_filter.setCurrentIndex(relation_index)
        app.processEvents()
        nodes, relations, _total_nodes, _total_relations = widget.graph_view._node_payload()
        assert {name for name, _type in nodes} == {"Initial Imperfection", "Buckling"}
        assert len(relations) == 1

        type_index = widget.graph_type_filter.findData("FailureMode")
        assert type_index > 0
        widget.graph_type_filter.setCurrentIndex(type_index)
        app.processEvents()
        nodes, relations, _total_nodes, _total_relations = widget.graph_view._node_payload()
        assert {name for name, _type in nodes} == {"Initial Imperfection", "Buckling"}
        assert len(relations) == 1
        assert any(button.isChecked() for button in widget.graph_type_chip_buttons)

        widget.graph_type_filter.setCurrentIndex(0)
        app.processEvents()
        relation_chip = next(button for button in widget.graph_relation_chip_buttons if "CO_OCCURS_WITH" in button.toolTip())
        relation_chip.setChecked(True)
        app.processEvents()
        assert widget.graph_view.active_relation_types == {"CO_OCCURS_WITH"}
        assert "总实体" in widget.graph_detail_browser.toHtml()
        widget.graph_relation_button.setChecked(False)
        app.processEvents()
        assert widget.graph_view.show_relations is True
        assert widget.graph_view.show_relation_labels is False
        widget.graph_relation_button.setChecked(True)
        app.processEvents()
        assert widget.graph_view.show_relations is True
        assert widget.graph_view.show_relation_labels is True

        widget.graph_view._selected_node_name = "Initial Imperfection"
        widget._update_graph_detail("Initial Imperfection")
        detail_html = widget.graph_detail_browser.toHtml()
        assert "选中节点" in detail_html
        assert "Initial Imperfection" in detail_html
    finally:
        widget.close()
        app.processEvents()


def test_knowledge_widget_default_graph_uses_builtin_kg_without_query(monkeypatch, tmp_path) -> None:
    builtin_kg = tmp_path / "csllm" / "kg"
    builtin_kg.mkdir(parents=True)
    (builtin_kg / "entities.jsonl").write_text(
        "\n".join(
            [
                json.dumps({"type": "DesignFormula", "name": "ASME RD-1172"}, ensure_ascii=False),
                json.dumps({"type": "FailureMode", "name": "Buckling"}, ensure_ascii=False),
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    with gzip.open(builtin_kg / "relations.compact.jsonl.gz", "wt", encoding="utf-8") as handle:
        handle.write(
            json.dumps(
                {
                    "source": "ASME RD-1172",
                    "source_type": "DesignFormula",
                    "relation": "PREDICTS",
                    "target": "Buckling",
                    "target_type": "FailureMode",
                    "record_id": "BUILTIN_DOC",
                },
                ensure_ascii=False,
            )
            + "\n"
        )

    class BuiltinOnlyKnowledge(FakeKnowledge):
        def status(self) -> dict:
            status = super().status()
            status.update(
                {
                    "document_count": 0,
                    "runtime_document_count": 0,
                    "runtime_rag_chunk_count": 0,
                    "runtime_kg_entity_count": 0,
                    "runtime_kg_relation_count": 0,
                    "builtin_rag_chunk_count": 1,
                    "builtin_kg_entity_count": 2,
                    "builtin_kg_relation_count": 1,
                    "rag_chunk_count": 1,
                    "kg_entity_count": 2,
                    "kg_relation_count": 1,
                }
            )
            return status

    class BuiltinOnlyIngestion(FakeIngestionService):
        def __init__(self, *args, **kwargs) -> None:
            super().__init__(*args, **kwargs)
            self.builtin_kg_dir = builtin_kg

    global _DOCS_PATH
    _DOCS_PATH = tmp_path / "documents.jsonl"
    _DOCS_PATH.write_text("", encoding="utf-8")
    monkeypatch.setattr("gui.knowledge_widget.DomainKnowledgeBase", BuiltinOnlyKnowledge)
    monkeypatch.setattr("gui.knowledge_widget.KnowledgeIngestionService", BuiltinOnlyIngestion)

    app = _app()
    widget = KnowledgeWidget()
    try:
        widget.refresh(load_evidence=False)

        assert widget.graph_view.relations
        assert widget.graph_view.relations[0]["source"] == "ASME RD-1172"
        assert widget.graph_view.relations[0]["target"] == "Buckling"
        assert widget.graph_view.highlight_relations == []
    finally:
        widget.close()
        app.processEvents()


def test_knowledge_graph_view_filters_and_resets_interactive_state() -> None:
    app = _app()
    _ = app
    graph = KnowledgeGraphView()
    try:
        graph.set_graph(
            entities=[
                {"name": "ASME RD-1172", "type": "DesignFormula"},
                {"name": "Buckling", "type": "FailureMode"},
                {"name": "Manufacturing Quality", "type": "ManufacturingProcess"},
            ],
            relations=[
                {"source": "ASME RD-1172", "relation": "PREDICTS", "target": "Buckling"},
                {"source": "Manufacturing Quality", "relation": "AFFECTS", "target": "Buckling"},
            ],
        )
        all_nodes, all_relations, _, _ = graph._node_payload()
        assert len(all_nodes) == 3
        assert len(all_relations) == 2

        graph.set_filter_text("ASME")
        filtered_nodes, filtered_relations, _, _ = graph._node_payload()
        assert {name for name, _type in filtered_nodes} == {"ASME RD-1172", "Buckling"}
        assert len(filtered_relations) == 1

        graph.set_filter_text("")
        graph.set_type_filter({"DesignFormula"})
        filtered_nodes, filtered_relations, _, _ = graph._node_payload()
        assert {name for name, _type in filtered_nodes} == {"ASME RD-1172", "Buckling"}
        assert len(filtered_relations) == 1

        graph.set_type_filter(set())
        graph.set_relation_filter({"AFFECTS"})
        filtered_nodes, filtered_relations, _, _ = graph._node_payload()
        assert {name for name, _type in filtered_nodes} == {"Manufacturing Quality", "Buckling"}
        assert len(filtered_relations) == 1
        type_options, relation_options = graph.filter_options()
        assert ("DesignFormula", 1) in type_options
        assert ("AFFECTS", 1) in relation_options

        graph._scale = 1.8
        graph._pan = QPointF(24.0, -12.0)
        graph._manual_node_offsets["ASME RD-1172"] = QPointF(16.0, 8.0)
        graph.reset_view()
        assert graph._scale == 1.0
        assert graph._pan.x() == 0.0
        assert graph._pan.y() == 0.0
        assert graph._manual_node_offsets == {}

        graph.zoom_by(1.4)
        assert graph._scale > 1.0
        graph.set_show_labels(False)
        assert graph.show_labels is False
        graph.set_show_labels(True)
        assert graph.show_labels is True
    finally:
        graph.close()
        app.processEvents()


def test_knowledge_graph_view_pans_with_mouse_drag() -> None:
    app = _app()
    graph = KnowledgeGraphView()
    try:
        graph.resize(420, 260)
        graph.set_graph(
            entities=[
                {"name": "ASME RD-1172", "type": "DesignFormula"},
                {"name": "Buckling", "type": "FailureMode"},
            ],
            relations=[{"source": "ASME RD-1172", "relation": "PREDICTS", "target": "Buckling"}],
        )
        graph.show()
        app.processEvents()

        QTest.mousePress(graph, Qt.MouseButton.LeftButton, pos=QPoint(28, 232))
        QTest.mouseMove(graph, QPoint(78, 246))
        QTest.mouseRelease(graph, Qt.MouseButton.LeftButton, pos=QPoint(78, 246))
        app.processEvents()

        assert graph._pan.x() != 0.0
        assert graph._pan.y() != 0.0
    finally:
        graph.close()
        app.processEvents()


def test_knowledge_graph_view_drags_visible_node() -> None:
    app = _app()
    graph = KnowledgeGraphView()
    try:
        graph.resize(420, 260)
        graph.set_graph(
            entities=[
                {"name": "ASME RD-1172", "type": "DesignFormula"},
                {"name": "Buckling", "type": "FailureMode"},
                {"name": "Manufacturing Quality", "type": "ManufacturingProcess"},
            ],
            relations=[
                {"source": "ASME RD-1172", "relation": "PREDICTS", "target": "Buckling"},
                {"source": "Manufacturing Quality", "relation": "AFFECTS", "target": "Buckling"},
            ],
        )
        graph.show()
        app.processEvents()
        graph.grab()
        app.processEvents()

        start = graph._last_node_positions["ASME RD-1172"]
        start_point = QPoint(int(start.x()), int(start.y()))
        end_point = QPoint(int(start.x() + 34), int(start.y() + 18))
        QTest.mousePress(graph, Qt.MouseButton.LeftButton, pos=start_point)
        QTest.mouseMove(graph, end_point)
        QTest.mouseRelease(graph, Qt.MouseButton.LeftButton, pos=end_point)
        app.processEvents()

        offset = graph._manual_node_offsets.get("ASME RD-1172")
        assert offset is not None
        assert offset.x() != 0.0
        assert offset.y() != 0.0
    finally:
        graph.close()
        app.processEvents()


def test_knowledge_graph_view_default_layout_fits_canvas() -> None:
    app = _app()
    graph = KnowledgeGraphView()
    try:
        graph.resize(680, 360)
        entities = [{"name": f"Node {index}", "type": "Material" if index % 3 == 0 else "Structure"} for index in range(50)]
        relations = [
            {
                "source": f"Node {index % 50}",
                "relation": "RELATED_TO" if index % 2 else "AFFECTS",
                "target": f"Node {(index * 7 + 3) % 50}",
                "source_type": "Material",
                "target_type": "Structure",
            }
            for index in range(90)
        ]
        graph.set_graph(entities=entities, relations=relations)
        _nodes, visible_relations, _total_nodes, total_relations = graph._node_payload()
        assert total_relations == 90
        assert len(visible_relations) <= 28

        graph.set_filter_text("Node")
        _nodes, filtered_relations, _total_nodes, _total_relations = graph._node_payload()
        assert len(filtered_relations) > len(visible_relations)
        graph.set_filter_text("")

        graph.show()
        app.processEvents()
        graph.grab()
        app.processEvents()

        assert graph._last_node_positions
        xs = [point.x() for point in graph._last_node_positions.values()]
        ys = [point.y() for point in graph._last_node_positions.values()]
        assert min(xs) >= 40
        assert max(xs) <= graph.width() - 40
        assert min(ys) >= 64
        assert max(ys) <= graph.height() - 36
    finally:
        graph.close()
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
                {"name": "KG 实体/关系抽取", "status": "pending", "message": "等待文本块"},
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
        assert _wait_until(app, lambda: widget.parser_pill.text == "索引重建完成")

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


def test_knowledge_widget_toolbar_buttons_click_through(monkeypatch, tmp_path) -> None:
    global _DOCS_PATH
    _DOCS_PATH = tmp_path / "documents.jsonl"
    _DOCS_PATH.write_text("", encoding="utf-8")
    upload_file = tmp_path / "upload.md"
    upload_file.write_text("复合材料耐压壳外压屈曲证据。", encoding="utf-8")
    batch_file = tmp_path / "batch.md"
    batch_file.write_text("PBIPF 与 ASME RD-1172 校核证据。", encoding="utf-8")

    monkeypatch.setattr("gui.knowledge_widget.DomainKnowledgeBase", FakeKnowledge)
    monkeypatch.setattr("gui.knowledge_widget.KnowledgeIngestionService", FakeIngestionService)
    monkeypatch.setattr(
        "gui.knowledge_widget.QFileDialog.getOpenFileName",
        lambda *args, **kwargs: (str(upload_file), "Markdown (*.md)"),
    )
    monkeypatch.setattr(
        "gui.knowledge_widget.QFileDialog.getOpenFileNames",
        lambda *args, **kwargs: ([str(upload_file), str(batch_file)], "Markdown (*.md)"),
    )

    app = _app()
    widget = KnowledgeWidget()
    operations: list[tuple[str, object]] = []

    def record_ingest_path(path) -> None:
        operations.append(("ingest_path", str(path)))

    def record_ingest_paths(paths) -> None:
        operations.append(("ingest_paths", [str(path) for path in paths]))

    def record_maintenance(operation: str) -> None:
        operations.append(("maintenance", operation))

    try:
        widget.ingest_path = record_ingest_path
        widget.ingest_paths = record_ingest_paths
        widget._run_maintenance = record_maintenance

        widget.upload_button.click()
        widget.batch_button.click()
        widget.rebuild_button.click()
        widget.export_snapshot_button.click()
        widget.refresh_button.click()
        widget.graph_search_input.setText("Damage")
        widget.search_input.setText("屈曲 失效")
        widget.search_button.click()
        widget.graph_zoom_in_button.click()
        widget.graph_zoom_out_button.click()
        widget.graph_reset_button.click()
        widget.graph_label_button.click()
        widget.graph_relation_button.click()
        assert _wait_until(app, lambda: "屈曲" in widget.evidence_browser.toPlainText())

        assert ("ingest_path", str(upload_file)) in operations
        assert ("ingest_paths", [str(upload_file), str(batch_file)]) in operations
        assert ("maintenance", "rebuild") in operations
        assert ("maintenance", "export") in operations
        assert widget.graph_view.show_labels is False
        assert widget.graph_view.show_relation_labels is False
        assert "屈曲" in widget.evidence_browser.toPlainText()
    finally:
        widget.close()
        app.processEvents()


def test_knowledge_case_pill_deduplicates_formal_case_records(monkeypatch, tmp_path) -> None:
    cases_dir = tmp_path / "cases"
    library_dir = tmp_path / "case_library"
    cases_dir.mkdir()
    library_dir.mkdir()
    for case_id in ["CASE_1", "CASE_2"]:
        (cases_dir / f"{case_id}.json").write_text("{}", encoding="utf-8")
    (library_dir / "CASE_2.json").write_text("{}", encoding="utf-8")

    monkeypatch.setattr("gui.knowledge_widget.CASES_DIR", cases_dir)
    monkeypatch.setattr("gui.knowledge_widget.CASE_LIBRARY_DIR", library_dir)

    app = _app()
    widget = KnowledgeWidget()
    try:
        widget._update_status_pills({"ready": True, "rag_chunk_count": 1})

        assert widget.case_pill.text == "案例库 2 / 正式 1"
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
        assert widget.store_pill.text == "合并 RAG 51794 块"
        assert widget.rag_pill.text.startswith("RAG ")
        assert widget.vector_pill.text.startswith("Vector ")
        assert widget.kg_pill.text.startswith("KG ")
        assert widget.case_pill.text.startswith("案例库 ")
        assert widget.parser_pill.status == "success"
        assert widget.document_table.rowCount() == 1
        assert _wait_until(
            app,
            lambda: widget._refresh_thread is None and len(widget.graph_view.entities) >= 1 and len(widget.graph_view.relations) >= 1,
            timeout=10.0,
        )
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

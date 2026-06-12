from __future__ import annotations

import json

from core.knowledge_ingestion import KnowledgeIngestionService, SUPPORTED_INGEST_SUFFIXES, SUPPORTED_QT_FILE_FILTER


def test_runtime_knowledge_ingestion_builds_chunks_kg_vector_index_and_dedupes(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CSDM_cph_USE_HASH_EMBEDDING", "1")
    source = tmp_path / "pressure_hull_notes.md"
    source.write_text(
        "\n\n".join(
            [
                "# 复合材料外压圆柱耐压壳设计",
                "T700 碳纤维/环氧复合材料 pressure hull 在 external pressure 下需要关注 buckling 和 imperfection sensitivity。",
                "ASME RD-1172 用于线性屈曲压力估算，PBIPF 用于极限压力预测，Abaqus Lanczos 与 Riks 用于有限元验证。",
                "制造上需要控制 filament winding 张力、固化过程和铺层角度偏差，避免分层和初始缺陷放大。",
                "这些信息用于 RAG 检索、KG 实体关系抽取和报告解释，不替代 FEM 结果。",
            ]
        ),
        encoding="utf-8",
    )

    service = KnowledgeIngestionService(base_dir=tmp_path / "knowledge", chunk_token_size=48, chunk_overlap_tokens=8)
    first = service.ingest_file(source)
    second = service.ingest_file(source)

    assert first.success
    assert second.success
    assert first.document_id == second.document_id
    assert first.chunk_count >= 1
    assert first.entity_count >= 3
    assert first.relation_count >= 1
    assert first.retrieval_verification["status"] == "success"
    assert first.retrieval_verification["evidence_chunks"]

    manifest = json.loads(service.manifest_path.read_text(encoding="utf-8"))
    assert manifest["document_count"] == 1
    assert manifest["rag_chunk_count"] == first.chunk_count
    assert manifest["chunk_token_size"] == 48
    assert manifest["chunk_overlap_tokens"] == 8
    assert manifest["dedupe_key"] == "content_hash"
    assert manifest["vector_chunk_count"] == first.chunk_count
    assert manifest["vector_collection_name"] == "csdm_cph_project_knowledge"
    assert manifest["last_ingestion"]["steps"][2]["status"] == "success"
    assert manifest["last_ingestion"]["steps"][4]["name"] == "检索验证 / 证据引用"
    assert manifest["last_ingestion"]["steps"][4]["status"] == "success"
    assert manifest["last_ingestion"]["retrieval_verification"]["hit_count"] >= 1
    assert manifest["last_retrieval_verification"]["evidence_chunks"]

    chunks = [json.loads(line) for line in service.chunks_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(chunks) == first.chunk_count
    assert all(item["token_estimate"] <= 56 for item in chunks)
    assert len({item["content_hash"] for item in chunks}) == len(chunks)

    relations = [json.loads(line) for line in service.relations_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    chunk_ids = {item["chunk_id"] for item in chunks}
    assert all(item["evidence_chunk_id"] in chunk_ids for item in relations)


def test_runtime_knowledge_ingestion_emits_step_progress(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CSDM_cph_USE_HASH_EMBEDDING", "1")
    source = tmp_path / "pressure_hull_progress.md"
    source.write_text(
        "\n\n".join(
            [
                "# 复合材料外压圆柱耐压壳",
                "T800G composite pressure hull 在 external pressure 下需要关注 buckling 和 imperfection sensitivity。",
                "ASME RD-1172、PBIPF、Abaqus Lanczos 与 Static Riks 用于校核设计结果。",
                "filament winding、curing 和铺层角度偏差是制造质量控制重点。",
            ]
        ),
        encoding="utf-8",
    )

    progress_events: list[list[dict]] = []

    service = KnowledgeIngestionService(
        base_dir=tmp_path / "knowledge",
        chunk_token_size=40,
        chunk_overlap_tokens=6,
        progress_callback=lambda steps: progress_events.append([dict(step) for step in steps]),
    )
    result = service.ingest_file(source)

    assert result.success
    assert len(progress_events) >= 4
    assert progress_events[0][0]["status"] == "running"
    assert any(event[1]["status"] == "running" for event in progress_events)
    assert any(event[2]["status"] == "running" for event in progress_events)
    assert progress_events[-1][0]["status"] == "success"
    assert progress_events[-1][1]["status"] == "success"
    assert progress_events[-1][2]["status"] == "success"
    assert progress_events[-1][3]["status"] in {"success", "warning"}
    assert progress_events[-1][4]["name"] == "检索验证 / 证据引用"
    assert progress_events[-1][4]["status"] == "success"


def test_runtime_knowledge_rebuild_and_snapshot_export(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CSDM_cph_USE_HASH_EMBEDDING", "1")
    source = tmp_path / "pressure_hull_rebuild.md"
    source.write_text(
        "\n\n".join(
            [
                "# 外压耐压壳知识入库",
                "composite pressure hull 在 external pressure 下需要结合 ASME RD-1172、PBIPF 与 Abaqus 校核。",
                "buckling、postbuckling、initial imperfection 与 filament winding 质量控制都需要进入证据链。",
            ]
        ),
        encoding="utf-8",
    )

    service = KnowledgeIngestionService(base_dir=tmp_path / "knowledge", chunk_token_size=42, chunk_overlap_tokens=6)
    result = service.ingest_file(source)
    assert result.success

    rebuilt = service.rebuild_indexes()

    assert rebuilt["document_count"] == 1
    assert rebuilt["rag_chunk_count"] >= 1
    assert rebuilt["kg_entity_count"] >= 1
    assert rebuilt["kg_relation_count"] >= 1
    assert rebuilt["last_reindex"]["duplicate_chunk_count"] == 0
    assert rebuilt["last_retrieval_verification"]["hit_count"] >= 1
    assert rebuilt["pipeline"][0]["name"] == "MinerU / Docling 文档解析"
    assert rebuilt["pipeline"][2]["name"] == "BGE-M3 向量化索引"

    snapshot_path = service.export_snapshot()
    payload = json.loads(snapshot_path.read_text(encoding="utf-8"))

    assert payload["schema"] == "csagent_project_knowledge_snapshot_v1"
    assert payload["manifest"]["document_count"] == 1
    assert len(payload["documents"]) == 1
    assert len(payload["chunks"]) == rebuilt["rag_chunk_count"]
    assert len(payload["entities"]) == rebuilt["kg_entity_count"]
    assert len(payload["relations"]) == rebuilt["kg_relation_count"]


def test_runtime_knowledge_ingestion_accepts_engineering_text_and_binary_metadata(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CSDM_cph_USE_HASH_EMBEDDING", "1")
    service = KnowledgeIngestionService(base_dir=tmp_path / "knowledge", chunk_token_size=48, chunk_overlap_tokens=8)

    status_file = tmp_path / "buckling_job.sta"
    status_file.write_text(
        "Abaqus Lanczos buckling step completed for composite pressure hull. PBIPF and ASME RD-1172 are checked.",
        encoding="utf-8",
    )
    status_result = service.ingest_file(status_file)

    odb_file = tmp_path / "buckling_job.odb"
    odb_file.write_bytes(b"ODB_BINARY_PLACEHOLDER")
    odb_result = service.ingest_file(odb_file)

    assert status_result.success
    assert status_result.parser_backend == "text"
    assert odb_result.success
    assert odb_result.parser_backend == "engineering_metadata"
    assert odb_result.chunk_count >= 1

    chunks = [json.loads(line) for line in service.chunks_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    odb_chunks = [item for item in chunks if item.get("source_id") == odb_result.document_id]
    assert odb_chunks
    assert any("工程二进制文件元数据" in item.get("content_markdown", "") for item in odb_chunks)


def test_runtime_knowledge_supported_suffix_contract_is_shared_with_gui_filter() -> None:
    for suffix in [".pdf", ".docx", ".pptx", ".xlsx", ".png", ".webp", ".inp", ".sta", ".odb"]:
        assert suffix in SUPPORTED_INGEST_SUFFIXES
        assert f"*{suffix}" in SUPPORTED_QT_FILE_FILTER

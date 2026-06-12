from __future__ import annotations

import json

from core.knowledge_ingestion import KnowledgeIngestionService


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

    manifest = json.loads(service.manifest_path.read_text(encoding="utf-8"))
    assert manifest["document_count"] == 1
    assert manifest["rag_chunk_count"] == first.chunk_count
    assert manifest["chunk_token_size"] == 48
    assert manifest["chunk_overlap_tokens"] == 8
    assert manifest["dedupe_key"] == "content_hash"
    assert manifest["vector_chunk_count"] == first.chunk_count
    assert manifest["vector_collection_name"] == "csdm_cph_project_knowledge"
    assert manifest["last_ingestion"]["steps"][2]["status"] == "success"

    chunks = [json.loads(line) for line in service.chunks_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(chunks) == first.chunk_count
    assert all(item["token_estimate"] <= 56 for item in chunks)
    assert len({item["content_hash"] for item in chunks}) == len(chunks)

    relations = [json.loads(line) for line in service.relations_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    chunk_ids = {item["chunk_id"] for item in chunks}
    assert all(item["evidence_chunk_id"] in chunk_ids for item in relations)

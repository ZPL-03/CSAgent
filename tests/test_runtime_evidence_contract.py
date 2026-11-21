import hashlib
import json
from pathlib import Path

from core.domain_knowledge import DomainKnowledgeBase
from core.knowledge_ingestion import KnowledgeIngestionService
from core.retrieval_evidence import binds_to_chunk, render_evidence


def rows(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_upload_and_formal_rebuild_preserve_atomic_formula_and_inherited_conditions(tmp_path):
    condition = "当复合材料圆柱耐压壳采用线弹性材料且两端固支时，公式仅用于来源工况。" * 20
    formula = "$$\nP_{runtimeformula} = " + " + ".join(f"a_{{{i}}}" for i in range(160)) + "\n\n+ 0\n$$"
    source = tmp_path / "pressure_hull.md"
    source.write_text("# pressure hull\n\n" + condition + "\n\n## Buckling\n\n" + formula, encoding="utf-8")
    source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    service = KnowledgeIngestionService(base_dir=tmp_path / "runtime", chunk_token_size=48, chunk_overlap_tokens=8)
    result = service.ingest_file(source)
    assert result.success
    chunks = rows(service.chunks_path)
    matched = dict(next(row for row in chunks if formula in row["content_markdown"]))
    assert matched["token_estimate"] > service.chunk_token_size
    assert condition in matched["applicability_context"]
    assert matched["retrieval_eligible"] is True
    assert matched["content_quality_version"] == "3"
    assert matched["evidence_usage"] == "source_conditions_only"
    relations = [row for row in rows(service.relations_path) if row["evidence_chunk_id"] == matched["chunk_id"]]
    assert relations and all(binds_to_chunk(row, matched) for row in relations)
    assert all(row["applicability_context"] == matched["applicability_context"] for row in relations)

    knowledge = DomainKnowledgeBase({"project_knowledge": {"rag_chunks_path": str(service.chunks_path), "kg_dir": str(service.kg_dir)}})
    retrieved = knowledge.retrieve_by_query("runtimeformula")
    packets, _ = render_evidence(retrieved["chunks"], retrieved["relations"], 20000)
    assert formula in json.loads(packets[0])["text"]
    assert condition in json.loads(packets[0])["applicability_context"]

    # 重建依据已保存 Markdown，旧分块缺失的条件和被截断的公式不作为恢复来源。
    for row in chunks:
        row["content_quality_version"] = "2"
        for key in ("retrieval_eligible", "evidence_kind", "evidence_usage", "applicability_context", "table_evidence"):
            row.pop(key)
        row["content_markdown"] = row["content_markdown"][:60]
    service.chunks_path.write_text("\n".join(json.dumps(row) for row in chunks), encoding="utf-8")
    stale_relations = rows(service.relations_path)
    for row in stale_relations:
        row["evidence_chunk_fingerprint"] = "stale"
    service.relations_path.write_text("\n".join(json.dumps(row) for row in stale_relations), encoding="utf-8")
    legacy_reader = DomainKnowledgeBase({"project_knowledge": {"rag_chunks_path": str(service.chunks_path), "kg_dir": str(service.kg_dir)}})
    assert legacy_reader.retrieve_by_query("pressure hull")["relations"] == []
    document = rows(service.documents_path)[0]
    stored_hash = hashlib.sha256(Path(document["stored_path"]).read_bytes()).hexdigest()
    markdown_hash = hashlib.sha256(Path(document["markdown_path"]).read_bytes()).hexdigest()
    service.rebuild_indexes()
    rebuilt = next(row for row in rows(service.chunks_path) if formula in row["content_markdown"])
    assert rebuilt == matched
    refreshed = legacy_reader.retrieve_by_query("runtimeformula")
    assert formula in refreshed["chunks"][0]["content_markdown"]
    assert condition in refreshed["chunks"][0]["applicability_context"]
    assert legacy_reader.kg.search("Buckling", refreshed["chunks"])
    assert rows(service.documents_path)[0]["chunk_count"] == len(rows(service.chunks_path))
    assert hashlib.sha256(source.read_bytes()).hexdigest() == source_hash
    assert hashlib.sha256(Path(document["stored_path"]).read_bytes()).hexdigest() == stored_hash
    assert hashlib.sha256(Path(document["markdown_path"]).read_bytes()).hexdigest() == markdown_hash


def test_uploaded_table_projects_known_columns_and_retains_source(tmp_path):
    source = tmp_path / "material.md"
    original = "# material\n\n| Material | E1 (GPa) | E2 (GPa) | unknown | nu12 |\n| --- | --- | --- | --- | --- |\n| T700 | 135 | 9 | 999 | 0.3 |"
    source.write_text(original, encoding="utf-8")
    service = KnowledgeIngestionService(base_dir=tmp_path / "runtime", chunk_token_size=48)
    result = service.ingest_file(source)
    assert result.success
    chunk = next(row for row in rows(service.chunks_path) if row["table_evidence"])
    table = chunk["table_evidence"][0]
    assert chunk["retrieval_eligible"] is True
    assert table["column_projection"]["source_column_indices"] == [0, 1, 2, 4]
    assert table["column_projection"]["excluded_columns"][0]["index"] == 3
    assert table["structure_issues"] == []
    assert "999" not in chunk["content_markdown"]
    assert source.read_text(encoding="utf-8") == original
    packets, _ = render_evidence([chunk], rows(service.relations_path), 12000)
    assert json.loads(packets[0])["table_evidence"] == [table]

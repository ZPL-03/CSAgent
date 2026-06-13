import json
import gzip
from pathlib import Path

from core.domain_knowledge import DomainKnowledgeBase


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n", encoding="utf-8")


def _task() -> dict:
    return {
        "task": {
            "application": "复合材料外压圆柱耐压壳",
            "load_conditions": {"type": "external_pressure", "external_pressure_MPa": 30.0},
            "boundary_conditions": {"type": "END_CLAMPED"},
            "geometry_envelope": {
                "length_mm": [450, 650],
                "radius_mm": [90, 130],
                "thickness_mm": [8, 14],
                "imperfection_ratio": [0.001, 0.01],
            },
            "material_system": {"name": "T700/Epoxy"},
            "hull_type": "CYLINDRICAL",
            "design_targets": {"ultimate_pressure_min_MPa": 35.0, "primary_objective": "最小壳体质量"},
        }
    }


def test_domain_knowledge_retrieves_knowledge_base_and_graph(tmp_path: Path) -> None:
    rag_path = tmp_path / "rag" / "rag_chunks.jsonl"
    kg_dir = tmp_path / "kg"
    manifest_path = tmp_path / "manifest.json"
    _write_jsonl(
        rag_path,
        [
            {
                "chunk_id": "CHUNK_1",
                "chunk_fingerprint": "fp1",
                "record_id": "SRC_1",
                "source_id": "DOC_1",
                "retrieval_scope": "main",
                "title": "Composite pressure hull external pressure buckling",
                "document_title": "Composite pressure hull external pressure buckling",
                "doi": "10.1000/hull.1",
                "source_url": "https://example.com/hull",
                "year": "2026",
                "venue": "Composite Structures",
                "chunk_type": "fulltext",
                "content_plain": "composite pressure hull external pressure cylindrical shell buckling laminate",
                "content_markdown": "Pressure hull buckling guidance.",
                "task_categories": ["stiffened_panel_shell_structure", "buckling_stability"],
            },
            {
                "chunk_id": "CHUNK_2",
                "chunk_fingerprint": "fp2",
                "record_id": "SRC_1",
                "source_id": "DOC_1",
                "retrieval_scope": "main",
                "title": "Composite pressure hull external pressure buckling",
                "document_title": "Composite pressure hull external pressure buckling",
                "doi": "10.1000/hull.1",
                "source_url": "https://example.com/hull",
                "year": "2026",
                "venue": "Composite Structures",
                "chunk_type": "fulltext",
                "content_plain": "pressure hull collapse pressure external hydrostatic pressure postbuckling",
                "content_markdown": "Second pressure hull guidance from same source.",
                "task_categories": ["stiffened_panel_shell_structure"],
            },
        ],
    )
    _write_jsonl(kg_dir / "entities.jsonl", [{"type": "Structure", "name": "Pressure Hull"}, {"type": "FailureMode", "name": "Buckling"}])
    _write_jsonl(
        kg_dir / "relations.jsonl",
        [
            {
                "source_type": "Structure",
                "source": "Pressure Hull",
                "target_type": "FailureMode",
                "target": "Buckling",
                "relation": "EXPERIENCES",
                "record_id": "SRC_1",
                "evidence_document_title": "Composite pressure hull external pressure buckling",
                "evidence_doi": "10.1000/hull.1",
                "evidence_source_url": "https://example.com/hull",
            },
            {
                "source_type": "Structure",
                "source": "Pressure Hull",
                "target_type": "FailureMode",
                "target": "Buckling",
                "relation": "EXPERIENCES",
                "record_id": "SRC_1",
                "evidence_document_title": "Composite pressure hull external pressure buckling",
                "evidence_doi": "10.1000/hull.1",
                "evidence_source_url": "https://example.com/hull",
            },
        ],
    )
    manifest_path.write_text(
        json.dumps(
            {
                "rag_chunk_count": 2,
                "kg_entity_count": 2,
                "kg_relation_count": 2,
                "structured_block_count": 10,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    knowledge = DomainKnowledgeBase(
        {
            "project_knowledge": {
                "enabled": True,
                "rag_chunks_path": str(rag_path),
                "kg_dir": str(kg_dir),
                "manifest_path": str(manifest_path),
                "top_k": 2,
                "kg_top_k": 2,
                "max_snippet_chars": 200,
            }
        }
    )

    result = knowledge.retrieve(_task(), top_k=2, kg_top_k=2)
    snippets = knowledge.format_snippets(_task(), top_k=2)
    status = knowledge.status()
    snippet_text = "\n".join(snippets)

    assert len(result["chunks"]) == 1
    assert all(chunk["source_url"] == "https://example.com/hull" for chunk in result["chunks"])
    assert result["relations"][0]["relation"] == "EXPERIENCES"
    assert "pressure hull guidance" in snippet_text.lower()
    assert "来源 S1" in snippet_text
    assert snippet_text.count("DOI: 10.1000/hull.1") == 1
    assert snippet_text.count("https://example.com/hull") == 1
    assert snippet_text.count("Pressure Hull(Structure) -[EXPERIENCES]-> Buckling(FailureMode)") == 1
    assert status["rag_chunk_count"] == 2
    assert status["structured_block_count"] == 10


def test_domain_knowledge_merges_builtin_and_runtime_rag_kg(tmp_path: Path) -> None:
    runtime_rag_path = tmp_path / "runtime" / "rag" / "rag_chunks.jsonl"
    runtime_kg_dir = tmp_path / "runtime" / "kg"
    manifest_path = tmp_path / "runtime" / "manifest.json"
    builtin_dir = tmp_path / "csllm"
    builtin_rag_path = builtin_dir / "rag" / "rag_chunks.compact.jsonl.gz"
    builtin_kg_dir = builtin_dir / "kg"
    builtin_manifest_path = builtin_dir / "provenance" / "manifest.json"

    runtime_chunk = {
        "chunk_id": "RUN_CHUNK_1",
        "record_id": "RUN_DOC_1",
        "source_id": "RUN_DOC_1",
        "retrieval_scope": "main",
        "title": "Uploaded pressure hull manufacturing note",
        "document_title": "Uploaded pressure hull manufacturing note",
        "content_plain": "uploaded composite pressure hull filament winding curing external pressure buckling",
        "content_markdown": "Uploaded manufacturing evidence.",
        "task_categories": ["manufacturing_process", "buckling_stability"],
    }
    builtin_chunk = {
        "chunk_id": "BASE_CHUNK_1",
        "record_id": "BASE_DOC_1",
        "source_id": "BASE_DOC_1",
        "retrieval_scope": "main",
        "title": "Built pressure hull buckling reference",
        "document_title": "Built pressure hull buckling reference",
        "content_plain": "built composite pressure hull ASME RD-1172 PBIPF external pressure buckling",
        "content_markdown": "Built RAG evidence.",
        "task_categories": ["buckling_stability"],
    }
    _write_jsonl(runtime_rag_path, [runtime_chunk])
    runtime_kg_dir.mkdir(parents=True, exist_ok=True)
    _write_jsonl(runtime_kg_dir / "entities.jsonl", [{"type": "ManufacturingProcess", "name": "Filament Winding"}])
    _write_jsonl(
        runtime_kg_dir / "relations.jsonl",
        [
            {
                "source_type": "ManufacturingProcess",
                "source": "Filament Winding",
                "target_type": "FailureMode",
                "target": "Buckling",
                "relation": "CONSTRAINS",
                "record_id": "RUN_DOC_1",
                "evidence_document_title": "Uploaded pressure hull manufacturing note",
            }
        ],
    )
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps(
            {
                "document_count": 1,
                "rag_chunk_count": 1,
                "kg_entity_count": 1,
                "kg_relation_count": 1,
                "structured_block_count": 1,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    builtin_rag_path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(builtin_rag_path, "wt", encoding="utf-8") as handle:
        handle.write(json.dumps(builtin_chunk, ensure_ascii=False) + "\n")
    _write_jsonl(builtin_kg_dir / "entities.jsonl", [{"type": "DesignFormula", "name": "ASME RD-1172"}])
    with gzip.open(builtin_kg_dir / "relations.compact.jsonl.gz", "wt", encoding="utf-8") as handle:
        handle.write(
            json.dumps(
                {
                    "source_type": "DesignFormula",
                    "source": "ASME RD-1172",
                    "target_type": "FailureMode",
                    "target": "Buckling",
                    "relation": "PREDICTED_BY",
                    "record_id": "BASE_DOC_1",
                    "evidence_document_title": "Built pressure hull buckling reference",
                },
                ensure_ascii=False,
            )
            + "\n"
        )
    (builtin_kg_dir / "kg_stats.json").write_text(
        json.dumps({"total_entities": 1, "total_relations": 1}, ensure_ascii=False),
        encoding="utf-8",
    )
    builtin_manifest_path.parent.mkdir(parents=True, exist_ok=True)
    builtin_manifest_path.write_text(
        json.dumps({"record_counts": {"rag_chunks": 1, "entities": 1, "relations": 1}}, ensure_ascii=False),
        encoding="utf-8",
    )

    knowledge = DomainKnowledgeBase(
        {
            "project_knowledge": {
                "enabled": True,
                "builtin_dir": str(builtin_dir),
                "builtin_rag_chunks_path": str(builtin_rag_path),
                "builtin_kg_dir": str(builtin_kg_dir),
                "builtin_manifest_path": str(builtin_manifest_path),
                "rag_chunks_path": str(runtime_rag_path),
                "kg_dir": str(runtime_kg_dir),
                "manifest_path": str(manifest_path),
                "top_k": 4,
                "kg_top_k": 4,
                "max_snippet_chars": 200,
            }
        }
    )

    result = knowledge.retrieve_by_query("composite pressure hull external pressure buckling ASME filament winding", top_k=4, kg_top_k=4)
    status = knowledge.status()

    assert status["ready"] is True
    assert status["builtin_ready"] is True
    assert status["runtime_document_count"] == 1
    assert status["runtime_rag_chunk_count"] == 1
    assert status["builtin_rag_chunk_count"] == 1
    assert status["rag_chunk_count"] == 2
    assert status["kg_relation_count"] == 2
    assert {chunk["source"] for chunk in result["chunks"]} == {"BUILTIN_KNOWLEDGE", "PROJECT_KNOWLEDGE"}
    assert {relation["record_id"] for relation in result["relations"]} == {"BASE_DOC_1", "RUN_DOC_1"}

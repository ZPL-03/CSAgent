import json
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
                "source_metadata_count": 1,
                "structured_block_count": 10,
                "table_record_count": 3,
                "figure_record_count": 4,
                "formula_record_count": 5,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    knowledge = DomainKnowledgeBase(
        {
            "external_knowledge": {
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
    assert status["source_metadata_count"] == 1
    assert status["structured_block_count"] == 10
    assert status["table_record_count"] == 3
    assert status["figure_record_count"] == 4
    assert status["formula_record_count"] == 5

import json
from copy import deepcopy
from types import SimpleNamespace

import pytest

from agents.candidate_gen import CandidateGenAgent
from core.domain_knowledge import DomainKnowledgeBase, KnowledgeGraphRetriever
from core.retrieval_evidence import exclusion_reason, render_evidence
from core.rule_checker import RuleChecker


def chunk():
    return {
        "chunk_id": "C1", "chunk_fingerprint": "fp1", "record_id": "R1", "source_id": "S1",
        "content_quality_version": "3", "content_quality_issues": [],
        "document_title": "Pressure hull buckling", "retrieval_eligible": True,
        "evidence_kind": "formula", "evidence_usage": "source_conditions_only",
        "applicability_context": ["简支圆柱壳，线弹性、小变形；几何与材料按来源定义。" * 30],
        "content_markdown": "$$\nP = \\frac{D}{R^3} \\left(" + " + ".join(f"a_{{{i}}}" for i in range(180)) + "\\right)\n$$",
        "content_plain": "pressure hull buckling formula",
    }


def relation(**overrides):
    return {
        "source": "Pressure Hull", "relation": "EXPERIENCES", "target": "Buckling",
        "record_id": "R1", "evidence_chunk_id": "C1", "evidence_chunk_fingerprint": "fp1",
        "evidence_source_id": "S1", "applicability_context": ["仅用于来源条件。"], **overrides,
    }


def test_complete_formula_and_conditions_reach_prompt_or_are_omitted(tmp_path):
    original = chunk()
    path = tmp_path / "rag.jsonl"
    path.write_text(json.dumps(original, ensure_ascii=False) + "\n", encoding="utf-8")
    knowledge = DomainKnowledgeBase({"project_knowledge": {"rag_chunks_path": str(path), "kg_dir": str(tmp_path / "kg")}})
    task = {"task": {"application": "pressure hull buckling", "layup_constraints": {"symmetric": True}}}
    snippets = knowledge.format_snippets(task)
    packet = json.loads(snippets[0])
    assert packet["text"] == original["content_markdown"]
    assert packet["applicability_context"] == original["applicability_context"]
    agent = CandidateGenAgent.__new__(CandidateGenAgent)
    agent.material_catalog = []
    agent.rule_checker = RuleChecker()
    _, prompt = agent._build_prompt(task, 2, snippets)
    assert snippets[0] in prompt

    rendered, audit = render_evidence([original], [relation()], 20000)
    exact_size = audit["used_chars"]
    assert json.loads(rendered[0])["relations"] == [relation()]
    assert render_evidence([original], [relation()], exact_size)[0] == rendered
    omitted, audit = render_evidence([original], [relation()], exact_size - 1)
    assert omitted == [] and audit["used_chars"] == 0
    assert audit["excluded"] == [{"chunk_id": "C1", "chunk_fingerprint": "fp1", "record_id": "R1", "reason": "context_budget"}]


def test_kg_support_requires_current_chunk_fingerprint_and_record(tmp_path):
    graph = KnowledgeGraphRetriever(tmp_path)
    graph._loaded = True
    graph.relations = [relation(), relation(evidence_chunk_id="C2"),
                       relation(evidence_chunk_fingerprint="old"), relation(evidence_chunk_id=None),
                       relation(record_id="R2"), relation(evidence_source_id="S2")]
    found = graph.search("Pressure Hull Buckling", [chunk()])
    assert len(found) == 1
    assert found[0]["evidence_chunk_id"] == "C1"
    assert found[0]["applicability_context"] == relation()["applicability_context"]
    assert graph.search("Pressure Hull", [{**chunk(), "retrieval_eligible": False}]) == []


def test_known_table_projection_preserves_columns_and_rejects_unknown_semantics():
    original = chunk()
    original.update(evidence_kind="table", content_markdown="| No. | E (GPa) |\n| --- | --- |\n| A | 135 |")
    table = {
        "headers": ["No.", "E (GPa)"], "missing_header_columns": [], "missing_unit_columns": [],
        "numeric_columns": [1],
        "structure_issues": [],
        "condition_required": True, "condition_context_present": True,
        "condition_context": ["Material A, 20 C"],
        "column_projection": {"source_column_indices": [0, 2], "excluded_columns": [{"index": 1, "header": "?", "issues": ["table_units_missing"]}]},
    }
    original["table_evidence"] = [table]
    packets, _ = render_evidence([original], [], 20000)
    packet = json.loads(packets[0])
    assert packet["text"] == original["content_markdown"]
    assert packet["table_evidence"] == [table]
    for patch, reason in [({"missing_header_columns": [1]}, "unknown_table_columns"),
                          ({"structure_issues": ["table_header_alignment_ambiguous"]}, "invalid_table_structure"),
                          ({"structure_issues": None}, "missing_table_structure_assessment"),
                          ({"numeric_columns": None}, "missing_table_numeric_assessment"),
                          ({"missing_unit_columns": [1]}, "unknown_table_columns"),
                          ({"condition_context_present": False}, "missing_table_conditions"),
                          ({"column_projection": {"source_column_indices": [0, 1], "excluded_columns": [{"index": 1}]}}, "invalid_table_projection"),
                          ({"column_projection": {"source_column_indices": [[0], 2]}}, "invalid_table_projection")]:
        invalid = deepcopy(original)
        invalid["table_evidence"][0].update(patch)
        assert exclusion_reason(invalid) == reason
        assert render_evidence([invalid], [], 20000)[0] == []

    original["content_quality_version"] = "2"
    assert exclusion_reason(original) == "unsupported_quality_version"
    assert render_evidence([original], [], 20000)[0] == []


def test_qualitative_table_preserves_source_without_numeric_conditions():
    from core.knowledge_quality import assess_content

    text = "| Technique | Application |\n| --- | --- |\n| Vibration | Buckling detection |"
    original = {**chunk(), **assess_content(text), "content_markdown": text}
    table = original["table_evidence"][0]
    assert table["numeric_columns"] == []
    assert table["condition_required"] is True
    assert table["condition_context_present"] is False
    assert exclusion_reason(original) is None
    packets, audit = render_evidence([original], [], 20000)
    assert json.loads(packets[0])["text"] == text
    assert audit["excluded"] == []


@pytest.mark.parametrize("overrides,accepted", [({}, True), ({"chunk_fingerprint": "old"}, False), ({"text": "old content"}, False), ({"chunk_id": "unknown"}, False)])
def test_vector_hits_use_canonical_evidence_and_reject_stale_index(tmp_path, overrides, accepted):
    original = chunk()
    path = tmp_path / "rag.jsonl"
    path.write_text(json.dumps(original, ensure_ascii=False) + "\n", encoding="utf-8")
    knowledge = DomainKnowledgeBase({"project_knowledge": {"rag_chunks_path": str(path)}})
    hit = {"chunk_id": "C1", "record_id": "R1", "chunk_fingerprint": "fp1",
           "text": original["content_plain"], "score": 1.0, "source": "VECTOR_INDEX",
           "retrieval_sources": ["VECTOR_INDEX"], **overrides}
    knowledge.vector = SimpleNamespace(is_ready=True, search=lambda *args, **kwargs: [hit])
    rows = knowledge._retrieve_chunks("pressure hull", 3)
    assert len(rows) == 1
    assert ("VECTOR_INDEX" in rows[0]["retrieval_sources"]) is accepted
    assert rows[0]["text"] == original["content_markdown"]
    assert rows[0]["applicability_context"] == original["applicability_context"]

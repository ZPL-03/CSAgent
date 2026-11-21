"""检索证据的可用性、原文范围和提示词预算契约。"""

from __future__ import annotations

from copy import deepcopy
import json
from typing import Any

from core.knowledge_quality import QUALITY_VERSION


def exclusion_reason(chunk: dict[str, Any]) -> str | None:
    """依据来源元数据排除不可用证据，不推断缺失的条件或列单位。"""
    if not all(chunk.get(key) for key in ("chunk_id", "chunk_fingerprint", "record_id")):
        return "missing_chunk_identity"
    if chunk.get("content_quality_version") != QUALITY_VERSION:
        return "unsupported_quality_version"
    if chunk.get("retrieval_eligible", True) is not True:
        return "retrieval_ineligible"
    if str(chunk.get("retrieval_scope") or "main") not in {"main", "mixed"}:
        return "outside_retrieval_scope"
    if chunk.get("content_quality_issues") or chunk.get("evidence_usage") == "review_required":
        return "review_required"
    tables = chunk.get("table_evidence") or []
    if not isinstance(tables, list) or (chunk.get("evidence_kind") == "table" and not tables):
        return "missing_table_evidence"
    for table in tables:
        if not isinstance(table, dict) or not isinstance(table.get("structure_issues"), list):
            return "missing_table_structure_assessment"
        if table["structure_issues"]:
            return "invalid_table_structure"
        if table.get("missing_header_columns") or table.get("missing_unit_columns"):
            return "unknown_table_columns"
        numeric_columns = table.get("numeric_columns")
        if not isinstance(numeric_columns, list):
            return "missing_table_numeric_assessment"
        # 工况约束用于数值性能结果；术语和方法对照表按原文提供定性信息。
        if numeric_columns and table.get("condition_required") and not table.get("condition_context_present"):
            return "missing_table_conditions"
        projection = table.get("column_projection")
        if projection is not None:
            if not isinstance(projection, dict):
                return "invalid_table_projection"
            selected = projection.get("source_column_indices", [])
            excluded = projection.get("excluded_columns", [])
            headers = table.get("headers")
            if (not isinstance(selected, list) or not selected or not isinstance(headers, list)
                    or len(selected) != len(headers)
                    or any(type(index) is not int or index < 0 for index in selected)
                    or not isinstance(excluded, list)
                    or any(not isinstance(item, dict) or type(item.get("index")) is not int
                           or item["index"] < 0 for item in excluded)):
                return "invalid_table_projection"
            indices = selected + [item["index"] for item in excluded]
            if len(indices) != len(set(indices)):
                return "invalid_table_projection"
    return None


def full_text(chunk: dict[str, Any]) -> str:
    """保留来源中的换行和数学表达式；预览文本不覆盖完整 Markdown。"""
    return str(chunk.get("content_markdown") or chunk.get("content_plain") or chunk.get("text") or "")


def binds_to_chunk(relation: dict[str, Any], chunk: dict[str, Any]) -> bool:
    """图谱关系必须指向当前可检索块及其指纹和来源记录。"""
    return exclusion_reason(chunk) is None and all((
        relation.get("evidence_chunk_id") == chunk["chunk_id"],
        relation.get("evidence_chunk_fingerprint") == chunk["chunk_fingerprint"],
        relation.get("record_id") == chunk["record_id"],
        not relation.get("evidence_source_id") or relation["evidence_source_id"] == chunk.get("source_id"),
    ))


def evidence_packet(chunk: dict[str, Any], relations: list[dict[str, Any]]) -> dict[str, Any]:
    """原文、适用条件、已知列投影和已绑定关系组成不可分割的引用单元。"""
    metadata_keys = (
        "chunk_id", "chunk_fingerprint", "record_id", "source_id", "document_title", "title",
        "section_path", "page_start", "page_end", "doi", "source_url", "year", "venue",
        "retrieval_eligible", "evidence_kind", "evidence_usage", "applicability_context", "table_evidence",
        "content_quality_version", "content_quality_issues",
        "retrieval_scope", "load_case_tag", "design_platform_scope", "formula_validity", "table_structure_status",
    )
    packet = {key: deepcopy(chunk.get(key)) for key in metadata_keys}
    packet["text"] = full_text(chunk)
    packet["relations"] = [
        {key: deepcopy(value) for key, value in relation.items() if key not in {"score", "retrieval_source"}}
        for relation in relations if binds_to_chunk(relation, chunk)
    ]
    return packet


def render_evidence(chunks: list[dict[str, Any]], relations: list[dict[str, Any]], budget: int):
    """按完整序列化单元计费，预算不足时不截断原文、公式或条件。"""
    rendered = []
    audit = {"budget_chars": budget, "used_chars": 0, "included": [], "excluded": []}
    for chunk in chunks:
        identity = {key: chunk.get(key) for key in ("chunk_id", "chunk_fingerprint", "record_id")}
        reason = exclusion_reason(chunk)
        if reason is None and not full_text(chunk).strip():
            reason = "empty_evidence"
        if reason is None:
            packet = evidence_packet(chunk, relations)
            text = json.dumps(packet, ensure_ascii=False, separators=(",", ":"))
            cost = len(text) + (2 if rendered else 0)
            if cost > budget - audit["used_chars"]:
                reason = "context_budget"
            else:
                rendered.append(text)
                audit["used_chars"] += cost
                audit["included"].append({**identity, "chars": len(text), "relations": len(packet["relations"])})
        if reason:
            audit["excluded"].append({**identity, "reason": reason})
    return rendered, audit

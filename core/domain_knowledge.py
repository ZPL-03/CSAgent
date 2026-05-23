"""外部知识库/知识图谱检索。"""

from __future__ import annotations

import json
import math
import re
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Iterable, List

from core.config_loader import load_app_config
from core.paths import ROOT_DIR
from core.task_contract import describe_boundary_conditions, describe_load_conditions, task_payload_from_request


TOKEN_PATTERN = re.compile(r"[a-zA-Z][a-zA-Z0-9_\-./]*|\d+(?:\.\d+)?|[\u4e00-\u9fff]")
DISABLED_RETRIEVAL_TERMS = {"".join(("m", "d", "d", "f"))}

DOMAIN_TERMS = [
    "composite pressure hull",
    "pressure hull",
    "cylindrical shell",
    "externally pressurized shell",
    "external hydrostatic pressure",
    "composite cylindrical shell",
    "composite shell buckling",
    "pressure vessel",
    "submersible hull",
    "laminate",
    "laminated composite",
    "buckling",
    "postbuckling",
    "linear buckling",
    "eigenvalue buckling",
    "collapse pressure",
    "critical pressure",
    "imperfection sensitivity",
    "finite element",
    "abaqus",
    "surrogate model",
    "carbon fiber",
    "cfrp",
    "耐压壳",
    "压力壳",
    "圆柱壳",
    "外压壳",
    "外压圆柱壳",
    "静水压力",
    "极限压力",
    "失效压力",
    "初始缺陷",
    "层合板",
    "铺层",
    "屈曲",
    "后屈曲",
    "线性屈曲",
    "有限元",
    "代理模型",
    "碳纤维",
    "复合材料",
]

QUERY_SYNONYMS = {
    "耐压壳": ["composite pressure hull", "pressure hull", "externally pressurized cylindrical shell"],
    "压力壳": ["pressure hull", "pressure vessel", "cylindrical shell"],
    "圆柱壳": ["cylindrical shell", "composite cylindrical shell"],
    "外压": ["external pressure", "external hydrostatic pressure", "externally pressurized shell"],
    "静水压力": ["hydrostatic pressure", "external hydrostatic pressure"],
    "极限压力": ["collapse pressure", "ultimate pressure", "critical pressure"],
    "失效压力": ["collapse pressure", "failure pressure"],
    "初始缺陷": ["initial imperfection", "imperfection sensitivity"],
    "屈曲": ["buckling", "linear buckling", "shell buckling"],
    "有限元": ["finite element", "fea", "abaqus"],
    "铺层": ["layup", "laminate", "stacking sequence"],
    "碳纤维": ["carbon fiber", "cfrp"],
    "复合材料": ["composite", "composite material"],
    "pressure hull": ["composite pressure hull", "cylindrical shell", "collapse pressure"],
    "buckling": ["linear buckling", "shell buckling", "critical pressure"],
}

CN_TO_ENTITY = {
    "碳纤维": "Carbon Fiber",
    "玻璃纤维": "Glass Fiber",
    "环氧树脂": "Epoxy Resin",
    "复合材料": "Composite Material",
    "CFRP": "CFRP",
    "层合板": "Laminate",
    "铺层": "Layup",
    "屈曲": "Buckling",
    "后屈曲": "Buckling",
    "疲劳": "Fatigue",
    "分层": "Delamination",
    "基体开裂": "Matrix Cracking",
    "纤维断裂": "Fiber Breakage",
    "有限元": "Finite Element Verification",
    "Abaqus": "Abaqus Verification",
    "代理模型": "Surrogate Model",
    "拉伸强度": "Tensile Strength",
    "压缩强度": "Compressive Strength",
    "剪切强度": "Shear Strength",
    "弹性模量": "Elastic Modulus",
    "剪切模量": "Shear Modulus",
    "密度": "Density",
    "耐压壳": "Pressure Hull",
    "压力壳": "Pressure Hull",
    "圆柱壳": "Cylindrical Shell",
    "外压": "External Pressure",
    "静水压力": "Hydrostatic Pressure",
    "极限压力": "Collapse Pressure",
    "初始缺陷": "Initial Imperfection",
}

PREFERRED_CATEGORIES = {
    "stiffened_panel_shell_structure": 3.0,
    "general_composite_structure": 2.0,
    "buckling_stability": 2.0,
    "laminate_layup_optimization": 1.5,
    "strength_stiffness": 1.5,
    "simulation_modeling": 1.2,
    "material_properties": 1.0,
    "failure_damage": 1.0,
    "data_ai_methods": 0.8,
}


def _as_path(value: str | Path) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return ROOT_DIR / path


def _jsonl_rows(path: Path) -> Iterable[dict[str, Any]]:
    if not path.exists():
        return
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(payload, dict):
                yield payload


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except (json.JSONDecodeError, OSError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _count_jsonl(path: Path) -> int:
    if not path.exists():
        return 0
    count = 0
    try:
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    count += 1
    except OSError:
        return 0
    return count


def tokenize(text: Any) -> list[str]:
    """提取英文词、数字和中文单字。"""
    return [token.lower() for token in TOKEN_PATTERN.findall(str(text or ""))]


def expand_query_terms(query: str) -> list[str]:
    """按复合材料耐压壳语境扩展检索词。"""
    query_lower = query.lower()
    terms = set(tokenize(query))
    for term in DOMAIN_TERMS:
        term_lower = term.lower()
        if term_lower in query_lower:
            terms.add(term_lower)
    for key, values in QUERY_SYNONYMS.items():
        if key.lower() in query_lower:
            terms.update(value.lower() for value in values)
    return sorted(terms, key=lambda item: (-len(item), item))


def trim_text(text: Any, limit: int) -> str:
    """按字符数裁剪检索片段。"""
    cleaned = " ".join(str(text or "").split())
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[:limit].rstrip() + "..."


def _format_path(items: Any) -> str:
    if isinstance(items, list):
        values = [str(item).strip() for item in items if str(item).strip()]
        return " > ".join(values)
    return str(items or "")


def _contains_disabled_retrieval_term(text: str) -> bool:
    lowered = text.lower()
    return any(term in lowered for term in DISABLED_RETRIEVAL_TERMS)


class RagChunkRetriever:
    """基于知识库 JSONL 的本地关键词检索器。"""

    def __init__(self, chunks_path: Path, max_snippet_chars: int = 1200) -> None:
        self.chunks_path = chunks_path
        self.max_snippet_chars = max_snippet_chars
        self.rows: list[dict[str, Any]] = []
        self.idf: dict[str, float] = {}
        self._loaded = False

    @property
    def is_ready(self) -> bool:
        return self.chunks_path.exists()

    def _ensure_loaded(self) -> None:
        if self._loaded:
            return
        self._loaded = True
        if not self.chunks_path.exists():
            return

        doc_freq: Counter[str] = Counter()
        for chunk in _jsonl_rows(self.chunks_path):
            if str(chunk.get("retrieval_scope") or "main") not in {"main", "mixed"}:
                continue
            text = str(chunk.get("content_plain") or chunk.get("content_markdown") or chunk.get("text") or "")
            title = str(chunk.get("title") or "")
            record_id = str(chunk.get("record_id") or "")
            combined = " ".join(
                [
                    record_id,
                    title,
                    str(chunk.get("chunk_type") or ""),
                    str(chunk.get("primary_category") or ""),
                    " ".join(str(item) for item in (chunk.get("task_categories") or [])),
                    text,
                ]
            ).lower()
            if _contains_disabled_retrieval_term(combined):
                continue
            token_set = set(tokenize(combined))
            doc_freq.update(token_set)
            self.rows.append(
                {
                    "metadata": {
                        "chunk_id": chunk.get("chunk_id"),
                        "chunk_fingerprint": chunk.get("chunk_fingerprint"),
                        "record_id": chunk.get("record_id"),
                        "title": chunk.get("title") or _format_path(chunk.get("title_path")),
                        "chunk_type": chunk.get("chunk_type"),
                        "source_type": chunk.get("source_type"),
                        "page_start": chunk.get("page_start"),
                        "page_end": chunk.get("page_end"),
                        "section_path": chunk.get("section_path") or [],
                        "title_path": chunk.get("title_path") or [],
                        "source": "KNOWLEDGE_BASE",
                    },
                    "content_preview": trim_text(chunk.get("content_markdown") or chunk.get("text") or text, self.max_snippet_chars),
                    "categories": chunk.get("task_categories") or [],
                    "primary_category": str(chunk.get("primary_category") or ""),
                    "search_text": combined,
                    "title_text": title.lower(),
                    "record_text": record_id.lower(),
                    "token_set": token_set,
                }
            )

        total = max(len(self.rows), 1)
        self.idf = {token: math.log((total + 1) / (count + 1)) + 1.0 for token, count in doc_freq.items()}

    def _category_bonus(self, row: dict[str, Any]) -> float:
        categories = row.get("categories") or []
        if isinstance(categories, str):
            categories = [item for item in categories.split(";") if item]
        bonus = 0.0
        for category in categories:
            bonus += PREFERRED_CATEGORIES.get(str(category), 0.0)
        primary = str(row.get("primary_category") or "")
        bonus += PREFERRED_CATEGORIES.get(primary, 0.0)
        return min(bonus, 5.0)

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        self._ensure_loaded()
        terms = expand_query_terms(query)
        if not terms or not self.rows:
            return []

        results: list[dict[str, Any]] = []
        for row in self.rows:
            search_text = row["search_text"]
            score = 0.0
            for term in terms:
                if len(term) == 1 and "\u4e00" <= term <= "\u9fff":
                    if term in row["token_set"]:
                        score += self.idf.get(term, 1.0) * 0.2
                    continue
                hits = search_text.count(term)
                if not hits:
                    continue
                score += (1.0 + min(hits, 5) * 0.35) * (1.0 + min(len(term), 28) / 10.0)
                if term in row["title_text"]:
                    score *= 1.3
                if term in row["record_text"]:
                    score *= 1.1
            if score <= 0:
                continue

            score += self._category_bonus(row)
            item = dict(row["metadata"])
            item["score"] = round(score, 4)
            item["text"] = row["content_preview"]
            results.append(item)

        results.sort(key=lambda item: float(item.get("score") or 0.0), reverse=True)
        return results[:top_k]


class KnowledgeGraphRetriever:
    """基于知识图谱 JSONL 的文件型关系检索器。"""

    def __init__(self, kg_dir: Path) -> None:
        self.kg_dir = kg_dir
        self.entities: list[dict[str, Any]] = []
        self.relations: list[dict[str, Any]] = []
        self.entity_names: list[str] = []
        self._loaded = False

    @property
    def is_ready(self) -> bool:
        return (self.kg_dir / "entities.jsonl").exists() and (self.kg_dir / "relations.jsonl").exists()

    def _ensure_loaded(self) -> None:
        if self._loaded:
            return
        self._loaded = True
        self.entities = list(_jsonl_rows(self.kg_dir / "entities.jsonl"))
        self.relations = list(_jsonl_rows(self.kg_dir / "relations.jsonl"))
        self.entity_names = [str(item.get("name") or "") for item in self.entities if str(item.get("name") or "")]

    def _matched_entities(self, query: str) -> set[str]:
        query_lower = query.lower()
        expanded_terms = expand_query_terms(query)
        mapped_names = {
            target
            for keyword, target in CN_TO_ENTITY.items()
            if keyword.lower() in query_lower or keyword in query
        }
        matches: set[str] = set()
        for name in self.entity_names:
            lowered = name.lower()
            if lowered in query_lower:
                matches.add(name)
                continue
            if name in mapped_names:
                matches.add(name)
                continue
            if any(term and (term in lowered or lowered in term) for term in expanded_terms):
                matches.add(name)
        return matches

    def search(self, query: str, record_ids: Iterable[str], top_k: int = 8) -> list[dict[str, Any]]:
        self._ensure_loaded()
        if not self.relations:
            return []

        matched_entities = self._matched_entities(query)
        record_set = {str(record_id) for record_id in record_ids if str(record_id).strip()}
        results: list[dict[str, Any]] = []
        seen: set[tuple[str, str, str, str]] = set()

        for relation in self.relations:
            source = str(relation.get("source") or "")
            target = str(relation.get("target") or "")
            record_id = str(relation.get("record_id") or "")
            relation_type = str(relation.get("relation") or "")
            score = 0.0
            if source in matched_entities:
                score += 2.0
            if target in matched_entities:
                score += 2.0
            if record_id in record_set:
                score += 1.0
            if score <= 0:
                continue

            key = (source, relation_type, target, record_id)
            if key in seen:
                continue
            seen.add(key)
            item = dict(relation)
            item["score"] = round(score, 4)
            item["retrieval_source"] = "KNOWLEDGE_GRAPH"
            results.append(item)

        results.sort(key=lambda item: (-float(item.get("score") or 0.0), str(item.get("record_id") or "")))
        return results[:top_k]


class DomainKnowledgeBase:
    """面向 CSDM_cph 的外部知识库/知识图谱运行时入口。"""

    def __init__(self, config: Dict[str, Any] | None = None) -> None:
        app_config = config or load_app_config()
        knowledge_config = dict(app_config.get("external_knowledge", {}))
        self.enabled = bool(knowledge_config.get("enabled", True))
        self.top_k = int(knowledge_config.get("top_k", 5) or 5)
        self.kg_top_k = int(knowledge_config.get("kg_top_k", 8) or 8)
        self.manifest_path = _as_path(str(knowledge_config.get("manifest_path", "knowledge/external/manifest.json")))
        rag_path = _as_path(str(knowledge_config.get("rag_chunks_path", "knowledge/external/rag/rag_chunks.jsonl")))
        kg_dir = _as_path(str(knowledge_config.get("kg_dir", "knowledge/external/kg")))
        max_snippet_chars = int(knowledge_config.get("max_snippet_chars", 1200) or 1200)
        self.rag = RagChunkRetriever(rag_path, max_snippet_chars=max_snippet_chars)
        self.kg = KnowledgeGraphRetriever(kg_dir)

    @property
    def is_ready(self) -> bool:
        return self.enabled and self.rag.is_ready

    def task_query_text(self, task: Dict[str, Any]) -> str:
        task_payload = task_payload_from_request(task)
        target = task_payload.get("design_targets", {})
        material = task_payload.get("material_system", {})
        envelope = task_payload.get("geometry_envelope", {})
        return "\n".join(
            [
                "复合材料外压圆柱耐压壳 composite pressure hull external pressure shell buckling",
                f"应用：{task_payload.get('application', '复合材料外压圆柱耐压壳')}",
                f"工况：{describe_load_conditions(task_payload.get('load_conditions', {}))}",
                f"边界：{describe_boundary_conditions(task_payload.get('boundary_conditions', {}))}",
                f"壳体：{task_payload.get('hull_type', 'CYLINDRICAL')}",
                f"材料：{material.get('name', '')}",
                f"几何：L={envelope.get('length_mm')}, R={envelope.get('radius_mm')}, t={envelope.get('thickness_mm')}, Ir={envelope.get('imperfection_ratio')}",
                f"目标：P_ult >= {target.get('ultimate_pressure_min_MPa', 30.0)} MPa，{target.get('primary_objective', '最小壳体质量')}",
            ]
        )

    def retrieve(self, task: Dict[str, Any], top_k: int | None = None, kg_top_k: int | None = None) -> dict[str, Any]:
        if not self.is_ready:
            return {"query": "", "chunks": [], "relations": []}
        query = self.task_query_text(task)
        chunks = self.rag.search(query, top_k=top_k or self.top_k)
        record_ids = [str(item.get("record_id") or "") for item in chunks]
        relations = self.kg.search(query, record_ids, top_k=kg_top_k or self.kg_top_k) if self.kg.is_ready else []
        return {"query": query, "chunks": chunks, "relations": relations}

    def format_snippets(self, task: Dict[str, Any], top_k: int | None = None) -> list[str]:
        payload = self.retrieve(task, top_k=top_k or self.top_k)
        formatted: list[str] = []
        for index, item in enumerate(payload.get("chunks", []), start=1):
            title = item.get("title") or item.get("record_id") or f"资料片段{index}"
            formatted.append(
                f"[外部知识库 {index}] {title}\n{item.get('text') or ''}"
            )

        relations = payload.get("relations", [])
        if relations:
            relation_lines = []
            for index, relation in enumerate(relations, start=1):
                relation_lines.append(
                    "图谱 {idx}: {source}({source_type}) -[{rel}]-> {target}({target_type})".format(
                        idx=index,
                        source=relation.get("source"),
                        source_type=relation.get("source_type"),
                        rel=relation.get("relation"),
                        target=relation.get("target"),
                        target_type=relation.get("target_type"),
                    )
                )
            formatted.append("知识图谱关系：\n" + "\n".join(relation_lines))
        return formatted

    def status(self) -> dict[str, Any]:
        manifest = _load_json(self.manifest_path)
        kg_stats = _load_json(self.kg.kg_dir / "kg_stats.json")
        rag_chunk_count = int(manifest.get("rag_chunk_count", 0) or 0)
        if rag_chunk_count <= 0:
            rag_chunk_count = _count_jsonl(self.rag.chunks_path)
        kg_entity_count = int(
            manifest.get("kg_entity_count", 0)
            or kg_stats.get("total_entities", 0)
            or 0
        )
        if kg_entity_count <= 0:
            kg_entity_count = _count_jsonl(self.kg.kg_dir / "entities.jsonl")
        kg_relation_count = int(
            manifest.get("kg_relation_count", 0)
            or kg_stats.get("total_relations", 0)
            or 0
        )
        if kg_relation_count <= 0:
            kg_relation_count = _count_jsonl(self.kg.kg_dir / "relations.jsonl")
        return {
            "enabled": self.enabled,
            "ready": self.is_ready,
            "manifest_path": str(self.manifest_path),
            "rag_chunks_path": str(self.rag.chunks_path),
            "kg_dir": str(self.kg.kg_dir),
            "rag_chunk_count": rag_chunk_count,
            "kg_entity_count": kg_entity_count,
            "kg_relation_count": kg_relation_count,
            "provenance_dir": manifest.get("provenance_dir"),
            "source_registry_path": manifest.get("source_registry_path"),
            "structured_documents_path": manifest.get("structured_documents_path"),
            "markdown_documents_dir": manifest.get("markdown_documents_dir"),
            "source_registry_count": int(manifest.get("source_registry_count", 0) or 0),
            "structured_document_count": int(manifest.get("structured_document_count", 0) or 0),
            "markdown_document_count": int(manifest.get("markdown_document_count", 0) or 0),
            "updated_at": manifest.get("updated_at"),
        }

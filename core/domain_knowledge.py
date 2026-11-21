"""项目知识库/知识图谱检索。"""

from __future__ import annotations

import gzip
import json
import math
import re
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Iterable

from core.config_loader import load_app_config
from core.paths import CHROMA_DIR, ROOT_DIR
from core.retrieval_evidence import binds_to_chunk, exclusion_reason, full_text, render_evidence
from core.task_contract import describe_boundary_conditions, describe_load_conditions, task_payload_from_request


TOKEN_PATTERN = re.compile(r"[a-zA-Z][a-zA-Z0-9_\-./]*|\d+(?:\.\d+)?|[\u4e00-\u9fff]")

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
    opener = gzip.open if path.suffix.lower() == ".gz" else open
    with opener(path, "rt", encoding="utf-8") as handle:
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


def _count_rows(path: Path) -> int:
    return sum(1 for _row in _jsonl_rows(path))


def _file_signature(paths: Iterable[Path]) -> tuple:
    """上传或重建改变文件时，检索对象必须重新装载当前证据。"""
    return tuple((str(path), stat.st_mtime_ns, stat.st_size) for path in paths
                 if path.exists() for stat in [path.stat()])


def _builtin_record_counts(manifest_path: Path, kg_stats_path: Path, rag_path: Path, relations_path: Path, entities_path: Path) -> dict[str, int]:
    manifest = _load_json(manifest_path)
    record_counts = manifest.get("record_counts") if isinstance(manifest.get("record_counts"), dict) else {}
    kg_stats = _load_json(kg_stats_path)
    return {
        "rag_chunks": int(record_counts.get("rag_chunks") or (_count_rows(rag_path) if rag_path.exists() else 0)),
        "relations": int(record_counts.get("relations") or kg_stats.get("total_relations") or (_count_rows(relations_path) if relations_path.exists() else 0)),
        "entities": int(record_counts.get("entities") or kg_stats.get("total_entities") or (_count_rows(entities_path) if entities_path.exists() else 0)),
    }


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
    """生成日志和界面预览，不能用于模型提示词证据。"""
    cleaned = " ".join(str(text or "").split())
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[:limit].rstrip() + "..."


def _format_path(items: Any) -> str:
    if isinstance(items, list):
        values = [str(item).strip() for item in items if str(item).strip()]
        return " > ".join(values)
    return str(items or "")


def _list_values(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        return [item.strip() for item in value.split(";") if item.strip()]
    return []


def _normalize_source_key(*values: Any) -> str:
    for value in values:
        text = re.sub(r"\s+", " ", str(value or "")).strip().lower()
        if text:
            return text
    return ""


class RagChunkRetriever:
    """基于知识库 JSONL 的轻量关键词检索器。"""

    def __init__(
        self,
        chunks_path: Path,
        *,
        builtin_chunks_paths: list[Path] | None = None,
    ) -> None:
        self.chunks_path = chunks_path
        self.builtin_chunks_paths = list(builtin_chunks_paths or [])
        self.chunks_by_id: dict[str, dict[str, Any]] = {}
        self.rows: list[dict[str, Any]] = []
        self.idf: dict[str, float] = {}
        self._loaded = False
        self._source_signature: tuple = ()

    @property
    def is_ready(self) -> bool:
        return any(path.exists() for path in self._chunk_paths())

    def _chunk_paths(self) -> list[Path]:
        paths: list[Path] = []
        seen: set[str] = set()
        for path in [*self.builtin_chunks_paths, self.chunks_path]:
            key = str(path.resolve()) if path.exists() else str(path)
            if key in seen:
                continue
            seen.add(key)
            paths.append(path)
        return paths

    def _ensure_loaded(self) -> None:
        signature = _file_signature(self._chunk_paths())
        if self._loaded and signature == self._source_signature:
            return
        self.chunks_by_id.clear()
        self.rows.clear()
        self.idf.clear()
        self._source_signature = signature
        self._loaded = True

        doc_freq: Counter[str] = Counter()
        for path in self._chunk_paths():
            if not path.exists():
                continue
            source_label = "PROJECT_KNOWLEDGE" if path == self.chunks_path else "BUILTIN_KNOWLEDGE"
            for chunk in _jsonl_rows(path):
                if exclusion_reason(chunk) is not None:
                    continue
                self.chunks_by_id[chunk["chunk_id"]] = chunk
                text = str(
                    chunk.get("content_search")
                    or chunk.get("content_plain")
                    or chunk.get("content_markdown")
                    or chunk.get("text")
                    or ""
                )
                title = str(chunk.get("title") or chunk.get("document_title") or _format_path(chunk.get("title_path")) or "")
                document_title = str(chunk.get("document_title") or title)
                section_title = str(chunk.get("section_title") or _format_path(chunk.get("section_path")) or "")
                record_id = str(chunk.get("record_id") or "")
                source_id = str(chunk.get("source_id") or "")
                task_categories = _list_values(chunk.get("task_categories"))
                physics_quantities = _list_values(chunk.get("physics_quantities_mentioned"))
                combined = " ".join(
                    [
                        record_id,
                        source_id,
                        title,
                        document_title,
                        section_title,
                        str(chunk.get("doi") or ""),
                        str(chunk.get("year") or ""),
                        str(chunk.get("venue") or ""),
                        str(chunk.get("source_url") or ""),
                        str(chunk.get("chunk_type") or ""),
                        str(chunk.get("source_type") or ""),
                        str(chunk.get("primary_category") or ""),
                        " ".join(task_categories),
                        str(chunk.get("load_case_tag") or ""),
                        str(chunk.get("design_platform_scope") or ""),
                        " ".join(physics_quantities),
                        text,
                    ]
                ).lower()
                token_set = set(tokenize(combined))
                doc_freq.update(token_set)
                self.rows.append(
                    {
                        "metadata": {
                            **chunk,
                            "chunk_id": chunk.get("chunk_id"),
                            "chunk_fingerprint": chunk.get("chunk_fingerprint"),
                            "record_id": chunk.get("record_id"),
                            "source_id": chunk.get("source_id"),
                            "title": title,
                            "document_title": document_title,
                            "section_title": section_title,
                            "doi": chunk.get("doi"),
                            "source_url": chunk.get("source_url"),
                            "year": chunk.get("year"),
                            "venue": chunk.get("venue"),
                            "chunk_type": chunk.get("chunk_type"),
                            "source_type": chunk.get("source_type"),
                            "page_start": chunk.get("page_start"),
                            "page_end": chunk.get("page_end"),
                            "section_path": chunk.get("section_path") or [],
                            "title_path": chunk.get("title_path") or [],
                            "primary_category": chunk.get("primary_category"),
                            "task_categories": task_categories,
                            "load_case_tag": chunk.get("load_case_tag"),
                            "design_platform_scope": chunk.get("design_platform_scope"),
                            "physics_quantities_mentioned": physics_quantities,
                            "source": source_label,
                            "retrieval_sources": [source_label],
                        },
                        "content": full_text(chunk),
                        "categories": task_categories,
                        "primary_category": str(chunk.get("primary_category") or ""),
                        "search_text": combined,
                        "title_text": " ".join([title, document_title, section_title]).lower(),
                        "record_text": record_id.lower(),
                        "token_set": token_set,
                    }
                )

        total = max(len(self.rows), 1)
        self.idf = {token: math.log((total + 1) / (count + 1)) + 1.0 for token, count in doc_freq.items()}

    def _category_bonus(self, row: dict[str, Any]) -> float:
        categories = _list_values(row.get("categories"))
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
            item["text"] = row["content"]
            results.append(item)

        results.sort(key=lambda item: float(item.get("score") or 0.0), reverse=True)
        unique_results: list[dict[str, Any]] = []
        seen_sources: set[str] = set()
        for item in results:
            source_key = _normalize_source_key(
                item.get("source_url"),
                item.get("doi"),
                item.get("document_title") or item.get("title"),
                item.get("source_id"),
                item.get("record_id"),
            )
            if source_key and source_key in seen_sources:
                continue
            if source_key:
                seen_sources.add(source_key)
            unique_results.append(item)
            if len(unique_results) >= top_k:
                break
        return unique_results


class VectorChunkRetriever:
    """基于项目知识向量 collection 的检索器。"""

    def __init__(
        self,
        chroma_dir: Path,
        collection_name: str,
        *,
        enabled: bool = True,
    ) -> None:
        self.enabled = enabled
        if enabled:
            from core.rag_engine import RAGEngine

        self.engine = RAGEngine(chroma_dir=chroma_dir, collection_name=collection_name) if enabled else None

    @property
    def is_ready(self) -> bool:
        if not self.enabled or self.engine is None:
            return False
        return self.engine.count() > 0

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        if not self.is_ready or not str(query or "").strip():
            return []
        rows = self.engine.query_text(query, top_k=top_k, where={"source": "PROJECT_KNOWLEDGE"}) if self.engine else []
        results: list[dict[str, Any]] = []
        for row in rows:
            metadata = dict(row.get("metadata") or {})
            document = str(row.get("document") or "")
            distance = row.get("distance")
            try:
                score = 1.0 / (1.0 + float(distance or 0.0))
            except (TypeError, ValueError):
                score = 0.0
            item = {
                **metadata,
                "chunk_id": metadata.get("chunk_id") or row.get("id"),
                "record_id": metadata.get("record_id"),
                "source_id": metadata.get("source_id"),
                "title": metadata.get("title") or metadata.get("document_title"),
                "document_title": metadata.get("document_title") or metadata.get("title"),
                "section_title": metadata.get("section_title"),
                "doi": metadata.get("doi"),
                "source_url": metadata.get("source_url"),
                "chunk_type": "vector",
                "source_type": metadata.get("source_type"),
                "page_start": metadata.get("page_start"),
                "page_end": metadata.get("page_end"),
                "load_case_tag": metadata.get("load_case_tag"),
                "design_platform_scope": metadata.get("design_platform_scope"),
                "score": round(score, 4),
                "vector_distance": distance,
                "text": document,
                "source": "VECTOR_INDEX",
                "retrieval_sources": ["VECTOR_INDEX"],
            }
            results.append(item)
        return results


class KnowledgeGraphRetriever:
    """基于知识图谱 JSONL 的文件型关系检索器。"""

    def __init__(self, kg_dir: Path, *, builtin_kg_dirs: list[Path] | None = None) -> None:
        self.kg_dir = kg_dir
        self.builtin_kg_dirs = list(builtin_kg_dirs or [])
        self.entities: list[dict[str, Any]] = []
        self.relations: list[dict[str, Any]] = []
        self.entity_names: list[str] = []
        self._loaded = False
        self._source_signature: tuple = ()

    @property
    def is_ready(self) -> bool:
        return any((kg_dir / "entities.jsonl").exists() and self._relation_paths(kg_dir) for kg_dir in self._kg_dirs())

    def _kg_dirs(self) -> list[Path]:
        dirs: list[Path] = []
        seen: set[str] = set()
        for kg_dir in [*self.builtin_kg_dirs, self.kg_dir]:
            key = str(kg_dir.resolve()) if kg_dir.exists() else str(kg_dir)
            if key in seen:
                continue
            seen.add(key)
            dirs.append(kg_dir)
        return dirs

    def _relation_paths(self, kg_dir: Path) -> list[Path]:
        return [path for path in [kg_dir / "relations.jsonl", kg_dir / "relations.compact.jsonl.gz"] if path.exists()]

    def _ensure_loaded(self) -> None:
        signature = _file_signature(path for directory in self._kg_dirs()
                                    for path in [directory / "entities.jsonl", *self._relation_paths(directory)])
        if self._loaded and signature == self._source_signature:
            return
        self.entities.clear()
        self.relations.clear()
        self.entity_names.clear()
        self._source_signature = signature
        self._loaded = True
        for kg_dir in self._kg_dirs():
            self.entities.extend(_jsonl_rows(kg_dir / "entities.jsonl"))
            for relation_path in self._relation_paths(kg_dir):
                self.relations.extend(_jsonl_rows(relation_path))
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

    def search(self, query: str, chunks: Iterable[dict[str, Any]], top_k: int = 8) -> list[dict[str, Any]]:
        self._ensure_loaded()
        if not self.relations:
            return []

        matched_entities = self._matched_entities(query)
        evidence = {chunk["chunk_id"]: chunk for chunk in chunks if exclusion_reason(chunk) is None}
        expanded_terms = [term for term in expand_query_terms(query) if len(term) >= 2]
        results: list[dict[str, Any]] = []
        seen: set[tuple[str, ...]] = set()

        for relation in self.relations:
            chunk = evidence.get(relation.get("evidence_chunk_id"))
            if chunk is None or not binds_to_chunk(relation, chunk):
                continue
            source = str(relation.get("source") or "")
            target = str(relation.get("target") or "")
            record_id = str(relation.get("record_id") or "")
            relation_type = str(relation.get("relation") or "")
            score = 0.0
            if source in matched_entities:
                score += 2.0
            if target in matched_entities:
                score += 2.0
            relation_text = " ".join(
                [
                    source,
                    target,
                    relation_type,
                    str(relation.get("source_type") or ""),
                    str(relation.get("target_type") or ""),
                    str(relation.get("evidence_document_title") or ""),
                ]
            ).lower()
            for term in expanded_terms:
                if term in relation_text:
                    score += 1.0
            if score <= 0:
                continue

            key = (source, relation_type, target, record_id, chunk["chunk_id"], chunk["chunk_fingerprint"])
            if key in seen:
                continue
            seen.add(key)
            item = dict(relation)
            item["score"] = round(score, 4)
            item["retrieval_source"] = "KNOWLEDGE_GRAPH"
            results.append(item)

        results.sort(key=lambda item: (-float(item.get("score") or 0.0), str(item.get("record_id") or "")))
        return results[:top_k]


def merge_knowledge_status(retrieval: dict[str, Any], ingestion: dict[str, Any]) -> dict[str, Any]:
    """合并检索可用性与增量入库状态，入库流水线保持独立事实。"""
    merged = {**retrieval, **ingestion}
    builtin_ready = bool(retrieval.get("builtin_vector_ready"))
    runtime_ready = bool(ingestion.get("vector_ready"))
    builtin_count = int(retrieval.get("builtin_vector_chunk_count") or 0)
    runtime_count = int(ingestion.get("vector_chunk_count") or 0)
    statuses = {str(retrieval.get("builtin_vector_status") or "pending"), str(ingestion.get("vector_status") or "pending")}
    ready = builtin_ready or runtime_ready
    backend = str(ingestion.get("vector_backend") or "unavailable")
    if builtin_ready:
        backend = "builtin_bge_m3" + (f" + {backend}" if runtime_ready else "")
    merged.update(
        vector_ready=ready,
        vector_chunk_count=builtin_count + runtime_count,
        runtime_vector_chunk_count=runtime_count,
        runtime_vector_status=ingestion.get("vector_status", "pending"),
        runtime_vector_backend=ingestion.get("vector_backend", "unavailable"),
        vector_status="warning" if statuses & {"warning", "failed"} else "success" if ready else "pending",
        vector_message=f"内置向量 {builtin_count:,} / 用户增量 {runtime_count:,}",
        vector_backend=backend,
        vector_detail=f"内置：{retrieval.get('builtin_vector_status', 'pending')}；用户增量：{ingestion.get('vector_status', 'pending')}。{ingestion.get('vector_detail') or ''}",
    )
    return merged


class DomainKnowledgeBase:
    """面向 CSAgent 的项目知识库/知识图谱运行时入口。"""

    def __init__(self, config: Dict[str, Any] | None = None) -> None:
        using_default_config = config is None
        app_config = load_app_config() if using_default_config else config
        knowledge_config = dict(app_config.get("project_knowledge", {}))
        self.enabled = bool(knowledge_config.get("enabled", True))
        self.top_k = int(knowledge_config.get("top_k", 5) or 5)
        self.kg_top_k = int(knowledge_config.get("kg_top_k", 8) or 8)
        self.base_dir = _as_path(str(knowledge_config.get("base_dir", "knowledge/runtime")))
        self.upload_dir = _as_path(str(knowledge_config.get("upload_dir", "knowledge/runtime/uploads")))
        self.structured_dir = _as_path(str(knowledge_config.get("structured_dir", "knowledge/runtime/structured_text")))
        self.manifest_path = _as_path(str(knowledge_config.get("manifest_path", "knowledge/runtime/manifest.json")))
        rag_path = _as_path(str(knowledge_config.get("rag_chunks_path", "knowledge/runtime/rag/rag_chunks.jsonl")))
        kg_dir = _as_path(str(knowledge_config.get("kg_dir", "knowledge/runtime/kg")))
        builtin_config_keys = {"builtin_dir", "builtin_rag_chunks_path", "builtin_kg_dir", "builtin_manifest_path"}
        builtin_enabled = using_default_config or any(key in knowledge_config for key in builtin_config_keys)
        if builtin_enabled:
            builtin_dir = _as_path(str(knowledge_config.get("builtin_dir", "knowledge/csllm")))
            builtin_rag_path = _as_path(str(knowledge_config.get("builtin_rag_chunks_path", builtin_dir / "rag" / "rag_chunks.compact.jsonl.gz")))
            builtin_kg_dir = _as_path(str(knowledge_config.get("builtin_kg_dir", builtin_dir / "kg")))
            builtin_manifest_path = _as_path(str(knowledge_config.get("builtin_manifest_path", builtin_dir / "provenance" / "manifest.json")))
        else:
            builtin_dir = ROOT_DIR / "knowledge" / "__disabled_builtin__"
            builtin_rag_path = builtin_dir / "rag" / "rag_chunks.compact.jsonl.gz"
            builtin_kg_dir = builtin_dir / "kg"
            builtin_manifest_path = builtin_dir / "provenance" / "manifest.json"
        self.builtin_dir = builtin_dir
        self.builtin_manifest_path = builtin_manifest_path
        self.builtin_rag_chunks_path = builtin_rag_path
        self.builtin_kg_dir = builtin_kg_dir
        self.max_context_chars = max(0, int(knowledge_config.get("max_context_chars", 12000)))
        self.last_evidence_audit: dict[str, Any] = {}
        vector_chroma_dir = _as_path(str(knowledge_config.get("vector_chroma_dir", CHROMA_DIR)))
        vector_collection_name = str(knowledge_config.get("vector_collection_name", "csdm_cph_project_knowledge"))
        vector_enabled = bool(knowledge_config.get("vector_enabled", False))
        vector_top_k_multiplier = int(knowledge_config.get("vector_top_k_multiplier", 2) or 2)
        builtin_rag_paths = [builtin_rag_path] if builtin_rag_path.exists() else []
        builtin_kg_dirs = [builtin_kg_dir] if builtin_kg_dir.exists() else []
        self.rag = RagChunkRetriever(rag_path, builtin_chunks_paths=builtin_rag_paths)
        self.vector = VectorChunkRetriever(
            vector_chroma_dir,
            vector_collection_name,
            enabled=vector_enabled,
        )
        self.vector_top_k_multiplier = max(1, vector_top_k_multiplier)
        from core.builtin_knowledge import BuiltinKnowledgeIndex

        index_value = knowledge_config.get("builtin_retrieval_index_path")
        index_path = _as_path(index_value) if index_value else builtin_dir / "rag" / "retrieval_index.sqlite"
        self.builtin_index = (
            BuiltinKnowledgeIndex(index_path, engine=self.vector.engine,
                                  dense_enabled=bool(knowledge_config.get("builtin_dense_enabled", vector_enabled)))
            if builtin_enabled and (index_value or index_path.exists()) else None
        )
        if self.builtin_index is not None:
            self.rag.builtin_chunks_paths = []
        self.kg = KnowledgeGraphRetriever(kg_dir, builtin_kg_dirs=builtin_kg_dirs)

    @property
    def is_ready(self) -> bool:
        return self.enabled and (self.builtin_index is not None or self.rag.is_ready or self.vector.is_ready)

    def _retrieve_chunks(self, query: str, top_k: int) -> list[dict[str, Any]]:
        keyword_chunks = self.rag.search(query, top_k=top_k) if self.rag.is_ready else []
        vector_hits = (
            self.vector.search(query, top_k=top_k * self.vector_top_k_multiplier)
            if self.vector.is_ready
            else []
        )
        # 向量命中只提供排序线索；完整证据从当前 JSONL 回填，过期向量不进入提示词。
        vector_chunks = []
        if vector_hits:
            self.rag._ensure_loaded()
        for hit in vector_hits:
            chunk = self.rag.chunks_by_id.get(hit.get("chunk_id"))
            if chunk is None or hit.get("record_id") != chunk.get("record_id"):
                continue
            document = str(chunk.get("content_plain") or chunk.get("content_markdown") or chunk.get("text") or "").strip()
            if hit.get("text", "").strip() != document or (
                hit.get("chunk_fingerprint") and hit["chunk_fingerprint"] != chunk["chunk_fingerprint"]
            ):
                continue
            vector_chunks.append({**chunk, "text": full_text(chunk), "score": hit["score"],
                                  "retrieval_sources": hit["retrieval_sources"], "source": hit["source"]})
        builtin_chunks = self.builtin_index.search(query, top_k) if self.builtin_index is not None else []
        ranked_chunks = []
        for group in (builtin_chunks, keyword_chunks, vector_chunks):
            ranked_chunks.extend({**chunk, "score": 61.0 / (60 + rank)} for rank, chunk in enumerate(group, 1))
        merged: dict[str, dict[str, Any]] = {}
        for chunk in ranked_chunks:
            if exclusion_reason(chunk) is not None:
                continue
            source_key = _normalize_source_key(
                chunk.get("source_url"),
                chunk.get("doi"),
                chunk.get("document_title") or chunk.get("title"),
                chunk.get("source_id"),
                chunk.get("record_id"),
                chunk.get("chunk_id"),
            )
            if not source_key:
                continue
            current = merged.get(source_key)
            incoming_score = float(chunk.get("score") or 0.0)
            if current is None:
                item = dict(chunk)
                sources = item.get("retrieval_sources")
                if not isinstance(sources, list):
                    base_source = str(item.get("source") or "KNOWLEDGE_BASE")
                    sources = [base_source]
                item["retrieval_sources"] = sorted({str(source) for source in sources if str(source)})
                merged[source_key] = item
                continue
            current_score = float(current.get("score") or 0.0)
            current["score"] = round(max(current_score, incoming_score) + min(current_score, incoming_score) * 0.15, 4)
            sources = set(str(source) for source in current.get("retrieval_sources", []) if str(source))
            incoming_sources = chunk.get("retrieval_sources")
            if isinstance(incoming_sources, list):
                sources.update(str(source) for source in incoming_sources if str(source))
            else:
                sources.add(str(chunk.get("source") or "KNOWLEDGE_BASE"))
            current["retrieval_sources"] = sorted(sources)
            if not current.get("text") and chunk.get("text"):
                current["text"] = chunk.get("text")
        result = sorted(merged.values(), key=lambda item: float(item.get("score") or 0.0), reverse=True)[:top_k]
        return result

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
                f"目标：P_ult >= {task_payload['load_conditions']['external_pressure_MPa']} MPa，{target.get('primary_objective', '最小壳体质量')}",
            ]
        )

    def retrieve(self, task: Dict[str, Any], top_k: int | None = None, kg_top_k: int | None = None) -> dict[str, Any]:
        if not self.is_ready:
            return {"query": "", "chunks": [], "relations": []}
        query = self.task_query_text(task)
        chunks = self._retrieve_chunks(query, top_k or self.top_k)
        relations = self.kg.search(query, chunks, top_k=kg_top_k or self.kg_top_k) if self.kg.is_ready else []
        return {"query": query, "chunks": chunks, "relations": relations}

    def retrieve_by_query(self, query: str, top_k: int | None = None, kg_top_k: int | None = None) -> dict[str, Any]:
        """按人工输入的工程查询检索 RAG 文本块和知识图谱关系。"""
        query_text = str(query or "").strip()
        if not self.is_ready or not query_text:
            return {"query": query_text, "chunks": [], "relations": []}
        chunks = self._retrieve_chunks(query_text, top_k or self.top_k)
        relations = self.kg.search(query_text, chunks, top_k=kg_top_k or self.kg_top_k) if self.kg.is_ready else []
        return {"query": query_text, "chunks": chunks, "relations": relations}

    def format_snippets(self, task: Dict[str, Any], top_k: int | None = None) -> list[str]:
        payload = self.retrieve(task, top_k=top_k or self.top_k)
        formatted, self.last_evidence_audit = render_evidence(
            payload["chunks"], payload["relations"], self.max_context_chars,
        )
        manifest = _load_json(self.builtin_manifest_path)
        self.last_evidence_audit["builtin_source_package_sha256"] = manifest.get("source_package_sha256")
        self.last_evidence_audit["builtin_generated_at"] = manifest.get("generated_at")
        return formatted

    def status(self) -> dict[str, Any]:
        manifest = _load_json(self.manifest_path)
        kg_stats = _load_json(self.kg.kg_dir / "kg_stats.json")
        runtime_rag_count = int(manifest.get("rag_chunk_count", 0) or 0)
        runtime_entity_count = int(manifest.get("kg_entity_count", 0) or kg_stats.get("total_entities", 0) or 0)
        runtime_relation_count = int(manifest.get("kg_relation_count", 0) or kg_stats.get("total_relations", 0) or 0)
        builtin_relation_path = self.builtin_kg_dir / "relations.compact.jsonl.gz"
        builtin_counts = _builtin_record_counts(
            self.builtin_manifest_path,
            self.builtin_kg_dir / "kg_stats.json",
            self.builtin_rag_chunks_path,
            builtin_relation_path,
            self.builtin_kg_dir / "entities.jsonl",
        )
        builtin_ready = bool(
            self.builtin_rag_chunks_path.exists()
            and (self.builtin_kg_dir / "entities.jsonl").exists()
            and builtin_relation_path.exists()
        )
        runtime_vectors = self.vector.engine.count() if self.vector.engine is not None else 0
        builtin_vectors_ready = self.builtin_index is not None and self.builtin_index.vector_ready
        builtin_vectors = self.builtin_index.count if builtin_vectors_ready else 0
        vector_ready = bool(builtin_vectors_ready or self.vector.is_ready)
        vector_status = "success" if vector_ready else str(manifest.get("vector_status") or "pending")
        if self.builtin_index is not None and self.builtin_index.dense_enabled and not builtin_vectors_ready:
            vector_status = "warning"
        builtin_manifest = _load_json(self.builtin_manifest_path)
        return {
            "enabled": self.enabled,
            "ready": self.is_ready,
            "base_dir": str(self.base_dir),
            "upload_dir": str(self.upload_dir),
            "structured_dir": str(self.structured_dir),
            "manifest_path": str(self.manifest_path),
            "rag_chunks_path": str(self.rag.chunks_path),
            "kg_dir": str(self.kg.kg_dir),
            "builtin_ready": builtin_ready,
            "builtin_dir": str(self.builtin_dir),
            "builtin_manifest_path": str(self.builtin_manifest_path),
            "builtin_rag_chunks_path": str(self.builtin_rag_chunks_path),
            "builtin_kg_dir": str(self.builtin_kg_dir),
            "builtin_rag_chunk_count": builtin_counts["rag_chunks"],
            "builtin_kg_entity_count": builtin_counts["entities"],
            "builtin_kg_relation_count": builtin_counts["relations"],
            "builtin_generated_at": builtin_manifest.get("generated_at"),
            "builtin_source_count": int((builtin_manifest.get("record_counts") or {}).get("sources") or 0),
            "builtin_index_ready": self.builtin_index is not None,
            "builtin_vector_ready": builtin_vectors_ready,
            "builtin_vector_status": "success" if builtin_vectors_ready else "warning" if self.builtin_index is not None and self.builtin_index.dense_enabled else "pending",
            "builtin_vector_chunk_count": builtin_vectors,
            "runtime_vector_chunk_count": runtime_vectors,
            "runtime_document_count": int(manifest.get("document_count", 0) or 0),
            "runtime_rag_chunk_count": runtime_rag_count,
            "runtime_kg_entity_count": runtime_entity_count,
            "runtime_kg_relation_count": runtime_relation_count,
            "vector_ready": vector_ready,
            "vector_chunk_count": builtin_vectors + runtime_vectors,
            "vector_status": vector_status,
            "store_type": manifest.get("store_type", "project_runtime_knowledge"),
            "document_count": int(manifest.get("document_count", 0) or 0),
            "rag_chunk_count": runtime_rag_count + builtin_counts["rag_chunks"],
            "kg_entity_count": runtime_entity_count + builtin_counts["entities"],
            "kg_relation_count": runtime_relation_count + builtin_counts["relations"],
            "structured_document_count": int(manifest.get("structured_document_count", 0) or 0),
            "structured_block_count": int(manifest.get("structured_block_count", 0) or 0),
            "markdown_document_count": int(manifest.get("markdown_document_count", 0) or 0),
            "pipeline": manifest.get("pipeline") if isinstance(manifest.get("pipeline"), list) else [],
            "last_ingestion": manifest.get("last_ingestion") if isinstance(manifest.get("last_ingestion"), dict) else {},
            "updated_at": manifest.get("updated_at"),
        }

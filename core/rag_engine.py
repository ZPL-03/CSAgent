"""基于 ChromaDB 的文本向量检索。"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any, Dict, Iterable, List

from core.config_loader import load_app_config
from core.paths import CHROMA_DIR


class _InMemoryCollection:
    def __init__(self) -> None:
        self._rows: List[Dict[str, Any]] = []

    def upsert(self, ids: List[str], documents: List[str], embeddings: List[List[float]], metadatas: List[Dict]) -> None:
        for row_id, document, embedding, metadata in zip(ids, documents, embeddings, metadatas):
            replaced = False
            for row in self._rows:
                if row["id"] == row_id:
                    row.update({"document": document, "embedding": embedding, "metadata": metadata})
                    replaced = True
                    break
            if not replaced:
                self._rows.append({"id": row_id, "document": document, "embedding": embedding, "metadata": metadata})

    def query(self, query_embeddings: List[List[float]], n_results: int, where: Dict | None = None) -> Dict[str, List[List[Any]]]:
        rows = self._rows
        if where:
            filtered = []
            for row in rows:
                metadata = row.get("metadata", {})
                if all(metadata.get(key) == value for key, value in where.items()):
                    filtered.append(row)
            rows = filtered
        query_embedding = query_embeddings[0] if query_embeddings else []
        ranked = sorted(rows, key=lambda row: self._distance(query_embedding, row.get("embedding", [])))[:n_results]
        return {
            "documents": [[row.get("document") for row in ranked]],
            "metadatas": [[row.get("metadata") for row in ranked]],
            "ids": [[row.get("id") for row in ranked]],
            "distances": [[self._distance(query_embedding, row.get("embedding", [])) for row in ranked]],
        }

    @staticmethod
    def _distance(left: List[float], right: List[float]) -> float:
        if not left or not right:
            return 0.0
        size = min(len(left), len(right))
        return sum((left[index] - right[index]) ** 2 for index in range(size))


class _InMemoryClient:
    def __init__(self) -> None:
        self._collections: Dict[str, _InMemoryCollection] = {}

    def get_or_create_collection(self, name: str):
        if name not in self._collections:
            self._collections[name] = _InMemoryCollection()
        return self._collections[name]

    def delete_collection(self, name: str) -> None:
        self._collections.pop(name, None)


class RAGEngine:
    """负责知识写入与相似案例检索。"""

    def __init__(
        self,
        chroma_dir: Path | None = None,
        embedding_model: str | None = None,
        collection_name: str = "csdm_case_memory",
    ) -> None:
        app_config = load_app_config()
        rag_config = dict(app_config.get("rag", {}))

        self.chroma_dir = chroma_dir or CHROMA_DIR
        self.chroma_dir.mkdir(parents=True, exist_ok=True)
        self.collection_name = collection_name
        self.client = self._build_client()
        self.collection = self.client.get_or_create_collection(name=self.collection_name)

        self.embedding_model_name = embedding_model or str(rag_config.get("embedding_model", "BAAI/bge-m3"))
        self.embedding_cache_dir = Path(str(rag_config.get("embedding_cache_dir", "models/embedding_cache")))
        self.embedding_cache_dir.mkdir(parents=True, exist_ok=True)
        self.local_files_only = bool(rag_config.get("local_files_only", True))
        self.use_hash_embedding_only = (os.getenv("CSDM_cph_USE_HASH_EMBEDDING", "0") == "1") or bool(
            rag_config.get("use_hash_embedding_only", False)
        )
        self.allow_hash_fallback = bool(rag_config.get("allow_hash_fallback", True))

        self._embedder = None
        self._embedder_failed = False

    def _build_client(self):
        try:
            import chromadb
        except Exception:
            return _InMemoryClient()
        return chromadb.PersistentClient(path=str(self.chroma_dir))

    @property
    def embedder(self):
        if self.use_hash_embedding_only:
            self._embedder_failed = True
            raise RuntimeError("当前配置显式启用哈希嵌入模式")

        if self._embedder is None and not self._embedder_failed:
            try:
                from sentence_transformers import SentenceTransformer

                self._embedder = SentenceTransformer(
                    self.embedding_model_name,
                    cache_folder=str(self.embedding_cache_dir),
                    local_files_only=self.local_files_only,
                )
            except Exception:
                self._embedder_failed = True
                raise
        return self._embedder

    def _embedding(self, text: str) -> List[float]:
        if self._embedder_failed:
            return self._hash_embedding(text)

        try:
            vector = self.embedder.encode(text)
            return [float(value) for value in vector]
        except Exception:
            self._embedder_failed = self.allow_hash_fallback
            if not self.allow_hash_fallback:
                raise
            return self._hash_embedding(text)

    def _hash_embedding(self, text: str, dims: int = 32) -> List[float]:
        chunks = []
        seed = text.encode("utf-8", errors="replace")
        for index in range(dims):
            digest = hashlib.sha256(seed + f":{index}".encode("ascii")).digest()
            value = int.from_bytes(digest[:4], byteorder="big", signed=False) / 2**32
            chunks.append(float(value))
        return chunks

    def _to_text(self, record: Dict) -> str:
        return json.dumps(record, ensure_ascii=False, sort_keys=True)

    def _reset_collection(self) -> None:
        try:
            self.client.delete_collection(self.collection_name)
        except Exception:
            pass
        self.collection = self.client.get_or_create_collection(name=self.collection_name)

    def reset_collection(self) -> None:
        """只重置当前 collection，避免误删同一 Chroma 目录下的其他集合。"""
        self._reset_collection()

    def count(self) -> int:
        try:
            return int(self.collection.count())
        except Exception:
            rows = getattr(self.collection, "_rows", None)
            if isinstance(rows, list):
                return len(rows)
        return 0

    def upsert_documents(self, ids: Iterable[str], documents: Iterable[str], metadatas: Iterable[Dict] | None = None) -> None:
        doc_ids = [str(item) for item in ids]
        docs = [str(item) for item in documents]
        if not doc_ids or not docs:
            return
        if len(doc_ids) != len(docs):
            raise ValueError("ids 和 documents 数量不一致")
        metadata_list = list(metadatas) if metadatas is not None else [{} for _ in docs]
        if len(metadata_list) != len(docs):
            raise ValueError("metadatas 和 documents 数量不一致")
        embeddings = [self._embedding(doc) for doc in docs]
        try:
            self.collection.upsert(ids=doc_ids, documents=docs, embeddings=embeddings, metadatas=metadata_list)
        except Exception:
            self._reset_collection()
            self.collection.upsert(ids=doc_ids, documents=docs, embeddings=embeddings, metadatas=metadata_list)

    def upsert_records(self, records: Iterable[Dict], id_key: str) -> None:
        records = list(records)
        if not records:
            return
        self.upsert_documents(
            ids=[str(record[id_key]) for record in records],
            documents=[self._to_text(record) for record in records],
            metadatas=[{"kind": id_key} for _ in records],
        )

    def query_text(self, query_text: str, top_k: int = 5, where: Dict | None = None) -> List[Dict[str, object]]:
        try:
            results = self.collection.query(
                query_embeddings=[self._embedding(query_text)],
                n_results=top_k,
                where=where,
            )
        except Exception:
            self._reset_collection()
            return []

        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        ids = results.get("ids", [[]])[0]
        distances = results.get("distances", [[]])[0]
        output: List[Dict[str, object]] = []
        for index, document in enumerate(documents):
            output.append(
                {
                    "id": ids[index] if index < len(ids) else None,
                    "document": document,
                    "metadata": metadatas[index] if index < len(metadatas) else {},
                    "distance": distances[index] if index < len(distances) else None,
                }
            )
        return output

    def retrieve(self, query: Dict, top_k: int = 5) -> List[Dict]:
        query_text = self._to_text(query)
        results = self.query_text(query_text, top_k=top_k)
        output: List[Dict] = []
        for item in results:
            document = str(item.get("document", ""))
            try:
                output.append(json.loads(document))
            except json.JSONDecodeError:
                output.append({"raw": document})
        return output

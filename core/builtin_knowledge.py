"""内置知识包的只读 BM25 与语义向量检索。"""

from __future__ import annotations

import json
import re
import sqlite3
import threading
import unicodedata
from functools import lru_cache
from contextlib import closing
from pathlib import Path
from typing import Any


ENCODING_CONTRACT = "unique_token_weighted_mean_normalized_cls"


def retrieval_tokens(text: str) -> list[str]:
    """匹配内置 FTS5 索引的英文词及中文二至四字分词契约。"""
    tokens = []
    value = unicodedata.normalize("NFKC", text).lower()
    for match in re.finditer(r"[a-z0-9]+(?:[-_/][a-z0-9]+)*|[\u3400-\u4dbf\u4e00-\u9fff]+", value):
        term = match.group()
        if re.fullmatch(r"[\u3400-\u4dbf\u4e00-\u9fff]+", term):
            if len(term) == 1:
                tokens.append(term)
            for size in range(2, min(4, len(term)) + 1):
                tokens.extend(term[index:index + size] for index in range(len(term) - size + 1))
        else:
            tokens.append(term)
    return list(dict.fromkeys(tokens))


_MODEL_LOCK = threading.Lock()


@lru_cache(maxsize=1)
def _encoder(model_path: str):
    import torch
    from transformers import AutoModel, AutoTokenizer

    device = "cuda" if torch.cuda.is_available() else "cpu"
    tokenizer = AutoTokenizer.from_pretrained(model_path, local_files_only=True, use_fast=True)
    model = AutoModel.from_pretrained(
        model_path, local_files_only=True, use_safetensors=False,
        dtype=torch.float16 if device == "cuda" else torch.float32,
    ).to(device).eval()
    return tokenizer, model


def encode_query(query: str, engine, metadata: dict[str, str]):
    """按索引的窗口、CLS 池化和去重 token 权重编码完整查询。"""
    import torch

    if engine.use_hash_embedding_only:
        raise RuntimeError("内置知识语义检索不接受哈希嵌入")
    if engine.embedding_model_name != metadata["dense_model"]:
        raise RuntimeError("配置的嵌入模型与内置向量索引不一致")
    with _MODEL_LOCK, torch.inference_mode():
        tokenizer, model = _encoder(engine._resolve_embedding_model_reference())
        encoded = tokenizer(
            [query], padding=True, truncation=True,
            max_length=int(metadata["dense_max_length"]), stride=int(metadata["dense_window_overlap"]),
            return_overflowing_tokens=True, return_tensors="pt",
        )
        encoded.pop("overflow_to_sample_mapping")
        weights = (encoded["attention_mask"].sum(dim=1).float() - tokenizer.num_special_tokens_to_add(pair=False)).clamp_min(1)
        weights[1:] = (weights[1:] - int(metadata["dense_window_overlap"])).clamp_min(1)
        aggregate = torch.zeros(int(metadata["dense_dimension"]), device=model.device)
        for start in range(0, len(weights), 8):
            inputs = {key: value[start:start + 8].to(model.device) for key, value in encoded.items()}
            vectors = torch.nn.functional.normalize(model(**inputs).last_hidden_state[:, 0].float(), p=2, dim=1)
            aggregate += (vectors * weights[start:start + 8].to(model.device).unsqueeze(1)).sum(dim=0)
        return torch.nn.functional.normalize(aggregate / weights.sum().to(model.device), p=2, dim=0).cpu().numpy()


class BuiltinKnowledgeIndex:
    """SQLite 连接逐查询创建，向量矩阵只读映射，模型仅在后台首次查询时加载。"""

    def __init__(self, index_path: Path, *, engine=None, dense_enabled: bool = True) -> None:
        import numpy as np

        self.index_path = index_path.resolve(strict=True)
        with self.connect() as connection:
            self.metadata = dict(connection.execute("SELECT key,value FROM metadata"))
        if self.metadata.get("schema_version") != "2":
            raise ValueError("内置检索索引版本不受支持")
        self.count = int(self.metadata["chunk_count"])
        self.engine = engine
        self.dense_enabled = dense_enabled and engine is not None
        self.embeddings = None
        if self.metadata.get("dense_enabled") == "1":
            if self.metadata.get("dense_window_aggregation") != ENCODING_CONTRACT:
                raise ValueError("内置索引语义编码契约不匹配")
            path = (self.index_path.parent / self.metadata["dense_file"]).resolve(strict=True)
            if path.parent != self.index_path.parent:
                raise ValueError("内置向量文件必须位于索引目录内")
            self.embeddings = np.load(path, mmap_mode="r", allow_pickle=False)
            if self.embeddings.shape != (self.count, int(self.metadata["dense_dimension"])) or self.embeddings.dtype != np.float32:
                raise ValueError("内置向量矩阵与索引记录数、维度或类型不一致")
        elif self.dense_enabled:
            raise ValueError("内置索引未包含语义向量")

    def connect(self):
        return closing(sqlite3.connect(self.index_path.as_uri() + "?mode=ro", uri=True))

    @property
    def vector_ready(self) -> bool:
        if not self.dense_enabled or self.embeddings is None:
            return False
        try:
            if self.engine.use_hash_embedding_only or self.engine.embedding_model_name != self.metadata["dense_model"]:
                return False
            return Path(self.engine._resolve_embedding_model_reference()).is_dir()
        except RuntimeError:
            return False

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        import numpy as np

        if not query.strip() or top_k <= 0 or self.count == 0:
            return []
        tokens = retrieval_tokens(query)
        candidate_k = min(self.count, max(top_k * 20, 100))
        lexical = {}
        payloads = {}
        with self.connect() as connection:
            focused = [token for token in tokens if token.isascii() or len(token) >= 3]
            exact = [token for token in tokens if token.isascii() and len(token) >= 2]
            groups = [(tokens, 1.0)]
            if focused and focused != tokens:
                groups.append((focused, 1.5))
            if exact and exact != focused:
                groups.append((exact, 3.0))
            for group, weight in groups:
                if not group:
                    continue
                expression = " OR ".join('"' + token.replace('"', '""') + '"' for token in group)
                rows = connection.execute(
                    "SELECT chunks.rowid,chunks.payload FROM chunks_fts JOIN chunks ON chunks.rowid=chunks_fts.rowid "
                    "WHERE chunks_fts MATCH ? ORDER BY bm25(chunks_fts,3.0,2.0,1.0) LIMIT ?",
                    (expression, candidate_k),
                ).fetchall()
                for rank, (rowid, payload) in enumerate(rows, 1):
                    lexical[rowid] = lexical.get(rowid, 0.0) + weight / (60 + rank)
                    payloads[rowid] = json.loads(payload)
            lexical_order = sorted(lexical, key=lambda rowid: (-lexical[rowid], rowid))[:candidate_k]
            scores = {rowid: 1.0 / (60 + rank) for rank, rowid in enumerate(lexical_order, 1)}
            sources = {rowid: ["BUILTIN_BM25"] for rowid in scores}
            if self.dense_enabled:
                query_vector = encode_query(query, self.engine, self.metadata)
                if query_vector.shape != (self.embeddings.shape[1],) or not np.isfinite(query_vector).all():
                    raise ValueError("查询向量维度不匹配或包含无效数值")
                similarities = np.asarray(self.embeddings @ query_vector)
                indexes = np.argpartition(similarities, -candidate_k)[-candidate_k:]
                indexes = indexes[np.argsort(similarities[indexes])[::-1]]
                rowids = [int(index) + 1 for index in indexes]
                placeholders = ",".join("?" for _ in rowids)
                for rowid, payload in connection.execute(f"SELECT rowid,payload FROM chunks WHERE rowid IN ({placeholders})", rowids):
                    payloads[rowid] = json.loads(payload)
                for rank, rowid in enumerate(rowids, 1):
                    scores[rowid] = scores.get(rowid, 0.0) + 1.0 / (60 + rank)
                    sources.setdefault(rowid, []).append("BUILTIN_DENSE")
        results = []
        seen_sources = set()
        for rowid in sorted(scores, key=lambda key: (-scores[key], key)):
            chunk = payloads[rowid]
            if chunk.get("retrieval_scope", "main") not in {"main", "mixed"}:
                continue
            source_key = str(chunk.get("source_id") or chunk.get("record_id") or chunk["chunk_id"])
            if source_key in seen_sources:
                continue
            seen_sources.add(source_key)
            results.append({
                **chunk, "text": chunk.get("content_markdown") or chunk.get("content_plain") or "",
                "score": scores[rowid] * 61, "source": "BUILTIN_KNOWLEDGE", "retrieval_sources": sources[rowid],
            })
            if len(results) >= top_k:
                break
        return results

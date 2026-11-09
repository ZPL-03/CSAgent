import json
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from core import builtin_knowledge
from core.builtin_knowledge import BuiltinKnowledgeIndex, retrieval_tokens


def make_index(root: Path, *, shape=(3, 2), aggregation=builtin_knowledge.ENCODING_CONTRACT):
    root.mkdir(parents=True, exist_ok=True)
    path = root / "retrieval_index.sqlite"
    chunks = [
        {"chunk_id":"A1", "source_id":"DOC_A", "record_id":"REC_A", "document_title":"Pressure hull buckling", "content_plain":"pressure hull buckling guidance"},
        {"chunk_id":"B1", "source_id":"DOC_B", "record_id":"REC_B", "document_title":"Filament winding", "content_plain":"filament winding manufacturing"},
        {"chunk_id":"A2", "source_id":"DOC_A", "record_id":"REC_A", "document_title":"Pressure hull buckling", "content_plain":"pressure hull collapse"},
    ]
    metadata = {"schema_version":"2", "chunk_count":"3", "dense_enabled":"1", "dense_dimension":"2", "dense_file":"retrieval_embeddings.npy", "dense_model":"BAAI/bge-m3", "dense_max_length":"1024", "dense_window_overlap":"128", "dense_window_aggregation":aggregation}
    with sqlite3.connect(path) as connection:
        connection.executescript("CREATE TABLE metadata(key TEXT PRIMARY KEY,value TEXT); CREATE TABLE chunks(rowid INTEGER PRIMARY KEY,payload TEXT); CREATE VIRTUAL TABLE chunks_fts USING fts5(title_tokens,section_tokens,content_tokens);")
        connection.executemany("INSERT INTO metadata VALUES (?,?)",metadata.items())
        for rowid, row in enumerate(chunks,1):
            connection.execute("INSERT INTO chunks VALUES (?,?)",(rowid,json.dumps(row)))
            connection.execute("INSERT INTO chunks_fts(rowid,title_tokens,section_tokens,content_tokens) VALUES (?,?,?,?)",(rowid," ".join(retrieval_tokens(row["document_title"])),""," ".join(retrieval_tokens(row["content_plain"]))))
    vectors = np.array([[1.0,0.0],[0.0,1.0],[0.8,0.2]],dtype="float32")
    np.save(root / "retrieval_embeddings.npy", vectors if shape == (3,2) else np.zeros(shape,dtype="float32"))
    return path


def test_builtin_bm25_is_read_only_and_deduplicates_sources(tmp_path):
    path = make_index(tmp_path)
    before = path.read_bytes()
    index = BuiltinKnowledgeIndex(path,dense_enabled=False)
    result = index.search("pressure hull buckling",top_k=3)
    assert len(result) == 1 and result[0]["source_id"] == "DOC_A"
    assert result[0]["retrieval_sources"] == ["BUILTIN_BM25"]
    assert path.read_bytes() == before
    assert not list(tmp_path.glob("*-wal")) and not list(tmp_path.glob("*-journal"))


def test_builtin_dense_uses_prebuilt_vectors_and_preserves_ids(monkeypatch,tmp_path):
    engine = SimpleNamespace(use_hash_embedding_only=False,embedding_model_name="BAAI/bge-m3",_resolve_embedding_model_reference=lambda:str(tmp_path))
    index = BuiltinKnowledgeIndex(make_index(tmp_path),engine=engine)
    monkeypatch.setattr(builtin_knowledge,"encode_query",lambda *args:np.array([0.0,1.0],dtype="float32"))
    result = index.search("无词法命中的查询",top_k=2)
    assert result[0]["chunk_id"] == "B1"
    assert result[0]["retrieval_sources"] == ["BUILTIN_DENSE"]
    assert index.vector_ready


@pytest.mark.parametrize("shape,aggregation",[((2,2),builtin_knowledge.ENCODING_CONTRACT),((3,2),"mean_pooling")])
def test_builtin_rejects_mismatched_index(tmp_path,shape,aggregation):
    with pytest.raises(ValueError):
        BuiltinKnowledgeIndex(make_index(tmp_path,shape=shape,aggregation=aggregation),dense_enabled=False)


def test_builtin_does_not_hide_encoder_failure(monkeypatch,tmp_path):
    engine = SimpleNamespace(use_hash_embedding_only=False)
    index = BuiltinKnowledgeIndex(make_index(tmp_path),engine=engine)
    def fail(*args):
        raise RuntimeError("编码器不可用")
    monkeypatch.setattr(builtin_knowledge,"encode_query",fail)
    with pytest.raises(RuntimeError,match="编码器不可用"):
        index.search("pressure hull")


def test_builtin_connections_can_be_used_from_multiple_workers(tmp_path):
    index = BuiltinKnowledgeIndex(make_index(tmp_path),dense_enabled=False)
    with ThreadPoolExecutor(max_workers=3) as executor:
        results = list(executor.map(index.search,["pressure hull","filament winding","buckling"]))
    assert all(results)
    assert results[1][0]["chunk_id"] == "B1"


def test_builtin_tokenization_matches_bilingual_index():
    tokens = retrieval_tokens("Ｔ７００ 外压圆柱壳 buckling")
    assert "t700" in tokens and "buckling" in tokens
    assert "外压" in tokens and "圆柱壳" in tokens and "外压圆柱" in tokens


def test_builtin_hybrid_combines_lexical_and_dense_provenance(monkeypatch,tmp_path):
    engine = SimpleNamespace(use_hash_embedding_only=False)
    index = BuiltinKnowledgeIndex(make_index(tmp_path),engine=engine)
    monkeypatch.setattr(builtin_knowledge,"encode_query",lambda *args:np.array([1.0,0.0],dtype="float32"))
    result = index.search("pressure hull",top_k=2)
    assert result[0]["chunk_id"] == "A1"
    assert set(result[0]["retrieval_sources"]) == {"BUILTIN_BM25","BUILTIN_DENSE"}


@pytest.mark.parametrize("file", ["retrieval_index.sqlite", "retrieval_embeddings.npy"])
def test_builtin_missing_files_fail_explicitly(tmp_path, file):
    path = make_index(tmp_path)
    (tmp_path / file).unlink()
    with pytest.raises(FileNotFoundError):
        BuiltinKnowledgeIndex(path, dense_enabled=False)


def test_status_merge_preserves_ingestion_pipeline_and_vector_failure():
    from core.domain_knowledge import merge_knowledge_status

    retrieval = {"builtin_vector_ready": True, "builtin_vector_chunk_count": 3, "builtin_vector_status": "success", "pipeline": []}
    steps = [{"name": "解析", "status": "pending"}]
    status = merge_knowledge_status(retrieval, {"vector_ready": False, "vector_status": "pending", "vector_chunk_count": 0, "pipeline": steps})
    assert status["pipeline"] == steps
    assert status["vector_chunk_count"] == 3 and status["vector_status"] == "success"
    assert status["vector_backend"] == "builtin_bge_m3"
    failed = merge_knowledge_status(retrieval, {"vector_ready": False, "vector_status": "failed", "vector_chunk_count": 0, "vector_detail": "模型加载失败"})
    assert failed["vector_status"] == "warning" and failed["runtime_vector_status"] == "failed"
    assert "模型加载失败" in failed["vector_detail"]


def test_domain_merges_prebuilt_index_with_runtime_chunks(tmp_path):
    from core.domain_knowledge import DomainKnowledgeBase

    builtin = tmp_path / "builtin"
    path = make_index(builtin / "rag")
    runtime = tmp_path / "runtime.jsonl"
    runtime.write_text(json.dumps({"chunk_id": "R1", "source_id": "DOC_R", "record_id": "DOC_R", "document_title": "Runtime pressure hull", "content_plain": "pressure hull buckling test"}) + "\n", encoding="utf-8")
    knowledge = DomainKnowledgeBase({"project_knowledge": {"builtin_dir": str(builtin), "builtin_retrieval_index_path": str(path), "builtin_dense_enabled": False, "vector_enabled": False, "rag_chunks_path": str(runtime), "kg_dir": str(tmp_path / "kg"), "manifest_path": str(tmp_path / "manifest.json")}})
    result = knowledge.retrieve_by_query("pressure hull buckling", top_k=4)
    assert {chunk["source_id"] for chunk in result["chunks"]} == {"DOC_A", "DOC_R"}
    assert knowledge.rag.builtin_chunks_paths == []
    assert not knowledge.status()["builtin_vector_ready"]

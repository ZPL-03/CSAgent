"""校验并同步内置知识包，不覆盖用户增量资料、案例或求解工件。"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import shutil
import sqlite3
import sys
from contextlib import closing
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

PATH_MAPPING = {
    "runtime/rag_chunks.compact.jsonl.gz": "rag/rag_chunks.compact.jsonl.gz",
    "runtime/relations.compact.jsonl.gz": "kg/relations.compact.jsonl.gz",
    "runtime/retrieval_index.sqlite": "rag/retrieval_index.sqlite",
    "runtime/retrieval_embeddings.npy": "rag/retrieval_embeddings.npy",
}
REQUIRED_SOURCE_FILES = {
    *PATH_MAPPING, "kg/entities.jsonl", "kg/kg_stats.json", "provenance/source_metadata.compact.jsonl.gz",
    "provenance/retrieval_evaluation.json", "provenance/README.md", "provenance/file_manifest.jsonl",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def jsonl_rows(path: Path):
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8") as stream:
        for line in stream:
            if line.strip():
                yield json.loads(line)


def safe_file(root: Path, relative: str) -> Path:
    path = (root / relative).resolve(strict=True)
    if not path.is_relative_to(root.resolve()) or not path.is_file() or path.is_symlink():
        raise ValueError(f"知识包文件路径不合法：{relative}")
    return path


def validate_bundle(root: Path, *, records: bool = True) -> dict:
    manifest = json.loads((root / "provenance/manifest.json").read_text(encoding="utf-8"))
    for entry in manifest["files"]:
        path = safe_file(root, entry["path"])
        if path.stat().st_size != entry["bytes"] or sha256(path) != entry["sha256"]:
            raise ValueError(f"知识包文件哈希不匹配：{entry['path']}")
    paths = {entry["path"] for entry in manifest["files"]}
    imported = "source_package_sha256" in manifest
    mapping = PATH_MAPPING if imported else {}
    expected = {mapping.get(path, path) for path in REQUIRED_SOURCE_FILES}
    if not expected.issubset(paths):
        raise ValueError(f"知识包缺少文件：{sorted(expected - paths)}")
    index_path = root / mapping.get("runtime/retrieval_index.sqlite", "runtime/retrieval_index.sqlite")
    with closing(sqlite3.connect(index_path.resolve().as_uri() + "?mode=ro", uri=True)) as connection:
        metadata = dict(connection.execute("SELECT key,value FROM metadata"))
        if int(metadata["chunk_count"]) != manifest["record_counts"]["rag_chunks"]:
            raise ValueError("索引与知识包的文本块数量不一致")
        if connection.execute("SELECT count(*) FROM chunks").fetchone()[0] != int(metadata["chunk_count"]):
            raise ValueError("索引实际记录数不一致")
        if records:
            rag_path = root / mapping.get("runtime/rag_chunks.compact.jsonl.gz", "runtime/rag_chunks.compact.jsonl.gz")
            identities = {}
            for row in jsonl_rows(rag_path):
                if not row.get("chunk_id") or row["chunk_id"] in identities:
                    raise ValueError("RAG 文本块编号缺失或重复")
                identities[row["chunk_id"]] = (row.get("chunk_fingerprint"), row.get("record_id"))
            if len(identities) != manifest["record_counts"]["rag_chunks"]:
                raise ValueError("RAG 实际记录数不一致")
            for payload, in connection.execute("SELECT payload FROM chunks"):
                chunk = json.loads(payload)
                if identities.get(chunk["chunk_id"]) != (chunk.get("chunk_fingerprint"), chunk.get("record_id")):
                    raise ValueError("索引与 RAG 的文本块身份不一致")
            relations_path = root / mapping.get("runtime/relations.compact.jsonl.gz", "runtime/relations.compact.jsonl.gz")
            relation_count = 0
            for row in jsonl_rows(relations_path):
                relation_count += 1
                identity = identities.get(row.get("evidence_chunk_id"))
                if identity != (row.get("evidence_chunk_fingerprint"), row.get("record_id")):
                    raise ValueError(f"图谱关系的证据块无效：{row.get('evidence_chunk_id')}")
            if relation_count != manifest["record_counts"]["relations"]:
                raise ValueError("KG 实际关系数不一致")
            for name, path in (("entities", root / "kg/entities.jsonl"), ("sources", root / "provenance/source_metadata.compact.jsonl.gz")):
                if sum(1 for _ in jsonl_rows(path)) != manifest["record_counts"][name]:
                    raise ValueError(f"知识包实际记录数不一致：{name}")
    from core.builtin_knowledge import BuiltinKnowledgeIndex

    index = BuiltinKnowledgeIndex(index_path, dense_enabled=False)
    if imported and sha256(root / "provenance/source_manifest.json") != manifest["source_package_sha256"]:
        raise ValueError("知识包来源清单哈希不一致")
    return {"generated_at": manifest["generated_at"], "record_counts": manifest["record_counts"], "files": len(manifest["files"]), "dense_dimension": index.metadata["dense_dimension"], "verified": True}


def sync_bundle(source: Path, destination: Path, archive: Path) -> dict:
    source = source.resolve(strict=True)
    destination = destination.resolve()
    archive = archive.resolve()
    if destination != ROOT / "knowledge/csllm" or archive.exists() or archive.is_relative_to(ROOT):
        raise ValueError("同步目标必须是项目内置知识目录，备份必须是项目外不存在的目录")
    result = validate_bundle(source)
    source_manifest_path = source / "provenance/manifest.json"
    manifest = json.loads(source_manifest_path.read_text(encoding="utf-8"))
    if {entry["path"] for entry in manifest["files"]} != REQUIRED_SOURCE_FILES:
        raise ValueError("来源文件清单含未定义文件，停止同步")
    if destination.exists():
        shutil.copytree(destination, archive)
        for path in destination.rglob("*"):
            if path.is_file() and sha256(path) != sha256(archive / path.relative_to(destination)):
                raise ValueError("知识包备份校验失败")
    for entry in manifest["files"]:
        target = destination / PATH_MAPPING.get(entry["path"], entry["path"])
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source / entry["path"], target)
        entry["path"] = target.relative_to(destination).as_posix()
    provenance = destination / "provenance"
    shutil.copy2(source_manifest_path, provenance / "source_manifest.json")
    manifest["source_package_sha256"] = sha256(source_manifest_path)
    (provenance / "README.md").write_text(
        "# 内置知识包\n\n`rag/` 保存 RAG 文本块、只读 SQLite FTS5 索引和 BGE-M3 向量矩阵。\n"
        "`kg/` 保存实体、关系与统计。`provenance/` 保存来源元数据、检索评测及文件哈希。\n"
        "`source_manifest.json` 保留数据包的来源清单；`manifest.json` 使用当前项目的相对路径。\n"
        "用户增量资料和真实设计案例不属于该目录。\n", encoding="utf-8",
    )
    manifest["files"] = [entry for entry in manifest["files"] if entry["path"] != "provenance/file_manifest.jsonl"]
    for entry in manifest["files"]:
        path = destination / entry["path"]
        entry.update(bytes=path.stat().st_size, sha256=sha256(path))
    source_copy = provenance / "source_manifest.json"
    manifest["files"].append({"path":"provenance/source_manifest.json", "bytes":source_copy.stat().st_size, "sha256":sha256(source_copy), "records":None})
    file_manifest = provenance / "file_manifest.jsonl"
    file_manifest.write_text("".join(json.dumps(entry, ensure_ascii=False, separators=(",", ":")) + "\n" for entry in manifest["files"]), encoding="utf-8")
    manifest["files"].append({"path":"provenance/file_manifest.jsonl", "bytes":file_manifest.stat().st_size, "sha256":sha256(file_manifest), "records":len(manifest["files"])})
    (provenance / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    result["installed"] = validate_bundle(destination, records=False)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path)
    parser.add_argument("--archive-dir", type=Path)
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    if args.verify_only:
        result = validate_bundle(ROOT / "knowledge/csllm")
    else:
        if args.source is None or args.archive_dir is None:
            parser.error("同步必须提供 --source 和项目外的 --archive-dir")
        result = sync_bundle(args.source, ROOT / "knowledge/csllm", args.archive_dir)
    print(json.dumps(result, ensure_ascii=True))


if __name__ == "__main__":
    main()

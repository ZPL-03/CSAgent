"""只读核查 Chroma SQLite 的逻辑状态，文件字节指纹用于定位存储变化。"""

from __future__ import annotations

import argparse
from contextlib import closing
import hashlib
import json
from pathlib import Path
import sqlite3


DOCUMENT_TABLES = {
    "embeddings", "embedding_metadata", "embedding_metadata_array",
    "embedding_fulltext_search", "embeddings_queue", "max_seq_id",
}
COLLECTION_TABLES = {"collections", "collection_metadata", "segments", "segment_metadata", "tenants", "databases"}
JSON_COLUMNS = {("collections", "config_json_str"), ("collections", "schema_str"),
                ("embeddings_queue_config", "config_json_str")}


def fingerprint(value) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def file_fingerprint(path: Path) -> str:
    with path.open("rb") as source:
        digest = hashlib.sha256()
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def quoted(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def inspect_database(path: Path) -> dict:
    """按事务读取完整逻辑快照，不导入 Chroma，不实例化 PersistentClient。"""
    path = path.resolve(strict=True)
    byte_hash = file_fingerprint(path)
    with closing(sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)) as connection:
        connection.execute("PRAGMA query_only=ON")
        connection.execute("BEGIN")
        integrity = [row[0] for row in connection.execute("PRAGMA integrity_check")]
        if integrity != ["ok"]:
            raise ValueError(f"SQLite 完整性检查失败：{integrity}")
        pragmas = {name: connection.execute("PRAGMA " + name).fetchone()[0] for name in (
            "schema_version", "user_version", "application_id", "page_size", "page_count",
            "freelist_count", "journal_mode", "encoding", "auto_vacuum",
        )}
        schema = connection.execute(
            "SELECT type, name, tbl_name, sql FROM sqlite_schema ORDER BY type, name"
        ).fetchall()
        tables = {}
        for kind, name, _, _ in schema:
            if kind != "table":
                continue
            cursor = connection.execute("SELECT * FROM " + quoted(name))
            columns = [column[0] for column in cursor.description]
            row_hashes = []
            for row in cursor:
                # 配置 JSON 的键序不属于集合语义；文本和向量数据仍按完整值核对。
                values = [
                    {"blob_hex": value.hex()} if isinstance(value, bytes)
                    else json.loads(value) if value is not None and (name, column) in JSON_COLUMNS
                    else value
                    for column, value in zip(columns, row)
                ]
                row_hashes.append(fingerprint(values))
            tables[name] = {"columns": columns, "count": len(row_hashes),
                            "sha256": fingerprint(sorted(row_hashes))}
        lock_rows = []
        if tables.get("acquire_write", {}).get("columns") == ["id", "lock_status"]:
            lock_rows = connection.execute("SELECT id, lock_status FROM acquire_write ORDER BY id").fetchall()
        migrations = connection.execute("SELECT * FROM migrations ORDER BY dir, version").fetchall() if "migrations" in tables else []
        connection.rollback()
    if file_fingerprint(path) != byte_hash:
        raise ValueError("审计期间数据库文件发生变化，不能将快照用于静态比较")
    def group_hash(names):
        return fingerprint({name: tables[name] for name in sorted(names) if name in tables})
    return {
        "path": str(path), "bytes_sha256": byte_hash, "bytes": path.stat().st_size,
        "integrity": integrity, "pragmas": pragmas, "schema": schema, "schema_sha256": fingerprint(schema),
        "tables": tables, "logical_sha256": group_hash(tables),
        "collections_sha256": group_hash(COLLECTION_TABLES),
        "documents_sha256": group_hash(DOCUMENT_TABLES), "migrations_sha256": fingerprint(migrations),
        "migrations": migrations, "write_lock_rows": [list(row) for row in lock_rows],
        "document_counts": {name: tables[name]["count"] for name in sorted(DOCUMENT_TABLES) if name in tables},
    }


def compare_states(before: dict, after: dict) -> dict:
    """区分内容、schema、迁移与已知写锁记录变化，不以文件 bytes 单独判失败。"""
    names = set(before["tables"]) | set(after["tables"])
    changed = sorted(name for name in names if before["tables"].get(name) != after["tables"].get(name))
    equal = {name: before[name + "_sha256"] == after[name + "_sha256"]
             for name in ("schema", "collections", "documents", "migrations")}
    semantic_pragmas_equal = all(before["pragmas"][name] == after["pragmas"][name]
                                for name in ("user_version", "application_id", "encoding"))
    old_locks, new_locks = before["write_lock_rows"], after["write_lock_rows"]
    lock_append = bool(old_locks and len(new_locks) > len(old_locks)
                       and new_locks[:len(old_locks)] == old_locks
                       and new_locks == [[index, 1] for index in range(1, len(new_locks) + 1)])
    known_bookkeeping = changed == ["acquire_write"] and lock_append and all(equal.values()) and semantic_pragmas_equal
    unchanged = not changed and all(equal.values()) and semantic_pragmas_equal
    return {
        "status": "passed" if unchanged or known_bookkeeping else "review_required",
        "bytes_equal": before["bytes_sha256"] == after["bytes_sha256"],
        "logical_equal": before["logical_sha256"] == after["logical_sha256"],
        "semantic_pragmas_equal": semantic_pragmas_equal,
        **{name + "_equal": value for name, value in equal.items()},
        "changed_tables": changed, "known_lock_bookkeeping_only": known_bookkeeping,
        "pragma_changes": {key: [before["pragmas"][key], value] for key, value in after["pragmas"].items()
                           if before["pragmas"][key] != value},
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--compare", type=Path, help="同一数据库的既有只读快照 JSON")
    args = parser.parse_args(argv)
    if args.output.exists():
        parser.error("输出文件已存在，保留既有审计记录")
    result = inspect_database(args.database)
    if args.compare:
        before = json.loads(args.compare.read_text(encoding="utf-8"))
        result["comparison"] = compare_states(before, result)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.output), "bytes_sha256": result["bytes_sha256"],
                      "document_counts": result["document_counts"], "comparison": result.get("comparison")}, ensure_ascii=False))
    return 1 if result.get("comparison", {}).get("status") == "review_required" else 0


if __name__ == "__main__":
    raise SystemExit(main())

import sqlite3

import pytest

from scripts.audit_chroma_state import compare_states, file_fingerprint, inspect_database


def database(tmp_path):
    path = tmp_path / "chroma.sqlite3"
    with sqlite3.connect(path) as connection:
        connection.executescript("""
            CREATE TABLE acquire_write (id INTEGER PRIMARY KEY, lock_status INTEGER NOT NULL);
            INSERT INTO acquire_write VALUES (1, 1);
            CREATE TABLE embeddings (id INTEGER PRIMARY KEY, embedding_id TEXT);
        """)
    return path


def test_readonly_snapshot_and_storage_bytes_are_separate(tmp_path):
    path = database(tmp_path)
    initial_hash = file_fingerprint(path)
    before = inspect_database(path)
    assert file_fingerprint(path) == initial_hash
    with sqlite3.connect(path) as connection:
        connection.execute("VACUUM")
    comparison = compare_states(before, inspect_database(path))
    assert comparison["bytes_equal"] is False
    assert comparison["logical_equal"] is True
    assert comparison["status"] == "passed"
    with pytest.raises(FileNotFoundError):
        inspect_database(tmp_path / "missing.sqlite3")
    assert not (tmp_path / "missing.sqlite3").exists()


def test_write_lock_append_is_not_document_change(tmp_path):
    path = database(tmp_path)
    before = inspect_database(path)
    with sqlite3.connect(path) as connection:
        connection.execute("INSERT INTO acquire_write (lock_status) VALUES (1)")
    comparison = compare_states(before, inspect_database(path))
    assert comparison["changed_tables"] == ["acquire_write"]
    assert comparison["known_lock_bookkeeping_only"] is True
    assert comparison["documents_equal"] is True
    assert comparison["status"] == "passed"


def test_document_or_unknown_lock_change_requires_review(tmp_path):
    path = database(tmp_path)
    before = inspect_database(path)
    with sqlite3.connect(path) as connection:
        connection.execute("UPDATE acquire_write SET lock_status=0")
    assert compare_states(before, inspect_database(path))["status"] == "review_required"
    with sqlite3.connect(path) as connection:
        connection.execute("UPDATE acquire_write SET lock_status=1")
        connection.execute("INSERT INTO embeddings VALUES (1, 'user-document')")
    comparison = compare_states(before, inspect_database(path))
    assert comparison["documents_equal"] is False
    assert comparison["status"] == "review_required"


def test_schema_version_marker_requires_review(tmp_path):
    path = database(tmp_path)
    before = inspect_database(path)
    with sqlite3.connect(path) as connection:
        connection.execute("PRAGMA user_version=7")
    comparison = compare_states(before, inspect_database(path))
    assert comparison["semantic_pragmas_equal"] is False
    assert comparison["pragma_changes"]["user_version"] == [0, 7]
    assert comparison["status"] == "review_required"

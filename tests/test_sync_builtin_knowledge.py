"""用隔离的小型运行包验证完整校验、目录切换和故障回滚。"""

import gzip
import json
from pathlib import Path
import sqlite3

import numpy as np
import pytest

from core.builtin_knowledge import ENCODING_CONTRACT
from core.knowledge_quality import assess_content
from scripts import sync_builtin_knowledge as sync


def write_rows(path, rows):
    with gzip.open(path, "wt", encoding="utf-8") as stream:
        for row in rows:
            stream.write(json.dumps(row, ensure_ascii=False) + "\n")


def refresh_manifest(source):
    path = source / "provenance/manifest.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    for entry in manifest["files"]:
        asset = source / entry["path"]
        entry.update(bytes=asset.stat().st_size, sha256=sync.sha256(asset))
    path.write_text(json.dumps(manifest), encoding="utf-8")


def make_source(source):
    for name in sync.REQUIRED_SOURCE_FILES:
        (source / name).parent.mkdir(parents=True, exist_ok=True)
    content = "Assuming linear elastic material, pressure hull buckling depends on boundary conditions."
    chunk = {"chunk_id": "C1", "chunk_fingerprint": "fp1", "source_id": "S1", "record_id": "R1",
             "content_markdown": content, **assess_content(content)}
    relation = {"source": "Pressure Hull", "target": "Buckling", "relation": "EXPERIENCES",
                "record_id": "R1", "evidence_chunk_id": "C1", "evidence_chunk_fingerprint": "fp1",
                **{key: chunk[key] for key in ("evidence_kind", "evidence_usage", "applicability_context")}}
    write_rows(source / "runtime/rag_chunks.compact.jsonl.gz", [chunk])
    write_rows(source / "runtime/relations.compact.jsonl.gz", [relation])
    write_rows(source / "provenance/source_metadata.compact.jsonl.gz", [{"record_id": "R1", "source_id": "S1"}])
    (source / "kg/entities.jsonl").write_text('{"name":"Pressure Hull"}\n{"name":"Buckling"}\n', encoding="utf-8")
    (source / "kg/kg_stats.json").write_text('{"total_entities":2,"total_relations":1}', encoding="utf-8")
    (source / "provenance/retrieval_evaluation.json").write_text("{}", encoding="utf-8")
    (source / "provenance/README.md").write_text("知识来源说明。", encoding="utf-8")
    (source / "provenance/file_manifest.jsonl").write_text("", encoding="utf-8")
    np.save(source / "runtime/retrieval_embeddings.npy", np.array([[1, 0]], dtype=np.float32))
    metadata = {"schema_version": "2", "chunk_count": "1", "dense_enabled": "1", "dense_dimension": "2",
                "dense_file": "retrieval_embeddings.npy", "dense_window_aggregation": ENCODING_CONTRACT}
    with sqlite3.connect(source / "runtime/retrieval_index.sqlite") as connection:
        connection.executescript("CREATE TABLE metadata(key TEXT PRIMARY KEY, value TEXT); CREATE TABLE chunks(payload TEXT);")
        connection.executemany("INSERT INTO metadata VALUES (?, ?)", metadata.items())
        connection.execute("INSERT INTO chunks VALUES (?)", (json.dumps(chunk),))
    manifest = {"generated_at": "2026-11-19T00:00:00Z",
                "record_counts": {"rag_chunks": 1, "relations": 1, "entities": 2, "sources": 1},
                "files": [{"path": name} for name in sorted(sync.REQUIRED_SOURCE_FILES)]}
    (source / "provenance/manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    refresh_manifest(source)


def hashes(path):
    return {name: sync.sha256(asset) for name, asset in sync.bundle_files(path).items()}


@pytest.fixture
def package(tmp_path, monkeypatch):
    root = tmp_path / "project"
    destination = root / "knowledge/csllm"
    destination.mkdir(parents=True)
    (destination / "old.bin").write_bytes(b"existing knowledge")
    (destination / "obsolete.txt").write_text("旧生成缓存", encoding="utf-8")
    source = tmp_path / "source"
    make_source(source)
    archive = tmp_path / "archive/previous"
    monkeypatch.setattr(sync, "ROOT", root)
    return source, destination, archive


def assert_temporary_removed(destination, archive):
    assert not list(destination.parent.glob(".csllm-sync-*"))
    assert not list(archive.parent.glob(".csllm-backup-*"))


def test_success_replaces_directory_and_archives_all_old_files(package):
    source, destination, archive = package
    before, source_before = hashes(destination), hashes(source)
    result = sync.sync_bundle(source, destination, archive)
    assert result["installed"]["verified"] is True
    assert sync.validate_bundle(destination)["record_counts"] == result["record_counts"]
    assert hashes(archive) == before
    assert hashes(source) == source_before
    manifest = json.loads((destination / "provenance/manifest.json").read_text(encoding="utf-8"))
    assert set(hashes(destination)) == {row["path"] for row in manifest["files"]} | {"provenance/manifest.json"}
    assert "obsolete.txt" not in hashes(destination)
    assert_temporary_removed(destination, archive)


@pytest.mark.parametrize("field", ["evidence_kind", "evidence_usage", "applicability_context"])
@pytest.mark.parametrize("missing", [False, True])
def test_kg_semantics_must_match_current_chunk(package, field, missing):
    source, destination, archive = package
    before = hashes(destination)
    path = source / "runtime/relations.compact.jsonl.gz"
    row = next(sync.jsonl_rows(path))
    if missing:
        del row[field]
    else:
        row[field] = ["Other source conditions"] if field == "applicability_context" else "different"
    write_rows(path, [row])
    refresh_manifest(source)
    with pytest.raises(ValueError):
        sync.sync_bundle(source, destination, archive)
    assert hashes(destination) == before
    assert not archive.exists()
    assert_temporary_removed(destination, archive)


@pytest.mark.parametrize("failure", ["copy", "corrupt_copy", "validation", "backup", "corrupt_backup"])
def test_preparation_failure_never_changes_installed_package(package, monkeypatch, failure):
    source, destination, archive = package
    before = hashes(destination)
    copy, validate, copytree = sync.shutil.copy2, sync.validate_bundle, sync.shutil.copytree

    def copy_file(src, target, *args, **kwargs):
        result = copy(src, target, *args, **kwargs)
        if Path(target).name == "retrieval_embeddings.npy":
            if failure == "copy":
                raise OSError("copy interrupted")
            if failure == "corrupt_copy":
                Path(target).write_bytes(b"damaged vector file")
        return result

    def validate_stage(path, **kwargs):
        if path != source and failure == "validation":
            assert hashes(destination) == before
            assert not archive.exists()
            raise ValueError("staged validation failed")
        return validate(path, **kwargs)

    def copy_backup(src, target, *args, **kwargs):
        result = copytree(src, target, *args, **kwargs)
        if Path(src) == destination and failure == "backup":
            raise OSError("backup interrupted")
        if Path(src) == destination and failure == "corrupt_backup":
            (Path(target) / "old.bin").write_bytes(b"damaged backup")
        return result

    monkeypatch.setattr(sync.shutil, "copy2", copy_file)
    monkeypatch.setattr(sync, "validate_bundle", validate_stage)
    monkeypatch.setattr(sync.shutil, "copytree", copy_backup)
    with pytest.raises((OSError, ValueError)):
        sync.sync_bundle(source, destination, archive)
    assert hashes(destination) == before
    assert not archive.exists()
    assert_temporary_removed(destination, archive)


@pytest.mark.parametrize("phase", ["old_rename", "activation", "after_activation"])
def test_directory_switch_failure_restores_complete_old_package(package, monkeypatch, phase):
    source, destination, archive = package
    before = hashes(destination)
    rename = Path.rename

    def move(path, target):
        if path == destination and phase == "old_rename":
            raise PermissionError("old directory locked")
        if path.name == "package" and Path(target) == destination:
            if phase == "activation":
                raise OSError("activation failed")
            if phase == "after_activation":
                rename(path, target)
                raise KeyboardInterrupt()
        return rename(path, target)

    monkeypatch.setattr(Path, "rename", move)
    with pytest.raises((OSError, KeyboardInterrupt)):
        sync.sync_bundle(source, destination, archive)
    assert hashes(destination) == hashes(archive) == before
    assert_temporary_removed(destination, archive)


def test_failed_rollback_preserves_old_directory_and_verified_archive(package, monkeypatch):
    source, destination, archive = package
    before = hashes(destination)
    rename = Path.rename

    def move(path, target):
        if Path(target) == destination:
            raise PermissionError("destination unavailable")
        return rename(path, target)

    monkeypatch.setattr(Path, "rename", move)
    with pytest.raises(RuntimeError):
        sync.sync_bundle(source, destination, archive)
    retained = list(destination.parent.glob(".csllm-sync-*/previous"))
    assert len(retained) == 1
    assert hashes(retained[0]) == hashes(archive) == before
    assert not destination.exists()


def test_first_install_has_no_old_archive(package):
    source, destination, archive = package
    for path in destination.iterdir():
        path.unlink()
    destination.rmdir()
    sync.sync_bundle(source, destination, archive)
    assert sync.validate_bundle(destination)["verified"] is True
    assert not archive.exists()
    assert_temporary_removed(destination, archive)


@pytest.mark.parametrize("after_activation", [False, True])
def test_first_install_switch_failure_leaves_no_installed_package(package, monkeypatch, after_activation):
    source, destination, archive = package
    for path in destination.iterdir():
        path.unlink()
    destination.rmdir()
    rename = Path.rename

    def move(path, target):
        if path.name == "package" and Path(target) == destination:
            if after_activation:
                rename(path, target)
            raise OSError("activation interrupted")
        return rename(path, target)

    monkeypatch.setattr(Path, "rename", move)
    with pytest.raises(OSError):
        sync.sync_bundle(source, destination, archive)
    assert not destination.exists()
    assert not archive.exists()
    assert_temporary_removed(destination, archive)


def test_validator_rejects_unlisted_files(package):
    source, _, _ = package
    (source / "unused.bin").write_bytes(b"unlisted")
    with pytest.raises(ValueError):
        sync.validate_bundle(source)


def test_archive_must_be_new_and_outside_project_and_source(package):
    source, destination, archive = package
    before = hashes(destination)
    for invalid in (destination.parent / "backup", source / "backup", source):
        with pytest.raises(ValueError):
            sync.sync_bundle(source, destination, invalid)
    assert hashes(destination) == before
    assert not archive.exists()

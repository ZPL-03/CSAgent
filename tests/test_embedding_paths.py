from core import rag_engine


def test_embedding_paths_are_relative_to_project_not_working_directory(monkeypatch, tmp_path):
    project = tmp_path / "project"
    outside = tmp_path / "outside"
    outside.mkdir()
    model = project / "models/local-model"
    model.mkdir(parents=True)
    monkeypatch.chdir(outside)
    monkeypatch.setattr(rag_engine, "ROOT_DIR", project)
    monkeypatch.setattr(rag_engine, "load_app_config", lambda: {
        "rag": {"embedding_model": "models/local-model", "embedding_cache_dir": "models/cache"},
    })
    monkeypatch.setattr(rag_engine.RAGEngine, "_build_client", lambda _self: rag_engine._InMemoryClient())
    engine = rag_engine.RAGEngine(chroma_dir=tmp_path / "chroma")
    assert engine.embedding_cache_dir == project / "models/cache"
    assert engine._resolve_embedding_model_reference() == str(model.resolve())
    assert not (outside / "models").exists()


def test_absolute_embedding_cache_directory_is_preserved(monkeypatch, tmp_path):
    cache = tmp_path / "shared-cache"
    monkeypatch.setattr(rag_engine, "load_app_config", lambda: {"rag": {"embedding_cache_dir": str(cache)}})
    monkeypatch.setattr(rag_engine.RAGEngine, "_build_client", lambda _self: rag_engine._InMemoryClient())
    engine = rag_engine.RAGEngine(chroma_dir=tmp_path / "chroma")
    assert engine.embedding_cache_dir == cache

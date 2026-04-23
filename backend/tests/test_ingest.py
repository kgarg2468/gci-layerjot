from __future__ import annotations

from types import SimpleNamespace

import backend.rag.ingest as ingest


def test_is_ingested_requires_sqlite_artifact(monkeypatch, tmp_path):
    db_dir = tmp_path / "chroma_db"
    monkeypatch.setattr(ingest, "settings", SimpleNamespace(chroma_db_path=str(db_dir)))

    assert ingest.is_ingested() is False

    db_dir.mkdir()
    assert ingest.is_ingested() is False

    (db_dir / "chroma.sqlite3").write_text("", encoding="utf-8")
    assert ingest.is_ingested() is True

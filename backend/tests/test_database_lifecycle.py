
from fastapi.testclient import TestClient

import app.main as main


def test_lifespan_disposes_shared_database_engines(monkeypatch):
    disposed = []

    monkeypatch.setattr(
        main,
        "dispose_database_engines",
        lambda: disposed.append("postgres"),
    )
    monkeypatch.setattr(
        main,
        "dispose_sqlite_engine",
        lambda: disposed.append("sqlite"),
    )

    with TestClient(main.app):
        pass

    assert disposed == ["postgres", "sqlite"]

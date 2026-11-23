
from fastapi.testclient import TestClient

import app.main as main


def test_lifespan_disposes_shared_database_engines(monkeypatch):
    disposed = []

    monkeypatch.setattr(
        main,
        "dispose_redis_client",
        lambda: disposed.append("redis"),
    )
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

    assert disposed == ["redis", "postgres", "sqlite"]


def test_lifespan_runs_document_index_recovery(monkeypatch):
    calls = []

    monkeypatch.setattr(
        main,
        "_run_document_index_recovery",
        lambda: calls.append("recovery"),
    )
    monkeypatch.setattr(main, "dispose_redis_client", lambda: None)
    monkeypatch.setattr(main, "dispose_database_engines", lambda: None)
    monkeypatch.setattr(main, "dispose_sqlite_engine", lambda: None)

    with TestClient(main.app):
        pass

    assert calls == ["recovery"]


def test_document_recovery_connection_failure_does_not_escape(monkeypatch):
    def fail_to_connect():
        raise RuntimeError("database unavailable")

    monkeypatch.setattr(main, "get_document_connection", fail_to_connect)

    # The helper must contain the connection failure so startup can continue.
    main._run_document_index_recovery()

    monkeypatch.setattr(main, "_run_document_index_recovery", lambda: None)
    monkeypatch.setattr(main, "dispose_redis_client", lambda: None)
    monkeypatch.setattr(main, "dispose_database_engines", lambda: None)
    monkeypatch.setattr(main, "dispose_sqlite_engine", lambda: None)

    with TestClient(main.app):
        pass

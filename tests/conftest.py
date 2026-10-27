from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from services.api.app.main import app
from services.common.db import Base, get_db, make_engine, make_session_factory
from apps.api.main import app as nourishloop_app
from apps.api.core.database import Base as NourishLoopBase
from apps.api.core.database import get_db as nourishloop_get_db
from apps.api.core.database import make_engine as nourishloop_make_engine
from apps.api.core.database import make_session_factory as nourishloop_make_session_factory
from apps.api.core import import_models  # noqa: F401
from apps.api.seed import seed as nourishloop_seed


@pytest.fixture()
def db_session(tmp_path):
    database_url = f"sqlite:///{tmp_path / 'test.db'}"
    engine = make_engine(database_url)
    testing_session_factory = make_session_factory(engine)

    Base.metadata.create_all(bind=engine)
    session = testing_session_factory()

    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture()
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture()
def nl_stack(tmp_path, monkeypatch):
    from apps.api.core.config import get_settings

    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("DEMO_AUTH_ENABLED", "true")
    monkeypatch.setenv("EXPLANATION_PROVIDER", "deterministic")
    get_settings.cache_clear()
    engine = nourishloop_make_engine(f"sqlite:///{tmp_path / 'nourishloop.db'}")
    NourishLoopBase.metadata.create_all(bind=engine)
    session_factory = nourishloop_make_session_factory(engine)
    with session_factory() as db:
        nourishloop_seed(db)

    def override_get_db():
        with session_factory() as db:
            yield db

    nourishloop_app.dependency_overrides[nourishloop_get_db] = override_get_db
    with TestClient(nourishloop_app) as test_client:
        yield test_client, session_factory
    nourishloop_app.dependency_overrides.clear()
    engine.dispose()
    get_settings.cache_clear()


@pytest.fixture()
def nl_client(nl_stack):
    return nl_stack[0]

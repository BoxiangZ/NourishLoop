from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from apps.api.core.config import get_settings


class Base(DeclarativeBase):
    pass


def make_engine(url: str):
    kwargs = {"pool_pre_ping": True}
    if url.startswith("sqlite"):
        kwargs["connect_args"] = {"check_same_thread": False}
    return create_engine(url, **kwargs)


def make_session_factory(engine):
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, class_=Session)


_engine = None
_session_factory = None


def get_db() -> Generator[Session, None, None]:
    global _engine, _session_factory
    if _session_factory is None:
        _engine = make_engine(get_settings().database_url)
        _session_factory = make_session_factory(_engine)
    with _session_factory() as db:
        yield db

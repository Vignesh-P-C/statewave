"""Shared fake DB-session test doubles for admin endpoint tests.

Several admin endpoint tests need to stand in for a real async SQLAlchemy
session without hitting Postgres: they monkeypatch
``server.db.engine.get_session_factory`` with a factory that returns one of
these fakes, then inspect the compiled statement(s) the endpoint executed.

This module holds only the generic scaffolding shared by callers with the
same lightweight execute/scalar shape used by ``test_admin_like_escape.py``.
Tests that need a differently-shaped fake session (e.g. one that tracks
commits/rollbacks, or pops results off a queue) should keep their own local
fake rather than force-fitting it into this one.
"""

from __future__ import annotations


class FakeScalarRows:
    def all(self):
        return []


class FakeResult:
    def all(self):
        return []

    def scalars(self):
        return FakeScalarRows()


class FakeSession:
    def __init__(self):
        self.statements = []

    async def scalar(self, statement):
        self.statements.append(statement)
        return 0

    async def execute(self, statement):
        self.statements.append(statement)
        return FakeResult()


class FakeSessionContext:
    def __init__(self, session):
        self.session = session

    async def __aenter__(self):
        return self.session

    async def __aexit__(self, exc_type, exc, tb):
        return False


def install_fake_session_factory(monkeypatch):
    session = FakeSession()
    monkeypatch.setattr(
        "server.db.engine.get_session_factory",
        lambda: lambda: FakeSessionContext(session),
    )
    return session
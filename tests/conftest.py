"""Shared test fixtures."""

from __future__ import annotations

from typing import Generator

import pytest
from httpx import ASGITransport, AsyncClient
from starlette.routing import BaseRoute

from server.app import create_app


def iter_routes(app_or_router) -> Generator[BaseRoute, None, None]:
    """Recursively yield all leaf routes, handling _IncludedRouter wrappers.

    Starlette ≥1.3 stores included routers as _IncludedRouter objects with an
    `original_router` attribute rather than flattening APIRoute entries into
    app.routes directly.  Older versions flatten them.  This walker handles
    both shapes so route-registration tests stay version-agnostic.
    """
    for route in getattr(app_or_router, "routes", []):
        if hasattr(route, "path") and isinstance(route.path, str):
            yield route
        # Starlette <1.3: sub-routers expose their routes via .routes
        if hasattr(route, "routes"):
            yield from iter_routes(route)
        # Starlette ≥1.3: _IncludedRouter wraps the original APIRouter
        if hasattr(route, "original_router"):
            yield from iter_routes(route.original_router)

@pytest.fixture(autouse=True)
def _no_api_key_in_tests(monkeypatch):
    """Unit tests assume open access unless they explicitly set settings.api_key.
    A developer .env with STATEWAVE_API_KEY would otherwise make every HTTP
    test hit the auth middleware and return 401.
    """
    from server.core.config import settings
    monkeypatch.setattr(settings, "api_key", None)


@pytest.fixture
async def client():
    """Async test client that talks to the app without needing a real DB.

    For integration tests that need Postgres, skip or use a test-scoped DB.
    """
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    
    # Dispose engine after test to ensure clean state for next test
    from server.db.engine import dispose_engine
    await dispose_engine()

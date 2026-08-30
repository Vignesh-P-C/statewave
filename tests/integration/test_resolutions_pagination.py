"""Regression: GET /v1/resolutions must actually page — limit/offset were
accepted at the repo layer but never exposed on the route (#332), so a
subject with more resolutions than the hardcoded page size could never
retrieve the rest. This walks every page with a small limit and asserts
every resolution is returned exactly once, in stable order.
"""

from __future__ import annotations

import datetime as dt
import uuid

import pytest

from server.db import repositories as repo
from server.db.tables import ResolutionRow


@pytest.mark.anyio
async def test_offset_pagination_returns_every_resolution_exactly_once(
    session_factory, subject_id
):
    n = 5
    base = dt.datetime(2020, 6, 1, 12, 0, 0, tzinfo=dt.timezone.utc)
    ids = [uuid.uuid4() for _ in range(n)]
    async with session_factory() as session:
        for i, rid in enumerate(ids):
            session.add(
                ResolutionRow(
                    id=rid,
                    subject_id=subject_id,
                    session_id=f"sess-{i}",
                    status="resolved",
                    resolution_summary=f"resolution {i}",
                    resolved_at=base,
                    # updated_at is the ORDER BY key; space these out so page
                    # boundaries are deterministic instead of relying on
                    # same-millisecond insert order.
                    updated_at=base + dt.timedelta(minutes=i),
                )
            )
        await session.commit()

    seen: list[uuid.UUID] = []
    limit = 2
    offset = 0
    for _ in range(n + 3):  # safety bound against an infinite loop
        async with session_factory() as session:
            rows = await repo.list_resolutions(
                session, subject_id, tenant_id=None, limit=limit, offset=offset
            )
        if not rows:
            break
        seen.extend(r.id for r in rows)
        if len(rows) < limit:
            break
        offset += limit

    assert sorted(seen) == sorted(ids), "every resolution must be returned across pages"
    assert len(seen) == len(set(seen)), "no resolution may be returned twice"


@pytest.mark.anyio
async def test_offset_skips_the_correct_number_of_rows(session_factory, subject_id):
    base = dt.datetime(2020, 6, 1, 12, 0, 0, tzinfo=dt.timezone.utc)
    async with session_factory() as session:
        for i in range(3):
            session.add(
                ResolutionRow(
                    id=uuid.uuid4(),
                    subject_id=subject_id,
                    session_id=f"sess-{i}",
                    status="resolved",
                    updated_at=base + dt.timedelta(minutes=i),
                )
            )
        await session.commit()

    async with session_factory() as session:
        first_page = await repo.list_resolutions(
            session, subject_id, tenant_id=None, limit=2, offset=0
        )
    async with session_factory() as session:
        second_page = await repo.list_resolutions(
            session, subject_id, tenant_id=None, limit=2, offset=2
        )

    assert len(first_page) == 2
    assert len(second_page) == 1
    assert {r.id for r in first_page}.isdisjoint({r.id for r in second_page})

@pytest.mark.anyio
async def test_route_exposes_limit_and_offset(client, subject_id):
    """The #332 fix is the route wiring, so exercise GET /v1/resolutions itself."""
    for i in range(3):
        resp = await client.post(
            "/v1/resolutions",
            json={
                "subject_id": subject_id,
                "session_id": f"sess-page-{i}",
                "status": "resolved",
                "resolution_summary": f"resolution {i}",
            },
        )
        assert resp.status_code == 200, resp.text

    first = await client.get(
        "/v1/resolutions", params={"subject_id": subject_id, "limit": 2, "offset": 0}
    )
    assert first.status_code == 200, first.text
    assert len(first.json()) == 2

    second = await client.get(
        "/v1/resolutions", params={"subject_id": subject_id, "limit": 2, "offset": 2}
    )
    assert second.status_code == 200, second.text
    assert len(second.json()) == 1

    seen = {r["session_id"] for r in first.json()} | {r["session_id"] for r in second.json()}
    assert seen == {"sess-page-0", "sess-page-1", "sess-page-2"}

    bad = await client.get("/v1/resolutions", params={"subject_id": subject_id, "limit": 0})
    assert bad.status_code == 422

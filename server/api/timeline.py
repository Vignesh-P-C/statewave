"""Timeline route."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from server.db import repositories as repo
from server.db.engine import get_session
from server.schemas.responses import EpisodeResponse, MemoryResponse, TimelineResponse
from server.core.dependencies import get_tenant_id

router = APIRouter(tags=["timeline"])


@router.get("/v1/timeline", response_model=TimelineResponse, summary="Get subject timeline")
async def get_timeline(
    subject_id: str = Query(...),
    session: AsyncSession = Depends(get_session),
    tenant_id: str | None = Depends(get_tenant_id),
):
    episodes = await repo.list_episodes_by_subject(session, subject_id, tenant_id=tenant_id)
    memories = await repo.list_memories_by_subject(session, subject_id, tenant_id=tenant_id)
    return TimelineResponse(
        subject_id=subject_id,
        episodes=[EpisodeResponse.from_row(e) for e in episodes],
        memories=[MemoryResponse.from_row(m) for m in memories],
    )
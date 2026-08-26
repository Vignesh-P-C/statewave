"""Resolution tracking routes."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from server.core.dependencies import get_tenant_id
from server.db import repositories as repo
from server.db.engine import get_session
from server.db.tables import ResolutionRow
from server.schemas.requests import CreateResolutionRequest
from server.schemas.responses import ResolutionResponse

router = APIRouter(tags=["resolutions"])


@router.post(
    "/v1/resolutions", response_model=ResolutionResponse, summary="Create or update a resolution"
)
async def create_resolution(
    body: CreateResolutionRequest,
    session: AsyncSession = Depends(get_session),
    tenant_id: str | None = Depends(get_tenant_id),
):
    """Track resolution state for a support session. Upserts by subject_id + session_id."""
    resolved_at = datetime.now(timezone.utc) if body.status == "resolved" else None

    row = ResolutionRow(
        id=uuid.uuid4(),
        subject_id=body.subject_id,
        session_id=body.session_id,
        tenant_id=tenant_id,
        status=body.status,
        resolution_summary=body.resolution_summary,
        resolved_at=resolved_at,
        metadata_=body.metadata,
    )

    result = await repo.upsert_resolution(session, row)
    await session.commit()

    return ResolutionResponse.from_row(result)


@router.get(
    "/v1/resolutions",
    response_model=list[ResolutionResponse],
    summary="List resolutions for a subject",
)
async def list_resolutions(
    subject_id: str = Query(..., min_length=1),
    status: str | None = Query(None, pattern=r"^(open|resolved|unresolved)$"),
    session: AsyncSession = Depends(get_session),
    tenant_id: str | None = Depends(get_tenant_id),
):
    """List resolution records for a subject, optionally filtered by status."""
    rows = await repo.list_resolutions(session, subject_id, tenant_id=tenant_id, status=status)
    return [ResolutionResponse.from_row(r) for r in rows]
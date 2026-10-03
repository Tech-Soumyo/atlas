"""Job status routes."""

from __future__ import annotations

from uuid import UUID

from atlas_persistence.postgres.repositories.jobs import JobRepository
from fastapi import APIRouter, HTTPException

from atlas_api.dependencies import ApiKeyDep, SessionDep
from atlas_api.schemas.documents import JobOut

router = APIRouter(prefix="/v1/jobs", tags=["jobs"])


@router.get("/{job_id}", response_model=JobOut)
async def get_job(job_id: UUID, session: SessionDep, _: ApiKeyDep) -> JobOut:
    job = await JobRepository(session).get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="job not found")
    return JobOut.model_validate(JobRepository(session).to_dict(job))

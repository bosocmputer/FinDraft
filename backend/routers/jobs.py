from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

router = APIRouter()


@router.get("/{project_id}/jobs")
async def list_jobs(project_id: str):
    # TODO: list jobs ของ project
    raise HTTPException(501, "Not implemented")


@router.get("/{project_id}/jobs/{job_id}")
async def get_job(project_id: str, job_id: str):
    # TODO: status + progress (%) ของ job
    raise HTTPException(501, "Not implemented")


@router.get("/{project_id}/jobs/{job_id}/stream")
async def stream_job_progress(project_id: str, job_id: str):
    """SSE stream สำหรับ real-time job progress"""
    # TODO: Server-Sent Events — poll jobs table ทุก 1s แล้ว yield
    raise HTTPException(501, "Not implemented")

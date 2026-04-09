from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.post("/{project_id}/export/excel")
async def export_excel(project_id: str):
    """
    Export Excel — async Celery task
    Rate limit: 20/minute per org+user
    """
    # TODO: dispatch export_worker task, return job_id
    raise HTTPException(501, "Not implemented")


@router.post("/{project_id}/export/pdf")
async def export_pdf(project_id: str):
    """
    Export PDF พร้อม DRAFT watermark ถ้า status != finalized
    Rate limit: 20/minute per org+user
    """
    # TODO: dispatch export_worker task, return job_id
    raise HTTPException(501, "Not implemented")


@router.get("/{project_id}/export/history")
async def get_export_history(project_id: str):
    # TODO: list export_history ของ project
    raise HTTPException(501, "Not implemented")


@router.get("/{project_id}/export/{export_id}/download")
async def download_export(project_id: str, export_id: str):
    # TODO: สร้าง signed URL (expire 1h) จาก Supabase Storage
    raise HTTPException(501, "Not implemented")

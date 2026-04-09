from fastapi import APIRouter, HTTPException, UploadFile, File

router = APIRouter()


@router.post("/{project_id}/upload")
async def upload_tb(project_id: str, file: UploadFile = File(...)):
    """
    รับไฟล์ TB (Excel/CSV/PDF)
    1. Validate magic bytes + size
    2. Parse → TBRow list
    3. Insert ลง tb_rows table
    4. Update project status → 'mapping'
    """
    # TODO: wire file_validator + parser
    raise HTTPException(501, "Not implemented")


@router.get("/{project_id}/tb-rows")
async def get_tb_rows(project_id: str):
    # TODO: ดึง tb_rows ของ project
    raise HTTPException(501, "Not implemented")

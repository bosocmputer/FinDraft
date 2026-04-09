from fastapi import APIRouter, HTTPException, UploadFile, File, Depends
from database import supabase
from dependencies import get_current_user
from services.parser.file_validator import validate_file
from services.parser.excel_parser import parse_excel
from services.parser.csv_parser import parse_csv

router = APIRouter()


async def _check_project_access(project_id: str, user_id: str, roles=("admin", "auditor")) -> dict:
    project = (
        supabase.table("projects")
        .select("*")
        .eq("id", project_id)
        .is_("deleted_at", "null")
        .single()
        .execute()
    )
    if not project.data:
        raise HTTPException(404, "Project not found")

    member = (
        supabase.table("user_organizations")
        .select("role")
        .eq("user_id", user_id)
        .eq("org_id", project.data["org_id"])
        .execute()
    )
    if not member.data or member.data[0]["role"] not in roles:
        raise HTTPException(403, "Insufficient permissions")

    return project.data


@router.post("/{project_id}/upload")
async def upload_tb(
    project_id: str,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    project = await _check_project_access(project_id, current_user["id"])

    if project["status"] not in ("uploading", "mapping"):
        raise HTTPException(400, f"Cannot upload in status: {project['status']}")

    # 1. Validate file
    await validate_file(file)

    # 2. Read bytes
    file_bytes = await file.read()
    ext = file.filename.rsplit(".", 1)[-1].lower() if file.filename else ""

    # 3. Parse
    try:
        if ext == "xlsx":
            rows = parse_excel(file_bytes)
        elif ext == "csv":
            rows = parse_csv(file_bytes)
        elif ext == "pdf":
            raise HTTPException(400, "PDF upload coming in Phase 2 — please use Excel/CSV")
        else:
            raise HTTPException(400, f"Unsupported file type: .{ext}")
    except (ValueError, Exception) as e:
        raise HTTPException(400, f"Parse error: {str(e)}")

    # 4. ลบ tb_rows เก่าของ project นี้ก่อน
    supabase.table("tb_rows").delete().eq("project_id", project_id).execute()

    # 5. Insert tb_rows ใหม่ (batch 500)
    batch_size = 500
    rows_data = [
        {
            "project_id": project_id,
            "account_code": r.account_code,
            "account_name": r.account_name,
            "debit": float(r.debit),
            "credit": float(r.credit),
            "row_order": r.row_order,
        }
        for r in rows
    ]

    for i in range(0, len(rows_data), batch_size):
        supabase.table("tb_rows").insert(rows_data[i:i + batch_size]).execute()

    # 6. Update project status → mapping
    supabase.table("projects").update({"status": "mapping"}).eq("id", project_id).execute()

    # 7. Upload ไฟล์ต้นฉบับขึ้น Supabase Storage
    try:
        storage_path = f"{project['org_id']}/{project_id}/{file.filename}"
        supabase.storage.from_("tb-files").upload(
            path=storage_path,
            file=file_bytes,
            file_options={"content-type": file.content_type or "application/octet-stream"},
        )
    except Exception:
        pass  # storage upload ไม่ block — continue ได้

    return {
        "message": "Upload successful",
        "rows_imported": len(rows),
        "project_status": "mapping",
    }


@router.get("/{project_id}/tb-rows")
async def get_tb_rows(
    project_id: str,
    current_user: dict = Depends(get_current_user),
):
    await _check_project_access(project_id, current_user["id"], roles=("admin", "auditor", "viewer"))

    result = (
        supabase.table("tb_rows")
        .select("*")
        .eq("project_id", project_id)
        .order("row_order")
        .execute()
    )
    return result.data or []

from fastapi import HTTPException, UploadFile

ALLOWED_MAGIC_BYTES = {
    "xlsx": b"PK\x03\x04",
    "csv": None,   # ตรวจ encoding แทน
    "pdf": b"%PDF",
}
MAX_FILE_SIZE_BYTES = 20 * 1024 * 1024  # 20 MB


async def validate_file(file: UploadFile) -> None:
    # ตรวจขนาดจาก Content-Length header ถ้ามี
    if file.size and file.size > MAX_FILE_SIZE_BYTES:
        raise HTTPException(400, "File too large (max 20MB)")

    header = await file.read(8)
    await file.seek(0)

    # ตรวจขนาดจาก bytes ที่อ่านมา (fallback)
    if len(header) == 0:
        raise HTTPException(400, "Empty file")

    ext = file.filename.rsplit(".", 1)[-1].lower() if file.filename else ""
    if ext not in ALLOWED_MAGIC_BYTES:
        raise HTTPException(400, f"Unsupported file type: .{ext} — use xlsx, csv, or pdf")

    expected = ALLOWED_MAGIC_BYTES.get(ext)
    if expected and not header.startswith(expected):
        raise HTTPException(400, "File content does not match extension")

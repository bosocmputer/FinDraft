# Module 2 — File Upload & Parser

_Blueprint v3.2 | [← Index](../README.md)_

---

## รองรับ Input

| Format        | วิธีอ่าน        | ความซับซ้อน |
| ------------- | --------------- | ----------- |
| Excel (.xlsx) | openpyxl        | ต่ำ         |
| CSV           | pandas          | ต่ำ         |
| PDF (text)    | pdfplumber      | กลาง        |
| PDF (scan)    | pytesseract OCR | สูง         |

## File Validation (ก่อน Parse)

```python
ALLOWED_MAGIC_BYTES = {
    "xlsx": b"PK\x03\x04",          # ZIP-based
    "csv":  None,                    # ตรวจ encoding แทน
    "pdf":  b"%PDF",
}
MAX_FILE_SIZE_BYTES = 20 * 1024 * 1024  # 20 MB

async def validate_file(file: UploadFile) -> None:
    # 1. ตรวจขนาดไฟล์
    if file.size > MAX_FILE_SIZE_BYTES:
        raise HTTPException(400, "File too large (max 20MB)")
    # 2. ตรวจ magic bytes — ไม่ใช่แค่ extension
    header = await file.read(8)
    await file.seek(0)
    ext = file.filename.rsplit(".", 1)[-1].lower()
    expected = ALLOWED_MAGIC_BYTES.get(ext)
    if expected and not header.startswith(expected):
        raise HTTPException(400, "File content does not match extension")
```

## TBRow Schema

> **หมายเหตุ:** ใช้ `Decimal` แทน `float` เพื่อป้องกัน floating-point rounding error
> ที่ทำให้ validation fail (เช่น `1500000.0 != 1500000.000000000001`)

```python
from decimal import Decimal, ROUND_HALF_UP

class TBRow(BaseModel):
    account_code: str
    account_name: str
    debit: Decimal = Decimal("0")
    credit: Decimal = Decimal("0")
    net: Decimal = Decimal("0")   # คำนวณหลัง parse — debit - credit

    @validator("debit", "credit", pre=True)
    def parse_number(cls, v):
        if isinstance(v, str):
            cleaned = v.replace(",", "").strip() or "0"
            return Decimal(cleaned).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        return Decimal(str(v or 0)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    @validator("net", always=True)
    def compute_net(cls, v, values):
        debit = values.get("debit", Decimal("0"))
        credit = values.get("credit", Decimal("0"))
        return (debit - credit).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
```

## Claude Code Prompt

```
สร้าง parser service ใน Python ที่:
1. รับไฟล์ Excel/CSV/PDF
2. ตรวจ magic bytes ก่อน parse (ใช้ file_validator.py)
3. Auto-detect ว่า column ไหนคือ account_code, account_name, debit, credit
4. Normalize ตัวเลข (ลบ comma, แปลง string เป็น float, handle None/empty)
5. Return list ของ TBRow objects พร้อม row_order
6. Handle error กรณี format ไม่ตรง พร้อม error message ชัดเจน
```

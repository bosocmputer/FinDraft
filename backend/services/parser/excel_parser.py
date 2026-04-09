from decimal import Decimal, ROUND_HALF_UP
from pydantic import BaseModel, validator
from typing import List
import openpyxl
import io


class TBRow(BaseModel):
    account_code: str
    account_name: str
    debit: Decimal = Decimal("0")
    credit: Decimal = Decimal("0")
    net: Decimal = Decimal("0")
    row_order: int = 0

    @validator("debit", "credit", pre=True)
    def parse_number(cls, v):
        if v is None or v == "":
            return Decimal("0")
        if isinstance(v, str):
            cleaned = v.replace(",", "").strip() or "0"
            return Decimal(cleaned).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        return Decimal(str(v)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    @validator("net", always=True)
    def compute_net(cls, v, values):
        debit = values.get("debit", Decimal("0"))
        credit = values.get("credit", Decimal("0"))
        return (debit - credit).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


# Keywords สำหรับ auto-detect columns
_CODE_KEYWORDS = {"code", "รหัส", "account_code", "acct", "เลขที่"}
_NAME_KEYWORDS = {"name", "ชื่อ", "account_name", "description", "รายการ", "บัญชี"}
_DEBIT_KEYWORDS = {"debit", "เดบิต", "dr", "ยอดดร"}
_CREDIT_KEYWORDS = {"credit", "เครดิต", "cr", "ยอดcr"}


def _detect_column(header: str, keywords: set) -> bool:
    return any(kw in header.lower() for kw in keywords)


def parse_excel(file_bytes: bytes) -> List[TBRow]:
    wb = openpyxl.load_workbook(io.BytesIO(file_bytes), data_only=True)
    ws = wb.active

    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        raise ValueError("Excel file is empty")

    # หา header row (row แรกที่มีค่า)
    header_row_idx = 0
    for i, row in enumerate(rows):
        if any(cell is not None for cell in row):
            header_row_idx = i
            break

    headers = [str(cell).strip() if cell is not None else "" for cell in rows[header_row_idx]]

    # Auto-detect column index
    col_code = col_name = col_debit = col_credit = None
    for i, h in enumerate(headers):
        if col_code is None and _detect_column(h, _CODE_KEYWORDS):
            col_code = i
        elif col_name is None and _detect_column(h, _NAME_KEYWORDS):
            col_name = i
        if col_debit is None and _detect_column(h, _DEBIT_KEYWORDS):
            col_debit = i
        if col_credit is None and _detect_column(h, _CREDIT_KEYWORDS):
            col_credit = i

    if col_code is None or col_name is None:
        raise ValueError(
            "Cannot detect account_code/account_name columns. "
            f"Found headers: {headers}"
        )

    result = []
    for order, row in enumerate(rows[header_row_idx + 1:], start=1):
        code = row[col_code] if col_code < len(row) else None
        name = row[col_name] if col_name < len(row) else None

        if not code or not name:
            continue  # skip empty rows

        debit = row[col_debit] if col_debit is not None and col_debit < len(row) else 0
        credit = row[col_credit] if col_credit is not None and col_credit < len(row) else 0

        result.append(TBRow(
            account_code=str(code).strip(),
            account_name=str(name).strip(),
            debit=debit,
            credit=credit,
            row_order=order,
        ))

    if not result:
        raise ValueError("No data rows found in Excel file")

    return result

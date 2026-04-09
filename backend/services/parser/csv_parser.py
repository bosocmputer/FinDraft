import io
import csv
from typing import List
from .excel_parser import TBRow, _detect_column, _CODE_KEYWORDS, _NAME_KEYWORDS, _DEBIT_KEYWORDS, _CREDIT_KEYWORDS


def parse_csv(file_bytes: bytes) -> List[TBRow]:
    # ลอง decode UTF-8 ก่อน ถ้าไม่ได้ลอง TIS-620 (ภาษาไทย)
    for encoding in ("utf-8-sig", "tis-620", "cp874", "utf-8"):
        try:
            text = file_bytes.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    else:
        raise ValueError("Cannot decode CSV file — unsupported encoding")

    reader = csv.reader(io.StringIO(text))
    rows = list(reader)

    if not rows:
        raise ValueError("CSV file is empty")

    headers = [h.strip() for h in rows[0]]

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
    for order, row in enumerate(rows[1:], start=1):
        if len(row) <= max(filter(None, [col_code, col_name])):
            continue

        code = row[col_code].strip() if col_code < len(row) else ""
        name = row[col_name].strip() if col_name < len(row) else ""

        if not code or not name:
            continue

        debit = row[col_debit].strip() if col_debit is not None and col_debit < len(row) else "0"
        credit = row[col_credit].strip() if col_credit is not None and col_credit < len(row) else "0"

        result.append(TBRow(
            account_code=code,
            account_name=name,
            debit=debit or "0",
            credit=credit or "0",
            row_order=order,
        ))

    if not result:
        raise ValueError("No data rows found in CSV file")

    return result

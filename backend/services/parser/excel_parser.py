from decimal import Decimal, ROUND_HALF_UP
from pydantic import BaseModel, validator
from typing import List
import openpyxl


class TBRow(BaseModel):
    account_code: str
    account_name: str
    debit: Decimal = Decimal("0")
    credit: Decimal = Decimal("0")
    net: Decimal = Decimal("0")
    row_order: int = 0

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


def parse_excel(file_bytes: bytes) -> List[TBRow]:
    """
    Auto-detect columns: account_code, account_name, debit, credit
    TODO: implement column detection logic
    """
    raise NotImplementedError("Excel parser — implement column auto-detection")

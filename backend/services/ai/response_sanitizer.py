import json
import re
from pydantic import BaseModel, validator

CATEGORIES = {
    "current_asset", "non_current_asset",
    "current_liability", "non_current_liability",
    "equity", "revenue", "cost_of_sales",
    "selling_expense", "admin_expense",
    "other_income", "other_expense",
    "operating_activity", "investing_activity", "financing_activity",
}


class MappingResult(BaseModel):
    account_code: str
    category: str
    fs_line_item: str
    confidence: float

    @validator("category")
    def valid_category(cls, v):
        if v not in CATEGORIES:
            raise ValueError(f"Invalid category: {v}")
        return v

    @validator("confidence")
    def clamp_confidence(cls, v):
        return max(0.0, min(1.0, float(v)))

    @validator("fs_line_item")
    def sanitize_text(cls, v):
        return re.sub(r"[<>\"';&]", "", str(v))[:200]


def sanitize_and_parse_json(raw: str) -> list[MappingResult]:
    # ตัด markdown code block ถ้า provider ใส่มา
    raw = re.sub(r"```(?:json)?|```", "", raw).strip()
    data = json.loads(raw)
    if not isinstance(data, list):
        raise ValueError("Expected JSON array")
    return [MappingResult(**item) for item in data]

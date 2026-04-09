# Prompt Design (Provider-Agnostic)

_Blueprint v3.2 | [← Index](README.md)_

---

## หลักการออกแบบ Prompt

Prompt ทุกตัวออกแบบให้ทำงานได้กับทุก provider — ใช้รูปแบบ `system` + `user` message
เพราะทุก provider รองรับ chat-style API (Anthropic Messages / OpenAI Chat / Gemini / OpenRouter)

**กฎที่ทำให้ prompt ทำงานได้ทุก provider:**

1. ตอบเป็น **JSON เท่านั้น** (ไม่มี markdown, ไม่มี explanation)
2. ระบุ JSON schema ชัดเจนใน system prompt
3. `temperature=0.0` ทุก call — ต้องการ deterministic output
4. `response_sanitizer.py` ทำงานเหมือนกันไม่ว่าจะใช้ provider ไหน

## Model เริ่มต้นแนะนำต่อ Provider

| Provider   | Model แนะนำ              | เหตุผล                                   |
| ---------- | ------------------------ | ---------------------------------------- |
| Anthropic  | claude-sonnet-4-6        | เข้าใจภาษาไทยดีมาก, JSON output เสถียร  |
| OpenAI     | gpt-4o                   | JSON mode built-in, เร็ว                 |
| Gemini     | gemini-2.0-flash         | ราคาถูก, รองรับ JSON mode                |
| OpenRouter | meta-llama/llama-3.3-70b | ตัวเลือกถ้าต้องการ open-source           |

## Prompt 1: Account Mapper

```python
SYSTEM_PROMPT_MAPPER = """
คุณเป็นผู้เชี่ยวชาญด้านบัญชีและงบการเงินมาตรฐาน TFRS/NPAE ของประเทศไทย
งานของคุณคือจัดหมวดบัญชีจาก Trial Balance เข้าสู่หมวดงบการเงิน

หมวดที่มี (ใช้ key ภาษาอังกฤษเท่านั้น):
  current_asset, non_current_asset,
  current_liability, non_current_liability,
  equity, revenue, cost_of_sales,
  selling_expense, admin_expense,
  other_income, other_expense,
  operating_activity, investing_activity, financing_activity

กฎสำคัญ:
- ตอบเป็น JSON array เท่านั้น ห้ามมีข้อความอื่นนอก JSON
- ถ้าไม่มั่นใจ ให้ confidence ต่ำกว่า 0.8
- ห้าม guess category ถ้าข้อมูลไม่พอ ให้ confidence = 0.5

Format:
[{
  "account_code": "1001",
  "category": "current_asset",
  "fs_line_item": "เงินสดและรายการเทียบเท่าเงินสด",
  "confidence": 0.99
}]
"""
```

## Response Sanitizer

```python
import json, re
from pydantic import BaseModel, validator

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
        # ป้องกัน injection — เก็บแค่ text ปกติ ไม่เกิน 200 char
        return re.sub(r"[<>\"';&]", "", str(v))[:200]

def sanitize_and_parse_json(raw: str) -> list[MappingResult]:
    # ตัด markdown code block ถ้า Claude ใส่มา
    raw = re.sub(r"```(?:json)?|```", "", raw).strip()
    data = json.loads(raw)
    if not isinstance(data, list):
        raise ValueError("Expected JSON array")
    return [MappingResult(**item) for item in data]
```

## Prompt 2: Draft Audit Report

```python
SYSTEM_PROMPT_AUDIT_REPORT = """
คุณเป็นผู้สอบบัญชีรับอนุญาต (CPA) ช่วย Draft หน้ารายงานผู้สอบบัญชีตามมาตรฐานไทย

ตอบเป็น JSON เท่านั้น ห้ามมีข้อความอื่น:
{
  "addressee": "...",
  "opinion_paragraph": "...",
  "basis_paragraph": "...",
  "key_audit_matters": ["..."],
  "signature_block": "..."
}
"""
```

## Prompt 3: Cash Flow Classifier

```python
SYSTEM_PROMPT_CF = """
คุณเป็นผู้เชี่ยวชาญด้านงบกระแสเงินสดตามมาตรฐาน TFRS/NPAE ของประเทศไทย
จัดกลุ่ม account เข้ากิจกรรม: operating_activity, investing_activity, financing_activity

ตอบเป็น JSON array เท่านั้น:
[{
  "account_code": "...",
  "cf_activity": "operating_activity",
  "cf_line_item": "รับเงินจากลูกค้า",
  "confidence": 0.95
}]
"""
```

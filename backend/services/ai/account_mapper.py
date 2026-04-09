import json
from typing import List
from .provider_factory import get_provider
from .base_provider import AIMessage
from .response_sanitizer import MappingResult, sanitize_and_parse_json
from services.parser.excel_parser import TBRow

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


def chunked(lst: list, size: int):
    for i in range(0, len(lst), size):
        yield lst[i:i + size]


def fallback_unreviewed(batch: List[TBRow]) -> List[MappingResult]:
    return [
        MappingResult(
            account_code=row.account_code,
            category="current_asset",  # placeholder
            fs_line_item=row.account_name,
            confidence=0.0,
        )
        for row in batch
    ]


async def get_cached_mappings(org_id: str, account_codes: List[str]) -> dict:
    from database import supabase
    result = (
        supabase.table("account_mappings")
        .select("account_code, category, fs_line_item, confidence")
        .eq("org_id", org_id)
        .eq("is_confirmed", True)
        .in_("account_code", account_codes)
        .execute()
    )
    cache = {}
    for row in (result.data or []):
        cache[row["account_code"]] = MappingResult(
            account_code=row["account_code"],
            category=row["category"],
            fs_line_item=row["fs_line_item"] or row["account_code"],
            confidence=float(row["confidence"] or 1.0),
        )
    return cache


async def call_ai_mapper(batch: List[TBRow], org_id: str) -> str:
    provider = await get_provider(org_id)
    user_prompt = json.dumps(
        [{"account_code": r.account_code, "account_name": r.account_name} for r in batch],
        ensure_ascii=False,
    )
    message = AIMessage(system=SYSTEM_PROMPT_MAPPER, user=user_prompt)
    response = await provider.complete(message, temperature=0.0)
    return response.content


async def map_accounts(rows: List[TBRow], org_id: str) -> List[MappingResult]:
    cached = await get_cached_mappings(org_id, [r.account_code for r in rows])
    cache_hits = {r.account_code: cached[r.account_code] for r in rows if r.account_code in cached}
    to_map = [r for r in rows if r.account_code not in cached]

    results: List[MappingResult] = list(cache_hits.values())

    for batch in chunked(to_map, 50):
        for attempt in range(3):
            try:
                raw = await call_ai_mapper(batch, org_id)
                parsed = sanitize_and_parse_json(raw)
                results.extend(parsed)
                break
            except Exception:
                if attempt == 2:
                    results.extend(fallback_unreviewed(batch))

    return results

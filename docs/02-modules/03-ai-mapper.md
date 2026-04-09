# Module 3 — AI Account Mapper

_Blueprint v3.2 | [← Index](../README.md)_

---

## หมวดบัญชี (Chart of Accounts — TFRS/NPAE)

```python
CATEGORIES = {
    "current_asset":          "สินทรัพย์หมุนเวียน",
    "non_current_asset":      "สินทรัพย์ไม่หมุนเวียน",
    "current_liability":      "หนี้สินหมุนเวียน",
    "non_current_liability":  "หนี้สินไม่หมุนเวียน",
    "equity":                 "ส่วนของผู้ถือหุ้น",
    "revenue":                "รายได้",
    "cost_of_sales":          "ต้นทุนขาย",
    "selling_expense":        "ค่าใช้จ่ายในการขาย",
    "admin_expense":          "ค่าใช้จ่ายในการบริหาร",
    "other_income":           "รายได้อื่น",
    "other_expense":          "ค่าใช้จ่ายอื่น",
    # สำหรับ Cash Flow
    "operating_activity":     "กิจกรรมดำเนินงาน",
    "investing_activity":     "กิจกรรมลงทุน",
    "financing_activity":     "กิจกรรมจัดหาเงิน",
}
```

## AI Mapper Flow

```
1. ตรวจ cache: ดึง mapping rules ที่ confirmed แล้วของ org นี้ (scope = org_id)
2. แยก rows ที่มี cache hit vs cache miss
3. ส่งเฉพาะ cache miss ให้ AI provider (ผ่าน provider_factory) batch ละ 50 rows พร้อม retry
4. AI provider return JSON: { account_code, category, fs_line_item, confidence }
5. Sanitize + Validate JSON response ก่อนใช้งาน
6. rows ที่ confidence < 0.8 → flag ให้ user review (unmapped queue)
7. บันทึก confirmed mapping ลง DB ระดับ org_id
```

## Batch + Retry Logic

```python
async def map_accounts(rows: list[TBRow], org_id: str) -> list[MappingResult]:
    # 1. Cache lookup (scoped to org — ไม่ใช่ global)
    cached = await get_cached_mappings(org_id, [r.account_code for r in rows])
    cache_hits = {r.account_code: cached[r.account_code]
                  for r in rows if r.account_code in cached}
    to_map   = [r for r in rows if r.account_code not in cached]

    results = list(cache_hits.values())

    # 2. Batch ส่ง AI provider (ผ่าน provider_factory)
    for batch in chunked(to_map, 50):
        for attempt in range(3):  # retry 3 ครั้ง
            try:
                raw = await call_ai_mapper(batch, org_id)
                parsed = sanitize_and_parse_json(raw)  # validate + sanitize
                results.extend(parsed)
                break
            except (JSONDecodeError, ValidationError):
                if attempt == 2:
                    # fallback: mark ทั้ง batch เป็น needs_review
                    results.extend(fallback_unreviewed(batch))

    return results
```

## Background Job Queue

AI mapping รันเป็น **Celery async task** — FastAPI endpoint return `{ job_id }` ทันที แล้ว client poll `/jobs/{job_id}` หรือ subscribe SSE เพื่อดู progress:

```python
# workers/celery_app.py
from celery import Celery
import os

celery_app = Celery(
    "findraft",
    broker=os.environ["REDIS_URL"],
    backend=os.environ["REDIS_URL"],
)
```

```python
# workers/mapping_worker.py
from workers.celery_app import celery_app

@celery_app.task(bind=True, max_retries=3)
def run_mapping_task(self, project_id: str, org_id: str):
    rows = get_unconfirmed_tb_rows(project_id)
    update_job(project_id, status="running", total_rows=len(rows))
    for i, batch in enumerate(chunked(rows, 50)):
        results = map_accounts(batch, org_id)
        save_mapping_results(results)
        done = min((i + 1) * 50, len(rows))
        update_job(project_id, done_rows=done, progress=int(done / len(rows) * 100))
    update_job(project_id, status="done", finished_at=now())
```

**Environment Variable เพิ่มเติม:** `REDIS_URL=redis://localhost:6379/0`

## Claude Code Prompt

```
สร้าง account_mapper.py ที่:
1. รับ list ของ TBRow และ org_id
2. ตรวจ cache ระดับ org_id ก่อน (ไม่ใช่ global cache)
3. ส่งเฉพาะ cache miss ให้ AI provider (ผ่าน provider_factory) เป็น batch ละ 50 rows
4. Retry 3 ครั้งถ้า AI provider return invalid JSON
5. Fallback: rows ที่ retry หมดแล้วยัง fail → mark confidence=0, is_confirmed=false
6. Sanitize JSON response ก่อน insert ลง DB (ใช้ response_sanitizer.py)
7. บันทึก confirmed mapping rules ลง PostgreSQL (scoped ต่อ org_id)
```

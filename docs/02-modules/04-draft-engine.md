# Module 4 — Draft Engine

_Blueprint v3.2 | [← Index](../README.md)_

---

## งบที่ Draft (ครบชุด MVP)

1. Balance Sheet (งบฐานะการเงิน)
2. P&L (งบกำไรขาดทุนเบ็ดเสร็จ)
3. Cash Flow Statement (งบกระแสเงินสด) — **รวมใน MVP**
4. Statement of Changes in Equity (งบแสดงการเปลี่ยนแปลงส่วนของผู้ถือหุ้น) — **รวมใน MVP**
5. Audit Report — Phase 2

## Validation Rules (5 เงื่อนไข)

> **หมายเหตุ:** เปรียบเทียบด้วย tolerance `Decimal("0.01")` เพื่อป้องกัน rounding error
> ทุก condition ใช้ `abs(diff) > TOLERANCE` ไม่ใช่ `!=`

```python
from decimal import Decimal

TOLERANCE = Decimal("0.01")  # รับผิดชอบ rounding สูงสุด 1 สตางค์

def validate_financial_statements(bs: dict, pl: dict, cf: dict, sce: dict, project_id: str) -> ValidationResult:
    errors = []

    # 1. Balance Sheet สมดุล
    diff1 = abs(Decimal(str(bs["total_assets"])) - Decimal(str(bs["total_liabilities_equity"])))
    if diff1 > TOLERANCE:
        errors.append(
            f"Balance Sheet ไม่สมดุล: diff = {diff1:,.2f} "
            f"(Assets={bs['total_assets']:,.2f}, Liabilities+Equity={bs['total_liabilities_equity']:,.2f})"
        )

    # 2. Net profit ต้องตรงกับ retained earnings delta
    diff2 = abs(Decimal(str(pl["net_profit"])) - Decimal(str(bs["equity_change"]["retained_earnings_delta"])))
    if diff2 > TOLERANCE:
        errors.append(
            f"Net profit ({pl['net_profit']:,.2f}) ไม่ตรงกับ retained earnings delta "
            f"({bs['equity_change']['retained_earnings_delta']:,.2f}) ใน Balance Sheet"
        )

    # 3. ตรวจว่าทุก TB row ถูก confirm แล้ว (ไม่มี unmapped หลุด)
    unmapped = get_unconfirmed_rows(project_id)
    if unmapped:
        codes = ", ".join(r.account_code for r in unmapped[:5])
        errors.append(f"มี {len(unmapped)} rows ที่ยังไม่ได้ confirm mapping (เช่น {codes})")

    # 4. Cash Flow: ยอด net change ต้องตรงกับการเปลี่ยนแปลงเงินสดใน BS
    cf_net = Decimal(str(cf["operating"])) + Decimal(str(cf["investing"])) + Decimal(str(cf["financing"]))
    bs_cash_delta = Decimal(str(bs["end_cash"])) - Decimal(str(bs["begin_cash"]))
    diff4 = abs(cf_net - bs_cash_delta)
    if diff4 > TOLERANCE:
        errors.append(f"Cash Flow net change ({cf_net:,.2f}) ไม่ตรงกับ BS cash delta ({bs_cash_delta:,.2f}): diff = {diff4:,.2f}")

    # 5. SCE: equity ending balance ต้องตรงกับ BS total equity
    diff5 = abs(Decimal(str(sce["equity_end"])) - Decimal(str(bs["total_equity"])))
    if diff5 > TOLERANCE:
        errors.append(f"SCE equity ending ({sce['equity_end']:,.2f}) ไม่ตรงกับ BS total equity ({bs['total_equity']:,.2f}): diff = {diff5:,.2f}")

    return ValidationResult(is_valid=len(errors) == 0, errors=errors)
```

## Cash Flow Method — Indirect Method (มาตรฐาน TFRS/NPAE)

ระบบใช้ **Indirect Method** ตาม TAS 7 / TFRS — เริ่มจาก net profit แล้ว adjust รายการ non-cash:

```
กระแสเงินสดจากกิจกรรมดำเนินงาน (Operating Activities)
  กำไรสุทธิ (Net Profit)                          xxx
  บวก: รายการที่ไม่ใช่เงินสด (Non-cash adjustments)
    ค่าเสื่อมราคาและค่าตัดจำหน่าย                  xxx
    หนี้สูญและหนี้สงสัยจะสูญ                       xxx
    กำไร/ขาดทุนจากการขายสินทรัพย์                 (xxx)
  การเปลี่ยนแปลงในสินทรัพย์/หนี้สินดำเนินงาน
    ลูกหนี้การค้าเพิ่มขึ้น/(ลดลง)                 (xxx)
    สินค้าคงเหลือเพิ่มขึ้น/(ลดลง)                 (xxx)
    เจ้าหนี้การค้าเพิ่มขึ้น/(ลดลง)                 xxx
  เงินสดสุทธิจากกิจกรรมดำเนินงาน                  xxx

กระแสเงินสดจากกิจกรรมลงทุน (Investing Activities)
  ซื้อสินทรัพย์ถาวร                               (xxx)
  ขายสินทรัพย์ถาวร                                xxx
  เงินสดสุทธิจากกิจกรรมลงทุน                      (xxx)

กระแสเงินสดจากกิจกรรมจัดหาเงิน (Financing Activities)
  เงินกู้ยืมระยะยาวเพิ่มขึ้น                        xxx
  ชำระคืนเงินกู้                                   (xxx)
  เงินปันผลจ่าย                                   (xxx)
  เงินสดสุทธิจากกิจกรรมจัดหาเงิน                  (xxx)

เงินสดและรายการเทียบเท่าเงินสดเพิ่มขึ้น/(ลดลง)     xxx
เงินสดต้นงวด                                       xxx
เงินสดปลายงวด                                      xxx  ← ต้องตรงกับ BS end_cash
```

**รายการที่ต้องกรอกมือ (Manual Adjust Items):**
- ค่าเสื่อมราคา — ไม่อยู่ใน TB โดยตรง ต้องกรอกใน CF Editor
- รายการ non-cash อื่น เช่น gain/loss จากการขายสินทรัพย์
- Editor จะมี section "รายการปรับปรุง (Adjustments)" ให้กรอก manual

## Project Status Flow

```
uploading → mapping → reviewing → drafting → finalized
                          ↑
              (unmapped rows ต้องเป็น 0 ก่อนกด Draft)
                                                 ↑
                                     (admin only — lock การแก้ไข)
```

## Comparative Period (ตัวเลขปีก่อน)

งบการเงินครบชุดต้องแสดง **2 คอลัมน์** (ปีปัจจุบัน + ปีก่อนหน้า) ตามมาตรฐาน TFRS/NPAE

- `projects.comparative_year` เก็บปีเปรียบเทียบ (optional)
- `financial_statements.data` JSONB รองรับ `current` และ `comparative` ต่อแต่ละ line item: `{ "line_item": "...", "current": 1500000, "comparative": 1200000 }`
- ถ้า `comparative_year` ระบุ → ดึงจาก finalized project ปีก่อนของ org เดียวกันโดยอัตโนมัติ
- ถ้าไม่ระบุ → Editor แสดงคอลัมน์ปีก่อนว่าง ให้ user กรอก manual ได้

## Claude Code Prompt

```
สร้าง draft_engine.py ที่:
1. รับ confirmed mapping (list of MappingResult) และ project_id
2. ตรวจว่าทุก TB row ถูก confirm แล้ว (ไม่มี is_confirmed=false) ก่อน draft
3. Group และ sum ตาม category → สร้าง BS, P&L, Cash Flow structure
4. Validate 5 เงื่อนไข: BS สมดุล, Net profit = retained earnings delta,
   ไม่มี unmapped rows, CF net = BS cash delta, SCE equity end = BS total equity
5. ถ้า validate ผ่าน → บันทึกงบลง financial_statements, เปลี่ยน project status → 'drafting'
6. ถ้าไม่ผ่าน → return ValidationResult พร้อม error list ทุกจุด
```

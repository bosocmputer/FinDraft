from decimal import Decimal
from dataclasses import dataclass, field
from typing import List
from database import supabase

TOLERANCE = Decimal("0.01")


@dataclass
class ValidationResult:
    is_valid: bool
    errors: List[str] = field(default_factory=list)


def _d(v) -> Decimal:
    return Decimal(str(v or 0))


def build_balance_sheet(mappings: list, comparative: dict = None) -> dict:
    """Group mappings เข้า BS structure
    net = debit - credit
    Asset  → debit normal → net เป็นบวก ✓
    Liab/Equity → credit normal → net เป็นลบ → ต้อง negate เพื่อให้แสดงเป็นบวก
    """
    groups = {
        "current_asset": [],
        "non_current_asset": [],
        "current_liability": [],
        "non_current_liability": [],
        "equity": [],
    }
    for m in mappings:
        if m["category"] in groups:
            groups[m["category"]].append(m)

    def sum_assets(items):
        return float(sum(_d(i["net"]) for i in items))

    def sum_liab_equity(items):
        # negate เพราะ credit normal → net ติดลบ
        return float(sum(-_d(i["net"]) for i in items))

    current_assets = sum_assets(groups["current_asset"])
    non_current_assets = sum_assets(groups["non_current_asset"])
    total_assets = current_assets + non_current_assets

    current_liab = sum_liab_equity(groups["current_liability"])
    non_current_liab = sum_liab_equity(groups["non_current_liability"])
    equity = sum_liab_equity(groups["equity"])
    total_liab_equity = current_liab + non_current_liab + equity

    # หา cash (account ที่ fs_line_item มีคำว่า เงินสด หรือ cash)
    cash_items = [m for m in groups["current_asset"] if
                  "เงินสด" in (m.get("fs_line_item") or "") or
                  "cash" in (m.get("fs_line_item") or "").lower()]
    end_cash = float(sum(_d(i["net"]) for i in cash_items))  # asset → net บวกปกติ

    return {
        "current_assets": {"items": groups["current_asset"], "total": current_assets},
        "non_current_assets": {"items": groups["non_current_asset"], "total": non_current_assets},
        "total_assets": total_assets,
        "current_liabilities": {"items": groups["current_liability"], "total": current_liab},
        "non_current_liabilities": {"items": groups["non_current_liability"], "total": non_current_liab},
        "equity": {"items": groups["equity"], "total": equity},
        "total_liabilities_equity": total_liab_equity,
        "end_cash": end_cash,
        "begin_cash": 0,  # user ต้องกรอก comparative period
        "equity_change": {
            "retained_earnings_delta": 0,  # จะ fill จาก P&L
        },
        "total_equity": equity,
    }


def build_profit_loss(mappings: list) -> dict:
    """
    Revenue/Income → credit normal → net ติดลบ → negate ให้เป็นบวก
    Expense/Cost   → debit normal  → net เป็นบวกอยู่แล้ว
    """
    groups = {
        "revenue": [],
        "cost_of_sales": [],
        "selling_expense": [],
        "admin_expense": [],
        "other_income": [],
        "other_expense": [],
    }
    for m in mappings:
        if m["category"] in groups:
            groups[m["category"]].append(m)

    def sum_income(items):
        return float(sum(-_d(i["net"]) for i in items))  # negate credit-normal

    def sum_expense(items):
        return float(sum(_d(i["net"]) for i in items))   # debit-normal ปกติ

    revenue = sum_income(groups["revenue"])
    cost_of_sales = sum_expense(groups["cost_of_sales"])
    gross_profit = revenue - cost_of_sales
    selling = sum_expense(groups["selling_expense"])
    admin = sum_expense(groups["admin_expense"])
    other_income = sum_income(groups["other_income"])
    other_expense = sum_expense(groups["other_expense"])
    net_profit = gross_profit - selling - admin + other_income - other_expense

    return {
        "revenue": {"items": groups["revenue"], "total": revenue},
        "cost_of_sales": {"items": groups["cost_of_sales"], "total": cost_of_sales},
        "gross_profit": gross_profit,
        "selling_expense": {"items": groups["selling_expense"], "total": selling},
        "admin_expense": {"items": groups["admin_expense"], "total": admin},
        "other_income": {"items": groups["other_income"], "total": other_income},
        "other_expense": {"items": groups["other_expense"], "total": other_expense},
        "net_profit": net_profit,
    }


def build_cash_flow(mappings: list, net_profit: float) -> dict:
    """Indirect method — เริ่มจาก net profit"""
    groups = {
        "operating_activity": [],
        "investing_activity": [],
        "financing_activity": [],
    }
    for m in mappings:
        if m["category"] in groups:
            groups[m["category"]].append(m)

    def sum_group(items):
        return float(sum(_d(i["net"]) for i in items))

    operating_adjustments = sum_group(groups["operating_activity"])
    investing = sum_group(groups["investing_activity"])
    financing = sum_group(groups["financing_activity"])
    operating_total = net_profit + operating_adjustments

    return {
        "net_profit": net_profit,
        "operating_adjustments": {
            "items": groups["operating_activity"],
            "total": operating_adjustments,
            "manual_items": [],  # user กรอกเพิ่ม (ค่าเสื่อม ฯลฯ)
        },
        "operating": operating_total,
        "investing_activities": {"items": groups["investing_activity"], "total": investing},
        "investing": investing,
        "financing_activities": {"items": groups["financing_activity"], "total": financing},
        "financing": financing,
        "net_change": operating_total + investing + financing,
        "begin_cash": 0,
        "end_cash": 0,
    }


def build_sce(equity_total: float, net_profit: float) -> dict:
    """Statement of Changes in Equity — โครงพื้นฐาน"""
    return {
        "equity_begin": equity_total - net_profit,
        "net_profit": net_profit,
        "dividends": 0,
        "other_changes": 0,
        "equity_end": equity_total,
    }


def validate_financial_statements(bs: dict, pl: dict, cf: dict, sce: dict, project_id: str) -> ValidationResult:
    errors = []

    # 1. Balance Sheet สมดุล
    diff1 = abs(_d(bs["total_assets"]) - _d(bs["total_liabilities_equity"]))
    if diff1 > TOLERANCE:
        errors.append(
            f"Balance Sheet ไม่สมดุล: diff = {diff1:,.2f} "
            f"(Assets={bs['total_assets']:,.2f}, L+E={bs['total_liabilities_equity']:,.2f})"
        )

    # 2. Net profit ต้องตรงกับ retained earnings delta
    diff2 = abs(_d(pl["net_profit"]) - _d(bs["equity_change"]["retained_earnings_delta"]))
    if diff2 > TOLERANCE:
        errors.append(
            f"Net profit ({pl['net_profit']:,.2f}) ไม่ตรงกับ retained earnings delta "
            f"({bs['equity_change']['retained_earnings_delta']:,.2f})"
        )

    # 3. Unmapped rows
    unmapped = (
        supabase.table("account_mappings")
        .select("account_code")
        .eq("project_id", project_id)
        .eq("is_confirmed", False)
        .execute()
    )
    if unmapped.data:
        codes = ", ".join(r["account_code"] for r in unmapped.data[:5])
        errors.append(f"มี {len(unmapped.data)} rows ที่ยังไม่ได้ confirm (เช่น {codes})")

    # 4. Cash Flow net change vs BS cash delta
    cf_net = _d(cf["operating"]) + _d(cf["investing"]) + _d(cf["financing"])
    bs_cash_delta = _d(bs["end_cash"]) - _d(bs["begin_cash"])
    diff4 = abs(cf_net - bs_cash_delta)
    if diff4 > TOLERANCE:
        errors.append(
            f"CF net change ({float(cf_net):,.2f}) ≠ BS cash delta ({float(bs_cash_delta):,.2f}): diff={float(diff4):,.2f}"
        )

    # 5. SCE equity end vs BS total equity
    diff5 = abs(_d(sce["equity_end"]) - _d(bs["total_equity"]))
    if diff5 > TOLERANCE:
        errors.append(
            f"SCE equity end ({sce['equity_end']:,.2f}) ≠ BS total equity ({bs['total_equity']:,.2f}): diff={float(diff5):,.2f}"
        )

    return ValidationResult(is_valid=len(errors) == 0, errors=errors)


async def run_draft(project_id: str, org_id: str, created_by: str) -> dict:
    # 1. ตรวจ unmapped ก่อน
    unmapped = (
        supabase.table("account_mappings")
        .select("account_code")
        .eq("project_id", project_id)
        .eq("is_confirmed", False)
        .execute()
    )
    if unmapped.data:
        codes = [r["account_code"] for r in unmapped.data[:5]]
        raise ValueError(f"ยังมี {len(unmapped.data)} rows ที่ยังไม่ confirmed: {', '.join(codes)}")

    # 2. ดึง mappings พร้อม net amount จาก tb_rows
    mappings_resp = (
        supabase.table("account_mappings")
        .select("account_code, account_name, category, fs_line_item, confidence")
        .eq("project_id", project_id)
        .eq("is_confirmed", True)
        .execute()
    )
    mappings = mappings_resp.data or []

    # Join กับ tb_rows เพื่อได้ net amount
    tb_resp = (
        supabase.table("tb_rows")
        .select("account_code, debit, credit, net")
        .eq("project_id", project_id)
        .execute()
    )
    tb_map = {r["account_code"]: r for r in (tb_resp.data or [])}

    for m in mappings:
        tb = tb_map.get(m["account_code"], {})
        m["net"] = tb.get("net", 0)
        m["debit"] = tb.get("debit", 0)
        m["credit"] = tb.get("credit", 0)

    # 3. Build financial statements
    bs = build_balance_sheet(mappings)
    pl = build_profit_loss(mappings)

    # ใส่ net_profit กลับไปใน BS equity_change
    bs["equity_change"]["retained_earnings_delta"] = pl["net_profit"]

    cf = build_cash_flow(mappings, pl["net_profit"])
    sce = build_sce(bs["total_equity"], pl["net_profit"])

    # 4. Validate (soft — บันทึกได้แม้ไม่ผ่าน แต่ return errors)
    validation = validate_financial_statements(bs, pl, cf, sce, project_id)

    # 5. บันทึกลง financial_statements (upsert ต่อ type)
    fs_types = [
        ("balance_sheet", bs),
        ("profit_loss", pl),
        ("cash_flow", cf),
        ("equity_changes", sce),
    ]

    saved_ids = {}
    for fs_type, data in fs_types:
        # ดึง version ล่าสุด
        existing = (
            supabase.table("financial_statements")
            .select("version")
            .eq("project_id", project_id)
            .eq("fs_type", fs_type)
            .order("version", desc=True)
            .limit(1)
            .execute()
        )
        new_version = (existing.data[0]["version"] + 1) if existing.data else 1

        result = supabase.table("financial_statements").insert({
            "project_id": project_id,
            "fs_type": fs_type,
            "data": data,
            "version": new_version,
            "is_final": False,
            "created_by": created_by,
        }).execute()
        saved_ids[fs_type] = result.data[0]["id"]

    # 6. Update project status → drafting
    supabase.table("projects").update({"status": "drafting"}).eq("id", project_id).execute()

    return {
        "validation": {
            "is_valid": validation.is_valid,
            "errors": validation.errors,
        },
        "fs_ids": saved_ids,
        "summary": {
            "total_assets": bs["total_assets"],
            "net_profit": pl["net_profit"],
            "cf_net_change": cf["net_change"],
        },
    }

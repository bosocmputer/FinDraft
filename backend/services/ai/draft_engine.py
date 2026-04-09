from decimal import Decimal
from dataclasses import dataclass, field
from typing import List, Optional

TOLERANCE = Decimal("0.01")


@dataclass
class ValidationResult:
    is_valid: bool
    errors: List[str] = field(default_factory=list)


def validate_financial_statements(
    bs: dict,
    pl: dict,
    cf: dict,
    sce: dict,
    project_id: str,
) -> ValidationResult:
    errors = []

    # 1. Balance Sheet สมดุล
    diff1 = abs(Decimal(str(bs["total_assets"])) - Decimal(str(bs["total_liabilities_equity"])))
    if diff1 > TOLERANCE:
        errors.append(
            f"Balance Sheet ไม่สมดุล: diff = {diff1:,.2f} "
            f"(Assets={bs['total_assets']:,.2f}, Liabilities+Equity={bs['total_liabilities_equity']:,.2f})"
        )

    # 2. Net profit ต้องตรงกับ retained earnings delta
    diff2 = abs(
        Decimal(str(pl["net_profit"])) -
        Decimal(str(bs["equity_change"]["retained_earnings_delta"]))
    )
    if diff2 > TOLERANCE:
        errors.append(
            f"Net profit ({pl['net_profit']:,.2f}) ไม่ตรงกับ retained earnings delta "
            f"({bs['equity_change']['retained_earnings_delta']:,.2f})"
        )

    # 3. ตรวจว่าทุก TB row ถูก confirm แล้ว
    # TODO: query get_unconfirmed_rows(project_id)
    unmapped = []
    if unmapped:
        codes = ", ".join(r.account_code for r in unmapped[:5])
        errors.append(f"มี {len(unmapped)} rows ที่ยังไม่ได้ confirm mapping (เช่น {codes})")

    # 4. Cash Flow: net change ต้องตรงกับ BS cash delta
    cf_net = (
        Decimal(str(cf["operating"])) +
        Decimal(str(cf["investing"])) +
        Decimal(str(cf["financing"]))
    )
    bs_cash_delta = Decimal(str(bs["end_cash"])) - Decimal(str(bs["begin_cash"]))
    diff4 = abs(cf_net - bs_cash_delta)
    if diff4 > TOLERANCE:
        errors.append(
            f"Cash Flow net change ({cf_net:,.2f}) ไม่ตรงกับ BS cash delta ({bs_cash_delta:,.2f}): diff = {diff4:,.2f}"
        )

    # 5. SCE: equity ending balance ต้องตรงกับ BS total equity
    diff5 = abs(Decimal(str(sce["equity_end"])) - Decimal(str(bs["total_equity"])))
    if diff5 > TOLERANCE:
        errors.append(
            f"SCE equity ending ({sce['equity_end']:,.2f}) ไม่ตรงกับ BS total equity ({bs['total_equity']:,.2f}): diff = {diff5:,.2f}"
        )

    return ValidationResult(is_valid=len(errors) == 0, errors=errors)


async def run_draft(project_id: str, org_id: str) -> ValidationResult:
    """
    สร้างงบการเงินครบชุด:
    1. ดึง confirmed mappings
    2. Group/sum ตาม category → BS, P&L, CF, SCE
    3. Validate 5 เงื่อนไข
    4. บันทึกลง financial_statements
    TODO: implement full draft logic
    """
    raise NotImplementedError("Draft engine — implement grouping + financial statement creation")

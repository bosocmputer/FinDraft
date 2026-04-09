import xlsxwriter
from io import BytesIO


def export_balance_sheet(fs_data: dict, is_draft: bool = True) -> bytes:
    output = BytesIO()
    workbook = xlsxwriter.Workbook(output, {"in_memory": True})
    ws = workbook.add_worksheet("งบฐานะการเงิน")

    number_fmt = workbook.add_format({"num_format": "#,##0", "align": "right"})
    total_fmt = workbook.add_format({"bold": True, "top": 1, "num_format": "#,##0"})

    if is_draft:
        draft_fmt = workbook.add_format({"bold": True, "font_color": "#FF0000", "font_size": 14})
        ws.write(0, 0, "*** DRAFT — ยังไม่ได้รับการรับรอง ***", draft_fmt)

    # TODO: write fs_data rows ลง worksheet
    workbook.close()
    return output.getvalue()


def export_all_statements(project_id: str, fs_data: dict, is_draft: bool = True) -> bytes:
    """Export งบทั้งชุด (BS + P&L + CF + SCE) ลง Excel workbook เดียว"""
    # TODO: implement multi-sheet export
    raise NotImplementedError("Full export — implement multi-sheet")

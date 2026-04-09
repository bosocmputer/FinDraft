# Module 6 — Export

_Blueprint v3.2 | [← Index](../README.md)_

---

## DRAFT Watermark Policy

| สถานะ project | Excel watermark     | PDF watermark        |
| ------------- | ------------------- | -------------------- |
| drafting      | header: DRAFT (red) | diagonal red overlay |
| finalized     | ไม่มี               | ไม่มี                |

## Export เป็น Excel

```python
import xlsxwriter

def export_balance_sheet(fs_data: dict, output_path: str, is_draft: bool = True):
    workbook = xlsxwriter.Workbook(output_path)
    ws = workbook.add_worksheet("งบฐานะการเงิน")
    number_fmt = workbook.add_format({"num_format": "#,##0", "align": "right"})
    total_fmt  = workbook.add_format({"bold": True, "top": 1, "num_format": "#,##0"})

    if is_draft:
        draft_fmt = workbook.add_format({
            "bold": True, "font_color": "#FF0000", "font_size": 14
        })
        ws.write(0, 0, "*** DRAFT — ยังไม่ได้รับการรับรอง ***", draft_fmt)
```

## Export เป็น PDF (พร้อม DRAFT watermark)

```python
from weasyprint import HTML, CSS

DRAFT_CSS = """
    body::after {
        content: "DRAFT";
        position: fixed;
        top: 50%; left: 50%;
        transform: translate(-50%, -50%) rotate(-45deg);
        font-size: 100px;
        color: rgba(255, 0, 0, 0.15);
        font-weight: bold;
        z-index: 9999;
        pointer-events: none;
    }
"""

def export_to_pdf(html_content: str, output_path: str, is_draft: bool = True):
    extra_css = DRAFT_CSS if is_draft else ""
    HTML(string=html_content).write_pdf(
        output_path,
        stylesheets=[CSS(string=f"""
            @page {{ size: A4; margin: 2cm; }}
            body {{ font-family: 'Sarabun', sans-serif; }}
            .total {{ border-top: 1px solid black; font-weight: bold; }}
            {extra_css}
        """)]
    )
```

## Signed URL (ไม่ใช่ Public URL ถาวร)

```python
# ทุก export ใช้ signed URL — expire 1 ชั่วโมง
async def get_export_download_url(file_path: str) -> str:
    response = supabase.storage.from_("exports").create_signed_url(
        path=file_path,
        expires_in=3600  # 1 ชั่วโมง
    )
    return response["signedURL"]
```

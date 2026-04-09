try:
    from weasyprint import HTML, CSS
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False

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

BASE_CSS = """
    @page { size: A4; margin: 2cm; }
    body { font-family: 'Sarabun', sans-serif; }
    .total { border-top: 1px solid black; font-weight: bold; }
"""


def export_to_pdf(html_content: str, is_draft: bool = True) -> bytes:
    if not WEASYPRINT_AVAILABLE:
        raise RuntimeError("PDF export requires weasyprint — deploy with Dockerfile")
    extra_css = DRAFT_CSS if is_draft else ""
    return HTML(string=html_content).write_pdf(
        stylesheets=[CSS(string=BASE_CSS + extra_css)]
    )

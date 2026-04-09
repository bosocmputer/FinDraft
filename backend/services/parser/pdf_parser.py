from typing import List
from .excel_parser import TBRow


def parse_pdf(file_bytes: bytes) -> List[TBRow]:
    """
    ใช้ pdfplumber ก่อน ถ้าอ่านไม่ได้ → fallback pytesseract OCR
    TODO: implement PDF parsing + OCR
    """
    raise NotImplementedError("PDF parser — implement pdfplumber + OCR")

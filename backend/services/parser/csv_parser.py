from typing import List
from .excel_parser import TBRow


def parse_csv(file_bytes: bytes) -> List[TBRow]:
    """
    Auto-detect columns: account_code, account_name, debit, credit
    TODO: implement column detection logic
    """
    raise NotImplementedError("CSV parser — implement column auto-detection")

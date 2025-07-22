import os
from decimal import Decimal

from src import BASEPATH

UISPATH = os.path.join(BASEPATH, "billeUI", "uis")
ICONSPATH = os.path.join(BASEPATH, "billeUI", "icons")


def currency_format(value: str | float | Decimal, to_numeric: bool = False) -> str:
    if value == None:
        return None
    if not to_numeric:
        return f"{value:,.2f}".replace(".", "x").replace(",", ".").replace("x", ",")
    elif isinstance(value, str):
        return value.replace(".", "").replace(",", ".")

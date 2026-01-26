from decimal import Decimal, InvalidOperation
from typing import Union

  
def format_currency(amount: Union[Decimal, float, str, int]) -> str:
    try:
        decimal_amount = Decimal(str(amount))
        return f"{decimal_amount:,.2f}"
    except (ValueError, TypeError, InvalidOperation):
        raise ValueError("Invalid amount supplied for formatting")



def parse_decimal(amount: Union[str, float, int, Decimal]) -> Decimal:
    try:
        if isinstance(amount, str):
            amount = amount.replace(',', '')

        return Decimal(str(amount))
    except (InvalidOperation, ValueError, TypeError):
        raise ValueError(f"Could not convert {amount} to Decimal.")

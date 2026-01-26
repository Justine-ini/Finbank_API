import secrets
from decimal import Decimal, ROUND_HALF_UP
from typing import Tuple
from backend.app.bank_account.enums import AccountCurrencyEnum
from backend.app.core.config import settings
from backend.app.core.logging import get_logger
from fastapi import HTTPException, status

logger = get_logger()


def get_currency_code(currency: AccountCurrencyEnum) -> str:
    currency_codes = {
        AccountCurrencyEnum.USD: settings.CURRENCY_CODE_USD,
        AccountCurrencyEnum.EUR: settings.CURRENCY_CODE_EURO,
        AccountCurrencyEnum.GBP: settings.CURRENCY_CODE_GBP,
        AccountCurrencyEnum.NGR: settings.CURRENCY_CODE_NGR,
    }
    currency_code = currency_codes.get(currency)

    if not currency_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "status":"error",
                "message":f"Invalid currency: {currency}"
            }
        )
    
    return currency_code

def split_into_digits(number: str | int)-> list[int]:
    return [int(digit) for digit in str(number)]


def calculate_luhn_check_digit(number:str) -> int:
    digits = split_into_digits(number)

    odd_digits = digits[-1::-2]
    even_digits = digits[-2::-2]

    total = sum(odd_digits)

    for digit in even_digits:
        doubled = digit * 2
        total += sum(split_into_digits(doubled))

    return (10 - (total % 10)) % 10


def generate_account_number(currency:AccountCurrencyEnum) -> str:
    try:
        if not all([settings.BANK_CODE, settings.BANK_BRANCH_CODE]):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "status":"error",
                    "message":"Bank or Branch code not configured"
                }
            )
        currency_code = get_currency_code(currency)

        prefix = f"{settings.BANK_CODE}{settings.BANK_BRANCH_CODE}{currency_code}"

        remaining_digits = 16 - len(prefix) - 1

        random_digits = "".join(
            secrets.choice("0123456789") for _ in range(remaining_digits)
        )
        partial_account_number = f"{prefix}{random_digits}"

        check_digit = calculate_luhn_check_digit(partial_account_number)

        account_number = f"{partial_account_number}{check_digit}"

        return account_number 
    
    except HTTPException as httex:
        logger.error(f"HTTP Exception in account number generation: {httex}")
    except Exception as e:
        logger.error(f"Error generating account number: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status":"error",
                "message":f"Failed to generate account number: {str(e)}"
            }
        )


EXCHANGE_RATES = {
    "USD": {
        "EUR": Decimal("0.8455"),
        "GBP": Decimal("0.7329"),
        "NGN": Decimal("1420.75")
    },
    "EUR": {
        "USD": Decimal("1.1828"),
        "GBP": Decimal("0.8668"),
        "NGN": Decimal("1508.00")
    },
    "GBP": {
        "USD": Decimal("1.3645"),
        "EUR": Decimal("1.1536"),
        "NGN": Decimal("2019.65")
    },
    "NGN": {
        "USD": Decimal("0.00070"),
        "EUR": Decimal("0.00066"),
        "GBP": Decimal("0.00050")
    }
}

CONVERSION_FEE_RATE = Decimal("0.02")  # 2% conversion fee


def get_exchange_rate(
    from_currency: AccountCurrencyEnum,
    to_currency: AccountCurrencyEnum,
) -> Decimal:
    if from_currency == to_currency:
        return Decimal("1.0000")

    try:
        rate = EXCHANGE_RATES[from_currency.value][to_currency.value]
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "status": "error",
                "message": f"Exchange rate from {from_currency} to {to_currency} not available."
            }
        )

    return rate.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)


def calculate_conversion(
    amount: Decimal,
    from_currency: AccountCurrencyEnum,
    to_currency: AccountCurrencyEnum
) -> Tuple[Decimal, Decimal, Decimal]:
    
    if from_currency == to_currency:
        return amount, Decimal("1.00"), Decimal("0.00")
    try:
        exchange_rate = get_exchange_rate(from_currency, to_currency)

        converted_amount = (amount * exchange_rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        conversion_fee = (converted_amount * CONVERSION_FEE_RATE).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        net_amount = (converted_amount - conversion_fee).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        return converted_amount, conversion_fee, net_amount
    except Exception as e:
        logger.error(f"Error calculating conversion: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status":"error",
                "message":f"Failed to calculate currency conversion: {str(e)}"
            }
)

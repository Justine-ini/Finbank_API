import secrets
from datetime import datetime, timedelta, timezone
from typing import Tuple
from argon2 import PasswordHasher
from backend.app.virtual_card.enums import VirtualCardProviderEnum
from backend.app.core.logging import get_logger


logger = get_logger()


def _luhn_checksum(card_number: str) -> int:
    """
    Calculate Luhn checksum for a card number.
    Returns the total - if divisible by 10, card is valid
    """
    total = 0
    reverse_digits = card_number[::-1]

    for i, digit in enumerate(reverse_digits):
        n = int(digit)
        if i % 2 == 1:          # odd positions get doubled
            n *= 2
            if n > 9:
                n -= 9
        total += n

    return total


def luhn_is_valid(card_number: str) -> bool:
    """
    Validate a card number using the Luhn algorithm.

    Usage:
        luhn_is_valid("4532015112830366")  → True
        luhn_is_valid("1234567890123456")  → False
    """
    # basic sanity checks first
    if not card_number.isdigit():
        return False
    if len(card_number) != 16:  # Adjusted for standard 16-digit card numbers
        return False

    return _luhn_checksum(card_number) % 10 == 0


def _calculate_check_digit(partial_number: str) -> int:
    """
    Calculate the Luhn check digit for a partial card number.
    The check digit is the last digit of a valid card number.
    """
    total = 0
    reverse_digits = partial_number[::-1]

    for i, digit in enumerate(reverse_digits):
        n = int(digit)
        if i % 2 == 0:          # even here because check digit not added yet
            n *= 2
            if n > 9:
                n -= 9
        total += n

    return (10 - (total % 10)) % 10


def generate_card_for_provider(provider: VirtualCardProviderEnum) -> str:
    """
    Generate card number based on provider prefix

    Visa       → starts with 4
    Mastercard → starts with 53
    Verve      → starts with 650
    """
    prefix_map = {
        VirtualCardProviderEnum.VISA:       "4",
        VirtualCardProviderEnum.MASTERCARD: "53",
        VirtualCardProviderEnum.VERVE:      "650",
    }

    prefix = prefix_map.get(provider, "4")  # default to Visa

    # total 16 digits - prefix length - 1 (check digit)
    random_length = 15 - len(prefix)

    random_digits = "".join(
        secrets.choice("0123456789") for _ in range(random_length)
    )

    partial = prefix + random_digits

    check_digit = _calculate_check_digit(partial)

    full_card = partial + str(check_digit)

    if not luhn_is_valid(full_card):
        # dont include card number in the log
        logger.error(f"Generated card number failed Luhn validation for provider {provider}")
        raise ValueError("Generated card number is invalid")

    return full_card


def generate_cvv() -> Tuple[str, str]:
    """
    Generate a random 3-digit CVV and its hashed version.
    """
    cvv = "".join(secrets.choice("0123456789") for _ in range(3))
    ph = PasswordHasher()
    cvv_hash = ph.hash(cvv)
    return cvv, cvv_hash

def verify_cvv(cvv: str, cvv_hash: str) -> bool:
    """
    Verify a CVV against its hashed version.
    """

    try:
        ph = PasswordHasher()
        return ph.verify(cvv_hash, cvv)
    except Exception as e:
        logger.error(f"CVV verification failed: {e}")
        return False
    
def generate_expiry_date() -> datetime:
    """
    Generate an expiry date 3 years from now.
    """
    now = datetime.now(timezone.utc)
    year = now.year + 3
    month = now.month

    # Handle month overflow
    if month == 12:
        expiry = datetime(year + 1, 1, 1, tzinfo=timezone.utc)
    else:
        expiry = datetime(year, month + 1, 1, tzinfo=timezone.utc)
    return expiry
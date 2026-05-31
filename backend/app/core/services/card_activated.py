from datetime import datetime
from backend.app.core.config import settings
from backend.app.core.emails.base import EmailTemplate

class VirtualCardActivatedEmail(EmailTemplate):
    """Email template for virtual card activation notifications."""
    template_name = "card_activated.html"
    template_name_plain = "card_activated.txt"
    subject = "Your Virtual Card is Now Active"

async def send_card_activated_email(
    email: str,
    full_name: str,
    card_type: str,
    currency: str,
    masked_card_number: str,
    cvv: str,
    daily_limit: float,
    monthly_limit: float,
    expiry_date: str,
    available_balance: float
)-> None:
    context = {
        "full_name": full_name,
        "card_type": card_type,
        "currency": currency,
        "masked_card_number": masked_card_number,
        "cvv": cvv,
        "daily_limit": daily_limit,
        "monthly_limit": monthly_limit,
        "expiry_date": expiry_date,
        "available_balance": available_balance,
        "site_name": settings.SITE_NAME,
        "support_email": settings.SUPPORT_EMAIL,
        "activated_at": datetime.now().strftime("%Y-%m-%d at %H:%M %S UTC"),
    }
    await VirtualCardActivatedEmail.send_email(email_to=email, context=context)
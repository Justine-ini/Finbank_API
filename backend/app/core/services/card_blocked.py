from datetime import datetime
from locale import currency
from backend.app.core.config import settings
from backend.app.core.emails.base import EmailTemplate

class VirtualCardBlockedEmail(EmailTemplate):
    """Email template for virtual card blocking notifications."""
    template_name = "card_blocked.html"
    template_name_plain = "card_blocked.txt"
    subject = "Your Virtual Card Has Been Blocked"

async def send_card_blocked_email(
    email: str,
    full_name: str,
    card_type: str,
    masked_card_number: str,
    blocked_reason: str,
    blocked_reason_details: str,
    blocked_at: datetime
)-> None:
    context = {
        "full_name": full_name,
        "card_type": card_type,
        "currency": currency,
        "masked_card_number": masked_card_number,
        "blocked_reason": blocked_reason,
        "blocked_reason_details": blocked_reason_details,
        "site_name": settings.SITE_NAME,
        "support_email": settings.SUPPORT_EMAIL,
        "blocked_at": blocked_at.strftime("%Y-%m-%d at %H:%M %S UTC"),
    }
    await VirtualCardBlockedEmail.send_email(email_to=email, context=context)
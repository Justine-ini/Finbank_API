from datetime import datetime
from backend.app.core.config import settings
from backend.app.core.emails.base import EmailTemplate

class VirtualCardCreatedEmail(EmailTemplate):
    """Email template for virtual card creation notifications."""
    template_name = "card_created.html"
    template_name_plain = "card_created.txt"
    subject = "Your Virtual Card Has been Created"

async def send_card_created_email(
    email: str,
    full_name: str,
    card_type: str,
    currency: str,
    masked_card_number: str,
    name_on_card: str,
    daily_limit: float,
    monthly_limit: float,
    expiry_date: str   
)-> None:
    context = {
        "full_name": full_name,
        "card_type": card_type,
        "currency": currency,
        "masked_card_number": masked_card_number,
        "name_on_card": name_on_card,
        "daily_limit": daily_limit,
        "monthly_limit": monthly_limit,
        "expiry_date": expiry_date,
        "site_name": settings.SITE_NAME,
        "support_email": settings.SUPPORT_EMAIL,
        "created_at": datetime.now().strftime("%Y-%m-%d at %H:%M %S UTC"),
    }
    await VirtualCardCreatedEmail.send_email(email_to=email, context=context)
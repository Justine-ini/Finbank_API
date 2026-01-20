from backend.app.core.config import settings
from backend.app.core.emails.base import EmailTemplate


class AccountActivatedEmail(EmailTemplate):
    template_name = "account_activated.html"
    template_name_plain = "account_activated.txt"
    subject = "Bank Account Activated Successfully"

async def send_account_activated_email(
        email:str, 
        full_name: str,
        account_number: str,
        account_name: str,
        account_type: str,
        account_currency: str,
        ) -> None:

    context = {
        "fullname": full_name,
        "account_number": account_number,
        "account_name": account_name,
        "account_type": account_type,
        "currency": account_currency,
        "expiry_time": settings.ACTIVATION_TOKEN_EXPIRATION_MINUTES,
        "site_name": settings.SITE_NAME,
        "support_email": settings.SUPPORT_EMAIL,
    }
    await AccountActivatedEmail.send_email(email_to=email, context=context)
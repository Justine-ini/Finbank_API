from backend.app.core.config import settings
from backend.app.core.emails.base import EmailTemplate



class AccountCreatedEmail(EmailTemplate):
    template_name = "account_created.html"
    template_name_plain = "account_created.txt"
    subject = "welcome - Your bank Account has been Created"

async def send_account_created_email(
        email_to: str,
        fullname: str,
        account_number: str,
        account_type: str,
        account_name,
        currency: str,
        identification_type: str) -> None:
    
    context = {
        "fullname": fullname,
        "account_number": account_number,
        "account_name": account_name,
        "account_type": account_type,
        "currency": currency,
        "identification_type": identification_type,
        "site_name": settings.SITE_NAME,
    }
    await AccountCreatedEmail.send_email(email_to=email_to, context=context)
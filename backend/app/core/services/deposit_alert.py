from decimal import Decimal
from datetime import datetime
from backend.app.core.emails.base import EmailTemplate
from backend.app.core.config import settings

class DepositAlertEmail(EmailTemplate):
    template_name = "deposit_alert.html"
    template_name_plain = "deposit_alert.txt"
    subject = "Deposit Alert Notification"

async def send_deposit_alert_email(
    email: str,
    full_name: str,
    amount: Decimal,
    action: str,
    account_name: str,
    currency: str,
    account_number: str,
    description: str,
    transaction_date: datetime,
    reference: str,
    balance: Decimal,
) -> None:
    
    context = {
        "full_name": full_name,
        "amount": amount,
        "action": action,
        "account_name": account_name,
        "currency": currency,
        "account_number": account_number,
        "description": description,
        "transaction_date": transaction_date,
        "reference": reference,
        "balance": balance,
        "support_email": settings.SUPPORT_EMAIL,
        "site_name": settings.SITE_NAME
    }
    await DepositAlertEmail.send_email(email_to=email, context=context)
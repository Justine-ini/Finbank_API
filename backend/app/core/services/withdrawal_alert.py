from decimal import Decimal
from datetime import datetime
from backend.app.core.emails.base import EmailTemplate
from backend.app.core.config import settings

class WithdrawalAlertEmail(EmailTemplate):
    template_name = "withdrawal_alert.html"
    template_name_plain = "withdrawal_alert.txt"
    subject = "Withdrawal Alert Notification"

async def send_withdrawal_alert_email(
    email: str,
    full_name: str,
    amount: Decimal,
    account_name: str,
    account_number: str,
    currency: str,
    description: str,
    transaction_date: datetime,
    reference: str,
    balance: Decimal,
) -> None:
    
    context = {
        "full_name": full_name,
        "amount": amount,
        "action": "withdrawn",
        "account_name": account_name,
        "currency": currency,
        "account_number": account_number,
        "description": description,
        "transaction_date": transaction_date.strftime("%Y-%m-%d %H:%M:%S UTC"),
        "reference": reference,
        "balance": balance,
        "support_email": settings.SUPPORT_EMAIL,
        "site_name": settings.SITE_NAME
    }
    await WithdrawalAlertEmail.send_email(email_to=email, context=context)
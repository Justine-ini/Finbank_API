from decimal import Decimal
from datetime import datetime
from backend.app.core.emails.base import EmailTemplate
from backend.app.core.config import settings
from backend.app.core.logging import get_logger
from backend.app.bank_account.enums import AccountTypeEnum, AccountCurrencyEnum
from backend.app.core.utils.number_format import format_currency

logger = get_logger()


class TransferAlertEmail(EmailTemplate):
    template_name = "transfer_alert.html"
    template_name_plain = "transfer_alert.txt"
    subject = "Transfer Notification"

async def send_transfer_alert_email(
    *,
    sender_email: str,
    sender_name: str,
    receiver_email: str,
    receiver_name: str,
    receiver_account_number: str,
    amount: Decimal,
    converted_amount: Decimal,
    sender_currency: AccountCurrencyEnum,
    receiver_currency: AccountCurrencyEnum,
    exchange_rate: Decimal | None = None,
    conversion_fee: Decimal | None = None,
    description: str,
    reference: str,
    transaction_date: datetime,
    sender_balance: Decimal,
    receiver_balance: Decimal,
)-> None:
    
    try:
        conversion_applied = sender_currency != receiver_currency

        common_details = {
            "transaction_date": transaction_date.strftime("%Y-%m-%d %H:%M:%S UTC"),
            "description":description,
            "reference": reference,
            "site_name": settings.SITE_NAME,
            "support_email": settings.SUPPORT_EMAIL,

        }
        sender_context = {
            **common_details,
            "is_sender": True,
            "user_name": sender_name,
            "counterparty_name":receiver_name,
            "counterparty_account": receiver_account_number,
            "amount": format_currency(amount),
            "currency": sender_currency.value,
            "user_balance": format_currency(sender_balance),
            "conversion_applied": conversion_applied
        }

        if conversion_applied:
            sender_context.update(
                {
                    "converted_amount": format_currency(converted_amount),
                    "exchange_rate": format_currency(exchange_rate) if exchange_rate else "1.00",
                    "conversion_fee": format_currency(conversion_fee) if conversion_fee else "0.00",
                    "to_currency": receiver_currency.value
                }

            )
        receiver_context = {
            **common_details,
            "is_sender": False,
            "user_name": receiver_name,
            "counterparty_name":sender_name,
            "amount": format_currency(converted_amount if conversion_applied else amount),
            "currency": receiver_currency.value,
            "user_balance": format_currency(receiver_balance),
            "conversion_applied": conversion_applied,
        }

        if conversion_applied:
            receiver_context.update(
                {
                    "orignal_amount": format_currency(amount),
                    "from_currency": sender_currency.value,
                    "exchange_rate": format_currency(exchange_rate) if exchange_rate else "1.00",
                }

            )
        
        await TransferAlertEmail.send_email(
            email_to=sender_email,
            context=sender_context
        )

        await TransferAlertEmail.send_email(
            email_to=receiver_email,
            context=receiver_context
        )

        logger.info(
            f"Transfer alerts sent successfully. Reference: {reference}"
            f"Sender: {sender_email}, Receiver: {receiver_email}"
        )

    except Exception as e:
        logger.error(
            f"Failed to send transfer alerts. Reference: {reference}, Error: {str(e)}"
        )
        raise
from datetime import datetime, timedelta, timezone
from backend.app.core.config import settings
from backend.app.core.emails.base import EmailTemplate


class AccountLockoutEmail(EmailTemplate):
    template_name = "account_lockout.html"
    template_name_plain = "account_lockout.txt"
    subject = "Account Security Alert - Temporary Lockout Notification"

async def send_account_lockout_email(email_to: str, lockout_time: datetime) -> None:
    unlock_time = lockout_time + timedelta(minutes=settings.LOCKOUT_DURATION_MINUTES)
    context = {
        "support_email": settings.SUPPORT_EMAIL,
        "lockout_duration_minutes": settings.LOCKOUT_DURATION_MINUTES,
        "lockout_time": lockout_time.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "unlock_time": unlock_time.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "site_name": settings.SITE_NAME,
    }
    await AccountLockoutEmail.send_email(email_to=email_to, context=context)
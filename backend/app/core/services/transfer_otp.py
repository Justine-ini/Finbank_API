from backend.app.core.emails.base import EmailTemplate
from backend.app.core.config import settings


class TransferOTPEmail(EmailTemplate):
    template_name = "transfer_otp.html"
    template_name_plain = "transfer_otp.txt"
    subject = "Transfer Authorization OTP"

async def send_transfer_otp_email(email: str, otp:str)-> None:
    context = {
        "otp":otp,
        "expiry_time": settings.OTP_EXPIRATION_MINUTES,
        "site_name": settings.SITE_NAME,
        "support_email": settings.SUPPORT_EMAIL
    }

    await TransferOTPEmail.send_email(
        email_to=email,
        context=context
    )
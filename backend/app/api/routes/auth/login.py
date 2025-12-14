from fastapi import APIRouter, Depends, Response, status, HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession
from backend.app.core.db import get_session
from backend.app.auth.utils import create_jwt_token, set_auth_cookies
from backend.app.core.logging import get_logger
from backend.app.core.config import settings
from backend.app.auth.schema import LoginRequestSchema, OTPVerifyRequestSchema
from backend.app.api.services.user_auth import user_auth_service

logger = get_logger()

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/login/request-otp", status_code=status.HTTP_200_OK)
async def request_login_otp(
    login_data: LoginRequestSchema,
    session: AsyncSession = Depends(get_session),
):
    try:
        user =  await user_auth_service.get_user_by_email(login_data.email, session)
        if user:
            await user_auth_service.check_user_lockout(user, session)
            if not await user_auth_service.verify_user_password(login_data.password, user.hashed_password):
                await user_auth_service.increment_failed_login_attempts(user, session)
                remaining_attempts = settings.LOGIN_ATTEMPTS - user.failed_login_attempts

                if remaining_attempts > 0:
                    error_message = (
                        f"Invalid credentials. You have {remaining_attempts} "
                        f"attempt{'s' if remaining_attempts > 1 else ''} remaining "
                        "before your account is temporarily locked."
                    )
                else:
                    error_message = "Your account has been temporarily locked due"
                    f" to multiple failed login attempts. Please try again after {settings.LOCKOUT_DURATION_MINUTES} minutes."

                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED, 
                    detail={
                        "status": "error",
                        "message": error_message,
                        "action": "Please check your email and password and try again.",
                        "remaining_attempts": remaining_attempts,
                    }
                )
            if not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "status": "error",
                        "message": "Your account is inactive.",
                        "action": "Please activate your account.",
                    }
                )
            await user_auth_service.reset_user_state(
                user, session, clear_otp=True, log_action=True
            )
            await user_auth_service.generate_and_save_otp(user, session)

        return {
            "message": "If an account with the provided email exists, an OTP has been sent.",
        }
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Failed to process login OTP request: {e}")
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail={
            "status": "error",
            "message": "Failed to process login OTP request.",
        }
    )


@router.post("/login/verify-otp", status_code=status.HTTP_200_OK)
async def verify_login_otp(
    verify_data: OTPVerifyRequestSchema,
    response: Response,
    session: AsyncSession = Depends(get_session),
):
    try:
        user =await user_auth_service.verify_login_otp(verify_data.email, verify_data.otp, session)

        await user_auth_service.reset_user_state(user, session, clear_otp=True, log_action=True)

        access_token = create_jwt_token(user.id)
        refresh_token = create_jwt_token(user.id)

        set_auth_cookies(response, access_token, refresh_token)

        return {
            "status": "success",
            "message": "Login successful.",
            "user": {
                "email": user.email,
                "username": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "full_name": user.full_name,
                "id_no": user.id_no,
                "role": user.role,
            },
        }

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Failed to verify login OTP request: {e}")
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail={
            "status": "error",
            "message": "Failed to verify login OTP request.",
            "action": "Please try again."
        }
    )
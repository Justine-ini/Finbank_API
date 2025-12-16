from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession
from backend.app.auth.schema import PasswordResetRequestSchema, PasswordResetConfirmSchema
from backend.app.core.db import get_session
from backend.app.api.services.user_auth import user_auth_service
from backend.app.core.services.password_reset import send_password_reset_email
from backend.app.core.logging import get_logger
from backend.app.auth.schema import AccountStatusSchema


logger = get_logger()

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/request-password-reset", status_code=status.HTTP_200_OK)
async def request_password_reset(
    reset_data: PasswordResetRequestSchema,
    session: AsyncSession = Depends(get_session),
) -> dict:
    try:
        user = await user_auth_service.get_user_by_email(reset_data.email,session, include_inactive=True)

        if user:
            if user.account_status != AccountStatusSchema.LOCKED:
                await send_password_reset_email(user.email, user.id)

            else:
                logger.warning(f"Password reset attempted for locked account: {user.email}")
            
        return {"message": "If an account with that email exists, a password reset link has been sent."}
    except Exception as e:
        logger.error(f"Password reset request failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail={
                "status": "error",
                "message": "Failed to process password reset request.",
                "action": "Please try again later."
            })
    
@router.post("/reset-password/{token}", status_code=status.HTTP_200_OK)
async def reset_password(
    token: str,
    reset_data: PasswordResetConfirmSchema,
    session: AsyncSession = Depends(get_session),
) -> dict:
    try:
        await user_auth_service.reset_password(token, reset_data.new_password, session)

        return {"message": "Password has been successfully reset."}
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "status": "error",
                "message": str(e),
                "action": "Please request a new password reset link."
            }
        )

    except Exception as e:
        logger.error(f"Password reset failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail={
                "status": "error",
                "message": "Failed to reset password.",
                "action": "Please try again later."
            })
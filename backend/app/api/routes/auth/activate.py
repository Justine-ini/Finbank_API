from fastapi import APIRouter, HTTPException, status, Depends
from sqlmodel.ext.asyncio.session import AsyncSession
from backend.app.core.db import get_session
from backend.app.core.logging import get_logger
from backend.app.auth.schema import AccountStatusSchema
from backend.app.api.services.user_auth import user_auth_service
from backend.app.core.config import settings
from backend.app.auth.utils import create_activation_token
from backend.app.core.services.activation_email import send_activation_email
from backend.app.auth.schema import EmailRequestSchema


logger = get_logger()

router = APIRouter(prefix="/auth")
@router.get("/activate/{token}", status_code=status.HTTP_200_OK)
async def activate_user(
    token: str,
    session: AsyncSession = Depends(get_session)
):
    try:
        user = await user_auth_service.activate_user_account(token, session)
        return {"message":"Account activated successfully", "email":user.email}
    except ValueError as e:
        error_msg = str(e)

        if error_msg == "Activation token expired":
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail={
                    "status": "error",
                    "message": "Activation link has expired",
                    "action": "Please request a new activation link",
                    "action_url": f"{settings.API_BASE_URL}{settings.API_V1_STR}/auth/resend-activation-link",
                    "email_required": True
                },
            )
        elif error_msg == "Invalid activation token":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "status": "error",
                    "message": "Invalid activation token",
                    "action": "Please confirm that the link you clicked on is correct",
                },
            )
        elif error_msg == "User already activated":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "status": "error",
                    "message": "User already activated",
                    "action": "Please login to your account",
                },
            )
    except HTTPException as http_ex:
        raise http_ex
    except Exception as e:
        logger.error(f"Failed to activate user account: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": "error",
                "message": "Failed to activate user account",
                "action": "Please try again later",
            },
        )
    
@router.post("/resend-activation-link", status_code=status.HTTP_200_OK)
async def resend_activation_link(
    email_data: EmailRequestSchema,
    session: AsyncSession = Depends(get_session),
):
    try:
        user = await user_auth_service.get_user_by_email(
            email_data.email, session, include_inactive=True
        )
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "status": "error",
                    "message": "If an account exists with this email, please check your inbox for the activation link"
                }
            )
        if user.is_active or user.account_status == AccountStatusSchema.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "status": "error",
                    "message": "User account already activated",
                    "action": "Please login to your account"
                }
            )
        activation_token = create_activation_token(user.id)
        await send_activation_email(user.email, activation_token)
        return {
            "message": "If an account exists with this email, please check your inbox for the activation link"
        }
    except HTTPException as http_ex:
        raise http_ex
    except Exception as e:
        logger.error(f"Failed to resend activation link: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": "error",
                "message": "Failed to resend activation link",
                "action": "Please try again later or contact support if the issue persists"
            },
        )
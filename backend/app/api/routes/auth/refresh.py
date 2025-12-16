import jwt
from fastapi import APIRouter, Depends, HTTPException, status, Response, Cookie
from sqlmodel.ext.asyncio.session import AsyncSession
from backend.app.core.db import get_session
from backend.app.core.logging import get_logger
from backend.app.auth.utils import create_jwt_token, set_auth_cookies
from backend.app.api.services.user_auth import user_auth_service
from backend.app.core.config import settings


logger = get_logger()
router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/refresh", status_code=status.HTTP_200_OK)
async def refresh_access_token(
    response: Response,
    refresh_token: str | None = Cookie(None, alias=settings.COOKIE_REFRESH_NAME),
    session: AsyncSession = Depends(get_session)
) -> dict:
    
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail={
                "status": "error",
                "message": "Refresh token missing",
                "action": "Please log in again."
            }
        )   

    try:
        payload = jwt.decode(refresh_token, settings.SIGNING_KEY, algorithms=[settings.JWT_ALGORITHM])

        if payload.get("type") != settings.COOKIE_REFRESH_NAME:

            logger.warning(f"Invalid token type for refresh. Expected '{settings.COOKIE_REFRESH_NAME}', got '{payload.get('type')}'")

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail={
                    "status": "error",
                    "message": "Invalid token type",
                    "action": "Please log in again."
                }
            )
        
        user_id = payload.get("id")
        user = await user_auth_service.get_user_by_id(user_id, session)
        if not user:
            logger.warning(f"User not found for ID in refresh token: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail={
                    "status": "error",
                    "message": "User not found",
                    "action": "Please log in again."
                }
            )
        
        await user_auth_service.validate_user_status(user)

        # Create a new access token
        new_access_token = create_jwt_token(user.id)

        set_auth_cookies(response, new_access_token)

        logger.info(f"Successfully refreshed access token for user: {user.email}")

        return {
            "message": "Access token refreshed successfully.",
            "user": {
                "first_name": user.first_name,
                "last_name": user.last_name,
                "full_name": user.full_name,
                "username": user.username,
                "email": user.email,
                "id_no": user.id_no,
                "role": user.role
            }
        }
    
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    except Exception as e:
        logger.error(f"Failed to refresh access token: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail={
                "status": "error",
                "message": "Failed to refresh access token.",
                "action": "Please try again later."
            }
        )

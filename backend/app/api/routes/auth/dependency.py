import jwt
from fastapi import Depends, Cookie, HTTPException, status
from typing import Annotated
from sqlmodel.ext.asyncio.session import AsyncSession
from backend.app.core.config import settings
from backend.app.auth.models import User
from backend.app.core.db import get_session
from backend.app.core.logging import get_logger

logger = get_logger()

async def get_current_user(
    session: AsyncSession = Depends(get_session),
    access_token: str | None = Cookie(None, alias=settings.COOKIE_ACCESS_NAME),
) -> User:

    if not access_token:
        logger.warning("Authentication token is missing in cookies.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "status": "error",
                "message": "Authentication token is missing.",
                "action": "Plese login to continue.",
            },
        )
    try:
        payload = jwt.decode(
            access_token,
            settings.SIGNING_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )

        if payload.get("type") != settings.COOKIE_ACCESS_NAME:
            logger.warning("Invalid token type in payload.")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "status": "error",
                    "message": "Invalid token type.",
                },
            )
        
        from backend.app.api.services.user_auth import user_auth_service

        user = await user_auth_service.get_user_by_id(payload.get("id"), session)

        if user is None:
            logger.warning("User ID not found in token payload.")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "status": "error",
                    "message": "User not found."
                },
            )
        
        await user_auth_service.validate_user_status(user)

        return user
    
    except jwt.PyJWTError as e:
        logger.error(f"Error decoding JWT token: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "status": "error",
                "message": "Could not validate credentials."
            },
        )
    except jwt.ExpiredSignatureError:
        logger.warning("JWT token has expired.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "status": "error",
                "message": "Token has expired.",
                "action": "Please login again.",
            },
        )
    except jwt.InvalidTokenError:
        logger.warning("Invalid JWT token.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "status": "error",
                "message": "Invalid token.",
                "action": "Please login again.",
            },
        )
    except Exception as e:
        logger.error(f"Unexpected error during token validation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": "error",
                "message": "Authentication failed.",
                "action": "Please try again later.",
            },
        )
    

CurrentUser = Annotated[User, Depends(get_current_user)]

    
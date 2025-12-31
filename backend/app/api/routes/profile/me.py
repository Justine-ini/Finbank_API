from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession
from backend.app.api.routes.auth.dependency import CurrentUser
from backend.app.core.logging import get_logger
from backend.app.user_profile.schema import ProfileResponseSchema
from backend.app.api.services.profile import get_user_with_profile
from backend.app.core.db import get_session

logger = get_logger()

router = APIRouter(prefix="/profile")

@router.get("/me", response_model=ProfileResponseSchema, status_code=status.HTTP_200_OK)
async def get_my_profile(
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session)
) -> ProfileResponseSchema:
    try:
        user_with_profile = await get_user_with_profile(current_user.id, session)

        if not user_with_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                details={
                    "status":"error",
                    "message":"User not found",
                    "action":"Please try again or contact support"
                }
            )
        response = ProfileResponseSchema(
            username=user_with_profile.username or "",
            first_name=user_with_profile.first_name or "",
            middle_name=user_with_profile.middle_name or "",
            last_name=user_with_profile.last_name or "",
            email=user_with_profile.email or "",
            id_no=str(user_with_profile.id_no) if user_with_profile.id_no else "",
            role=user_with_profile.role,
            profile=user_with_profile.profile,
        )
        logger.debug(f"Successfully fetched profile for user {user_with_profile.id}")
        return response
    except HTTPException as httpex:
        raise httpex
    
    except Exception as e:
        logger.error(f"Unexpected error getting profile: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status":"error",
                "message":f"Failed to fetch user profile: {str(e)}",
                "action":"Please try again later"
            }
        )
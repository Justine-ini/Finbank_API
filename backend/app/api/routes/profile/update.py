from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession
from backend.app.core.logging import get_logger
from backend.app.user_profile.schema import ProfileUpdateSchema
from backend.app.user_profile.models import Profile
from backend.app.api.routes.auth.dependency import CurrentUser
from backend.app.core.db import get_session
from backend.app.api.services.profile import update_user_profile

logger = get_logger()

router = APIRouter(prefix="/profile", tags=["Profile"])
@router.patch("/update", response_model=Profile, status_code=status.HTTP_200_OK)
async def update_profile(
    profile_data: ProfileUpdateSchema,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
) -> Profile:

    try:
        updated_profile = await update_user_profile(
            user_id=current_user.id,
            profile_data=profile_data,
            session=session,
        )
        logger.info(f"Profile updated successfully for user {current_user.id}")

        return updated_profile
    
    except HTTPException as http_exc:
        raise http_exc
    
    except Exception as e:
        logger.error(f"Failed to update profile for user {current_user.email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": "error",
                "message": "Failed to update user profile.",
                "action": "Please try again later.",
            },
        )
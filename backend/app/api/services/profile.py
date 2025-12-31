import uuid
from backend.app.user_profile.models import Profile
from fastapi import HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from backend.app.user_profile.schema import ProfileCreateSchema, ProfileUpdateSchema, ImageTypeSchema
from backend.app.core.tasks.image_upload import upload_profile_image_task
from backend.app.auth.models import User
from backend.app.core.logging import get_logger

logger = get_logger()

async def get_user_profile(
    user_id: uuid.UUID, 
    session: AsyncSession
) -> Profile | None:
    """Get a user profile by user_id.

    Raises:
        HTTPException: If the profile is not found.
    """
    try:
        statement = select(Profile).where(Profile.user_id == user_id)
        result = await session.exec(statement)
        profile = result.first()
        return profile
    except Exception as e:
        logger.error(f"Error retrieving profile for user_id {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": "error",
                "message": "Failed to fetch user profile."
            },
        )
    
async def create_user_profile(
    user_id:uuid.UUID, 
    profile_data: ProfileCreateSchema,
    session: AsyncSession
) -> Profile:
    try:
        existing_profile = await get_user_profile(user_id, session)
        if existing_profile:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "status": "error",
                    "message": "Profile already exists for this user."
                },
            )
        profile_data_dict = profile_data.model_dump()
        new_profile = Profile(
            user_id=user_id,
            **profile_data_dict
        )

        session.add(new_profile)
        await session.commit()
        await session.refresh(new_profile)

        logger.info(f"Created new profile for user_id {user_id}")

        return new_profile

    except HTTPException as http_ex:
        raise http_ex

    except Exception as e:
        logger.error(f"Error creating profile for user_id {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": "error",
                "message": "Failed to verify existing profile."
            },
        )


async def update_user_profile(
        user_id: uuid.UUID, profile_data: ProfileUpdateSchema, session: AsyncSession
) -> Profile:
    try:
        profile = await get_user_profile(user_id, session)
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "status": "error",
                    "message": "Profile not found.",
                    "action": "Please create a profile first."
                },
            )
        update_data = profile_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if field not in ["profile_photo_url", "id_photo_url", "signature_photo_url"]:
                setattr(profile, field, value)

        await session.commit()
        await session.refresh(profile)

        logger.info(f"Updated profile for user_id {user_id}")

        return profile
    
    except HTTPException as http_ex:
        raise http_ex

    except Exception as e:
        logger.error(f"Error updating profile for user_id {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": "error",
                "message": "Failed to update user profile."
            },
        )

async def initiate_image_upload(
    file_content: bytes,
    image_type: ImageTypeSchema,
    content_type: str,
    user_id: uuid.UUID,
) -> str:
    
    try:
        task = upload_profile_image_task.delay(
            file_content, 
            image_type.value,
            str(user_id),
            content_type
        )
        return task.id
    except Exception as e:
        logger.error(f"Failed to initiate image upload task for user {user_id}, type {image_type.value}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": "error",
                "message": "Failed to initiate image upload."
            }
        )
    
async def update_profile_image_url(
    user_id: uuid.UUID,
    image_type: ImageTypeSchema,
    image_url: str,
    session: AsyncSession
) -> Profile:
    try:
        profile = await get_user_profile(user_id, session)
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "status": "error",
                    "message": "Profile not found.",
                    "action": "Please create a profile first."
                },
            )

        field_mapping = {
            ImageTypeSchema.PROFILE_PHOTO: "profile_photo_url",
            ImageTypeSchema.ID_PHOTO: "id_photo_url",
            ImageTypeSchema.SIGNATURE_PHOTO: "signature_photo_url",
        }

        field_name = field_mapping.get(image_type)
        if not field_name:
            raise ValueError(f"Invalid image type: {image_type}")
        setattr(profile, field_name, image_url)

        await session.commit()
        await session.refresh(profile)

        logger.info(f"Updated {image_type.value} URL for user_id {user_id}")

        return profile

    except HTTPException as http_ex:
        raise http_ex

    except Exception as e:
        logger.error(f"Error updating profile image {image_type.value} URL for user_id {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": "error",
                "message": f"Failed to update profile {image_type.value} URL."
            },
        )
  

async def get_user_with_profile(
        user_id: uuid.UUID,
        session: AsyncSession
) -> User:
    try:
        statement = select(User).where(User.id==user_id)
        result = await session.exec(statement)
        user = result.first()

        if user:
            await session.refresh(user, ["profile"])
            return user
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "status":"error",
                    "message": "User not found"
                }
            )
    except Exception as e:
        logger.error(f"Error fetching user with profile: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "status":"error",
                    "message": "Failed to fetch user with profile"
                }
        )
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession
from backend.app.core.logging import get_logger
from backend.app.next_of_kin.schema import NextOfKinUpdateSchema, NextOfKinReadSchema
from backend.app.api.routes.auth.dependency import CurrentUser
from backend.app.core.db import get_session
from backend.app.api.services.next_of_kin import update_next_of_kin

logger = get_logger()

router = APIRouter(prefix="/next-of-kin", tags=["Next of Kin"])
@router.patch(
    "/{next_of_kin_id}", 
    response_model=NextOfKinReadSchema, status_code=status.HTTP_201_CREATED,
    description="Update next of kin. only provided fields will be updated"
)
async def update_next_of_kin_route(
    update_data: NextOfKinUpdateSchema,
    next_of_kin_id: UUID,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
) -> NextOfKinReadSchema:

    try:
        next_of_kin = await update_next_of_kin(
            user_id=current_user.id,
            next_of_kin_id=next_of_kin_id,
            update_data=update_data,
            session=session
        )
    
        logger.info(f"User {current_user.email} updated next of kin: {next_of_kin_id}")

        return NextOfKinReadSchema.model_validate(next_of_kin)
    
    except HTTPException as http_ex:
        logger.warning(f"Next of kin update failed for user {current_user.email}: {http_ex.detail}")
        raise http_ex
    
    except Exception as e:
        logger.error(f"Failed to update next of kin: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": "error",
                "message": "Failed to update next of kin.",
                "action": "Please try again later.",
            },
        )
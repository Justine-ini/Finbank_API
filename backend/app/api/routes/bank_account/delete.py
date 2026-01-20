from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession
from backend.app.core.logging import get_logger
from backend.app.api.routes.auth.dependency import CurrentUser
from backend.app.core.db import get_session
from backend.app.api.services.bank_account import delete_bank_account

logger = get_logger()

router = APIRouter(prefix="/bank-account", tags=["Bank Account"])
@router.delete(
    "/{bank_account_id}", 
    status_code=status.HTTP_204_NO_CONTENT,
    description="Delete a bank account. Cannot delete if its the only one remaining"
)
async def delete_bank_account_route(
    bank_account_id: UUID,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
) -> None:

    try:
        await delete_bank_account(
            user_id=current_user.id,
            bank_account_id=bank_account_id,
            session=session
        )
        logger.info(f"Bank account has been deleted successfully for user {current_user.email}")
    
    except HTTPException as http_ex:
        logger.warning(f"Failed to delete bank account for user {current_user.email}: {http_ex.detail}")
        raise http_ex
    
    except Exception as e:
        logger.error(f"Failed to delete bank account: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": "error",
                "message": "Failed to delete bank account.",
                "action": "Please try again later.",
            },
        )
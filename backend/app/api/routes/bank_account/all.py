from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession
from backend.app.core.logging import get_logger
from backend.app.api.routes.auth.dependency import CurrentUser
from backend.app.core.db import get_session
from backend.app.bank_account.schema import BankAccountReadSchema
from backend.app.api.services.bank_account import get_user_bank_accounts

logger = get_logger()

router = APIRouter(prefix="/bank-accounts", tags=["Bank Account"])
@router.get(
    "/",
    response_model=list[BankAccountReadSchema],
    status_code=status.HTTP_200_OK,
    description="Retrieve all bank accounts associated with the current user.",
)
async def get_bank_accounts_route(
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
) -> list[BankAccountReadSchema]:

    try:
        bank_accounts = await get_user_bank_accounts(
            user_id=current_user.id,
            session=session
        )
        logger.info(f"Successfully retrieved bank accounts for user {current_user.email}")
        return [BankAccountReadSchema.model_validate(account) for account in bank_accounts]
    
    except HTTPException as http_ex:
        logger.warning(f"Failed to retrieve bank accounts for user {current_user.email}: {http_ex.detail}")
        raise http_ex
    
    except Exception as e:
        logger.error(f"Error retrieving bank accounts for user {current_user.email}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": "error",
                "message": "Failed to retrieve bank accounts.",
                "action": "Please try again later.",
            },
        )
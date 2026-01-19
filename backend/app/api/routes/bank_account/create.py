from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession
from backend.app.core.logging import get_logger
from backend.app.bank_account.schema import BankAccountCreateSchema, BankAccountReadSchema
from backend.app.api.routes.auth.dependency import CurrentUser
from backend.app.core.services.bank_account_created_email import send_account_created_email
from backend.app.core.db import get_session
from backend.app.api.services.bank_account import create_bank_account

logger = get_logger()

router = APIRouter(prefix="/bank-account", tags=["Bank Account"])
@router.post(
    "/create", 
    response_model=BankAccountReadSchema, status_code=status.HTTP_201_CREATED,
    description="Create a new bank account requires a completed user profile and least one next of ki. Maximum one primary account and 3 accounts per user."
)
async def create_bank_account_route(
    bank_account_data: BankAccountCreateSchema,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
) -> BankAccountReadSchema:

    try:
        bank_account = await create_bank_account(
            user_id=current_user.id,
            bank_account_data=bank_account_data,
            session=session
        )
        try:
            if not bank_account.account_number:
                logger.error(f"Account number missing for bank account ID: {bank_account.id}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail={
                        "status": "error",
                        "message": "Failed to generate account number."
                    },
                )
            await send_account_created_email(
                email_to=current_user.email, 
                fullname=current_user.full_name,
                account_number=bank_account.account_number,
                account_type=bank_account.account_type,
                account_name=bank_account.account_name,
                currency=bank_account.currency.value,
                identification_type=current_user.profile.means_of_identification.value
                )
        except Exception as email_ex:
            logger.error(f"Failed to send account created email to {current_user.email}: {str(email_ex)}")
        
        logger.info(f"Bank account created successfully for user {current_user.email}")

        return BankAccountReadSchema.model_validate(bank_account)
    
    except HTTPException as http_ex:
        logger.warning(f"Bank account creation failed for user {current_user.email}: {http_ex.detail}")
        raise http_ex
    
    except Exception as e:
        logger.error(f"Failed to create account: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": "error",
                "message": "Failed to create bank account.",
                "action": "Please try again later.",
            },
        )
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession
from backend.app.core.logging import get_logger
from backend.app.api.routes.auth.dependency import CurrentUser
from backend.app.core.db import get_session
from backend.app.bank_account.schema import BankAccountReadSchema
from backend.app.core.services.bank_account_activated_email import send_account_activated_email
from backend.app.api.services.bank_account import activate_bank_account
from backend.app.auth.schema import RoleChoicesSchema

logger = get_logger()

router = APIRouter(prefix="/bank-account", tags=["Bank Account"])
@router.patch(
    "/{account_id}/activate",
    response_model=BankAccountReadSchema,
    status_code=status.HTTP_200_OK,
    description="Activate a specific bank account after KYC verification, only account executives can perform this action.",
)

async def activate_bank_account_route(
    account_id: UUID,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
) -> BankAccountReadSchema:
    try:
        if not current_user.role == RoleChoicesSchema.ACCOUNT_EXECUTIVE:
            logger.warning(f"Unauthorized activation attempt by user {current_user.email}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "status": "error",
                    "message": "You do not have permission to activate bank accounts."
                }
            )
        
        activated_account, account_owner = await activate_bank_account(
            account_id=account_id,
            verified_by=current_user.id,
            session=session
        )

        try:
            if not activated_account.account_number:
                logger.error(f"Account number missing for activated bank account ID: {activated_account.id}")
                raise HTTPException(
                    status_code=status.HTTP_400_INTERNAL_SERVER_ERROR,
                    detail={
                        "status": "error",
                        "message": "Account number not found for the activated bank account."
                    },
                )
            
            await send_account_activated_email(
                email=account_owner.email,
                full_name=account_owner.full_name,
                account_number=activated_account.account_number,
                account_type=activated_account.account_type.value,
                account_name=activated_account.account_name,
                account_currency=activated_account.account_currency.value
            )
            logger.info(f"Account activated email sent to {account_owner.email} for account ID: {activated_account.id}")
        except Exception as email_ex:
            logger.error(f"Failed to send account activated email to {account_owner.email}: {str(email_ex)}")


        logger.info(f"Bank account {account_id} activated successfully by account executive: {current_user.email} for user {account_owner.email}")

        return BankAccountReadSchema.model_validate(activated_account)

    except HTTPException as http_ex:
        logger.warning(f"Bank account activation failed for user {current_user.email}: {http_ex.detail}")
        raise http_ex

    except Exception as e:
        logger.error(f"Failed to activate bank account for user {current_user.email}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": "error",
                "message": "Failed to activate bank account."
            }
        )

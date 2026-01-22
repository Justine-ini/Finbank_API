from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession
from backend.app.core.logging import get_logger
from backend.app.transaction.schema import DepositRequestSchema, TransactionReadSchema
from backend.app.transaction.enums import TransactionTypeEnum
from backend.app.auth.schema import RoleChoicesSchema
from backend.app.api.routes.auth.dependency import CurrentUser
from backend.app.core.db import get_session
from backend.app.api.services.transaction import process_deposit
from backend.app.core.services.deposit_alert import send_deposit_alert_email

logger = get_logger()

router = APIRouter(prefix="/bank-account", tags=["Bank Account"])
@router.post(
    "/deposit", 
    response_model=dict,status_code=status.HTTP_201_CREATED,
    description="Deposit funds into a bank account. Only tellers are authorized to perform this action."
)
async def create_deposit(
    deposit_data: DepositRequestSchema,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
):

    try:
        if current_user.role != RoleChoicesSchema.TELLER:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "status": "error",
                    "message": "You are not authorized to perform this action, Only tellers are authorized.",
                },
            )
        new_transaction, updated_account, account_owner = await process_deposit(
            amount=deposit_data.amount,
            account_id=deposit_data.account_id,
            teller_id=current_user.id,
            description=deposit_data.description,
            session=session
        )

        if not updated_account.account_number:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "status": "error",
                    "message": "Account number is required.",
                },
            )
        
        if new_transaction.transaction_type != TransactionTypeEnum.DEPOSIT:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "status": "error",
                    "message": "Transaction type mismatch.",
                },
            )
        
        try:
            currency_value = updated_account.account_currency.value

            await send_deposit_alert_email(
                email=account_owner.email,
                full_name=account_owner.full_name,
                amount=new_transaction.amount,
                action=TransactionTypeEnum.DEPOSIT.value,
                account_name=account_owner.full_name,
                currency=currency_value,
                account_number=updated_account.account_number,
                description=new_transaction.description,
                transaction_date=new_transaction.completed_at or new_transaction.created_at,
                reference=new_transaction.reference,
                balance=new_transaction.balance_after
            )
        except Exception as email_error:
            logger.error(f"Failed to send deposit alert email for transaction {new_transaction.id}: {email_error}")

        logger.info(f"Deposit of {new_transaction.amount} to account {updated_account.account_number} completed successfully.")

        return {
            "status": "success",
            "message": "Deposit processed successfully.",
            "data":{
                "transaction_id":new_transaction.id,
                "reference":new_transaction.reference,
                "amount":new_transaction.amount,
                "balance":new_transaction.balance_after,
                "status":new_transaction.status
            }
        }
    except HTTPException as http_ex:
        logger.warning(f"Deposit failed for account {deposit_data.account_id} by teller {current_user.email}: {http_ex.detail}")
        raise http_ex
    except Exception as e:
        logger.error(f"Failed to process deposit: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": "error",
                "message": "Failed to process deposit.",
                "action": "Please try again later.",
            },
        )


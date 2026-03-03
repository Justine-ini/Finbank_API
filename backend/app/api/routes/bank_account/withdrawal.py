from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlmodel.ext.asyncio.session import AsyncSession
from backend.app.core.db import get_session
from backend.app.core.logging import get_logger
from backend.app.api.routes.auth.dependency import CurrentUser
from sqlmodel import select
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from backend.app.transaction.schema import WithdrawRequestSchema
from backend.app.core.services.withdrawal_alert import send_withdrawal_alert_email
from backend.app.transaction.models import IdempotencyKey
from backend.app.api.services.transaction import process_withdrawal

logger = get_logger()

router = APIRouter(prefix="/bank-account", tags=["Bank Account"])

def validate_uuid4(value: str) -> str:
    try:
        uuid_obj = UUID(value, version=4)
        if str(uuid_obj) != value.lower():
            raise ValueError("Not a valid UUID v4")
        return value
    except (ValueError, AttributeError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "status": "error",
                "message": "Idempotency-key must be a valid UUID v4"
            }
        )
    
@router.post("/withdraw", status_code=status.HTTP_201_CREATED)
async def create_withdrawal(
    withdrawal_data: WithdrawRequestSchema,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
    idempotency_key: str = Header(
        description="Idempotency Key for the withdrawal request"
    ),
):
    try:
        idempotency_key = validate_uuid4(idempotency_key)

        if not idempotency_key:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "status": "error",
                    "message": "Idempotency-key header is required and must be a valid UUID v4"
                }
            )

        # Check for existing idempotency key
        existing_key_result = await session.execute(
            select(IdempotencyKey).where(
                IdempotencyKey.key == idempotency_key,
                IdempotencyKey.user_id == current_user.id,
                IdempotencyKey.endpoint == "/withdraw",
                IdempotencyKey.expires_at > datetime.now(timezone.utc)
                )
        )        
        existing_key = existing_key_result.first()

        if existing_key:
            return {
                "status": "success",
                "message": "Retrieved from cache",
                "data": existing_key.response_body
            }

        transaction, account, account_owner = await process_withdrawal(
            account_number=withdrawal_data.account_number, 
            amount=withdrawal_data.amount, 
            username=withdrawal_data.username, 
            description=withdrawal_data.description, 
            session=session
            )

        try:
        # Send withdrawal alert email
            await send_withdrawal_alert_email(
                email=account_owner.email,
                full_name=account_owner.full_name,
                amount=transaction.amount,
                account_name=account.account_name,
                account_number=account.account_number or "Unknown",
                currency=account.account_currency.value,
                description=transaction.description,
                transaction_date=transaction.completed_at or transaction.created_at,
                reference=transaction.reference,
                balance=Decimal(str(account.balance)),
            )
            logger.info(f"Withdrawal alert email sent to {account_owner.email} for transaction {transaction.id}")
        except Exception as e:
            logger.error(f"Failed to send withdrawal alert email: {str(e)}")

        response_data = {
            "status": "success",
            "message": "Withdrawal processed successfully",
            "data": {
                "transaction_id": str(transaction.id),
                "reference": transaction.reference,
                "amount": str(transaction.amount),
                "balance": str(transaction.balance_after),
                "status": transaction.status.value
            }
        }
        # Update idempotency key with response data
        idempotency_record = IdempotencyKey(
            key=idempotency_key,
            user_id=account_owner.id,
            endpoint="/withdraw",
            response_code=status.HTTP_201_CREATED,
            response_body=response_data,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=24)
        )
        session.add(idempotency_record)
        await session.commit()

        return response_data


    except HTTPException as e:
        logger.error(f"Withdrawal initiation failed: {e.detail}")
        raise e
    except Exception as e:
        logger.error(f"Failed to process withdrawal: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": "error",
                "message": "Failed to process withdrawal"
            }
        )

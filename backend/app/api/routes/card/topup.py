from uuid import UUID
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from backend.app.core.logging import get_logger
from backend.app.api.routes.auth.dependency import CurrentUser
from backend.app.core.db import get_session
from backend.app.api.services.card import top_up_virtual_card
from backend.app.transaction.models import IdempotencyKey
from backend.app.virtual_card.schema import TopUpResponseSchema, CardTopUpSchema


logger = get_logger()

router = APIRouter(prefix="/virtual-card", tags=["Cards"])



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

@router.post(
    "/{card_id}/top-up", response_model=TopUpResponseSchema,
    status_code=status.HTTP_200_OK,
    description="Top up the virtual card with a specified amount from a linked bank account"
)
async def top_up_card(
    card_id:UUID,
    top_up_data: CardTopUpSchema,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
    idempotency_key: str = Header(
        description="Idempotency Key for the top-up request"
    )
) -> TopUpResponseSchema:
    try:
        idempotency_key = validate_uuid4(idempotency_key)
        if not idempotency_key:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "status": "error",
                    "message": "Idempotency-key is required"
                }
            )
        existing_key = await session.exec(
            select(IdempotencyKey).where(
                IdempotencyKey.key == idempotency_key,
                IdempotencyKey.user_id == current_user.id,
                IdempotencyKey.endpoint == f"/virtual-card/{card_id}/top-up",
                IdempotencyKey.expires_at > datetime.now(timezone.utc)
            )
        )
        existing_key = existing_key.first()
        if existing_key:
            return TopUpResponseSchema(
                status="success",
                message="Retrieved from cache",
                data=existing_key.response_body
                )

        card, transaction = await top_up_virtual_card(
            card_id=card_id,
            account_number=top_up_data.account_number,
            amount=top_up_data.amount,
            description=top_up_data.description,
            session=session
        )
        response = TopUpResponseSchema(
            status="success",
            message="Card topped up successfully",
            data={
                "card_id": str(card.id),
                "transaction_id": str(transaction.id),
                "amount": float(transaction.amount),
                "new_balance": str(card.available_balance),
                "reference": transaction.reference,
            }
        )
        new_key = IdempotencyKey(
            key=idempotency_key,
            user_id=current_user.id,
            endpoint=f"/virtual-card/{card_id}/top-up",
            response_code=status.HTTP_200_OK,
            response_body=response.model_dump(),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=24)  # Set expiration time for the idempotency key
        )
        session.add(new_key)
        await session.commit()

        return response
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to top up virtual card: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": "error",
                "message": "Failed to top up virtual card"
            }
        )

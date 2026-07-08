from uuid import UUID
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession
from backend.app.core.logging import get_logger
from backend.app.api.routes.auth.dependency import CurrentUser
from backend.app.core.db import get_session
from backend.app.api.services.card import block_virtual_card
from backend.app.core.services.card_blocked import send_card_blocked_email
from backend.app.virtual_card.schema import CardBlockSchema


logger = get_logger()

router = APIRouter(prefix="/virtual-card", tags=["Cards"])

@router.post("/{card_id}/block", status_code=status.HTTP_200_OK, description="Block a virtual card, only account executives or card owners can block a card")
async def block_card(
    card_id: UUID,
    blocked_data: CardBlockSchema,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session)
):
    try:
        card, card_owner = await block_virtual_card(
            card_id=card_id,
            block_data=blocked_data.model_dump(),
            blocked_by=current_user.id, 
            session=session
            )
        try:
            await send_card_blocked_email(
                email=card_owner.email,
                full_name=card_owner.full_name, 
                card_type=card.card_type.value,
                masked_card_number=card.masked_card_number,
                blocked_reason=str(card.block_reason.value) if card.block_reason else "",
                blocked_reason_details=str(card.block_reason_details) if card.block_reason_details else "",
                blocked_at=card.blocked_at or datetime.now(timezone.utc)
            )
        except Exception as email_error:
            logger.error(f"Failed to send card blocked email: {email_error}")
        return {
            "status": "success",
            "message": "Card blocked successfully",
            "data": {
                "card_id": str(card.id),
                "status": card.card_status.value,
                "blocked_reason": str(card.block_reason.value) if card.block_reason else "",
                "blocked_at":(
                    card.blocked_at.isoformat() if card.blocked_at else None
                )
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to block virtual card: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": "error",
                "message": "Failed to block virtual card",
                "error": str(e)
            }
        )

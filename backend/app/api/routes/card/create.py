from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession
from backend.app.core.logging import get_logger
from backend.app.api.routes.auth.dependency import CurrentUser
from backend.app.core.db import get_session
from backend.app.api.services.card import create_virtual_card
from backend.app.core.services.card_created import send_card_created_email
from backend.app.virtual_card.schema import VirtualCardCreateSchema, VirtualCardReadSchema


logger = get_logger()

router = APIRouter(prefix="/virtual-card", tags=["Cards"])
@router.post(
    "/create",
    response_model=VirtualCardReadSchema,
    status_code=status.HTTP_201_CREATED, 
    description="Create a virtual card, card will be in pending status until activated by an account executive")
async def create_card(
    card_data: VirtualCardCreateSchema,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session)
) -> VirtualCardReadSchema:
    try:
        card, user, bank_account = await create_virtual_card(
            user_id=current_user.id, 
            bank_account_id=card_data.bank_account_id, 
            card_data=card_data.model_dump(exclude={"bank_account_id"}), 
            session=session
        )
        try:
            await send_card_created_email(
                email=user.email,
                full_name=user.full_name, 
                card_type=card.card_type.value,
                currency=card.currency.value,
                masked_card_number=card.masked_card_number,
                name_on_card=card.cardholder_name,
                daily_limit=card.daily_spending_limit,
                monthly_limit=card.monthly_spending_limit,
                expiry_date=card.expiry_date.strftime("%m/%y"),
            )
        except Exception as email_error:
            logger.error(f"Failed to send card created email: {email_error}")
        return VirtualCardReadSchema.model_validate(card)
    
    except HTTPException:
        raise
    except HTTPException as e:
        logger.error(f"Failed to create virtual card: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": "error",
                "message": "Failed to create virtual card"
            }
        )

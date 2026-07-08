from datetime import datetime, timezone
from uuid import UUID
import uuid
from fastapi import HTTPException, status
from sqlmodel import select
from decimal import Decimal
from sqlmodel.ext.asyncio.session import AsyncSession
from backend.app.virtual_card.models import VirtualCard
from backend.app.bank_account.models import BankAccount
from backend.app.auth.models import User
from backend.app.transaction.models import Transaction
from backend.app.transaction.enums import (
    TransactionTypeEnum,
    TransactionCategoryEnum,
    TransactionStatusEnum
)
from backend.app.virtual_card.enums import VirtualCardStatusEnum, VirtualCardProviderEnum
from backend.app.bank_account.enums import AccountStatusEnum
from backend.app.auth.schema import RoleChoicesSchema
from backend.app.virtual_card.utils import (
    generate_card_for_provider,
    generate_cvv,
    generate_expiry_date
)
from backend.app.core.logging import get_logger

logger = get_logger()

async def create_virtual_card(
    user_id: UUID,
    bank_account_id: UUID,
    card_data: dict,
    session: AsyncSession
) -> tuple[VirtualCard, User, BankAccount]:
    
    try:
        statement = (
            select(BankAccount, User)
            .join(User)
            .where(BankAccount.id == bank_account_id, BankAccount.user_id == user_id)
        )
        result = await session.exec(statement)
        account_user = result.first()

        if not account_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail= {
                    "status": "error",
                    "message": "Bank account not found or does not belong to the user"
                }
            )
        bank_account, user = account_user

        if bank_account.account_status != AccountStatusEnum.Active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail= {
                    "status": "error",
                    "message": "Bank account is not active"
                }
            )
        
        card_currency = card_data.get("currency")

        if card_currency != bank_account.account_currency:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail= {
                    "status": "error",
                    "message": "Card currency must match bank account currency"
                }
            )
        
        cleaned_data = card_data.copy()
        # Keep currency because the virtual card table requires it when saving the card.
        cleaned_data.pop("card_status", None)  # Remove card_status as it's not needed for card creation
        cleaned_data.pop("is_active", None)  # Remove is_active as it's not needed for card creation
        cleaned_data.pop("cvv_hash", None)  # Remove cvv_hash as it's not needed for card creation
        cleaned_data.pop("available_balance", None)  # Remove available_balance as it's not needed for card creation
        cleaned_data.pop("total_topped_amount", None)  # Remove total_topped_amount as it's not needed for card creation
        cleaned_data.pop("card_metadata", None)  # Remove card_metadata as it's not needed for card creation
        cleaned_data.pop("card_number", None)  # Remove client-provided card_number so the system-generated value is used

        provider = cleaned_data.get("card_provider")
        # Normalize provider strings like "Visa" into the enum expected by card generation.
        try:
            provider = (
                provider
                if isinstance(provider, VirtualCardProviderEnum)
                else VirtualCardProviderEnum(provider)
            )
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail= {
                    "status": "error",
                    "message": "Invalid card provider"
                }
            )
        cleaned_data["card_provider"] = provider


        try:
            card_number = generate_card_for_provider(cleaned_data["card_provider"])

            if not cleaned_data.get("expiry_date"):
                expiry_date = generate_expiry_date()
                cleaned_data["expiry_date"] = expiry_date.date()
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail=str(e)
            ) from e
        
        card = VirtualCard(
            **cleaned_data,
            card_number=card_number,
            bank_account_id=bank_account_id,
            card_status=VirtualCardStatusEnum.PENDING,
            is_active=True,
            available_balance=0.0,
            total_topped_amount=0.0,
            last_transaction_amount=0.0,  # Initialize new cards with no transaction amount yet
            last_topped_at=datetime.now(timezone.utc),
            card_metadata={
                "created_by": str(user_id),
                "created_at": datetime.now(timezone.utc).isoformat(),
                }
        )

        session.add(card)
        await session.commit()
        await session.refresh(card)

        logger.info(
            "Virtual card created successfully. card_id=%s user_id=%s bank_account_id=%s",
            card.id,
            user_id,
            bank_account_id,
        )

        return card, user, bank_account
    
    except HTTPException:
        await session.rollback()
        raise
        
    except Exception as e:
        await session.rollback()
        logger.error(f"failed to create virtual card for user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": "error",
                "message": "Failed to create virtual card"
            }
        ) from e

async def block_virtual_card(
    card_id: UUID,
    block_data: dict,
    blocked_by: UUID,
    session: AsyncSession
) -> tuple[VirtualCard, User]:
    try:
    
        statement = (
            select(VirtualCard, User)
            .select_from(VirtualCard)
            .join(BankAccount)
            .join(User)
            .where(VirtualCard.id == card_id)
        )
        result = await session.exec(statement)
        card_data = result.first()

        if not card_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail= {
                    "status": "error",
                    "message": "Virtual card not found or does not belong to the user"
                }
            )
        card, card_owner = card_data
        
        if card.card_status == VirtualCardStatusEnum.BLOCKED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail= {
                    "status": "error",
                    "message": "Virtual card is already blocked"
                }
            )
        block_time = datetime.now(timezone.utc)
        
        card.card_status = VirtualCardStatusEnum.BLOCKED
        card.block_reason = block_data.get("block_reason")
        card.block_reason_details = block_data.get("block_reason_details")
        card.blocked_by = blocked_by
        card.blocked_at = block_time

        existing_metadata = card.card_metadata or {}
        card.card_metadata = {
            **existing_metadata,
            "blocked_by": str(blocked_by),
            "blocked_at": block_time.isoformat(),
            "block_reason": block_data["block_reason"].value,
        }

        session.add(card)
        await session.commit()
        await session.refresh(card)

        logger.info(
            "Virtual card blocked successfully. card_id=%s user_id=%s block_reason=%s",
            card.id,
            card_owner.id,
            block_data["block_reason"].value
        )

        return card, card_owner
    
    except HTTPException:
        await session.rollback()
        raise

    except Exception as e:
        await session.rollback()
        logger.error(f"failed to block virtual card {card_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": "error",
                "message": "Failed to block virtual card"
            }
        ) from e
   
async def top_up_virtual_card(
    card_id: UUID,
    account_number: str,
    amount: float,
    description: str,
    session: AsyncSession
) -> tuple[VirtualCard, Transaction]:
    try:
        statement = select(VirtualCard, BankAccount).join(BankAccount).where(VirtualCard.id == card_id, BankAccount.account_number == account_number)
        
        result = await session.exec(statement)
        card_account = result.first()

        if not card_account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail= {
                    "status": "error",
                    "message": "Virtual card or bank account not found"
                }
            )
        
        card, bank_account = card_account
        
        if card.card_status != VirtualCardStatusEnum.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail= {
                    "status": "error",
                    "message": "Only active cards can be topped up"
                }
            )
        
        if bank_account.account_status != AccountStatusEnum.Active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail= {
                    "status": "error",
                    "message": "Bank account must be active to top up card"
                }
            )
              
        if Decimal(str(bank_account.balance)) < Decimal(str(amount)):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail= {
                    "status": "error",
                    "message": "Insufficient funds in the bank account"
                }
            )
        
        if card.currency != bank_account.account_currency:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail= {
                    "status": "error",
                    "message": "Currency mismatch between card and bank account"
                }
            )
        
        reference = f"TOPUP{uuid.uuid4().hex[:8].upper()}"

        balance_before = Decimal(str(bank_account.balance))
        balance_after = balance_before - Decimal(str(amount))
        current_time = datetime.now(timezone.utc)
        transaction = Transaction(
            amount=Decimal(str(amount)),
            description=description,
            reference=reference,
            transaction_type=TransactionTypeEnum.TRANSFER,
            transaction_category=TransactionCategoryEnum.DEBIT,
            status=TransactionStatusEnum.COMPLETED,
            balance_before=balance_before,
            balance_after=balance_after,
            sender_account_id=bank_account.id,
            sender_id=bank_account.user_id,
            completed_at=current_time,
            transaction_metadata={
                "top_up_type": "virtual_card",
                "card_id": str(card.id),
                "card_last_four": card.last_four_digits,
                "currency": card.currency.value,
            }
        )

        bank_account.balance = float(balance_after)

        card.available_balance += amount
        card.total_topped_amount += amount
        card.last_topped_at = current_time

        session.add(card)
        session.add(transaction)
        session.add(bank_account)

        await session.commit()
        await session.refresh(card)
        await session.refresh(transaction)

        logger.info(
            "Virtual card topped up successfully. card_id=%s amount=%.2f new_balance=%.2f",
            card.id,
            amount,
            card.available_balance
        )

        return card, transaction
    
    except HTTPException:
        await session.rollback()
        raise

    except Exception as e:
        await session.rollback()
        logger.error(f"failed to top up virtual card {card_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": "error",
                "message": "Failed to top up virtual card"
            }
        ) from e

async def activate_virtual_card(
    card_id: UUID,
    activated_by: UUID,
    session: AsyncSession
) -> tuple[VirtualCard, User, str]:
    try:
        statement = select(VirtualCard,BankAccount, User).select_from(VirtualCard).join(BankAccount).join(User).where(VirtualCard.id == card_id)
        result = await session.exec(statement)
        card_data = result.first()

        if not card_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail= {
                    "status": "error",
                    "message": "Virtual card not found"
                }
            )

        card, bank_account, card_owner = card_data

        if card.card_status == VirtualCardStatusEnum.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail= {
                    "status": "error",
                    "message": "Virtual card is already active"
                }
            )

        executive = await session.get(User, activated_by)  
        if not executive or executive.role != RoleChoicesSchema.ACCOUNT_EXECUTIVE:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail= {
                    "status": "error",
                    "message": "Only executives can activate virtual cards"
                }
            )
        new_cvv, cvv_hash = generate_cvv()
        card.card_status = VirtualCardStatusEnum.ACTIVE
        card.cvv_hash = cvv_hash

        existing_metadata = card.card_metadata or {}
        card.card_metadata = {
            **existing_metadata,
            "activated_by": str(activated_by),
            "activated_at": datetime.now(timezone.utc).isoformat(),
        }

        session.add(card)
        await session.commit()
        await session.refresh(card)

        logger.info(
            "Virtual card activated successfully. card_id=%s",
            card.id,
        )

        return card, card_owner, new_cvv
    
    except HTTPException:
        await session.rollback()
        raise

    except Exception as e:
        await session.rollback()
        logger.error(f"failed to activate virtual card {card_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": "error",
                "message": "Failed to activate virtual card"
            }
        ) from e
    
async def delete_virtual_card(
    card_id: UUID,
    user_id: UUID,
    session: AsyncSession
) -> dict:
    try:
        statement = select(VirtualCard, BankAccount).join(BankAccount).where(VirtualCard.id == card_id, BankAccount.user_id == user_id)
        result = await session.exec(statement)
        card_account = result.first()

        if not card_account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail= {
                    "status": "error",
                    "message": "Virtual card not found"
                }
            )
        
        card, _ = card_account

        if card.card_status != VirtualCardStatusEnum.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail= {
                    "status": "error",
                    "message": "Only active cards can be deleted"
                }
            )
        if card.physical_card_requested_at:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail= {
                    "status": "error",
                    "message": "Cannot delete card with pending physical card request"
                }
            )
        if card.available_balance > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail= {
                    "status": "error",
                    "message": "Cannot delete card with available balance greater than zero",
                    "action": "please transfer remaining balance to another account or spend it down to zero before deleting the card"
                }
            )
        
        deletion_time = datetime.now(timezone.utc)

        existing_metadata = card.card_metadata or {}
        new_metadata = {
            **existing_metadata,
            "deleted_at": deletion_time.isoformat(),
            "deleted_reason": "user_requested",
            "deleted_by": str(user_id),
            "card_status_before_deletion": card.card_status.value,
            "deletion_timestamp": deletion_time.timestamp(),
        }
        card.card_metadata = new_metadata
        card.card_status = VirtualCardStatusEnum.INACTIVE
        card.is_active = False

        session.add(card)
        await session.commit()
        await session.refresh(card)

        logger.info(
            "Virtual card soft deleted successfully. card_id=%s",
            card_id,
        )

        return {
            "status": "success",
            "message": "Virtual card deleted successfully",
            "deleted_at": deletion_time.isoformat()
        }

    except HTTPException:
        await session.rollback()
        raise

    except Exception as e:
        await session.rollback()
        logger.error(f"failed to delete virtual card {card_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": "error",
                "message": "Failed to delete virtual card"
            }
        ) from e

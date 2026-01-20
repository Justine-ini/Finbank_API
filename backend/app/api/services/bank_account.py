from uuid import UUID
from fastapi import HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from backend.app.bank_account.models import BankAccount
from backend.app.bank_account.schema import BankAccountCreateSchema, BankAccountReadSchema
from backend.app.bank_account.utils import generate_account_number
from backend.app.auth.models import User
from backend.app.core.logging import get_logger
from backend.app.core.config import settings


logger = get_logger()

async def get_primary_bank_account(user_id: UUID, session: AsyncSession) -> BankAccount | None:
    statement = select(BankAccount).where(
        BankAccount.user_id == user_id,
        BankAccount.is_primary)
    result = await session.exec(statement)
    return result.first()


async def validate_user_kyc(user: User) -> bool:
    if not user.profile:
        return False
    if not user.next_of_kins or len(user.next_of_kins) == 0:
        return False
    return True

async def create_bank_account(
        user_id: UUID,
        bank_account_data: BankAccountCreateSchema,
        session: AsyncSession
    ) -> BankAccount:
    
    try:
        statement = select(User).where(User.id == user_id)
        result = await session.exec(statement)
        user = result.first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "status":"error",
                    "message":"User not found."
                }
            )

        await session.refresh(user, ["profile", "next_of_kins"])

        is_kyc_completed = await validate_user_kyc(user)
        if not is_kyc_completed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "status":"error",
                    "message":"User KYC is incomplete.",
                    "action":"Please complete your profile and next of kin details."
                }
            )
        
        statement = select(BankAccount).where(BankAccount.user_id == user_id)
        result = await session.exec(statement)
        existing_accounts = result.all()

        if len(existing_accounts) >= settings.MAX_BANK_ACCOUNTS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "status":"error",
                    "message":"Maximum number of bank accounts reached."
                }
            )
        
        if bank_account_data.is_primary:
            existing_primary = any(account.is_primary for account in existing_accounts)

            if existing_primary:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "status":"error",
                        "message":"User already has a primary bank account."
                    }
                )
        elif len(existing_accounts) == 0:
                bank_account_data.is_primary = True
                

        account_number = generate_account_number(bank_account_data.account_currency)
        new_bank_account = BankAccount(
            **bank_account_data.model_dump(exclude={"account_number"}),
            user_id=user_id,
            account_number=account_number
        )
        session.add(new_bank_account)
        await session.commit()
        await session.refresh(new_bank_account)

        logger.info(f"Bank account {new_bank_account.account_number} created for user {user.email}")

        return new_bank_account
    
    except HTTPException as httpex:
        raise httpex
    except Exception as e:
        await session.rollback()
        logger.error(f"Failed to create bank account for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status":"error",
                "message":"An error occurred while creating the bank account."
            }
        )
    

async def update_bank_account_primary_status(
        user_id: UUID,
        bank_account_id: UUID,
        is_primary: bool,
        session: AsyncSession
    ) -> None:
    try:
        statement = select(BankAccount).where(
            BankAccount.id == bank_account_id,
            BankAccount.user_id == user_id
        )
        result = await session.exec(statement)
        bank_account = result.first()

        if not bank_account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "status":"error",
                    "message":"Bank account not found."
                }
            )

        if is_primary:
            statement = select(BankAccount).where(
                BankAccount.user_id == user_id,
                BankAccount.is_primary == True,
                BankAccount.id != bank_account_id
            )
            result = await session.exec(statement)
            existing_primary = result.first()

            if existing_primary:
                existing_primary.is_primary = False
                session.add(existing_primary)

        bank_account.is_primary = is_primary
        session.add(bank_account)
        await session.commit()

        logger.info(f"Bank account {bank_account.account_number} primary status updated for user ID {user_id}")

    except HTTPException as httpex:
        raise httpex
    except Exception as e:
        await session.rollback()
        logger.error(f"Failed to update primary status for bank account {bank_account_id} for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status":"error",
                "message":"An error occurred while updating the bank account."
            }
        )
    

async def delete_bank_account(
        user_id: UUID,
        bank_account_id: UUID,
        session: AsyncSession
    ) -> None:
    try:
        statement = select(BankAccount).where(
            BankAccount.id == bank_account_id,
            BankAccount.user_id == user_id
        )
        result = await session.exec(statement)
        bank_account = result.first()

        if not bank_account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "status":"error",
                    "message":"Bank account not found."
                }
            )

        statement = select(BankAccount).where(BankAccount.user_id == user_id)
        result = await session.exec(statement)
        user_accounts = result.all()

        if len(user_accounts) <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "status":"error",
                    "message":"Cannot delete the only bank account."
                }
            )


        await session.delete(bank_account)
        await session.commit()

        logger.info(f"Bank account {bank_account.account_number} deleted for user ID {user_id}")

    except HTTPException as httpex:
        raise httpex
    except Exception as e:
        await session.rollback()
        logger.error(f"Failed to delete bank account {bank_account_id} for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status":"error",
                "message":"An error occurred while deleting the bank account."
            }
        )
    
async def get_user_bank_accounts(
        user_id: UUID,
        session: AsyncSession
    ) -> list[BankAccount]:
    try:
        statement = select(BankAccount).where(BankAccount.user_id == user_id)
        result = await session.exec(statement)
        bank_accounts = result.all()

        logger.info(f"Fetched {len(bank_accounts)} bank accounts for user ID {user_id}")

        return [BankAccountReadSchema.model_validate(account) for account in bank_accounts]
    
    except HTTPException as httpex:
        raise httpex
    except Exception as e:
        logger.error(f"Error fetching bank accounts for user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status":"error",
                "message":"Failed to fetch user bank accounts",
                "action":"Please try again later"
            }
        )
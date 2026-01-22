import uuid
from decimal import Decimal
from datetime import datetime, timezone
from fastapi import HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from backend.app.bank_account.models import BankAccount
from backend.app.transaction.models import Transaction
from backend.app.transaction.enums import TransactionStatusEnum, TransactionTypeEnum, TransactionCategoryEnum
from backend.app.bank_account.enums import AccountStatusEnum
from backend.app.auth.models import User
from backend.app.core.logging import get_logger



logger = get_logger()

async def process_deposit(
        *,
        amount: Decimal,
        account_id: uuid.UUID,
        teller_id: uuid.UUID,
        description: str,
        session: AsyncSession
) -> tuple[Transaction, BankAccount, User]:
    try:
        statement = (
            select(BankAccount, User).join(User).where(BankAccount.id == account_id)
        )
        result = await session.exec(statement)
        bank_account_with_user = result.first()

        if not bank_account_with_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "status":"error",
                    "message":"Bank account not found."
                }
            )

        account, account_owner = bank_account_with_user

        if account.account_status != AccountStatusEnum.Active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "status":"error",
                    "message":"Cannot deposit to an inactive bank account."
                }
            )
        
        reference = f"DEP-{uuid.uuid4().hex[:8].upper()}"

        balance_before = Decimal(str(account.balance))
        balance_after = balance_before + amount

        new_transaction = Transaction(
            amount=amount,
            description=description,
            reference=reference,
            transaction_type=TransactionTypeEnum.DEPOSIT,
            transaction_category=TransactionCategoryEnum.CREDIT,
            status=TransactionStatusEnum.PENDING,
            balance_before=balance_before,
            balance_after=balance_after,
            receiver_account_id=account_id,
            receiver_id=account_owner.id,
            processed_by=teller_id,
            transaction_metadata={
                "currency": account.account_currency,
                "account_number": account.account_number,
            }
        )
        teller = await session.get(User, teller_id)

        if teller:
            if new_transaction.transaction_metadata is None:
                new_transaction.transaction_metadata = {}
            new_transaction.transaction_metadata["teller_name"] = teller.full_name

            new_transaction.transaction_metadata["teller_email"] = teller.email
        
        account.balance = float(balance_after)

        new_transaction.status = TransactionStatusEnum.COMPLETED
        new_transaction.completed_at = datetime.now(timezone.utc)

        session.add(new_transaction)
        session.add(account)
        await session.commit()
        await session.refresh(new_transaction)
        await session.refresh(account)

        logger.info(f"Deposit transaction {new_transaction.id} processed for account {account.account_number} by teller {teller_id}")

        return new_transaction, account, account_owner

    except HTTPException as httpex:
        await session.rollback()
        raise httpex
    except Exception as e:
        await session.rollback()
        logger.error(f"Failed to process deposit for account {account_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status":"error",
                "message":"Failed to process deposit."
            }
        )

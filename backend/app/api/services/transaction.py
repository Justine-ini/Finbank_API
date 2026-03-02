import uuid
from decimal import Decimal
from datetime import datetime, timezone, timedelta
from fastapi import HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from backend.app.bank_account.models import BankAccount
from backend.app.transaction.models import Transaction
from backend.app.transaction.enums import TransactionStatusEnum, TransactionTypeEnum, TransactionCategoryEnum
from backend.app.transaction.utils import TransactionFailureReasonEnum
from backend.app.auth.utils import generate_otp
from backend.app.core.config import settings
from backend.app.bank_account.utils import calculate_conversion
from backend.app.transaction.utils import mark_transaction_failed
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
            select(BankAccount, User).join(User).where(
                BankAccount.id == account_id)
        )
        result = await session.exec(statement)
        bank_account_with_user = result.first()

        if not bank_account_with_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "status": "error",
                    "message": "Bank account not found."
                }
            )

        account, account_owner = bank_account_with_user

        if account.account_status != AccountStatusEnum.Active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "status": "error",
                    "message": "Cannot deposit to an inactive bank account."
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

        logger.info(
            f"Deposit transaction {new_transaction.id} processed for account {account.account_number} by teller {teller_id}")

        return new_transaction, account, account_owner

    except HTTPException as httpex:
        await session.rollback()
        raise httpex
    except Exception as e:
        await session.rollback()
        logger.error(
            f"Failed to process deposit for account {account_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": "error",
                "message": "Failed to process deposit."
            }
        )


async def initiate_transfer(
        *,
        sender_id: uuid.UUID,
        sender_account_id: uuid.UUID,
        receiver_account_number: str,
        amount: Decimal,
        description: str,
        security_answer: str,
        session: AsyncSession
) -> tuple[Transaction, BankAccount, BankAccount, User, User]:
    try:
        receiver_account_result = await session.exec(
            select(BankAccount).where(BankAccount.account_number == receiver_account_number, BankAccount.user_id == sender_id)
        )
        receiver_account = receiver_account_result.first()

        # Blocks sender from send to self
        if receiver_account:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "status": "error",
                    "message": "Cannot transfer to your own account",
                    "action": "Please use a different recipient account"
                },
            )

        sender_statement = (
            select(BankAccount, User).join(User).where(
                BankAccount.id == sender_account_id, BankAccount.user_id == sender_id
            )
        )

        sender_result = await session.exec(sender_statement)
        sender_data = sender_result.first()

        # Validate sender is the owner of account
        if not sender_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "status": "error",
                    "message": "Sender account not found"
                }
            )

        sender_account, sender = sender_data

        # Validate sender account is active
        if sender_account.account_status != AccountStatusEnum.Active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "status": "error",
                    "message": "Sender account is not active"
                },
            )

        if security_answer != sender.security_answer:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "status": "error",
                    "message": "Incorrect security answer",
                    "action": "Please use a different recipient account"
                },
            )

        receiver_statement = (select(BankAccount, User).join(User).where(BankAccount.account_number == receiver_account_number)
                              )
        receiver_result = await session.exec(receiver_statement)
        receiver_data = receiver_result.first()

        if not receiver_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "status": "error",
                    "message": "Receiver account not found"
                }
            )

        receiver_account, receiver = receiver_data

        if receiver_account.account_status != AccountStatusEnum.Active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "status": "error",
                    "message": "Receiver account is not active"
                },
            )

        if Decimal(str(sender_account.balance)) < amount:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "status": "error",
                    "message": "Insufficient balance"
                },
            )

        try:
            if sender_account.account_currency != receiver_account.account_currency:
                converted_amount, exchange_rate, conversion_fee = calculate_conversion(
                    amount,
                    sender_account.account_currency,
                    receiver_account.account_currency
                )
            else:
                converted_amount = amount
                exchange_rate = Decimal("1.0")
                conversion_fee = Decimal("0")

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "status": "error",
                    "message": f"Currency conversion failed: {str(e)}"
                },
            )

        reference = f"TRF{uuid.uuid4().hex[:8].upper()}"

        transaction = Transaction(
            amount=amount,
            description=description,
            reference=reference,
            transaction_type=TransactionTypeEnum.TRANSFER,
            transaction_category=TransactionCategoryEnum.DEBIT,
            status=TransactionStatusEnum.PENDING,
            balance_before=Decimal(str(sender_account.balance)),
            balance_after=Decimal(str(sender_account.balance)) - amount,
            sender_account_id=sender_account.id,
            receiver_account_id=receiver_account.id,
            sender_id=sender.id,
            receiver_id=receiver.id,
            transaction_metadata={
                "conversion_rate": str(exchange_rate),
                "conversion_fee": str(conversion_fee),
                "original_amount": str(amount),
                "converted_amount": str(converted_amount),
                "from_currency": sender_account.account_currency.value,
                "to_currency": receiver_account.account_currency.value
            }
        )

        otp = generate_otp()
        sender.otp = otp
        sender.otp_expiry_time = datetime.now(
            timezone.utc) + timedelta(minutes=settings.OTP_EXPIRATION_MINUTES)

        session.add(transaction)
        # check y should i add sender
        session.add(sender)
        await session.commit()
        await session.refresh(transaction)

        return transaction, sender_account, receiver_account, sender, receiver
    except HTTPException:
        await session.rollback()
        raise
    except Exception as e:
        await session.rollback()
        logger.error(f"Failed to initiate transfer: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": "error",
                "message": "Failed to initiate transfer"
            }
        )


async def complete_transfer(
        *,
        reference: str,
        otp: str,
        session: AsyncSession
) -> tuple[Transaction, BankAccount, BankAccount, User, User]:
    try:
        statement = select(Transaction).where(Transaction.reference ==
                                              reference, Transaction.status == TransactionStatusEnum.PENDING)

        result = await session.exec(statement)
        transaction = result.first()

        if not transaction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "status": "error",
                    "message": "Transfer not found"
                }
            )

         # Get the SENDER'S account
        sender_account = await session.get(BankAccount, transaction.sender_account_id)

        # Get the RECEIVER'S account
        receiver_account = await session.get(BankAccount, transaction.receiver_account_id)

        sender = await session.get(User, transaction.sender_id)
        receiver = await session.get(User, transaction.receiver_id)

        if not all([sender_account, receiver_account, sender, receiver]):
            await mark_transaction_failed(
                transaction=transaction,
                reason=TransactionFailureReasonEnum.INVALID_ACCOUNT,
                details={
                    "sender_account_found": bool(sender_account),
                    "receiver_account_found": bool(receiver_account),
                    "sender_found": bool(sender),
                    "receiver_found": bool(receiver)
                },
                session=session,
                error_message="Account information not found"
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "status": "error",
                    "message": "Account information not found"
                }
            )

        if not sender or not sender.otp or sender.otp != otp:
            await mark_transaction_failed(
                transaction=transaction,
                reason=TransactionFailureReasonEnum.INVALID_OTP,
                details={
                    "provided_otp": otp,
                },
                session=session,
                error_message="Invalid OTP"
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "status": "error",
                    "message": "Invalid OTP"
                }
            )

        now = datetime.now(timezone.utc)
        if (not sender.otp_expiry_time or now > sender.otp_expiry_time):
            await mark_transaction_failed(
                transaction=transaction,
                reason=TransactionFailureReasonEnum.OTP_EXPIRED,
                details={
                    "expiry_time": (
                        sender.otp_expiry_time.isoformat() if sender.otp_expiry_time else None
                    ),
                    "current_time": now.isoformat()
                },
                session=session,
                error_message="OTP has expired"
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "status": "error",
                    "message": "OTP has expired"
                }
            )

        if sender_account and sender_account.account_status != AccountStatusEnum.Active:
            await mark_transaction_failed(
                transaction=transaction,
                reason=TransactionFailureReasonEnum.ACCOUNT_INACTIVE,
                details={"account": "sender"},
                session=session,
                error_message="Sender account is no longer active"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "status": "error",
                    "message": "Sender account is no longer active"
                }
            )

        if receiver_account and receiver_account.account_status != AccountStatusEnum.Active:
            await mark_transaction_failed(
                transaction=transaction,
                reason=TransactionFailureReasonEnum.ACCOUNT_INACTIVE,
                details={"account": "receiver"},
                session=session,
                error_message="Receiver account is no longer active"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "status": "error",
                    "message": "Receiver account is no longer active"
                }
            )
        if not sender_account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "status": "error",
                    "message": "Sender account not found"
                }
            )

        if Decimal(str(sender_account.balance)) < transaction.amount:
            await mark_transaction_failed(
                transaction=transaction,
                reason=TransactionFailureReasonEnum.INSUFFICIENT_FUNDS,
                details={"required_amount": str(transaction.amount),
                         "available_balance": str(sender_account.balance),
                         "shortfall": str(transaction.amount - Decimal(str(sender_account.balance)))
                         },
                session=session,
                error_message="Insufficient balance"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "status": "error",
                    "message": "Insufficient balance"
                }
            )

        if not transaction.transaction_metadata:
            await mark_transaction_failed(
                transaction=transaction,
                reason=TransactionFailureReasonEnum.SYSTEM_ERROR,
                details={"error": "Missing transaction metadata"},
                session=session,
                error_message="System error: Missing transaction metadata"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "status": "error",
                    "message": "System error: Missing transaction metadata"
                }
            )

        converted_amount_str = transaction.transaction_metadata.get(
            "converted_amount")
        if not converted_amount_str:
            await mark_transaction_failed(
                transaction=transaction,
                reason=TransactionFailureReasonEnum.SYSTEM_ERROR,
                details={"error": "Missing converted amount"},
                session=session,
                error_message="System error: Missing converted amount"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "status": "error",
                    "message": "System error: Missing converted amount"
                }
            )
        try:
            converted_amount = Decimal(converted_amount_str)
        except (TypeError, ValueError) as e:
            await mark_transaction_failed(
                transaction=transaction,
                reason=TransactionFailureReasonEnum.SYSTEM_ERROR,
                details={
                    "error": f"Invalid converted amount format: {str(e)}"},
                session=session,
                error_message="System error: Invalid converted amount format"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "status": "error",
                    "message": "System error: Invalid converted amount format"
                }
            )

        sender_account.balance = float(
            Decimal(str(sender_account.balance)) - transaction.amount
        )

        if not receiver_account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "status": "error",
                    "message": "Receiver account not found"
                }
            )

        receiver_account.balance = float(
            Decimal(str(receiver_account.balance)) + converted_amount
        )

        transaction.status = TransactionStatusEnum.COMPLETED
        transaction.completed_at = datetime.now(timezone.utc)

        sender.otp = ""
        sender.otp_expiry_time = None

        session.add(transaction)
        session.add(sender_account)
        session.add(receiver_account)
        session.add(sender)
        session.add(receiver)

        await session.commit()

        await session.refresh(transaction)
        await session.refresh(sender_account)
        await session.refresh(receiver_account)
        await session.refresh(sender)
        await session.refresh(receiver)

        if not receiver:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "status": "error",
                    "message": "Receiver not found"
                }
            )
        return transaction, sender_account, receiver_account, sender, receiver

    except HTTPException:
        await session.rollback()
        raise
    except Exception as e:
        if transaction:
            await mark_transaction_failed(
                transaction=transaction,
                reason=TransactionFailureReasonEnum.SYSTEM_ERROR,
                details={"error": str(e)},
                session=session,
                error_message=" A system error occured"
            )
        await session.rollback()
        logger.error(f"Failed to complete transfer")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": "error",
                "message": "Failed to complete the transfer"
            }
        )

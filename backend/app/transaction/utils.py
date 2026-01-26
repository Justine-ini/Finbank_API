from datetime import datetime, timezone
from typing import Optional
from sqlmodel.ext.asyncio.session import AsyncSession
from backend.app.transaction.models import Transaction
from backend.app.transaction.enums import TransactionFailureReasonEnum, TransactionStatusEnum
from backend.app.core.logging import get_logger

logger = get_logger()

async def mark_transaction_failed(
    transaction: Transaction,
    reason: TransactionFailureReasonEnum,
    details: dict,
    session: AsyncSession,
    error_message: Optional[str] = None
):

    try:
        transaction.status = TransactionStatusEnum.FAILED

        transaction.failed_reason = reason.value

        current_metadata = transaction.transaction_metadata or {}

        failure_details = {
            "reason": reason.value,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error_message": error_message,
            **details,
        }

        transaction.transaction_metadata = {
            **current_metadata,
            "failure_details": failure_details
        }

        session.add(transaction)
        await session.commit()
        await session.refresh(transaction)

        logger.error(
            f"Transaction {transaction.reference} marked as failed",
            extra={
                "reference": transaction.reference,
                "reason": reason.value,
                "details": failure_details,
            }
        )

    except Exception as e:
        logger.error(f"Error marking transaction {transaction.reference} as failed: {e}")
        
        raise



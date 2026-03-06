from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel.ext.asyncio.session import AsyncSession
from backend.app.transaction.schema import (
    PaginatedTransactionHistoryResponseSchema, 
    TransactionHistoryResponseSchema, 
    TransactionFilterParamsSchema
)
from backend.app.api.routes.auth.dependency import CurrentUser
from backend.app.core.logging import get_logger
from backend.app.core.db import get_session
from backend.app.api.services.transaction import get_user_transactions

logger = get_logger()

router = APIRouter(prefix="/transactions")

@router.get(
    "/history", 
    response_model=PaginatedTransactionHistoryResponseSchema,
    status_code=status.HTTP_200_OK,
    description="Get paginated transaction history for the authenticated user with optional filters"
)
async def get_transaction_history(
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
    skip: int = Query(default=0, ge=0, description="Number of records to skip for pagination"),
    limit: int = Query(default=20, ge=1, le=100, description="Maximum number of records to return for pagination"),
    filters: TransactionFilterParamsSchema = Depends(),  
)-> PaginatedTransactionHistoryResponseSchema:
    """
    Retrieve a paginated list of transactions for the authenticated user, with optional filtering by date range.
    """
    try:
        if filters.start_date and filters.end_date and filters.start_date > filters.end_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail={
                    "status": "error",
                    "message": "Invalid date range: start_date must be before end_date"
                }
            )
        
        transactions, total_count = await get_user_transactions(
            user_id=current_user.id,
            session=session,
            skip=skip,
            limit=limit,
            start_date=filters.start_date,
            end_date=filters.end_date,
            transaction_type=filters.transaction_type,
            transaction_category=filters.transaction_category,
            transaction_status=filters.transaction_status,
            min_amount=filters.min_amount,
            max_amount=filters.max_amount
        )

        transaction_responses = []

        for txn in transactions:
            metadata = txn.transaction_metadata or {}
            response = TransactionHistoryResponseSchema(
                id=txn.id,
                reference=txn.reference,
                amount=txn.amount,
                description=txn.description,
                transaction_type=txn.transaction_type,
                transaction_category=txn.transaction_category,
                transaction_status=txn.status,
                created_at=txn.created_at,
                completed_at=txn.completed_at,
                balance_after=txn.balance_after,
                account_currency=metadata.get("account_currency"),
                converted_amount=metadata.get("converted_amount"),
                from_currency=metadata.get("from_currency"),
                to_currency=metadata.get("to_currency"),
                counterparty_name=metadata.get("counterparty_name"),
                counterparty_account=metadata.get("counterparty_account")
            )
            transaction_responses.append(response)
          
        return PaginatedTransactionHistoryResponseSchema(
            total=total_count,
            skip=skip,
            limit=limit,
            transactions=transaction_responses
        )
    except HTTPException as httpex:
        raise httpex
    except Exception as e:
        logger.error(f"Error fetching transaction history for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": "error",
                "message": "Failed to retrieve transaction history",
                "action": "Please try again later"
            }
        )
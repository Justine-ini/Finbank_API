from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, status,Response
from sqlmodel.ext.asyncio.session import AsyncSession
from backend.app.api.routes.auth.dependency import CurrentUser
from backend.app.core.db import get_session
from backend.app.transaction.schema import (
    StatementRequestSchema, StatementResponseSchema
)
from backend.app.bank_account.enums import AccountStatusEnum
from backend.app.api.services.transaction import generate_user_statement
from backend.app.core.celery_app import celery_app
from backend.app.core.logging import get_logger
from sqlmodel import select
from backend.app.bank_account.models import BankAccount

logger = get_logger()
router = APIRouter(prefix="/bank-account", tags=["Bank Account"])
@router.post("/statement/generate",
             response_model=StatementResponseSchema,
             status_code=status.HTTP_202_ACCEPTED
            )
async def generate_statement(
    statement_request: StatementRequestSchema,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session)
)-> StatementResponseSchema:
    
    try:
        # Validate date range
        if statement_request.start_date > statement_request.end_date:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={
                "status": "error",
                "message": "Start date must be before end date."
            })
        # Check if account number is provided and user is owner
        if statement_request.account_number:
            result = await session.exec(
                select(BankAccount).where(
                    BankAccount.account_number == statement_request.account_number,
                    BankAccount.user_id == current_user.id
                )
            )
            bank_account = result.first()
            if not bank_account:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={
                    "status": "error",
                    "message": "Bank account not found or does not belong to the user."
                })
            # Check if bank account is active
            if bank_account.account_status != AccountStatusEnum.Active:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, 
                    detail={
                        "status": "error",
                        "message": "Cannot generate statement for inactive bank account."
                    }
                )
        # Generate statement for specific account
        result = await generate_user_statement(
            user_id=current_user.id,
            start_date=statement_request.start_date,
            end_date=statement_request.end_date,
            session=session,
            account_number=statement_request.account_number
        )

        celery_app.AsyncResult(result["task_id"])
        generated_at = datetime.now(timezone.utc)
        expires_at = generated_at + timedelta(hours=1)
        return StatementResponseSchema(
            task_id=result["task_id"],
            status="pending",
            message="Statement generation is in progress. Please check back later.",
            statement_id=result["statement_id"],
            generated_at=generated_at,
            expires_at=expires_at
        )
    
    except ValueError as ve:
        logger.error(f"Validation error: {ve}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "status": "error",
                "message": str(ve)
            }
        )
    
    except HTTPException as http_ex:
        raise http_ex

    except Exception as e:
        logger.error(f"Error generating statement: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": "error",
                "message": f"Failed to generate statement: {e}.",
                "action": "Please try again later or contact support if the issue persists."
            }
        )
    
@router.get("/statement/{statement_id}", status_code=status.HTTP_200_OK)
async def get_statement(statement_id: str) -> Response:
    try:
        # get statment from redis
        redis_client = celery_app.backend.client
        statement_data = redis_client.get(f"statement:{statement_id}")
        if not statement_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "status": "error",
                    "message": "Statement not found or has expired."
                }
            )
        return Response(
            content=statement_data, 
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=statement_{statement_id}.pdf"
            }
        )
    except HTTPException as http_ex:
        raise http_ex
    except Exception as e:
        logger.error(f"Error retrieving statement: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": "error",
                "message": f"Failed to retrieve statement: {e}.",
                "action": "Please try again later or contact support if the issue persists."
            }
)


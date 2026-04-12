import uuid
from fastapi import Query
from decimal import Decimal
from datetime import datetime
from typing_extensions import Annotated
from sqlmodel import SQLModel, Field, Column
from backend.app.transaction.enums import TransactionTypeEnum, TransactionStatusEnum, TransactionCategoryEnum
from sqlalchemy.dialects import postgresql as pg
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import Enum as SAEnum


class TransactionBaseSchema(SQLModel):

    amount: Annotated[Decimal, Field(decimal_places=2, ge=0)]
    description: str = Field(max_length=250)
    reference: str = Field(unique=True, index=True)
    transaction_type: TransactionTypeEnum = Field(
        sa_column=Column(
            SAEnum(
                TransactionTypeEnum,
                name="transaction_type_enum",
                create_type=False
            ),
            nullable=False
        )
    )
    transaction_category: TransactionCategoryEnum = Field(
        sa_column=Column(
            SAEnum(
                TransactionCategoryEnum,
                name="transaction_category_enum",
                create_type=False
            ),
            nullable=False
        )
    )
    status: TransactionStatusEnum = Field(
        default=TransactionStatusEnum.PENDING,
        sa_column=Column(
            SAEnum(
                TransactionStatusEnum,
                name="transaction_status_enum",
                create_type=False
            ),
            nullable=False
        )
    )
    balance_before: Annotated[Decimal, Field(decimal_places=2)]
    balance_after: Annotated[Decimal, Field(decimal_places=2)]

    transaction_metadata: dict | None = Field(default=None, sa_column=Column(JSONB))

    failed_reason: str | None = Field(default=None, max_length=255)

class TransactionCreateSchema(TransactionBaseSchema):
    pass

class TransactionReadSchema(TransactionBaseSchema):
    id: uuid.UUID
    created_at: datetime = Field(sa_column=Column(pg.TIMESTAMP(timezone=True), nullable=False))
    completed_at: datetime | None = Field(
        default=None,
        sa_column=Column(pg.TIMESTAMP(timezone=True), nullable=True)
    )

class TransactionUpdateSchema(TransactionBaseSchema):
    pass

class DepositRequestSchema(SQLModel):
    account_id: uuid.UUID
    amount: Decimal = Field(decimal_places=2, ge=0)
    description: str = Field(max_length=250)
    

class TransferRequestSchema(SQLModel):
    sender_account_id: uuid.UUID
    receiver_account_number: str = Field(min_length=16, max_length=16)
    amount: Decimal = Field(decimal_places=2, ge=0)
    security_answer: str = Field(max_length=30)
    description: str = Field(max_length=250)


class TransferOTPVerificationSchema(SQLModel):
    transfer_reference: str = Field(max_length=100)
    otp: str = Field(min_length=6, max_length=6)


class TransferResponseSchema(SQLModel):
    status: str
    message: str
    data: dict | None = None

class CurrencyConversionSchema(SQLModel):
    amount: Decimal 
    from_currency: str = Field(min_length=3, max_length=3)
    to_currency: str = Field(min_length=3, max_length=3)
    exchange_rate: Decimal
    original_amount: Decimal 
    converted_amount: Decimal
    conversion_fee: Decimal = Field(default=Decimal("0.00"))


class WithdrawRequestSchema(SQLModel):
    account_number: str = Field(min_length=16, max_length=16)
    amount: Decimal = Field(decimal_places=2, ge=0)
    username: str = Field(min_length=1, max_length=12)
    description: str = Field(max_length=250)


class TransactionHistoryResponseSchema(SQLModel):
    id: uuid.UUID
    reference: str
    amount: Decimal
    description: str
    transaction_type: TransactionTypeEnum
    transaction_category: TransactionCategoryEnum
    transaction_status: TransactionStatusEnum
    created_at: datetime
    completed_at: datetime | None = None
    balance_after: Decimal
    account_currency: str
    converted_amount: str | None = None
    from_currency: str | None = None
    to_currency: str | None = None
    counterparty_name: str | None = None
    counterparty_account: str | None = None


class PaginatedTransactionHistoryResponseSchema(SQLModel):
    total: int
    skip: int
    limit: int
    transactions: list[TransactionHistoryResponseSchema]


class TransactionFilterParamsSchema(SQLModel):
    start_date: datetime | None = Query(
        default=None,
        description="Filter transactions created after this date",
        example="2024-01-01T00:00:00Z")
    end_date: datetime | None = Query(
        default=None,
        description="Filter transactions created before this date",
        example="2024-12-01T00:00:00Z")
    transaction_type: TransactionTypeEnum | None = Query(
        default=None,
        description="Filter transactions by type")
    transaction_category: TransactionCategoryEnum | None = Query(
        default=None,
        description="Filter transactions by category")
    transaction_status: TransactionStatusEnum | None = Query(
        default=None,
        description="Filter transactions by status")
    min_amount: Decimal | None = Query(
        default=None,
        ge=0,
        description="Filter transactions with amount greater than or equal to this value")
    max_amount: Decimal | None = Query(
        default=None,
        ge=0,
        description="Filter transactions with amount less than or equal to this value")


class StatementRequestSchema(SQLModel):
    start_date: datetime
    end_date: datetime
    account_number: str | None = Field(
        default=None,
        min_length=16,
        max_length=16,
        description="16-digit account number for specific account state"
    )

class StatementResponseSchema(SQLModel):
    status: str
    message: str
    task_id: str | None = None
    statement_id: str | None = None
    generated_at: datetime | None = None
    expires_at: datetime | None = None

class TransactionReviewSchema(SQLModel):
    is_fraud: bool
    notes: str | None = None
    approved_transaction: bool = False

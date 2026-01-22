import uuid
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
    
    
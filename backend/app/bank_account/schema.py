from uuid import UUID
from datetime import datetime
from sqlmodel import SQLModel, Field, Column
from sqlalchemy import Enum as SAEnum
from backend.app.bank_account.enums import AccountTypeEnum, AccountStatusEnum, AccountCurrencyEnum


class BankAccountBaseSchema(SQLModel):
    account_status: AccountStatusEnum = Field(
        default=AccountStatusEnum.Pending,
        sa_column=Column(
            SAEnum(
                AccountStatusEnum,
                name="bank_account_status_enum",
                create_type=False
            ),
            nullable=False
        )
    )
    account_type: AccountTypeEnum = Field(
        sa_column=Column(
            SAEnum(
                AccountTypeEnum,
                name="bank_account_type_enum",
                create_type=False
            ),
            nullable=False
        )
    )
    account_currency: AccountCurrencyEnum = Field(
        sa_column=Column(
            SAEnum(
                AccountCurrencyEnum,
                name="bank_account_currency_enum",
                create_type=False
            ),
            nullable=False
        )
    )
    account_number: str | None = Field(default=None, unique=True, index=True)
    account_name: str
    balance: float = Field(default=0.0)
    is_primary: bool = Field(default=False)
    kyc_submitted: bool = Field(default=False)
    kyc_verified: bool = Field(default=False)
    kyc_verified_by: UUID | None = Field(default=None)
    interest_rate: float = Field(default=0.0)


class BankAccountCreateSchema(BankAccountBaseSchema):
    account_number: str | None = None

class BankAccountReadSchema(BankAccountBaseSchema):
    id:UUID
    user_id: UUID
    account_number: str | None = None
    account_number: str | None = None
    created_at: datetime
    updated_at: datetime

class BankAccountUpdateSchema(BankAccountBaseSchema):
    account_name: str | None = None
    is_primary: bool | None = None
    account_status: AccountStatusEnum | None = None
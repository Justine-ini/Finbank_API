from datetime import date, datetime
from typing import Any
from uuid import UUID
from pydantic import Field
from sqlmodel import SQLModel
from backend.app.virtual_card.enums import (
    VirtualCardStatusEnum,
    VirtualCardTypeEnum,
    VirtualCardProviderEnum,
    VirtualCardCurrencyEnum,
    CardBlockReasonEnum
)

class VirtualCardBaseSchema(SQLModel):
    card_number: str | None = Field(
        default=None, 
        description="Unique card number"
    )
    card_type: VirtualCardTypeEnum = Field(
        ..., 
        description="Type of the virtual card (debit or credit)"
    )
    card_provider: VirtualCardProviderEnum = Field(
        default=VirtualCardProviderEnum.VISA, 
        description="Card provider (Visa, MasterCard, Verve)"
    )
    currency: VirtualCardCurrencyEnum = Field(
        ..., 
        description="Currency of the virtual card"
    )
    card_status: VirtualCardStatusEnum = Field(
        default=VirtualCardStatusEnum.PENDING, 
        description="Current status of the virtual card"
    )
    daily_spending_limit: float = Field(
        ...,
        gt=0,
        description="Daily spending limit for the virtual card"
    )
    monthly_spending_limit: float = Field(
        ...,
        gt=0,
        description="Monthly spending limit for the virtual card"
    )
    cardholder_name: str = Field(max_length=100, description="Name of the cardholder")
    expiry_date: date 
    is_active: bool = Field(default=True, description="Indicates if the card is active")
    is_physical_card_requested: bool = Field(
        default=False, 
        description="Indicates if the card is physical or virtual")
    block_reason: CardBlockReasonEnum | None = Field(
        default=None, 
        description="Reason for blocking the card (if applicable)"
    )
    block_reason_details: str | None = Field(
        default=None,
        description="Additional details about the block reason (if applicable)"
    )
    card_metadata: dict[str, Any] | None = Field(
        default=None,
        description="Additional metadata related to the virtual card"
    )

class VirtualCardCreateSchema(VirtualCardBaseSchema):
    bank_account_id: UUID = Field(
        ..., 
        description="ID of the associated bank account"
    )
    expiry_date: date | None = None
    
    

class VirtualCardReadSchema(VirtualCardBaseSchema):
    id: UUID = Field(..., description="Unique identifier for the virtual card")
    bank_account_id: UUID = Field(..., description="ID of the associated bank account")
    last_four_digits: str | None = Field(
        default=None,
        description="Last four digits of the card number"
    )
    created_at: datetime = Field(..., description="Timestamp when the virtual card was created")
    updated_at: datetime | None = Field(
        default=None,
        description="Timestamp when the virtual card was last updated"
    )

class VirtualCardUpdateSchema(VirtualCardBaseSchema):
    daily_spending_limit: float | None = Field(
        default=None,
        gt=0,
        description="Daily spending limit for the virtual card"
    )
    monthly_spending_limit: float | None = Field(
        default=None,
        gt=0,
        description="Monthly spending limit for the virtual card"
    )
    is_active: bool | None = Field(
        default=None,
        description="Indicates if the card is active"
    )

class VirtualCardBlockSchema(VirtualCardBaseSchema):
    block_reason: CardBlockReasonEnum = Field(
        ..., 
        description="Reason for blocking the card"
    )
    block_reason_details: str = Field(
        ...,
        description="Additional details about the block reason (if applicable)"
    )
    blocked_at: datetime = Field(..., description="Timestamp when the card was blocked")
    blocked_by: UUID = Field(..., description="ID of the user who blocked the card")

class VirtualCardStatusSchema(VirtualCardBaseSchema):
    card_status: VirtualCardStatusEnum = Field(
        ..., 
        description="Current status of the virtual card"
    )
    available_balance: float = Field(
        ...,
        description="Current available balance on the virtual card"
    )
    daily_spending_limit: float = Field(
        ...,
        description="Daily spending limit for the virtual card"
    )
    monthly_spending_limit: float = Field(
        ...,
        description="Monthly spending limit for the virtual card"
    )
    total_spent_today: float = Field(
        ...,
        description="Total amount spent today using the virtual card"
    )
    total_spent_this_month: float = Field(
        ...,
        description="Total amount spent this month using the virtual card"
    )
    last_transaction_date: datetime | None = Field(
        default=None,
        description="Timestamp of the last transaction made with the virtual card"
    )
    last_transaction_amount: float | None = Field(
        default=None,
        description="Amount of the last transaction made with the virtual card"
    )

class PhysicalCardRequestSchema(SQLModel):
    delivery_address: str = Field(
        max_length=255, 
        description="Shipping address for the physical card"
    )
    city: str = Field(max_length=100, description="City for the delivery address")
    state: str = Field(max_length=100, description="State for the delivery address")
    postal_code: str = Field(max_length=20, description="Postal code for the delivery address")
    country: str = Field(max_length=100, description="Country for the delivery address")

class CardTopUpSchema(SQLModel):
    account_number: str = Field(
        min_length=16, 
        max_length=16, 
        description="Bank account number to top up the virtual card from"
    )
    amount: float = Field(..., gt=0, description="Amount to top up the virtual card")
    description: str | None = Field(
        default=None, 
        max_length=255, 
        description="Description for the top-up transaction"
    )

class TopUpResponseSchema(SQLModel):
    status: str = Field(..., description="Status of the top-up operation")
    message: str = Field(..., description="Detailed message about the top-up operation")
    data: dict[str, Any] | None = Field(
        default=None,
        description="Additional data related to the top-up operation (e.g., transaction details)"
    )

class CardDeleteResponseSchema(SQLModel):
    status: str = Field(..., description="Status of the card deletion operation")
    message: str = Field(..., description="Detailed message about the card deletion operation")
    deleted_at: datetime = Field(..., description="Timestamp when the card was deleted")

class CardBlockSchema(SQLModel):
    block_reason: CardBlockReasonEnum = Field(
        ..., 
        description="Reason for blocking the card"
    )
    block_reason_details: str = Field(
        ...,
        description="Additional details about the block reason (if applicable)"
    )
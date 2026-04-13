import uuid
from typing import TYPE_CHECKING, Any
from datetime import datetime, timezone
from sqlmodel import Field, Column, Relationship
from sqlalchemy.dialects import postgresql as pg
from sqlalchemy import text, func
from sqlalchemy.dialects.postgresql import JSONB
from backend.app.virtual_card.schema import VirtualCardBaseSchema


if TYPE_CHECKING:
    from backend.app.auth.models import User
    from backend.app.bank_account.models import BankAccount

class VirtualCard(VirtualCardBaseSchema, table=True): # type: ignore
    id: uuid.UUID = Field(
        sa_column=Column(
            pg.UUID(as_uuid=True),
            primary_key=True,
        ),
        default_factory=uuid.uuid4
    )
    bank_account_id: uuid.UUID = Field(
        foreign_key="bankaccount.id",
        ondelete="CASCADE"
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(
            pg.TIMESTAMP(timezone=True), 
            nullable=False, 
            server_default=text("CURRENT_TIMESTAMP"),
        )
    )

    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(
            pg.TIMESTAMP(timezone=True), 
            nullable=False, 
            onupdate=func.current_timestamp(),
        ),
    )
    cvv_hash: str | None = Field(
        default=None,
        description="Hashed value of the card's CVV for security purposes"
    )
    available_balance: float = Field(
        default=0.0,
        description="Current available balance on the virtual card"
    )
    total_topped_amount: float = Field(
        default=0.0,
        description="Total amount that has been topped up to the virtual card"
    )
    last_topped_at: datetime | None = Field(
        default=None,
        sa_column=Column(
            pg.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=text("CURRENT_TIMESTAMP"),
        ),
        description="Timestamp of the last top-up to the virtual card"
    )
    blocked_at: datetime | None = Field(
        default=None,
        sa_column=Column(
            pg.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=text("CURRENT_TIMESTAMP"),
        ),
        description="Timestamp of the last top-up to the virtual card"
    )
    total_spent_today: float = Field(
        default=0.0,
        description="Total amount spent today using the virtual card"
    )
    total_spent_this_month: float = Field(
        default=0.0,
        description="Total amount spent this month using the virtual card"
    )
    last_transaction_date: datetime | None = Field(
        default=None,
        description="Timestamp of the last transaction made with the virtual card"
    )
    last_transaction_amount: float = Field(
        default=None,
        description="Amount of the last transaction made with the virtual card"
    )
    physical_card_requested_at: datetime | None = Field(
        default=None,
        description="Timestamp when the user requested a physical card"
    )
    delivery_address: str | None = Field(
        default=None,
        description="Delivery address for the physical card"
    )
    city: str | None = Field(
        default=None,
        description="City for the delivery address of the physical card"
    )
    state: str | None = Field(
        default=None,
        description="State for the delivery address of the physical card"
    )
    postal_code: str | None = Field(
        default=None,
        description="Postal code for the delivery address of the physical card"
    )
    country: str | None = Field(
        default=None,
        description="Country for the delivery address of the physical card"
    )
    physical_card_status: str | None = Field(
        default=None,
        description="Status of the physical card (e.g., pending, shipped, delivered)"
    )
    blocked_by: uuid.UUID | None = Field(
        foreign_key="user.id",
        nullable=True,
        description="ID of the user who blocked the card, if applicable"
    )
    card_metadata: dict[str, Any] | None = Field(
        default=None,
        sa_column=Column(JSONB)
    )
    bank_account: "BankAccount" = Relationship(back_populates="virtual_cards")
    blocked_by_user: "User" = Relationship(
        sa_relationship_kwargs={
            "foreign_keys": "VirtualCard.blocked_by",
        }
    )
    @property
    def masked_card_number(self) -> str:
        if not self.card_number:
            return ""
        return f"**** **** **** {self.card_number[-4:]}"
    
    @property
    def last_four_digits(self) -> str:
        if not self.card_number:
            return ""
        return self.card_number[-4:]


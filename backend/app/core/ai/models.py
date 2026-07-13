import uuid
from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy import text
from sqlalchemy.dialects import postgresql as pg
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Column, Field, SQLModel

class TransactionRiskScore(SQLModel, table=True):
    __tablename__ = "transaction_risk_scores"

    id: uuid.UUID = Field(
        sa_column=Column(
            pg.UUID(as_uuid=True), 
            unique=True,
            primary_key=True,
        ),
        default_factory=uuid.uuid4,
    )
    transaction_id: uuid.UUID = Field(
        foreign_key="transaction.id",
        index=True,
    )
    risk_score: float = Field(ge=0, le=1, index=True)
    risk_factors: dict = Field(sa_column=Column(JSONB))
    ai_model_version: str
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(
            pg.TIMESTAMP(timezone=True),
            server_default=text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
    )
    reviewed_by: UUID | None = Field(
        foreign_key="user.id",
        default=None,
        nullable=True,
    )
    is_confirmed_fraud: bool | None = Field(
        default=None,
    )

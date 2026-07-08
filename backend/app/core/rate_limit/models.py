import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, text
from sqlalchemy.dialects import postgresql as pg
from sqlmodel import SQLModel, Field

class RateLimitLog(SQLModel, table=True):
    id: uuid.UUID = Field(
        sa_column=Column(
            pg.UUID(as_uuid=True),
            primary_key=True,
        ),
        default_factory=uuid.uuid4
    )
    ip_address: str = Field(index=True)

    user_id: uuid.UUID | None = Field(
        foreign_key="user.id",
        default=None
    )
    endpoint: str = Field(index=True)
    request_count: int 
    request_method: str
    request_path: str
    window_start: datetime = Field(
        sa_column=Column(
            pg.TIMESTAMP(timezone=True), 
            nullable=True
        )
    )
    window_end: datetime = Field(
        sa_column=Column(
            pg.TIMESTAMP(timezone=True), 
            nullable=True
        )
    )
    blocked_until: datetime | None = Field(
        default=None,
        sa_column=Column(
            pg.TIMESTAMP(timezone=True), 
            nullable=True
        )
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(
            pg.TIMESTAMP(timezone=True), 
            nullable=False, 
            server_default=text("CURRENT_TIMESTAMP"),
        )
    )
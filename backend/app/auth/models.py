import uuid
from datetime import datetime, timezone
from sqlmodel import Field, Column
from pydantic import computed_field
from sqlalchemy.dielects import postgresql as pg
from sqlalchemy import text, func
from backend.app.auth.schema import BASE_USER_SCHEMA, RoleChoicsSchema


class User(BASE_USER_SCHEMA, table=True):
    id: uuid.UUID = Field(sa_column=Column(
        pg.UUID(as_uuid=True),
        primary_key=True,
    ),
    default_factory=uuid.uuid4
    )
    hashed_password: str
    failed_login_attempts: int = Field(default=0, sa_type=pg.SMALLINT)
    last_failed_login: datetime | None = Field(
        default=None, 
        sa_column=Column(pg.TIMESTAMP(timezone=True))
    )
    otp: str = Field(max_length=6, default="")
    otp_expiry_time: datetime | None = Field(
        default=None, 
        sa_column=Column(pg.TIMESTAMP(timezone=True))
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

    @computed_field
    @property
    def full_name(self) -> str:
        full_name = f"{self.first_name} {self.middle_name + ' ' if self.middle_name else ''} {self.last_name}"
        return full_name.title().strip()
    
    def has_role(self, role: RoleChoicsSchema) -> bool:
        return self.role.value == role.value
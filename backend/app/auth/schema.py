import uuid
from enum import Enum
from sqlalchemy import Enum as SAEnum
from sqlmodel import SQLModel, Field, Column
from pydantic import EmailStr, field_validator
from fastapi import HTTPException, status

class SecurityQuestionSchema(str, Enum):
    MOTHER_MAIDEN_NAME = "mother_maiden_name"
    CHILDHOOD_FRIEND = "childhood_friend"
    FAVORITE_COLOR = "favorite_color"
    BIRTH_CITY = "birth_city"

    @classmethod
    def get_description(cls, value: "SecurityQuestionSchema") -> str:
        description = {
            cls.MOTHER_MAIDEN_NAME: "What is the name of your mother?",
            cls.CHILDHOOD_FRIEND: "What is the name of your childhood friend?",
            cls.FAVORITE_COLOR: "What is your favorite color?",
            cls.BIRTH_CITY: "What is the name of the city you were born?"
        }
        return description.get(value, "Unknown security question")


class AccountStatusSchema(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    LOCKED = "locked"
    PENDING = "pending"

class RoleChoicesSchema(str, Enum):
    CUSTOMER = "customer"
    ACCOUNT_EXECUTIVE = "account_executive"
    BRANCH_MANAGER = "branch_manager"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"
    TELLER = "teller"


class BaseUserSchema(SQLModel):
    username: str | None = Field(default=None, max_length=12, unique=True)
    email: EmailStr = Field(unique=True, index=True, max_length=255)
    first_name: str = Field(max_length=30)
    middle_name: str | None = Field(max_length=30, default=None)
    last_name: str = Field(max_length=30)
    id_no: int = Field(unique=True, gt=0)
    is_active: bool = False
    is_superuser: bool = False
    security_question: SecurityQuestionSchema = Field(
        sa_column=Column(
            SAEnum(
                SecurityQuestionSchema,
                name="security_question_enum",
                create_type=False
            ),
            nullable=False
        )
    )
    security_answer: str = Field(max_length=30)
    account_status: AccountStatusSchema = Field(
        default=AccountStatusSchema.INACTIVE,
        sa_column=Column(
            SAEnum(
                AccountStatusSchema,
                name="account_status_enum",
                create_type=False
            ),
            nullable=False
        )
    )

    role: RoleChoicesSchema = Field(
        default=RoleChoicesSchema.CUSTOMER,
        sa_column=Column(
            SAEnum(
                RoleChoicesSchema,
                name="role_enum",
                create_type=False
            ),
            nullable=False
        )
    )


class UserCreateSchema(BaseUserSchema):
    password: str = Field(min_length=8, max_length=40)
    confirm_password: str = Field(min_length=8, max_length=40)

    # This means this function below will run automatically whenever Pydantic is validating the confirm_password field.
    @field_validator("confirm_password")
    def validate_confirm_password(cls, v, values):
        if "password" in values.data and v != values.data["password"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail = {
                    "status": "error",
                    "message": "passwords did not match",
                    "action": "Please ensure that the passwords you entered match"
                }
            )
        return v

class USerReadSchema(BaseUserSchema):
    id: uuid.UUID
    full_name: str


class EmailRequestSchema(SQLModel):
    email: EmailStr


class LoginRequestSchema(SQLModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=40)


class OTPVerifyRequestSchema(SQLModel):
    email: EmailStr
    otp: str = Field(min_length=6, max_length=6)

class PasswordResetRequestSchema(SQLModel):
    email: EmailStr
    
class PasswordResetConfirmSchema(SQLModel):
    new_password: str = Field(
        ...,
        min_length=8, 
        max_length=40
    )
    confirm_new_password: str = Field(
        ...,
        min_length=8,
        max_length=40
    )

    @field_validator("confirm_new_password")
    def validate_password_match(cls, v, values):
        if "new_password" in values.data and v != values.data["new_password"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "status": "error",
                    "message": "New passwords did not match",
                    "action": "Please ensure that the new passwords you entered match"
                }
            )
        return v
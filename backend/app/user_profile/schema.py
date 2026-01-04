from datetime import date
from sqlmodel import SQLModel, Field, Column
from sqlalchemy import Enum as SAEnum
from pydantic import field_validator, model_validator
from pydantic_extra_types.phone_numbers import PhoneNumber
from pydantic_extra_types.country import CountryShortName
from backend.app.auth.schema import RoleChoicesSchema
from backend.app.user_profile.utils import validate_id_dates
from .enums import (
    SalutationEnum,
    MaritalStatusEnum,
    GenderEnum,
    IdentificationTypeEnum,
    EmploymentStatusEnum,
)

class ProfileBaseSchema(SQLModel):
    title: SalutationEnum = Field(
        sa_column=Column(
            SAEnum(SalutationEnum, name="salutation_enum", create_type=False),
            nullable=False
        )
    )
    gender: GenderEnum = Field(
        sa_column=Column(
            SAEnum(GenderEnum, name="gender_enum", create_type=False),
            nullable=False
        )
    )
    marital_status: MaritalStatusEnum = Field(
        sa_column=Column(
            SAEnum(MaritalStatusEnum, name="marital_status_enum", create_type=False),
            nullable=False
        )
    )
    date_of_birth: date
    country_of_birth: CountryShortName
    place_of_birth: str
    identification_type: IdentificationTypeEnum = Field(
        sa_column=Column(
            SAEnum(
                IdentificationTypeEnum,
                name="identification_type_enum",
                create_type=False
            ),
            nullable=False
        )
    )
    phone_number: PhoneNumber
    means_of_identification: IdentificationTypeEnum = Field(
        sa_column=Column(
            SAEnum(
                IdentificationTypeEnum,
                name="means_of_identification_enum",
                create_type=False
            ),
            nullable=False
        )
    )
    id_issued_date: date
    id_expiry_date: date
    passport_number: str | None = Field(default=None)
    nationality: str
    address: str
    city: str
    country: str
    employment_status: EmploymentStatusEnum = Field(
        sa_column=Column(
            SAEnum(
                EmploymentStatusEnum,
                name="employment_status_enum",
                create_type=False
            ),
            nullable=False
        )
    )
    employer_name: str | None = Field(default=None)
    employer_address: str | None = Field(default=None)
    employer_city: str | None = Field(default=None)
    employer_country: str | None = Field(default=None)
    annual_income: float = Field(gt=0)
    date_of_employment: date | None = Field(default=None)
    profile_photo_url: str | None = Field(default=None)
    id_photo_url: str | None = Field(default=None)
    signature_photo_url: str | None = Field(default=None)


class ProfileCreateSchema(ProfileBaseSchema):

    @field_validator("id_expiry_date")
    def validate_id_dates(cls, v, values):
        issued = values.data.get("id_issued_date")
        if issued is not None:
            validate_id_dates(issued, v)
        return v

    @model_validator(mode="after")
    def validate_passport_number(self):
        if self.identification_type == IdentificationTypeEnum.PASSPORT:
            if not self.passport_number:
                raise ValueError(
                    "passport_number is required when identification_type is PASSPORT"
                )
        return self



class ProfileUpdateSchema(SQLModel):
    title: SalutationEnum | None = None
    gender: GenderEnum | None = None
    marital_status: MaritalStatusEnum | None = None
    date_of_birth: date | None = None
    country_of_birth: CountryShortName | None = None
    place_of_birth: str | None = None
    identification_type: IdentificationTypeEnum | None = None
    phone_number: PhoneNumber | None = None
    means_of_identification: IdentificationTypeEnum | None = None
    id_issued_date: date | None = None
    id_expiry_date: date | None = None
    passport_number: str | None = None
    nationality: str | None = None
    address: str | None = None
    city: str | None = None
    country: str | None = None
    employment_status: EmploymentStatusEnum | None = None
    employer_name: str | None = None
    employer_address: str | None = None
    employer_city: str | None = None
    employer_country: str | None = None
    annual_income: float | None = None
    date_of_employment: date | None = None
 
    
    @field_validator("id_expiry_date")
    def validate_id_dates(cls, v: date | None, values) -> date | None:
        issued = values.data.get("id_issued_date")
        if v is not None and issued is not None:
            validate_id_dates(issued, v)
        return v

    @model_validator(mode="after")
    def validate_passport_number(self):
        # Only enforce if identification_type is being updated
        if self.identification_type == IdentificationTypeEnum.PASSPORT:
            if not self.passport_number:
                raise ValueError(
                    "passport_number is required when identification_type is PASSPORT"
                )
        return self


class ProfileResponseSchema(SQLModel):
    username: str
    first_name: str
    middle_name: str
    last_name: str
    email: str
    id_no: str
    role: RoleChoicesSchema
    profile: ProfileBaseSchema | None

    class Config:
        from_attributes = True


class PaginatedProfileResponseSchema(SQLModel):
    profiles: list[ProfileResponseSchema]
    total: int
    skip: int
    limit: int
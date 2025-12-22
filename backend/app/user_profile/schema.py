from enum import Enum
from datetime import date
from sqlmodel import SQLModel, Field
from pydantic import field_validator
from pydantic_extra_types.phone_numbers import PhoneNumber
from pydantic_extra_types.country import CountryShortName
from backend.app.user_profile.utils import validate_id_dates



class SalutationSchema(str, Enum):
    MR = "Mr."
    MRS = "Mrs."
    MS = "Ms."
    

class GenderSchema(str, Enum):
    MALE = "Male"
    FEMALE = "Female"
    OTHER = "Other"

class MaritalStatusSchema(str, Enum):
    SINGLE = "Single"
    MARRIED = "Married"
    DIVORCED = "Divorced"
    WIDOWED = "Widowed"

class IdentificationTypeSchema(str, Enum):
    PASSPORT = "Passport"
    NATIONAL_ID = "National ID"
    DRIVER_LICENSE = "Driver's License"


class EmploymentStatusSchema(str, Enum):
    EMPLOYED = "Employed"
    SELF_EMPLOYED = "Self-Employed"
    UNEMPLOYED = "Unemployed"
    STUDENT = "Student"
    RETIRED = "Retired"


class ProfileBaseSchema(SQLModel):
    title: SalutationSchema
    gender: GenderSchema
    marital_status: MaritalStatusSchema
    date_of_birth: date
    country_of_birth: CountryShortName
    place_of_birth: str
    identification_type: IdentificationTypeSchema
    phone_number: PhoneNumber
    means_of_identification: IdentificationTypeSchema
    id_issued_date: date
    id_expiry_date: date
    passport_number: str
    nationality: str
    address: str
    city: str
    country: str
    employment_status: EmploymentStatusSchema
    employer_name: str
    employer_address: str
    employer_city: str
    employer_country: str
    annual_income: float
    date_of_employment: date
    profile_photo_url: str | None = Field(default=None)
    id_photo_url: str | None = Field(default=None)
    signature_photo_url: str | None = Field(default=None)


class ProfileCreateSchema(ProfileBaseSchema):
    @field_validator("id_expiry_date")
    def validate_id_dates(cls, v, values):
        if "id_issue_date" in values.data:
            validate_id_dates(values.data["id_issue_date"], v)
        return v
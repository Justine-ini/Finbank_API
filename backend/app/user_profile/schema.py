from enum import Enum
from datetime import date
from sqlmodel import SQLModel, Field
from pydantic import field_validator, model_validator
from pydantic_extra_types.phone_numbers import PhoneNumber
from pydantic_extra_types.country import CountryShortName
from backend.app.auth.schema import RoleChoicesSchema
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
    passport_number: str | None = Field(default=None)
    nationality: str
    address: str
    city: str
    country: str
    employment_status: EmploymentStatusSchema
    employer_name: str | None = Field(default=None)
    employer_address: str | None = Field(default=None)
    employer_city: str | None = Field(default=None)
    employer_country: str | None = Field(default=None)
    annual_income: float = Field(gt=0)
    date_of_employment: date | None = Field(default=None)
    profile_photo_url: str | None = Field(default=None)
    id_photo_url: str | None = Field(default=None)
    signature_photo_url: str | None = Field(default=None)


# class ProfileCreateSchema(ProfileBaseSchema):
#     @field_validator("id_expiry_date")
#     def validate_id_dates(cls, v, values):
#         if "id_issued_date" in values.data:
#             validate_id_dates(values.data["id_issued_date"], v)
#         return v
    
#     @model_validator(mode="after")
#     def validate_passport_number(self):
#         if self.identification_type == IdentificationTypeSchema.PASSPORT:
#             if not self.passport_number:
#                 raise ValueError(
#                     "passport_number is required when identification_type is PASSPORT"
#                 )
#         return self

class ProfileCreateSchema(ProfileBaseSchema):

    @field_validator("id_expiry_date")
    def validate_id_dates(cls, v, values):
        issued = values.data.get("id_issued_date")
        if issued is not None:
            validate_id_dates(issued, v)
        return v

    @model_validator(mode="after")
    def validate_passport_number(self):
        if self.identification_type == IdentificationTypeSchema.PASSPORT:
            if not self.passport_number:
                raise ValueError(
                    "passport_number is required when identification_type is PASSPORT"
                )
        return self



class ProfileUpdateSchema(SQLModel):
    title: SalutationSchema | None = None
    gender: GenderSchema | None = None
    marital_status: MaritalStatusSchema | None = None
    date_of_birth: date | None = None
    country_of_birth: CountryShortName | None = None
    place_of_birth: str | None = None
    identification_type: IdentificationTypeSchema | None = None
    phone_number: PhoneNumber | None = None
    means_of_identification: IdentificationTypeSchema | None = None
    id_issued_date: date | None = None
    id_expiry_date: date | None = None
    passport_number: str | None = None
    nationality: str | None = None
    address: str | None = None
    city: str | None = None
    country: str | None = None
    employment_status: EmploymentStatusSchema | None = None
    employer_name: str | None = None
    employer_address: str | None = None
    employer_city: str | None = None
    employer_country: str | None = None
    annual_income: float | None = None
    date_of_employment: date | None = None
 
    
    # @field_validator("id_expiry_date")
    # def validate_id_dates(cls, v:date | None, values) -> date | None:
    #     if v is not None and "id_issued_date" in values.data:
    #         validate_id_dates(values.data["id_issued_date"], v)
    #     return v
    
    # @model_validator(mode="after")
    # def validate_passport_number(self):
    #     if self.identification_type == IdentificationTypeSchema.PASSPORT:
    #         if not self.passport_number:
    #             raise ValueError(
    #                 "passport_number is required when identification_type is PASSPORT"
    #             )
    #     return self

    @field_validator("id_expiry_date")
    def validate_id_dates(cls, v: date | None, values) -> date | None:
        issued = values.data.get("id_issued_date")
        if v is not None and issued is not None:
            validate_id_dates(issued, v)
        return v

    @model_validator(mode="after")
    def validate_passport_number(self):
        # Only enforce if identification_type is being updated
        if self.identification_type == IdentificationTypeSchema.PASSPORT:
            if not self.passport_number:
                raise ValueError(
                    "passport_number is required when identification_type is PASSPORT"
                )
        return self


class ImageTypeSchema(str, Enum):
    PROFILE_PHOTO = "profile_photo"
    ID_PHOTO = "id_photo"
    SIGNATURE_PHOTO = "signature_photo"

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
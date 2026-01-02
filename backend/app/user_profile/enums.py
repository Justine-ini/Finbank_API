from enum import Enum


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


class ImageTypeSchema(str, Enum):
    PROFILE_PHOTO = "profile_photo"
    ID_PHOTO = "id_photo"
    SIGNATURE_PHOTO = "signature_photo"
from enum import Enum


class SalutationEnum(str, Enum):
    MR = "Mr."
    MRS = "Mrs."
    MS = "Ms."


class GenderEnum(str, Enum):
    MALE = "Male"
    FEMALE = "Female"
    OTHER = "Other"


class MaritalStatusEnum(str, Enum):
    SINGLE = "Single"
    MARRIED = "Married"
    DIVORCED = "Divorced"
    WIDOWED = "Widowed"


class IdentificationTypeEnum(str, Enum):
    PASSPORT = "Passport"
    NATIONAL_ID = "National ID"
    DRIVER_LICENSE = "Driver's License"


class EmploymentStatusEnum(str, Enum):
    EMPLOYED = "Employed"
    SELF_EMPLOYED = "Self-Employed"
    UNEMPLOYED = "Unemployed"
    STUDENT = "Student"
    RETIRED = "Retired"


class ImageTypeEnum(str, Enum):
    PROFILE_PHOTO = "profile_photo"
    ID_PHOTO = "id_photo"
    SIGNATURE_PHOTO = "signature_photo"
from enum import Enum

class AIReviewStatusEnum(str, Enum):
    PENDING = "pending"
    FLAGGED = "flagged"
    CLEARED = "cleared"
    CONFIRMED_FRAUD = "confirmed_fraud"
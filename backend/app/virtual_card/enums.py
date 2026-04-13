from enum import Enum

class VirtualCardStatusEnum(str, Enum):
    ACTIVE   = "active"
    INACTIVE = "inactive"
    BLOCKED  = "blocked"
    PENDING  = "pending"
    EXPPIRED = "expired"

class VirtualCardTypeEnum(str, Enum):
    DEBIT  = "debit"
    CREDIT = "credit"

class VirtualCardProviderEnum(str, Enum):
    VISA = "Visa"
    MASTERCARD = "MasterCard"
    VERVE = "Verve"

class VirtualCardCurrencyEnum(str, Enum):
    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"
    NGN = "NGN"

class CardBlockReasonEnum(str, Enum):
    SUSPECTED_FRAUD         = "suspected_fraud"
    UNAUTHORIZED_TRANSACTION = "unauthorized_transaction"
    LOST_CARD               = "lost_card"
    STOLEN_CARD             = "stolen_card"
    EXCEEDED_PIN_ATTEMPTS   = "exceeded_pin_attempts"
    CUSTOMER_REQUEST        = "customer_request"
    ACCOUNT_SUSPENDED       = "account_suspended"
    ACCOUNT_CLOSED          = "account_closed"
    EXPIRED_CARD            = "expired_card"
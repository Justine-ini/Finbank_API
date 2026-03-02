from enum import Enum

class TransactionTypeEnum(str, Enum):
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    TRANSFER = "transfer"
    REVERSAL = "reversal"
    FEE_CHARGED = "fee_charged"
    LOAN_DISBURSEMENT = "loan_disbursement"
    LOAN_REPAYMENT = "loan_repayment"
    INTEREST_CREDITED = "interest_credited"

class TransactionStatusEnum(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REVERSED = "reversed"
    CANCELLED = "cancelled"


class TransactionCategoryEnum(str, Enum):
    CREDIT = "credit"
    DEBIT = "debit"

class TransactionFailureReasonEnum(str, Enum):
    INSUFFICIENT_FUNDS = "insufficient_funds"
    INVALID_OTP = "invalid_otp"
    OTP_EXPIRED = "otp_expired"
    CURRENCY_CONVERSION_FAILED = "currency_conversion_failed"
    ACCOUNT_INACTIVE = "account_inactive"
    INVALID_AMOUNT = "invalid_amount"
    INVALID_ACCOUNT = "invalid_account"
    SELF_TRANSFER = "self_transfer"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    SYSTEM_ERROR = "system_error"
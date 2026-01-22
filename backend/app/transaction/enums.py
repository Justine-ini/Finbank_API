from enum import Enum

class TransactionTypeEnum(Enum):
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    TRANSFER = "transfer"
    REVERSAL = "reversal"
    FEE_CHARGED = "fee_charged"
    LOAN_DISBURSEMENT = "loan_disbursement"
    LOAN_REPAYMENT = "loan_repayment"
    INTEREST_CREDITED = "interest_credited"

class TransactionStatusEnum(Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REVERSED = "reversed"
    CANCELLED = "cancelled"


class TransactionCategoryEnum(Enum):
    CREDIT = "credit"
    DEBIT = "debit"
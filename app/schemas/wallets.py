from datetime import datetime
from decimal import Decimal
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class OperationType(str, Enum):
    DEPOSIT = "DEPOSIT"
    WITHDRAW = "WITHDRAW"


class OperationRequest(BaseModel):
    operation_type: OperationType
    amount: Decimal = Field(..., gt=0, description="Amount must be positive")


class WalletCreateRequest(BaseModel):
    pass


class WalletResponse(BaseModel):
    id: UUID
    balance: Decimal
    model_config = ConfigDict(from_attributes=True)


class TransactionResponse(BaseModel):
    id: UUID
    wallet_id: UUID
    operation_type: OperationType
    amount: Decimal
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class TransactionListResponse(BaseModel):
    items: list[TransactionResponse]
    total: int

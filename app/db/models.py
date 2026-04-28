import enum
import uuid
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import DECIMAL, CheckConstraint, Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base


class OperationType(enum.Enum):
    DEPOSIT = "DEPOSIT"
    WITHDRAW = "WITHDRAW"

class Wallet(Base):

    __tablename__ = "wallets"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    balance: Mapped[Decimal] = mapped_column(DECIMAL(15, 2), default=Decimal("0.00"))
    transactions: Mapped[list["Transaction"]] = relationship(back_populates="wallet", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("balance >= 0", name="negative_balance_check"),
    )


class Transaction(Base):

    __tablename__ = "transactions"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    wallet_id: Mapped[UUID] = mapped_column(ForeignKey("wallets.id", ondelete="CASCADE"))
    operation_type: Mapped[OperationType] = mapped_column(Enum(OperationType), nullable=False)
    amount: Mapped[Decimal] = mapped_column(DECIMAL(15, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    wallet: Mapped["Wallet"] = relationship(back_populates="transactions")
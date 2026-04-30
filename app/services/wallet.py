from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import OperationType as DbOperationType
from app.db.models import Transaction, Wallet
from app.exceptions.wallet import InsufficientFundsError, WalletNotFoundError


class WalletService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_wallet(self, wallet_id: UUID) -> Wallet:
        wallet = await self.session.get(Wallet, wallet_id)
        if not wallet:
            raise WalletNotFoundError(f"Wallet {wallet_id} not found")
        return wallet

    async def apply_operation(
        self,
        wallet_id: UUID,
        operation_type: object,
        amount: Decimal
    ) -> Wallet:
        if isinstance(operation_type, DbOperationType):
            db_operation_type = operation_type
        else:
            op_value = getattr(operation_type, "value", operation_type)
            db_operation_type = DbOperationType(str(op_value))

        stmt = (
            select(Wallet)
            .where(Wallet.id == wallet_id)
            .with_for_update()
            .execution_options(populate_existing=True)
        )
        result = await self.session.execute(stmt)
        wallet = result.scalar_one_or_none()

        if not wallet:
            raise WalletNotFoundError(f"Wallet {wallet_id} not found")

        if db_operation_type == DbOperationType.WITHDRAW:
            if wallet.balance < amount:
                raise InsufficientFundsError(
                    f"Insufficient funds. Balance: {wallet.balance}, Request: {amount}"
                )
            wallet.balance -= amount
        elif db_operation_type == DbOperationType.DEPOSIT:
            wallet.balance += amount

        transaction = Transaction(
            wallet_id=wallet.id,
            operation_type=db_operation_type,
            amount=amount
        )
        self.session.add(transaction)
        await self.session.commit()
        await self.session.refresh(wallet)

        return wallet

    async def get_transactions(
            self,
            wallet_id: UUID,
            limit: int,
            offset: int
    ) -> tuple[list[Transaction], int]:
        await self.get_wallet(wallet_id)

        count_stmt = select(func.count()).select_from(Transaction).where(Transaction.wallet_id == wallet_id)
        total_result = await self.session.execute(count_stmt)
        total = total_result.scalar() or 0

        stmt = (
            select(Transaction)
            .where(Transaction.wallet_id == wallet_id)
            .order_by(Transaction.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        transactions = result.scalars().all()

        return list(transactions), total

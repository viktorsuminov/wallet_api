from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import OperationType, Transaction, Wallet
from app.exceptions.wallet import InsufficientFundsError, WalletNotFoundError


class WalletService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_wallet(self, wallet_id: UUID) -> Wallet:
        wallet = await self.session.get(Wallet, wallet_id)
        if not wallet:
            raise WalletNotFoundError(f"Wallet {wallet_id} not found")
        return wallet

    async def create_wallet(self) -> Wallet:
        async with self.session.begin():
            wallet = Wallet(balance=Decimal("0.00"))
            self.session.add(wallet)
        return wallet

    async def apply_operation(
        self,
        wallet_id: UUID,
        operation_type: OperationType,
        amount: Decimal
    ) -> Wallet:
        async with self.session.begin():
            stmt = select(Wallet).where(Wallet.id == wallet_id).with_for_update()
            result = await self.session.execute(stmt)
            wallet = result.scalar_one_or_none()

            if not wallet:
                raise WalletNotFoundError(f"Wallet {wallet_id} not found")

            if operation_type == OperationType.WITHDRAW:
                if wallet.balance < amount:
                    raise InsufficientFundsError(
                        f"InsufficientFundsError funds. Balance:{wallet.balance}, Request:{amount}"
                    )
                wallet.balance -= amount

            elif operation_type == OperationType.DEPOSIT:
                wallet.balance += amount

            transaction = Transaction(
                wallet_id=wallet.id,
                operation_type=operation_type,
                amount=amount
            )
            self.session.add(transaction)

        return wallet

    async def get_transactions(
            self,
            wallet_id: UUID,
            limit: int,
            offset: int
    ) -> tuple[list[Transaction], int]:
        await self.get_wallet(wallet_id)

        count_stmt = select(func.count()).where(Transaction.wallet_id == wallet_id)
        total_result = await self.session.execute(count_stmt)
        total = total_result.scalar()

        stmt = (
            select(Transaction)
            .where(Transaction.wallet_id == wallet_id)
            .order_by(Transaction.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        transaction = result.scalars().all()

        return list(transaction), total

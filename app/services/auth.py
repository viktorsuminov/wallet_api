from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import User, Wallet
from app.exceptions.auth import InvalidCredentialsError, UserAlreadyExistsError
from app.schemas.users import UserCreate
from app.security import hash_password, verify_password


class AuthService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def register_user(self, user_data: UserCreate) -> User:
        query = select(User).where(User.email == user_data.email)
        result = await self.session.execute(query)
        if result.scalar_one_or_none():
            raise UserAlreadyExistsError(f"User with email {user_data.email} already exists")

        new_user = User(
            email=user_data.email,
            hashed_password=hash_password(user_data.password)
        )
        self.session.add(new_user)
        await self.session.flush()

        new_wallet = Wallet(user_id=new_user.id)
        self.session.add(new_wallet)
        await self.session.commit()

        await self.session.refresh(new_user)
        return new_user

    async def get_user_by_id(self, user_id: UUID) -> User | None:
        stmt = (
            select(User)
            .where(User.id == user_id)
            .options(selectinload(User.wallet))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def authenticate_user(self, email: str, password: str) -> User:
        query = select(User).where(User.email == email)
        result = await self.session.execute(query)
        user = result.scalar_one_or_none()

        if not user or not verify_password(password, user.hashed_password):
            raise InvalidCredentialsError("Invalid email or password")

        return user

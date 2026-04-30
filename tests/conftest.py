import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.db.base import Base
from app.db.session import get_session
from app.main import app

engine = create_async_engine(
    settings.db_url,
    echo=False,
    pool_size=20,
    max_overflow=40,
    pool_pre_ping=True,
    future=True,
)

TestingSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

AppSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session():
    """Сессия без управления транзакциями — приложение само решает"""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        await session.rollback()  # Откат всех изменений теста
        await session.close()


@pytest_asyncio.fixture
async def client():
    async def override_get_session():
        async with AppSessionLocal() as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def auth_headers(client: AsyncClient, db_session: AsyncSession):
    from sqlalchemy import delete

    from app.db.models import User

    user_data = {"email": "test@example.com", "password": "password123"}

    await db_session.execute(delete(User).where(User.email == user_data["email"]))
    await db_session.commit()

    resp = await client.post("/api/v1/auth/register", json=user_data)
    if resp.status_code == 409:
        await db_session.execute(delete(User).where(User.email == user_data["email"]))
        await db_session.commit()
        resp = await client.post("/api/v1/auth/register", json=user_data)

    assert resp.status_code in (200, 201)

    login = await client.post("/api/v1/auth/login", json=user_data)
    assert login.status_code == 200

    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

from collections.abc import AsyncGenerator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings
from app.db.base import Base
from app.db.session import get_session
from app.main import app

# Используем базу из конфига (для ТЗ можно тестовую, но проще текущую)
engine = create_async_engine(settings.db_url)
TestingSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_db():
    """Создаем таблицы перед началом всех тестов и сносим после"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with TestingSessionLocal() as session:
        yield session

@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def _get_test_db():
        yield db_session

    app.dependency_overrides[get_session] = _get_test_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()

@pytest_asyncio.fixture
async def auth_headers(client: AsyncClient) -> dict:
    email = "test@example.com"
    password = "password123"

    await client.post("/api/v1/auth/register", json={"email": email, "password": password})

    response = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    token = response.json()["access_token"]

    return {"Authorization": f"Bearer {token}"}

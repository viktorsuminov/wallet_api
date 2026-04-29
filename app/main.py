from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1.auth import router as auth_router
from app.api.v1.wallets import router as wallets_router
from app.db.session import dispose_engine


@asynccontextmanager
async def lifespan(app:FastAPI):
    yield
    await dispose_engine()

app = FastAPI(
    title="Wallet API",
    description="Управление кошельком и транзакциями",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(auth_router, prefix="/api/v1")
app.include_router(wallets_router, prefix="/api/v1")

@app.get("/health", tags=["system"])
async def health_check():
    return{"status": "ok"}

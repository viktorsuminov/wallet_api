# tests/test_wallets.py
import asyncio

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_and_get_wallet(client: AsyncClient, auth_headers: dict):
    response = await client.get("/api/v1/wallets/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert float(data["balance"]) == 0.00


@pytest.mark.asyncio
async def test_insufficient_funds(client: AsyncClient, auth_headers: dict):
    response = await client.post(
        "/api/v1/wallets/me/operation",
        json={"operation_type": "WITHDRAW", "amount": 1000},
        headers=auth_headers
    )
    assert response.status_code == 400
    assert "Insufficient funds" in response.json()["detail"]


@pytest.mark.asyncio
async def test_concurrent_deposit(client: AsyncClient, auth_headers: dict):
    """
    Конкурентные депозиты.
    Важно: используем ОДИН client fixture, но запросы идут параллельно.
    Благодаря pool_size=20, каждый запрос получит своё соединение из пула.
    """
    amount_per_request = 100
    num_requests = 10

    async def make_deposit():
        response = await client.post(
            "/api/v1/wallets/me/operation",
            json={"operation_type": "DEPOSIT", "amount": amount_per_request},
            headers=auth_headers
        )
        return response.status_code

    results = await asyncio.gather(*[make_deposit() for _ in range(num_requests)])

    assert all(r == 200 for r in results), f"Failed: {results}"

    final = await client.get("/api/v1/wallets/me", headers=auth_headers)
    balance = float(final.json()["balance"])

    assert balance == amount_per_request * num_requests

import asyncio

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_and_get_wallet(client: AsyncClient, auth_headers: dict):
    response = await client.get("/api/v1/wallets/me", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["balance"] == "0.00"

@pytest.mark.asyncio
async def test_insufficient_funds(client: AsyncClient, auth_headers: dict):
    wallet_response = await client.get("/api/v1/wallets/me", headers=auth_headers)
    wallet_id = wallet_response.json()["id"]

    response = await client.post(
        f"/api/v1/wallets/{wallet_id}/operation",
        json={"operation_type": "WITHDRAW", "amount": 1000},
        headers=auth_headers
    )
    assert response.status_code == 400
    assert "Insufficient funds" in response.json()["detail"]

@pytest.mark.asyncio
async def test_concurrent_deposit(client: AsyncClient, auth_headers: dict):
    wallet_response = await client.get("/api/v1/wallets/me", headers=auth_headers)
    wallet_id = wallet_response.json()["id"]

    amount_per_request = 100
    num_requests = 10
    tasks = [
        client.post(
            f"/api/v1/wallets/{wallet_id}/operation",
            json={"operation_type": "DEPOSIT", "amount": amount_per_request},
            headers=auth_headers
        ) for _ in range(num_requests)
    ]
    responses = await asyncio.gather(*tasks)

    for resp in responses:
        assert resp.status_code == 200

    final_wallet = await client.get("/api/v1/wallets/me", headers=auth_headers)
    assert float(final_wallet.json()["balance"]) == amount_per_request * num_requests

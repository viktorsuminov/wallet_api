from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.exceptions.wallet import InsufficientFundsError, WalletNotFoundError
from app.schemas.wallets import OperationRequest, TransactionListResponse, WalletResponse
from app.services.wallet import WalletService

router = APIRouter(prefix="/wallets", tags=["wallets"])

async def get_wallet_service(db: AsyncSession = Depends(get_session)) -> WalletService:
    return WalletService(db)

@router.post("/", response_model=WalletResponse)
async def create_wallet(service: WalletService = Depends(get_wallet_service)):
    return await service.create_wallet()

@router.get("/{wallet_uuid}", response_model=WalletResponse)
async def get_wallet(
    wallet_uuid: UUID = Path(..., description="UUID кошелька"),
    service: WalletService = Depends(get_wallet_service)
):
    try:
        return await service.get_wallet(wallet_uuid)
    except WalletNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e

@router.post("/{wallet_uuid}/operation", response_model=WalletResponse)
async def perform_operation(
    wallet_uuid: UUID = Path(..., description="UUID кошелька"),
    operation_data: OperationRequest = ...,
    service: WalletService = Depends(get_wallet_service)
):
    try:
        return await service.apply_operation(
            wallet_id=wallet_uuid,
            operation_type=operation_data.operation_type,
            amount=operation_data.amount
        )
    except WalletNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except InsufficientFundsError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

@router.get("/{wallet_uuid}/transactions", response_model=TransactionListResponse)
async def get_transactions(
    wallet_uuid: UUID = Path(...),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    service: WalletService = Depends(get_wallet_service)
):
    try:
        transactions, total = await service.get_transactions(wallet_uuid, limit, offset)
        return TransactionListResponse(items=transactions, total=total)
    except WalletNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e

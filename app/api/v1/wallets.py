from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.models import User
from app.db.session import get_session
from app.exceptions.wallet import InsufficientFundsError, WalletNotFoundError
from app.schemas.wallets import OperationRequest, TransactionListResponse, WalletResponse
from app.services.wallet import WalletService

router = APIRouter(prefix="/wallets", tags=["wallets"])

async def get_wallet_service(db: AsyncSession = Depends(get_session)) -> WalletService:
    return WalletService(db)

@router.get("/me", response_model=WalletResponse)
async def get_my_wallet(
    current_user: User = Depends(get_current_user)
):
    return current_user.wallet

@router.post("/{wallet_uuid}/operation", response_model=WalletResponse)
async def perform_operation(
    operation_data: OperationRequest,
    wallet_uuid: UUID = Path(..., description="UUID кошелька"),
    current_user: User = Depends(get_current_user),
    service: WalletService = Depends(get_wallet_service)
):
    if current_user.wallet.id != wallet_uuid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="You don't have access to this wallet"
        ) from None

    try:
        return await service.apply_operation(
            wallet_id=wallet_uuid,
            operation_type=operation_data.operation_type,
            amount=operation_data.amount
        )
    except WalletNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except InsufficientFundsError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

@router.get("/{wallet_uuid}/transactions", response_model=TransactionListResponse)
async def get_transactions(
    wallet_uuid: UUID = Path(...),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    service: WalletService = Depends(get_wallet_service)
):
    if current_user.wallet.id != wallet_uuid:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied") from None

    try:
        transactions, total = await service.get_transactions(wallet_uuid, limit, offset)
        return TransactionListResponse(items=transactions, total=total)
    except WalletNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e

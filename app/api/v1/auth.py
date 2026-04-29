from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.exceptions.auth import InvalidCredentialsError, UserAlreadyExistsError
from app.schemas.users import Token, UserCreate, UserLogin, UserResponse
from app.security import create_access_token
from app.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])

async def get_auth_service(db: AsyncSession = Depends(get_session)) -> AuthService:
    return AuthService(db)

@router.post("/register", response_model=UserResponse, status_code=201)
async def register(
    user_data: UserCreate,
    service: AuthService = Depends(get_auth_service)
):
    try:
        return await service.register_user(user_data)
    except UserAlreadyExistsError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

@router.post("/login", response_model=Token)
async def login(
    login_data: UserLogin,
    service: AuthService = Depends(get_auth_service)
):
    try:
        user = await service.authenticate_user(login_data.email, login_data.password)
        access_token = create_access_token(data={"user_id": user.id})
        return {"access_token": access_token, "token_type": "bearer"}
    except InvalidCredentialsError as e:
        raise HTTPException(status_code=401, detail=str(e)) from e

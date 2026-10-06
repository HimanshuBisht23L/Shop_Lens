
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_db
from db.models.users import User  

from apis.v1.schemas.auth import (
    RegisterRequest,
    UserResponse,
    TokenResponse,
    LoginRequest,
)

from core.security import (
    hash_password,
    verify_password,
    create_access_token,
)

from core.dependencies import get_current_user

router = APIRouter(
    prefix="/auth",
    tags=["authentication"],
)


@router.post(
    "/register", 
    response_model=UserResponse, 
    status_code=status.HTTP_201_CREATED,
)
async def register_user(data : RegisterRequest, db: AsyncSession =  Depends(get_db)) :
    result = await db.execute(
        select(User).where(
            User.email == data.email
        )
    )

    existing_user = result.scalar_one_or_none()

    if(existing_user):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    user = User(
        full_name=data.full_name,
        email=data.email,
        password_hash=hash_password(data.password),
        is_active=True,
    )

    db.add(user)

    await db.commit()
    await db.refresh(user)

    return user



@router.post(
    "/login",
    response_model=TokenResponse,
)
async def login_user( data: LoginRequest, db : AsyncSession = Depends(get_db) ):
    result = await db.execute(
        select(User).where(
            User.email == data.email
        )
    )

    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not verify_password(data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    access_token = create_access_token(user_id = user.id)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user,
    }


# CURRENT USER
@router.get("/me",response_model = UserResponse)
async def get_me(current_user: User = Depends(get_current_user) ):
    return current_user


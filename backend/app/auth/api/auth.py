from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.auth.schemas.auth import (
    UserSignup,
    UserLogin,
    UserResponse,
    TokenResponse,
)
from app.auth.service.auth_service import AuthService
from app.user.dependencies import get_current_user

router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication"],
)


auth_service = AuthService()


@router.post(
    "/signup",
    response_model=UserResponse,
)
def signup(
    request: UserSignup,
    db: Session = Depends(get_db),
):
    return auth_service.signup(
        db,
        request,
    )


@router.post(
    "/login",
    response_model=TokenResponse,
)
def login(
    request: UserLogin,
    db: Session = Depends(get_db),
):
    access_token = auth_service.login(
        db,
        request,
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }

@router.get("/me", response_model=UserResponse)
def get_me(current_user=Depends(get_current_user)):
    return current_user
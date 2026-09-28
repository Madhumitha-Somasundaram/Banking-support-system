from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.user.model.user import User
from app.user.repository.user_repository import UserRepository
from app.auth.schemas.auth import UserSignup, UserLogin
from shared.jwt import (
    hash_password,
    verify_password,
    create_access_token,
)


class AuthService:

    def __init__(self):
        self.user_repository = UserRepository()

    def signup(
        self,
        db: Session,
        request: UserSignup,
    ):

        existing_user = self.user_repository.get_by_email(
            db,
            request.email,
        )

        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User already exists",
            )

        hashed_password = hash_password(
            request.password
        )

        user = User(
            email=request.email,
            password_hash=hashed_password,
            name=request.name,
            role="CUSTOMER",
        )

        return self.user_repository.create(
            db,
            user,
        )

    def login(
        self,
        db: Session,
        request: UserLogin,
    ):

        user = self.user_repository.get_by_email(
            db,
            request.email,
        )

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        if not verify_password(
            request.password,
            user.password_hash,
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        access_token = create_access_token(
            user.id
        )

        return access_token
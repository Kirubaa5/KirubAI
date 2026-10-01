from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from models.user import User
from schemas.user import UserCreate, LoginRequest
from utils.security import hash_password, verify_password, create_access_token


class AuthService:
    @staticmethod
    def register(db: Session, data: UserCreate) -> tuple[User, str]:
        """Register a new user and return (user, access_token)."""
        normalized_email = data.email.strip().lower()
        existing = db.query(User).filter(User.email == normalized_email).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with this email already exists",
            )

        user = User(
            email=normalized_email,
            hashed_password=hash_password(data.password),
            full_name=data.full_name.strip(),
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        token = create_access_token({"sub": str(user.id), "email": user.email})
        return user, token

    @staticmethod
    def login(db: Session, data: LoginRequest) -> tuple[User, str]:
        """Authenticate user and return (user, access_token)."""
        normalized_email = data.email.strip().lower()
        user = db.query(User).filter(User.email == normalized_email).first()
        if not user or not verify_password(data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive",
            )

        token = create_access_token({"sub": str(user.id), "email": user.email})
        return user, token

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import verify_password, create_access_token
from app.schemas.user import UserCreate, UserLogin, UserResponse, Token
from app.services import UserService

router = APIRouter()


@router.post('/register', response_model=UserResponse)
def register(data: UserCreate, db: Session = Depends(get_db)):
    svc = UserService(db)
    if svc.get_by_email(data.email):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Email already registered')
    user = svc.create(data)
    return user


@router.post('/login', response_model=Token)
def login(data: UserLogin, db: Session = Depends(get_db)):
    svc = UserService(db)
    user = svc.get_by_email(data.email)
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Incorrect email or password',
        )
    token = create_access_token(data={'sub': str(user.id)})
    return Token(access_token=token)

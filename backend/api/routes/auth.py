import os
import uuid
from typing import Dict
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, Header
from fastapi.security import APIKeyHeader
import bcrypt
from jose import JWTError, jwt

from infrastructure import db
from core.schemas import UserSignup, UserLogin, Token, UserResponse

router = APIRouter(prefix="/auth", tags=["auth"])

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "tangent-super-secret-key-000")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7 # 1 week

def get_password_hash(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(plain_password, hashed_password):
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# --- Auth Endpoints ---
@router.post("/signup", response_model=Token)
async def signup(user: UserSignup):
    if db.get_user_by_email(user.email):
        raise HTTPException(status_code=400, detail="Email already registered.")

    user_id = f"user_{uuid.uuid4().hex[:8]}"
    hashed_pwd = get_password_hash(user.password)

    success = db.create_user(
        user_id=user_id,
        email=user.email,
        hashed_password=hashed_pwd,
        first_name=user.first_name,
        last_name=user.last_name,
    )

    if not success:
        raise HTTPException(status_code=500, detail="Failed to create user.")

    access_token = create_access_token(data={"sub": user.email, "user_id": user_id})
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/login", response_model=Token)
async def login(user: UserLogin):
    db_user = db.get_user_by_email(user.email)
    if not db_user or not verify_password(user.password, db_user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    access_token = create_access_token(data={"sub": db_user["email"], "user_id": db_user["id"]})
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserResponse)
async def get_me(token: str = Query(...)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid token.")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token.")

    db_user = db.get_user_by_email(email)
    if not db_user:
        raise HTTPException(status_code=401, detail="User not found.")

    return {
        "id": db_user["id"],
        "email": db_user["email"],
        "first_name": db_user["first_name"] or "",
        "last_name": db_user["last_name"] or "",
        "tenant_id": db_user["tenant_id"]
    }

# --- Security Dependency ---
def get_current_user(
    authorization: str = Header(None),
):
    """JWT-based user auth. Expects 'Authorization: Bearer <token>' header."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated. Provide Authorization: Bearer <token> header.")
    token = authorization[7:]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("user_id")
        email: str = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token.")
        return {"user_id": user_id, "email": email}
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token.")

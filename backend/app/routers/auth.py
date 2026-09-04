from fastapi import APIRouter, HTTPException, Depends, status
from datetime import datetime
from uuid import uuid4
from app.database import get_database
from app.schemas.auth import UserSignup, UserLogin, TokenResponse, UserResponse, ForgotPasswordRequest
from app.services.auth_service import hash_password, verify_password, create_access_token, get_current_user

router = APIRouter(prefix="/api/auth", tags=["Auth"])

@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def signup(user_data: UserSignup):
    db = get_database()
    
    # Check if email already exists
    existing = await db.users.find_one({"email": user_data.email.lower()})
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists."
        )

    user_doc = {
        "user_id": str(uuid4()),
        "full_name": user_data.full_name,
        "email": user_data.email.lower(),
        "phone": user_data.phone,
        "organization_type": user_data.organization_type,
        "role": "officer",  # Backend enforced role
        "hashed_password": hash_password(user_data.password),
        "created_at": datetime.utcnow()
    }

    await db.users.insert_one(user_doc)

    return UserResponse(
        user_id=user_doc["user_id"],
        full_name=user_doc["full_name"],
        email=user_doc["email"],
        phone=user_doc["phone"],
        organization_type=user_doc["organization_type"],
        role=user_doc["role"],
        created_at=user_doc["created_at"]
    )

@router.post("/login", response_model=TokenResponse)
async def login(credentials: UserLogin):
    db = get_database()
    
    user = await db.users.find_one({"email": credentials.email.lower()})
    if not user or not verify_password(credentials.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid official email or password."
        )

    role = user.get("role", "officer")
    token = create_access_token({
        "user_id": user["user_id"],
        "sub": user["user_id"],
        "email": user["email"],
        "role": role
    })
    
    user_resp = UserResponse(
        user_id=user["user_id"],
        full_name=user["full_name"],
        email=user["email"],
        phone=user["phone"],
        organization_type=user["organization_type"],
        role=role,
        created_at=user["created_at"]
    )

    return TokenResponse(access_token=token, user=user_resp)

@router.get("/me", response_model=UserResponse)
async def get_me(user: dict = Depends(get_current_user)):
    return UserResponse(
        user_id=user["user_id"],
        full_name=user["full_name"],
        email=user["email"],
        phone=user["phone"],
        organization_type=user["organization_type"],
        role=user.get("role", "officer"),
        created_at=user["created_at"]
    )

@router.post("/forgot-password")
async def forgot_password(req: ForgotPasswordRequest):
    return {"message": "If an institutional account exists for this email address, reset instructions have been dispatched."}

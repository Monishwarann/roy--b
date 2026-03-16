from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer
from datetime import datetime
from database import get_users_collection
from models.schemas import UserSignup, UserLogin, Token, UserOut
from models.auth import hash_password, verify_password, create_access_token, decode_access_token

router = APIRouter(prefix="/auth", tags=["Authentication"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


@router.post("/signup", response_model=dict, status_code=201)
async def signup(user: UserSignup):
    users = get_users_collection()

    # Check if email already exists
    existing = await users.find_one({"email": user.email})
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Check if username already taken
    existing_username = await users.find_one({"username": user.username})
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )

    hashed = hash_password(user.password)
    new_user = {
        "username": user.username,
        "email": user.email,
        "password": hashed,
        "created_at": datetime.utcnow()
    }

    await users.insert_one(new_user)
    token = create_access_token({"sub": user.email})

    return {
        "message": "Account created successfully",
        "access_token": token,
        "token_type": "bearer",
        "username": user.username,
        "email": user.email
    }


@router.post("/login", response_model=dict)
async def login(user: UserLogin):
    users = get_users_collection()

    db_user = await users.find_one({"email": user.email})
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    if not verify_password(user.password, db_user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    token = create_access_token({"sub": user.email})

    return {
        "message": "Login successful",
        "access_token": token,
        "token_type": "bearer",
        "username": db_user["username"],
        "email": db_user["email"]
    }


async def get_current_user(token: str = Depends(oauth2_scheme)):
    email = decode_access_token(token)
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    users = get_users_collection()
    user = await users.find_one({"email": email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.get("/profile", response_model=dict)
async def get_profile(current_user: dict = Depends(get_current_user)):
    return {
        "username": current_user["username"],
        "email": current_user["email"],
        "created_at": str(current_user.get("created_at", ""))
    }

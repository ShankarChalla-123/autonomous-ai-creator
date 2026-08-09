import os
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

import jwt
from dotenv import load_dotenv
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pwdlib import PasswordHash
from pwdlib.hashers.bcrypt import BcryptHasher
from pydantic import BaseModel, EmailStr, Field

load_dotenv()

# ==========================================
# CONFIGURATION
# ==========================================

DATABASE_PATH = os.getenv(
    "DATABASE_PATH",
    str(Path(__file__).resolve().parent / "users.db"),
)

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")

if not JWT_SECRET_KEY:
    raise ValueError("JWT_SECRET_KEY is missing from .env")

JWT_ALGORITHM = "HS256"


def _env_int(name, default):
    try:
        return int(os.getenv(name, str(default)))
    except (TypeError, ValueError):
        return default


JWT_EXPIRE_MINUTES = _env_int("JWT_EXPIRE_MINUTES", 60 * 24)

PASSWORD_MIN_LENGTH = 8
PASSWORD_MAX_LENGTH = 128

# ==========================================
# PASSWORD HASHING (bcrypt via pwdlib)
# ==========================================

password_hash = PasswordHash(hashers=[BcryptHasher()])


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, password_hash_str: str) -> bool:
    try:
        return password_hash.verify(password, password_hash_str)
    except (ValueError, TypeError):
        return False


# ==========================================
# DATABASE
# ==========================================

def get_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    if DATABASE_PATH != ":memory:":
        Path(DATABASE_PATH).parent.mkdir(parents=True, exist_ok=True)
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )


init_db()


def create_user(email: str, password: str) -> sqlite3.Row:
    now = datetime.now(timezone.utc).isoformat()
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO users (email, password_hash, created_at)
            VALUES (?, ?, ?)
            """,
            (email, hash_password(password), now),
        )
        user = conn.execute(
            "SELECT * FROM users WHERE id = ?", (cursor.lastrowid,)
        ).fetchone()
    return user


def get_user_by_email(email: str):
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM users WHERE email = ?", (email,)
        ).fetchone()


# ==========================================
# JWT TOKENS
# ==========================================

def create_access_token(email: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": email,
        "iat": now,
        "exp": now + timedelta(minutes=JWT_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    return jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])


# ==========================================
# CURRENT USER DEPENDENCY
# ==========================================

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> sqlite3.Row:
    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated. Please log in.",
        )
    try:
        payload = decode_access_token(credentials.credentials)
        email = payload.get("sub")
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token. Please log in again.",
        )
    if not email:
        raise HTTPException(
            status_code=401,
            detail="Invalid token. Please log in again.",
        )
    user = get_user_by_email(email)
    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Account no longer exists. Please register again.",
        )
    return user


# ==========================================
# REQUEST / RESPONSE MODELS
# ==========================================

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(
        min_length=PASSWORD_MIN_LENGTH,
        max_length=PASSWORD_MAX_LENGTH,
    )


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=PASSWORD_MAX_LENGTH)

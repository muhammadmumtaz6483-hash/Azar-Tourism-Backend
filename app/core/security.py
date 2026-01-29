from datetime import datetime, timedelta
from jose import jwt
from passlib.context import CryptContext
from core.confiq import SECRET_KEY, ALGORITHM


pwd_context = CryptContext(
    schemes=["argon2"],   # ✅ ONLY argon2
    deprecated="auto"
)

# ✅ Hash Password
def hash_password(password: str) -> str:

    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters")

    if len(password) > 128:
        raise ValueError("Password too long (max 128 characters)")

    return pwd_context.hash(password)


# ✅ Verify Password
def verify_password(password: str, hashed: str) -> bool:
    try:
        return pwd_context.verify(password, hashed)
    except Exception:
        return False


# ✅ Access Token
def create_access_token(data: dict, minutes: int):

    payload = data.copy()
    payload["exp"] = datetime.utcnow() + timedelta(minutes=minutes)

    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


# ✅ Refresh Token
def create_refresh_token(data: dict, days: int):

    payload = data.copy()
    payload["exp"] = datetime.utcnow() + timedelta(days=days)

    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

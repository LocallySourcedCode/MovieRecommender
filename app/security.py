from datetime import datetime, timedelta
from jose import jwt
from passlib.context import CryptContext

# Use pbkdf2_sha256 to avoid OS-specific bcrypt issues and 72-byte limits
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

JWT_SECRET = "CHANGE_ME_IN_PROD"
JWT_ALG = "HS256"
JWT_EXPIRES_MIN = 60

def hash_password(p: str) -> str:
    return pwd_context.hash(p)

def verify_password(p: str, h: str) -> bool:
    return pwd_context.verify(p, h)

def create_token(sub: str) -> str:
    payload = {"sub": sub, "exp": datetime.utcnow() + timedelta(minutes=JWT_EXPIRES_MIN)}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)

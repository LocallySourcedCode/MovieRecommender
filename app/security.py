from datetime import datetime, timedelta, timezone
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
    # Use timezone-aware timestamp for JWT exp to avoid deprecation warnings
    exp_dt = datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRES_MIN)
    payload = {"sub": sub, "exp": int(exp_dt.timestamp())}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)


# ---- New helpers for mixed identity model ----

def create_user_token(user_id: int) -> str:
    """Issue a JWT where subject is the user id (backwards compatible)."""
    return create_token(str(user_id))


def create_participant_token(participant_id: int) -> str:
    """Issue a JWT where subject encodes a participant principal."""
    return create_token(f"participant:{participant_id}")


def parse_subject(sub: str):
    """Parse JWT subject and discriminate between user and participant tokens.

    Returns a tuple (kind, id). kind in {"user", "participant", "unknown"}.
    """
    try:
        if isinstance(sub, str) and sub.startswith("participant:"):
            _, pid = sub.split(":", 1)
            return "participant", int(pid)
        # fall back to integer-only user id
        return "user", int(sub)
    except Exception:
        return "unknown", None

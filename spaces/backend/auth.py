"""JWT creation and verification."""
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

from config import JWT_ALG, JWT_EXPIRE_HOURS, JWT_SECRET


def create_token(username: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRE_HOURS)
    return jwt.encode(
        {"sub": username, "exp": expire},
        JWT_SECRET,
        algorithm=JWT_ALG,
    )


def verify_token(token: str) -> str | None:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
        sub = payload.get("sub")
        return str(sub) if sub else None
    except JWTError:
        return None

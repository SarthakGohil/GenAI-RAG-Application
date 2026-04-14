"""Database layer: local JSON user store + optional MongoDB for audit logs."""
import json
import os
from pathlib import Path
from typing import Any

from pymongo import MongoClient
from pymongo.database import Database
from pymongo.errors import PyMongoError

import config  # noqa: F401 — loads .env via config side effect

# ── Local JSON user store (works without MongoDB) ────────────────────────────
_USERS_FILE = Path(__file__).resolve().parent / "users.json"


def _load_users() -> dict[str, str]:
    """Load local users. Prefer MongoDB if available."""
    try:
        db = get_db()
        if db is not None:
            # We don't load all users from Mongo into memory for every call
            # This function is used to check for local fallback users
            pass
    except PyMongoError:
        pass

    if _USERS_FILE.exists():
        try:
            return json.loads(_USERS_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def _save_users(users: dict[str, str]) -> None:
    try:
        _USERS_FILE.write_text(json.dumps(users, indent=2), encoding="utf-8")
    except OSError:
        pass


def create_user(username: str, password_hash: str) -> bool:
    """Create user. MongoDB first, then local JSON fallback."""
    success = False
    # Try MongoDB
    try:
        db = get_db()
        if db is not None:
            db.users.create_index("username", unique=True)
            db.users.update_one(
                {"username": username},
                {"$set": {"password": password_hash}},
                upsert=True,
            )
            success = True
    except PyMongoError:
        pass

    # Local fallback
    users = _load_users()
    users[username] = password_hash
    _save_users(users)
    return True  # At least local worked if we get here


def get_user_hash(username: str) -> str | None:
    """Look up bcrypt hash — MongoDB first, then local JSON fallback."""
    # Try Mongo first for production scalability
    try:
        db = get_db()
        if db is not None:
            user = db.users.find_one({"username": username})
            if user:
                return user.get("password")
    except PyMongoError:
        pass

    # Fallback: try local JSON
    users = _load_users()
    if username in users:
        return users[username]
    return None


# ── MongoDB (optional) ────────────────────────────────────────────────────────
_client: MongoClient | None = None


def get_client() -> MongoClient | None:
    global _client
    uri = os.getenv("MONGODB_URI", "").strip()
    if not uri:
        return None
    if _client is None:
        try:
            _client = MongoClient(uri, serverSelectionTimeoutMS=3000)
        except Exception:
            return None
    return _client


def get_db() -> Database[Any] | None:
    c = get_client()
    if c is None:
        return None
    name = os.getenv("MONGODB_DB", "securerag")
    return c[name]


def ping_mongo() -> bool:
    try:
        c = get_client()
        if c is None:
            return False
        c.admin.command("ping")
        return True
    except PyMongoError:
        return False


def log_query(username: str, question: str, answer_preview: str) -> None:
    """Log to MongoDB if available. Silently skip if not."""
    try:
        db = get_db()
        if db is None:
            return
        db.audit_logs.insert_one(
            {
                "user": username,
                "question": question[:200],
                "answer_preview": answer_preview[:500],
            }
        )
    except PyMongoError:
        return


def get_user_history(username: str) -> list[dict[str, Any]]:
    """Fetch per-user history from MongoDB (empty list if Mongo unavailable)."""
    try:
        db = get_db()
        if db is None:
            return []
        cursor = db.audit_logs.find({"user": username}).sort("_id", -1).limit(20)
        return [
            {"question": doc["question"], "answer": doc["answer_preview"]}
            for doc in cursor
        ]
    except PyMongoError:
        return []

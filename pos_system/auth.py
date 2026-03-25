"""
Authentication module: login, user management, and role checks.
"""
import hashlib
from dataclasses import dataclass
from typing import Optional
from .database import get_connection


def _hash(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


@dataclass
class User:
    id: int
    username: str
    role: str
    full_name: str


_current_user: Optional[User] = None


def login(username: str, password: str) -> Optional[User]:
    """Verify credentials and return a User on success, None on failure."""
    global _current_user
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM users WHERE username=? AND password=? AND active=1",
        (username, _hash(password)),
    ).fetchone()
    conn.close()
    if row:
        _current_user = User(row["id"], row["username"], row["role"], row["full_name"])
        return _current_user
    return None


def logout() -> None:
    global _current_user
    _current_user = None


def current_user() -> Optional[User]:
    return _current_user


def is_admin() -> bool:
    return _current_user is not None and _current_user.role == "admin"


# ── User CRUD ────────────────────────────────────────────────────────────────

def list_users():
    conn = get_connection()
    rows = conn.execute(
        "SELECT id, username, role, full_name, active FROM users ORDER BY username"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def create_user(username: str, password: str, role: str, full_name: str) -> int:
    conn = get_connection()
    cur = conn.execute(
        "INSERT INTO users (username, password, role, full_name) VALUES (?,?,?,?)",
        (username, _hash(password), role, full_name),
    )
    conn.commit()
    conn.close()
    return cur.lastrowid


def update_user(user_id: int, role: str, full_name: str, active: int) -> None:
    conn = get_connection()
    conn.execute(
        "UPDATE users SET role=?, full_name=?, active=? WHERE id=?",
        (role, full_name, active, user_id),
    )
    conn.commit()
    conn.close()


def change_password(user_id: int, new_password: str) -> None:
    conn = get_connection()
    conn.execute("UPDATE users SET password=? WHERE id=?", (_hash(new_password), user_id))
    conn.commit()
    conn.close()


def delete_user(user_id: int) -> None:
    conn = get_connection()
    conn.execute("DELETE FROM users WHERE id=?", (user_id,))
    conn.commit()
    conn.close()

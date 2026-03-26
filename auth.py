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
    can_manage_products: bool = False
    can_manage_customers: bool = False
    can_view_reports: bool = False
    can_manage_users: bool = False
    can_apply_discounts: bool = True
    can_delete_receipts: bool = False
    can_delete_all_receipts: bool = False


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
        _current_user = User(
            row["id"],
            row["username"],
            row["role"],
            row["full_name"],
            bool(row["can_manage_products"]),
            bool(row["can_manage_customers"]),
            bool(row["can_view_reports"]),
            bool(row["can_manage_users"]),
            bool(row["can_apply_discounts"]),
            bool(row["can_delete_receipts"]),
            bool(row["can_delete_all_receipts"]),
        )
        return _current_user
    return None


def logout() -> None:
    global _current_user
    _current_user = None


def current_user() -> Optional[User]:
    return _current_user


def is_admin() -> bool:
    return _current_user is not None and _current_user.role == "admin"


def can(permission: str) -> bool:
    if _current_user is None:
        return False
    if _current_user.role == "admin":
        return True
    mapping = {
        "manage_products": _current_user.can_manage_products,
        "manage_customers": _current_user.can_manage_customers,
        "view_reports": _current_user.can_view_reports,
        "manage_users": _current_user.can_manage_users,
        "apply_discounts": _current_user.can_apply_discounts,
        "delete_receipts": _current_user.can_delete_receipts,
        "delete_all_receipts": _current_user.can_delete_all_receipts,
    }
    return bool(mapping.get(permission, False))


# ── User CRUD ────────────────────────────────────────────────────────────────

def list_users():
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT id, username, role, full_name,
               can_manage_products, can_manage_customers,
               can_view_reports, can_manage_users, can_apply_discounts,
               can_delete_receipts, can_delete_all_receipts,
               active
        FROM users
        ORDER BY username
        """
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def create_user(username: str, password: str, role: str, full_name: str, permissions: Optional[dict] = None) -> int:
    permissions = permissions or {}
    can_manage_products = int(bool(permissions.get("can_manage_products", role == "admin")))
    can_manage_customers = int(bool(permissions.get("can_manage_customers", role == "admin")))
    can_view_reports = int(bool(permissions.get("can_view_reports", role == "admin")))
    can_manage_users = int(bool(permissions.get("can_manage_users", role == "admin")))
    can_apply_discounts = int(bool(permissions.get("can_apply_discounts", True if role != "admin" else True)))
    can_delete_receipts = int(bool(permissions.get("can_delete_receipts", role == "admin")))
    can_delete_all_receipts = int(bool(permissions.get("can_delete_all_receipts", role == "admin")))
    conn = get_connection()
    cur = conn.execute(
        """
        INSERT INTO users (
            username, password, role, full_name,
            can_manage_products, can_manage_customers,
            can_view_reports, can_manage_users, can_apply_discounts,
            can_delete_receipts, can_delete_all_receipts
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            username,
            _hash(password),
            role,
            full_name,
            can_manage_products,
            can_manage_customers,
            can_view_reports,
            can_manage_users,
            can_apply_discounts,
            can_delete_receipts,
            can_delete_all_receipts,
        ),
    )
    conn.commit()
    conn.close()
    return cur.lastrowid


def update_user(user_id: int, role: str, full_name: str, active: int, permissions: Optional[dict] = None) -> None:
    permissions = permissions or {}
    can_manage_products = int(bool(permissions.get("can_manage_products", role == "admin")))
    can_manage_customers = int(bool(permissions.get("can_manage_customers", role == "admin")))
    can_view_reports = int(bool(permissions.get("can_view_reports", role == "admin")))
    can_manage_users = int(bool(permissions.get("can_manage_users", role == "admin")))
    can_apply_discounts = int(bool(permissions.get("can_apply_discounts", True if role != "admin" else True)))
    can_delete_receipts = int(bool(permissions.get("can_delete_receipts", role == "admin")))
    can_delete_all_receipts = int(bool(permissions.get("can_delete_all_receipts", role == "admin")))
    conn = get_connection()
    conn.execute(
        """
        UPDATE users
        SET role=?, full_name=?, active=?,
            can_manage_products=?, can_manage_customers=?,
            can_view_reports=?, can_manage_users=?, can_apply_discounts=?,
            can_delete_receipts=?, can_delete_all_receipts=?
        WHERE id=?
        """,
        (
            role,
            full_name,
            active,
            can_manage_products,
            can_manage_customers,
            can_view_reports,
            can_manage_users,
            can_apply_discounts,
            can_delete_receipts,
            can_delete_all_receipts,
            user_id,
        ),
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

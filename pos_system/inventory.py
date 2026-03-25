"""
Inventory / product management module.
"""
from typing import Optional, List, Dict, Any
from .database import get_connection


# ── Categories ────────────────────────────────────────────────────────────────

def list_categories() -> List[Dict]:
    conn = get_connection()
    rows = conn.execute("SELECT * FROM categories ORDER BY name").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_category(name: str) -> int:
    conn = get_connection()
    cur = conn.execute("INSERT INTO categories (name) VALUES (?)", (name,))
    conn.commit()
    conn.close()
    return cur.lastrowid


def delete_category(cat_id: int) -> None:
    conn = get_connection()
    conn.execute("DELETE FROM categories WHERE id=?", (cat_id,))
    conn.commit()
    conn.close()


# ── Products ─────────────────────────────────────────────────────────────────

def list_products(search: str = "", category_id: Optional[int] = None,
                  active_only: bool = True) -> List[Dict]:
    query = """
        SELECT p.*, c.name AS category_name
        FROM products p
        LEFT JOIN categories c ON p.category_id = c.id
        WHERE 1=1
    """
    params: list = []
    if active_only:
        query += " AND p.active=1"
    if search:
        query += " AND (p.name LIKE ? OR p.barcode LIKE ? OR p.description LIKE ?)"
        s = f"%{search}%"
        params.extend([s, s, s])
    if category_id is not None:
        query += " AND p.category_id=?"
        params.append(category_id)
    query += " ORDER BY p.name"
    conn = get_connection()
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_product(product_id: int) -> Optional[Dict]:
    conn = get_connection()
    row = conn.execute(
        "SELECT p.*, c.name AS category_name FROM products p "
        "LEFT JOIN categories c ON p.category_id=c.id WHERE p.id=?",
        (product_id,),
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def get_product_by_barcode(barcode: str) -> Optional[Dict]:
    conn = get_connection()
    row = conn.execute(
        "SELECT p.*, c.name AS category_name FROM products p "
        "LEFT JOIN categories c ON p.category_id=c.id WHERE p.barcode=? AND p.active=1",
        (barcode,),
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def add_product(
    name: str,
    price: float,
    cost: float = 0,
    stock: int = 0,
    min_stock: int = 5,
    barcode: str = "",
    description: str = "",
    category_id: Optional[int] = None,
    unit: str = "pza",
) -> int:
    conn = get_connection()
    cur = conn.execute(
        """INSERT INTO products
           (name, price, cost, stock, min_stock, barcode, description, category_id, unit)
           VALUES (?,?,?,?,?,?,?,?,?)""",
        (name, price, cost, stock, min_stock, barcode or None, description, category_id, unit),
    )
    conn.commit()
    conn.close()
    return cur.lastrowid


def update_product(
    product_id: int,
    name: str,
    price: float,
    cost: float,
    stock: int,
    min_stock: int,
    barcode: str,
    description: str,
    category_id: Optional[int],
    unit: str,
    active: int = 1,
) -> None:
    conn = get_connection()
    conn.execute(
        """UPDATE products SET name=?, price=?, cost=?, stock=?, min_stock=?,
           barcode=?, description=?, category_id=?, unit=?, active=?
           WHERE id=?""",
        (name, price, cost, stock, min_stock, barcode or None,
         description, category_id, unit, active, product_id),
    )
    conn.commit()
    conn.close()


def delete_product(product_id: int) -> None:
    """Soft-delete: mark as inactive."""
    conn = get_connection()
    conn.execute("UPDATE products SET active=0 WHERE id=?", (product_id,))
    conn.commit()
    conn.close()


def adjust_stock(product_id: int, delta: int) -> None:
    """Add *delta* units to stock (use negative delta to subtract)."""
    conn = get_connection()
    conn.execute("UPDATE products SET stock = stock + ? WHERE id=?", (delta, product_id))
    conn.commit()
    conn.close()


def low_stock_products() -> List[Dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM products WHERE active=1 AND stock <= min_stock ORDER BY stock"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

"""
Sales processing module: cart management and transaction recording.
"""
import datetime
from dataclasses import dataclass, field
from typing import List, Optional, Dict
from .database import get_connection, get_setting


@dataclass
class CartItem:
    product_id: int
    name: str
    quantity: float
    unit_price: float
    discount: float = 0.0  # percentage 0-100

    @property
    def subtotal(self) -> float:
        return round(self.quantity * self.unit_price * (1 - self.discount / 100), 2)


@dataclass
class Cart:
    items: List[CartItem] = field(default_factory=list)
    customer_id: Optional[int] = None
    discount: float = 0.0       # global percentage discount 0-100
    payment_method: str = "cash"
    amount_paid: float = 0.0
    notes: str = ""

    def add_item(self, product_id: int, name: str, unit_price: float,
                 quantity: float = 1, item_discount: float = 0) -> None:
        for item in self.items:
            if item.product_id == product_id and item.discount == item_discount:
                item.quantity += quantity
                return
        self.items.append(CartItem(product_id, name, quantity, unit_price, item_discount))

    def remove_item(self, index: int) -> None:
        if 0 <= index < len(self.items):
            self.items.pop(index)

    def update_quantity(self, index: int, quantity: float) -> None:
        if 0 <= index < len(self.items):
            if quantity <= 0:
                self.remove_item(index)
            else:
                self.items[index].quantity = quantity

    def clear(self) -> None:
        self.items.clear()
        self.customer_id = None
        self.discount = 0.0
        self.payment_method = "cash"
        self.amount_paid = 0.0
        self.notes = ""

    @property
    def subtotal(self) -> float:
        return round(sum(i.subtotal for i in self.items), 2)

    @property
    def tax_rate(self) -> float:
        return float(get_setting("tax_rate", "16"))

    @property
    def tax_amount(self) -> float:
        taxable = self.subtotal * (1 - self.discount / 100)
        return round(taxable * self.tax_rate / 100, 2)

    @property
    def discount_amount(self) -> float:
        return round(self.subtotal * self.discount / 100, 2)

    @property
    def total(self) -> float:
        return round(self.subtotal - self.discount_amount + self.tax_amount, 2)

    @property
    def change_due(self) -> float:
        return round(max(0, self.amount_paid - self.total), 2)

    def is_empty(self) -> bool:
        return len(self.items) == 0


def _generate_folio() -> str:
    conn = get_connection()
    count = conn.execute("SELECT COUNT(*) FROM sales").fetchone()[0]
    conn.close()
    now = datetime.datetime.now()
    return f"{now.strftime('%Y%m%d')}-{count + 1:05d}"


def process_sale(cart: Cart, user_id: int) -> int:
    """
    Persist a completed sale to the database and update stock.
    Returns the new sale ID.
    """
    if cart.is_empty():
        raise ValueError("El carrito está vacío.")
    if cart.amount_paid < cart.total:
        raise ValueError("El monto pagado es insuficiente.")

    folio = _generate_folio()
    conn = get_connection()
    try:
        cur = conn.execute(
            """INSERT INTO sales
               (folio, customer_id, user_id, subtotal, tax, discount, total,
                payment_method, amount_paid, change_due, notes)
               VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (folio, cart.customer_id, user_id,
             cart.subtotal, cart.tax_amount, cart.discount_amount,
             cart.total, cart.payment_method, cart.amount_paid,
             cart.change_due, cart.notes),
        )
        sale_id = cur.lastrowid

        for item in cart.items:
            conn.execute(
                """INSERT INTO sale_items
                   (sale_id, product_id, product_name, quantity, unit_price, discount, subtotal)
                   VALUES (?,?,?,?,?,?,?)""",
                (sale_id, item.product_id, item.name, item.quantity,
                 item.unit_price, item.discount, item.subtotal),
            )
            # Deduct stock
            conn.execute(
                "UPDATE products SET stock = stock - ? WHERE id=?",
                (item.quantity, item.product_id),
            )

        conn.commit()
        return sale_id
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_sale(sale_id: int) -> Optional[Dict]:
    conn = get_connection()
    sale = conn.execute("SELECT * FROM sales WHERE id=?", (sale_id,)).fetchone()
    if not sale:
        conn.close()
        return None
    items = conn.execute(
        "SELECT * FROM sale_items WHERE sale_id=?", (sale_id,)
    ).fetchall()
    conn.close()
    result = dict(sale)
    result["items"] = [dict(i) for i in items]
    return result


def cancel_sale(sale_id: int) -> None:
    """Cancel a completed sale and restore stock."""
    conn = get_connection()
    sale = conn.execute("SELECT * FROM sales WHERE id=?", (sale_id,)).fetchone()
    if not sale or sale["status"] == "cancelled":
        conn.close()
        return
    items = conn.execute(
        "SELECT product_id, quantity FROM sale_items WHERE sale_id=?", (sale_id,)
    ).fetchall()
    try:
        conn.execute("UPDATE sales SET status='cancelled' WHERE id=?", (sale_id,))
        for item in items:
            if item["product_id"]:
                conn.execute(
                    "UPDATE products SET stock = stock + ? WHERE id=?",
                    (item["quantity"], item["product_id"]),
                )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ── Customer CRUD ─────────────────────────────────────────────────────────────

def list_customers(search: str = "") -> List[Dict]:
    conn = get_connection()
    if search:
        s = f"%{search}%"
        rows = conn.execute(
            "SELECT * FROM customers WHERE name LIKE ? OR phone LIKE ? OR email LIKE ? "
            "ORDER BY name",
            (s, s, s),
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM customers ORDER BY name").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_customer(customer_id: int) -> Optional[Dict]:
    conn = get_connection()
    row = conn.execute("SELECT * FROM customers WHERE id=?", (customer_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def add_customer(name: str, email: str = "", phone: str = "",
                 address: str = "", rfc: str = "", notes: str = "") -> int:
    conn = get_connection()
    cur = conn.execute(
        "INSERT INTO customers (name, email, phone, address, rfc, notes) VALUES (?,?,?,?,?,?)",
        (name, email, phone, address, rfc, notes),
    )
    conn.commit()
    conn.close()
    return cur.lastrowid


def update_customer(customer_id: int, name: str, email: str, phone: str,
                    address: str, rfc: str, notes: str) -> None:
    conn = get_connection()
    conn.execute(
        "UPDATE customers SET name=?, email=?, phone=?, address=?, rfc=?, notes=? WHERE id=?",
        (name, email, phone, address, rfc, notes, customer_id),
    )
    conn.commit()
    conn.close()


def delete_customer(customer_id: int) -> None:
    conn = get_connection()
    conn.execute("DELETE FROM customers WHERE id=?", (customer_id,))
    conn.commit()
    conn.close()

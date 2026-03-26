"""
Reports module: queries for dashboard and detailed reports.
"""
from typing import Dict, List, Any
from pathlib import Path
from .database import get_connection

# Validated period → SQL fragment mapping.
# Only values from this dict are interpolated into queries, ensuring no user-
# controlled data reaches the SQL engine (parameterized queries cannot be used
# for structural SQL fragments like WHERE sub-expressions).
_PERIOD_FILTERS: Dict[str, str] = {
    "today": "date(created_at) = date('now')",
    "week":  "created_at >= datetime('now', '-7 days')",
    "month": "strftime('%Y-%m', created_at) = strftime('%Y-%m', 'now')",
    "year":  "strftime('%Y', created_at) = strftime('%Y', 'now')",
}

_PERIOD_FILTERS_ALIASED: Dict[str, str] = {
    "today": "date(s.created_at) = date('now')",
    "week":  "s.created_at >= datetime('now', '-7 days')",
    "month": "strftime('%Y-%m', s.created_at) = strftime('%Y-%m', 'now')",
    "year":  "strftime('%Y', s.created_at) = strftime('%Y', 'now')",
}


def _get_receipts_folder() -> Path:
    """Get or create receipts folder."""
    if getattr(__import__('sys'), 'frozen', False):
        # PyInstaller executable
        base_dir = Path(__import__('sys').executable).resolve().parent
    else:
        # Script mode
        base_dir = Path(__file__).resolve().parent
    
    receipts_dir = base_dir / "receipts"
    receipts_dir.mkdir(exist_ok=True)
    return receipts_dir


def _delete_receipt_file(folio: str) -> None:
    """Delete the PDF receipt file for the given folio."""
    try:
        receipts_dir = _get_receipts_folder()
        filename = f"boleta_{folio.replace('/', '_')}.pdf"
        filepath = receipts_dir / filename
        if filepath.exists():
            filepath.unlink()
    except Exception as e:
        # Log the error but don't raise - the database record is already deleted
        print(f"Warning: Could not delete receipt file for folio {folio}: {e}")


def _period_where(period: str, aliased: bool = False) -> str:
    """Return a safe, hardcoded SQL fragment for *period*."""
    mapping = _PERIOD_FILTERS_ALIASED if aliased else _PERIOD_FILTERS
    if period not in mapping:
        period = "today"
    return mapping[period]


def sales_summary(period: str = "today", selected_date: str | None = None) -> Dict[str, Any]:
    """
    Return totals for the given period.
    period: 'today' | 'week' | 'month' | 'year' | 'date'
    """
    conn = get_connection()
    if period == "date" and selected_date:
        row = conn.execute(
            "SELECT COUNT(*) as count, COALESCE(SUM(total),0) as total, "
            "COALESCE(SUM(tax),0) as tax, COALESCE(SUM(discount),0) as discount "
            "FROM sales WHERE status='completed' AND date(created_at) = date(?)",
            (selected_date,),
        ).fetchone()
    else:
        where = _period_where(period)
        row = conn.execute(
            "SELECT COUNT(*) as count, COALESCE(SUM(total),0) as total, "
            "COALESCE(SUM(tax),0) as tax, COALESCE(SUM(discount),0) as discount "
            f"FROM sales WHERE status='completed' AND {where}"
        ).fetchone()
    conn.close()
    return dict(row)


def sales_by_day(days: int = 30) -> List[Dict]:
    conn = get_connection()
    rows = conn.execute(
        """SELECT date(created_at) as day,
                  COUNT(*) as count,
                  COALESCE(SUM(total),0) as total
           FROM sales
           WHERE status='completed' AND created_at >= datetime('now', ?)
           GROUP BY day ORDER BY day""",
        (f"-{days} days",),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def top_products(limit: int = 10, period: str = "month", selected_date: str | None = None) -> List[Dict]:
    if period == "date" and selected_date:
        where = "date(s.created_at) = date(?)"
        params = (selected_date, limit)
    else:
        where = _period_where(period, aliased=True)
        params = (limit,)
    conn = get_connection()
    rows = conn.execute(
        f"""SELECT si.product_name,
                   SUM(si.quantity) as qty_sold,
                   SUM(si.subtotal) as revenue
            FROM sale_items si
            JOIN sales s ON si.sale_id = s.id
            WHERE s.status='completed' AND {where}
            GROUP BY si.product_name
            ORDER BY qty_sold DESC
            LIMIT ?""",
        params,
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def payment_method_breakdown(period: str = "month") -> List[Dict]:
    where = _period_where(period)
    conn = get_connection()
    rows = conn.execute(
        f"""SELECT payment_method, COUNT(*) as count, COALESCE(SUM(total),0) as total
            FROM sales WHERE status='completed' AND {where}
            GROUP BY payment_method ORDER BY total DESC""",
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def recent_sales(limit: int = 20) -> List[Dict]:
    conn = get_connection()
    rows = conn.execute(
        """SELECT s.*, c.name as customer_name
           FROM sales s
           LEFT JOIN customers c ON s.customer_id = c.id
           ORDER BY s.created_at DESC
           LIMIT ?""",
        (limit,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_sale_by_folio(folio: str) -> Dict | None:
    conn = get_connection()
    sale = conn.execute("SELECT * FROM sales WHERE folio=?", (folio,)).fetchone()
    if not sale:
        conn.close()
        return None
    items = conn.execute("SELECT * FROM sale_items WHERE sale_id=?", (sale["id"],)).fetchall()
    conn.close()
    data = dict(sale)
    data["items"] = [dict(i) for i in items]
    return data


def delete_sale_by_folio(folio: str) -> bool:
    """Delete one sale (and its items) by folio. Returns True if deleted."""
    conn = get_connection()
    sale = conn.execute("SELECT id FROM sales WHERE folio=?", (folio,)).fetchone()
    if not sale:
        conn.close()
        return False
    try:
        conn.execute("DELETE FROM sale_items WHERE sale_id=?", (sale["id"],))
        conn.execute("DELETE FROM sales WHERE id=?", (sale["id"],))
        conn.commit()
        # Delete the receipt PDF file
        _delete_receipt_file(folio)
        return True
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def delete_all_sales() -> int:
    """Delete all sales and sale items. Returns number of deleted sales."""
    conn = get_connection()
    try:
        # Get all folios before deleting so we can remove their files
        rows = conn.execute("SELECT folio FROM sales").fetchall()
        folios = [row["folio"] for row in rows]
        
        row = conn.execute("SELECT COUNT(*) AS c FROM sales").fetchone()
        count = int(row["c"] if row else 0)
        conn.execute("DELETE FROM sale_items")
        conn.execute("DELETE FROM sales")
        conn.commit()
        
        # Delete all receipt PDF files
        for folio in folios:
            _delete_receipt_file(folio)
        
        return count
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def inventory_value() -> Dict[str, Any]:
    conn = get_connection()
    row = conn.execute(
        """SELECT COUNT(*) as products,
                  COALESCE(SUM(stock),0) as units,
                  COALESCE(SUM(stock * cost),0) as cost_value,
                  COALESCE(SUM(stock * price),0) as sale_value
           FROM products WHERE active=1"""
    ).fetchone()
    conn.close()
    return dict(row)

"""
Reports module: queries for dashboard and detailed reports.
"""
from typing import Dict, List, Any
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


def _period_where(period: str, aliased: bool = False) -> str:
    """Return a safe, hardcoded SQL fragment for *period*."""
    mapping = _PERIOD_FILTERS_ALIASED if aliased else _PERIOD_FILTERS
    if period not in mapping:
        period = "today"
    return mapping[period]


def sales_summary(period: str = "today") -> Dict[str, Any]:
    """
    Return totals for the given period.
    period: 'today' | 'week' | 'month' | 'year'
    """
    conn = get_connection()
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


def top_products(limit: int = 10, period: str = "month") -> List[Dict]:
    where = _period_where(period, aliased=True)
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
        (limit,),
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

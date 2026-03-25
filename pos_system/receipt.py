"""
Receipt generator: builds a text receipt for printing or display.
"""
import datetime
from typing import Dict
from .database import get_setting


def build_receipt(sale: Dict) -> str:
    """Return a formatted text receipt string for *sale* (dict from get_sale)."""
    sym = get_setting("currency_symbol", "$")
    store = get_setting("store_name", "Mi Tienda")
    address = get_setting("store_address", "")
    phone = get_setting("store_phone", "")
    rfc = get_setting("store_rfc", "")
    footer = get_setting("receipt_footer", "¡Gracias por su compra!")

    width = 42
    sep = "─" * width

    def center(text: str) -> str:
        return text.center(width)

    def row(label: str, value: str) -> str:
        space = width - len(label) - len(value)
        return f"{label}{' ' * max(1, space)}{value}"

    lines = [
        center(store),
        center(address),
        center(phone),
    ]
    if rfc:
        lines.append(center(f"RFC: {rfc}"))
    lines += [
        sep,
        f"Folio: {sale['folio']}",
        f"Fecha: {sale['created_at']}",
        sep,
        f"{'Artículo':<24} {'Cant':>4} {'P.U.':>6} {'Imp.':>6}",
        sep,
    ]

    for item in sale.get("items", []):
        name = item["product_name"][:23]
        qty = f"{item['quantity']:.0f}"
        pu = f"{sym}{item['unit_price']:.2f}"
        sub = f"{sym}{item['subtotal']:.2f}"
        lines.append(f"{name:<24} {qty:>4} {pu:>6} {sub:>6}")
        if item["discount"] > 0:
            lines.append(f"  Descuento {item['discount']:.0f}%")

    lines += [
        sep,
        row("  Subtotal:", f"{sym}{sale['subtotal']:.2f}"),
    ]
    if sale["discount"] > 0:
        lines.append(row("  Descuento:", f"-{sym}{sale['discount']:.2f}"))
    lines += [
        row(f"  IVA ({get_setting('tax_rate', '16')}%):", f"{sym}{sale['tax']:.2f}"),
        row("  TOTAL:", f"{sym}{sale['total']:.2f}"),
        sep,
        row("  Forma de pago:", sale["payment_method"].upper()),
        row("  Pagó:", f"{sym}{sale['amount_paid']:.2f}"),
        row("  Cambio:", f"{sym}{sale['change_due']:.2f}"),
        sep,
        center(footer),
        "",
    ]
    return "\n".join(lines)

"""
Database module: creates and manages the SQLite database for the POS system.
"""
import sqlite3
import os
from pathlib import Path

DB_PATH = Path(__file__).parent / "pos_data.db"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def initialize_database() -> None:
    """Create all tables and seed default data if the database is new."""
    conn = get_connection()
    cursor = conn.cursor()

    # ── Users ──────────────────────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            username  TEXT    NOT NULL UNIQUE,
            password  TEXT    NOT NULL,
            role      TEXT    NOT NULL DEFAULT 'cashier',
            full_name TEXT    NOT NULL DEFAULT '',
            active    INTEGER NOT NULL DEFAULT 1,
            created_at TEXT   NOT NULL DEFAULT (datetime('now'))
        )
    """)

    # ── Categories ──────────────────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id   INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT    NOT NULL UNIQUE
        )
    """)

    # ── Products ────────────────────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            barcode     TEXT    UNIQUE,
            name        TEXT    NOT NULL,
            description TEXT    DEFAULT '',
            category_id INTEGER REFERENCES categories(id) ON DELETE SET NULL,
            price       REAL    NOT NULL DEFAULT 0,
            cost        REAL    NOT NULL DEFAULT 0,
            stock       INTEGER NOT NULL DEFAULT 0,
            min_stock   INTEGER NOT NULL DEFAULT 5,
            unit        TEXT    NOT NULL DEFAULT 'pza',
            active      INTEGER NOT NULL DEFAULT 1,
            created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
        )
    """)

    # ── Customers ───────────────────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            name       TEXT    NOT NULL,
            email      TEXT    DEFAULT '',
            phone      TEXT    DEFAULT '',
            address    TEXT    DEFAULT '',
            rfc        TEXT    DEFAULT '',
            notes      TEXT    DEFAULT '',
            created_at TEXT    NOT NULL DEFAULT (datetime('now'))
        )
    """)

    # ── Sales ────────────────────────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sales (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            folio        TEXT    NOT NULL UNIQUE,
            customer_id  INTEGER REFERENCES customers(id) ON DELETE SET NULL,
            user_id      INTEGER REFERENCES users(id),
            subtotal     REAL    NOT NULL DEFAULT 0,
            tax          REAL    NOT NULL DEFAULT 0,
            discount     REAL    NOT NULL DEFAULT 0,
            total        REAL    NOT NULL DEFAULT 0,
            payment_method TEXT  NOT NULL DEFAULT 'cash',
            amount_paid  REAL    NOT NULL DEFAULT 0,
            change_due   REAL    NOT NULL DEFAULT 0,
            status       TEXT    NOT NULL DEFAULT 'completed',
            notes        TEXT    DEFAULT '',
            created_at   TEXT    NOT NULL DEFAULT (datetime('now'))
        )
    """)

    # ── Sale Items ───────────────────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sale_items (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            sale_id     INTEGER NOT NULL REFERENCES sales(id) ON DELETE CASCADE,
            product_id  INTEGER REFERENCES products(id) ON DELETE SET NULL,
            product_name TEXT   NOT NULL,
            quantity    REAL    NOT NULL,
            unit_price  REAL    NOT NULL,
            discount    REAL    NOT NULL DEFAULT 0,
            subtotal    REAL    NOT NULL
        )
    """)

    # ── Store Settings ───────────────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key   TEXT PRIMARY KEY,
            value TEXT NOT NULL DEFAULT ''
        )
    """)

    # ── Seed default admin user (password: admin123) ─────────────────────────
    import hashlib
    default_pw = hashlib.sha256("admin123".encode()).hexdigest()
    cursor.execute("""
        INSERT OR IGNORE INTO users (username, password, role, full_name)
        VALUES ('admin', ?, 'admin', 'Administrador')
    """, (default_pw,))

    # ── Seed default categories ───────────────────────────────────────────────
    for cat in ("General", "Alimentos", "Bebidas", "Electrónica", "Ropa", "Otros"):
        cursor.execute("INSERT OR IGNORE INTO categories (name) VALUES (?)", (cat,))

    # ── Seed default settings ─────────────────────────────────────────────────
    defaults = {
        "store_name": "Mi Tienda",
        "store_address": "Calle Principal #1",
        "store_phone": "555-0000",
        "store_rfc": "",
        "tax_rate": "16",
        "currency": "MXN",
        "currency_symbol": "$",
        "receipt_footer": "¡Gracias por su compra!",
    }
    for key, value in defaults.items():
        cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (key, value))

    conn.commit()
    conn.close()


def get_setting(key: str, default: str = "") -> str:
    conn = get_connection()
    row = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    conn.close()
    return row["value"] if row else default


def set_setting(key: str, value: str) -> None:
    conn = get_connection()
    conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
    conn.commit()
    conn.close()

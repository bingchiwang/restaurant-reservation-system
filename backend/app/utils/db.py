import os
import sqlite3
from contextlib import contextmanager
from backend.config import Config

try:
    import pymysql
    from pymysql.cursors import DictCursor
except ImportError:
    pymysql = None
    DictCursor = None

def get_connection(config_class=Config):
    """
    Returns a database connection based on config.
    Supports MySQL (PyMySQL) and SQLite.
    """
    if config_class.DB_TYPE == "mysql":
        if pymysql is None:
            raise ImportError("PyMySQL is not installed. Please install pymysql or set DB_TYPE=sqlite")
        return pymysql.connect(
            host=config_class.MYSQL_HOST,
            port=config_class.MYSQL_PORT,
            user=config_class.MYSQL_USER,
            password=config_class.MYSQL_PASSWORD,
            database=config_class.MYSQL_DATABASE,
            cursorclass=DictCursor,
            autocommit=False
        )
    else:
        # SQLite
        conn = sqlite3.connect(config_class.SQLITE_PATH, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        # Enable foreign key support in SQLite
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

@contextmanager
def get_db_cursor(conn, commit=False):
    """
    Context manager for database cursor with automatic transaction handling.
    """
    cursor = conn.cursor()
    try:
        yield cursor
        if commit:
            conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()

def init_sqlite_db(conn):
    """
    Initializes SQLite tables corresponding to MySQL schema for local dev and testing.
    """
    cursor = conn.cursor()
    cursor.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        display_name TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'MEMBER',
        status TEXT NOT NULL DEFAULT 'ACTIVE',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS dining_tables (
        table_id INTEGER PRIMARY KEY AUTOINCREMENT,
        table_name TEXT NOT NULL,
        capacity INTEGER NOT NULL,
        status TEXT NOT NULL DEFAULT 'ACTIVE',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS reservations (
        reservation_id INTEGER PRIMARY KEY AUTOINCREMENT,
        reservation_code TEXT UNIQUE NOT NULL,
        user_id INTEGER,
        party_size INTEGER NOT NULL,
        start_at DATETIME NOT NULL,
        end_at DATETIME NOT NULL,
        status TEXT NOT NULL DEFAULT 'CONFIRMED',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE SET NULL
    );

    CREATE TABLE IF NOT EXISTS reservation_guests (
        reservation_id INTEGER PRIMARY KEY,
        guest_name TEXT NOT NULL,
        guest_phone TEXT NOT NULL,
        FOREIGN KEY (reservation_id) REFERENCES reservations(reservation_id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS reservation_tables (
        reservation_id INTEGER NOT NULL,
        table_id INTEGER NOT NULL,
        PRIMARY KEY (reservation_id, table_id),
        FOREIGN KEY (reservation_id) REFERENCES reservations(reservation_id) ON DELETE CASCADE,
        FOREIGN KEY (table_id) REFERENCES dining_tables(table_id) ON DELETE RESTRICT
    );

    CREATE TABLE IF NOT EXISTS menu_categories (
        category_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'ACTIVE',
        sort_order INTEGER NOT NULL DEFAULT 0
    );

    CREATE TABLE IF NOT EXISTS menu_items (
        item_id INTEGER PRIMARY KEY AUTOINCREMENT,
        category_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        description TEXT,
        price NUMERIC NOT NULL,
        is_available INTEGER NOT NULL DEFAULT 1,
        image_url TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (category_id) REFERENCES menu_categories(category_id) ON DELETE RESTRICT
    );

    CREATE TABLE IF NOT EXISTS orders (
        order_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        reservation_id INTEGER,
        table_id INTEGER,
        order_type TEXT NOT NULL DEFAULT 'DINE_IN',
        status TEXT NOT NULL DEFAULT 'PENDING',
        total_amount NUMERIC NOT NULL DEFAULT 0.00,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE SET NULL,
        FOREIGN KEY (reservation_id) REFERENCES reservations(reservation_id) ON DELETE SET NULL,
        FOREIGN KEY (table_id) REFERENCES dining_tables(table_id) ON DELETE SET NULL
    );

    CREATE TABLE IF NOT EXISTS order_items (
        order_item_id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER NOT NULL,
        item_id INTEGER NOT NULL,
        item_name_snapshot TEXT NOT NULL,
        quantity INTEGER NOT NULL,
        unit_price NUMERIC NOT NULL,
        subtotal NUMERIC NOT NULL,
        note TEXT,
        FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE,
        FOREIGN KEY (item_id) REFERENCES menu_items(item_id) ON DELETE RESTRICT
    );
    """)
    conn.commit()

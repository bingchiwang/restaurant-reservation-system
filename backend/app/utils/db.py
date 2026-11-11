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

def _get_conf(config, key, default=None):
    if hasattr(config, key):
        return getattr(config, key)
    if isinstance(config, dict) or hasattr(config, "get"):
        return config.get(key, default)
    return default

def get_connection(config_class=Config):
    """
    Returns a database connection based on config.
    Supports MySQL (PyMySQL) and SQLite.
    """
    db_type = _get_conf(config_class, "DB_TYPE", "sqlite")
    if db_type == "mysql":
        if pymysql is None:
            raise ImportError("PyMySQL is not installed. Please install pymysql or set DB_TYPE=sqlite")
        return pymysql.connect(
            host=_get_conf(config_class, "MYSQL_HOST", "127.0.0.1"),
            port=int(_get_conf(config_class, "MYSQL_PORT", 3306)),
            user=_get_conf(config_class, "MYSQL_USER", "root"),
            password=_get_conf(config_class, "MYSQL_PASSWORD", ""),
            database=_get_conf(config_class, "MYSQL_DATABASE", "restaurant_db"),
            cursorclass=DictCursor,
            autocommit=False
        )
    else:
        # SQLite
        sqlite_path = _get_conf(config_class, "SQLITE_PATH", "restaurant_dev.db")
        is_uri = sqlite_path.startswith("file:")
        conn = sqlite3.connect(sqlite_path, uri=is_uri, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        # Enable foreign key support in SQLite
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

@contextmanager
def get_db_cursor(conn, commit=False):
    """
    Context manager for database cursor with automatic transaction handling.
    Wraps execute to support '?' placeholders across both SQLite and MySQL.
    """
    raw_cursor = conn.cursor()
    is_mysql = pymysql is not None and isinstance(conn, pymysql.connections.Connection)

    class CursorWrapper:
        def __init__(self, cur, is_mysql):
            self._cur = cur
            self._is_mysql = is_mysql

        def execute(self, sql, params=None):
            if self._is_mysql and params is not None:
                # Replace '?' with '%s' for MySQL compatibility
                sql = sql.replace("?", "%s")
            if params is None:
                return self._cur.execute(sql)
            return self._cur.execute(sql, params)

        def fetchone(self):
            return self._cur.fetchone()

        def fetchall(self):
            return self._cur.fetchall()

        def close(self):
            return self._cur.close()

        @property
        def lastrowid(self):
            return self._cur.lastrowid

        @property
        def rowcount(self):
            return self._cur.rowcount

    cursor = CursorWrapper(raw_cursor, is_mysql)
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

    CREATE TABLE IF NOT EXISTS store_settings (
        setting_id INTEGER PRIMARY KEY,
        store_status TEXT NOT NULL DEFAULT 'OPEN',
        reservations_enabled INTEGER NOT NULL DEFAULT 1,
        ordering_enabled INTEGER NOT NULL DEFAULT 1,
        pre_order_enabled INTEGER NOT NULL DEFAULT 1,
        announcement_text TEXT NOT NULL DEFAULT '',
        announcement_type TEXT NOT NULL DEFAULT 'info',
        opening_time TEXT NOT NULL DEFAULT '11:00',
        closing_time TEXT NOT NULL DEFAULT '21:30',
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );

    INSERT OR IGNORE INTO store_settings (
        setting_id, store_status, reservations_enabled, ordering_enabled,
        pre_order_enabled, announcement_text, announcement_type, opening_time, closing_time
    ) VALUES (1, 'OPEN', 1, 1, 1, '', 'info', '11:00', '21:30');
    """)
    conn.commit()

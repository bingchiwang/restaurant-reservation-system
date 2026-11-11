from backend.app.utils.db import get_db_cursor

class MenuDAO:
    def __init__(self, conn):
        self.conn = conn

    def get_categories(self, status="ACTIVE"):
        """
        Retrieves all menu categories with the given status.
        """
        with get_db_cursor(self.conn) as cursor:
            if status is None:
                cursor.execute("""
                    SELECT category_id, name, status, sort_order
                    FROM menu_categories
                    ORDER BY sort_order ASC, category_id ASC
                """)
            else:
                cursor.execute("""
                    SELECT category_id, name, status, sort_order
                    FROM menu_categories
                    WHERE status = ?
                    ORDER BY sort_order ASC, category_id ASC
                """, (status,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def get_items(self, category_id=None, only_available=True):
        """
        Retrieves menu items, optionally filtered by category and availability.
        Includes category_name from menu_categories join.
        """
        query = """
            SELECT 
                i.item_id,
                i.category_id,
                c.name AS category_name,
                i.name,
                i.description,
                i.price,
                i.is_available,
                i.image_url,
                i.created_at,
                i.updated_at
            FROM menu_items i
            JOIN menu_categories c ON i.category_id = c.category_id
            WHERE 1=1
        """
        params = []
        if only_available:
            query += " AND i.is_available = 1 AND c.status = 'ACTIVE'"
        if category_id is not None:
            query += " AND i.category_id = ?"
            params.append(category_id)

        query += " ORDER BY c.sort_order ASC, i.item_id ASC"

        with get_db_cursor(self.conn) as cursor:
            cursor.execute(query, tuple(params))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def get_item_by_id(self, item_id):
        """
        Retrieves a single menu item by item_id.
        """
        with get_db_cursor(self.conn) as cursor:
            cursor.execute("""
                SELECT 
                    i.item_id,
                    i.category_id,
                    c.name AS category_name,
                    i.name,
                    i.description,
                    i.price,
                    i.is_available,
                    i.image_url
                FROM menu_items i
                JOIN menu_categories c ON i.category_id = c.category_id
                WHERE i.item_id = ?
            """, (item_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_category_by_id(self, category_id):
        """
        Retrieves a single category by category_id.
        """
        with get_db_cursor(self.conn) as cursor:
            cursor.execute("""
                SELECT category_id, name, status, sort_order
                FROM menu_categories
                WHERE category_id = ?
            """, (category_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def create_item(self, category_id, name, description, price, is_available=1, image_url=None):
        """
        Creates a new menu item.
        """
        with get_db_cursor(self.conn, commit=True) as cursor:
            cursor.execute("""
                INSERT INTO menu_items (category_id, name, description, price, is_available, image_url)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (category_id, name.strip(), description, price, 1 if is_available else 0, image_url))
            return cursor.lastrowid

    def update_item(self, item_id, fields: dict):
        """
        Updates fields of a menu item dynamically.
        Allowed fields: category_id, name, description, price, is_available, image_url
        """
        allowed = {"category_id", "name", "description", "price", "is_available", "image_url"}
        update_cols = []
        params = []
        for k, v in fields.items():
            if k in allowed:
                update_cols.append(f"{k} = ?")
                params.append(v)

        if not update_cols:
            return False

        params.append(item_id)
        sql = f"UPDATE menu_items SET {', '.join(update_cols)}, updated_at = CURRENT_TIMESTAMP WHERE item_id = ?"
        with get_db_cursor(self.conn, commit=True) as cursor:
            cursor.execute(sql, tuple(params))
            return cursor.rowcount > 0

    def update_availability(self, item_id, is_available: bool):
        """
        Quickly toggles/updates availability (shelf on/off).
        """
        with get_db_cursor(self.conn, commit=True) as cursor:
            cursor.execute("""
                UPDATE menu_items
                SET is_available = ?, updated_at = CURRENT_TIMESTAMP
                WHERE item_id = ?
            """, (1 if is_available else 0, item_id))
            return cursor.rowcount > 0

    def create_category(self, name: str, status: str = "ACTIVE", sort_order: int = 0):
        """Creates a new menu category."""
        with get_db_cursor(self.conn, commit=True) as cursor:
            cursor.execute("""
                INSERT INTO menu_categories (name, status, sort_order)
                VALUES (?, ?, ?)
            """, (name.strip(), status, sort_order))
            return cursor.lastrowid

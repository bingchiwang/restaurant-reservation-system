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

from backend.app.utils.db import get_db_cursor

class OrderDAO:
    def __init__(self, conn):
        self.conn = conn

    def create_order(self, user_id, reservation_id, table_id, order_type="DINE_IN", status="PENDING", total_amount=0.0):
        with get_db_cursor(self.conn) as cursor:
            cursor.execute("""
                INSERT INTO orders (user_id, reservation_id, table_id, order_type, status, total_amount)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (user_id, reservation_id, table_id, order_type, status, float(total_amount)))
            return cursor.lastrowid

    def create_order_item(self, order_id, item_id, item_name_snapshot, quantity, unit_price, subtotal, note=None):
        with get_db_cursor(self.conn) as cursor:
            cursor.execute("""
                INSERT INTO order_items (order_id, item_id, item_name_snapshot, quantity, unit_price, subtotal, note)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (order_id, item_id, item_name_snapshot, quantity, float(unit_price), float(subtotal), note))
            return cursor.lastrowid

    def get_order_by_id(self, order_id: int):
        with get_db_cursor(self.conn) as cursor:
            cursor.execute("""
                SELECT 
                    o.order_id,
                    o.user_id,
                    o.reservation_id,
                    o.table_id,
                    o.order_type,
                    o.status,
                    o.total_amount,
                    o.created_at,
                    o.updated_at,
                    dt.table_name
                FROM orders o
                LEFT JOIN dining_tables dt ON o.table_id = dt.table_id
                WHERE o.order_id = ?
            """, (order_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_order_items(self, order_id: int):
        with get_db_cursor(self.conn) as cursor:
            cursor.execute("""
                SELECT 
                    order_item_id,
                    order_id,
                    item_id,
                    item_name_snapshot,
                    quantity,
                    unit_price,
                    subtotal,
                    note
                FROM order_items
                WHERE order_id = ?
                ORDER BY order_item_id ASC
            """, (order_id,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def delete_order_items(self, order_id: int):
        """Deletes all items of an order inside an enclosing transaction."""
        with get_db_cursor(self.conn) as cursor:
            cursor.execute("DELETE FROM order_items WHERE order_id = ?", (order_id,))
            return cursor.rowcount

    def update_order_header(self, order_id: int, table_id, total_amount: float):
        """Updates order table_id and total_amount inside an enclosing transaction."""
        with get_db_cursor(self.conn) as cursor:
            cursor.execute("""
                UPDATE orders
                SET table_id = ?, total_amount = ?, updated_at = CURRENT_TIMESTAMP
                WHERE order_id = ?
            """, (table_id, float(total_amount), order_id))
            return cursor.rowcount > 0

    def update_order_status(self, order_id: int, new_status: str):
        with get_db_cursor(self.conn, commit=True) as cursor:
            cursor.execute("""
                UPDATE orders
                SET status = ?, updated_at = CURRENT_TIMESTAMP
                WHERE order_id = ?
            """, (new_status, order_id))
            return cursor.rowcount > 0

    def list_orders(self, status=None, reservation_id=None, table_id=None, date_str=None, sort_order="desc", limit=50, offset=0):
        order_dir = "ASC" if str(sort_order or "").lower() == "asc" else "DESC"
        query = """
            SELECT 
                o.order_id,
                o.user_id,
                o.reservation_id,
                o.table_id,
                o.order_type,
                o.status,
                o.total_amount,
                o.created_at,
                dt.table_name
            FROM orders o
            LEFT JOIN dining_tables dt ON o.table_id = dt.table_id
            WHERE 1=1
        """
        params = []
        if status:
            query += " AND o.status = ?"
            params.append(status)
        if reservation_id:
            query += " AND o.reservation_id = ?"
            params.append(reservation_id)
        if table_id:
            query += " AND o.table_id = ?"
            params.append(table_id)
        if date_str:
            query += " AND DATE(o.created_at) = DATE(?)"
            params.append(date_str)

        query += f" ORDER BY o.created_at {order_dir}, o.order_id {order_dir} LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        with get_db_cursor(self.conn) as cursor:
            cursor.execute(query, tuple(params))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

from backend.app.utils.db import get_db_cursor

class ReservationDAO:
    def __init__(self, conn):
        self.conn = conn

    def create_reservation(self, reservation_code: str, user_id, party_size: int, start_at: str, end_at: str, status: str = "CONFIRMED"):
        with get_db_cursor(self.conn) as cursor:
            cursor.execute("""
                INSERT INTO reservations (reservation_code, user_id, party_size, start_at, end_at, status)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (reservation_code, user_id, party_size, start_at, end_at, status))
            return cursor.lastrowid

    def create_guest_contact(self, reservation_id: int, guest_name: str, guest_phone: str):
        with get_db_cursor(self.conn) as cursor:
            cursor.execute("""
                INSERT INTO reservation_guests (reservation_id, guest_name, guest_phone)
                VALUES (?, ?, ?)
            """, (reservation_id, guest_name.strip(), guest_phone.strip()))

    def assign_table(self, reservation_id: int, table_id: int):
        with get_db_cursor(self.conn) as cursor:
            cursor.execute("""
                INSERT INTO reservation_tables (reservation_id, table_id)
                VALUES (?, ?)
            """, (reservation_id, table_id))

    def update_assigned_table(self, reservation_id: int, new_table_id: int):
        with get_db_cursor(self.conn, commit=True) as cursor:
            cursor.execute("""
                UPDATE reservation_tables
                SET table_id = ?
                WHERE reservation_id = ?
            """, (new_table_id, reservation_id))
            return cursor.rowcount > 0

    def get_by_code(self, reservation_code: str):
        with get_db_cursor(self.conn) as cursor:
            cursor.execute("""
                SELECT 
                    r.reservation_id,
                    r.reservation_code,
                    r.user_id,
                    r.party_size,
                    r.start_at,
                    r.end_at,
                    r.status,
                    r.created_at,
                    g.guest_name,
                    g.guest_phone,
                    t.table_id,
                    dt.table_name,
                    dt.capacity
                FROM reservations r
                LEFT JOIN reservation_guests g ON r.reservation_id = g.reservation_id
                LEFT JOIN reservation_tables t ON r.reservation_id = t.reservation_id
                LEFT JOIN dining_tables dt ON t.table_id = dt.table_id
                WHERE r.reservation_code = ?
            """, (reservation_code,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_by_id(self, reservation_id: int):
        with get_db_cursor(self.conn) as cursor:
            cursor.execute("""
                SELECT 
                    r.reservation_id,
                    r.reservation_code,
                    r.user_id,
                    r.party_size,
                    r.start_at,
                    r.end_at,
                    r.status,
                    r.created_at,
                    g.guest_name,
                    g.guest_phone,
                    t.table_id,
                    dt.table_name,
                    dt.capacity
                FROM reservations r
                LEFT JOIN reservation_guests g ON r.reservation_id = g.reservation_id
                LEFT JOIN reservation_tables t ON r.reservation_id = t.reservation_id
                LEFT JOIN dining_tables dt ON t.table_id = dt.table_id
                WHERE r.reservation_id = ?
            """, (reservation_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def update_status(self, reservation_id: int, status: str):
        with get_db_cursor(self.conn, commit=True) as cursor:
            cursor.execute("""
                UPDATE reservations
                SET status = ?, updated_at = CURRENT_TIMESTAMP
                WHERE reservation_id = ?
            """, (status, reservation_id))
            return cursor.rowcount > 0

    def update_reservation_fields(self, reservation_id: int, fields: dict):
        """Updates allowed fields on reservations table."""
        allowed = {"party_size", "start_at", "end_at", "status"}
        update_cols = []
        params = []
        for k, v in fields.items():
            if k in allowed:
                update_cols.append(f"{k} = ?")
                params.append(v)
        if not update_cols:
            return False
        params.append(reservation_id)
        sql = f"UPDATE reservations SET {', '.join(update_cols)}, updated_at = CURRENT_TIMESTAMP WHERE reservation_id = ?"
        with get_db_cursor(self.conn, commit=True) as cursor:
            cursor.execute(sql, tuple(params))
            return cursor.rowcount > 0

    def list_reservations(self, date_str=None, status=None, sort_order="asc", limit=50, offset=0):
        order_dir = "DESC" if str(sort_order or "").lower() == "desc" else "ASC"
        query = """
            SELECT 
                r.reservation_id,
                r.reservation_code,
                r.user_id,
                r.party_size,
                r.start_at,
                r.end_at,
                r.status,
                r.created_at,
                g.guest_name,
                g.guest_phone,
                t.table_id,
                dt.table_name,
                dt.capacity
            FROM reservations r
            LEFT JOIN reservation_guests g ON r.reservation_id = g.reservation_id
            LEFT JOIN reservation_tables t ON r.reservation_id = t.reservation_id
            LEFT JOIN dining_tables dt ON t.table_id = dt.table_id
            WHERE 1=1
        """
        params = []
        if date_str:
            query += " AND DATE(r.start_at) = DATE(?)"
            params.append(date_str)
        if status:
            query += " AND r.status = ?"
            params.append(status)

        query += f" ORDER BY r.start_at {order_dir}, r.reservation_id {order_dir} LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        with get_db_cursor(self.conn) as cursor:
            cursor.execute(query, tuple(params))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

from backend.app.utils.db import get_db_cursor

class TableDAO:
    def __init__(self, conn):
        self.conn = conn

    def get_all_tables(self, status="ACTIVE"):
        """
        Retrieves dining tables with given status, ordered by capacity ASC, table_id ASC.
        """
        with get_db_cursor(self.conn) as cursor:
            if status:
                cursor.execute("""
                    SELECT table_id, table_name, capacity, status, created_at, updated_at
                    FROM dining_tables
                    WHERE status = ?
                    ORDER BY capacity ASC, table_id ASC
                """, (status,))
            else:
                cursor.execute("""
                    SELECT table_id, table_name, capacity, status, created_at, updated_at
                    FROM dining_tables
                    ORDER BY capacity ASC, table_id ASC
                """)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def get_conflicting_table_ids(self, start_at: str, end_at: str, exclude_reservation_id: int = None):
        """
        Retrieves table IDs that have active (non-cancelled) reservations
        overlapping with [start_at, end_at).
        Optionally excludes a specific reservation_id.
        """
        query = """
            SELECT DISTINCT rt.table_id
            FROM reservation_tables rt
            JOIN reservations r ON rt.reservation_id = r.reservation_id
            WHERE r.status != 'CANCELLED'
              AND r.start_at < ?
              AND r.end_at > ?
        """
        params = [end_at, start_at]
        if exclude_reservation_id:
            query += " AND r.reservation_id != ?"
            params.append(exclude_reservation_id)

        with get_db_cursor(self.conn) as cursor:
            cursor.execute(query, tuple(params))
            rows = cursor.fetchall()
            return set(row["table_id"] if isinstance(row, dict) else row[0] for row in rows)

    def get_table_by_id(self, table_id: int):
        """Retrieves a single dining table by table_id."""
        with get_db_cursor(self.conn) as cursor:
            cursor.execute("""
                SELECT table_id, table_name, capacity, status, created_at, updated_at
                FROM dining_tables
                WHERE table_id = ?
            """, (table_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def create_table(self, table_name: str, capacity: int, status: str = "ACTIVE"):
        """
        Creates a new dining table.
        """
        with get_db_cursor(self.conn, commit=True) as cursor:
            cursor.execute("""
                INSERT INTO dining_tables (table_name, capacity, status)
                VALUES (?, ?, ?)
            """, (table_name.strip(), capacity, status))
            return cursor.lastrowid

    def update_table(self, table_id: int, fields: dict):
        """Updates allowed fields on a dining table."""
        allowed = {"table_name", "capacity", "status"}
        update_cols = []
        params = []
        for k, v in fields.items():
            if k in allowed:
                update_cols.append(f"{k} = ?")
                params.append(v)

        if not update_cols:
            return False

        params.append(table_id)
        sql = f"UPDATE dining_tables SET {', '.join(update_cols)}, updated_at = CURRENT_TIMESTAMP WHERE table_id = ?"
        with get_db_cursor(self.conn, commit=True) as cursor:
            cursor.execute(sql, tuple(params))
            return cursor.rowcount > 0

from backend.app.utils.db import get_db_cursor

class ReservationDAO:
    def __init__(self, conn):
        self.conn = conn

    def create_reservation(self, reservation_code: str, user_id, party_size: int, start_at: str, end_at: str, status: str = "CONFIRMED"):
        """
        Creates reservation record. Does not commit automatically to allow transaction enclosing.
        """
        with get_db_cursor(self.conn) as cursor:
            cursor.execute("""
                INSERT INTO reservations (reservation_code, user_id, party_size, start_at, end_at, status)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (reservation_code, user_id, party_size, start_at, end_at, status))
            return cursor.lastrowid

    def create_guest_contact(self, reservation_id: int, guest_name: str, guest_phone: str):
        """
        Inserts guest contact information.
        """
        with get_db_cursor(self.conn) as cursor:
            cursor.execute("""
                INSERT INTO reservation_guests (reservation_id, guest_name, guest_phone)
                VALUES (?, ?, ?)
            """, (reservation_id, guest_name.strip(), guest_phone.strip()))

    def assign_table(self, reservation_id: int, table_id: int):
        """
        Associates a reservation with an allocated table.
        """
        with get_db_cursor(self.conn) as cursor:
            cursor.execute("""
                INSERT INTO reservation_tables (reservation_id, table_id)
                VALUES (?, ?)
            """, (reservation_id, table_id))

    def get_by_code(self, reservation_code: str):
        """
        Retrieves reservation by its unique code, including guest and table info.
        """
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

    def update_status(self, reservation_id: int, status: str):
        """
        Updates reservation status (e.g. CANCELLED, COMPLETED).
        """
        with get_db_cursor(self.conn, commit=True) as cursor:
            cursor.execute("""
                UPDATE reservations
                SET status = ?, updated_at = CURRENT_TIMESTAMP
                WHERE reservation_id = ?
            """, (status, reservation_id))
            return cursor.rowcount > 0

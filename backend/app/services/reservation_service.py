import uuid
from datetime import datetime, timedelta
from backend.config import Config
from backend.app.daos.table_dao import TableDAO
from backend.app.daos.reservation_dao import ReservationDAO

class NoAvailableTableError(Exception):
    """Raised when no suitable table is available."""
    pass

class ReservationService:
    def __init__(self, conn, config=Config):
        self.conn = conn
        self.config = config
        self.table_dao = TableDAO(conn)
        self.reservation_dao = ReservationDAO(conn)

    def validate_reservation_input(self, party_size, reservation_time_str, guest_name=None, guest_phone=None, is_guest=True):
        """
        Validates party size, contact info, and time slot restrictions.
        """
        # 1. Party Size
        try:
            party_size = int(party_size)
            if party_size <= 0:
                raise ValueError("Party size must be greater than 0")
            max_size = getattr(self.config, "MAX_PARTY_SIZE", 10)
            if party_size > max_size:
                raise ValueError(f"Party size cannot exceed {max_size} people in the current release")
        except (TypeError, ValueError) as e:
            raise ValueError(str(e))

        # 2. Guest Info (if guest reservation)
        if is_guest:
            if not guest_name or not str(guest_name).strip():
                raise ValueError("Guest contact name is required")
            if not guest_phone or not str(guest_phone).strip():
                raise ValueError("Guest contact phone is required")

        # 3. Parse DateTime
        try:
            if "T" in reservation_time_str:
                start_dt = datetime.fromisoformat(reservation_time_str.replace("Z", "+00:00"))
                # Strip timezone for local comparison
                start_dt = start_dt.replace(tzinfo=None)
            elif len(reservation_time_str.strip()) == 16:
                start_dt = datetime.strptime(reservation_time_str.strip(), "%Y-%m-%d %H:%M")
            elif len(reservation_time_str.strip()) == 19:
                start_dt = datetime.strptime(reservation_time_str.strip(), "%Y-%m-%d %H:%M:%S")
            else:
                raise ValueError("Invalid format")
        except Exception:
            raise ValueError("Invalid reservation time format. Expected YYYY-MM-DD HH:MM or ISO 8601")

        # 4. Advance Time & Range Checks
        now = datetime.now()
        min_advance = getattr(self.config, "MIN_ADVANCE_MINUTES", 30)
        if start_dt < now + timedelta(minutes=min_advance):
            raise ValueError(f"Reservations must be booked at least {min_advance} minutes in advance")

        max_days = getattr(self.config, "MAX_RESERVATION_DAYS", 30)
        if start_dt > now + timedelta(days=max_days):
            raise ValueError(f"Reservations can only be made within {max_days} days in advance")

        # 5. Business Hours Check
        opening_str = getattr(self.config, "OPENING_TIME", "11:00")
        closing_str = getattr(self.config, "CLOSING_TIME", "21:30")
        
        opening_time = datetime.strptime(opening_str, "%H:%M").time()
        closing_time = datetime.strptime(closing_str, "%H:%M").time()

        if start_dt.time() < opening_time or start_dt.time() > closing_time:
            raise ValueError(f"Reservation time must be within opening hours ({opening_str} ~ {closing_str})")

        return party_size, start_dt

    def calculate_end_time(self, start_dt: datetime) -> datetime:
        """
        Calculates end time including meal duration and cleaning buffer.
        """
        meal_duration = getattr(self.config, "MEAL_DURATION_MINUTES", 90)
        cleaning_buffer = getattr(self.config, "CLEANING_BUFFER_MINUTES", 15)
        return start_dt + timedelta(minutes=meal_duration + cleaning_buffer)

    def generate_reservation_code(self, start_dt: datetime) -> str:
        """
        Generates unique human-readable reservation code: RES-YYYYMMDD-XXXX
        """
        date_str = start_dt.strftime("%Y%m%d")
        random_suffix = uuid.uuid4().hex[:6].upper()
        return f"RES-{date_str}-{random_suffix}"

    def select_best_table(self, party_size: int, start_dt: datetime, end_dt: datetime):
        """
        REQ-003: 桌位自動分配演算法
        1. 排除非使用中桌位 (status != 'ACTIVE')
        2. 排除時段重疊衝突之桌位
        3. 排除容量不足 (capacity < party_size)
        4. 優先選擇剩餘座位較少 (capacity - party_size 最小化)
        5. 多張合適時依 table_id 升冪排序
        """
        start_str = start_dt.strftime("%Y-%m-%d %H:%M:%S")
        end_str = end_dt.strftime("%Y-%m-%d %H:%M:%S")

        all_active_tables = self.table_dao.get_all_tables(status="ACTIVE")
        conflicting_ids = self.table_dao.get_conflicting_table_ids(start_str, end_str)

        # Filter candidates
        candidates = [
            t for t in all_active_tables
            if t["table_id"] not in conflicting_ids and t["capacity"] >= party_size
        ]

        if not candidates:
            return None

        # Sort candidates: (wasted_capacity, table_id)
        candidates.sort(key=lambda t: (t["capacity"] - party_size, t["table_id"]))
        return candidates[0]

    def create_guest_reservation(self, party_size, reservation_time_str, guest_name, guest_phone, note=None):
        """
        REQ-002 & REQ-003: 訪客預約完整交易流程
        """
        party_size, start_dt = self.validate_reservation_input(
            party_size=party_size,
            reservation_time_str=reservation_time_str,
            guest_name=guest_name,
            guest_phone=guest_phone,
            is_guest=True
        )
        end_dt = self.calculate_end_time(start_dt)
        start_str = start_dt.strftime("%Y-%m-%d %H:%M:%S")
        end_str = end_dt.strftime("%Y-%m-%d %H:%M:%S")

        # Transaction Boundary
        try:
            # Table allocation check inside transaction
            best_table = self.select_best_table(party_size, start_dt, end_dt)
            if not best_table:
                raise NoAvailableTableError("No available table for the selected party size and time slot")

            res_code = self.generate_reservation_code(start_dt)
            
            # 1. Insert reservation
            res_id = self.reservation_dao.create_reservation(
                reservation_code=res_code,
                user_id=None,
                party_size=party_size,
                start_at=start_str,
                end_at=end_str,
                status="CONFIRMED"
            )

            # 2. Insert guest contact
            self.reservation_dao.create_guest_contact(
                reservation_id=res_id,
                guest_name=guest_name,
                guest_phone=guest_phone
            )

            # 3. Associate table
            self.reservation_dao.assign_table(
                reservation_id=res_id,
                table_id=best_table["table_id"]
            )

            self.conn.commit()
            return self.reservation_dao.get_by_code(res_code)
        except Exception:
            self.conn.rollback()
            raise

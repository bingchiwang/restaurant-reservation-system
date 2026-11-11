import uuid
from datetime import datetime, timedelta
from backend.config import Config
from backend.app.daos.table_dao import TableDAO
from backend.app.daos.reservation_dao import ReservationDAO
from backend.app.daos.system_dao import SystemDAO
from backend.app.utils.exceptions import FeatureDisabledError

class NoAvailableTableError(Exception):
    """Raised when no suitable table is available."""
    pass

class ReservationService:
    def __init__(self, conn, config=Config):
        self.conn = conn
        self.config = config
        self.table_dao = TableDAO(conn)
        self.reservation_dao = ReservationDAO(conn)
        self.system_dao = SystemDAO(conn)

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

        # 5. Business Hours Check (read from backend store settings)
        settings = self.system_dao.get_settings()
        opening_str = settings.get("opening_time") or getattr(self.config, "OPENING_TIME", "11:00")
        closing_str = settings.get("closing_time") or getattr(self.config, "CLOSING_TIME", "21:30")
        
        opening_time = datetime.strptime(opening_str, "%H:%M").time()
        closing_time = datetime.strptime(closing_str, "%H:%M").time()

        if start_dt.time() < opening_time or start_dt.time() > closing_time:
            raise ValueError(f"Reservation time must be within opening hours ({opening_str} ~ {closing_str})")

        return party_size, start_dt

    def calculate_end_time(self, start_dt: datetime) -> datetime:
        meal_duration = getattr(self.config, "MEAL_DURATION_MINUTES", 90)
        cleaning_buffer = getattr(self.config, "CLEANING_BUFFER_MINUTES", 15)
        return start_dt + timedelta(minutes=meal_duration + cleaning_buffer)

    def generate_reservation_code(self, start_dt: datetime) -> str:
        date_str = start_dt.strftime("%Y%m%d")
        random_suffix = uuid.uuid4().hex[:6].upper()
        return f"RES-{date_str}-{random_suffix}"

    def select_best_table(self, party_size: int, start_dt: datetime, end_dt: datetime):
        start_str = start_dt.strftime("%Y-%m-%d %H:%M:%S")
        end_str = end_dt.strftime("%Y-%m-%d %H:%M:%S")

        all_active_tables = self.table_dao.get_all_tables(status="ACTIVE")
        conflicting_ids = self.table_dao.get_conflicting_table_ids(start_str, end_str)

        candidates = [
            t for t in all_active_tables
            if t["table_id"] not in conflicting_ids and t["capacity"] >= party_size
        ]

        if not candidates:
            return None

        candidates.sort(key=lambda t: (t["capacity"] - party_size, t["table_id"]))
        return candidates[0]

    def create_guest_reservation(self, party_size, reservation_time_str, guest_name, guest_phone, note=None, items=None):
        """
        REQ-002, REQ-003 & REQ-006: 訪客預約（可包含預約時預點餐原子交易）
        """
        settings = self.system_dao.get_settings()
        store_status = settings.get("store_status", "OPEN")
        if store_status == "MAINTENANCE":
            raise FeatureDisabledError("系統維護中，暫停線上預約服務")
        if store_status == "CLOSED":
            raise FeatureDisabledError("本店目前休息中，暫停線上預約")
        if not settings.get("reservations_enabled", 1):
            raise FeatureDisabledError("線上預約功能目前已由後端管理員暫停")
        if items and (not settings.get("pre_order_enabled", 1) or not settings.get("ordering_enabled", 1)):
            raise FeatureDisabledError("預約預點餐功能目前已由後端管理員暫停")

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

        from backend.app.services.order_service import OrderService
        order_svc = OrderService(self.conn)

        # Pre-validate items if pre-ordering
        validated_items = None
        total_amount = None
        if items:
            total_amount, validated_items = order_svc.calculate_and_validate_items(items)

        try:
            best_table = self.select_best_table(party_size, start_dt, end_dt)
            if not best_table:
                raise NoAvailableTableError("No available table for the selected party size and time slot")

            res_code = self.generate_reservation_code(start_dt)
            
            res_id = self.reservation_dao.create_reservation(
                reservation_code=res_code,
                user_id=None,
                party_size=party_size,
                start_at=start_str,
                end_at=end_str,
                status="CONFIRMED"
            )

            self.reservation_dao.create_guest_contact(
                reservation_id=res_id,
                guest_name=guest_name,
                guest_phone=guest_phone
            )

            self.reservation_dao.assign_table(
                reservation_id=res_id,
                table_id=best_table["table_id"]
            )

            order_data = None
            if items and validated_items:
                order_id = order_svc.order_dao.create_order(
                    user_id=None,
                    reservation_id=res_id,
                    table_id=best_table["table_id"],
                    order_type="PRE_ORDER",
                    status="PENDING",
                    total_amount=float(total_amount)
                )
                for vi in validated_items:
                    order_svc.order_dao.create_order_item(
                        order_id=order_id,
                        item_id=vi["item_id"],
                        item_name_snapshot=vi["item_name_snapshot"],
                        quantity=vi["quantity"],
                        unit_price=float(vi["unit_price"]),
                        subtotal=float(vi["subtotal"]),
                        note=vi["note"]
                    )
                order_data = order_svc.get_order_details(order_id)

            self.conn.commit()
            result = self.reservation_dao.get_by_code(res_code)
            if order_data:
                result["pre_order"] = order_data
            return result
        except Exception:
            self.conn.rollback()
            raise

    def get_reservation_with_auth(self, reservation_code: str, phone: str = None, user_id: int = None, is_admin: bool = False):
        """
        REQ-004: 憑預約編號與身分核對查詢預約，防止任意猜測號碼窺探他人個資
        """
        res = self.reservation_dao.get_by_code(reservation_code)
        if not res:
            return None

        if is_admin:
            return res

        # Check guest phone or member user_id
        if res.get("user_id"):
            if user_id != res["user_id"]:
                raise PermissionError("Access denied: Not authorized to view this reservation")
        else:
            if not phone or str(phone).strip() != str(res.get("guest_phone")).strip():
                raise PermissionError("Verification failed: Phone number does not match reservation contact")

        return res

    def cancel_reservation(self, reservation_code: str, phone: str = None, user_id: int = None, is_admin: bool = False):
        """
        REQ-004: 顧客取消預約（1 小時前限制、釋放座位）
        """
        res = self.get_reservation_with_auth(reservation_code, phone=phone, user_id=user_id, is_admin=is_admin)
        if not res:
            raise LookupError(f"Reservation {reservation_code} not found")

        current_status = res.get("status")
        if current_status == "CANCELLED":
            raise ValueError("Reservation has already been cancelled")
        if current_status == "COMPLETED":
            raise ValueError("Completed reservations cannot be cancelled")

        # Check 1-hour cancellation limit for non-admin
        if not is_admin:
            start_str = res["start_at"]
            if isinstance(start_str, str):
                start_dt = datetime.strptime(start_str[:19], "%Y-%m-%d %H:%M:%S")
            else:
                start_dt = start_str

            now = datetime.now()
            if start_dt - now < timedelta(hours=1):
                raise ValueError("Reservations cannot be cancelled within 1 hour of meal time online. Please contact the restaurant.")

        self.reservation_dao.update_status(res["reservation_id"], "CANCELLED")
        return self.reservation_dao.get_by_id(res["reservation_id"])

    # Admin Methods (REQ-012)
    def admin_list_reservations(self, date_str=None, status=None, sort_order="asc", limit=50, offset=0):
        return self.reservation_dao.list_reservations(
            date_str=date_str,
            status=status,
            sort_order=sort_order,
            limit=limit,
            offset=offset,
        )

    def admin_update_reservation(self, reservation_id: int, fields: dict):
        """Updates reservation status and/or table_id with full validation."""
        if not isinstance(fields, dict):
            raise ValueError("Invalid update payload")

        if "status" in fields and fields["status"]:
            self.admin_update_status(reservation_id, str(fields["status"]).strip().upper())

        if "table_id" in fields and fields["table_id"] is not None:
            self.admin_change_table(reservation_id, int(fields["table_id"]))

        res = self.reservation_dao.get_by_id(reservation_id)
        if not res:
            raise LookupError(f"Reservation {reservation_id} not found")
        return res

    def admin_update_status(self, reservation_id: int, new_status: str):
        valid_statuses = {"PENDING", "CONFIRMED", "COMPLETED", "CANCELLED"}
        if new_status not in valid_statuses:
            raise ValueError(f"Invalid status: {new_status}. Allowed: {valid_statuses}")

        res = self.reservation_dao.get_by_id(reservation_id)
        if not res:
            raise LookupError(f"Reservation {reservation_id} not found")

        self.reservation_dao.update_status(reservation_id, new_status)
        return self.reservation_dao.get_by_id(reservation_id)

    def admin_change_table(self, reservation_id: int, new_table_id: int):
        res = self.reservation_dao.get_by_id(reservation_id)
        if not res:
            raise LookupError(f"Reservation {reservation_id} not found")

        if res["status"] == "CANCELLED":
            raise ValueError("Cannot assign table to a cancelled reservation")

        all_tables = {t["table_id"]: t for t in self.table_dao.get_all_tables(status=None)}
        if new_table_id not in all_tables:
            raise ValueError(f"Table {new_table_id} does not exist")

        target_table = all_tables[new_table_id]
        if target_table["status"] != "ACTIVE":
            raise ValueError(f"Table {new_table_id} is currently {target_table['status']}")

        if target_table["capacity"] < res["party_size"]:
            raise ValueError(f"Table capacity ({target_table['capacity']}) is insufficient for party size ({res['party_size']})")

        # Conflict check
        conflicts = self.table_dao.get_conflicting_table_ids(
            start_at=str(res["start_at"])[:19],
            end_at=str(res["end_at"])[:19],
            exclude_reservation_id=reservation_id
        )
        if new_table_id in conflicts:
            raise ValueError(f"Table {new_table_id} has a scheduling conflict with another reservation")

        self.reservation_dao.update_assigned_table(reservation_id, new_table_id)
        return self.reservation_dao.get_by_id(reservation_id)

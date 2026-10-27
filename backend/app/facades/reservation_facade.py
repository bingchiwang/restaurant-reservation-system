from flask import has_app_context, current_app
from backend.app.utils.db import get_connection
from backend.app.services.reservation_service import ReservationService

class ReservationFacade:
    def __init__(self, conn=None):
        self._external_conn = conn

    def _get_service(self):
        if self._external_conn:
            conn = self._external_conn
            config = getattr(conn, "_config", None) or (current_app.config if has_app_context() else None)
        else:
            config = current_app.config if has_app_context() else None
            conn = get_connection(config) if config else get_connection()
        service = ReservationService(conn, config)
        return conn, service

    def create_guest_reservation(self, party_size, reservation_time, guest_name, guest_phone, note=None, items=None):
        conn, service = self._get_service()
        try:
            return service.create_guest_reservation(
                party_size=party_size,
                reservation_time_str=reservation_time,
                guest_name=guest_name,
                guest_phone=guest_phone,
                note=note,
                items=items
            )
        finally:
            if not self._external_conn:
                conn.close()

    def get_reservation_by_code(self, reservation_code: str, phone: str = None, user_id: int = None, is_admin: bool = False):
        conn, service = self._get_service()
        try:
            return service.get_reservation_with_auth(
                reservation_code=reservation_code,
                phone=phone,
                user_id=user_id,
                is_admin=is_admin
            )
        finally:
            if not self._external_conn:
                conn.close()

    def cancel_reservation(self, reservation_code: str, phone: str = None, user_id: int = None, is_admin: bool = False):
        conn, service = self._get_service()
        try:
            return service.cancel_reservation(
                reservation_code=reservation_code,
                phone=phone,
                user_id=user_id,
                is_admin=is_admin
            )
        finally:
            if not self._external_conn:
                conn.close()

    def admin_list_reservations(self, date_str=None, status=None, limit=50, offset=0):
        conn, service = self._get_service()
        try:
            return service.admin_list_reservations(date_str=date_str, status=status, limit=limit, offset=offset)
        finally:
            if not self._external_conn:
                conn.close()

    def admin_update_status(self, reservation_id: int, new_status: str):
        conn, service = self._get_service()
        try:
            return service.admin_update_status(reservation_id, new_status)
        finally:
            if not self._external_conn:
                conn.close()

    def admin_change_table(self, reservation_id: int, new_table_id: int):
        conn, service = self._get_service()
        try:
            return service.admin_change_table(reservation_id, new_table_id)
        finally:
            if not self._external_conn:
                conn.close()

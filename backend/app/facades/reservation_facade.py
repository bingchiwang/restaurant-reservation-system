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

    def create_guest_reservation(self, party_size, reservation_time, guest_name, guest_phone, note=None):
        """
        Coordinates guest reservation and table allocation.
        """
        conn, service = self._get_service()
        try:
            return service.create_guest_reservation(
                party_size=party_size,
                reservation_time_str=reservation_time,
                guest_name=guest_name,
                guest_phone=guest_phone,
                note=note
            )
        finally:
            if not self._external_conn:
                conn.close()

    def get_reservation_by_code(self, reservation_code: str):
        """
        Retrieves reservation details by unique code.
        """
        conn, service = self._get_service()
        try:
            return service.reservation_dao.get_by_code(reservation_code)
        finally:
            if not self._external_conn:
                conn.close()

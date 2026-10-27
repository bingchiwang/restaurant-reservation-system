from flask import Blueprint, request, jsonify
from backend.app.facades.reservation_facade import ReservationFacade
from backend.app.services.reservation_service import NoAvailableTableError

reservation_bp = Blueprint("reservation", __name__, url_prefix="/api/v1/reservations")

@reservation_bp.route("", methods=["POST"])
def create_reservation():
    """
    REQ-002: 建立訪客預約（自動分配座位 REQ-003）
    """
    data = request.get_json() or {}
    
    party_size = data.get("party_size")
    reservation_time = data.get("reservation_time")
    # Support separate date and time fields if provided
    if not reservation_time and data.get("reservation_date") and data.get("start_time"):
        reservation_time = f"{data['reservation_date'].strip()} {data['start_time'].strip()}"

    guest_name = data.get("guest_name")
    guest_phone = data.get("guest_phone")
    note = data.get("note")

    if party_size is None or not reservation_time or not guest_name or not guest_phone:
        return jsonify({
            "success": False,
            "error": "BAD_REQUEST",
            "message": "party_size, reservation_time, guest_name, and guest_phone are required"
        }), 400

    facade = ReservationFacade()
    try:
        reservation = facade.create_guest_reservation(
            party_size=party_size,
            reservation_time=reservation_time,
            guest_name=guest_name,
            guest_phone=guest_phone,
            note=note
        )
        return jsonify({
            "success": True,
            "message": "Reservation confirmed",
            "data": reservation
        }), 201
    except NoAvailableTableError as e:
        return jsonify({
            "success": False,
            "error": "NO_AVAILABLE_TABLE",
            "message": str(e)
        }), 409
    except ValueError as e:
        return jsonify({
            "success": False,
            "error": "BAD_REQUEST",
            "message": str(e)
        }), 400

@reservation_bp.route("/<string:reservation_code>", methods=["GET"])
def get_reservation(reservation_code):
    """
    REQ-004: 查詢預約 (基礎公開查詢端點，後續搭配電話身分驗證)
    """
    facade = ReservationFacade()
    res = facade.get_reservation_by_code(reservation_code)
    if not res:
        return jsonify({
            "success": False,
            "error": "RESERVATION_NOT_FOUND",
            "message": f"Reservation {reservation_code} not found"
        }), 404

    return jsonify({
        "success": True,
        "data": res
    }), 200

from flask import Blueprint, request, jsonify
from backend.app.facades.reservation_facade import ReservationFacade
from backend.app.services.reservation_service import NoAvailableTableError
from backend.app.utils.exceptions import FeatureDisabledError
from backend.app.utils.auth import get_optional_current_user

reservation_bp = Blueprint("reservation", __name__, url_prefix="/api/v1/reservations")

@reservation_bp.route("", methods=["POST"])
def create_reservation():
    """
    REQ-002: 建立訪客預約（自動分配座位 REQ-003）
    """
    data = request.get_json() or {}
    
    party_size = data.get("party_size")
    reservation_time = data.get("reservation_time")
    if not reservation_time and data.get("reservation_date") and data.get("start_time"):
        reservation_time = f"{data['reservation_date'].strip()} {data['start_time'].strip()}"

    guest_name = data.get("guest_name")
    guest_phone = data.get("guest_phone")
    note = data.get("note")
    items = data.get("items")

    if party_size is None or not reservation_time or not guest_name or not guest_phone:
        return jsonify({
            "success": False,
            "error": "BAD_REQUEST",
            "message": "party_size, reservation_time, guest_name, and guest_phone are required"
        }), 400

    current_user = get_optional_current_user()
    user_id = current_user["user_id"] if current_user else None

    facade = ReservationFacade()
    try:
        reservation = facade.create_guest_reservation(
            party_size=party_size,
            reservation_time=reservation_time,
            guest_name=guest_name,
            guest_phone=guest_phone,
            note=note,
            items=items,
            user_id=user_id
        )
        return jsonify({
            "success": True,
            "message": "Reservation confirmed",
            "data": reservation
        }), 201
    except FeatureDisabledError as e:
        return jsonify({
            "success": False,
            "error": "SERVICE_PAUSED",
            "message": str(e)
        }), 403
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
    REQ-004: 查詢預約 (支援電話驗證或登入會員本人查詢)
    """
    phone = request.args.get("phone")
    current_user = get_optional_current_user()
    user_id = current_user["user_id"] if current_user else None
    facade = ReservationFacade()
    try:
        res = facade.get_reservation_by_code(reservation_code, phone=phone, user_id=user_id, is_admin=False)
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
    except PermissionError as e:
        return jsonify({
            "success": False,
            "error": "FORBIDDEN",
            "message": str(e)
        }), 403

@reservation_bp.route("/<string:reservation_code>/cancel", methods=["POST"])
def cancel_reservation(reservation_code):
    """
    REQ-004: 顧客取消預約（支援電話驗證或登入會員本人取消）
    """
    data = request.get_json() or {}
    phone = data.get("phone")
    current_user = get_optional_current_user()
    user_id = current_user["user_id"] if current_user else None

    facade = ReservationFacade()
    try:
        cancelled = facade.cancel_reservation(reservation_code, phone=phone, user_id=user_id, is_admin=False)
        return jsonify({
            "success": True,
            "message": "Reservation has been successfully cancelled",
            "data": cancelled
        }), 200
    except LookupError as e:
        return jsonify({
            "success": False,
            "error": "RESERVATION_NOT_FOUND",
            "message": str(e)
        }), 404
    except PermissionError as e:
        return jsonify({
            "success": False,
            "error": "FORBIDDEN",
            "message": str(e)
        }), 403
    except ValueError as e:
        return jsonify({
            "success": False,
            "error": "BAD_REQUEST",
            "message": str(e)
        }), 400

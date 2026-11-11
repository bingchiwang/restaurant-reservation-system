from flask import Blueprint, request, jsonify
from backend.app.utils.auth import admin_required
from backend.app.facades.reservation_facade import ReservationFacade

admin_reservation_bp = Blueprint("admin_reservation", __name__, url_prefix="/api/v1/admin/reservations")

@admin_reservation_bp.route("", methods=["GET"])
@admin_required
def list_reservations():
    """
    REQ-012: 管理端查詢預約（依日期、狀態篩選）
    """
    date_str = request.args.get("date")
    status = request.args.get("status")
    sort_order = request.args.get("sort", "asc")
    limit = int(request.args.get("limit", 50))
    offset = int(request.args.get("offset", 0))

    facade = ReservationFacade()
    results = facade.admin_list_reservations(
        date_str=date_str, status=status, sort_order=sort_order, limit=limit, offset=offset
    )
    return jsonify({
        "success": True,
        "count": len(results),
        "data": results
    }), 200

@admin_reservation_bp.route("/<int:reservation_id>", methods=["PATCH"])
@admin_required
def update_reservation(reservation_id):
    """REQ-012: 管理端更新預約（狀態、桌位）"""
    data = request.get_json() or {}
    facade = ReservationFacade()
    try:
        updated = facade.admin_update_reservation(reservation_id, data)
        return jsonify({
            "success": True,
            "message": "Reservation updated successfully",
            "data": updated
        }), 200
    except LookupError as e:
        return jsonify({
            "success": False,
            "error": "NOT_FOUND",
            "message": str(e)
        }), 404
    except ValueError as e:
        return jsonify({
            "success": False,
            "error": "BAD_REQUEST",
            "message": str(e)
        }), 400

@admin_reservation_bp.route("/<int:reservation_id>/status", methods=["PATCH"])
@admin_required
def update_reservation_status(reservation_id):
    """
    REQ-012: 管理端更新預約狀態
    """
    data = request.get_json() or {}
    new_status = data.get("status")
    if not new_status:
        return jsonify({
            "success": False,
            "error": "BAD_REQUEST",
            "message": "Field 'status' is required"
        }), 400

    facade = ReservationFacade()
    try:
        updated = facade.admin_update_status(reservation_id, new_status)
        return jsonify({
            "success": True,
            "message": f"Reservation status updated to {new_status}",
            "data": updated
        }), 200
    except LookupError as e:
        return jsonify({
            "success": False,
            "error": "NOT_FOUND",
            "message": str(e)
        }), 404
    except ValueError as e:
        return jsonify({
            "success": False,
            "error": "BAD_REQUEST",
            "message": str(e)
        }), 400

@admin_reservation_bp.route("/<int:reservation_id>/table", methods=["PATCH"])
@admin_required
def change_reservation_table(reservation_id):
    """
    REQ-012: 管理端手動更換桌位（重新檢查時段衝突）
    """
    data = request.get_json() or {}
    new_table_id = data.get("table_id")
    if not new_table_id:
        return jsonify({
            "success": False,
            "error": "BAD_REQUEST",
            "message": "Field 'table_id' is required"
        }), 400

    facade = ReservationFacade()
    try:
        updated = facade.admin_change_table(reservation_id, int(new_table_id))
        return jsonify({
            "success": True,
            "message": "Reservation table changed successfully",
            "data": updated
        }), 200
    except LookupError as e:
        return jsonify({
            "success": False,
            "error": "NOT_FOUND",
            "message": str(e)
        }), 404
    except ValueError as e:
        return jsonify({
            "success": False,
            "error": "BAD_REQUEST",
            "message": str(e)
        }), 400

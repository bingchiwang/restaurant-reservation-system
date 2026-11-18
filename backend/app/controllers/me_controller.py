from flask import Blueprint, request, jsonify
from backend.app.utils.auth import login_required
from backend.app.facades.auth_facade import AuthFacade
from backend.app.facades.reservation_facade import ReservationFacade
from backend.app.facades.order_facade import OrderFacade

me_bp = Blueprint("me", __name__, url_prefix="/api/v1/me")

@me_bp.route("", methods=["GET"])
@login_required
def get_my_profile():
    """REQ-011: 會員查看個人基本資料"""
    user_id = request.current_user["user_id"]
    facade = AuthFacade()
    try:
        profile = facade.get_profile(user_id)
        return jsonify({"success": True, "data": profile}), 200
    except LookupError as e:
        return jsonify({"success": False, "error": "NOT_FOUND", "message": str(e)}), 404

@me_bp.route("", methods=["PATCH"])
@login_required
def update_my_profile():
    """REQ-011: 會員更新個人基本資料"""
    user_id = request.current_user["user_id"]
    data = request.get_json() or {}
    facade = AuthFacade()
    try:
        updated = facade.update_profile(user_id, data)
        return jsonify({"success": True, "message": "Profile updated", "data": updated}), 200
    except LookupError as e:
        return jsonify({"success": False, "error": "NOT_FOUND", "message": str(e)}), 404
    except ValueError as e:
        return jsonify({"success": False, "error": "BAD_REQUEST", "message": str(e)}), 400

@me_bp.route("/reservations", methods=["GET"])
@login_required
def get_my_reservations():
    """REQ-015: 會員查看自己的預約紀錄"""
    user_id = request.current_user["user_id"]
    facade = ReservationFacade()
    reservations = facade.list_member_reservations(user_id)
    return jsonify({
        "success": True,
        "count": len(reservations),
        "data": reservations
    }), 200

@me_bp.route("/orders", methods=["GET"])
@login_required
def get_my_orders():
    """REQ-015: 會員查看自己的訂單紀錄（含明細快照）"""
    user_id = request.current_user["user_id"]
    facade = OrderFacade()
    orders = facade.list_member_orders(user_id)
    return jsonify({
        "success": True,
        "count": len(orders),
        "data": orders
    }), 200

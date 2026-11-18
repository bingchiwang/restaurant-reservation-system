from flask import Blueprint, request, jsonify
from backend.app.facades.order_facade import OrderFacade
from backend.app.utils.exceptions import FeatureDisabledError
from backend.app.utils.auth import get_optional_current_user

order_bp = Blueprint("order", __name__, url_prefix="/api/v1/orders")

@order_bp.route("", methods=["POST"])
def create_order():
    """
    REQ-005 & REQ-007: 建立現場點餐訂單（透過桌位 QR Code 或指定桌號，登入會員會自動關聯 user_id）
    """
    data = request.get_json() or {}
    table_id = data.get("table_id")
    items = data.get("items")

    if table_id is None or not items:
        return jsonify({
            "success": False,
            "error": "BAD_REQUEST",
            "message": "Field 'table_id' and non-empty 'items' list are required"
        }), 400

    current_user = get_optional_current_user()
    user_id = current_user["user_id"] if current_user else None

    facade = OrderFacade()
    try:
        order = facade.create_dine_in_order(table_id=int(table_id), items=items, user_id=user_id)
        return jsonify({
            "success": True,
            "message": "Order created successfully",
            "data": order
        }), 201
    except FeatureDisabledError as e:
        return jsonify({
            "success": False,
            "error": "SERVICE_PAUSED",
            "message": str(e)
        }), 403
    except ValueError as e:
        return jsonify({
            "success": False,
            "error": "BAD_REQUEST",
            "message": str(e)
        }), 400

@order_bp.route("/<int:order_id>", methods=["GET"])
def get_order(order_id):
    """
    查詢訂單詳細內容與明細快照（私人會員訂單需本人或管理員登入驗證）
    """
    facade = OrderFacade()
    order = facade.get_order(order_id)
    if not order:
        return jsonify({
            "success": False,
            "error": "ORDER_NOT_FOUND",
            "message": f"Order {order_id} not found"
        }), 404

    if order.get("user_id") is not None:
        current_user = get_optional_current_user()
        if not current_user:
            return jsonify({
                "success": False,
                "error": "UNAUTHORIZED",
                "message": "Authentication required to view member order"
            }), 401
        if current_user.get("user_id") != order["user_id"] and current_user.get("role") not in ("ADMIN", "STAFF"):
            return jsonify({
                "success": False,
                "error": "FORBIDDEN",
                "message": "Not authorized to view this order"
            }), 403

    return jsonify({
        "success": True,
        "data": order
    }), 200

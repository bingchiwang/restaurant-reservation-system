from flask import Blueprint, request, jsonify
from backend.app.facades.order_facade import OrderFacade
from backend.app.utils.exceptions import FeatureDisabledError

order_bp = Blueprint("order", __name__, url_prefix="/api/v1/orders")

@order_bp.route("", methods=["POST"])
def create_order():
    """
    REQ-005 & REQ-007: 建立現場點餐訂單（透過桌位 QR Code 或指定桌號）
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

    facade = OrderFacade()
    try:
        order = facade.create_dine_in_order(table_id=int(table_id), items=items)
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
    查詢訂單詳細內容與明細快照
    """
    facade = OrderFacade()
    order = facade.get_order(order_id)
    if not order:
        return jsonify({
            "success": False,
            "error": "ORDER_NOT_FOUND",
            "message": f"Order {order_id} not found"
        }), 404

    return jsonify({
        "success": True,
        "data": order
    }), 200

from flask import Blueprint, request, jsonify
from backend.app.utils.auth import admin_required
from backend.app.facades.order_facade import OrderFacade

admin_order_bp = Blueprint("admin_order", __name__, url_prefix="/api/v1/admin/orders")

@admin_order_bp.route("", methods=["GET"])
@admin_required
def list_orders():
    """
    REQ-008: 管理端查詢訂單（支援狀態、桌位與預約篩選）
    """
    status = request.args.get("status")
    reservation_id = request.args.get("reservation_id")
    table_id = request.args.get("table_id")
    date_str = request.args.get("date")
    sort_order = request.args.get("sort", "desc")
    limit = int(request.args.get("limit", 50))
    offset = int(request.args.get("offset", 0))

    facade = OrderFacade()
    orders = facade.admin_list_orders(
        status=status,
        reservation_id=int(reservation_id) if reservation_id else None,
        table_id=int(table_id) if table_id else None,
        date_str=date_str,
        sort_order=sort_order,
        limit=limit,
        offset=offset
    )
    return jsonify({
        "success": True,
        "count": len(orders),
        "data": orders
    }), 200

@admin_order_bp.route("/<int:order_id>", methods=["PATCH"])
@admin_required
def update_order_content(order_id):
    """管理端更改訂單內容（桌號、餐點項目與數量，後端重算金額）"""
    data = request.get_json() or {}
    table_id = data.get("table_id")
    items = data.get("items")

    if table_id is None and items is None:
        return jsonify({
            "success": False,
            "error": "BAD_REQUEST",
            "message": "Provide 'table_id' and/or 'items' to update order"
        }), 400

    facade = OrderFacade()
    try:
        updated = facade.admin_update_order(
            order_id=order_id,
            table_id=table_id,
            items=items
        )
        return jsonify({
            "success": True,
            "message": "Order updated successfully",
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

@admin_order_bp.route("/<int:order_id>/status", methods=["PATCH"])
@admin_required
def update_order_status(order_id):
    """
    REQ-008: 管理端推進/更新訂單狀態（嚴格狀態機檢查）
    """
    data = request.get_json() or {}
    new_status = data.get("status")
    if not new_status:
        return jsonify({
            "success": False,
            "error": "BAD_REQUEST",
            "message": "Field 'status' is required"
        }), 400

    facade = OrderFacade()
    try:
        updated = facade.admin_update_order_status(order_id, str(new_status).strip().upper())
        return jsonify({
            "success": True,
            "message": f"Order status updated to {new_status}",
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

from flask import Blueprint, request, jsonify
from backend.app.facades.menu_facade import MenuFacade

menu_bp = Blueprint("menu", __name__, url_prefix="/api/v1/menu")

@menu_bp.route("/categories", methods=["GET"])
def get_categories():
    """
    REQ-001: 取得餐點分類
    """
    facade = MenuFacade()
    categories = facade.list_categories(status="ACTIVE")
    return jsonify({
        "success": True,
        "data": categories
    }), 200

@menu_bp.route("", methods=["GET"])
def get_menu_items():
    """
    REQ-001: 瀏覽可供應餐點（支援 category_id 篩選）
    """
    category_id = request.args.get("category_id", default=None)
    
    facade = MenuFacade()
    try:
        items = facade.list_menu_items(category_id=category_id, only_available=True)
    except ValueError as e:
        return jsonify({
            "success": False,
            "error": "BAD_REQUEST",
            "message": str(e)
        }), 400

    return jsonify({
        "success": True,
        "count": len(items),
        "data": items
    }), 200

@menu_bp.route("/<int:item_id>", methods=["GET"])
def get_menu_item(item_id):
    """
    REQ-001: 查詢單一餐點詳細資訊
    """
    facade = MenuFacade()
    try:
        item = facade.get_menu_item_detail(item_id)
    except ValueError as e:
        return jsonify({
            "success": False,
            "error": "BAD_REQUEST",
            "message": str(e)
        }), 400

    if not item:
        return jsonify({
            "success": False,
            "error": "ITEM_NOT_FOUND",
            "message": f"Menu item {item_id} not found"
        }), 404

    return jsonify({
        "success": True,
        "data": item
    }), 200

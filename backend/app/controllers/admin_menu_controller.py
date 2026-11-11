from flask import Blueprint, request, jsonify
from backend.app.utils.auth import admin_required
from backend.app.facades.menu_facade import MenuFacade

admin_menu_bp = Blueprint("admin_menu", __name__, url_prefix="/api/v1/admin/menu")

@admin_menu_bp.route("", methods=["GET"])
@admin_required
def list_all_items():
    """REQ-010: 管理員查看全部餐點（含已下架）"""
    category_id = request.args.get("category_id")
    facade = MenuFacade()
    try:
        items = facade.list_menu_items(category_id=category_id, only_available=False)
        return jsonify({
            "success": True,
            "count": len(items),
            "data": items
        }), 200
    except ValueError as e:
        return jsonify({
            "success": False,
            "error": "BAD_REQUEST",
            "message": str(e)
        }), 400

@admin_menu_bp.route("/categories", methods=["GET"])
@admin_required
def list_all_categories():
    """REQ-010: 管理員查看所有分類"""
    facade = MenuFacade()
    categories = facade.list_categories(status=None)
    return jsonify({
        "success": True,
        "data": categories
    }), 200

@admin_menu_bp.route("/categories", methods=["POST"])
@admin_required
def create_category():
    """REQ-010: 管理員新增餐點分類"""
    data = request.get_json() or {}
    facade = MenuFacade()
    try:
        cat = facade.create_category(
            name=data.get("name"),
            status=data.get("status", "ACTIVE"),
            sort_order=data.get("sort_order", 0)
        )
        return jsonify({
            "success": True,
            "message": "Category created successfully",
            "data": cat
        }), 201
    except ValueError as e:
        return jsonify({
            "success": False,
            "error": "BAD_REQUEST",
            "message": str(e)
        }), 400

@admin_menu_bp.route("", methods=["POST"])
@admin_required
def create_item():
    """
    REQ-010: 管理員新增餐點
    """
    data = request.get_json() or {}
    category_id = data.get("category_id")
    name = data.get("name")
    description = data.get("description", "")
    price = data.get("price")
    is_available = data.get("is_available", True)
    image_url = data.get("image_url")

    if not name or price is None or category_id is None:
        return jsonify({
            "success": False,
            "error": "BAD_REQUEST",
            "message": "category_id, name, and price are required"
        }), 400

    facade = MenuFacade()
    try:
        item = facade.create_menu_item(
            category_id=category_id,
            name=name,
            description=description,
            price=price,
            is_available=is_available,
            image_url=image_url
        )
        return jsonify({
            "success": True,
            "message": "Menu item created successfully",
            "data": item
        }), 201
    except ValueError as e:
        return jsonify({
            "success": False,
            "error": "BAD_REQUEST",
            "message": str(e)
        }), 400

@admin_menu_bp.route("/<int:item_id>", methods=["PATCH"])
@admin_required
def update_item(item_id):
    """
    REQ-010: 管理員修改餐點資訊
    """
    data = request.get_json() or {}
    facade = MenuFacade()
    try:
        updated = facade.update_menu_item(item_id, data)
        return jsonify({
            "success": True,
            "message": "Menu item updated successfully",
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

@admin_menu_bp.route("/<int:item_id>/availability", methods=["PATCH"])
@admin_required
def update_availability(item_id):
    """
    REQ-010: 管理員上下架餐點
    """
    data = request.get_json() or {}
    if "is_available" not in data:
        return jsonify({
            "success": False,
            "error": "BAD_REQUEST",
            "message": "Field 'is_available' (boolean) is required"
        }), 400

    is_available = bool(data["is_available"])
    facade = MenuFacade()
    try:
        updated = facade.update_item_availability(item_id, is_available)
        action_str = "restocked / on-shelf" if is_available else "off-shelf"
        return jsonify({
            "success": True,
            "message": f"Menu item set to {action_str}",
            "data": updated
        }), 200
    except LookupError as e:
        return jsonify({
            "success": False,
            "error": "NOT_FOUND",
            "message": str(e)
        }), 404

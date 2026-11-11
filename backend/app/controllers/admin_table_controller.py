from flask import Blueprint, request, jsonify
from backend.app.utils.auth import admin_required
from backend.app.facades.table_facade import TableFacade

admin_table_bp = Blueprint("admin_table", __name__, url_prefix="/api/v1/admin/tables")

@admin_table_bp.route("", methods=["GET"])
@admin_required
def list_tables():
    """REQ-013: 管理端查看所有桌位"""
    status = request.args.get("status")
    facade = TableFacade()
    tables = facade.list_tables(status=status)
    return jsonify({
        "success": True,
        "count": len(tables),
        "data": tables
    }), 200

@admin_table_bp.route("", methods=["POST"])
@admin_required
def create_table():
    """REQ-013: 管理端新增桌位"""
    data = request.get_json() or {}
    table_name = data.get("table_name")
    capacity = data.get("capacity")
    status = data.get("status", "ACTIVE")

    if not table_name or capacity is None:
        return jsonify({
            "success": False,
            "error": "BAD_REQUEST",
            "message": "table_name and capacity are required"
        }), 400

    facade = TableFacade()
    try:
        created = facade.create_table(table_name=table_name, capacity=capacity, status=status)
        return jsonify({
            "success": True,
            "message": "Table created successfully",
            "data": created
        }), 201
    except ValueError as e:
        return jsonify({
            "success": False,
            "error": "BAD_REQUEST",
            "message": str(e)
        }), 400

@admin_table_bp.route("/<int:table_id>", methods=["PATCH"])
@admin_required
def update_table(table_id):
    """REQ-013: 管理端修改桌位名稱、容量或狀態 (ACTIVE / MAINTENANCE / DISABLED)"""
    data = request.get_json() or {}
    facade = TableFacade()
    try:
        updated = facade.update_table(table_id, data)
        return jsonify({
            "success": True,
            "message": "Table updated successfully",
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

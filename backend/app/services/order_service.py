from decimal import Decimal
from backend.app.daos.order_dao import OrderDAO
from backend.app.daos.menu_dao import MenuDAO
from backend.app.daos.table_dao import TableDAO
from backend.app.daos.system_dao import SystemDAO
from backend.app.utils.exceptions import FeatureDisabledError

class OrderService:
    ALLOWED_TRANSITIONS = {
        "PENDING": {"CONFIRMED", "CANCELLED"},
        "CONFIRMED": {"PREPARING", "CANCELLED"},
        "PREPARING": {"READY", "CANCELLED"},
        "READY": {"COMPLETED"},
        "COMPLETED": set(),
        "CANCELLED": set()
    }

    def __init__(self, conn):
        self.conn = conn
        self.order_dao = OrderDAO(conn)
        self.menu_dao = MenuDAO(conn)
        self.table_dao = TableDAO(conn)
        self.system_dao = SystemDAO(conn)

    def calculate_and_validate_items(self, items_input: list, allow_existing_item_ids=None):
        """
        REQ-005: 購物車校驗與金額重算
        1. 檢查數量為正整數
        2. 檢查餐點存在且處於供應狀態 (is_available == 1)
        3. 以資料庫有效價格為準計算小計與總額 (使用 Decimal)
        4. 保存餐點名稱快照
        """
        if not items_input or not isinstance(items_input, list):
            raise ValueError("Order must contain at least one item")

        existing_ids = set(allow_existing_item_ids or [])
        validated_items = []
        total_amount = Decimal("0.00")

        for entry in items_input:
            if not isinstance(entry, dict):
                raise ValueError("Invalid item format in order list")

            item_id = entry.get("item_id")
            quantity = entry.get("quantity")
            note = entry.get("note", "")

            try:
                item_id = int(item_id)
            except (ValueError, TypeError):
                raise ValueError(f"Invalid item_id: {item_id}")

            try:
                quantity = int(quantity)
            except (ValueError, TypeError):
                raise ValueError(f"Invalid quantity for item {item_id}: must be an integer")

            if quantity <= 0:
                raise ValueError(f"Quantity for item {item_id} must be greater than 0")

            # Query database for current active item
            db_item = self.menu_dao.get_item_by_id(item_id)
            if not db_item:
                raise ValueError(f"Menu item {item_id} does not exist")

            if not db_item.get("is_available") and item_id not in existing_ids:
                raise ValueError(f"Menu item '{db_item['name']}' is currently not available / off-shelf")

            unit_price = Decimal(str(db_item["price"]))
            subtotal = unit_price * Decimal(quantity)
            total_amount += subtotal

            validated_items.append({
                "item_id": item_id,
                "item_name_snapshot": db_item["name"],
                "quantity": quantity,
                "unit_price": unit_price,
                "subtotal": subtotal,
                "note": str(note).strip() if note else None
            })

        return total_amount, validated_items

    def _validate_active_table(self, table_id: int):
        all_tables = {t["table_id"]: t for t in self.table_dao.get_all_tables(status=None)}
        if table_id not in all_tables:
            raise ValueError(f"Table {table_id} does not exist")
        if all_tables[table_id]["status"] != "ACTIVE":
            raise ValueError(f"Table {table_id} is not active ({all_tables[table_id]['status']})")

    def create_order(self, order_type: str, items_input: list, user_id=None, reservation_id=None, table_id=None, status="PENDING"):
        """
        Creates an order and its item snapshots in a transaction.
        """
        settings = self.system_dao.get_settings()
        store_status = settings.get("store_status", "OPEN")
        if store_status == "MAINTENANCE":
            raise FeatureDisabledError("系統維護中，暫停線上點餐服務")
        if store_status == "CLOSED":
            raise FeatureDisabledError("本店目前休息中，暫停線上點餐")
        if not settings.get("ordering_enabled", 1):
            raise FeatureDisabledError("現場點餐功能目前已由後端管理員暫停")

        # Validate table if table_id is provided
        if table_id is not None:
            self._validate_active_table(int(table_id))

        total_amount, validated_items = self.calculate_and_validate_items(items_input)

        try:
            order_id = self.order_dao.create_order(
                user_id=user_id,
                reservation_id=reservation_id,
                table_id=table_id,
                order_type=order_type,
                status=status,
                total_amount=float(total_amount)
            )

            for vi in validated_items:
                self.order_dao.create_order_item(
                    order_id=order_id,
                    item_id=vi["item_id"],
                    item_name_snapshot=vi["item_name_snapshot"],
                    quantity=vi["quantity"],
                    unit_price=float(vi["unit_price"]),
                    subtotal=float(vi["subtotal"]),
                    note=vi["note"]
                )

            self.conn.commit()
            return self.get_order_details(order_id)
        except Exception:
            self.conn.rollback()
            raise

    def get_order_details(self, order_id: int):
        order = self.order_dao.get_order_by_id(order_id)
        if not order:
            return None
        items = self.order_dao.get_order_items(order_id)
        order["total_amount"] = float(order["total_amount"])
        for item in items:
            item["unit_price"] = float(item["unit_price"])
            item["subtotal"] = float(item["subtotal"])
        order["items"] = items
        return order

    def update_order_status(self, order_id: int, new_status: str):
        """
        REQ-008: 訂單狀態機轉移驗證
        """
        order = self.order_dao.get_order_by_id(order_id)
        if not order:
            raise LookupError(f"Order {order_id} not found")

        current_status = order["status"]
        if new_status == current_status:
            return self.get_order_details(order_id)

        allowed = self.ALLOWED_TRANSITIONS.get(current_status, set())
        if new_status not in allowed:
            raise ValueError(
                f"Invalid status transition from {current_status} to {new_status}. "
                f"Allowed target states: {sorted(list(allowed)) if allowed else 'None (Terminal state)'}"
            )

        self.order_dao.update_order_status(order_id, new_status)
        return self.get_order_details(order_id)

    def admin_update_order(self, order_id: int, table_id=None, items_input=None):
        """
        Admin edits order table and/or items with backend Decimal recalculation in an atomic transaction.
        """
        order = self.order_dao.get_order_by_id(order_id)
        if not order:
            raise LookupError(f"Order {order_id} not found")

        if order["status"] in ("COMPLETED", "CANCELLED"):
            raise ValueError(f"Orders in {order['status']} state cannot be modified")

        new_table_id = order["table_id"]
        if table_id is not None:
            new_table_id = int(table_id)
            self._validate_active_table(new_table_id)

        validated_items = None
        new_total = Decimal(str(order["total_amount"]))

        if items_input is not None:
            existing_items = self.order_dao.get_order_items(order_id)
            existing_ids = {it["item_id"] for it in existing_items}
            new_total, validated_items = self.calculate_and_validate_items(
                items_input, allow_existing_item_ids=existing_ids
            )

        try:
            if validated_items is not None:
                self.order_dao.delete_order_items(order_id)
                for vi in validated_items:
                    self.order_dao.create_order_item(
                        order_id=order_id,
                        item_id=vi["item_id"],
                        item_name_snapshot=vi["item_name_snapshot"],
                        quantity=vi["quantity"],
                        unit_price=float(vi["unit_price"]),
                        subtotal=float(vi["subtotal"]),
                        note=vi["note"],
                    )

            self.order_dao.update_order_header(order_id, new_table_id, float(new_total))
            self.conn.commit()
            return self.get_order_details(order_id)
        except Exception:
            self.conn.rollback()
            raise

    def list_orders(self, status=None, reservation_id=None, table_id=None, date_str=None, sort_order="desc", limit=50, offset=0):
        orders = self.order_dao.list_orders(
            status=status,
            reservation_id=reservation_id,
            table_id=table_id,
            date_str=date_str,
            sort_order=sort_order,
            limit=limit,
            offset=offset,
        )
        for o in orders:
            o["total_amount"] = float(o["total_amount"])
            o["items"] = self.order_dao.get_order_items(o["order_id"])
            for it in o["items"]:
                it["unit_price"] = float(it["unit_price"])
                it["subtotal"] = float(it["subtotal"])
        return orders

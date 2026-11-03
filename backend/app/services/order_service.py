from decimal import Decimal
from backend.app.daos.order_dao import OrderDAO
from backend.app.daos.menu_dao import MenuDAO
from backend.app.daos.table_dao import TableDAO

class OrderService:
    ALLOWED_TRANSITIONS = {
        "PENDING": {"CONFIRMED", "CANCELLED"},
        "CONFIRMED": {"PREPARING", "CANCELLED"},
        "PREPARING": {"READY"},
        "READY": {"COMPLETED"},
        "COMPLETED": set(),
        "CANCELLED": set()
    }

    def __init__(self, conn):
        self.conn = conn
        self.order_dao = OrderDAO(conn)
        self.menu_dao = MenuDAO(conn)
        self.table_dao = TableDAO(conn)

    def calculate_and_validate_items(self, items_input: list):
        """
        REQ-005: 購物車校驗與金額重算
        1. 檢查數量為正整數
        2. 檢查餐點存在且處於供應狀態 (is_available == 1)
        3. 以資料庫有效價格為準計算小計與總額 (使用 Decimal)
        4. 保存餐點名稱快照
        """
        if not items_input or not isinstance(items_input, list):
            raise ValueError("Order must contain at least one item")

        validated_items = []
        total_amount = Decimal("0.00")

        for entry in items_input:
            if not isinstance(entry, dict):
                raise ValueError("Invalid item format in order list")

            item_id = entry.get("item_id")
            quantity = entry.get("quantity")
            note = entry.get("note", "")

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

            if not db_item.get("is_available"):
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

    def create_order(self, order_type: str, items_input: list, user_id=None, reservation_id=None, table_id=None, status="PENDING"):
        """
        Creates an order and its item snapshots in a transaction.
        """
        # Validate table if table_id is provided
        if table_id is not None:
            all_tables = {t["table_id"]: t for t in self.table_dao.get_all_tables(status=None)}
            if table_id not in all_tables:
                raise ValueError(f"Table {table_id} does not exist")
            if all_tables[table_id]["status"] != "ACTIVE":
                raise ValueError(f"Table {table_id} is not active ({all_tables[table_id]['status']})")

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

    def list_orders(self, status=None, reservation_id=None, table_id=None, date_str=None, limit=50, offset=0):
        orders = self.order_dao.list_orders(status=status, reservation_id=reservation_id, table_id=table_id, date_str=date_str, limit=limit, offset=offset)
        for o in orders:
            o["total_amount"] = float(o["total_amount"])
            o["items"] = self.order_dao.get_order_items(o["order_id"])
            for it in o["items"]:
                it["unit_price"] = float(it["unit_price"])
                it["subtotal"] = float(it["subtotal"])
        return orders

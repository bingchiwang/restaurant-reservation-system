import pytest
from datetime import datetime, timedelta
from backend.app.utils.db import get_connection
from backend.app.utils.auth import hash_password

@pytest.fixture
def seed_order_test_data(app):
    """
    Seeds admin user, tables, categories, active items, and an off-shelf item.
    """
    conn = get_connection(app.config)
    cursor = conn.cursor()

    cursor.execute("DELETE FROM order_items")
    cursor.execute("DELETE FROM orders")
    cursor.execute("DELETE FROM reservation_tables")
    cursor.execute("DELETE FROM reservation_guests")
    cursor.execute("DELETE FROM reservations")
    cursor.execute("DELETE FROM menu_items")
    cursor.execute("DELETE FROM menu_categories")
    cursor.execute("DELETE FROM dining_tables")
    cursor.execute("DELETE FROM users")

    # Admin
    admin_pwd = hash_password("Manager123!")
    cursor.execute("""
        INSERT INTO users (user_id, email, password_hash, display_name, role, status)
        VALUES (1, 'admin@test.com', ?, '管理者', 'ADMIN', 'ACTIVE')
    """, (admin_pwd,))

    # Dining Tables
    cursor.execute("INSERT INTO dining_tables (table_id, table_name, capacity, status) VALUES (1, 'T-01', 4, 'ACTIVE')")
    cursor.execute("INSERT INTO dining_tables (table_id, table_name, capacity, status) VALUES (2, 'T-02', 4, 'MAINTENANCE')")

    # Menu Categories
    cursor.execute("INSERT INTO menu_categories (category_id, name, status, sort_order) VALUES (1, '主廚精選', 'ACTIVE', 1)")

    # Menu Items
    cursor.execute("""
        INSERT INTO menu_items (item_id, category_id, name, description, price, is_available)
        VALUES (1, 1, '義式青醬烤雞麵', '羅勒青醬、現煎溫體雞腿肉', 280.00, 1)
    """)
    cursor.execute("""
        INSERT INTO menu_items (item_id, category_id, name, description, price, is_available)
        VALUES (2, 1, '黑松露野菇燉飯', '義大利米佐松露白醬', 320.00, 1)
    """)
    # Off-shelf item
    cursor.execute("""
        INSERT INTO menu_items (item_id, category_id, name, description, price, is_available)
        VALUES (3, 1, '售罄限定和牛堡', '已售完下架', 450.00, 0)
    """)

    conn.commit()
    conn.close()

def get_admin_token(client):
    res = client.post("/api/v1/auth/login", json={
        "email": "admin@test.com",
        "password": "Manager123!"
    })
    return res.get_json()["data"]["token"]

def test_order_amount_backend_recalculation(client, seed_order_test_data):
    """
    REQ-005: 訂單金額由後端重新計算，防範前端竄改金額。
    Item 1 ($280) * 2 + Item 2 ($320) * 1 = $880.00
    前端送出 total_amount = 1.00，後端計算後必須為 880.00。
    """
    response = client.post("/api/v1/orders", json={
        "table_id": 1,
        "total_amount": 1.00,  # 試圖竄改總額
        "items": [
            {"item_id": 1, "quantity": 2, "note": "麵硬一點"},
            {"item_id": 2, "quantity": 1}
        ]
    })
    assert response.status_code == 201
    order = response.get_json()["data"]
    assert order["total_amount"] == 880.00
    assert len(order["items"]) == 2

    # Check snapshots
    item1 = [i for i in order["items"] if i["item_id"] == 1][0]
    assert item1["item_name_snapshot"] == "義式青醬烤雞麵"
    assert item1["unit_price"] == 280.00
    assert item1["subtotal"] == 560.00
    assert item1["note"] == "麵硬一點"

def test_order_with_off_shelf_item_or_invalid_quantity(client, seed_order_test_data):
    """
    REQ-005: 下架餐點不得加入訂單，餐點數量必須大於 0。
    """
    # 1. 包含已下架餐點 (Item 3 is_available = 0)
    res_off_shelf = client.post("/api/v1/orders", json={
        "table_id": 1,
        "items": [{"item_id": 3, "quantity": 1}]
    })
    assert res_off_shelf.status_code == 400
    assert "not available" in res_off_shelf.get_json()["message"]

    # 2. 數量為 0 或負數
    res_neg_qty = client.post("/api/v1/orders", json={
        "table_id": 1,
        "items": [{"item_id": 1, "quantity": -2}]
    })
    assert res_neg_qty.status_code == 400
    assert "greater than 0" in res_neg_qty.get_json()["message"]

def test_reservation_with_pre_order(client, seed_order_test_data):
    """
    REQ-006: 預約時可同時預點餐，預約主檔與訂單正確關聯，明細快照正確保存。
    """
    target_time = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d 12:30")
    res = client.post("/api/v1/reservations", json={
        "party_size": 2,
        "reservation_time": target_time,
        "guest_name": "美食家林先生",
        "guest_phone": "0911222333",
        "items": [
            {"item_id": 1, "quantity": 1},
            {"item_id": 2, "quantity": 2}
        ]
    })
    assert res.status_code == 201
    data = res.get_json()["data"]
    assert "pre_order" in data
    order = data["pre_order"]
    assert order["order_type"] == "PRE_ORDER"
    assert order["reservation_id"] == data["reservation_id"]
    # 280 * 1 + 320 * 2 = 920.00
    assert order["total_amount"] == 920.00
    assert len(order["items"]) == 2

def test_reservation_pre_order_atomic_rollback(client, seed_order_test_data, app):
    """
    REQ-006: 若預點餐有下架餐點，預約與訂單應全數回滾，不得留下孤立預約。
    """
    target_time = (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d 18:00")
    res = client.post("/api/v1/reservations", json={
        "party_size": 2,
        "reservation_time": target_time,
        "guest_name": "回滾測試者",
        "guest_phone": "0999000111",
        "items": [
            {"item_id": 3, "quantity": 1}  # Item 3 is off-shelf!
        ]
    })
    assert res.status_code == 400

    # Verify atomic rollback in DB
    conn = get_connection(app.config)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM reservation_guests WHERE guest_name = '回滾測試者'")
    assert cursor.fetchone() is None
    cursor.execute("SELECT * FROM orders WHERE reservation_id IS NOT NULL")
    assert cursor.fetchone() is None
    conn.close()

def test_dine_in_table_validation(client, seed_order_test_data):
    """
    REQ-007: 現場點餐驗證桌位有效性，維護中桌位不得建立現場訂單。
    """
    # Table 2 is MAINTENANCE
    res_maint = client.post("/api/v1/orders", json={
        "table_id": 2,
        "items": [{"item_id": 1, "quantity": 1}]
    })
    assert res_maint.status_code == 400
    assert "not active" in res_maint.get_json()["message"]

    # Table 9999 does not exist
    res_none = client.post("/api/v1/orders", json={
        "table_id": 9999,
        "items": [{"item_id": 1, "quantity": 1}]
    })
    assert res_none.status_code == 400

def test_order_status_state_machine(client, seed_order_test_data):
    """
    REQ-008: 訂單狀態機轉移驗證
    PENDING -> CONFIRMED -> PREPARING -> READY -> COMPLETED
    非法跳轉如 COMPLETED -> PREPARING 應報錯 400。
    """
    token = get_admin_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create order (initial state: PENDING)
    create_res = client.post("/api/v1/orders", json={
        "table_id": 1,
        "items": [{"item_id": 1, "quantity": 1}]
    })
    order_id = create_res.get_json()["data"]["order_id"]
    assert create_res.get_json()["data"]["status"] == "PENDING"

    # 2. PENDING -> CONFIRMED
    s1 = client.patch(f"/api/v1/admin/orders/{order_id}/status", json={"status": "CONFIRMED"}, headers=headers)
    assert s1.status_code == 200
    assert s1.get_json()["data"]["status"] == "CONFIRMED"

    # 3. CONFIRMED -> PREPARING
    s2 = client.patch(f"/api/v1/admin/orders/{order_id}/status", json={"status": "PREPARING"}, headers=headers)
    assert s2.status_code == 200
    assert s2.get_json()["data"]["status"] == "PREPARING"

    # 4. PREPARING -> READY
    s3 = client.patch(f"/api/v1/admin/orders/{order_id}/status", json={"status": "READY"}, headers=headers)
    assert s3.status_code == 200
    assert s3.get_json()["data"]["status"] == "READY"

    # 5. READY -> COMPLETED
    s4 = client.patch(f"/api/v1/admin/orders/{order_id}/status", json={"status": "COMPLETED"}, headers=headers)
    assert s4.status_code == 200
    assert s4.get_json()["data"]["status"] == "COMPLETED"

    # 6. COMPLETED -> PREPARING (Illegal reversal -> 400)
    s5 = client.patch(f"/api/v1/admin/orders/{order_id}/status", json={"status": "PREPARING"}, headers=headers)
    assert s5.status_code == 400
    assert "Invalid status transition" in s5.get_json()["message"]

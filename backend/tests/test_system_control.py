import pytest
from datetime import datetime, timedelta
from backend.app.utils.db import get_connection
from backend.app.utils.auth import hash_password

@pytest.fixture
def seed_control_data(app):
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
    cursor.execute("""
        UPDATE store_settings
        SET store_status = 'OPEN',
            reservations_enabled = 1,
            ordering_enabled = 1,
            pre_order_enabled = 1,
            announcement_text = '',
            announcement_type = 'info',
            opening_time = '11:00',
            closing_time = '21:30'
        WHERE setting_id = 1
    """)

    cursor.execute("""
        INSERT INTO users (user_id, email, password_hash, display_name, role, status)
        VALUES (1, 'admin@control.com', ?, '系統管理員', 'ADMIN', 'ACTIVE')
    """, (hash_password("ControlPass123!"),))

    cursor.execute("""
        INSERT INTO users (user_id, email, password_hash, display_name, role, status)
        VALUES (2, 'member@control.com', ?, '一般會員', 'MEMBER', 'ACTIVE')
    """, (hash_password("MemberPass123!"),))

    cursor.execute("INSERT INTO dining_tables (table_id, table_name, capacity, status) VALUES (1, 'A-01', 2, 'ACTIVE')")
    cursor.execute("INSERT INTO dining_tables (table_id, table_name, capacity, status) VALUES (2, 'B-01', 4, 'ACTIVE')")
    cursor.execute("INSERT INTO dining_tables (table_id, table_name, capacity, status) VALUES (3, 'C-01', 6, 'MAINTENANCE')")

    cursor.execute("INSERT INTO menu_categories (category_id, name, status, sort_order) VALUES (1, '主餐', 'ACTIVE', 1)")
    cursor.execute("""
        INSERT INTO menu_items (item_id, category_id, name, description, price, is_available)
        VALUES (1, 1, '松露燉飯', '黑松露野菇', 300.00, 1)
    """)
    cursor.execute("""
        INSERT INTO menu_items (item_id, category_id, name, description, price, is_available)
        VALUES (2, 1, '肋眼牛排', '美國熟成肋眼', 650.00, 1)
    """)
    cursor.execute("""
        INSERT INTO menu_items (item_id, category_id, name, description, price, is_available)
        VALUES (3, 1, '停售龍蝦', '已下架', 900.00, 0)
    """)

    conn.commit()
    conn.close()

    yield

    # Reset store_settings back to defaults so subsequent test files are unaffected
    conn = get_connection(app.config)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE store_settings
        SET store_status = 'OPEN',
            reservations_enabled = 1,
            ordering_enabled = 1,
            pre_order_enabled = 1,
            announcement_text = '',
            announcement_type = 'info',
            opening_time = '11:00',
            closing_time = '21:30'
        WHERE setting_id = 1
    """)
    conn.commit()
    conn.close()

def get_token(client, email, password):
    res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    return res.get_json()["data"]["token"]

def test_unified_routes_and_admin_console(client, seed_control_data):
    """Unified Flask server hosts both customer frontend / and backend console /admin."""
    res_home = client.get("/")
    assert res_home.status_code == 200

    res_admin = client.get("/admin")
    assert res_admin.status_code == 200
    assert "後端管理控制中心" in res_admin.get_data(as_text=True)

def test_public_config_and_admin_authorization(client, seed_control_data):
    """Public /system/config exposes storefront state; admin config requires ADMIN role."""
    pub = client.get("/api/v1/system/config")
    assert pub.status_code == 200
    data = pub.get_json()["data"]
    assert data["store_status"] == "OPEN"
    assert data["reservations_enabled"] is True
    assert data["ordering_enabled"] is True
    # Only ACTIVE tables appear in active_tables
    table_ids = [t["table_id"] for t in data["active_tables"]]
    assert table_ids == [1, 2]

    # Unauthorized & member forbidden
    assert client.patch("/api/v1/admin/system/config", json={"store_status": "CLOSED"}).status_code == 401
    member_tok = get_token(client, "member@control.com", "MemberPass123!")
    assert client.patch(
        "/api/v1/admin/system/config",
        json={"store_status": "CLOSED"},
        headers={"Authorization": f"Bearer {member_tok}"}
    ).status_code == 403

def test_backend_controls_store_status_and_feature_toggles(client, seed_control_data):
    """Backend store_status and toggles strictly enforce reservation and ordering access."""
    admin_tok = get_token(client, "admin@control.com", "ControlPass123!")
    headers = {"Authorization": f"Bearer {admin_tok}"}
    valid_time = (datetime.now() + timedelta(days=2)).replace(hour=13, minute=0).strftime("%Y-%m-%d %H:%M")

    # 1. Pause reservations only + set announcement
    patch_res = client.patch("/api/v1/admin/system/config", json={
        "reservations_enabled": False,
        "announcement_text": "今日訂位已滿",
        "announcement_type": "warning"
    }, headers=headers)
    assert patch_res.status_code == 200
    assert patch_res.get_json()["data"]["reservations_enabled"] is False
    assert patch_res.get_json()["data"]["announcement_text"] == "今日訂位已滿"

    # Reservation blocked (403), dine-in ordering still works (201)
    book_blocked = client.post("/api/v1/reservations", json={
        "party_size": 2, "reservation_time": valid_time, "guest_name": "王小明", "guest_phone": "0912345678"
    })
    assert book_blocked.status_code == 403
    assert book_blocked.get_json()["error"] == "SERVICE_PAUSED"

    order_ok = client.post("/api/v1/orders", json={
        "table_id": 1, "items": [{"item_id": 1, "quantity": 1}]
    })
    assert order_ok.status_code == 201

    # 2. Switch store_status to MAINTENANCE -> both reservations & ordering blocked
    client.patch("/api/v1/admin/system/config", json={
        "store_status": "MAINTENANCE",
        "reservations_enabled": True,
        "ordering_enabled": True
    }, headers=headers)
    assert client.post("/api/v1/orders", json={"table_id": 1, "items": [{"item_id": 1, "quantity": 1}]}).status_code == 403
    assert client.post("/api/v1/reservations", json={
        "party_size": 2, "reservation_time": valid_time, "guest_name": "王小明", "guest_phone": "0912345678"
    }).status_code == 403

    # 3. Restore OPEN + disable pre_order_enabled -> pre-order blocked, plain reservation allowed
    client.patch("/api/v1/admin/system/config", json={
        "store_status": "OPEN",
        "pre_order_enabled": False
    }, headers=headers)
    pre_blocked = client.post("/api/v1/reservations", json={
        "party_size": 2, "reservation_time": valid_time, "guest_name": "王小明", "guest_phone": "0912345678",
        "items": [{"item_id": 1, "quantity": 1}]
    })
    assert pre_blocked.status_code == 403
    plain_ok = client.post("/api/v1/reservations", json={
        "party_size": 2, "reservation_time": valid_time, "guest_name": "王小明", "guest_phone": "0912345678"
    })
    assert plain_ok.status_code == 201

def test_backend_controls_dynamic_opening_hours(client, seed_control_data):
    """Updating opening/closing hours in backend immediately enforces valid booking hours."""
    admin_tok = get_token(client, "admin@control.com", "ControlPass123!")
    headers = {"Authorization": f"Bearer {admin_tok}"}

    client.patch("/api/v1/admin/system/config", json={
        "opening_time": "12:00",
        "closing_time": "20:00"
    }, headers=headers)

    t_1130 = (datetime.now() + timedelta(days=2)).replace(hour=11, minute=30).strftime("%Y-%m-%d %H:%M")
    t_1230 = (datetime.now() + timedelta(days=2)).replace(hour=12, minute=30).strftime("%Y-%m-%d %H:%M")

    res_early = client.post("/api/v1/reservations", json={
        "party_size": 2, "reservation_time": t_1130, "guest_name": "早鳥", "guest_phone": "0911222333"
    })
    assert res_early.status_code == 400
    assert "12:00 ~ 20:00" in res_early.get_json()["message"]

    res_ok = client.post("/api/v1/reservations", json={
        "party_size": 2, "reservation_time": t_1230, "guest_name": "準時", "guest_phone": "0911222333"
    })
    assert res_ok.status_code == 201

def test_admin_table_management_and_frontend_sync(client, seed_control_data):
    """REQ-013: Admin can create/update/disable tables and active_tables reflects immediately."""
    admin_tok = get_token(client, "admin@control.com", "ControlPass123!")
    headers = {"Authorization": f"Bearer {admin_tok}"}

    # Create table
    c_res = client.post("/api/v1/admin/tables", json={"table_name": "VIP-1", "capacity": 10}, headers=headers)
    assert c_res.status_code == 201
    new_id = c_res.get_json()["data"]["table_id"]

    # Disable table 1
    u_res = client.patch(f"/api/v1/admin/tables/{new_id}", json={"status": "DISABLED", "capacity": 12}, headers=headers)
    assert u_res.status_code == 200
    assert u_res.get_json()["data"]["status"] == "DISABLED"
    assert u_res.get_json()["data"]["capacity"] == 12

    # Check active_tables excludes disabled table
    pub = client.get("/api/v1/system/config").get_json()["data"]["active_tables"]
    assert all(t["table_id"] != new_id for t in pub)

    # Dine-in order for disabled table fails
    ord_res = client.post("/api/v1/orders", json={"table_id": new_id, "items": [{"item_id": 1, "quantity": 1}]})
    assert ord_res.status_code == 400
    assert "not active" in ord_res.get_json()["message"]

def test_admin_edit_order_content_and_cancel_preparing(client, seed_control_data):
    """Admin can edit order table/items with Decimal recalculation and cancel PREPARING orders."""
    admin_tok = get_token(client, "admin@control.com", "ControlPass123!")
    headers = {"Authorization": f"Bearer {admin_tok}"}

    # 1. Create order: table 1, item 1 (300) * 1 = 300
    create_res = client.post("/api/v1/orders", json={
        "table_id": 1,
        "items": [{"item_id": 1, "quantity": 1}]
    })
    assert create_res.status_code == 201
    order_id = create_res.get_json()["data"]["order_id"]

    # 2. Edit order: move to table 2, change to item 1 * 2 (600) + item 2 * 1 (650) = 1250
    edit_res = client.patch(f"/api/v1/admin/orders/{order_id}", json={
        "table_id": 2,
        "items": [
            {"item_id": 1, "quantity": 2, "note": "加辣"},
            {"item_id": 2, "quantity": 1}
        ]
    }, headers=headers)
    assert edit_res.status_code == 200
    edited = edit_res.get_json()["data"]
    assert edited["table_id"] == 2
    assert edited["total_amount"] == 1250.0
    assert len(edited["items"]) == 2

    # 3. Advance to CONFIRMED -> PREPARING -> CANCELLED
    assert client.patch(f"/api/v1/admin/orders/{order_id}/status", json={"status": "CONFIRMED"}, headers=headers).status_code == 200
    assert client.patch(f"/api/v1/admin/orders/{order_id}/status", json={"status": "PREPARING"}, headers=headers).status_code == 200
    cancel_res = client.patch(f"/api/v1/admin/orders/{order_id}/status", json={"status": "CANCELLED"}, headers=headers)
    assert cancel_res.status_code == 200
    assert cancel_res.get_json()["data"]["status"] == "CANCELLED"

    # 4. Cancelled order cannot be edited
    err_edit = client.patch(f"/api/v1/admin/orders/{order_id}", json={"table_id": 1}, headers=headers)
    assert err_edit.status_code == 400
    assert "cannot be modified" in err_edit.get_json()["message"]

def test_admin_menu_list_includes_off_shelf_and_bumps_config(client, seed_control_data):
    """Admin /admin/menu returns all items including off-shelf and bumps config updated_at."""
    admin_tok = get_token(client, "admin@control.com", "ControlPass123!")
    headers = {"Authorization": f"Bearer {admin_tok}"}

    all_items = client.get("/api/v1/admin/menu", headers=headers).get_json()["data"]
    assert len(all_items) == 3

    before_ts = client.get("/api/v1/system/config").get_json()["data"]["updated_at"]
    toggle_res = client.patch("/api/v1/admin/menu/3/availability", json={"is_available": True}, headers=headers)
    assert toggle_res.status_code == 200
    after_ts = client.get("/api/v1/system/config").get_json()["data"]["updated_at"]
    assert after_ts != before_ts

    # Now public menu also shows item 3
    pub_ids = [i["item_id"] for i in client.get("/api/v1/menu").get_json()["data"]]
    assert 3 in pub_ids

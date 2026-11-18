import pytest
from datetime import datetime, timedelta
from backend.app.utils.db import get_connection
from backend.app.utils.auth import hash_password

@pytest.fixture
def seed_member_test_data(app):
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
            opening_time = '11:00',
            closing_time = '21:30'
        WHERE setting_id = 1
    """)

    cursor.execute("""
        INSERT INTO users (user_id, email, password_hash, display_name, role, status)
        VALUES (1, 'admin@membertest.com', ?, '管理員', 'ADMIN', 'ACTIVE')
    """, (hash_password("AdminPass123!"),))

    cursor.execute("""
        INSERT INTO users (user_id, email, password_hash, display_name, role, status)
        VALUES (2, 'alice@example.com', ?, 'Alice', 'MEMBER', 'ACTIVE')
    """, (hash_password("AlicePass123!"),))

    cursor.execute("""
        INSERT INTO users (user_id, email, password_hash, display_name, role, status)
        VALUES (3, 'bob@example.com', ?, 'Bob', 'MEMBER', 'ACTIVE')
    """, (hash_password("BobPass123!"),))

    cursor.execute("INSERT INTO dining_tables (table_id, table_name, capacity, status) VALUES (1, 'A-01', 2, 'ACTIVE')")
    cursor.execute("INSERT INTO dining_tables (table_id, table_name, capacity, status) VALUES (2, 'B-01', 4, 'ACTIVE')")

    cursor.execute("INSERT INTO menu_categories (category_id, name, status, sort_order) VALUES (1, '主餐', 'ACTIVE', 1)")
    cursor.execute("""
        INSERT INTO menu_items (item_id, category_id, name, description, price, is_available)
        VALUES (1, 1, '經典義大利麵', '番茄肉醬', 260.00, 1)
    """)

    conn.commit()
    conn.close()

def test_member_register_validation_and_login(client, seed_member_test_data):
    """REQ-011: 會員註冊重複驗證、密碼長度驗證與登入錯誤不洩漏資訊"""
    # Duplicate email
    dup = client.post("/api/v1/auth/register", json={
        "email": "alice@example.com",
        "password": "Password123",
        "display_name": "Alice2"
    })
    assert dup.status_code == 400
    assert "already registered" in dup.get_json()["message"]

    # Short password
    short_pwd = client.post("/api/v1/auth/register", json={
        "email": "new@example.com",
        "password": "123",
        "display_name": "NewUser"
    })
    assert short_pwd.status_code == 400

    # Invalid email
    bad_email = client.post("/api/v1/auth/register", json={
        "email": "not-an-email",
        "password": "Password123",
        "display_name": "NewUser"
    })
    assert bad_email.status_code == 400

    # Successful registration
    reg = client.post("/api/v1/auth/register", json={
        "email": "carol@example.com",
        "password": "CarolPass123",
        "display_name": "Carol"
    })
    assert reg.status_code == 201
    reg_data = reg.get_json()["data"]
    assert reg_data["role"] == "MEMBER"
    assert reg_data["token"]

    # Login failure does not leak account existence
    err_missing = client.post("/api/v1/auth/member/login", json={
        "email": "unknown@example.com",
        "password": "wrong"
    })
    err_wrong_pwd = client.post("/api/v1/auth/member/login", json={
        "email": "carol@example.com",
        "password": "wrong"
    })
    assert err_missing.status_code == 401
    assert err_wrong_pwd.status_code == 401
    assert err_missing.get_json()["message"] == err_wrong_pwd.get_json()["message"]

def test_customer_member_login_blocks_admin_account(client, seed_member_test_data):
    """顧客前端會員登入端點 (/auth/member/login) 嚴格禁止管理員帳號登入"""
    res_admin = client.post("/api/v1/auth/member/login", json={
        "email": "admin@membertest.com",
        "password": "AdminPass123!"
    })
    assert res_admin.status_code == 403
    assert res_admin.get_json()["error"] == "FORBIDDEN"

    res_member = client.post("/api/v1/auth/member/login", json={
        "email": "alice@example.com",
        "password": "AlicePass123!"
    })
    assert res_member.status_code == 200
    assert res_member.get_json()["data"]["user"]["role"] == "MEMBER"

def test_member_profile_and_password_update(client, seed_member_test_data):
    """REQ-011: 會員查看與更新個人基本資料"""
    assert client.get("/api/v1/me").status_code == 401

    login = client.post("/api/v1/auth/member/login", json={
        "email": "alice@example.com",
        "password": "AlicePass123!"
    })
    token = login.get_json()["data"]["token"]
    headers = {"Authorization": f"Bearer {token}"}

    me = client.get("/api/v1/me", headers=headers)
    assert me.status_code == 200
    assert me.get_json()["data"]["display_name"] == "Alice"

    upd = client.patch("/api/v1/me", json={"display_name": "Alice Lin"}, headers=headers)
    assert upd.status_code == 200
    assert upd.get_json()["data"]["display_name"] == "Alice Lin"

def test_member_reservation_and_order_history_with_privacy(client, seed_member_test_data):
    """REQ-011 & REQ-015: 會員預約/預點餐/現場點餐自動關聯 user_id 與隱私隔離"""
    alice_tok = client.post("/api/v1/auth/member/login", json={
        "email": "alice@example.com", "password": "AlicePass123!"
    }).get_json()["data"]["token"]
    bob_tok = client.post("/api/v1/auth/member/login", json={
        "email": "bob@example.com", "password": "BobPass123!"
    }).get_json()["data"]["token"]

    alice_h = {"Authorization": f"Bearer {alice_tok}"}
    bob_h = {"Authorization": f"Bearer {bob_tok}"}

    slot = (datetime.now() + timedelta(days=2)).replace(hour=12, minute=30).strftime("%Y-%m-%d %H:%M")

    # Alice books with pre-order
    res_create = client.post("/api/v1/reservations", json={
        "party_size": 2,
        "reservation_time": slot,
        "guest_name": "Alice",
        "guest_phone": "0912345678",
        "items": [{"item_id": 1, "quantity": 2}]
    }, headers=alice_h)
    assert res_create.status_code == 201
    res_data = res_create.get_json()["data"]
    res_code = res_data["reservation_code"]
    pre_order_id = res_data["pre_order"]["order_id"]

    # Alice creates a dine-in order
    ord_create = client.post("/api/v1/orders", json={
        "table_id": 2,
        "items": [{"item_id": 1, "quantity": 1}]
    }, headers=alice_h)
    assert ord_create.status_code == 201
    dine_in_id = ord_create.get_json()["data"]["order_id"]

    # Alice sees 1 reservation and 2 orders in /me/*
    my_res = client.get("/api/v1/me/reservations", headers=alice_h).get_json()["data"]
    assert len(my_res) == 1
    assert my_res[0]["reservation_code"] == res_code

    my_orders = client.get("/api/v1/me/orders", headers=alice_h).get_json()["data"]
    assert len(my_orders) == 2
    assert my_orders[0]["items"][0]["item_name_snapshot"] == "經典義大利麵"

    # Privacy checks: Unauthenticated & Bob cannot view Alice's private order or reservation
    assert client.get(f"/api/v1/orders/{dine_in_id}").status_code == 401
    assert client.get(f"/api/v1/orders/{dine_in_id}", headers=bob_h).status_code == 403
    assert client.get(f"/api/v1/orders/{pre_order_id}", headers=alice_h).status_code == 200

    assert client.get(f"/api/v1/reservations/{res_code}?phone=0912345678").status_code == 403
    assert client.get(f"/api/v1/reservations/{res_code}", headers=bob_h).status_code == 403
    assert client.get(f"/api/v1/reservations/{res_code}", headers=alice_h).status_code == 200

    # Alice cancels her own reservation using member auth
    cancel_res = client.post(f"/api/v1/reservations/{res_code}/cancel", json={}, headers=alice_h)
    assert cancel_res.status_code == 200
    assert cancel_res.get_json()["data"]["status"] == "CANCELLED"

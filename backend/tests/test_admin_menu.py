import pytest
from backend.app.utils.db import get_connection
from backend.app.utils.auth import hash_password, generate_token

@pytest.fixture
def seed_admin_and_menu(app):
    """
    Seeds an admin user, a regular member user, and a category.
    """
    conn = get_connection(app.config)
    cursor = conn.cursor()

    cursor.execute("DELETE FROM users")
    cursor.execute("DELETE FROM menu_items")
    cursor.execute("DELETE FROM menu_categories")

    # Seed Admin User
    admin_pwd = hash_password("AdminPass123!")
    cursor.execute("""
        INSERT INTO users (user_id, email, password_hash, display_name, role, status)
        VALUES (1, 'admin@restaurant.com', ?, '系統管理員', 'ADMIN', 'ACTIVE')
    """, (admin_pwd,))

    # Seed Member User
    member_pwd = hash_password("MemberPass123!")
    cursor.execute("""
        INSERT INTO users (user_id, email, password_hash, display_name, role, status)
        VALUES (2, 'member@restaurant.com', ?, '一般會員', 'MEMBER', 'ACTIVE')
    """, (member_pwd,))

    # Seed Category
    cursor.execute("""
        INSERT INTO menu_categories (category_id, name, status, sort_order)
        VALUES (1, '甜點', 'ACTIVE', 1)
    """)

    # Seed Initial Item
    cursor.execute("""
        INSERT INTO menu_items (item_id, category_id, name, description, price, is_available)
        VALUES (1, 1, '提拉米蘇', '義大利傳統經典風味', 150.00, 1)
    """)

    conn.commit()
    conn.close()

def test_admin_auth_required_for_menu_management(client, seed_admin_and_menu):
    """
    REQ-009: 訪客未登入存取管理 API 回傳 401
    """
    response = client.post("/api/v1/admin/menu", json={
        "category_id": 1,
        "name": "焦糖布丁",
        "price": 100.0
    })
    assert response.status_code == 401
    assert response.get_json()["error"] == "UNAUTHORIZED"

def test_regular_member_forbidden_from_admin_menu(client, seed_admin_and_menu):
    """
    REQ-009: 一般會員存取管理 API 回傳 403
    """
    # Login as regular member
    login_res = client.post("/api/v1/auth/login", json={
        "email": "member@restaurant.com",
        "password": "MemberPass123!"
    })
    assert login_res.status_code == 200
    token = login_res.get_json()["data"]["token"]

    # Attempt to call admin API
    response = client.post("/api/v1/admin/menu", json={
        "category_id": 1,
        "name": "焦糖布丁",
        "price": 100.0
    }, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403
    assert response.get_json()["error"] == "FORBIDDEN"

def test_admin_create_menu_item_success(client, seed_admin_and_menu):
    """
    REQ-010: 管理員成功新增餐點
    """
    # Login as admin
    login_res = client.post("/api/v1/auth/login", json={
        "email": "admin@restaurant.com",
        "password": "AdminPass123!"
    })
    assert login_res.status_code == 200
    token = login_res.get_json()["data"]["token"]

    response = client.post("/api/v1/admin/menu", json={
        "category_id": 1,
        "name": "焦糖烤布蕾",
        "description": "脆糖焦香與綿密卡士達",
        "price": 120.0,
        "is_available": True
    }, headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 201
    item = response.get_json()["data"]
    assert item["name"] == "焦糖烤布蕾"
    assert item["price"] == 120.0
    assert item["is_available"] is True

    # Check it appears in public menu
    public_res = client.get("/api/v1/menu")
    names = [i["name"] for i in public_res.get_json()["data"]]
    assert "焦糖烤布蕾" in names

def test_admin_create_menu_item_validation(client, seed_admin_and_menu):
    """
    REQ-010: 價格為負數或分類不存在時應拒絕新增
    """
    login_res = client.post("/api/v1/auth/login", json={
        "email": "admin@restaurant.com",
        "password": "AdminPass123!"
    })
    token = login_res.get_json()["data"]["token"]

    # Negative price
    neg_res = client.post("/api/v1/admin/menu", json={
        "category_id": 1,
        "name": "負元甜點",
        "price": -50.0
    }, headers={"Authorization": f"Bearer {token}"})
    assert neg_res.status_code == 400
    assert "negative" in neg_res.get_json()["message"]

    # Non-existent category
    cat_res = client.post("/api/v1/admin/menu", json={
        "category_id": 9999,
        "name": "未知分類餐點",
        "price": 100.0
    }, headers={"Authorization": f"Bearer {token}"})
    assert cat_res.status_code == 400
    assert "does not exist" in cat_res.get_json()["message"]

def test_admin_update_item_and_availability(client, seed_admin_and_menu):
    """
    REQ-010: 管理員修改餐點資訊與切換下架狀態
    """
    login_res = client.post("/api/v1/auth/login", json={
        "email": "admin@restaurant.com",
        "password": "AdminPass123!"
    })
    token = login_res.get_json()["data"]["token"]

    # Update item price and name
    patch_res = client.patch("/api/v1/admin/menu/1", json={
        "name": "特級義式提拉米蘇",
        "price": 180.0
    }, headers={"Authorization": f"Bearer {token}"})
    assert patch_res.status_code == 200
    assert patch_res.get_json()["data"]["name"] == "特級義式提拉米蘇"
    assert patch_res.get_json()["data"]["price"] == 180.0

    # Toggle off-shelf
    avail_res = client.patch("/api/v1/admin/menu/1/availability", json={
        "is_available": False
    }, headers={"Authorization": f"Bearer {token}"})
    assert avail_res.status_code == 200
    assert avail_res.get_json()["data"]["is_available"] is False

    # Verify that public menu no longer includes this off-shelf item
    pub_res = client.get("/api/v1/menu")
    item_ids = [i["item_id"] for i in pub_res.get_json()["data"]]
    assert 1 not in item_ids

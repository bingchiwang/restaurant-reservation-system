import pytest
from backend.app.utils.db import get_connection

@pytest.fixture
def seed_menu_data(app):
    """
    Seeds initial categories and items for menu testing.
    """
    conn = get_connection(app.config)
    cursor = conn.cursor()
    
    # Clean tables
    cursor.execute("DELETE FROM order_items")
    cursor.execute("DELETE FROM menu_items")
    cursor.execute("DELETE FROM menu_categories")

    # Insert Categories
    cursor.execute("INSERT INTO menu_categories (category_id, name, status, sort_order) VALUES (1, '開胃菜', 'ACTIVE', 1)")
    cursor.execute("INSERT INTO menu_categories (category_id, name, status, sort_order) VALUES (2, '主餐', 'ACTIVE', 2)")
    cursor.execute("INSERT INTO menu_categories (category_id, name, status, sort_order) VALUES (3, '季節限定', 'HIDDEN', 99)")

    # Insert Items
    # Active items in category 1
    cursor.execute("""
        INSERT INTO menu_items (item_id, category_id, name, description, price, is_available)
        VALUES (1, 1, '松露薯條', '現炸脆薯佐主廚特製黑松露醬', 180.00, 1)
    """)
    cursor.execute("""
        INSERT INTO menu_items (item_id, category_id, name, description, price, is_available)
        VALUES (2, 1, '凱撒沙拉', '鮮脆羅美生菜搭配帕馬森起司', 160.00, 1)
    """)
    # Active item in category 2
    cursor.execute("""
        INSERT INTO menu_items (item_id, category_id, name, description, price, is_available)
        VALUES (3, 2, '爐烤肋眼牛排', '美國特選熟成肋眼牛排 10oz', 680.00, 1)
    """)
    # Unavailable (Sold out / Off-shelf) item in category 2
    cursor.execute("""
        INSERT INTO menu_items (item_id, category_id, name, description, price, is_available)
        VALUES (4, 2, '炭烤龍蝦燉飯', '季節限量現流龍蝦', 880.00, 0)
    """)
    # Item in hidden category
    cursor.execute("""
        INSERT INTO menu_items (item_id, category_id, name, description, price, is_available)
        VALUES (5, 3, '冬季限定草莓甜點', '草莓塔', 220.00, 1)
    """)

    conn.commit()
    conn.close()

def test_get_categories(client, seed_menu_data):
    """
    REQ-001: 顧客能獲取目前供應中的分類，不包含已隱藏分類
    """
    response = client.get("/api/v1/menu/categories")
    assert response.status_code == 200
    res_data = response.get_json()
    assert res_data["success"] is True
    
    categories = res_data["data"]
    assert len(categories) == 2
    cat_names = [c["name"] for c in categories]
    assert "開胃菜" in cat_names
    assert "主餐" in cat_names
    assert "季節限定" not in cat_names

def test_get_all_available_menu_items(client, seed_menu_data):
    """
    REQ-001: 顧客能查看所有供應中之餐點，下架餐點與隱藏分類餐點應被過濾
    """
    response = client.get("/api/v1/menu")
    assert response.status_code == 200
    res_data = response.get_json()
    assert res_data["success"] is True
    
    items = res_data["data"]
    # items 1, 2, 3 are available; item 4 is is_available=0, item 5 is category hidden
    assert len(items) == 3
    item_ids = [item["item_id"] for item in items]
    assert item_ids == [1, 2, 3]

    # Verify item fields
    first_item = items[0]
    assert first_item["name"] == "松露薯條"
    assert first_item["price"] == 180.0
    assert first_item["category_name"] == "開胃菜"
    assert first_item["is_available"] is True

def test_filter_menu_items_by_category(client, seed_menu_data):
    """
    REQ-001: 顧客可依指定分類篩選餐點
    """
    # Category 1: 開胃菜 (2 items)
    response = client.get("/api/v1/menu?category_id=1")
    assert response.status_code == 200
    data = response.get_json()["data"]
    assert len(data) == 2
    for item in data:
        assert item["category_id"] == 1

    # Category 2: 主餐 (1 available item: 爐烤肋眼牛排)
    response_cat2 = client.get("/api/v1/menu?category_id=2")
    assert response_cat2.status_code == 200
    data_cat2 = response_cat2.get_json()["data"]
    assert len(data_cat2) == 1
    assert data_cat2[0]["item_id"] == 3
    assert data_cat2[0]["name"] == "爐烤肋眼牛排"

def test_get_single_menu_item(client, seed_menu_data):
    """
    REQ-001: 查詢單一餐點詳情
    """
    response = client.get("/api/v1/menu/1")
    assert response.status_code == 200
    data = response.get_json()["data"]
    assert data["item_id"] == 1
    assert data["name"] == "松露薯條"
    assert data["price"] == 180.0

    # Non-existent item
    response_404 = client.get("/api/v1/menu/9999")
    assert response_404.status_code == 404
    assert response_404.get_json()["error"] == "ITEM_NOT_FOUND"

def test_invalid_category_parameter(client, seed_menu_data):
    """
    REQ-001: 輸入非法 category_id 參數應回傳 400
    """
    response = client.get("/api/v1/menu?category_id=invalid_id")
    assert response.status_code == 400
    assert response.get_json()["error"] == "BAD_REQUEST"

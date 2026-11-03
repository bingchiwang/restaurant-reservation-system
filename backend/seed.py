import os
import sys

root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from backend.app.utils.db import get_connection, init_sqlite_db
from backend.app.utils.auth import hash_password

def seed_data():
    conn = get_connection()
    init_sqlite_db(conn)
    cursor = conn.cursor()

    # 1. Seed Tables if empty
    cursor.execute("SELECT COUNT(*) as cnt FROM dining_tables")
    if cursor.fetchone()["cnt"] == 0:
        cursor.execute("INSERT INTO dining_tables (table_id, table_name, capacity, status) VALUES (1, 'A-01', 2, 'ACTIVE')")
        cursor.execute("INSERT INTO dining_tables (table_id, table_name, capacity, status) VALUES (2, 'A-02', 2, 'ACTIVE')")
        cursor.execute("INSERT INTO dining_tables (table_id, table_name, capacity, status) VALUES (3, 'B-01', 4, 'ACTIVE')")
        cursor.execute("INSERT INTO dining_tables (table_id, table_name, capacity, status) VALUES (4, 'B-02', 4, 'ACTIVE')")
        cursor.execute("INSERT INTO dining_tables (table_id, table_name, capacity, status) VALUES (5, 'C-01', 8, 'ACTIVE')")

    # 2. Seed Categories if empty
    cursor.execute("SELECT COUNT(*) as cnt FROM menu_categories")
    if cursor.fetchone()["cnt"] == 0:
        cursor.execute("INSERT INTO menu_categories (category_id, name, status, sort_order) VALUES (1, '開胃菜', 'ACTIVE', 1)")
        cursor.execute("INSERT INTO menu_categories (category_id, name, status, sort_order) VALUES (2, '主餐', 'ACTIVE', 2)")
        cursor.execute("INSERT INTO menu_categories (category_id, name, status, sort_order) VALUES (3, '甜點與飲品', 'ACTIVE', 3)")

    # 3. Seed Menu Items if empty
    cursor.execute("SELECT COUNT(*) as cnt FROM menu_items")
    if cursor.fetchone()["cnt"] == 0:
        cursor.execute("""
            INSERT INTO menu_items (category_id, name, description, price, is_available) VALUES
            (1, '松露起司脆薯', '主廚特製黑松露醬佐現炸酥脆薯條', 180.00, 1),
            (1, '經典凱撒沙拉', '鮮脆羅美生菜搭配帕馬森起司與特調凱撒醬', 160.00, 1),
            (2, '爐烤特選熟成肋眼牛排 (10oz)', '低溫熟成肋眼佐紅酒牛肉醬汁與時令烤時蔬', 680.00, 1),
            (2, '義式羅勒青醬舒肥烤雞麵', '每日手工青醬、溫體舒肥雞腿排與彈牙義大利麵', 280.00, 1),
            (2, '黑松露野菇燉飯', '義大利傳統長米、綜合野菇與頂級黑松露白醬', 320.00, 1),
            (3, '義式經典提拉米蘇', '馬斯卡彭起司佐濃縮咖啡浸潤手指餅乾', 150.00, 1),
            (3, '法式焦糖烤布蕾', '脆香焦糖表層與香草籽滑順卡士達', 120.00, 1),
            (3, '手工冷萃咖啡', '精選產區咖啡豆經 16 小時慢速冷萃', 120.00, 1)
        """)

    # 4. Seed Admin User if empty
    cursor.execute("SELECT COUNT(*) as cnt FROM users")
    if cursor.fetchone()["cnt"] == 0:
        admin_pwd = hash_password("admin123")
        cursor.execute("""
            INSERT INTO users (email, password_hash, display_name, role, status)
            VALUES ('admin@restaurant.com', ?, '系統管理員', 'ADMIN', 'ACTIVE')
        """, (admin_pwd,))

    conn.commit()
    conn.close()
    print("[*] Database initialized with default tables, menu items, and admin user.")

if __name__ == "__main__":
    seed_data()

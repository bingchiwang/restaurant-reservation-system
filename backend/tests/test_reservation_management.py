import pytest
from datetime import datetime, timedelta
from backend.app.utils.db import get_connection
from backend.app.utils.auth import hash_password

@pytest.fixture
def seed_admin_and_reservations(app):
    conn = get_connection(app.config)
    cursor = conn.cursor()

    cursor.execute("DELETE FROM users")
    cursor.execute("DELETE FROM reservation_tables")
    cursor.execute("DELETE FROM reservation_guests")
    cursor.execute("DELETE FROM reservations")
    cursor.execute("DELETE FROM dining_tables")

    # Seed Admin User
    admin_pwd = hash_password("AdminSecurePass!")
    cursor.execute("""
        INSERT INTO users (user_id, email, password_hash, display_name, role, status)
        VALUES (1, 'manager@restaurant.com', ?, '餐廳主管', 'ADMIN', 'ACTIVE')
    """, (admin_pwd,))

    # Seed Tables
    cursor.execute("INSERT INTO dining_tables (table_id, table_name, capacity, status) VALUES (1, 'T-01', 2, 'ACTIVE')")
    cursor.execute("INSERT INTO dining_tables (table_id, table_name, capacity, status) VALUES (2, 'T-02', 2, 'ACTIVE')")
    cursor.execute("INSERT INTO dining_tables (table_id, table_name, capacity, status) VALUES (3, 'T-03', 4, 'ACTIVE')")

    conn.commit()
    conn.close()

def get_admin_token(client):
    res = client.post("/api/v1/auth/login", json={
        "email": "manager@restaurant.com",
        "password": "AdminSecurePass!"
    })
    return res.get_json()["data"]["token"]

def test_guest_query_requires_phone_verification(client, seed_admin_and_reservations):
    """
    REQ-004: 訪客查詢預約必須核對登記電話，防止猜測號碼洩漏他人資料
    """
    target_time = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d 12:00")
    create_res = client.post("/api/v1/reservations", json={
        "party_size": 2,
        "reservation_time": target_time,
        "guest_name": "隱私測試者",
        "guest_phone": "0987654321"
    })
    code = create_res.get_json()["data"]["reservation_code"]

    # 1. 查詢未帶電話 -> 403
    res_no_phone = client.get(f"/api/v1/reservations/{code}")
    assert res_no_phone.status_code == 403
    assert res_no_phone.get_json()["error"] == "FORBIDDEN"

    # 2. 查詢帶錯誤電話 -> 403
    res_wrong_phone = client.get(f"/api/v1/reservations/{code}?phone=0911111111")
    assert res_wrong_phone.status_code == 403

    # 3. 查詢帶正確電話 -> 200
    res_ok = client.get(f"/api/v1/reservations/{code}?phone=0987654321")
    assert res_ok.status_code == 200
    assert res_ok.get_json()["data"]["guest_name"] == "隱私測試者"

def test_cancel_reservation_and_release_table(client, seed_admin_and_reservations):
    """
    REQ-004: 取消預約後釋放桌位占用，該桌位可立即被他人預約
    """
    target_time = (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d 13:00")
    # 預約 1: 分配到 Table 1 (唯一的 2 人桌)
    res1 = client.post("/api/v1/reservations", json={
        "party_size": 2,
        "reservation_time": target_time,
        "guest_name": "顧客A",
        "guest_phone": "0912121212"
    })
    code1 = res1.get_json()["data"]["reservation_code"]
    assert res1.get_json()["data"]["table_id"] == 1

    # 顧客 A 取消預約 (需核對電話)
    cancel_res = client.post(f"/api/v1/reservations/{code1}/cancel", json={
        "phone": "0912121212"
    })
    assert cancel_res.status_code == 200
    assert cancel_res.get_json()["data"]["status"] == "CANCELLED"

    # 再次取消相同預約應被拒絕
    re_cancel = client.post(f"/api/v1/reservations/{code1}/cancel", json={
        "phone": "0912121212"
    })
    assert re_cancel.status_code == 400
    assert "already been cancelled" in re_cancel.get_json()["message"]

    # 驗證釋放：顧客 B 在完全相同的時段預約 2 人，此時 Table 1 已釋放，應能成功取得 Table 1！
    res2 = client.post("/api/v1/reservations", json={
        "party_size": 2,
        "reservation_time": target_time,
        "guest_name": "顧客B",
        "guest_phone": "0934343434"
    })
    assert res2.status_code == 201
    assert res2.get_json()["data"]["table_id"] == 1

def test_cancel_within_one_hour_forbidden(client, seed_admin_and_reservations, app):
    """
    REQ-004 & 決策 Q-10: 距離用餐時間不足 1 小時不可線上取消
    """
    conn = get_connection(app.config)
    cursor = conn.cursor()
    # 建立一筆 30 分鐘後的預約
    imminent_start = (datetime.now() + timedelta(minutes=35)).strftime("%Y-%m-%d %H:%M:%S")
    imminent_end = (datetime.now() + timedelta(minutes=140)).strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
        INSERT INTO reservations (reservation_code, user_id, party_size, start_at, end_at, status)
        VALUES ('RES-IMM-001', NULL, 2, ?, ?, 'CONFIRMED')
    """, (imminent_start, imminent_end))
    res_id = cursor.lastrowid
    cursor.execute("""
        INSERT INTO reservation_guests (reservation_id, guest_name, guest_phone)
        VALUES (?, '趕不及的顧客', '0955555555')
    """, (res_id,))
    cursor.execute("INSERT INTO reservation_tables (reservation_id, table_id) VALUES (?, 1)", (res_id,))
    conn.commit()
    conn.close()

    cancel_res = client.post("/api/v1/reservations/RES-IMM-001/cancel", json={
        "phone": "0955555555"
    })
    assert cancel_res.status_code == 400
    assert "within 1 hour" in cancel_res.get_json()["message"]

def test_admin_reservation_management(client, seed_admin_and_reservations):
    """
    REQ-012: 管理端查詢、狀態更新、手動調桌與衝突防護
    """
    token = get_admin_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    # 1. 建立兩筆預約
    slot_time = (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d 18:00")
    res1 = client.post("/api/v1/reservations", json={
        "party_size": 2,
        "reservation_time": slot_time,
        "guest_name": "訂位甲",
        "guest_phone": "0966666666"
    })
    res2 = client.post("/api/v1/reservations", json={
        "party_size": 2,
        "reservation_time": slot_time,
        "guest_name": "訂位乙",
        "guest_phone": "0977777777"
    })
    id1 = res1.get_json()["data"]["reservation_id"]
    id2 = res2.get_json()["data"]["reservation_id"]

    # 2. 管理員查詢預約列表 (依狀態篩選)
    list_res = client.get("/api/v1/admin/reservations?status=CONFIRMED", headers=headers)
    assert list_res.status_code == 200
    data = list_res.get_json()["data"]
    assert len(data) >= 2

    # 3. 管理員手動更換訂位甲的桌位至 Table 3 (容量 4，符合需求且無衝突)
    change_res = client.patch(f"/api/v1/admin/reservations/{id1}/table", json={
        "table_id": 3
    }, headers=headers)
    assert change_res.status_code == 200
    assert change_res.get_json()["data"]["table_id"] == 3

    # 4. 管理員嘗試將訂位甲更換至訂位乙正在使用的 Table 2 (衝突) -> 應被拒絕 400
    conflict_change = client.patch(f"/api/v1/admin/reservations/{id1}/table", json={
        "table_id": 2
    }, headers=headers)
    assert conflict_change.status_code == 400
    assert "conflict" in conflict_change.get_json()["message"]

    # 5. 管理員更新狀態為 COMPLETED
    status_res = client.patch(f"/api/v1/admin/reservations/{id1}/status", json={
        "status": "COMPLETED"
    }, headers=headers)
    assert status_res.status_code == 200
    assert status_res.get_json()["data"]["status"] == "COMPLETED"

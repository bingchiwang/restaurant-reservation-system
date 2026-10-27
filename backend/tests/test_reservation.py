import pytest
from datetime import datetime, timedelta
from backend.app.utils.db import get_connection

@pytest.fixture
def seed_tables(app):
    """
    Seeds dining tables for reservation allocation testing:
    - Table 1: capacity 2
    - Table 2: capacity 4
    - Table 3: capacity 4
    - Table 4: capacity 8
    - Table 5: capacity 4 (MAINTENANCE - disabled)
    """
    conn = get_connection(app.config)
    cursor = conn.cursor()

    cursor.execute("DELETE FROM reservation_tables")
    cursor.execute("DELETE FROM reservation_guests")
    cursor.execute("DELETE FROM reservations")
    cursor.execute("DELETE FROM dining_tables")

    cursor.execute("INSERT INTO dining_tables (table_id, table_name, capacity, status) VALUES (1, 'A-01', 2, 'ACTIVE')")
    cursor.execute("INSERT INTO dining_tables (table_id, table_name, capacity, status) VALUES (2, 'B-01', 4, 'ACTIVE')")
    cursor.execute("INSERT INTO dining_tables (table_id, table_name, capacity, status) VALUES (3, 'B-02', 4, 'ACTIVE')")
    cursor.execute("INSERT INTO dining_tables (table_id, table_name, capacity, status) VALUES (4, 'C-01', 8, 'ACTIVE')")
    cursor.execute("INSERT INTO dining_tables (table_id, table_name, capacity, status) VALUES (5, 'B-03', 4, 'MAINTENANCE')")

    conn.commit()
    conn.close()

def get_future_valid_time(days_ahead=2, hour=12, minute=0):
    """Returns a valid reservation time string within business hours."""
    target_date = datetime.now() + timedelta(days=days_ahead)
    target_dt = target_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
    return target_dt.strftime("%Y-%m-%d %H:%M")

def test_guest_reservation_validation_errors(client, seed_tables):
    """
    REQ-002: 邊界測試 — 人數小於等於 0、超出 10 人、缺少聯絡資訊、非營業時間
    """
    valid_time = get_future_valid_time()

    # 1. Party size <= 0
    res = client.post("/api/v1/reservations", json={
        "party_size": 0,
        "reservation_time": valid_time,
        "guest_name": "王大明",
        "guest_phone": "0912345678"
    })
    assert res.status_code == 400
    assert "greater than 0" in res.get_json()["message"]

    # 2. Party size > 10
    res = client.post("/api/v1/reservations", json={
        "party_size": 15,
        "reservation_time": valid_time,
        "guest_name": "王大明",
        "guest_phone": "0912345678"
    })
    assert res.status_code == 400
    assert "cannot exceed 10" in res.get_json()["message"]

    # 3. Missing contact name
    res = client.post("/api/v1/reservations", json={
        "party_size": 2,
        "reservation_time": valid_time,
        "guest_name": "",
        "guest_phone": "0912345678"
    })
    assert res.status_code == 400

    # 4. Out of business hours (e.g. 08:00 AM)
    out_hours_time = get_future_valid_time(hour=8, minute=0)
    res = client.post("/api/v1/reservations", json={
        "party_size": 2,
        "reservation_time": out_hours_time,
        "guest_name": "王大明",
        "guest_phone": "0912345678"
    })
    assert res.status_code == 400
    assert "opening hours" in res.get_json()["message"]

    # 5. Too far in future (> 30 days)
    far_time = get_future_valid_time(days_ahead=35)
    res = client.post("/api/v1/reservations", json={
        "party_size": 2,
        "reservation_time": far_time,
        "guest_name": "王大明",
        "guest_phone": "0912345678"
    })
    assert res.status_code == 400
    assert "30 days" in res.get_json()["message"]

def test_auto_table_allocation_best_fit(client, seed_tables):
    """
    REQ-003: 桌位自動分配策略
    - 2 人用餐應分配 Table 1 (容量 2，剩餘座位浪費 0)
    - 3 人用餐應分配 Table 2 (容量 4，優先選擇剩餘較少且 table_id 較小者)
    - 停用之 Table 5 (MAINTENANCE) 不得被分配
    """
    time_slot = get_future_valid_time(days_ahead=1, hour=12, minute=0)

    # Booking 1: 2 persons -> should get Table 1 (capacity 2)
    res1 = client.post("/api/v1/reservations", json={
        "party_size": 2,
        "reservation_time": time_slot,
        "guest_name": "陳小姐",
        "guest_phone": "0922111333"
    })
    assert res1.status_code == 201
    data1 = res1.get_json()["data"]
    assert data1["table_id"] == 1
    assert data1["table_name"] == "A-01"
    assert data1["status"] == "CONFIRMED"
    assert data1["reservation_code"].startswith("RES-")

    # Booking 2: 3 persons -> Table 1 is 2-cap (too small); Tables 2 & 3 are 4-cap; Table 5 is maintenance
    # Should get Table 2 (table_id 2 < table_id 3)
    res2 = client.post("/api/v1/reservations", json={
        "party_size": 3,
        "reservation_time": time_slot,
        "guest_name": "林先生",
        "guest_phone": "0933444555"
    })
    assert res2.status_code == 201
    data2 = res2.get_json()["data"]
    assert data2["table_id"] == 2
    assert data2["table_name"] == "B-01"

def test_time_conflict_and_cleaning_buffer(client, seed_tables):
    """
    REQ-003 & 業務規則 5.1 & 5.2:
    用餐 90 分鐘 + 清桌緩衝 15 分鐘 = 總占用 105 分鐘。
    預約 1: 12:00 ~ 13:45 占用 Table 1。
    預約 2: 13:30 (在緩衝時間內) 嘗試訂 2 人桌 -> Table 1 仍在占用中，應避開 Table 1 分配 Table 2 或 3。
    預約 3: 13:45 或之後 (占用結束) -> Table 1 可再次被分配。
    """
    time_1200 = get_future_valid_time(days_ahead=3, hour=12, minute=0)
    time_1330 = get_future_valid_time(days_ahead=3, hour=13, minute=30)
    time_1400 = get_future_valid_time(days_ahead=3, hour=14, minute=0)

    # 1. 12:00 預約 2 人，分配到 Table 1
    res1 = client.post("/api/v1/reservations", json={
        "party_size": 2,
        "reservation_time": time_1200,
        "guest_name": "張先生",
        "guest_phone": "0911222333"
    })
    assert res1.status_code == 201
    assert res1.get_json()["data"]["table_id"] == 1

    # 2. 13:30 預約 2 人 (前一筆到 13:45 結束，包含緩衝時間，因此 Table 1 衝突)
    res2 = client.post("/api/v1/reservations", json={
        "party_size": 2,
        "reservation_time": time_1330,
        "guest_name": "李小姐",
        "guest_phone": "0944555666"
    })
    assert res2.status_code == 201
    # 應跳過 Table 1，分配給下一個最合適桌位 Table 2
    assert res2.get_json()["data"]["table_id"] == 2

    # 3. 14:00 預約 2 人 (Table 1 的 105 分鐘占用已於 13:45 結束)
    res3 = client.post("/api/v1/reservations", json={
        "party_size": 2,
        "reservation_time": time_1400,
        "guest_name": "趙先生",
        "guest_phone": "0977888999"
    })
    assert res3.status_code == 201
    # Table 1 已釋放，再次成為最符合 2 人的首選！
    assert res3.get_json()["data"]["table_id"] == 1

def test_no_available_table_and_rollback(client, seed_tables, app):
    """
    REQ-003: 所有合適桌位均被占用時，回傳 NO_AVAILABLE_TABLE (409)，
    且不得在資料庫殘留孤立預約或訪客資料。
    """
    time_slot = get_future_valid_time(days_ahead=4, hour=18, minute=0)

    # Table 4 是唯一容量能容納 8 人的桌位
    # 第一筆 8 人成功訂位 Table 4
    res1 = client.post("/api/v1/reservations", json={
        "party_size": 8,
        "reservation_time": time_slot,
        "guest_name": "高先生",
        "guest_phone": "0988777666"
    })
    assert res1.status_code == 201
    assert res1.get_json()["data"]["table_id"] == 4

    # 第二筆 8 人在同時段嘗試訂位 -> 無可用桌位
    res2 = client.post("/api/v1/reservations", json={
        "party_size": 8,
        "reservation_time": time_slot,
        "guest_name": "周先生",
        "guest_phone": "0999888777"
    })
    assert res2.status_code == 409
    assert res2.get_json()["error"] == "NO_AVAILABLE_TABLE"

    # 檢查資料庫一致性：周先生的預約與聯絡資料完全未殘留
    conn = get_connection(app.config)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM reservation_guests WHERE guest_name = '周先生'")
    assert cursor.fetchone() is None
    conn.close()

def test_get_reservation_by_code(client, seed_tables):
    """
    REQ-004: 透過預約代碼查詢預約詳細資訊
    """
    time_slot = get_future_valid_time(days_ahead=5, hour=19, minute=0)
    res = client.post("/api/v1/reservations", json={
        "party_size": 2,
        "reservation_time": time_slot,
        "guest_name": "黃先生",
        "guest_phone": "0911000111"
    })
    code = res.get_json()["data"]["reservation_code"]

    query_res = client.get(f"/api/v1/reservations/{code}")
    assert query_res.status_code == 200
    q_data = query_res.get_json()["data"]
    assert q_data["reservation_code"] == code
    assert q_data["guest_name"] == "黃先生"
    assert q_data["guest_phone"] == "0911000111"
    assert q_data["table_name"] == "A-01"

def test_prevent_duplicate_allocation_under_same_slot(client, seed_tables):
    """
    REQ-003 & ADR-002: 同一時段僅有單一合適桌位時，兩筆同時送出之預約不得重複分配同桌
    """
    time_slot = get_future_valid_time(days_ahead=6, hour=18, minute=30)
    
    # 預約 1: 成功取得 Table 4 (8 人桌)
    res1 = client.post("/api/v1/reservations", json={
        "party_size": 8,
        "reservation_time": time_slot,
        "guest_name": "併發測試者A",
        "guest_phone": "0911111111"
    })
    # 預約 2: 同時段嘗試再預約 8 人桌
    res2 = client.post("/api/v1/reservations", json={
        "party_size": 8,
        "reservation_time": time_slot,
        "guest_name": "併發測試者B",
        "guest_phone": "0922222222"
    })

    assert res1.status_code == 201
    assert res2.status_code == 409
    assert res2.get_json()["error"] == "NO_AVAILABLE_TABLE"

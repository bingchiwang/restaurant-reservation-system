def test_health_check(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "healthy"
    assert data["version"] == "1.0.0"

def test_database_initialization(db_conn):
    cursor = db_conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row["name"] if isinstance(row, dict) else row[0] for row in cursor.fetchall()]
    assert "users" in tables
    assert "dining_tables" in tables
    assert "reservations" in tables
    assert "reservation_guests" in tables
    assert "reservation_tables" in tables
    assert "menu_categories" in tables
    assert "menu_items" in tables
    assert "orders" in tables
    assert "order_items" in tables

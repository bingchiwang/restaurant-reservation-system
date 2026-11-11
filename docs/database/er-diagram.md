# 資料庫實體關聯圖 (ER Diagram) 與資料字典

依據 [SPEC.md](SPEC.md) 第 7 節之資料庫規格與 [schema.sql](schema.sql)。

## 1. 實體關聯圖 (ER Diagram)

```mermaid
erDiagram
    USERS ||--o{ RESERVATIONS : "makes"
    USERS ||--o{ ORDERS : "places"
    RESERVATIONS ||--o| RESERVATION_GUESTS : "has contact"
    RESERVATIONS ||--|{ RESERVATION_TABLES : "allocates"
    DINING_TABLES ||--o{ RESERVATION_TABLES : "assigned to"
    DINING_TABLES ||--o{ ORDERS : "serves"
    RESERVATIONS ||--o{ ORDERS : "links to"
    MENU_CATEGORIES ||--|{ MENU_ITEMS : "contains"
    MENU_ITEMS ||--o{ ORDER_ITEMS : "ordered as"
    ORDERS ||--|{ ORDER_ITEMS : "consists of"

    USERS {
        bigint user_id PK
        string email UK
        string password_hash
        string display_name
        string role
        string status
        datetime created_at
        datetime updated_at
    }

    DINING_TABLES {
        bigint table_id PK
        string table_name
        int capacity
        string status
        datetime created_at
        datetime updated_at
    }

    RESERVATIONS {
        bigint reservation_id PK
        string reservation_code UK
        bigint user_id FK "nullable for guests"
        int party_size
        datetime start_at
        datetime end_at
        string status
        datetime created_at
        datetime updated_at
    }

    RESERVATION_GUESTS {
        bigint reservation_id PK, FK
        string guest_name
        string guest_phone
    }

    RESERVATION_TABLES {
        bigint reservation_id PK, FK
        bigint table_id PK, FK
    }

    MENU_CATEGORIES {
        bigint category_id PK
        string name
        string status
        int sort_order
    }

    MENU_ITEMS {
        bigint item_id PK
        bigint category_id FK
        string name
        text description
        decimal price
        boolean is_available
        string image_url
        datetime created_at
        datetime updated_at
    }

    ORDERS {
        bigint order_id PK
        bigint user_id FK "nullable"
        bigint reservation_id FK "nullable"
        bigint table_id FK "nullable"
        string order_type
        string status
        decimal total_amount
        datetime created_at
        datetime updated_at
    }

    ORDER_ITEMS {
        bigint order_item_id PK
        bigint order_id FK
        bigint item_id FK
        string item_name_snapshot
        int quantity
        decimal unit_price
        decimal subtotal
        string note
    }

    STORE_SETTINGS {
        int setting_id PK
        string store_status
        boolean reservations_enabled
        boolean ordering_enabled
        boolean pre_order_enabled
        string announcement_text
        string announcement_type
        string opening_time
        string closing_time
        datetime updated_at
    }
```

---

## 2. 核心約束與規則說明

1. **訪客預約機制**：
   - 若為未註冊訪客，`reservations.user_id` 為 `NULL`。
   - 訪客預約時，必須同時寫入 `reservation_guests`，記錄姓名與電話。
2. **多桌與自動分配**：
   - 第一版自動分配策略僅分配單一合適桌位，寫入一筆 `reservation_tables`。
   - 透過 `reservation_tables` 關聯表保留未來多桌合併（REQ-P2）的擴充能力。
3. **歷史訂單金額保護 (Snapshot Pattern)**：
   - `order_items` 必須寫入當時的 `item_name_snapshot` 與 `unit_price`。
   - 菜單價格變動或餐點下架（`is_available = 0`）不得影響已成立之歷史訂單。
4. **金額型態**：
   - 統一使用 `DECIMAL(10, 2)`，避免浮點數誤差。

# 待決議事項清單 (Pending Decisions)

本文件追蹤 [SPEC.md](SPEC.md) 第 13 節列出的各項營運與業務邏輯待決議事項。在正式商業營運決議前，系統提供「第一版暫定預設值」，以利第一階段開發與測試進行。

| 編號 | 項目說明 | 目前狀態 | 第一版暫定決策 / 預設值 | 受影響模組 / 檔案 |
|---|---|---|---|---|
| **Q-01** | 營業時間與休息日設定 | 暫定採預設 | 每日 11:00 ~ 21:30，無固定公休日；可由組態檔配置 | ReservationService, TableAvailability |
| **Q-02** | 用餐時長及清桌緩衝時間 | 暫定採預設 | 用餐時長 90 分鐘，清桌緩衝 15 分鐘（占用總區間 105 分鐘） | ReservationService, TableConflictChecker |
| **Q-03** | 預約開放天數 | 暫定採預設 | 可預約未來 30 天內之時段 | ReservationValidation |
| **Q-04** | 最短預約提前時間 | 暫定採預設 | 最少須提前 30 分鐘預約 | ReservationValidation |
| **Q-05** | 單筆預約最大人數 | 暫定採預設 | 單筆最大限制 10 人（因第一版不支援自動併桌） | ReservationValidation, DiningTables |
| **Q-06** | 是否支援多桌合併 | 已確認暫不支援 | 第一版不支援自動併桌，一筆預約僅分配一張桌位 | TableAllocationService |
| **Q-07** | 同容量桌位的分配順序 | 暫定採預設 | 優先選擇容量足夠且浪費最少者；相同時依 `table_id` 升冪排序 | TableAllocationService |
| **Q-08** | 訪客預約查詢驗證方式 | 暫定採預設 | 需輸入「預約編號 (`reservation_code`)」+「聯絡電話 (`guest_phone`)」核對 | ReservationQueryController |
| **Q-09** | 預約是否立即確認 | 暫定採預設 | 系統自動分配桌位成功後狀態直接為 `CONFIRMED` | ReservationService |
| **Q-10** | 取消預約的時間限制 | 暫定採預設 | 用餐開始前 1 小時可由顧客自行取消；低於 1 小時需由管理端處理 | ReservationCancelService |
| **Q-11** | 預點餐截止時間 | 暫定採預設 | 用餐開始前 30 分鐘截止預點餐或修改 | OrderService |
| **Q-12** | 訂單修改與取消規則 | 暫定採預設 | `PENDING` 狀態可取消；進入 `PREPARING` 後顧客端不可取消 | OrderStatusService |
| **Q-13** | 現場點餐是否全面採用 QR Code | 暫定採預設 | 是，以桌位 QR Code 帶入 table_id / token 為主 | TableQRController |
| **Q-14** | 是否支援外帶 | 已確認第一版不支援 | 第一版僅支援「內用預約」與「現場桌位點餐」 | OrderTypeEnum |
| **Q-15** | 第一版是否完全不處理付款 | 已確認第一版不處理 | 第一版不串接金流，採現場結帳，保留狀態擴充空間 | OrderModel, SPEC.md 2.2 |
| **Q-16** | 餐點下架後的歷史紀錄保存方式 | 已確認依規格快照 | 訂單明細表記錄 `item_name_snapshot` 與 `unit_price`，不因調價/下架改變 | OrderItemsDAO |
| **Q-17** | 會員註冊是否需要電子郵件驗證 | 暫定採簡化 | 第一版免寄送驗證信，註冊成功即可登入（密碼需 bcrypt 雜湊） | AuthService |
| **Q-18** | 管理員與店員的權限差異 | 暫定第一版共用 | 第一版保留 `role` 欄位（`ADMIN`, `STAFF`, `MEMBER`），管理後台先統一以 ADMIN 驗證 | AuthMiddleware |
| **Q-19** | 第一版是否只支援單一餐廳 | 已確認單店 | 單店營運架構，資料庫不切分 store_id | All Modules |
| **Q-20** | 是否需要預約及訂單通知 | 已確認第一版不包含 | 不實作外部簡訊/電話 API，保留介面擴充空間 | NotificationService (Mock) |

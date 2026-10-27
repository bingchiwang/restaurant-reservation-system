# ADR-001: 後端分層架構 (Controller-Facade-Service-DAO)

## 狀態
已通過 (Accepted)

## 背景 (Context)
為符合課堂專題高品質代碼規範與分工維護需求，系統必須避免將資料庫 SQL、業務邏輯、時段衝突驗證、HTTP 請求處理混寫在單一模組中。特別是預約與點餐涉及跨資料庫實體（桌位、預約、訂單、明細）的一致性操作。

## 決策 (Decision)
嚴格落實四層架構，單向依賴呼叫方向：
`Controller` → `Facade` → `Service` → `DAO`

1. **Controller 層**：
   - 負責 HTTP Route、Query/Body JSON 輸入格式驗證。
   - 呼叫對應 Facade 函式。
   - 捕捉領域例外（如 `TableNotAvailableError`, `ValidationError`），轉換為標準 JSON 錯誤代碼與 HTTP 狀態碼。
   - 禁止在 Controller 中撰寫 SQL 語法。

2. **Facade 層**：
   - 作為複合業務流的協調中樞。
   - 例如「建立預約並預先點餐」，Facade 需協調 `ReservationService`（預約與桌位）、`OrderService`（訂單與菜單計價）在同一個資料庫交易中完成。

3. **Service 層**：
   - 包含領域業務邏輯與規則檢查。
   - 包含：桌位可用性演算、營業時間邊界判斷、菜單供應狀態校驗、訂單金額重算。
   - 不依賴 Web 框架（無 request, session 物件），具備高度單元可測試性。

4. **DAO (Data Access Object) 層**：
   - 封裝所有 SQL 讀寫操作與資料表映射。
   - 支援資料庫交易（Transaction Context）。
   - 採用參數化查詢，防止 SQL 注入。

## 結果與影響 (Consequences)
- 優點：職責切分清晰，業務邏輯可獨立執行單元測試；預約與桌位分配邏輯可進行高併發模擬測試。
- 限制：新增簡單 CRUD 功能需要建立四層結構檔案，但對長期維護與測試品質有顯著保障。

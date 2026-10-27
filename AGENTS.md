# AGENTS.md — AI 與開發者協作規範指南

本指南依據 [SPEC.md](SPEC.md) 制定，規範所有參與「餐廳預約與點餐系統」開發的 AI Agent（如 Antigravity CLI / Assistant）與人類開發者的協作行為、架構約束與交付流程。

---

## 1. 核心開發原則

1. **單一職責與需求導向**：
   - 每次開發任務嚴格對應一個具體需求編號（例如 `REQ-001`、`REQ-002`）。
   - 禁止在未授權的情況下擅自修改無關功能或進行大規模重構。
2. **規格與決策優先**：
   - 所有實作必須符合 [SPEC.md](SPEC.md) 與 `docs/adr/` 中的架構決策紀錄 (ADR)。
   - 若遇到未決策問題（參照待決議清單 `docs/DECISIONS.md`），不得擅自臆測，應主動提出或遵循預設暫定規範並記錄。
3. **架構分層嚴格遵守**：
   - 呼叫方向：`Controller → Facade → Service → DAO`。
   - 禁止 Controller 直接操作資料庫或撰寫業務核心邏輯。
   - 禁止 Service / DAO 依賴 Web 框架（Flask）的 Request/Response 物件。
4. **測試驅動與驗收標準**：
   - 所有業務規則必須具備單元測試與整合測試。
   - 不得將尚未通過測試的功能標記為完成。
   - 包含必要的邊界條件（邊界案例參照 SPEC.md 第 10.3 節）。

---

## 2. 開發流程 (Workflow)

每次開發必須嚴格依循以下 8 個步驟：

1. **確認需求編號**：明確當前開發的 `REQ-XXX`。
2. **閱讀規範文件**：閱讀 [SPEC.md](SPEC.md) 中該需求的驗收條件及對應 ADR。
3. **提出實作計畫**：在開始編寫代碼前，向使用者列出預計新增/修改的檔案清單與邏輯規劃。
4. **執行功能實作**：依分層架構編寫後端或前端代碼。
5. **編寫與執行測試**：執行自動化測試並確保全數通過。
6. **代碼與規範審查**：確認無直接跨層呼叫、SQL 注入風險、金額浮點數誤差等問題。
7. **更新相關文件**：若有架構變更或 API 更新，同步修訂 `SPEC.md` / `ADR` / `API` 文件。
8. **Git Commit**：依規範格式進行 Git 提交。

---

## 3. Git Commit 格式規範

所有 Commit 訊息必須遵循以下格式：

```text
type(REQ-ID): summary
```

- **類型 (type)**：
  - `feat`：新增功能
  - `fix`：修正錯誤
  - `test`：新增或修改測試
  - `docs`：新增或更新文件
  - `refactor`：重整程式結構（不影響外部行為）
  - `chore`：維護性工作（構建、環境配置等）

- **範例**：
  - `docs(SPEC): initialize project documentation and agents guide`
  - `feat(REQ-001): implement menu browsing api and service`
  - `test(REQ-003): add concurrency table allocation tests`
  - `fix(REQ-003): prevent duplicate table assignment with pessimistic locking`

---

## 4. 後端分層架構規範 (Flask)

後端目錄結構遵循：

```text
backend/
├── app/
│   ├── controllers/      # 接收 HTTP 請求、格式驗證、調用 Facade、回傳 JSON 回應
│   ├── facades/          # 跨領域服務協調（協調 Reservation, Table, Order）
│   ├── services/         # 業務邏輯、驗收規則計算、金額校驗、時段衝突檢查
│   ├── daos/             # 資料存取層、SQL 查詢與交易控制
│   ├── models/           # 資料結構定義、實體定義
│   └── utils/            # 工具函式（時間處理、密碼雜湊、JWT 驗證）
├── tests/                # 單元測試與整合測試
├── config.py             # 環境設定檔
└── run.py                # 應用程式啟動入口
```

### 資料型態與金額規範
- **金額**：所有貨幣與價格計算必須使用 `Decimal`，禁止使用浮點數 `float`。
- **快照保存**：歷史訂單必須保存當時的餐點名稱快照（`item_name_snapshot`）與成交單價（`unit_price`）。

---

## 5. 前端架構規範 (Expo / React Native)

```text
frontend/
├── src/
│   ├── api/              # API 封裝模組（Axios 或 fetch 實作）
│   ├── components/       # 共用 UI 元件（按鈕、輸入框、卡片等）
│   ├── screens/          # 頁面畫面（菜單、預約、點餐、訂單查詢等）
│   ├── navigation/       # 導覽路由配置
│   ├── hooks/            # 自訂 React Hooks
│   └── context/          # 狀態管理（會員登入狀態、購物車狀態）
├── App.tsx (或 App.js)
└── app.json
```

---

## 6. 安全性與環境變數

- 嚴禁將密碼、金鑰、JWT Secret 等硬編碼於程式碼中。
- 所有資料庫查詢必須使用參數化查詢（Prepared Statements / ORM 參數化），杜絕 SQL Injection。
- 資料庫連線與金鑰統一讀取 `.env`。

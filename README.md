# 餐廳預約與點餐系統 (Restaurant Reservation & Ordering System)

本專案為學校課堂專題與程式設計練習所規劃之餐廳預約與點餐系統，支援顧客線上查看菜單、預約時段、自動桌位分配、預先點餐、現場 QR Code 點餐，以及餐廳管理者之營運後台。

- **規格文件**：[SPEC.md](SPEC.md)
- **Agent 與開發者協同規範**：[AGENTS.md](AGENTS.md)
- **待決議事項清單**：[docs/DECISIONS.md](docs/DECISIONS.md)
- **架構決策紀錄 (ADR)**：
  - [ADR-001: 後端分層架構](docs/adr/ADR-001-layered-architecture.md)
  - [ADR-002: 資料庫交易與桌位併發控制機制](docs/adr/ADR-002-database-concurrency-and-locking.md)
  - [ADR-003: 統一後端託管前後端與後端控制前端架構](docs/adr/ADR-003-unified-hosting-and-frontend-control.md)
- **資料庫規範與 ER 圖**：
  - [docs/database/schema.sql](docs/database/schema.sql)
  - [docs/database/er-diagram.md](docs/database/er-diagram.md)

---

## 專案架構

```text
├── SPEC.md                    # 系統需求規格書
├── AGENTS.md                  # AI 與團隊開發協同規範
├── docs/                      # 系統架構、決策與資料庫文件
│   ├── DECISIONS.md           # 營運與業務邏輯待決議事項 (Q-01 ~ Q-20)
│   ├── adr/                   # Architecture Decision Records
│   └── database/              # MySQL DDL Schema 與 Mermaid ER 圖
├── backend/                   # Python Flask 後端
│   ├── app/
│   │   ├── controllers/       # HTTP 路由與輸入驗證
│   │   ├── facades/           # 跨領域服務協調
│   │   ├── services/          # 核心業務邏輯
│   │   ├── daos/              # 資料庫存取層
│   │   ├── models/            # 實體模型
│   │   └── utils/             # 工具與資料庫連線
│   ├── tests/                 # 單元與整合測試
│   ├── requirements.txt
│   ├── config.py
│   └── run.py
└── frontend/                  # Expo + React Native 前端
    ├── src/
    ├── package.json
    ├── app.json
    └── App.js
```

---

## 快速啟動

### 一鍵啟動統一伺服器（推薦）

直接雙擊專案根目錄的 **`啟動系統.bat`**，系統將於 `http://127.0.0.1:5000` 啟動統一伺服器：
- **顧客前端網頁**：`http://127.0.0.1:5000`
- **後端管理控制中心**：`http://127.0.0.1:5000/admin`

### 手動啟動後端 (Backend)

```bash
# 1. 進入後端目錄並啟動虛擬環境
cd backend
venv\Scripts\activate

# 2. 安裝依賴套件
pip install -r requirements.txt

# 3. 執行自動化測試
python -m pytest

# 4. 啟動統一伺服器 (預設埠號 5000)
python run.py
```

### 手動啟動前端開發伺服器 (Expo Dev)

```bash
cd frontend
npm install
npm start
```

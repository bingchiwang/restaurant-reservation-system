# ADR-003: 統一後端託管前後端與後端控制前端架構

## 狀態
已通過 (Accepted)

## 背景 (Context)
原先開發架構中，顧客端網頁與後端 API 分別運行於 Port `8080` 與 Port `5000`，且管理員登入畫面直接嵌入於顧客端分頁列中，容易讓一般訪客誤觸管理後台介面，且啟動兩個獨立伺服器對操作較為不便。

## 決策 (Decision)

1. **統一託管 (Unified Hosting on Port 5000)**：
   - 由 Flask / Waitress 後端單一伺服器（`127.0.0.1:5000`）統一承載：
     - `/`：顧客端網頁（編譯自 Expo Web 之 `frontend/dist_web/`）
     - `/admin`：後端獨立管理控制中心網頁（Server-rendered template，內含管理員登入驗證）
     - `/api/v1/*`：RESTful JSON API

2. **從顧客前端移除管理員登入 (Admin Isolation)**：
   - 徹底移除顧客前端內的 `AdminScreen`、`AuthAPI` 與 `AdminAPI`。
   - 顧客介面僅保留「美味菜單」、「線上預約」、「購物車」、「查詢預約」四項顧客專用功能。

3. **後端控制前端機制 (Backend-Controlled Storefront)**：
   - 新增 `store_settings` 資料表，儲存：
     - `store_status`（`OPEN` / `CLOSED` / `MAINTENANCE`）
     - 功能開關（`reservations_enabled`、`ordering_enabled`、`pre_order_enabled`）
     - 動態營業時間（`opening_time`、`closing_time`）
     - 全站公告橫幅（`announcement_text`、`announcement_type`）
   - 後端 Service 層（`ReservationService`, `OrderService`）於寫入前嚴格檢查上述設定並阻擋停用時段的請求（HTTP 403 `SERVICE_PAUSED`）。
   - 顧客前端透過 `SystemConfigContext` 定期同步 `/api/v1/system/config`，當後端調整營業狀態、功能開關、公告、營業時間、菜單或桌位時，顧客前端會即時更新 UI 狀態與可用選項。

## 結果與影響 (Consequences)
- 使用者只需執行單一啟動指令（`啟動系統.bat`）於 `http://127.0.0.1:5000` 即可存取整個系統，免除雙伺服器與跨域疑慮。
- 管理員入口完全與顧客前端分離（位於 `/admin`），提升系統安全性與產品定位清晰度。

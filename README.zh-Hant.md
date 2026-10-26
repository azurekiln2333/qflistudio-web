# QFLIWebForge

[简体中文](README.md) | [繁體中文](README.zh-Hant.md) | [English](README.en.md)

QFLIWebForge 是手機上的網頁 IDE。
它在本機預覽 HTML、CSS 和 JavaScript 專案。
它把 主控台輸出送回編輯器。

## 產品定位

- 產品名是 QFLIWebForge。
- 倉庫名是 `qfli_web`。
- 應用程式包名是 `com.azurekiln.qfli.webforge`。
- 應用程式版本是 1.0.0+1。
- 介面來自共享包 `qfli_studio_core`。
- 本倉庫只保留 Web 檔位和 Web 工具。

## 功能

### 編輯器與預覽

- 共享編輯器支援語法高亮和多檔案編輯。
- 專案範本有空白和 HTML 兩種。
- 預覽服務只監聽 `127.0.0.1`。
- 連接埠 0 自動選擇空閒連接埠。
- 支援靜態檔案、SPA 回退和目錄索引。
- 支援 HTTP 代理和 WebSocket 代理。
- 代理目標只允許本機迴環 IP。
- 支援即時重新整理。
- 支援 主控台、錯誤和請求診斷。
- 支援目前檔案預覽。
- 長按執行按鈕可預覽目前檔案。

### 雙引擎

- `.qfli/web.json` 的 `engine` 選擇引擎。
- `auto` 優先使用封裝的 Nginx。
- 引擎缺少時，`auto` 回退 Dart 中介軟體。
- iOS 和 HarmonyOS 先探測嵌入引擎。
- `nginx` 只用 Nginx。缺少時啟動失敗。
- `webforge` 用 Dart 中介軟體。
- Nginx 是上游 1.31.6。
- Android 和桌面用行程託管。
- iOS 和 HarmonyOS 用行程內嵌入生命週期。
- 明確指定 `nginx` 不會回退其他引擎。

### 離線工具

- 本機服務面板顯示位址、請求和主控台。
- JSON、URL 和 Base64 編解碼只在本機計算。
- 文件資源檢查找出缺少和外部參照。
- CSS 工具算顏色、對比度、盒模型和優先級。
- HTML 工具查標籤配對和無障礙。
- 工具頁提供終端機入口。
- 共享核心決定終端機的命令與權限。

### 程式碼分析

- HTML 用 `html` 解析器。
- CSS 用 `csslib` 解析器。
- JavaScript 用 QuickJS 2026-06-04。
- QuickJS 只編譯，不執行程式碼。
- 分析未儲存的緩衝區。
- 缺少原生程式庫時回報無法使用。
- 無法使用不會偽裝成沒有錯誤。

### 離線課程

- 課程有 481 個主題。
- 每個主題配 1 個教學和 1 個範例。
- 語言分布：HTML 160、CSS 160、JavaScript 161。
- 每個範例是可預覽的 `.html` 檔案。
- 瀏覽器檢查提供範例的語意斷言。
- HTML 範例 006 故意參照缺少的圖片。
- 教學和範例說明採用簡體中文。

## 離線邊界

- 產品隱藏登入、雲端同步和 Git 入口。
- 產品隱藏 HTTP 用戶端和外部代理入口。
- 工具只在本機計算。
- 預覽只連迴環位址。
- 代理目標必須是字面迴環 IP。
- 每個回應帶離線 CSP。
- CSP 保留內嵌指令碼和本機資源。
- CSP 允許同源 object 文件和 data/blob 資源。
- CSP 不阻止系統瀏覽器開啟一般連結。
- 離線不等於隔離整個系統瀏覽器。

## 快速開始

開發要求：

- 開發需要 Flutter SDK。
- Dart SDK 約束是 `^3.11.5`。
- OHOS 目標需要可用的 Flutter OHOS SDK。
- 本倉庫依賴同級包 `qfli_studio_core`。
- 首次安裝依賴可能需要網路。
- 產品本身離線工作。
- 產品不依賴遠端服務。

先檢出同級 `qfli_studio_core`。目錄結構如下。

```text
checkout-parent/
  qfli_studio_core/
  qfli_web/
```

1. 檢出同級 `qfli_studio_core`。
2. 在本倉庫執行 `flutter pub get`。
3. 連接裝置。
4. 執行 `flutter run`。
5. 開啟一個 HTML 專案。
6. 點選執行按鈕。
7. 查看預覽。

可選的 `.qfli/web.json` 設定：

```json
{
  "engine": "auto",
  "port": 0,
  "spaFallback": false,
  "root": ".",
  "proxies": [
    { "prefix": "/api", "target": "http://127.0.0.1:8080" }
  ]
}
```

發行建置命令：

```text
flutter build apk --release
flutter build hap --release
```

切換到發行建置時保留 pub 步驟。
`--no-pub` 可能保留舊外掛註冊表。

## 目錄

```text
qfli_web/
├── lib/                產品程式碼
│   ├── main.dart       檔位和啟動
│   ├── pages/          工具頁和 Web 檢視
│   ├── content/        離線課程轉接器
│   └── services/       預覽、引擎和設定
├── test/               單元和元件測試
├── integration_test/   裝置整合測試
├── tool/               原生引擎與驗收入口
├── scripts/            內容、建置和瀏覽器檢查
├── native/             嵌入引擎與語法分析橋接
├── vendor/             上游原始碼、修補檔和授權
├── assets/             圖示、授權和課程 JSON
├── android/ ios/ macos/ linux/ windows/ ohos/   平台外殼
└── web/                Flutter Web 外殼
```

## 驗證

```text
python -X utf8 scripts/emit_content.py
python -X utf8 scripts/test_emit_content.py
python -X utf8 scripts/audit_web_content.py --product --report build/content/audit.md
npm ci
npx playwright install chromium
npm run verify:content
flutter analyze --no-pub lib test integration_test tool
flutter test --no-pub --concurrency=1
```

- 內容指令碼重複執行得到相同位元組。
- 結構稽核檢查 ID、對應和唯一性。
- 瀏覽器檢查逐個執行範例。
- 預設 `flutter test` 只執行 `test/`。
- 靜態分析不執行整合測試。
- 裝置整合測試需要連接裝置。
- 原生引擎另有裝置冒煙測試。

裝置整合與冒煙命令：

```text
flutter test -d DEVICE integration_test/nginx_runtime_test.dart
flutter test -d DEVICE integration_test/content_import_test.dart
flutter run --debug --no-pub -d DEVICE -t tool/nginx_smoke.dart --no-resident
```

- 只有 `[NGINX_SMOKE] PASS` 才算通過。
- 建置成功不算執行證據。

## 平台限制

| 平台 | 封裝 | 執行證據 |
| --- | --- | --- |
| Windows x64 | 官方 Nginx 1.31.6 | 2026-10-01 真實二進位整合測試通過 |
| Android x86_64 | NDK PIE，16 KiB 對齊 | 2026-10-01 至 10-03 API 37 模擬器冒煙通過 |
| Android arm64 | APK 已封裝 | 2026-10-15 實機原生和內容冒煙通過 |
| Android armv7 | APK 已封裝 | 實機執行未驗證 |
| HarmonyOS arm64/x86_64 | 嵌入 NAPI 共享程式庫 | 2026-10-12 簽章套件實機冒煙通過 |
| Linux x86_64 | 上游原始碼 CMake | 2026-10-02 獨立引擎通過。Flutter 應用程式未驗證 |
| macOS arm64/x86_64 | Xcode 封裝並簽章 | 未執行。沒有 Apple 建置機 |
| iOS arm64 | 靜態程式庫和 Swift 通道 | 未執行。沒有 Apple 建置機 |

表中證據來自歷史紀錄。
歷史通過不代表目前候選版本通過。

發行簽章狀態：

- Android release 用偵錯金鑰，屬於驗證套件。
- 商店散布需要正式簽章。
- OHOS 目前沒有可達裝置目標。
- OHOS 目前套件執行未驗證。
- iOS 和 macOS 需要 Apple 建置機和簽章。
- Windows 完整 Flutter 建置缺少 Visual Studio C++ 工具。

目前驗證範圍：

- 2026-10-22 桌面與行動檢視區通過 481 項檢查。
- 同日 ArkWeb 檢查為 474 項通過、7 項失敗。
- 失敗項已修原始碼，原生複驗仍待執行。
- 2026-10-26 兩套引擎的 CSP 迴歸通過。
- 同日完整測試為 316 項通過、4 項失敗。
- 4 項失敗均在自有預覽策略和資源代理中。
- 格式、靜態分析和 481 對內容檢查通過。
- 本輪最終回報逾時，未通過 180 秒時限。
- 目前工作樹尚未完成端對端複驗。

## 深入閱讀

- 預覽和代理契約見 [.trellis/spec/backend/web-runtime.md](.trellis/spec/backend/web-runtime.md)。
- 原生引擎見 [.trellis/spec/backend/native-runtime.md](.trellis/spec/backend/native-runtime.md)。
- 課程驗證見 [.trellis/spec/backend/catalog-verification.md](.trellis/spec/backend/catalog-verification.md)。
- 平台證據見 [vendor/nginx/VALIDATION.md](vendor/nginx/VALIDATION.md)。
- 發行檢查見 [.trellis/tasks/10-15-webforge-store-readiness/](.trellis/tasks/10-15-webforge-store-readiness/)。

## 授權

- 上游 Nginx 授權見 [vendor/nginx/LICENSE](vendor/nginx/LICENSE)。
- QuickJS 用 MIT 授權，見 [vendor/quickjs/LICENSE](vendor/quickjs/LICENSE)。
- 課程為原創內容，採用 CC BY 4.0。
- 根目錄授權見 [LICENSE](LICENSE)，即 GPL-3.0。
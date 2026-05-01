# Bicasa 專案程式碼分析與優化規劃

## 1. 摘要 (Summary)
本次分析旨在檢視 Bicasa 專案目前的程式碼狀態，找出在效能 (Performance)、圖形使用者介面 (GUI)、系統架構 (Architecture) 等方面的優化空間，並將 `todo.md` 中提及的待開發項目納入未來的執行藍圖。目前專案主要以 PySide6 開發 GUI，使用 SQLite 儲存圖片與人臉資訊，並已導入基礎的多執行緒 (Threading) 來避免 UI 卡頓。但仍有許多可優化之處，以下為詳細的分析與規劃。

---

## 2. 效能優化建議 (Performance Optimizations)

### 2.1 資料庫連線管理 (Database Connection Management)
- **現狀問題**：在 `database.py` 中，幾乎每個方法（如 `addPhotoMetadata`, `getPhotoMetadata`, `getFaces`）都會建立新的連線 (`sqlite3.connect`) 並在執行完畢後關閉。這會造成極大的 I/O 負擔，特別是在批次處理大量照片或人臉資料時。
- **優化方案**：
  - 實作 **Connection Pool** 或在 Singleton 中維持單一連線（若開啟 SQLite 的 Check_Same_Thread=False 並妥善處理 Threading Lock）。
  - 將 SQLite 設定為 `PRAGMA journal_mode=WAL;`，以提升讀寫併發效能。

### 2.2 縮圖載入與快取 (Thumbnail Caching & Loading)
- **現狀問題**：每次點擊樹狀目錄時，`CollectListWidgetItem` 都會透過 `QImageReader` 即時讀取該目錄下所有圖檔並產生 `QPixmap`。對於包含大量高畫素照片的目錄，這會極度消耗記憶體與 CPU。
- **優化方案**：
  - 導入**縮圖快取機制 (Thumbnail Cache)**，將產生過的縮圖存在本地硬碟或資料庫中。
  - 實作**懶載入 (Lazy Loading)**，只有當圖片進入 `QListWidget` 的可視範圍時才讀取與生成縮圖。

### 2.3 執行緒管理 (Thread Management)
- **現狀問題**：目前的執行緒是透過 `QThread` 並放進 `listWidget_running_thread` 陣列管理，若未妥善清理已完成的執行緒，容易造成 Memory Leak。
- **優化方案**：改用 **`QThreadPool`** 與 **`QRunnable`** 架構。這樣可以更有效地重複利用 Thread 資源，並控制同時進行的 I/O 工作數量。

---

## 3. GUI 效率與體驗優化 (GUI Efficiency & UX)

### 3.1 Model/View 架構 (ItemDelegate)
- **現狀問題**：目前使用 `QListWidget` 並逐一塞入 `QListWidgetItem`。當項目動輒數千個時，GUI 初始化會非常緩慢。
- **優化方案**：如 `todo.md` 所提，使用 **Model/View 架構**。將 `QListWidget` 替換為 `QListView`，並配合 `QAbstractListModel` 管理資料。外觀部分使用自訂的 **`QStyledItemDelegate`** 進行繪製（Beautify thumbnails），這不僅大幅提升 GUI 效率，也能輕鬆實現客製化的卡片佈局 (Card Layout)。

### 3.2 鍵盤瀏覽與照片切換 (Left/Right Arrow Navigation)
- **現狀問題**：看圖時無法輕易切換上一張/下一張。
- **優化方案**：在 `PannableScrollArea` 或 `Window` 攔截 `keyPressEvent`，當按下左/右方向鍵時，自動將 `QListView` / Tab 的索引切換至上/下一個項目。

### 3.3 狀態反饋 (Loading Bar & Status)
- **優化方案**：在耗時操作（如人臉辨識、大量圖片載入）時，在 `StatusWidget` 中加入進度條 (`QProgressBar`)，提供明確的視覺反饋。

### 3.4 圖片上的人臉互動 (Faces-book Presentation)
- **現狀問題**：目前人臉的呈現需要決定是要直接畫在圖片上還是用 Overlay。
- **優化方案**：建議使用 **Overlay (QGraphicsView/QGraphicsScene 架構，或在 Label 上疊加透明 Widget)**。這樣可以讓人臉方框具備 Click 事件，不破壞原圖，且方便觸發後續功能（例如：點擊人臉即進入該人物的專屬相簿）。

---

## 4. 架構設計優化 (Architecture Design)

### 4.1 關注點分離 (Separation of Concerns)
- **現狀問題**：`gui_thread_safe.py` 中混雜了 UI 事件綁定、邏輯判斷與執行緒派發。
- **優化方案**：引入 MVC (Model-View-Controller) 或 MVP 模式。將「檔案系統讀取」、「人臉辨識 AI」等邏輯抽離到獨立的 Controller/Service 中，UI 層僅負責接收事件與更新畫面。

### 4.2 影像特效外掛系統 (Image Effects Plugin Structure)
- **優化方案**：設計一個基礎的 Plugin 介面 (`class BaseEffectPlugin`)，定義統一的 `apply_effect(image)` 方法。透過 Python 的 `importlib` 動態載入 `plugins/` 目錄下的模組，讓未來擴充濾鏡或 AI 特效時不需修改核心程式碼。

---

## 5. TODO.md 整合與後續開發規劃 (TODO Integration Plan)

基於上述分析，結合 `todo.md` 的項目，建議未來的執行優先順序如下：

### 第一階段：核心效能與 GUI 基礎升級 (High Priority)
1. **重構資料庫連線**：實作 Connection Pool，解決 `database.py` 的效能瓶頸。
2. **導入 Model/View 架構**：實作 `QListView` + `QAbstractListModel` + `QStyledItemDelegate`，同時解決縮圖美化與記憶體消耗問題。
3. **基礎 UX 升級**：實作左右鍵切換圖片、以及載入進度條 (Loading Bar)。

### 第二階段：Faces-book 與資料庫進階功能 (Medium Priority)
1. **人臉資料模型設計**：引入 `sqlite-vss`。將人臉特徵 (Embeddings) 存入向量資料庫，以支援快速的相似人臉搜尋。
2. **Faces-book UI**：實作人物卡片佈局 (Card Layout)，以及在照片上 Overlay 可點擊的人臉框。

### 第三階段：外掛架構與 AI 擴充 (Medium-Low Priority)
1. **Plugin System**：建立 Image effects 的外掛目錄與載入機制。
2. **AI Image Upscaling**：將超解析度模型封裝為 Plugin，非同步執行並整合進 UI 進度條。

### 第四階段：打包與發布 (Low Priority)
1. **封裝 (Packaging)**：撰寫 `setup.py`，並透過 PyInstaller 將專案打包為單一可執行檔 (Executable)。
2. 確認跨平台（至少 Windows/Linux）的執行相容性。

---
*此報告由 AI 助理於系統分析後自動生成，目的為建立後續開發與優化的參考基準。*

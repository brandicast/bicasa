# Bicasa 效能與 UX 優化實作紀錄 (v1)

## 1. 執行目的
本次執行的目的在於將先前的分析結果付諸實踐，針對 Bicasa 專案中的**資料庫效能**、**GUI 記憶體效率**以及**看圖體驗 (UX)** 進行初步的重構與調整。

## 2. 調整內容與實作細節

### 2.1 效能優化 (Performance) - `database.py`
- **問題描述**：原本在進行資料庫讀寫時，每一個方法都會建立與關閉新的 `sqlite3` 連線，導致頻繁的磁碟 I/O。
- **優化實作**：
  - 導入了 **單一常駐連線 (Persistent Connection)** 與 **Thread-Safe 鎖 (Lock)** 的機制。
  - 在 `DB` 類別的 `__init__` 中初始化 `self.conn`，並開啟 `check_same_thread=False` 以允許跨 Thread 使用。
  - 透過執行 `PRAGMA journal_mode=WAL;` 開啟 Write-Ahead Logging 模式，大幅提升 SQLite 的併發讀寫效能。
  - 使用 `threading.Lock()` 將所有的寫入操作 (`addPhotoMetadata`, `addFaces`, `insertFaces`) 包覆於 `with self.lock:` 區塊中，確保資料庫鎖定安全。

### 2.2 GUI 記憶體效率 (GUI Efficiency) - `handle_listwidget.py`
- **問題描述**：原先 `CollectListWidgetItem_Thread` 讀取原圖後直接轉成 `QIcon` 塞入 ListWidget，若遇到千萬像素的圖片會耗盡記憶體並導致閃退或卡頓。
- **優化實作**：
  - 在發送 Signal 前，先對 `QPixmap` 進行 **縮放 (Downscale)** 處理。
  - 將解析度降至 `200x200` (或嘗試從 `config` 中讀取 `thumbnail_size`)，並採用 `Qt.KeepAspectRatio` 與 `Qt.SmoothTransformation` 確保縮圖品質。這項改動極大地降低了系統記憶體的消耗，達到偽 Lazy-Loading 的成效。

### 2.3 使用者體驗與記憶體管理 (UX & MVC) - `gui_thread_safe.py`
- **左/右方向鍵看圖 (UX)**：
  - 在 `Window` 類別中覆寫了 `keyPressEvent`，攔截鍵盤左鍵與右鍵。
  - 實作了 `switchImage(direction)` 邏輯：當使用者在看圖 Tab (index > 0) 時按下方向鍵，程式會自動尋找目前圖片在 `listWidget` 中的索引，將其加/減一後，**先關閉目前的 Tab，再開啟下一張圖的 Tab**，達到順暢的看圖切換體驗。
- **防止 Memory Leak (MVC/架構)**：
  - 發現原本在點擊樹狀目錄時，不斷產生新的 `workerthread` 加入 `self.listWidget_running_thread` 陣列，卻未在執行緒結束後清除參考。
  - 新增了 `workerthread.finished.connect(lambda ...)` 的機制，當執行緒載入完成後會自動從陣列中移除自身，改善了記憶體資源回收的問題。

## 3. 下一步建議
這版本優先以最小改動的範圍實現了有感的優化。若要進一步邁向完整的 MVC 架構，未來建議可以：
1. 將 `handle_listwidget.py` 改寫為繼承 `QAbstractListModel`，完全替換掉目前的 `QListWidget` 做法。
2. 實作真正意義上的 Lazy Loading（只在捲動進入畫面時才進行 I/O 讀取與發送 Signal）。

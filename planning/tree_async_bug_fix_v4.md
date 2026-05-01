# Bicasa 樹狀目錄非同步載入修復紀錄 (v4)

## 1. 執行目的
本次優化的目的是為了解決前一版本在載入大量/多語系目錄時引發的三個問題：
1. **Loading Icon 無法顯示**：左下角的讀取圖示為空白。
2. **多國語言資料夾崩潰**：掃描多語系（繁體中文）資料夾時，背景執行緒崩潰並導致 Core Dump，並拋出 `only accepts 0 argument(s), 3 given!` 錯誤。
3. **目錄未排序**：掃描並列出資料夾時沒有按字母排序。

## 2. 變更項目與實作細節

### 2.1 修正 Loading Icon 路徑遺失問題
- **問題分析**：在 `status_widget.py` 中，雖然我們已經建立了動態解析的 `loading_icon` 變數來指向 `ui/loading.gif`，但在實際賦予給 `QMovie` 時，仍不小心使用了硬編碼的相對路徑 `QMovie('ui/loading.gif')`，導致 QMovie 在執行時找不到圖片而顯示空白。
- **解決方案**：將該行修改為 `self.movie = QMovie(loading_icon)`，讓 GIF 動畫能夠成功載入並在左下角正常播放。

### 2.2 修正跨執行緒操作 GUI 導致的 Core Dump (多國語言異常)
- **問題分析**：前版在掃描中文資料夾時出現 `only accepts 0 argument(s), 3 given!` 與 `Aborted (core dumped)`，其根本原因**並非** Python 無法處理中文，而是 Qt 的「跨執行緒 UI 操作」違規。
- 在前版程式中，背景掃描執行緒 (`tree_thread`) 雖然是在背景執行，但它與主視窗皆建立於主執行緒中。當我們進行 `connect(self.on_tree_dir_found)` 時，Qt 預設使用了 `DirectConnection`。這導致背景掃描到中文資料夾並呼叫 `emit()` 時，`on_tree_dir_found` 會直接在背景執行緒內被觸發，並於背景執行緒中實例化 `QTreeWidgetItem` (GUI 元件)，這在 Qt 中是嚴格禁止的，因此直接造成系統崩潰與參數誤報。
- **解決方案**：在 `gui_thread_safe.py` 的 Signal 連接中，強制加入了 `Qt.QueuedConnection` 參數：
  ```python
  self.tree_thread.dir_found.connect(self.on_tree_dir_found, Qt.QueuedConnection)
  ```
  確保所有背景找到的目錄路徑，都會被打包進佇列，交回給主執行緒進行安全的 `QTreeWidgetItem` 建立。

### 2.3 實作資料夾字母排序 (Sorting)
- **問題分析**：`os.scandir` 預設是依照檔案系統的硬碟儲存順序回傳目錄，因此呈現出來是亂序的。
- **解決方案**：在 `handle_treewidget.py` 的背景掃描邏輯中，將 `os.scandir` 回傳的產生器轉交給 Python 內建的 `sorted()` 進行排序，並以 `entry.name` 作為排序的 key：
  ```python
  sorted_entries = sorted(entries, key=lambda e: e.name)
  ```
  這使得載入後的所有目錄，都會乖乖依照字母或筆畫順序排列好。

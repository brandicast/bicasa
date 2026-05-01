# Bicasa Tree 載入與設定選單優化紀錄

## 1. 執行目的
本次優化的目的在於解決兩個關鍵的 UI/UX 問題：
1. **樹狀目錄 (TreeWidget) 載入優化**：原先同步遞迴掃描整個目錄，在面臨巨大且包含多國語言的資料夾時會卡死畫面。我們需要加入 Loading Bar 反饋與非同步載入，並確保對多國語言（Unicode 路徑）的正確支援。
2. **設定選單無反應**：使用者反映 `File -> Configuration` 點擊後 UI 毫無反應，需要將其實作。

## 2. 變更項目與實作細節

### 2.1 多國語言目錄與設定檔支援
- **問題分析**：在讀取 `config.ini` 時，如果設定檔內含有非 ASCII (如中文) 路徑，Python 預設的讀取編碼在不同系統環境下可能導致編碼錯誤，間接造成讀取不到多國語言的目錄。
- **解決方案**：在 `config_reader.py` 中，將 `config.read` 顯式地加上 `encoding='utf-8'`，確保能精準無誤地載入多國語言路徑字串，這確保了後續交給 OS 進行 `scandir` 時不會發生亂碼問題。

### 2.2 樹狀目錄非同步載入 (Asynchronous Tree Loading) & Loading Bar
- **問題分析**：原先的 `CollectTreeNodes` 是直接在 MainWindow 的 `__init__` 中遞迴掃描目錄，造成啟動時嚴重的畫面凍結。
- **解決方案**：
  - **背景執行緒**：我們將 `handle_treewidget.py` 徹底重寫，實作了繼承自 `QThread` 的 `CollectTreeNodes_Thread`。它會在背景進行高速的 `os.scandir`，並透過 Signal (`dir_found`) 即時向主執行緒回報發現的目錄。
  - **動態節點建立**：在 `gui_thread_safe.py` 中，我們透過一個暫存的 `tree_nodes_map` (字典) 來記憶每個路徑對應的 `QTreeWidgetItem`，每當收到背景回報新目錄，就在 UI 主執行緒中找到其父節點並加入，避免了跨執行緒建立 UI 的崩潰問題。
  - **Loading Bar 反饋**：在背景執行緒啟動前，我們呼叫了 `self.statusWidget.startLoadingAnimation()` 顯示讀取中的 GIF 動畫；並在執行緒發出 `finished_scan` 信號時，呼叫 `stopLoadingAnimation()`，完美解決了使用者在等待掃描時的不確定感。

### 2.3 Configuration 選單實作
- **問題分析**：使用者介面上已經繪製了 `actionConfiguration`，但在程式碼中缺乏訊號與槽 (Signal & Slot) 的連結。
- **解決方案**：在 `gui_thread_safe.py` 中，將 `actionConfiguration.triggered` 連結至新加入的方法 `onConfigurationTriggered`。
- 目前已實作一個暫時的 `QMessageBox` 彈跳視窗，告知使用者「Configuration 編輯器尚在開發中，請先手動編輯 conf/config.ini」，給予明確的互動反饋，消除原本點擊後毫無反應的問題。

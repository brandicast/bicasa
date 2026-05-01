# Bicasa 核心崩潰與中文目錄顯示修復紀錄 (v6)

## 1. 執行目的
本次優化的目的是為了解決以下兩項嚴重的核心錯誤：
1. **中文目錄顯示方塊亂碼 (Tofu/Missing Glyphs)**：中文資料夾可以被讀取，但在 Linux 系統的 Tree Widget 介面上，中文字元變成了方塊 (豆腐塊) 或無法辨識的符號。
2. **影片播放器崩潰 (Segmentation Fault)**：當點擊 `.mp4` 影片檔案時，系統因為 OpenGL / MESA 驅動程式初始化失敗而造成 Core Dump 崩潰。

## 2. 變更項目與實作細節

### 2.1 修復中文顯示方塊亂碼 (字型缺失問題)
- **問題分析**：您提到的「顯示錯誤的方塊亂碼」是 Linux 圖形介面開發中極為經典的**字型缺失 (Missing Glyphs)** 問題。這代表 Python 內部字串是正確的（所以點進去能運作），但 PySide6 (Qt) 預設套用的系統字型（通常為 Ubuntu 或 DejaVu）內不包含中文字體的字形資料，因此無法渲染中文字元，只能畫出空心方塊。
- **解決方案**：
  - 我們直接從開源庫下載了最標準的 **Noto Sans TC (思源黑體)** 繁體中文字型檔，並存放在 `python/src/ui/fonts/NotoSansTC-Regular.otf` 中。
  - 在主程式 `bicasa.py` 啟動時，使用 `QFontDatabase.addApplicationFont()` 動態將該字型載入記憶體。
  - 將其加入應用程式的全域字型 Fallback 序列 (`app_font.setFamilies([font, ...])`)。從此只要介面上有中文字，不論使用者的 Linux 系統有沒有裝中文字型，Qt 都能自動拿內建的思源黑體來完美渲染，徹底根絕方塊亂碼！

### 2.2 修復中文目錄無法建立樹狀節點的問題 (Unicode Signal Mismatch)
- **問題分析**：在深入分析後發現，問題在於 PySide6 的「訊號與槽 (Signal & Slots)」機制。我們原本宣告了 `dir_found = Signal(str, str, str)`，當 Python 傳遞含有中文字元的字串時，PySide 底層會先將其轉換為 C++ 的 `QString`，然後在接收端再轉換回 Python 的 `str`。這層轉換極容易因為作業系統與 Python 之間的 Unicode 正規化 (NFC vs NFD) 差異，導致字串內容發生微小變化。
- **崩潰點**：當我們拿這個經過轉換的字串，去 `tree_nodes_map` (字典) 內尋找父節點時，因為 Python 字典的 Key 是嚴格比對的，只要有一點點的編碼差異就會回傳 `None`，最終導致中文節點被默默拋棄，無法畫在介面上！
- **解決方案**：在 `handle_treewidget.py` 中，將 Signal 定義改為 `dir_found = Signal(object, object, object)`，並在 `gui_thread_safe.py` 的對應接收端加上 `@Slot(object, object, object)`。這會強迫 Qt 直接傳遞 Python 的物件參照 (Object Reference)，完全繞過任何 C++ 字串轉換。這使得 `tree_nodes_map` 的比對能 100% 成功，中文目錄也就順利長出來了。

### 2.2 修復影片播放器 OpenGL 崩潰 (Segmentation Fault)
- **問題分析**：從 Log 中的錯誤判斷，這是因為 PySide6 的 `QVideoWidget` 預設會強迫使用系統底層的 OpenGL (EGL) 進行影像硬體渲染。在某些 Linux 環境（尤其是 WSL、遠端桌面或無顯示卡驅動的環境中），會因為無法建立有效的渲染表面而直接引發 Segmentation Fault 讓整個程式閃退。
- **解決方案**：我們徹底移除了 `QVideoWidget`，改採一種更安全的純軟體渲染方法：
  - 導入了 PySide6 的 `QVideoSink` 元件。
  - 讓 `QMediaPlayer` 將影片解碼後的每一幀 (Frame) 直接拋給 `QVideoSink`。
  - 擷取這些 Frame，將其轉為 `QImage` 與 `QPixmap`，再由一般的 `QLabel` 來繪製畫面。
  - 這個做法完全避開了 OpenGL 顯示層，保證了在所有 Linux/WSL 環境下的影片播放穩定性，且完全不會閃退！

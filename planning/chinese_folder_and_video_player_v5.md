# Bicasa 中文路徑解析與影片播放功能實作紀錄 (v5)

## 1. 執行目的
本次實作旨在解決以下兩個問題：
1. **中文資料夾內容無法顯示**：修復點擊中文資料夾時，清單畫面 (`ListWidget`) 無法顯示任何縮圖與內容的問題。
2. **多媒體影片支援**：為資料夾內的影片檔案建立縮圖，並實作一個內建的多媒體播放器，支援播放、暫停、靜音、拖曳進度條等功能。

## 2. 變更項目與實作細節

### 2.1 修復中文路徑圖片讀取失敗
- **問題分析**：從先前的 Log 分析中發現，當我們點擊中文資料夾時，`QImageReader` 其實有嘗試讀取，但它在處理帶有非 ASCII (中文) 字元的絕對路徑時，會因為 Qt 底層字串轉換的 Bug 或作業系統語系不匹配而回報找不到檔案，最終導致 `QPixmap` 變成 `null pixmap`，因此清單上甚麼都顯示不出來。
- **解決方案**：
  - 我們在 `handle_listwidget.py` 中徹底改變了圖片讀取方式，**不再讓 Qt 處理檔案路徑**。
  - 改為先透過 Python 內建的 `open(entry, 'rb')` (Python 原生完美支援 Linux 上的 UTF-8 檔案路徑) 將圖片二進位資料讀入記憶體。
  - 接著將資料放入 `QByteArray` 與 `QBuffer` 中，再交給 `QImageReader` 從記憶體串流解析圖片，這樣不僅繞過了所有的路徑編碼地雷，同時保留了 `setAutoTransform(True)` 正確處理相片 EXIF 翻轉的優勢。

### 2.2 影片縮圖產生 (Video Thumbnail Generation)
- **實作細節**：
  - 擴充 `handle_listwidget.py`，加入影片副檔名判斷 (`.mp4`, `.mov`, `.avi`, `.mkv`)。
  - 若檔案為影片，則使用 OpenCV (`cv2.VideoCapture`) 直接讀取影片。
  - 為了避免很多影片開頭第一秒是純黑畫面，我們刻意快進抓取「第 10 幀 (Frame)」作為代表性縮圖。
  - 抓取後進行色彩空間轉換 (`BGR` to `RGB`)，轉換為 `QImage` 後交由主程式建立縮圖標籤。

### 2.3 影片播放器元件 (VideoPlayerWidget) 實作
- **元件設計**：
  - 在 `python/src/ui/` 下新增了獨立的元件模組 `video_player_widget.py`。
  - 使用 PySide6 最新的 `QtMultimedia` 框架，組裝了 `QMediaPlayer` (核心播放引擎) 與 `QVideoWidget` (影像輸出介面)。
  - 實作了下方控制列 (Controls Layout)，包含：播放/暫停按鈕、靜音切換按鈕、時間標籤 (`00:00 / 00:00`) 以及可拖曳的水平進度條 (`QSlider`)。
- **UI 路由串接**：
  - 修改 `gui_thread_safe.py` 的雙擊事件 (`listWigetItemDoubleClicked`)。
  - 當使用者點兩下圖片時，維持原先開啟 `Photo_Label` 與看圖滾輪介面；若點兩下的是影片檔，則會實例化 `VideoPlayerWidget`，自動載入該影片並開啟新分頁，提供完整的多媒體體驗。

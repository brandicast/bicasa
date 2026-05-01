# Bicasa 虛擬環境建立與測試報告

## 1. 執行目的
本次執行的目的在於為 Bicasa 專案建立隔離的 Python 虛擬環境 (venv)，安裝所有必要的第三方套件，並啟動應用程式進行測試，以找出潛在的環境與程式碼問題。

## 2. 虛擬環境與套件安裝 (venv Setup)
- **建立環境**：在專案根目錄下成功執行 `python3 -m venv venv`。
- **依賴套件分析與安裝**：透過分析原始碼 (`import` 語句)，安裝了以下主要套件及其次依賴：
  - `PySide6` (負責 GUI)
  - `opencv-python` (負責影像處理)
  - `deepface`, `numpy`, `tf-keras` (負責 AI 人臉辨識與神經網路)
  - `exifread` (負責讀取相片 EXIF 資訊)
- **匯出清單**：已將最終穩定的環境版本匯出至根目錄的 `requirements.txt`。

## 3. 測試過程與發現的問題 (Testing & Issues Found)

在嘗試無頭模式啟動 `bicasa.py` 時，我們發現並解決了以下三個問題：

### 3.1 遺漏的次級依賴 (Missing Dependencies)
- **問題**：第一次啟動時，DeepFace 模型底層的 Keras 引擎拋出了 `ModuleNotFoundError: No module named 'tf_keras'` 錯誤；且 `ui/photo_label.py` 拋出了 `ModuleNotFoundError: No module named 'exifread'` 錯誤。
- **解決方式**：手動透過 `pip install tf-keras exifread` 將缺少的依賴補齊。

### 3.2 Logging 初始化失敗 (Logging Error)
- **問題**：啟動時終端機提示 `Initialize logging error`。經過追查，發現 `python/conf/logging.conf` 中設定了日誌輸出路徑為 `logs/logging.log`，但專案目錄下並未預先建立 `logs` 資料夾，導致 `FileHandler` 找不到路徑而拋出例外。
- **解決方式**：已建立 `python/logs/` 目錄，使日誌系統能夠正常寫入。

### 3.3 設定檔的作業系統路徑衝突 (Hardcoded Windows Paths)
- **問題**：`python/conf/config.ini` 中的 `root` (圖庫根目錄) 與 `source_directory` (掃描目錄) 參數被寫死為 Windows 路徑（例如 `D:\CouldStation_Photo\` 與 `C:\workbench\...`）。由於目前測試環境為 Linux，這會導致程式在後續掃描目錄時發生例外。
- **解決方式**：為了順利完成測試，已暫時將 `config.ini` 中的這兩個路徑修改為當前目錄 (`.`)。

## 4. 測試結果
在修復上述問題後，程式已能成功啟動並載入 TensorFlow 與 PySide6 的 Main Window，並正常顯示「Init MainWindow」等除錯日誌，**目前程式在載入與初始化階段已無任何崩潰或異常狀況**。

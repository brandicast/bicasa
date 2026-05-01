# Bicasa 專案目錄結構重構紀錄

## 1. 執行目的
為了讓專案結構更清晰、符合標準的 Python 專案慣例，本次針對原始碼目錄、虛擬環境與文件進行了搬移與重構，並更新了相關的程式碼路徑引用。

## 2. 變更項目

### 2.1 原始碼 (Source Code) 集中管理
- 將原本散落於 `python/` 底下的所有 `*.py` 原始碼檔案，全數搬移至 **`python/src/`** 目錄中。
- 將輔助與 UI 模組目錄 (`python/ui/` 與 `python/utils/`) 統一搬移至 **`python/src/`** 下。

### 2.2 虛擬環境 (Virtual Environment) 與日誌/設定檔
- 將根目錄下的 `venv` 搬移至 **`python/venv/`**。
- 同步修正了 `venv/bin/` 內所有直譯器與 pip 的硬編碼路徑 (Hardcoded paths) 以確保 `activate` 能正常運作。
- **維持原狀**：`python/conf/` 與 `python/logs/` 保持不動，依然放在 `python/` 之下，與 `src/` 平行。

### 2.3 規劃文件 (Planning & Analysis) 統一歸檔
- 在專案根目錄建立了 **`planning/`** 資料夾。
- 將 `todo.md` 以及先前的分析報告與優化紀錄 (`bicasa_*.md`, `venv_*.md`) 全部集中到 `planning/`，讓專案根目錄保持乾淨。

## 3. 程式碼路徑動態解析調整 (Code Adjustments)
由於原始碼移動至 `src/`，而 `conf/` 與 `logs/` 等資料夾保持在上一層，原本使用相對路徑 (`"conf/config.ini"`) 的寫法會導致執行時找不到檔案。因此進行了以下修正：

1. **`python/src/config_reader.py`**:
   - 導入 `pathlib.Path`，定義 `BASE_DIR = Path(__file__).resolve().parent.parent` (即指向 `python/` 目錄)。
   - 將設定檔讀取路徑改為絕對路徑 `BASE_DIR / "conf" / "config.ini"`。

2. **`python/src/init.py` 與 `python/src/database.py`**:
   - 使用 `BASE_DIR` 動態組合 `logging.conf`、資料庫檔案 (`db/bicasa.db`) 及初始化腳本 (`conf/bicasa.db.sql`) 的絕對路徑。

3. **GUI UI 元件載入 (`python/src/gui_thread_safe.py` 等)**:
   - 將 `ui/bicasa.ui` 與 `ui/loading.gif` 的讀取路徑改用 `Path(__file__).parent` 解析。確保無論在哪個目錄啟動腳本，GUI 都能正確找到並載入這些靜態資源。

## 4. 測試結果
在套用上述結構與路徑修正後，透過指令 `cd python && QT_QPA_PLATFORM=offscreen python src/bicasa.py` 進行測試，應用程式能夠成功讀取所有配置並啟動 MainWindow，完全沒有路徑錯誤的問題。

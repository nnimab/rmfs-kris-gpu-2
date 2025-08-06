# RMFS 系統容量壓力測試工具

本工具提供完整的 RMFS（倉儲機器人系統）容量測試功能，包括並行執行、資源隔離、結果分析和視覺化報告。

## 功能特色

- ✅ **跨平台支援**: 支援 Windows 和 Linux
- ✅ **並行執行**: 可同時運行多個測試，提升效率
- ✅ **完全隔離**: 每個測試具有獨立的工作環境
- ✅ **長時間運行**: 支援超過 100,000 ticks 的測試
- ✅ **智能分析**: 自動生成詳細分析報告和圖表
- ✅ **互動式界面**: 友善的選單操作界面

## 快速開始

### 1. 安裝依賴項

```bash
pip install pandas numpy matplotlib rich
```

### 2. 執行測試

#### 方法一：互動式選單（推薦）
```bash
python run_capacity_test.py
```

#### 方法二：命令列模式
```bash
# 執行標準容量測試
python run_capacity_test.py --test

# 自訂測試參數
python run_capacity_test.py --test --robot-counts 20 30 40 --ticks 50000 --parallel
```

### 3. 檢視結果

測試完成後，結果將保存在 `test/results/` 目錄下，包含：
- 測試摘要 JSON 檔案
- 詳細評估結果
- 分析報告和圖表

## 核心組件

### 1. 容量測試控制器 (`capacity_test_controller.py`)
負責協調整個測試流程，包括：
- 並行測試管理
- 資源分配
- 進度追蹤
- 結果收集

### 2. 隔離管理器 (`isolation_manager.py`)
確保測試間的完全隔離：
- 獨立的工作空間
- 隔離的檔案路徑
- 獨立的環境變數

### 3. 容量分析器 (`capacity_analyzer.py`)
提供深度分析功能：
- 性能指標計算
- 擴展性分析
- 圖表生成
- 報告生成

### 4. 實驗選單 (`experiment_menu.py`)
友善的互動式界面：
- 測試參數配置
- 進度監控
- 結果瀏覽
- 檔案管理

## 測試配置

### 支援的機器人數量
- 預設: [20, 25, 30, 35, 40]
- 可自訂任意數量組合

### 測試模式
- **無控制器模式**: 機器人自由通過路口，測試系統容量上限
- **長時間測試**: 支援 100,000+ ticks 的穩定運行

### 並行設定
- 自動偵測最佳並行數量
- 可手動設定最大並行測試數
- 支援串行模式

## 分析報告

### 關鍵指標
- **完成率**: 訂單完成比例
- **等待時間**: 平均機器人等待時間
- **能源效率**: 每訂單能源消耗
- **吞吐量**: 單位時間處理能力
- **擴展性**: 系統擴展能力評估

### 圖表類型
- 容量-性能關係圖
- 效率分析圖
- 能源消耗分析圖
- 擴展性分析圖
- 綜合儀表板

## 命令參考

### 基本測試
```bash
# 執行基本功能測試
python run_capacity_test.py --test-basic

# 快速測試（較少 ticks）
python run_capacity_test.py --test --ticks 10000

# 標準測試
python run_capacity_test.py --test --ticks 100000
```

### 高級配置
```bash
# 自訂機器人數量和並行設定
python run_capacity_test.py --test \
  --robot-counts 15 20 25 30 35 40 45 \
  --ticks 150000 \
  --parallel \
  --max-parallel 4

# 串行執行（適合資源受限環境）
python run_capacity_test.py --test \
  --robot-counts 20 30 40 \
  --ticks 50000 \
  --parallel false
```

### 結果分析
```bash
# 分析特定測試結果
python run_capacity_test.py --analyze test/results/capacity_test_20240101_120000

# 只生成圖表
python test/capacity_analyzer.py test/results/capacity_test_20240101_120000 --charts-only

# 只生成報告
python test/capacity_analyzer.py test/results/capacity_test_20240101_120000 --report-only
```

### 維護操作
```bash
# 清理臨時檔案
python run_capacity_test.py --cleanup

# 檢視說明
python run_capacity_test.py --help
```

## 目錄結構

```
test/
├── __init__.py                    # 模組初始化
├── capacity_test_controller.py    # 主控制器
├── isolation_manager.py           # 隔離管理器
├── capacity_analyzer.py           # 分析器
├── experiment_menu.py             # 互動選單
├── test_basic_functionality.py    # 功能測試
├── README.md                      # 說明文件
└── results/                       # 測試結果目錄
    └── capacity_test_YYYYMMDD_HHMMSS_ID/
        ├── capacity_test_summary.json
        ├── workspaces/
        ├── charts/
        └── capacity_analysis_report_YYYYMMDD_HHMMSS.md
```

## 故障排除

### 常見問題

1. **依賴項缺失**
   ```bash
   pip install pandas numpy matplotlib rich
   ```

2. **權限問題**
   - 確保對工作目錄有寫入權限
   - Windows 用戶可能需要以管理員身份執行

3. **記憶體不足**
   - 減少並行測試數量
   - 降低測試 tick 數
   - 使用串行模式

4. **磁盤空間不足**
   - 定期清理臨時檔案
   - 調整輸出目錄到有足夠空間的位置

### 日誌查看

測試執行時會產生詳細日誌，位於：
- 控制器日誌: `test/results/capacity_test_*/capacity_test.log`
- 評估日誌: `test/results/capacity_test_*/workspaces/*/logs/`

### 性能調優

1. **提升並行效率**:
   - 設定 `max-parallel` 為 CPU 核心數的 50-75%
   - 確保足夠的記憶體和磁盤空間

2. **減少測試時間**:
   - 使用較少的 tick 數進行初步測試
   - 先測試較少的機器人數量組合

3. **節省資源**:
   - 啟用臨時檔案清理
   - 定期清理舊的測試結果

## 技術規格

- **Python 版本**: 3.7+
- **依賴項**: pandas, numpy, matplotlib, rich
- **支援平台**: Windows, Linux
- **記憶體需求**: 建議 4GB+ (取決於並行數量)
- **磁盤空間**: 每個測試約需 100MB-1GB

## 開發團隊

本工具是 RMFS 專案的一部分，專為深度學習優化倉儲交通控制研究而設計。

## 授權

本專案遵循與 RMFS 主專案相同的授權條款。
# 基準模型測試系統使用指南

## 概述

基準模型測試系統用於優化 Time-Based 和 Queue-Based 控制器的參數。系統支援並行執行和完整的檔案隔離機制。

## 系統特點

1. **隔離機制**：每個測試運行在獨立的工作空間中，避免檔案衝突
2. **並行支援**：支援 Windows 和 Linux 平台的多進程並行執行
3. **結果儲存**：所有結果儲存在 `test/results/` 目錄下
4. **自動分析**：提供圖表生成和最優參數報告

## 使用方法

### 1. 透過實驗選單（推薦）

```bash
python test/experiment_menu.py
```

選擇選項 2：基準模型參數優化

### 2. 直接執行測試

#### Time-Based 參數掃描
```bash
python test/baseline_test_controller.py --type time_based --robot-counts 30 35 --runs 3 --ticks 100000
```

#### Queue-Based 參數掃描
```bash
python test/baseline_test_controller.py --type queue_based --robot-counts 30 35 --runs 3 --ticks 100000
```

### 3. 驗證系統配置

```bash
python test/verify_baseline_system.py
```

### 4. 測試並行執行

```bash
python test/test_baseline_parallel.py
```

## 參數說明

- **robot-counts**: 要測試的機器人數量列表
- **runs**: 每個參數組合的重複運行次數
- **ticks**: 每次測試的模擬時長
- **type**: 測試類型（time_based 或 queue_based）

## 預設參數範圍

### Time-Based
- 時間配比：50:50, 60:40, 65:35, 70:30, 75:25, 80:20
- 格式：水平時間:垂直時間

### Queue-Based
- 隊列閾值：2, 3, 4, 5, 6
- 表示觸發信號切換的最小隊列長度

## 結果分析

測試完成後，使用分析器生成報告：

```bash
python test/baseline_analyzer.py test/results/baseline_[timestamp]_[id]
```

分析器會生成：
1. 參數比較圖表
2. 熱力圖分析
3. 最優參數報告

## 目錄結構

```
test/
├── results/                          # 測試結果目錄
│   └── baseline_YYYYMMDD_HHMMSS_ID/ # 單次測試會話
│       ├── time_based/               # Time-Based 結果
│       ├── queue_based/              # Queue-Based 結果
│       ├── analysis/                 # 分析結果
│       └── baseline_test.log         # 測試日誌
├── baseline_test_controller.py       # 主控制器
├── baseline_analyzer.py              # 結果分析器
├── isolation_manager.py              # 隔離管理器
└── experiment_menu.py                # 實驗選單

```

## 隔離機制說明

每個測試運行都有獨立的：
- 工作空間目錄 (`workspaces/test_[id]/`)
- NetLogo 狀態檔案 (`states/netlogo_[id].state`)
- 訂單檔案 (`orders_[id].csv`)
- 環境變數 (`SIMULATION_ID`)

這確保了並行執行時不會發生檔案衝突。

## 注意事項

1. 測試前確保有足夠的磁碟空間（每個測試約需 50-100MB）
2. Windows 用戶需要確保防毒軟體不會干擾檔案操作
3. 建議在測試前關閉其他占用大量 CPU 的程式
4. 測試結果會自動清理超過 30 天的舊檔案

## 故障排除

### 並行執行失敗
- 確認 Python 版本 >= 3.6
- Windows 用戶檢查是否有權限創建子進程
- 嘗試減少並行數或使用串行模式

### 檔案衝突
- 確認沒有手動修改 workspaces 目錄
- 檢查是否有其他程式占用相關檔案
- 使用 `verify_baseline_system.py` 驗證系統狀態

### 記憶體不足
- 減少並行執行的測試數
- 降低測試的 tick 數
- 關閉其他應用程式
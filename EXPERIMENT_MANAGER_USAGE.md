# RMFS 實驗自動化管理系統使用指南

## 📋 概述

`experiment_manager.py` 是一個完整的實驗自動化管理系統，整合了訓練、評估和圖表生成功能，解決了原有系統中單控制器對比問題和手動流程複雜性。

## 🚀 快速開始

### 啟動系統
```bash
python experiment_manager.py
```

### 首次使用推薦流程
1. 選擇 **[5] 系統狀態檢查** 查看可用控制器
2. 選擇 **[1] 完整實驗流程** 開始實驗
3. 選擇 **[2] 標準模式** 配置（平衡性能和時間）
4. 確認配置後開始執行

## 🎯 功能詳解

### 1. 完整實驗流程
**推薦新手使用**
- 自動執行：模型訓練 → 性能評估 → 圖表生成
- 解決單控制器對比問題（自動執行多控制器實驗）
- 生成完整的實驗報告和視覺化圖表

### 2. 模型訓練階段
- 並行訓練 4 個 AI 模型：
  - DQN Step 模式
  - DQN Global 模式
  - NERL Step 模式
  - NERL Global 模式
- 自動重命名模型文件為標準格式
- 支持多線程並行執行

### 3. 性能評估階段
- 自動檢測可用控制器
- 智能設計對比實驗組：
  - 完整對比實驗（所有控制器）
  - 傳統控制器基準測試
  - AI 控制器對比
  - DQN 獎勵模式對比
  - NERL 獎勵模式對比
- 多次重複實驗確保統計意義

### 4. 圖表生成階段
- 自動為所有評估結果生成圖表
- 支持多種圖表類型：
  - 性能對比雷達圖
  - 算法對比柱狀圖
  - 獎勵機制影響分析
  - 性能排行榜
  - 綜合對比熱力圖

### 5. 系統狀態檢查
- 檢查所有依賴文件
- 顯示可用/缺失控制器
- 顯示當前配置參數
- 系統健康狀態診斷

## ⚙️ 配置模式

### 快速模式 ⚡
**適合測試和驗證 (約 1-2 小時)**
- DQN 訓練：5000 ticks
- NERL 訓練：10 代，15 個體，1000 eval ticks
- 評估：10000 ticks × 2 次重複

### 標準模式 🎯
**平衡性能和時間 (約 3-4 小時)**
- DQN 訓練：10000 ticks
- NERL 訓練：20 代，20 個體，2000 eval ticks
- 評估：20000 ticks × 3 次重複

### 論文模式 🎓
**高品質學術結果 (約 6-8 小時)**
- DQN 訓練：20000 ticks
- NERL 訓練：50 代，25 個體，3000 eval ticks
- 評估：30000 ticks × 5 次重複

### 自定義模式 ⚙️
**手動設置所有參數**
- 可自定義所有訓練和評估參數
- 可選擇是否啟用並行執行
- 靈活配置重複次數和隨機種子

## 🔧 進階功能

### 多線程並行執行
- **訓練並行**：同時訓練多個模型，節省 60% 時間
- **評估並行**：同時執行多個評估實驗，節省 50% 時間
- **智能資源管理**：根據系統能力自動調整並行數量

### 智能實驗設計
- **依賴檢測**：自動檢測可用控制器，設計合適的對比實驗
- **統計意義**：確保每組實驗至少有 2 個控制器進行對比
- **結果完整性**：自動生成所有必要的 CSV 和 JSON 文件

### 實驗會話管理
- **會話追蹤**：每次實驗自動生成唯一會話 ID
- **進度監控**：實時顯示實驗進度和預估剩餘時間
- **結果總結**：自動生成實驗總結報告
- **歷史記錄**：查看過往實驗記錄和成功率

## 📊 輸出結果

### 評估結果
```
result/evaluations/EVAL_yyyymmdd_hhmmss_description/
├── evaluation_config.json          # 評估配置
├── overall_comparison.csv          # 整體性能對比
├── algorithm_comparison.csv        # 算法對比分析
├── reward_comparison.csv          # 獎勵機制對比
├── performance_rankings.json      # 性能排行榜
└── charts/                         # 圖表目錄
    ├── performance_radar_chart.png
    ├── algorithm_comparison_chart.png
    ├── reward_mechanism_chart.png
    ├── performance_rankings_chart.png
    └── comprehensive_heatmap.png
```

### 會話總結
```
result/session_summaries/
└── session_id_summary.json        # 實驗會話總結
    ├── session_id                  # 會話唯一標識
    ├── start_time / end_time       # 開始/結束時間
    ├── config                      # 使用的配置
    ├── results                     # 詳細結果
    └── statistics                  # 成功率統計
```

## 🛠️ 故障排除

### 常見問題

#### 1. 模型文件不存在
**現象**：顯示"缺少模型文件"
**解決**：
- 先運行 **[2] 模型訓練階段** 生成模型
- 或使用 **[5] 系統狀態檢查** 查看具體缺失的模型

#### 2. 評估實驗失敗
**現象**：評估成功率低於 100%
**解決**：
- 檢查 NetLogo 環境是否正常
- 確認 `train.py` 和 `evaluate.py` 可以單獨運行
- 嘗試降低評估時長（使用快速模式）

#### 3. 圖表生成失敗
**現象**：圖表生成成功率低
**解決**：
- 確認安裝了 `seaborn` 套件：`pip install seaborn`
- 檢查評估結果是否完整（需要 CSV 和 JSON 文件）
- 嘗試手動運行 `visualization_generator.py`

#### 4. 並行執行問題
**現象**：多線程執行出現錯誤
**解決**：
- 在自定義配置中關閉並行執行
- 檢查系統資源是否足夠
- 嘗試減少並行數量

### 系統要求

#### 軟體需求
- Python 3.8+
- NetLogo 6.0+
- 所有 requirements.txt 中的套件

#### 硬體建議
- **快速模式**：4GB RAM，2 核心 CPU
- **標準模式**：8GB RAM，4 核心 CPU
- **論文模式**：16GB RAM，8 核心 CPU
- **並行執行**：建議至少 8GB RAM

## 💡 使用技巧

### 1. 首次使用
```bash
# 1. 檢查系統狀態
python experiment_manager.py
# 選擇 [5] 系統狀態檢查

# 2. 快速驗證
# 選擇 [1] 完整實驗流程 → [1] 快速模式

# 3. 正式實驗
# 選擇 [1] 完整實驗流程 → [2] 標準模式
```

### 2. 分階段執行
```bash
# 1. 先訓練模型
# 選擇 [2] 模型訓練階段

# 2. 再評估性能
# 選擇 [3] 性能評估階段

# 3. 最後生成圖表
# 選擇 [4] 圖表生成階段
```

### 3. 自定義實驗
```bash
# 1. 設置自定義參數
# 選擇 [6] 配置參數設置

# 2. 執行自定義實驗
# 選擇 [1] 完整實驗流程 → [4] 自定義配置
```

## 📈 最佳實踐

### 1. 時間規劃
- **測試驗證**：使用快速模式，約 1-2 小時
- **初步實驗**：使用標準模式，約 3-4 小時
- **最終實驗**：使用論文模式，約 6-8 小時

### 2. 資源優化
- **並行執行**：在資源允許的情況下開啟並行，可節省 40-60% 時間
- **分階段執行**：如果系統資源有限，可以分階段執行
- **監控資源**：注意 CPU 和記憶體使用情況

### 3. 結果管理
- **定期備份**：重要實驗結果及時備份
- **命名規範**：使用有意義的描述字段
- **版本控制**：重要的配置更改記錄在版本控制中

## 🔗 相關文檔

- `EXPERIMENT_WORKFLOW_GUIDE.md`：詳細的實驗流程指南
- `train.py`：模型訓練腳本
- `evaluate.py`：性能評估腳本
- `visualization_generator.py`：圖表生成腳本
- `check_system.py`：系統完整性檢查腳本

## 🎉 總結

RMFS 實驗自動化管理系統是一個綜合性的實驗管理工具，它：

✅ **解決了原有問題**：
- 單控制器對比問題 → 自動多控制器實驗
- 手動流程複雜 → 一鍵自動化執行
- 參數配置困難 → 智能預設和自定義
- 圖表生成失敗 → 完整的數據和錯誤處理

✅ **提供了新功能**：
- 友好的交互式界面
- 多線程並行執行
- 智能實驗設計
- 完整的會話管理
- 進度監控和時間預估

✅ **適用於不同需求**：
- 新手：使用完整實驗流程 + 標準模式
- 研究者：使用自定義配置 + 論文模式
- 開發者：使用分階段執行 + 並行優化

這個系統讓複雜的 RMFS 實驗變得簡單、可靠和高效！
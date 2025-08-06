# evaluate.py 統一評估框架使用指南

## 🎯 概述

evaluate.py 是階段二的核心工具，用於公平地比較6種控制器的性能，並生成論文所需的核心數據。

### 支援的控制器
- **傳統控制器**: Time-based, Queue-based
- **AI控制器**: DQN-step, DQN-global, NERL-step, NERL-global

### 主要功能
- 統一評估流程，確保公平對比
- 自動生成三種對比分析報告
- 支援可視化和無頭模式
- 完整的性能指標收集

## 📋 快速開始

### 1. 檢查可用控制器
```bash
python evaluate.py --help
```

### 2. 評估傳統控制器（無需模型文件）
```bash
# 評估時間基和隊列基控制器
python evaluate.py --controllers time_based queue_based --ticks 5000

# 使用描述性命名
python evaluate.py --controllers time_based queue_based --description "traditional_only"

# 使用自定義輸出目錄（覆蓋自動命名）
python evaluate.py --controllers time_based queue_based --output result/my_custom_test
```

### 3. 評估所有可用控制器
```bash
# 自動檢測可用的控制器並評估（使用新的目錄結構）
python evaluate.py --ticks 10000

# 指定隨機種子和描述
python evaluate.py --seed 123 --ticks 10000 --description "paper_final"

# 論文最終結果評估
python evaluate.py --ticks 20000 --description "thesis_results" --seed 42
```

## 🔧 詳細使用方法

### 命令行參數

| 參數 | 描述 | 預設值 | 範例 |
|------|------|--------|------|
| `--controllers` | 要評估的控制器列表 | 所有可用 | `time_based queue_based` |
| `--ticks` | 每個控制器的評估時長 | 20000 | `10000` |
| `--seed` | 隨機種子 | 42 | `123` |
| `--output` | 結果輸出目錄（覆蓋自動命名） | 自動生成 | `result/my_test` |
| `--description` | 評估描述（用於目錄命名） | None | `paper_final` |
| `--analysis-only` | 僅執行分析，跳過評估 | False | - |

### 控制器ID對照表

| 控制器ID | 名稱 | 類型 | 需要模型文件 |
|----------|------|------|-------------|
| `time_based` | Time-Based | 傳統 | ❌ |
| `queue_based` | Queue-Based | 傳統 | ❌ |
| `dqn_step` | DQN-Step | AI | ✅ models/dqn_step.pth |
| `dqn_global` | DQN-Global | AI | ✅ models/dqn_global.pth |
| `nerl_step` | NERL-Step | AI | ✅ models/nerl_step.pth |
| `nerl_global` | NERL-Global | AI | ✅ models/nerl_global.pth |

## 📊 輸出結果

### 生成的文件

執行後會在指定目錄生成以下文件：

**🆕 新的目錄結構（與NetLogo結果分離）**：
```
result/
├── evaluations/                           # 🆕 評估框架專用目錄
│   └── EVAL_20250708_143000_6controllers_20kticks_paper_final/
│       ├── evaluation_config.json        # 🆕 評估配置記錄
│       ├── algorithm_comparison.csv      # 算法對比分析
│       ├── reward_comparison.csv         # 獎勵機制對比分析
│       ├── overall_comparison.csv        # 整體性能對比
│       ├── performance_rankings.json     # 性能排行榜
│       └── charts/                       # 🆕 圖表子目錄
│           ├── performance_radar_chart.png
│           ├── algorithm_comparison_chart.png
│           └── ...
└── 2025-07-08-143000/                    # NetLogo原有結果（不影響）
    ├── intersection-energy-consumption.csv
    └── ...
```

**目錄命名規則**：
- `EVAL_[時間戳]_[控制器描述]_[評估時長]_[自定義描述]`
- 範例：
  - `EVAL_20250708_143000_traditional_only_5kticks`
  - `EVAL_20250708_150000_6controllers_20kticks_paper_final`
  - `EVAL_20250708_160000_dqn_step_nerl_step_10kticks`

### 核心性能指標

| 指標 | 描述 | 單位 |
|------|------|------|
| `total_energy` | 總能源消耗 | 能源單位 |
| `completed_orders` | 完成訂單數 | 個 |
| `completion_rate` | 訂單完成率 | 0-1 |
| `avg_wait_time` | 平均等待時間 | ticks |
| `max_wait_time` | 最大等待時間 | ticks |
| `wait_time_std` | 等待時間標準差 | ticks |
| `robot_utilization` | 機器人利用率 | 0-1 |
| `energy_per_order` | 單位訂單能源消耗 | 能源/訂單 |
| `global_reward` | 綜合獎勵評分 | 無量綱 |

### 🆕 評估配置記錄 (`evaluation_config.json`)

每次評估都會自動生成配置記錄文件：
```json
{
  "timestamp": "2025-07-08 14:30:25",
  "evaluation_ticks": 20000,
  "random_seed": 42,
  "description": "paper_final",
  "planned_controllers": ["time_based", "queue_based"],
  "result_directory": "result/evaluations/EVAL_20250708_143000_...",
  "framework_version": "2.0",
  "directory_structure": {
    "type": "evaluation_namespace",
    "separate_from_netlogo": true,
    "charts_subdirectory": "charts/"
  }
}
```

## 🧪 測試和調試

### 1. 基本功能測試
```bash
# 快速測試傳統控制器（不需要模型文件）
python evaluate.py --controllers time_based --ticks 1000

# 檢查是否有語法錯誤
python evaluate.py --help
```

### 2. 模型文件檢查
```bash
# 檢查當前可用的模型文件
ls models/

# 如果缺少AI控制器模型，會自動跳過
python evaluate.py --controllers dqn_step nerl_step --ticks 1000
```

### 3. 錯誤處理測試
```bash
# 測試無效控制器ID
python evaluate.py --controllers invalid_controller

# 測試極短評估時間
python evaluate.py --controllers time_based --ticks 10
```

## 🔄 與train.py的配合使用

### 完整工作流程

```bash
# 1. 訓練AI模型（階段1.5已完成）
python train.py --agent dqn --reward_mode step --training_ticks 10000
python train.py --agent dqn --reward_mode global --training_ticks 10000
python train.py --agent nerl --reward_mode step --generations 20
python train.py --agent nerl --reward_mode global --generations 20

# 2. 重命名模型文件
mv models/dqn_traffic_10000.pth models/dqn_step.pth
# （其他模型文件類似處理）

# 3. 運行統一評估（使用新的目錄結構）
python evaluate.py --ticks 20000 --description "thesis_final"

# 4. 查看結果（新的目錄結構）
cd result/evaluations/EVAL_[timestamp]_[description]/
```

## 📈 分析報告說明

### 1. algorithm_comparison.csv
比較相同獎勵機制下的DQN vs NERL：
- `reward_mode`: 獎勵模式（step/global）
- `algorithm_1/2`: 對比的算法
- `metric`: 比較指標
- `improvement`: 改進百分比

### 2. reward_comparison.csv
比較相同算法下的step vs global：
- `algorithm`: 算法名稱（DQN/NERL）
- `mode_1/2`: 對比的獎勵模式
- `improvement`: 改進百分比

### 3. overall_comparison.csv
所有控制器的完整性能數據，包含：
- 所有核心KPI指標
- 控制器配置信息
- 評估參數記錄

### 4. performance_rankings.json
按不同指標的性能排行榜：
```json
{
  "total_energy": [
    ["Queue-Based", 1250.5],
    ["DQN-Global", 1380.2],
    ...
  ],
  "completion_rate": [
    ["NERL-Global", 0.95],
    ["DQN-Step", 0.92],
    ...
  ]
}
```

## ⚠️ 注意事項

### Windows環境配置
1. 確保Python環境正確配置
2. 檢查所有依賴套件已安裝
3. NetLogo路徑配置正確

### 模型文件管理
1. AI控制器需要對應的.pth模型文件
2. 缺少模型文件的控制器會自動跳過
3. 建議使用統一的模型命名規範

### 評估時間建議
- **快速測試**: 1000-5000 ticks
- **完整評估**: 20000 ticks（論文標準）
- **詳細分析**: 50000+ ticks

### 內存和時間考量
- 長時間評估可能需要較多內存
- 建議分批評估控制器
- 使用 `--analysis-only` 重新分析已有結果

## 🚀 進階用法

### 1. 批量評估腳本
```bash
# 創建批量評估腳本
cat > batch_evaluate.sh << 'EOF'
#!/bin/bash
echo "開始批量評估..."

# 短時間快速測試（使用新的描述性命名）
python evaluate.py --controllers time_based queue_based --ticks 5000 --description "quick_test"

# 中等時間測試
python evaluate.py --controllers time_based queue_based --ticks 15000 --description "medium_test"

# 完整長時間評估
python evaluate.py --ticks 20000 --description "full_evaluation"

echo "批量評估完成！"
EOF

chmod +x batch_evaluate.sh
./batch_evaluate.sh
```

### 2. 結果比較分析
```bash
# 比較不同評估時間的結果（使用新的目錄結構）
python -c "
import pandas as pd
df1 = pd.read_csv('result/evaluations/EVAL_*_quick_test/overall_comparison.csv')
df2 = pd.read_csv('result/evaluations/EVAL_*_medium_test/overall_comparison.csv')
print('5k vs 15k ticks結果差異:')
print(df2['total_energy'] - df1['total_energy'])
"
```

## 📞 故障排除

### 常見問題
1. **ImportError**: 檢查Python套件安裝
2. **模型文件不存在**: 確認models/目錄中有對應文件
3. **評估中斷**: 檢查內存使用情況
4. **結果異常**: 嘗試不同隨機種子

### 調試技巧
```bash
# 啟用詳細輸出
python evaluate.py --controllers time_based --ticks 100 -v

# 檢查單個控制器
python evaluate.py --controllers time_based --ticks 1000

# 查看生成的結果文件（新的目錄結構）
ls -la result/evaluations/EVAL_*/
head -5 result/evaluations/EVAL_*/overall_comparison.csv
```

---

🎉 **恭喜！** 您現在可以使用evaluate.py進行統一的控制器性能評估了！

有任何問題請參考此指南或查看代碼註釋。
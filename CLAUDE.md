# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 專案概述

這是一個基於 NetLogo 和 Python 的混合式 RMFS（Robotic Mobile Fulfillment System）倉儲自動化研究專案，專注於使用神經進化強化學習（NERL）和深度Q學習（DQN）來優化倉儲中的交通控制系統。

### 核心技術架構
- **混合架構**：Python 後端邏輯 + NetLogo 前端視覺化模擬
- **AI 控制器**：4 種交通控制方法（Time-based、Queue-based、DQN、NERL）
- **強化學習**：PyTorch 實現的深度 Q 網路和神經進化算法
- **分散式控制**：邏輯分散（每個路口獨立決策）、實例集中（每個路口有自己的控制器實例）

### 開發環境注意事項
- 系統使用繁體中文作為主要開發語言（註釋、文檔、用戶交互）
- 目前在 WSL 環境下運行，終端指令執行由用戶負責
- NetLogo 需要在 Windows 環境下運行

## 常用開發命令

### 套件安裝與環境設置
```bash
# 安裝所有依賴套件
pip install -r requirements.txt
```

### AI 模型訓練
```bash
# DQN 訓練（兩種獎勵模式）
python train.py --agent dqn --reward_mode step --episodes 100 --ticks 10000
python train.py --agent dqn --reward_mode global --episodes 100 --ticks 10000

# NERL 訓練（兩種獎勵模式）
python train.py --agent nerl --reward_mode step --generations 50 --population 20 --eval_ticks 2000
python train.py --agent nerl --reward_mode global --generations 50 --population 20 --eval_ticks 2000

# V6.0: Step 獎勵已自動改進（結合絕對值與相對改善）
# 直接使用 step 模式即可獲得改進的混合式獎勵
python train.py --agent nerl --reward_mode step --generations 50 --population 20 --eval_ticks 2000
python train.py --agent dqn --reward_mode step --episodes 100 --ticks 10000

# 訓練時啟動 NetLogo 視覺化
python train.py --agent [nerl/dqn] --netlogo
```

### 效能評估與分析
```bash
# 評估所有控制器
python evaluate.py --ticks 20000 --seed 42

# 評估特定控制器組合
python evaluate.py --controllers time_based queue_based dqn_step dqn_global nerl_step nerl_global

# 生成視覺化圖表
python visualization_generator.py result/evaluations/EVAL_xxxxx
```

### 實驗自動化系統
```bash
# 使用簡潔版實驗管理器（推薦）
python simple_experiment.py

# 系統完整性檢查
python check_system.py
```

## 高階架構說明

### 1. 交通控制系統架構
系統採用分層設計，實現了邏輯分散、實例集中的控制模式：

- **IntersectionManager**：每個路口的管理器，負責協調該路口的交通流
- **Traffic Controllers**：4 種不同的控制策略
  - Time-based：固定時間切換信號燈
  - Queue-based：根據隊列長度動態調整
  - DQN：使用深度 Q 學習的智能控制
  - NERL：使用神經進化的智能控制

### 2. 強化學習系統

#### DQN 控制器
- **狀態空間**：8 維標準化狀態（方向、等待時間、隊列長度、優先級比例等）
- **動作空間**：3 個動作（保持、切換到水平、切換到垂直）
- **獎勵函數**：統一獎勵系統，考慮等待時間減少、能源消耗、停止-前進次數、通過機器人數
- **神經網路**：3 層 MLP（8→24→24→3）

#### NERL 控制器
- **進化機制**：種群大小 40，菁英保留 8，錦標賽選擇
- **適應度函數**：基於累積獎勵的平均值
- **進化間隔**：每 15 ticks 進化一次
- **網路架構**：與 DQN 相同的 3 層 MLP

### 3. 統一獎勵系統

#### Step 模式獎勵（原始版本）
- 通過獎勵：根據機器人優先級 (+1.0/+0.7/+0.5)
- 等待成本：根據等待機器人優先級 (-0.05/-0.02/-0.01)
- 切換懲罰：-0.1（如果切換方向）

#### Global 模式獎勵
- 公式：R = (完成訂單數 × 200) / (能源成本 + 時間成本 + 溢出懲罰)
- 無溢出獎勵：+5.0（如果沒有排隊溢出）

#### V6.0 改進的 Step 獎勵（取代原始版本）
- 公式：R_final = 0.5 × R_current + 0.5 × R_improvement
- R_current：原始 Step 獎勵（絕對值）
- R_improvement：相對改善獎勵
  - Rw (40%)：等待時間是否改善
  - Ra (20%)：是否切換信號
  - Re (20%)：能源消耗是否改善
  - Rq (20%)：排隊長度是否改善

### 4. 倉儲模擬系統
- **實體管理**：Robot、Pod、Station、Intersection 等
- **訂單系統**：支援正常訂單和積壓訂單模式
- **能源模型**：基於物理的能源消耗計算
- **性能指標**：訂單完成率、平均等待時間、能源效率等

## 關鍵文件路徑

### 核心執行文件
- `train.py`：AI 模型訓練主程式
- `evaluate.py`：統一評估框架
- `simple_experiment.py`：簡潔實驗管理系統
- `visualization_generator.py`：圖表生成工具

### AI 控制器實現
- `ai/controllers/dqn_controller.py`：DQN 控制器
- `ai/controllers/nerl_controller.py`：NERL 控制器
- `ai/unified_reward_system.py`：統一獎勵系統
- `ai/adaptive_normalizer.py`：狀態標準化器

### 實驗管理工具
- `experiment_tools/simple_experiment_manager.py`：簡潔實驗管理器
- `experiment_tools/config_manager.py`：配置管理
- `experiment_tools/workflow_runner.py`：工作流執行器

### 結果輸出目錄
- `result/evaluations/`：評估結果
- `result/session_summaries/`：實驗會話總結
- `models/`：訓練好的模型文件

## 開發提示

### 除錯控制
在 `world/entities/robot.py` 中設置 `DEBUG_LEVEL`：
- 0：無除錯輸出
- 1：重要訊息（訓練進度、警告）
- 2：詳細訊息（所有移動和決策細節）

### 模型命名規範
- DQN 模型：`dqn_[reward_mode]_[ticks].pth`
- NERL 模型：`nerl_[reward_mode]_[ticks].pth`

### 實驗配置預設
- **快速模式**：適合測試（1-2 小時）
- **標準模式**：平衡效能（3-4 小時）
- **論文模式**：高品質結果（6-8 小時）

## 注意事項

1. **NetLogo 依賴**：確保 `rmfs.nlogo` 文件存在且 NetLogo 環境正常
2. **模型相容性**：評估時需要對應的預訓練模型文件
3. **路徑問題**：在 WSL 環境下注意 Windows 和 Linux 路徑差異
4. **並行執行**：實驗管理系統支援多線程，注意系統資源
5. **繁體中文**：所有用戶交互、註釋和文檔保持繁體中文
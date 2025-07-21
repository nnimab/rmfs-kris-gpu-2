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
- **神經網路**：3 層 MLP（17→128→64→3）- 2025/07/20 增強架構

#### NERL 控制器
- **進化機制**：種群大小 20（建議），菁英保留比例 0.2，錦標賽選擇
- **適應度函數**：基於累積獎勵的平均值
- **進化間隔**：每 15 ticks 進化一次
- **網路架構**：與 DQN 相同的 3 層 MLP（17→128→64→3）

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

## 2025/07/20 更新記錄

### DQN 訓練數據記錄增強
- 新增 `training_history.json` 自動記錄訓練過程
- 每 500 步保存檢查點（epsilon、loss、Q值、完成率）
- 每 1000 步保存 episode 總結（動作分布、系統指標）
- 新增 `dqn_training_visualizer.py` 用於訓練曲線視覺化

### 神經網路架構增強
- 原架構：17→64→32→3（3,331 參數）
- 新架構：17→128→64→3（11,011 參數）
- 提供更強的表達能力，適合學習複雜交通模式

### NERL 訓練參數優化
- 族群大小：10 → 20（避免過早收斂）
- 並行 workers：根據硬體調整（建議 8-15）
- 評估 ticks：3000（平衡訓練時間與評估品質）

### 修復問題
- 修正 NERL `signal_switch_count` 記錄欄位名稱
- 統一 DQN/NERL 動作編碼（1=水平，2=垂直）

## 2025/07/20 晚上更新 - 交通統計收集問題修復

### 發現的問題
訓練結果顯示所有交通統計都是 0：
- `avg_wait_time = 0`
- `signal_switch_count = 0`
- `total_stop_go_events = 0`
- `avg_traffic_rate = 0`

### 問題根源
1. **NERL/DQN 訓練缺少統計更新**：訓練過程沒有調用 `update_system_metrics()`
2. **方法名稱錯誤**：`unified_reward_system.py` 尋找 `calculateAverageFlow()` 但實際方法是 `getAverageTrafficRate()`
3. **evaluate.py 缺少指標收集**：沒有收集 `signal_switch_count` 和 `avg_traffic_rate`

### 已修復
1. ✅ `ai/unified_reward_system.py:569` - 修正方法名稱為 `getAverageTrafficRate()`
2. ✅ `train.py:157-160` - NERL 訓練加入 `update_system_metrics()` 和 `update_episode_metrics()`
3. ✅ `train.py:661-665` - DQN 訓練加入相同的統計更新
4. ✅ `evaluate.py:213-255` - 加入 signal_switch_count 和 avg_traffic_rate 的收集邏輯

### 重要提醒
- 重新訓練前請確保這些修改都已生效
- 現在訓練結果應該會正確顯示所有交通統計數據

## 2025/07/21 - V7.0 系統重大更新

### V7.0 核心改進
1. **關鍵路口權重系統**
   - 識別 11 個關鍵路口：[0, 6, 12, 18, 24, 30, 36, 42, 48, 54, 60]
   - 初始 5x 權重，後降至 2x（避免過度優化）
   - 實現位置：`ai/unified_reward_system.py`

2. **限速控制系統**
   - 動作空間從 3 擴展到 6
   - 新增動作：限速 30%、50%、取消限速
   - 能源消耗 ∝ 速度^1.5
   - 新增檔案：`world/speed_limit_manager.py`

3. **走廊級限速設計**
   - 整條走廊限速，而非單一路口
   - 支援水平/垂直走廊獨立控制
   - 自動應用到走廊上的所有機器人

### 訓練問題診斷與修復

#### 問題 1：NERL 不做決策（100% Keep）
- **原因**：網路初始化導致所有輸出為 0
- **修復**：
  - 重寫 `EvolvableNetwork` 初始化
  - 輸出層使用 uniform(-0.3, 0.3)
  - 偏置設為遞增值確保動作差異

#### 問題 2：動作統計缺失
- **新增功能**：
  - `action_counts` 追蹤各動作使用次數
  - 訓練日誌顯示動作使用百分比
  - 每代總結顯示最佳個體動作分布

#### 問題 3：模型相容性錯誤
- **錯誤**：`'EvolvableNetwork' object has no attribute 'fc1'`
- **修復**：
  - 添加 `load_state_dict` 方法處理舊模型
  - 保留 `self.layers` 屬性向後相容

### 獎勵系統調整（V7.1）
1. **簡化訂單完成獎勵**
   - 運送中機器人直接獲得 2.0 × 路口權重獎勵
   - 移除複雜的距離檢查

2. **降低系統複雜度**
   - 關鍵路口權重：5.0 → 2.0
   - 總獎勵放大倍數：10 → 5

### 關鍵檔案修改
- `ai/controllers/nerl_controller.py`：網路架構重寫、動作統計
- `ai/unified_reward_system.py`：V7 獎勵系統、權重調整
- `world/entities/robot.py`：限速支援
- `train.py`：動作統計輸出、錯誤修復

### 訓練建議
```bash
# 標準訓練
python train.py --agent nerl --reward_mode step --generations 10 --population 20 --eval_ticks 3000

# 快速測試
python train.py --agent nerl --reward_mode step --generations 5 --population 10 --eval_ticks 2000
```

### 預期改進
- 動作使用多樣化（不再 100% Keep）
- 限速功能開始被學習使用
- 更穩定的訓練過程
- 更好的訂單完成率

## 2025/07/21 晚上更新 - 重要問題修復

### 1. DQN 死鎖問題診斷
**問題現象**：
- DQN 訓練在 5250 ticks 死鎖
- 路口 30 等待超過 655 ticks
- 20 個機器人全部卡住
- Final Epsilon: 1.0（完全隨機探索）

**死鎖原因**：
- V7 的 6 動作空間 + epsilon=1.0 完全隨機 = 災難
- 關鍵路口（特別是路口 30）成為瓶頸

### 2. 機器人直衝揀貨台 Bug
**問題發現**：
- 機器人收到任務後沒有去取貨架
- 直接衝向揀貨台造成嚴重堵塞

**問題根源**：
```python
# robot.py 第 806 行（修復前）
def assignJobAndSetToTakePod(self, job: Job):
    self.job = job
    self.updateState("taking_pod", self.latest_tick)
    self.job.job_state = "take_pod"
    # 缺少：self.setMoveToTakePod()
```

**修復**：
- 在 `assignJobAndSetToTakePod()` 中加入 `self.setMoveToTakePod()`
- 確保機器人先移動到貨架位置

### 3. NetLogo 除錯訊息問題
**問題**：大量 DEBUG 訊息干擾訓練觀察

**修復**：
- 註釋掉 `netlogo.py` 中的所有 `print("DEBUG: ...")` 語句
- 現在 `--log_level` 參數能正確控制輸出

### 4. 機器人數量優化
**修改**：30 → 20 個機器人
- 檔案：`lib/generator/warehouse_generator.py:22`
- 理由：減少擁堵，提高學習效率

### 5. NetLogo + train.py 使用說明
**正確流程**：
```bash
python train.py --agent dqn --reward_mode step --netlogo --training_ticks 10000
# 等待 NetLogo 開啟
# 在終端機按 Enter（不要在 NetLogo 操作）
# Python 會自動控制一切
```

### 重要提醒
- 這些修復對 DQN 和 NERL 訓練都有幫助
- 建議先用較小參數測試系統穩定性
- V7 系統的 6 動作空間需要更謹慎的探索策略
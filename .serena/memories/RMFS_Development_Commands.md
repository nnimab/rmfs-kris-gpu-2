# RMFS 常用開發指令

## 環境設置
```bash
pip install -r requirements.txt
```

## AI 訓練指令

### DQN 訓練
```bash
# Step 獎勵模式
python train.py --agent dqn --reward_mode step --episodes 100 --ticks 10000

# Global 獎勵模式
python train.py --agent dqn --reward_mode global --episodes 100 --ticks 10000

# 啟用 NetLogo 視覺化
python train.py --agent dqn --reward_mode step --netlogo --training_ticks 10000
```

### NERL 訓練
```bash
# 標準訓練（推薦）
python train.py --agent nerl --reward_mode step --generations 10 --population 20 --eval_ticks 3000

# 快速測試
python train.py --agent nerl --reward_mode step --generations 5 --population 10 --eval_ticks 2000

# 論文品質
python train.py --agent nerl --reward_mode step --generations 50 --population 20 --eval_ticks 3000
```

## 評估與分析

### 效能評估
```bash
# 評估所有控制器
python evaluate.py --ticks 20000 --seed 42

# 評估特定控制器
python evaluate.py --controllers time_based queue_based dqn_step nerl_step

# 產生視覺化圖表
python visualization_generator.py result/evaluations/EVAL_xxxxx
```

### 實驗管理
```bash
# 簡潔實驗管理器（推薦）
python simple_experiment.py

# 系統檢查
python check_system.py
```

## 除錯設定
在 `world/entities/robot.py` 設定 `DEBUG_LEVEL`：
- 0：無輸出
- 1：重要訊息
- 2：詳細訊息

## 模型檔案命名
- DQN：`dqn_[reward_mode]_[ticks].pth`
- NERL：`nerl_[reward_mode]_[ticks].pth`

## NetLogo 注意事項
1. 等待 NetLogo 視窗開啟
2. 在終端機按 Enter（不要在 NetLogo 操作）
3. Python 會自動控制模擬流程
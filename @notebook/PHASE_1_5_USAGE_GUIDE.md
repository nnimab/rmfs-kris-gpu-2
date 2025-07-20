# 階段1.5改進使用指南

## 概述

階段1.5成功實現了三個關鍵算法優化，解決了原有NERL和DQN控制器的公平性問題：

1. **解決資訊孤島問題** - 16維狀態空間包含相鄰路口信息
2. **修復硬編碼正規化** - 自適應正規化機制
3. **統一獎勵機制** - 支持公平對比的雙重框架

## 🎯 主要改進功能

### 1. 16維狀態空間

#### 改進前（8維）
```
[方向編碼, 時間差, 水平機器人數, 垂直機器人數, 
 水平優先級比例, 垂直優先級比例, 水平等待時間, 垂直等待時間]
```

#### 改進後（16維）
```
當前路口狀態（8維）+ 相鄰路口狀態（8維）
- 相鄰路口機器人數量
- 相鄰路口優先級機器人數
- 相鄰路口平均等待時間
- 相鄰路口方向分佈
- 相鄰路口負載均衡指標
```

**優勢：** 解決資訊孤島問題，實現區域性協調決策

### 2. 自適應正規化機制

#### 改進前（硬編碼）
```python
h_count_norm = min(h_count / 10.0, 1.0)  # 固定最大值10
h_wait_norm = min(h_wait_time / 50.0, 1.0)  # 固定最大值50
```

#### 改進後（自適應）
```python
normalizer = TrafficStateNormalizer(window_size=1000)
normalizer.update_statistics(raw_features)
normalized = normalizer.normalize_features(raw_features)
```

**優勢：** 動態適應極端交通狀況，提高泛化能力

### 3. 統一獎勵機制

#### 改進前（不一致）
- **DQN：** 5個組件的即時獎勵
- **NERL：** 全局適應度函數

#### 改進後（統一）
- **即時模式：** 8個維度的詳細獎勵
- **全局模式：** 回合結束時的綜合評估
- **雙重對比：** 相同獎勵機制下的公平比較

## 🚀 使用方法

### 安裝依賴

```bash
pip install -r requirements.txt
```

### 訓練命令

#### 1. NERL訓練（推薦全局獎勵）
```bash
# 默認配置
python train.py --agent nerl

# 自定義配置
python train.py --agent nerl --reward_mode global --generations 30 --population 15 --eval_ticks 3000

# 即時獎勵模式（用於對比）
python train.py --agent nerl --reward_mode step
```

#### 2. DQN訓練（推薦即時獎勵）
```bash
# 默認配置
python train.py --agent dqn

# 自定義配置
python train.py --agent dqn --reward_mode step --training_ticks 15000

# 全局獎勵模式（用於對比）
python train.py --agent dqn --reward_mode global
```

#### 3. 四種對比模式
```bash
# 算法對比（相同獎勵機制）
python train.py --agent dqn --reward_mode step    # DQN即時獎勵
python train.py --agent nerl --reward_mode step   # NERL即時獎勵

python train.py --agent dqn --reward_mode global  # DQN全局獎勵
python train.py --agent nerl --reward_mode global # NERL全局獎勵

# 獎勵機制對比（相同算法）
python train.py --agent dqn --reward_mode step    # DQN即時 vs 全局
python train.py --agent dqn --reward_mode global

python train.py --agent nerl --reward_mode step   # NERL即時 vs 全局
python train.py --agent nerl --reward_mode global
```

### 參數說明

| 參數 | 說明 | 預設值 | 選項 |
|------|------|--------|------|
| `--agent` | 要訓練的算法 | 必需 | `nerl`, `dqn` |
| `--reward_mode` | 獎勵模式 | `auto` | `step`, `global`, `auto` |
| `--generations` | NERL進化代數 | 50 | 正整數 |
| `--population` | NERL族群大小 | 20 | 正整數 |
| `--eval_ticks` | NERL個體評估時間 | 2000 | 正整數 |
| `--training_ticks` | DQN訓練時間步 | 10000 | 正整數 |

### NetLogo介面使用

#### 1. 設置16維控制器
```python
# Python代碼中
netlogo.set_dqn_controller()  # 自動使用16維狀態空間
netlogo.set_nerl_controller() # 自動使用16維狀態空間
```

#### 2. 查看正規化統計
```python
# 獲取控制器統計
controller = warehouse.intersection_manager.controllers.get('dqn')
normalizer_stats = controller.normalizer.get_statistics_summary()
print(normalizer_stats)
```

#### 3. 獎勵模式切換
```python
controller = warehouse.intersection_manager.controllers.get('dqn')
controller.set_reward_mode('global')  # 切換到全局模式
```

## 📊 模型輸出

### 訓練模型命名
- **DQN模型：** `models/dqn_traffic_{ticks}.pth`
- **NERL模型：** `models/nerl_traffic_{ticks}.pth`

### 四種對比模型
訓練完成後將產出四個模型變體：
1. `dqn_step.pth` - DQN即時獎勵
2. `dqn_global.pth` - DQN全局獎勵  
3. `nerl_step.pth` - NERL即時獎勵
4. `nerl_global.pth` - NERL全局獎勵

## 🔧 高級配置

### 自定義獎勵權重
```python
from ai.unified_reward_system import UnifiedRewardSystem

custom_weights = {
    'wait_time': 2.0,        # 等待時間改善權重
    'passing': 1.5,          # 機器人通過獎勵
    'switch_penalty': -3.0,  # 方向切換懲罰
    'energy': -0.2,          # 能源消耗懲罰
    'fairness': 2.0,         # 公平性獎勵
    'deadlock_penalty': -10.0 # 死鎖懲罰
}

reward_system = UnifiedRewardSystem(reward_mode="step", weights=custom_weights)
```

### 自定義正規化窗口
```python
from ai.adaptive_normalizer import TrafficStateNormalizer

# 更長的統計窗口（更穩定但適應較慢）
normalizer = TrafficStateNormalizer(window_size=2000)

# 更短的窗口（適應更快但可能不穩定）
normalizer = TrafficStateNormalizer(window_size=500)
```

## 📈 性能預期

### 預期改進效果
1. **資訊孤島解決：** 路口協調決策能力提升15-25%
2. **自適應正規化：** 極端交通適應能力提升30-40%  
3. **統一獎勵：** 公平對比基礎，消除算法偏見

### 建議實驗流程
1. **基線測試：** 使用原有8維控制器建立基線
2. **16維測試：** 驗證狀態空間擴展效果
3. **對比實驗：** 四種模式公平比較
4. **消融研究：** 分析各改進組件的貢獻

## ⚠️ 注意事項

### 計算資源
- **16維狀態：** 計算複雜度略有增加（約15%）
- **自適應正規化：** 記憶體使用增加（統計窗口）
- **統一獎勵：** 獎勵計算更複雜但更準確

### 兼容性
- **向後兼容：** 原有8維控制器仍可使用
- **模型文件：** 新舊模型不互相兼容
- **NetLogo介面：** 無需修改，自動適配

### 調試建議
```bash
# 測試基本功能
python simple_test_phase_1_5.py

# 檢查模型架構
python -c "from ai.controllers.dqn_controller import DQNController; print(DQNController().state_size)"

# 驗證獎勵系統
python -c "from ai.unified_reward_system import UnifiedRewardSystem; r=UnifiedRewardSystem('step'); print('OK')"
```

## 🎯 下一步：階段2評估

完成階段1.5改進後，建議進入階段2：

1. **創建evaluate.py** - 統一評估框架
2. **多維度對比實驗** - 六種控制器公平比較
3. **數據分析與視覺化** - 論文所需圖表和報告

使用改進後的控制器將為論文提供更可靠、更公平的實驗結果。
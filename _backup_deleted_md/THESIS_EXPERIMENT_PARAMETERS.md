# 論文實驗參數配置指南

**版本**: 1.0  
**日期**: 2025年7月8日  
**目的**: 提供學術論文標準的實驗參數配置

---

## 🎯 論文實驗設計原則

### 學術標準要求
- **統計顯著性**: 足夠的樣本大小和實驗時長
- **公平對比**: 相同的評估條件和環境設置
- **可重現性**: 固定的隨機種子和參數記錄
- **計算可行性**: 在合理時間內完成的參數設置

### 基於階段1.5的改進
- ✅ 16維狀態空間（包含相鄰路口信息）
- ✅ 自適應正規化機制
- ✅ 統一獎勵系統（step/global兩種模式）

---

## 🧠 AI控制器訓練參數

### NERL控制器訓練參數

#### 建議配置（學術標準）
```bash
# NERL Step模式
python train.py --agent nerl --reward_mode step \
  --generations 50 \
  --population 20 \
  --eval_ticks 2000

# NERL Global模式  
python train.py --agent nerl --reward_mode global \
  --generations 50 \
  --population 20 \
  --eval_ticks 2000
```

#### 參數解釋
| 參數 | 值 | 學術依據 |
|------|----|---------| 
| `generations` | 50 | 足夠的進化代數，通常30-100代間收斂 |
| `population` | 20 | 標準族群大小，平衡多樣性與計算成本 |
| `eval_ticks` | 2000 | 單個個體評估時長，確保性能穩定性 |

#### 預期訓練時間
- **每個個體評估**: ~1-2分鐘（2000 ticks）
- **每代總時間**: ~30-40分鐘（20個個體）
- **完整訓練**: ~25-35小時（50代）
- **建議**: 分兩天進行，每天25代

### DQN控制器訓練參數

#### 建議配置（學術標準）
```bash
# DQN Step模式
python train.py --agent dqn --reward_mode step \
  --training_ticks 20000

# DQN Global模式
python train.py --agent dqn --reward_mode global \
  --training_ticks 20000
```

#### 參數解釋
| 參數 | 值 | 學術依據 |
|------|----|---------| 
| `training_ticks` | 20000 | 足夠的訓練時長，DQN通常需要15k-30k步收斂 |

#### 預期訓練時間
- **每個模型**: ~3-4小時
- **兩個模型**: ~6-8小時
- **建議**: 可並行訓練或分別進行

---

## 🏛️ 傳統控制器參數

### Time-Based控制器
```
固定參數（不可調）：
- 水平綠燈時間: 70 ticks
- 垂直綠燈時間: 30 ticks
- 週期性切換: 無動態調整
```

### Queue-Based控制器
```
建議參數配置：
- min_green_time: 15 ticks （防抖動）
- bias_factor: 1.5 （水平方向偏向）
- 優先級權重:
  - delivering_pod: 3.0
  - returning_pod: 2.0  
  - taking_pod: 1.0
  - idle: 0.5
```

---

## 📊 評估實驗參數

### 統一評估設置

#### 建議配置（論文標準）
```bash
# 完整論文評估
python evaluate.py \
  --ticks 30000 \
  --seed 42 \
  --description "thesis_final_30k"

# 中等規模測試  
python evaluate.py \
  --ticks 15000 \
  --seed 42 \
  --description "thesis_medium_15k"

# 快速驗證
python evaluate.py \
  --ticks 5000 \
  --seed 42 \
  --description "thesis_quick_5k"
```

#### 參數解釋
| 參數 | 建議值 | 學術依據 |
|------|--------|----------|
| `ticks` | 30000 | 足夠長的評估時間，確保統計顯著性 |
| `seed` | 42 | 固定隨機種子，確保結果可重現 |
| 重複次數 | 3-5次 | 不同種子下的多次實驗，計算平均值和標準差 |

### 多次實驗設計
```bash
# 建議進行3次獨立實驗，使用不同隨機種子
python evaluate.py --ticks 30000 --seed 42 --description "thesis_run1"
python evaluate.py --ticks 30000 --seed 123 --description "thesis_run2"  
python evaluate.py --ticks 30000 --seed 789 --description "thesis_run3"
```

---

## 🔬 論文實驗矩陣

### 實驗1：基準性能對比
**目的**: 建立各控制器的基準性能
```bash
python evaluate.py --controllers time_based queue_based \
  --ticks 15000 --seed 42 --description "baseline_traditional"

python evaluate.py --controllers dqn_step dqn_global nerl_step nerl_global \
  --ticks 15000 --seed 42 --description "baseline_ai"
```

### 實驗2：算法對比（DQN vs NERL）
**目的**: 比較兩種學習算法的效果
```bash
# Step獎勵模式下的算法對比
python evaluate.py --controllers dqn_step nerl_step \
  --ticks 20000 --seed 42 --description "algorithm_comparison_step"

# Global獎勵模式下的算法對比
python evaluate.py --controllers dqn_global nerl_global \
  --ticks 20000 --seed 42 --description "algorithm_comparison_global"
```

### 實驗3：獎勵機制對比（Step vs Global）
**目的**: 分析獎勵機制對學習效果的影響
```bash
# DQN在不同獎勵機制下的表現
python evaluate.py --controllers dqn_step dqn_global \
  --ticks 20000 --seed 42 --description "reward_comparison_dqn"

# NERL在不同獎勵機制下的表現
python evaluate.py --controllers nerl_step nerl_global \
  --ticks 20000 --seed 42 --description "reward_comparison_nerl"
```

### 實驗4：完整對比（論文主要結果）
**目的**: 所有控制器的全面對比，論文的核心數據
```bash
# 論文主要實驗結果
python evaluate.py --ticks 30000 --seed 42 --description "thesis_main_results"

# 重複實驗確保可靠性
python evaluate.py --ticks 30000 --seed 123 --description "thesis_replication_1" 
python evaluate.py --ticks 30000 --seed 789 --description "thesis_replication_2"
```

---

## ⏱️ 時間規劃建議

### 訓練階段（預計3-4天）
```
第1天：DQN模型訓練
- 上午：DQN Step模式（3-4小時）
- 下午：DQN Global模式（3-4小時）

第2-3天：NERL模型訓練  
- 第2天：NERL Step模式（25代，~12-15小時）
- 第3天：NERL Global模式（25代，~12-15小時）

第4天：模型驗證和整理
- 驗證所有模型可正常載入
- 進行快速評估測試
```

### 評估階段（預計1-2天）
```
第5天：核心實驗
- 上午：基準實驗（實驗1）
- 下午：算法對比實驗（實驗2）

第6天：完整實驗
- 上午：獎勵機制對比（實驗3）
- 下午：論文主要結果（實驗4）
```

---

## 📈 預期結果指標

### 關鍵性能指標（KPI）
1. **能源效率**: 總能源消耗、單位訂單能源消耗
2. **完成效率**: 訂單完成率、完成時間
3. **交通公平性**: 平均等待時間、最大等待時間、等待時間標準差
4. **系統穩定性**: 停止啟動次數、交通流量變化
5. **綜合評分**: 統一獎勵系統的全局評分

### 預期性能排序（假設）
```
能源效率：Queue-Based > NERL-Global > DQN-Global > NERL-Step > DQN-Step > Time-Based
完成效率：NERL-Global > DQN-Global > Queue-Based > NERL-Step > DQN-Step > Time-Based  
交通公平性：NERL-Global > Queue-Based > DQN-Global > NERL-Step > DQN-Step > Time-Based
```

---

## 🛠️ 參數調整策略

### 如果訓練效果不佳

#### NERL調整
```bash
# 如果收斂太慢，增加族群大小
--population 30

# 如果過擬合，減少評估時間
--eval_ticks 1500

# 如果需要更好收斂，增加代數
--generations 80
```

#### DQN調整
```bash
# 如果收斂太慢，增加訓練時間
--training_ticks 30000

# 如果想要快速驗證，減少訓練時間
--training_ticks 10000
```

### 如果計算資源不足
```bash
# 快速實驗參數（降低標準但保持相對對比）
NERL: --generations 30 --population 15 --eval_ticks 1500
DQN: --training_ticks 15000
評估: --ticks 15000
```

### 如果時間充裕（高標準論文）
```bash
# 高質量實驗參數
NERL: --generations 80 --population 25 --eval_ticks 3000
DQN: --training_ticks 30000  
評估: --ticks 50000（多次重複）
```

---

## 📋 實驗記錄模板

### 訓練記錄
```
日期：_______
模型：NERL/DQN + Step/Global
參數：generations=__, population=__, eval_ticks=__ / training_ticks=__
開始時間：_______
結束時間：_______
最終模型：models/[model_name].pth
最佳性能：_______
備註：_______
```

### 評估記錄
```
日期：_______
實驗編號：實驗1/2/3/4
控制器組合：_______
評估時長：_______
隨機種子：_______
結果目錄：result/evaluations/EVAL_______
關鍵指標：
- 能源消耗：_______
- 完成率：_______
- 平均等待：_______
備註：_______
```

---

## 💡 我的建議

### 推薦的實驗策略

**保守策略**（時間有限）：
- NERL: 30代、15個體、1500 ticks
- DQN: 15000 ticks
- 評估: 15000 ticks、單次實驗

**標準策略**（論文要求）：
- NERL: 50代、20個體、2000 ticks  
- DQN: 20000 ticks
- 評估: 30000 ticks、3次重複

**高標準策略**（充裕時間）：
- NERL: 80代、25個體、3000 ticks
- DQN: 30000 ticks
- 評估: 50000 ticks、5次重複

### 建議採用標準策略
這個配置在學術要求和計算成本間取得平衡，能夠產出可靠的論文結果。

---

🎯 **這個參數配置指南基於學術標準和您的階段1.5成果，應該能產出高質量的論文實驗數據！**
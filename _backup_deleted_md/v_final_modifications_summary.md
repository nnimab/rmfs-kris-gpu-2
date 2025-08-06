# V-Final 修改總結

## 執行日期：2025-07-16

### 第一部分：統一並簡化神經網絡架構

#### 1. NERL 神經網絡修改
**檔案：** `ai/controllers/nerl_controller.py`
**修改內容：**
- 將原本的 3 層架構 (1024→512→256) 簡化為 2 層架構 (64→32)
- 移除了 BatchNorm 層
- 新架構：
  - Input Layer: 17 nodes
  - Hidden Layer 1: 64 nodes (ReLU)
  - Hidden Layer 2: 32 nodes (ReLU)
  - Output Layer: 3 nodes

#### 2. DQN 神經網絡修改
**檔案：** `ai/deep_q_network.py`
**修改內容：**
- 與 NERL 保持完全一致的架構
- 同樣簡化為 2 層架構 (64→32)
- 確保兩種算法使用相同的網絡容量

### 第二部分：實現差異化的 NERL 超參數變體

#### 1. 主訓練腳本修改
**檔案：** `train.py`
**修改內容：**

##### a. 實現變體參數邏輯（第 558-591 行）
```python
# 通用基礎參數
base_nerl_params = {
    'elite_size': 2,
    'crossover_rate': 0.7
}

# 根據 variant 設置差異化參數
if args.variant == 'a':
    # 探索型 (Exploration)
    variant_params = {
        'mutation_rate': 0.3,
        'mutation_strength': 0.2
    }
elif args.variant == 'b':
    # 利用型 (Exploitation)
    variant_params = {
        'mutation_rate': 0.1,
        'mutation_strength': 0.05
    }
```

##### b. 修改函數簽名以傳遞參數
- `run_nerl_training` 函數新增 `nerl_params` 參數
- `evaluate_individual_parallel` 函數新增 `nerl_params` 參數處理

##### c. 確保參數傳遞到所有工作進程
- 在任務列表中包含 `nerl_params`
- 在 worker 進程中將參數傳遞給控制器

### 參數總結

#### Variant A (探索型)
- `elite_size`: 2
- `crossover_rate`: 0.7
- `mutation_rate`: 0.3 (高突變率)
- `mutation_strength`: 0.2 (高突變強度)
- 適合初期探索，尋找新的解決方案空間

#### Variant B (利用型)
- `elite_size`: 2
- `crossover_rate`: 0.7
- `mutation_rate`: 0.1 (低突變率)
- `mutation_strength`: 0.05 (低突變強度)
- 適合後期優化，精細調整已找到的解決方案

### 預期效果

1. **簡化網絡架構**
   - 參數量從約 673,536 減少到約 1,347
   - 訓練速度預計提升 10-20 倍
   - 減少過擬合風險

2. **差異化變體**
   - Variant A：更大的探索範圍，可能找到創新解決方案
   - Variant B：更穩定的收斂，適合精細優化

### 使用範例

```bash
# 探索型 NERL 訓練
python train.py --agent nerl --reward_mode global --variant a --generations 20 --population 20 --eval_ticks 4000

# 利用型 NERL 訓練
python train.py --agent nerl --reward_mode global --variant b --generations 20 --population 20 --eval_ticks 4000
```
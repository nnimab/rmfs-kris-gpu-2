# 訓練速度優化方案

## 當前瓶頸分析

基於代碼分析，訓練速度的主要瓶頸不是神經網絡大小，而是：

### 1. **NetLogo 通信開銷 (最大瓶頸)**
- 每個 tick 都要收集所有 25+ 個路口的狀態
- Python ↔ NetLogo 的通信是序列化的
- 即使路口沒有機器人也要收集狀態

### 2. **評估時長**
- 每個個體評估 4000 ticks
- 20 個個體 × 4000 ticks = 80,000 次通信/世代

### 3. **日誌和數據收集開銷**
- 頻繁的日誌寫入
- 大量的狀態追蹤

## 立即可實施的優化方案

### 優化 1：只收集有機器人的路口狀態
```python
# 在 netlogo.py 的 get_intersections_needing_action() 中
def get_intersections_needing_action(warehouse: Warehouse):
    states = {}
    for intersection in warehouse.intersection_manager.intersections:
        # 只有當路口有機器人時才收集狀態
        if len(intersection.horizontal_robots) > 0 or len(intersection.vertical_robots) > 0:
            state = controller.get_state(intersection, warehouse._tick, warehouse)
            intersection_key = f"intersection-{intersection.id}"
            states[intersection_key] = state.tolist()
    return states
```

### 優化 2：減少評估時長
```bash
# 快速實驗模式
python train.py --agent nerl --reward_mode global --variant a \
    --generations 10 --population 10 --eval_ticks 1000  # 從 4000 減到 1000

# 標準模式
--eval_ticks 2000  # 折中方案
```

### 優化 3：批量處理多個 ticks
```python
# 可以修改為每 N 個 ticks 才進行一次決策
DECISION_INTERVAL = 5  # 每 5 ticks 做一次決策

if python_tick % DECISION_INTERVAL == 0:
    states_dict = netlogo.get_intersections_needing_action(warehouse)
    # ... 進行決策
```

### 優化 4：減少日誌開銷
```bash
# 使用 WARNING 級別減少日誌輸出
python train.py --log_level WARNING
```

### 優化 5：增加並行 workers
```bash
# 充分利用多核 CPU
python train.py --parallel_workers 10  # 如果有 12 核 CPU
```

## 預期速度提升

實施這些優化後，預期速度提升：

1. **只收集活躍路口**：減少 60-80% 的通信量
2. **減少評估時長**：直接減少 50-75% 的總時間
3. **批量決策**：減少 80% 的決策計算
4. **減少日誌**：提升 10-20%
5. **並行處理**：線性加速（取決於 CPU 核心數）

## 建議的快速測試命令

```bash
# 極速測試（用於驗證代碼正確性）
python train.py --agent nerl --reward_mode global --variant a \
    --generations 3 --population 5 --eval_ticks 500 \
    --parallel_workers 5 --log_level WARNING

# 快速實驗（1小時內完成）
python train.py --agent nerl --reward_mode global --variant a \
    --generations 10 --population 10 --eval_ticks 1000 \
    --parallel_workers 10 --log_level WARNING

# 標準實驗（2-3小時）
python train.py --agent nerl --reward_mode global --variant a \
    --generations 20 --population 20 --eval_ticks 2000 \
    --parallel_workers 10 --log_level INFO
```

## 最重要的優化

如果只能選一個優化，請實施「只收集有機器人的路口狀態」，這將帶來最大的速度提升。
# 重大 Bug：評估階段等待時間計算錯誤

## 問題描述
evaluate.py 中的等待時間計算存在嚴重錯誤，導致評估結果不可靠。

## 訓練 vs 評估數據差異

### 訓練時（正常）
- avg_wait_time: 30-31（受防死鎖機制限制）
- 計算方式：總等待時間 / 等待事件數量
- 位置：ai/unified_reward_system.py:518

### 評估時（異常）
- avg_wait_time: 3465-5489（不合理的高值）
- 錯誤原因：計算邏輯有兩個嚴重問題

## 具體錯誤

### 錯誤 1：數據收集覆蓋而非累加
```python
# evaluate.py:251（錯誤）
metrics['total_wait_time'] = total_wait  # 每次覆蓋，應該累加
```
每 100 ticks 收集一次，但只保留最後一次的值。

### 錯誤 2：計算公式不一致
```python
# evaluate.py:290（錯誤）
avg_wait_time = metrics['total_wait_time'] / (metrics['total_robots'] * final_tick)
```
分母用總 tick 數 × 機器人數，但分子只是最後一次快照。

### 訓練的正確做法
```python
# ai/unified_reward_system.py:518（正確）
if len(all_robot_wait_times) > 0:
    self.episode_data['avg_wait_time'] = total_wait_time / len(all_robot_wait_times)
```

## 影響範圍
1. 所有評估結果的 avg_wait_time 不可靠
2. avg_traffic_rate 可能有類似問題
3. 其他指標（能源、訂單完成）看起來正常

## 修復建議

### 方案 1：累加修復
```python
# evaluate.py:251 改為
if 'total_wait_time' not in metrics:
    metrics['total_wait_time'] = 0
metrics['total_wait_time'] += total_wait  # 累加而非覆蓋
```

### 方案 2：與訓練保持一致（推薦）
```python
# 收集所有等待事件
all_wait_times = []
for robot in warehouse.robot_manager.robots:
    if hasattr(robot, 'intersection_wait_time'):
        for wait_time in robot.intersection_wait_time.values():
            if wait_time > 0:
                all_wait_times.append(wait_time)

# 計算平均（與訓練一致）
avg_wait_time = sum(all_wait_times) / len(all_wait_times) if all_wait_times else 0
```

## 其他發現

### 等待時間 30 上限
- 位置：world/entities/robot.py:537
- 機制：超過 30 ticks 強制通過（防死鎖）
- 這是設計特性，不是 bug

### 訓練數據正常
從 thesis/第四章/訓練過程紀錄檔 確認：
- 所有指標都有正確收集
- 數值合理且非零
- 2025/07/20 的修復有效

## 需要立即行動
1. 修復 evaluate.py 的計算邏輯
2. 重新執行所有評估
3. 更新論文中的評估數據
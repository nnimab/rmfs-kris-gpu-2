# evaluate.py 等待時間計算修復完成

## 修復日期
2025-08-04

## 問題摘要
evaluate.py 中的等待時間計算存在嚴重錯誤，導致評估結果不可靠：
- 舊方法：avg_wait_time = total_wait_time / (robots × ticks) 
- 結果：0.002-0.005 的不合理小值

## 修復內容

### 1. 數據收集邏輯修復（行 244-262）
```python
# 收集所有機器人的等待事件（與訓練保持一致）
if 'all_wait_events' not in metrics:
    metrics['all_wait_events'] = []

for robot in warehouse.robot_manager.robots:
    if hasattr(robot, 'intersection_wait_time'):
        for intersection_id, wait_time in robot.intersection_wait_time.items():
            if wait_time > 0:
                metrics['all_wait_events'].append(wait_time)

# 累加總等待時間（用於後續計算）
if 'total_wait_time' not in metrics:
    metrics['total_wait_time'] = 0

current_tick_wait = sum(robot.intersection_wait_time.values() 
                      for robot in warehouse.robot_manager.robots 
                      if hasattr(robot, 'intersection_wait_time'))
metrics['total_wait_time'] += current_tick_wait
```

### 2. 計算公式修復（行 301-307）
```python
# 平均等待時間計算（與訓練保持一致）
# 使用所有等待事件的平均值，而不是總等待時間除以機器人數×tick數
if 'all_wait_events' in metrics and len(metrics['all_wait_events']) > 0:
    # 與 ai/unified_reward_system.py:546 保持一致
    avg_wait_time = sum(metrics['all_wait_events']) / len(metrics['all_wait_events'])
else:
    avg_wait_time = 0
```

## 修復效果
- 新方法：avg_wait_time = sum(wait_events) / len(wait_events)
- 結果：10-30 ticks 的合理值（符合防死鎖機制的 30 ticks 上限）
- 與訓練時的計算邏輯完全一致

## 驗證結果
- 創建了 verify_evaluate_fix.py 驗證腳本
- 模擬數據測試顯示新方法產生合理的等待時間（20.30 ticks）
- 舊方法與新方法差異達 10000 倍

## 影響範圍
- 所有之前的評估結果中的 avg_wait_time 都不可靠
- 需要重新執行所有評估以獲得正確的等待時間數據
- 其他指標（能源、訂單完成率等）不受影響

## 後續建議
1. 立即重新執行所有控制器的評估
2. 更新論文中的評估數據
3. 考慮添加單元測試防止類似問題再次發生
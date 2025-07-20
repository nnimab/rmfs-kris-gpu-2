# 機器人利用率計算問題分析報告

## 問題概述

在整個 RMFS 系統中，`robot_utilization` 指標總是顯示 100% 或接近 100%，這並不反映真實的機器人利用率情況。

## 問題根因

### 錯誤的計算邏輯

目前系統中有 3 個主要位置使用了錯誤的計算邏輯：

1. **ai/unified_reward_system.py:505**
```python
self.episode_data['robot_utilization'] = active_robots / total_robots
```

2. **evaluate.py:187**
```python
robot_utilization = active_robots / total_robots if total_robots > 0 else 0
```

3. **evaluation/performance_report_generator.py:506**
```python
kpis["avg_robot_utilization"] = max(0, min(1, total_active_time / total_robot_time if total_robot_time > 0 else 0))
```

### 為什麼會導致 100% 利用率

1. **瞬時狀態計算**：現有邏輯只計算特定時刻有多少機器人不是 'idle' 狀態
2. **狀態定義問題**：機器人一旦被分配任務，即使只是在移動途中，狀態也不是 'idle'
3. **缺乏時間維度**：沒有考慮機器人在不同狀態的時間長度
4. **混淆移動和工作**：沒有區分「有效工作時間」和「移動/等待時間」

## 數據驗證

檢查訓練結果 JSON 文件證實了這個問題：

```bash
# 搜索結果顯示大量 1.0 利用率記錄
models/training_runs/2025-07-18_*/gen*/fitness_scores.json: "robot_utilization": 1.0
```

具體例子：
- `2025-07-18_224347_nerl_step/gen001`: robot_utilization = 1.0
- `2025-07-18_224347_nerl_step/gen002`: robot_utilization = 1.0
- 幾乎所有訓練記錄都顯示 100% 利用率

## 正確的利用率定義

機器人利用率應該定義為：
```
利用率 = (機器人實際工作時間) / (總可用時間)
```

其中「實際工作時間」應該包括：
- 執行有價值任務的時間（taking_pod, delivering_pod, station_processing）
- 排除純移動和等待時間
- 基於時間累積，而非瞬時狀態

## 建議的修復方案

### 方案 1：基於狀態時間的利用率（推薦）

```python
def calculate_time_based_utilization(warehouse):
    total_active_time = 0
    total_available_time = 0
    current_tick = warehouse._tick
    
    for robot in warehouse.robot_manager.getAllRobots():
        # 使用已有的 total_active_time 屬性
        robot_work_time = robot.total_active_time
        
        # 如果當前處於活動狀態，加上當前活動時間
        if robot.current_state != 'idle' and robot.last_state_change_time > 0:
            robot_work_time += current_tick - robot.last_state_change_time
        
        total_active_time += robot_work_time
        total_available_time += current_tick
    
    return total_active_time / total_available_time if total_available_time > 0 else 0
```

### 方案 2：基於有效任務的利用率

```python
def calculate_task_based_utilization(warehouse):
    productive_states = ['taking_pod', 'delivering_pod', 'station_processing']
    active_robots = 0
    total_robots = 0
    
    for robot in warehouse.robot_manager.getAllRobots():
        total_robots += 1
        if robot.current_state in productive_states:
            active_robots += 1
    
    return active_robots / total_robots if total_robots > 0 else 0
```

### 方案 3：混合計算（最佳實踐）

```python
def calculate_hybrid_utilization(warehouse):
    time_util = calculate_time_based_utilization(warehouse)
    task_util = calculate_task_based_utilization(warehouse)
    
    # 使用加權平均：時間基礎 70%，任務基礎 30%
    return 0.7 * time_util + 0.3 * task_util
```

## 需要修改的文件

1. **ai/unified_reward_system.py** - 更新主要計算邏輯
2. **evaluate.py** - 更新評估模組中的計算
3. **evaluation/performance_report_generator.py** - 更新性能報告中的計算
4. **world/entities/robot.py** - 確保狀態時間追蹤正確（已有相關屬性）

## 預期影響

修復後，機器人利用率將：
1. **更真實**：反映實際工作效率，而非簡單的非閒置比例
2. **更有用**：可以用來識別系統瓶頸和優化機會
3. **更準確**：提供有意義的性能比較基準

## 立即驗證方法

1. 檢查現有 JSON 結果文件中的 robot_utilization 值（已證實問題存在）
2. 運行短期模擬並手動計算利用率
3. 比較修復前後的利用率計算結果

## 結論

目前的機器人利用率計算邏輯從根本上是錯誤的，導致無法提供有意義的性能指標。建議採用基於時間的混合計算方法，以獲得更準確和有用的利用率數據。
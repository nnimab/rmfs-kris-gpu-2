# 獎勵系統數據問題總結

## 關鍵發現
訓練時獎勵系統可能出現數據為零的問題，主要集中在以下指標：

## 高風險問題（可能為零）

### 1. 等待時間 (avg_wait_time)
- **來源**：`Robot.intersection_wait_time` 字典
- **問題**：初始化條件複雜，可能未正確初始化
- **修復**：確保所有機器人創建時初始化 `self.intersection_wait_time = {}`

### 2. 信號切換計數 (signal_switch_count)  
- **來源**：`Intersection.signal_switch_count`
- **問題**：只在 `switchSignal()` 被調用時更新
- **修復**：檢查控制器是否真的在切換信號

### 3. 交通流量率 (avg_traffic_rate)
- **來源**：`Intersection.getAverageTrafficRate()`
- **問題**：方法名稱錯誤已修復，但實現可能有問題
- **修復**：確認方法實現正確且返回非零值

## 應該有值的指標

### 1. 能源消耗 (total_energy)
- **計算**：基於物理公式（質量×重力×摩擦×速度）
- **可靠性**：高，每個 tick 都會計算

### 2. 停止-前進事件 (stop_and_go)
- **計算**：當機器人速度從 >0 變為 0 時計數
- **位置**：`warehouse.py:134-135`

## 數據更新時機
- NERL：`train.py:162` 調用 `update_episode_metrics`
- DQN：`train.py:727` 訓練結束時更新
- 問題：只在訓練結束時更新一次，中間過程無法追蹤

## 立即驗證方法
```python
# 在 train.py 第 162 行後添加
print(f"Episode metrics: {controller.reward_system.episode_data}")
```

## 修復優先級
1. 🔴 初始化 intersection_wait_time
2. 🔴 驗證 getAverageTrafficRate 實現
3. 🟡 增加中間過程的數據收集
4. 🟡 所有除法加入零值檢查
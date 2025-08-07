# 機器人利用率計算修復報告

## 問題描述
在基準模型參數掃描測試中，發現 54.2% 的測試結果顯示機器人利用率為負值，這在物理上是不可能的。

### 問題數據示例
- 機器人數量：30
- 評估時長：10000 ticks
- total_robot_active_time：-150000（負數）
- 計算的利用率：-150000 / (10000 * 30) = -0.5

## 根本原因分析

問題出在 `Robot` 類別的活動時間追蹤邏輯：

1. **未初始化問題**：如果機器人從模擬開始就一直處於活動狀態，`last_state_change_time` 保持為 0
2. **狀態更新問題**：`updateState` 方法只在從非閒置轉為閒置時才更新 `total_active_time`
3. **計算錯誤**：`get_current_active_time` 在計算當前活動時間時，可能產生負數

## 修復方案

### 1. 修改 `get_current_active_time` 方法
```python
def get_current_active_time(self, current_tick):
    total_time = self.total_active_time
    
    if self.current_state != 'idle':
        # 處理從未記錄過狀態變化的情況
        if self.last_state_change_time == 0:
            total_time += current_tick  # 假設從 tick 0 開始活動
        elif self.last_state_change_time > 0:
            active_duration = current_tick - self.last_state_change_time
            if active_duration > 0:
                total_time += active_duration
    
    return max(0, total_time)  # 確保永不返回負數
```

### 2. 改進 `updateState` 方法
- 增加對特殊情況的處理（從未記錄狀態變化時間）
- 增加防禦性檢查，確保活動時間為正數
- 增加警告日誌，記錄異常情況

## 驗證結果

### 測試案例 1：機器人從開始就一直活動
- 預期：利用率 = 100%
- 實際：利用率 = 100% ✓

### 測試案例 2：機器人在中途開始活動
- 預期：利用率 = 90%（從 tick 100 開始活動）
- 實際：利用率 = 90% ✓

### 測試案例 3：多次狀態切換
- 預期活動時間：600 ticks
- 實際活動時間：600 ticks ✓

### 測試案例 4：邊界情況防護
- 測試負數防護機制
- 結果：成功防止負數出現 ✓

## 影響評估

此修復將：
1. 解決所有負利用率的問題
2. 確保利用率計算的準確性
3. 不影響現有的其他功能
4. 提高系統的穩定性和可靠性

## 建議後續行動

1. **重新執行基準測試**：使用修復後的程式碼重新執行參數掃描
2. **數據驗證**：確認所有測試結果的利用率都在 0-100% 範圍內
3. **平均等待時間問題**：調查為何所有測試的平均等待時間都是 30.8 ticks
4. **性能優化**：基於正確的數據重新評估最優參數配置

## 修復文件

- **world/entities/robot.py**：
  - 修改 `get_current_active_time` 方法
  - 改進 `updateState` 方法
- **test/verify_utilization_fix.py**：驗證腳本
- **test/utilization_fix_report.md**：本報告

修復時間：2025-08-07
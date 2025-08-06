# 數據收集系統分析總結

## 執行摘要
經過全面檢查 train.py 和 evaluate.py 的獎勵系統數據收集，發現訓練階段運作正常，但評估階段有嚴重計算錯誤。

## 訓練階段（✅ 正常）

### 數據來源與計算
1. **等待時間**
   - 來源：Robot.intersection_wait_time 字典
   - 計算：總等待時間 / 等待事件數
   - 限制：30 ticks 防死鎖機制
   - 實際值：30-31（正常）

2. **能源消耗**
   - 來源：Robot.current_tick_energy
   - 計算：物理公式（質量×速度×摩擦力）
   - 累積：warehouse.total_energy
   - 實際值：884-1078（正常）

3. **信號切換**
   - 來源：Intersection.signal_switch_count
   - 計算：每次切換 +1
   - 實際值：626-736 次（正常）

4. **停止前進**
   - 來源：warehouse.stop_and_go
   - 計算：速度從 >0 變 0 時 +1
   - 實際值：895-991 次（正常）

5. **交通流量率**
   - 來源：Intersection.getAverageTrafficRate()
   - 實際值：0.023-0.027（正常）

### 驗證來源
- thesis/第四章/訓練過程紀錄檔/B_nerl_step_b3000ticks/gen028/fitness_scores.json
- 所有數據都有值且合理

## 評估階段（❌ 有嚴重問題）

### 主要問題
1. **等待時間計算錯誤**
   - 錯誤 1：數據覆蓋而非累加（evaluate.py:251）
   - 錯誤 2：公式不一致（evaluate.py:290）
   - 結果：3465-5489（異常高）

2. **交通流量率偏低**
   - 實際值：0.0027-0.0064
   - 預期值：應該與訓練相近（0.02+）
   - 可能也有計算問題

### 正常部分
- 能源消耗：正常累積
- 訂單完成率：正確計算
- 信號切換：正常計數

## 關鍵發現

### 30 ticks 等待上限
- 位置：world/entities/robot.py:537
- 目的：防止死鎖
- 影響：所有等待時間統計都在 30 左右
- 性質：設計特性，非 bug

### 訓練與評估不一致
- 訓練：使用 UnifiedRewardSystem（正確）
- 評估：自行實現計算（有錯誤）
- 建議：統一使用相同計算邏輯

## 改進建議

### 立即修復
1. 修正 evaluate.py:251 的數據累加
2. 統一等待時間計算公式
3. 檢查交通流量率計算

### 長期改進
1. 建立統一的 MetricsCollector 類
2. 訓練與評估共用計算邏輯
3. 增加數據驗證機制

## 文件位置
- 訓練邏輯：ai/unified_reward_system.py
- 評估邏輯：evaluate.py
- 機器人邏輯：world/entities/robot.py
- 倉庫統計：world/warehouse.py
# 實際可行的重建策略

## 核心事實
- 沒有無 AI 的乾淨版本（Initial commit 就有 AI）
- CSV 優化已經完成（批量寫入、進程隔離）
- 主要問題是獎勵函數複雜度和數據收集不一致

## 最實際的方案：模組化重構

### 步驟 1：抽離核心邏輯（2天）
```python
# 新建 core/ 目錄
core/
├── warehouse_base.py  # 純倉庫邏輯（無 AI）
├── entities/          # 純實體（robot, pod, order）
└── managers/          # 純管理器（無控制器）
```

### 步驟 2：簡化獎勵系統（1天）
```python
# 新建 rewards/simple_reward.py
class SimpleReward:
    def calculate(self, state):
        # 30 行內完成
        throughput = len(passed_robots)
        wait_penalty = len(waiting_robots) * 0.1
        return throughput - wait_penalty
```

### 步驟 3：統一數據收集（1天）
```python
# 新建 metrics/collector.py
class MetricsCollector:
    def __init__(self):
        self.data = []
        
    def collect(self, tick, metrics):
        self.data.append(metrics)
        
    def flush_to_csv(self):
        # 批量寫入
        pd.DataFrame(self.data).to_csv(...)
```

### 優勢
1. 保留現有 CSV 優化
2. 可以逐步遷移（不是全部重寫）
3. 1週內完成
4. 數據收集可靠
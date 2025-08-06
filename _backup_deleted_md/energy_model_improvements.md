# 能源模型改進說明

## 改進內容

### 1. 啟動成本（Startup Cost）
- **常數定義**: `STARTUP_ENERGY_COST = 0.5`
- **觸發條件**: 當機器人從完全靜止（`previous_velocity = 0`）轉為移動（`velocity > 0`）時
- **物理意義**: 模擬克服靜摩擦力和啟動電機所需的額外能量
- **實現位置**: `robot.py:113-118`

### 2. 再生制動（Regenerative Braking）
- **效率常數**: `REGENERATIVE_BRAKING_EFFICIENCY = 0.3`（回收30%的動能）
- **觸發條件**: 當機器人從移動（`previous_velocity > 0`）減速到完全停止（`velocity = 0`）時
- **物理意義**: 模擬電動機器人將動能轉換回電能的過程
- **實現位置**: `robot.py:120-128`

### 3. 改進的加速能耗計算
- **加速時**：計入慣性項（`acceleration * INERTIA`）
- **減速時**：不計入慣性項，因為能量通過再生制動部分回收

## 能耗公式總結

### 基礎能耗
```
E_base = (MASS + LOAD_MASS) × GRAVITY × FRICTION × velocity × tick_unit / 3600
```

### 加速時能耗
```
E_accel = (MASS + LOAD_MASS) × [(GRAVITY × FRICTION) + (acceleration × INERTIA)] × average_speed × tick_unit / 7200
```

### 總能耗
```
E_total = E_base + E_startup - E_regenerative
```

其中：
- `E_startup` = 0.5（當從靜止啟動時）
- `E_regenerative` = 0.5 × (MASS + LOAD_MASS) × previous_velocity² × 0.3 / 3600（當剎車到停止時）

## 對系統的影響

### 1. 啟停成本明確化
- 每次從靜止啟動都會產生固定的額外能耗
- 鼓勵AI學習減少不必要的停車

### 2. 再生制動激勵
- 減速到停止不再是純粹的能量損失
- 但仍有70%的動能無法回收，保持了啟停的成本

### 3. 更真實的物理模型
- 符合電動機器人的實際能耗特性
- 區分了加速和減速的不同能耗模式

## 參數調整建議

如果需要調整模型行為，可以修改以下參數：

1. **增加啟停懲罰**: 提高 `STARTUP_ENERGY_COST`（如改為1.0）
2. **減少再生收益**: 降低 `REGENERATIVE_BRAKING_EFFICIENCY`（如改為0.2）
3. **調整慣性影響**: 修改 `INERTIA` 係數（當前為0.4）

## 與V5.0獎勵系統的協同

這個改進的能源模型與V5.0的全局獎勵系統相輔相成：
- V5.0 通過溢出懲罰鼓勵AI避免下游擁堵
- 能源模型通過啟停成本鼓勵AI保持流暢運行
- 兩者共同引導AI學習更智能的交通控制策略
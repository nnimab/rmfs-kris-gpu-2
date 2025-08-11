# NERL 控制器重構方案（GLOBAL 適應度，資料驅動權重 + 穩定性）

## 1) 目標與原則
- 採用回合級（GLOBAL）適應度，避免 STEP shaping 複雜度，對齊交通號誌神經演化文獻（Sensors 2019 等）之回合評估習慣。
- 以「吞吐 vs 能耗」為主目標，加入「穩定性」二級指標（最大等待、Stop-and-Go、可選：利用率短缺）。
- 權重採資料驅動校正，避免憑空常數；以 `capacity_test_20250809_134140_ea463e7d` 清洗後統計作為初始校準。

## 2) 資料驅動校準（來自 無任何控制器的capacity_test 清洗後統計）
參考檔：`test/results/capacity_test_20250809_134140_ea463e7d/csv_exports/grouped_statistics.csv`
- 25 台：`completed_orders_median = 453.5`，`total_energy_median = 97732.6276`
- 30 台：`completed_orders_median = 456.0`，`total_energy_median = 112154.0690`

合併代表值（作為尺度參考）：
- 訂單代表值 O_ref = (453.5 + 456.0) / 2 = 454.75
- 能耗代表值 E_ref = (97732.6276 + 112154.0690) / 2 ≈ 104943.3483

資料驅動能耗權重（與訂單同量級）：
- 設 `w_orders = 1`，令 `w_energy = O_ref / E_ref ≈ 454.75 / 104943.3483 ≈ 0.004334`
- 解讀：在代表尺度上，`1 × O_ref ≈ 0.004334 × E_ref`，兩者貢獻同量級。

## 3) GLOBAL 適應度（回合結束一次計分）
定案：採用「加權總和」＋「穩定性正規化」的簡潔公式。

- 主公式（不需 STEP）：
  - Fitness = (CompletedOrders × w_orders) − (TotalEnergy × w_energy) − (λ_wait × MaxWaitNorm) − (λ_sg × StopGoNorm) − (λ_util × UtilShortfall)

- 初始係數（建議值）：
  - w_orders = 1.0（無單位）
  - w_energy = 0.004334（orders per energy；由 O_ref/E_ref 資料導出）
  - λ_wait = 1.0（無單位；正規化後等權）
  - λ_sg = 1.0（無單位；正規化後等權）
  - λ_util = 0.5（無單位；可選，若要更強化穩定性可調到 1.0）

- 穩定性項之定義（皆正規化到 0~1）：
  - MaxWaitNorm = min(1, MaxWaitTime / W_thr)。建議 `W_thr = 500` ticks（工程門檻；或改用數據 P95）。
  - StopGoNorm = min(1, TotalStopGo / SG_thr)。`SG_thr` 由資料建立（見 §4-2 程序）。
  - UtilShortfall = max(0, (U_ref − Utilization) / U_ref)。`U_ref` 可用 25/30 中位數的平均：
    - 由清洗後資料：25 的 `robot_utilization_median ≈ 0.9357`；30 的 `≈ 0.8257`
    - 取 `U_ref ≈ (0.9357 + 0.8257)/2 ≈ 0.8807`

備註：上述穩定性皆已無單位，等權加入即可避免「魔術數」。若老師偏好更強穩定性，可將 `λ_wait` 或 `λ_sg` 提升為 1.5–2.0 並在文中說明偏好。

## 4) 重構步驟（不立即改碼；提供實作清單）

### 4-0 備份（保留舊版）
- 複製下列檔案為 legacy 版（僅重新命名，不做內容變更）：
  - `ai/controllers/nerl_controller.py` → `ai/controllers/nerl_controller_legacy.py`
  - `ai/unified_reward_system.py` → `ai/unified_reward_system_legacy.py`
- 目的：保留現行邏輯；後續新版本可平行切換比較。

### 4-1 新增 Fitness 設定（配置檔）
- 新增 `ai/config/nerl_fitness_config.json`（或 YAML），含：
  - mode: "global"
  - weights: { w_orders: 1.0, w_energy: 0.004334, λ_wait: 1.0, λ_sg: 1.0, λ_util: 0.5 }
  - refs: { O_ref: 454.75, E_ref: 104943.3483, W_thr: 500, SG_thr: null, U_ref: 0.8807 }
- NE 訓練時讀取該檔，將 Fitness 公式集中管理，便於校準與重現。

### 4-2 數據蒐集與正規化參考量建立（Stop-and-Go 與 MaxWait）
- Stop-and-Go 蒐集（務必實作）：
  - 在機器人狀態機中，當「由停滯/等待 → 恢復移動」時記 1 次事件；累計於 `warehouse.stop_and_go`。
  - 評估端（`evaluate.py`）將 `warehouse.stop_and_go` 記入結果 JSON（例如 `total_stop_go`）。
  - 校準 `SG_thr`：以 25/30 的清洗後 run，統計 `total_stop_go` 的 P95 作為歸一化上限（或以中位數 + IQR）。
- MaxWaitTime：
  - 既有於 `UnifiedRewardSystem` 內部；評估端需將「回合最大等待」寫入結果 JSON（例如 `max_wait_time`），以便統一用於 Fitness。

### 4-3 NERL 評分路徑（GLOBAL）
- 設定 `reward_mode = global`（與現行一致）。
- 每個個體一回合結束時計算 Fitness（本方案§3 公式），用於選擇/交叉/突變。
- 不使用 STEP 訊號做學習（可保留作診斷與消融）。

### 4-4 校準與驗證流程
- 校準腳本（資料導出）：
  - 從最新實驗的清洗後資料計算：`O_ref`、`E_ref`、`U_ref`、`SG_thr`（與 `W_thr` 若走分位數法）。
  - 重寫/覆蓋 `ai/config/nerl_fitness_config.json`。
- 小樣本驗證（各 N=5、100k ticks）：
  - 25 與 30 台各跑 5 次：報告 median + 95% bootstrap CI 的 `throughput`、`energy_per_order`、`max_wait_time`、`total_stop_go`、`completion_rate`。
  - 消融：移除 `λ_sg` 或 `λ_wait` 檢查穩定性指標是否退化（應上升）。

### 4-5 訓練與最終對比
- 訓練：GLOBAL + 本 Fitness，population=20、elite≈20%（維持現設），evolution_interval=1000。
- 對比：無控制、Time（最優參數）、Queue（最優參數）、NERL（本方案）。25 與 30 台，各 N=20，100k ticks。
- 報告：median + 95% CI；對穩定性（`max_wait`、`stop_go`）特別標注。 

## 5) 風險與對策
- 尺度漂移：新資料分佈變動導致 `w_energy` 失衡 → 以清洗後中位數/IQR 定期重估，配置化管理。
- Stop-and-Go 定義差異：需明確定義「一次事件」的準則，與等待/恢復的狀態切換對齊。
- 穩定性過懲罰：若發現吞吐明顯下降，將 `λ_wait`/`λ_sg` 降為 0.5 或改採分段懲罰（僅超閾才懲罰）。

## 6) 附：數學定義彙總
- Fitness = (CompletedOrders × 1.0) − (TotalEnergy × 0.004334) − (1.0 × MaxWaitNorm) − (1.0 × StopGoNorm) − (0.5 × UtilShortfall)
- MaxWaitNorm = min(1, MaxWaitTime / 500)（或用 P95）
- StopGoNorm = min(1, TotalStopGo / SG_thr)，`SG_thr` 校準自 25/30 清洗後資料（P95）
- UtilShortfall = max(0, (0.8807 − Utilization) / 0.8807)
- 代表尺度：O_ref = 454.75、E_ref ≈ 104943.3483 → w_energy ≈ 0.004334（資料導出）

---
說明：本方案僅提供設計與配置規格，不直接修改演算法代碼；實作需依 §4 的清單進行。完成蒐集與校準後，即可以 GLOBAL 適應度進行訓練與對比實驗。

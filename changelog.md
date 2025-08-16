- 2025-08-16 AI/等待時間統計與獎勵修正
  - 調整 `ai/unified_reward_system.py`：
    - Step 獎勵等待成本依等待時長加權（以 50 ticks 為基準，封頂 4x）。
    - Global Fitness 與回合統計改用路口 `waiting_time_records` 事件累積來計算 `max_wait_time`、`avg_wait_time`、`total_wait_time`，避免快照偏誤。
    - V8 Fitness 新增 `AvgWaitNorm` 懲罰（每事件平均等待）：新增權重 `lambda_avg_wait`（預設 0.3）與門檻 `AW_thr`（預設 50 ticks）。
    - 系統指標 `_update_system_metrics` 改為事件累積口徑。
  - 調整 `evaluate.py`：
    - 評估過程以事件累積口徑收集等待事件，並在最終結果輸出 `avg_wait_time`、`max_wait_time`、`total_wait_time`。
    - 加入增量游標避免重複累加既有事件。
  - 影響：訓練與評估將以累積事件為準，等待相關指標更穩健，可減少「快照」造成的偏差，提升學習穩定性。
# Changelog

## 2025-08-11 (選單自訂功能強化)
- 新增：`test/experiment_menu.py` 支援 Time-Based 自訂「時間配比」清單（格式 A:B 且 A+B=100）。
- 新增：Time-Based 與 Queue-Based 均支援自訂「機器人數量」清單（預設 `[25, 30]`，可改為自輸入）。
- 調整：抽取 `_get_time_ratios`、擴充 `_get_robot_counts(default_list)`，介面提示與驗證一致化。

## 2025-08-11 (論文修改計畫 PLAN 2)
- 新增：制定一週衝刺計畫，將 NERL 重新定位為「穩定性與能源效率優化器」
- 計畫：Day 1-2 問題診斷與評估系統強化
- 計畫：Day 3-4 NERL 獎勵函數基於理論依據重設計
- 計畫：Day 5-6 快速訓練與迭代
- 計畫：Day 7 對比實驗與結果分析
- 文檔：更新 THESIS_REVISION_PLAN.md 加入預期結果與論文敘事策略

## 2025-06- (工作空間隔離強化)
- 新增：`NETLOGO_STATE_FILE` / `NETLOGO_STATE_DIR` 優先策略，狀態檔完全隔離（`netlogo.py`）。
- 調整：`evaluate.py` 與 `netlogo.py` 對齊狀態檔讀寫邏輯；支援 `KEEP_STATE_FILE`。
- 調整：`world/warehouse.py` 訂單與 `assign_order` 路徑尊重 `GENERATED_ORDER_FILE`、`ORDERS_DIR`、`ASSIGN_ORDER_CSV`。
- 新增：`USE_EXISTING_ORDERS=1` 可完全跳過訂單生成/合併（`warehouse_generator.py`、`order_generator.py`）。
- 調整：在 `capacity_test_controller.py`、`baseline_test_controller.py` 預設注入 `USE_EXISTING_ORDERS=1`，避免並行競態。


## 2025-08-10 (基準模型圖表生成相容性修正)
- 調整：`test/experiment_menu.py` 中「生成基準模型分析圖表」目錄掃描邏輯，支援新舊命名：
  - 新：`queue_based_*`、`time_based_*`
  - 舊：`baseline_*`、或含 `time_based/`、`queue_based/` 子資料夾，以及子目錄 `tb_*`、`qb_*`
- 修正：`Baseline` 結果根目錄改為相對於檔案的 `test/results`（`Path(__file__).parent / "results"`），避免路徑不一致導致找不到結果。
- 新增：補上 `numpy` 匯入，修正 `_show_baseline_test_summary` 中使用 `np.mean` 的依賴。

## 2025-08-10 (利用率單位校正與分析相容)
- 修正：`evaluate.py` 將輸出的 `robot_utilization` 直接乘上 `TICK_TO_SECOND`（0.15），使結果落在 0~1 範圍。
- 相容：`test/capacity_analyzer.py` 在讀舊資料時，如 `robot_utilization > 1`，自動乘上 `0.15` 進行校正；圖表/統計仍使用 `robot_utilization`。

## 2025-08-10 (圖表中文顯示修正)
- 修正：`test/capacity_analyzer.py` 的 `data_cleaning_comparison.png` 摘要文字取消 `fontfamily='monospace'`，改用全域字型設定，避免中文顯示為方塊。

## 2025-08-10 (Baseline 分析清洗與欄位校正)
- 新增：`test/baseline_analyzer.py` 支援資料清洗（預設啟用）：
  - 全域訂單生成異常（`total_orders < 0.75 × max_total_orders`）
  - 群組內異常（`robot_count×parameter`，n≥5，`completed_orders < 0.85 × trimmed-mean`）
  - 跨參數一般性能異常（完成率<70% 且 完成數低於組內中位數50%）
- 校正：
  - 讀取 evaluation 指標時補齊 `completed_orders`、`total_orders`、`energy_per_order`（若缺則 `total_energy/完成訂單`）
  - 舊資料 `robot_utilization > 1` 自動乘 0.15 矯正
- 圖表：參數比較圖在完成率面板加標註樣本數 n；所有面板使用清洗後資料。

## 2025-08-10 (選單預設值調整)
- 調整：`test/experiment_menu.py` 將預設機器人數改為 `[25, 30]`；Time-Based 與 Queue-Based 掃描的預設也一致改為 `[25, 30]`。

## 2025-08-16 (調查報告新增)
- 新增：`GPT調查報告.md`（位於專案根目錄）—彙整 NERL 控制器的現況設計（獎勵/狀態/動作、global/step 差異）與初步統一建議（僅調查，不改碼）。
## 2025-08-16 (NERL 控制器重構方案)
- 新增：`NERL控制器重構方案.md`（位於專案根目錄）—定案使用 GLOBAL 適應度；以資料驅動權重（w_orders=1、w_energy≈0.004334）結合穩定性正規化（MaxWaitNorm、StopGoNorm、UtilShortfall）之 Fitness 設計；規劃備份舊版、加入 Stop-and-Go 蒐集、配置化權重與校準流程、最終對比與消融驗證。
## 2025-08-16 (NERL 狀態/動作一致性修正)
- 修正：`TrafficStateNormalizer` 新增 `picking_queue` 特徵（上限 10.0），NERL 狀態第 17 維改為直接使用正規化值（移除再除以 10）。
- 對齊：`NEController.action_to_direction()` 與系統語意一致（0=保持、1=Vertical、2=Horizontal），避免批次下發指令方向顛倒。

## 2025-08-17 (NERL 每代輸出摘要)
- 新增：`train.py` 在 NERL 訓練流程中，於每代進化後輸出一份摘要到 `test/train_results/nerl_global_gen_XXX_*.json`，包含：
  - `generation`、`best_fitness_of_generation`、`fitness_scores`
  - 若可用則包含 `best_individual_metrics`（完成訂單、能源、等待、擁堵、溢出懲罰、訊號切換、總回饋等）
  - 目的：讓訓練輸出更集中與 `evaluate.py` 類似，便於跨流程比對

- 修正：訓練每次評估執行環境隔離一致性
  - `train.py` 的 NERL 個體評估與最終評估，現在會為每個子進程（與每次評估）指定：
    - `SIMULATION_ID` 專屬資料夾
    - `NETLOGO_STATE_DIR/NETLOGO_STATE_FILE` 專屬狀態檔
    - `ASSIGN_ORDER_CSV` 專屬 `assign_order.csv`
    - 預設 `USE_EXISTING_ORDERS=1`，避免在併行或多次評估時重建/合併訂單導致細微差異
  - 影響：在相同評估時長下，各代/各個體的 `total_orders` 不再因共享檔或重建流程而出現不一致

## 2025-08-17 (合併衝突解決)
- 修正：解決 `THESIS_REVISION_PLAN.md` 中的 Git 合併衝突
- 保留：一週衝刺計畫的完整內容，包括 Day 1-7 的詳細實施步驟
- 完成：論文修改計畫的合併，準備開始執行第一階段

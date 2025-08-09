# Changelog

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

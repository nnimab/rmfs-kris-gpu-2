# Changelog

## 2025-06- (工作空間隔離強化)
- 新增：`NETLOGO_STATE_FILE` / `NETLOGO_STATE_DIR` 優先策略，狀態檔完全隔離（`netlogo.py`）。
- 調整：`evaluate.py` 與 `netlogo.py` 對齊狀態檔讀寫邏輯；支援 `KEEP_STATE_FILE`。
- 調整：`world/warehouse.py` 訂單與 `assign_order` 路徑尊重 `GENERATED_ORDER_FILE`、`ORDERS_DIR`、`ASSIGN_ORDER_CSV`。
- 新增：`USE_EXISTING_ORDERS=1` 可完全跳過訂單生成/合併（`warehouse_generator.py`、`order_generator.py`）。
- 調整：在 `capacity_test_controller.py`、`baseline_test_controller.py` 預設注入 `USE_EXISTING_ORDERS=1`，避免並行競態。



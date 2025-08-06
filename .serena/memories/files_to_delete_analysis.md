# 檔案分類與刪除建議

## 🗑️ 建議刪除的檔案（一次性/臨時性）

### 臨時修復和補丁
- `clean_states.py` - 狀態清理工具（可以需要時再寫）
- `netlogo_state_patch.py` - 臨時修補檔
- `direct_assign_backlog.py` - 直接分配積壓訂單（測試用）
- `reassign_orders.py` - 重新分配訂單（臨時工具）
- `encoding_handler.py` - 編碼處理（臨時修復）
- `implement_decision_interval.py` - 決策間隔實現（實驗性）

### 測試和驗證腳本
- `test_visualization.py` - 視覺化測試
- `verify_energy.py` - 能源驗證（一次性驗證）
- `nerl_solution.py` - NERL 解決方案測試
- `diagnose_simulation.py` - 模擬診斷（除錯用）

### 實驗性和並行版本
- `netlogo_parallel.py` - 並行版本（實驗性）
- `evaluate_parallel.py` - 並行評估（已有主版本）
- `evaluate_simple.py` - 簡化評估（已有主版本）

### 數據分析（可移至別處）
- `thesis_data_analyzer.py` - 論文數據分析
- `validation_analyzer.py` - 驗證分析器
- `dqn_training_visualizer.py` - DQN訓練視覺化
- `generate_thesis_plots.py` - 論文圖表生成
- `aggregate_results.py` - 結果聚合

### 舊版本文件
- `visualization_generator_v2.py` - V2版本（已有主版本）

### 實驗工具中的修復檔案
- `experiment_tools/auto_parallel_fix.py` - 自動修復
- `experiment_tools/parallel_fix.py` - 並行修復
- `experiment_tools/parallel_helper.py` - 並行輔助

## ✅ 應該保留的核心檔案

### 主要執行檔案
- `train.py` - 訓練主程式
- `evaluate.py` - 評估主程式
- `netlogo.py` - NetLogo橋接
- `visualization_generator.py` - 視覺化生成

### AI系統
- `ai/` 目錄下所有檔案

### 世界模擬
- `world/` 目錄下所有檔案

### 核心函式庫
- `lib/` 目錄下所有檔案

### 實驗管理
- `experiment_tools/config_manager.py`
- `experiment_tools/simple_experiment_manager.py`
- `experiment_tools/workflow_runner.py`
- `experiment_tools/presets.py`
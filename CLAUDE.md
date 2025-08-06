# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 重要：使用 Serena MCP 工具

本專案強烈建議使用 Serena MCP 工具進行程式碼分析與編輯。Serena 提供了符號級的精確編輯和快速的程式碼搜尋功能，能大幅提升開發效率。

### Serena 核心工具使用指南

#### 1. 程式碼分析工具
- **`mcp__serena__get_symbols_overview`**：獲取檔案或目錄的頂層符號概覽，快速了解程式碼結構
- **`mcp__serena__find_symbol`**：根據符號路徑尋找特定類別、方法或變數
- **`mcp__serena__find_referencing_symbols`**：找出引用特定符號的所有位置
- **`mcp__serena__search_for_pattern`**：使用正則表達式搜尋程式碼模式

#### 2. 程式碼編輯工具
- **`mcp__serena__replace_symbol_body`**：替換整個符號的內容（如整個方法或類別）
- **`mcp__serena__insert_before_symbol`**：在符號前插入程式碼（如新增 import）
- **`mcp__serena__insert_after_symbol`**：在符號後插入程式碼（如新增方法）
- **`mcp__serena__replace_regex`**：使用正則表達式進行精確的程式碼替換

#### 3. 記憶管理工具
- **`mcp__serena__write_memory`**：儲存專案相關的重要資訊
- **`mcp__serena__read_memory`**：讀取之前儲存的專案資訊
- **`mcp__serena__list_memories`**：列出所有可用的記憶檔案

### Serena 使用最佳實踐

1. **分析前先了解結構**：使用 `get_symbols_overview` 獲取檔案概覽，避免讀取整個檔案
2. **精確編輯**：優先使用符號級編輯工具，只在需要小範圍修改時使用 regex 替換
3. **善用記憶系統**：將重要的專案資訊儲存到 Serena 記憶中，避免重複分析
4. **批量操作**：盡可能批量執行搜尋和分析操作，提升效率

## 專案概述

這是一個基於 NetLogo 和 Python 的混合式 RMFS（Robotic Mobile Fulfillment System）倉儲自動化研究專案，專注於使用神經進化強化學習（NERL）和深度Q學習（DQN）來優化倉儲中的交通控制系統。

### 核心技術架構
- **混合架構**：Python 後端邏輯 + NetLogo 前端視覺化模擬
- **AI 控制器**：4 種交通控制方法（Time-based、Queue-based、DQN、NERL）
- **強化學習**：PyTorch 實現的深度 Q 網路和神經進化算法
- **分散式控制**：邏輯分散（每個路口獨立決策）、實例集中（每個路口有自己的控制器實例）

### 開發環境注意事項
- 系統使用繁體中文作為主要開發語言（註釋、文檔、用戶交互）
- 目前在 WSL 環境下運行，終端指令執行由用戶負責
- NetLogo 需要在 Windows 環境下運行

## Claude 的 sub agent 功能 :SUB AGENTS 協調機制

### 記憶指引
- 我會給妳我的需求，請依照需求去分配任務給 sub agent 讓他來實作
- 妳負責分配任務、理解任務以及協調任務
- 主要目標是確保每個 sub agent 能夠專注於其擅長的領域，並有效協同工作

### SUB AGENTS 協調原則
- 明確任務劃分
- 清晰的溝通界面
- 彈性的工作分配
- 即時的任務追蹤和回饋

我有的sub agent: 

AI 開發團隊成員職責總覽
第一階段：專案奠基與規劃
steering-architect (專案奠基者與文檔架構師)
核心職責：分析整個專案的程式碼庫，以建立或更新指導所有 AI 行為的核心規則文件 (.ai-rules/)。他是整個團隊工作的「地基」。
使用時機：當專案剛開始、需要初始化時；或當核心的產品願景、技術棧、或專案結構需要被文件化或更新時。
主要產出：三個核心指導文件：product.md、tech.md、structure.md。
strategic-planner (功能規劃師與軟體架構師)
核心職責：與使用者合作，將模糊的功能想法，轉化為具體的規格、技術設計和一份詳細的、按部就班的開發任務清單。他是從「想法」到「藍圖」的橋樑。
使用時機：當需要規劃一個新功能；或在寫任何程式碼之前，需要進行需求分析和技術設計時。
主要產出：一個規格目錄 (specs/<feature-name>/)，內含 requirements.md (需求)、design.md (設計) 和 tasks.md (任務) 三個文件。
第二階段：執行與交付
task-executor (精密的軟體工程師)
核心職責：嚴格遵循 tasks.md 的指示，一次只執行一個、且僅一個開發任務，以外科手術般的精確度編寫或修改程式碼。他是團隊的「主力開發者」。
使用時機：當規劃階段完成，並且有一份清晰的任務清單 (tasks.md) 等待執行時。
主要產出：已修改的程式碼文件，以及更新後的 tasks.md (將完成的任務標記為 [x])。
第三階段：品質保證與維護
code-reviewer (程式碼品質守門人)
核心職責：審查由 task-executor 提交的程式碼變更，根據專案規範、程式碼風格和最佳實踐，找出潛在的品質問題、錯誤或安全隱患。它絕不修改程式碼，只提供報告。
使用時機：當一段程式碼已經完成，需要進行正式的品質審查 (Code Review) 時。
主要產出：一份結構化的程式碼審查報告 (Markdown 格式)，詳細列出問題點和改進建議。
refactor-technician (程式碼結構優化師)
核心職責：專門改善現有程式碼的內部結構、可讀性、性能和維護性，同時保證其外部功能行為完全不變。他是負責清理「技術債」的專家。
使用時機：當使用者想要清理程式碼、優化效能、或簡化複雜的程式碼邏輯時 (例如簡化 unified_reward_system.py)。
主要產出：已重構並優化的程式碼文件，並附帶所有測試通過的確認。
bug-resolver (除錯偵探)
核心職責：根據錯誤報告、失敗的測試日誌或使用者描述，診斷問題的根本原因，並應用精確的修復程式碼來解決錯誤。
使用時機：當程式出現非預期行為、測試失敗、或系統崩潰，需要進行除錯 (Debug) 時。
主要產出：已修復錯誤的程式碼文件，以及一份說明問題根源、修復方法和驗證結果的報告。
這六個 sub-agent 共同構成了一個完整的軟體開發生命週期，從專案初始化、規劃設計、編碼實現，到最終的審查、重構與除錯，各司其職，協同工作。

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 重要：使用 Serena MCP 工具

本專案強烈建議使用 Serena MCP 工具進行程式碼分析與編輯。Serena 提供了符號級的精確編輯和快速的程式碼搜尋功能，能大幅提升開發效率。

### Serena 核心工具使用指南

#### 1. 程式碼分析工具
- **`mcp__serena__get_symbols_overview`**：獲取檔案或目錄的頂層符號概覽，快速了解程式碼結構
- **`mcp__serena__find_symbol`**：根據符號路徑尋找特定類別、方法或變數
- **`mcp__serena__find_referencing_symbols`**：找出引用特定符號的所有位置
- **`mcp__serena__search_for_pattern`**：使用正則表達式搜尋程式碼模式

#### 2. 程式碼編輯工具
- **`mcp__serena__replace_symbol_body`**：替換整個符號的內容（如整個方法或類別）
- **`mcp__serena__insert_before_symbol`**：在符號前插入程式碼（如新增 import）
- **`mcp__serena__insert_after_symbol`**：在符號後插入程式碼（如新增方法）
- **`mcp__serena__replace_regex`**：使用正則表達式進行精確的程式碼替換

#### 3. 記憶管理工具
- **`mcp__serena__write_memory`**：儲存專案相關的重要資訊
- **`mcp__serena__read_memory`**：讀取之前儲存的專案資訊
- **`mcp__serena__list_memories`**：列出所有可用的記憶檔案

### Serena 使用最佳實踐

1. **分析前先了解結構**：使用 `get_symbols_overview` 獲取檔案概覽，避免讀取整個檔案
2. **精確編輯**：優先使用符號級編輯工具，只在需要小範圍修改時使用 regex 替換
3. **善用記憶系統**：將重要的專案資訊儲存到 Serena 記憶中，避免重複分析
4. **批量操作**：盡可能批量執行搜尋和分析操作，提升效率

## 專案概述

這是一個基於 NetLogo 和 Python 的混合式 RMFS（Robotic Mobile Fulfillment System）倉儲自動化研究專案，專注於使用神經進化強化學習（NERL）和深度Q學習（DQN）來優化倉儲中的交通控制系統。

### 核心技術架構
- **混合架構**：Python 後端邏輯 + NetLogo 前端視覺化模擬
- **AI 控制器**：4 種交通控制方法（Time-based、Queue-based、DQN、NERL）
- **強化學習**：PyTorch 實現的深度 Q 網路和神經進化算法
- **分散式控制**：邏輯分散（每個路口獨立決策）、實例集中（每個路口有自己的控制器實例）

### 開發環境注意事項
- 系統使用繁體中文作為主要開發語言（註釋、文檔、用戶交互）
- 目前在 WSL 環境下運行，終端指令執行由用戶負責
- NetLogo 需要在 Windows 環境下運行

## 專案結構詳細說明

### 1. AI 模組 (`ai/`)

#### 核心控制器
- **`controllers/dqn_controller.py`** (DQNController)
  - 深度 Q 學習控制器，使用經驗回放和目標網路
  - 17 維狀態輸入，6 個動作輸出（含限速控制）
  - 支援 epsilon-greedy 探索策略

- **`controllers/nerl_controller.py`** (NEController, EvolvableNetwork)
  - 神經進化控制器，使用遺傳演算法進化神經網路
  - 支援種群進化、菁英保留、錦標賽選擇
  - 動作統計追蹤，避免單一動作主導

- **`controllers/queue_based_controller.py`** (QueueBasedController)
  - 基於隊列長度的動態控制策略
  - 根據各方向等待機器人數量決定信號

- **`controllers/time_based_controller.py`** (TimeBasedController)
  - 固定時間間隔切換的基準控制器
  - 簡單但穩定，作為性能比較基準

#### 獎勵系統
- **`unified_reward_system.py`** (UnifiedRewardSystem)
  - 統一的獎勵計算系統，支援多種模式
  - V7 版本：關鍵路口權重、限速獎勵、訂單完成獎勵
  - 591 行複雜邏輯，需要簡化重構

- **`reward_helpers.py`**
  - 獎勵計算輔助函數
  - 里程碑追蹤、優先級判斷等

#### 其他支援模組
- **`deep_q_network.py`** (DeepQNetwork)
  - DQN 的神經網路實現
  - 3 層 MLP：17→128→64→6

- **`adaptive_normalizer.py`** (AdaptiveNormalizer, TrafficStateNormalizer)
  - 狀態標準化器，確保輸入在合理範圍
  - 自適應更新標準化參數

- **`traffic_controller.py`** (TrafficController, TrafficControllerFactory)
  - 控制器基礎類別和工廠模式實現

### 2. 倉儲世界模組 (`world/`)

#### 實體類別 (`entities/`)
- **`robot.py`** (Robot): 機器人實體，負責移動、取貨、送貨
- **`pod.py`** (Pod): 貨架實體，儲存物品
- **`station.py`** (Station): 工作站（揀貨台）
- **`intersection.py`** (Intersection): 路口實體，交通控制點
- **`job.py`** (Job): 任務實體，包含取貨送貨資訊
- **`order.py`** (Order): 訂單實體
- **`zone.py`** (Zone): 區域劃分
- **`area_path.py`** (AreaPath): 路徑區域

#### 管理器類別 (`managers/`)
- **`intersection_manager.py`** (IntersectionManager): 路口管理，協調交通流
- **`robot_manager.py`** (RobotManager): 機器人調度管理
- **`pod_manager.py`** (PodManager): 貨架管理
- **`order_manager.py`** (OrderManager): 訂單處理管理
- **`job_manager.py`** (JobManager): 任務分配管理
- **`station_manager.py`** (StationManager): 工作站管理
- **`zone_manager.py`** (ZoneManager): 區域管理
- **`area_path_manager.py`** (AreaPathManager): 路徑管理

#### 核心倉儲類別
- **`warehouse.py`** (Warehouse)
  - 整合所有管理器的主要倉儲類別
  - CSV I/O 優化：批量處理、進程隔離
  - 負責整體模擬循環

- **`speed_limit_manager.py`** (SpeedLimitManager)
  - V7 新增：走廊級限速管理
  - 支援水平/垂直走廊獨立控制

### 3. 介面與通訊 (`lib/`)

#### NetLogo 介面
- **`netlogo_connector.py`** (NetLogoConnector)
  - Python 與 NetLogo 的通訊橋樑
  - 使用 pyNetLogo 套件

- **`netlogo.py`**
  - NetLogo 指令包裝器
  - 提供高階操作介面

#### 資料產生器 (`generator/`)
- **`config_generator.py`**: 配置檔產生
- **`data_generator.py`**: 測試資料產生
- **`warehouse_generator.py`**: 倉儲佈局產生
- **`network_generator.py`**: 網路拓撲產生

### 4. 實驗管理工具 (`experiment_tools/`)

- **`simple_experiment_manager.py`**: 簡潔的實驗管理介面
- **`config_manager.py`**: 實驗配置管理
- **`workflow_runner.py`**: 工作流程執行器
- **`result_analyzer.py`**: 結果分析工具
- **`checkpoint_manager.py`**: 檢查點管理

### 5. 主要執行檔案

- **`train.py`**: AI 模型訓練主程式
  - 支援 DQN 和 NERL 訓練
  - 多種獎勵模式選擇
  - 訓練進度追蹤與儲存

- **`evaluate.py`**: 統一評估框架
  - 比較所有控制器性能
  - 產生評估報告

- **`simple_experiment.py`**: 簡化的實驗執行介面

- **`visualization_generator.py`**: 視覺化圖表產生

- **`check_system.py`**: 系統完整性檢查

## 常用開發命令

### 套件安裝與環境設置
```bash
# 安裝所有依賴套件
pip install -r requirements.txt
```

### AI 模型訓練
```bash
# DQN 訓練（兩種獎勵模式）
python train.py --agent dqn --reward_mode step --episodes 100 --ticks 10000
python train.py --agent dqn --reward_mode global --episodes 100 --ticks 10000

# NERL 訓練（兩種獎勵模式）
python train.py --agent nerl --reward_mode step --generations 50 --population 20 --eval_ticks 2000
python train.py --agent nerl --reward_mode global --generations 50 --population 20 --eval_ticks 2000

# 訓練時啟動 NetLogo 視覺化
python train.py --agent [nerl/dqn] --netlogo
```

### 效能評估與分析
```bash
# 評估所有控制器
python evaluate.py --ticks 20000 --seed 42

# 評估特定控制器組合
python evaluate.py --controllers time_based queue_based dqn_step dqn_global nerl_step nerl_global

# 生成視覺化圖表
python visualization_generator.py result/evaluations/EVAL_xxxxx
```

### 實驗自動化系統
```bash
# 使用簡潔版實驗管理器（推薦）
python simple_experiment.py

# 系統完整性檢查
python check_system.py
```

## 核心問題與改進方向

### 1. 獎勵函數複雜度問題
- **現況**：`unified_reward_system.py` 有 591 行，混合 V3/V6/V7 版本
- **建議**：模組化重構，分離不同版本，簡化到 50-100 行

### 2. 資料收集不一致
- **現況**：訓練和評估使用不同的資料收集機制
- **建議**：統一資料收集介面，確保訓練與驗證一致性

### 3. CSV I/O 效能
- **現況**：已實施批量寫入和進程隔離優化
- **建議**：考慮使用更高效的資料格式（如 HDF5）

### 4. 模型版本管理
- **現況**：模型檔案混雜，版本控制不清
- **建議**：建立清晰的模型版本管理系統

## 關鍵文件路徑

### 核心執行文件
- `train.py`：AI 模型訓練主程式
- `evaluate.py`：統一評估框架
- `simple_experiment.py`：簡潔實驗管理系統
- `visualization_generator.py`：圖表生成工具

### AI 控制器實現
- `ai/controllers/dqn_controller.py`：DQN 控制器
- `ai/controllers/nerl_controller.py`：NERL 控制器
- `ai/unified_reward_system.py`：統一獎勵系統（需重構）
- `ai/adaptive_normalizer.py`：狀態標準化器

### 實驗管理工具
- `experiment_tools/simple_experiment_manager.py`：簡潔實驗管理器
- `experiment_tools/config_manager.py`：配置管理
- `experiment_tools/workflow_runner.py`：工作流執行器

### 結果輸出目錄
- `result/evaluations/`：評估結果
- `result/session_summaries/`：實驗會話總結
- `models/`：訓練好的模型文件

## 開發提示

### 除錯控制
在 `world/entities/robot.py` 中設置 `DEBUG_LEVEL`：
- 0：無除錯輸出
- 1：重要訊息（訓練進度、警告）
- 2：詳細訊息（所有移動和決策細節）

### 模型命名規範
- DQN 模型：`dqn_[reward_mode]_[ticks].pth`
- NERL 模型：`nerl_[reward_mode]_[ticks].pth`

### 實驗配置預設
- **快速模式**：適合測試（1-2 小時）
- **標準模式**：平衡效能（3-4 小時）
- **論文模式**：高品質結果（6-8 小時）

## 注意事項

1. **NetLogo 依賴**：確保 `rmfs.nlogo` 文件存在且 NetLogo 環境正常
2. **模型相容性**：評估時需要對應的預訓練模型文件
3. **路徑問題**：在 WSL 環境下注意 Windows 和 Linux 路徑差異
4. **並行執行**：實驗管理系統支援多線程，注意系統資源
5. **繁體中文**：所有用戶交互、註釋和文檔保持繁體中文
6. **Serena 優先**：優先使用 Serena MCP 工具進行程式碼分析和編輯

## 版本更新記錄

### 2025/07/20 更新
- DQN 訓練數據記錄增強
- 神經網路架構增強（17→128→64→3）
- NERL 訓練參數優化
- 修復統計數據收集問題

### 2025/07/21 - V7.0 系統重大更新
- 關鍵路口權重系統
- 限速控制系統（6 動作空間）
- 走廊級限速設計
- 獎勵系統調整（V7.1）

### 2025/07/21 晚上更新
- 修復 DQN 死鎖問題
- 修復機器人直衝揀貨台 Bug
- 優化機器人數量（30→20）
- 修復 NetLogo 除錯訊息問題

## 訓練建議
```bash
# 標準訓練
python train.py --agent nerl --reward_mode step --generations 10 --population 20 --eval_ticks 3000

# 快速測試
python train.py --agent nerl --reward_mode step --generations 5 --population 10 --eval_ticks 2000
```

## 預期改進
- 動作使用多樣化（不再 100% Keep）
- 限速功能開始被學習使用
- 更穩定的訓練過程
- 更好的訂單完成率

## 開發建議

### 測試和驗證腳本管理
- 測試和驗證腳本如有需要製作以上兩樣類型的東西時 要放入/test資料夾中方便整理
### GPT 調查報告：NERL 控制器強化學習設計（現況與建議）

本報告聚焦 `ai/` 內 NERL 控制器的強化學習方法，依需求提供：
- 目前設計（獎勵/狀態/動作空間、global/step 配置）
- 在尚未參照外部文獻前的初步改造建議（含統一配置與 a/b 激進程度）

---

### 一、目前怎麼設計

- 位置與訓練流程
  - 控制器：`ai/controllers/nerl_controller.py` 的 `NEController`
  - 訓練入口：`train.py` 的 `run_nerl_training()`，支援平行個體評估（`evaluate_individual_parallel`）
  - `NEController` 以「族群 + 精英保留 + 錦標賽選擇 + 均勻交叉 + 高斯突變」演化 `EvolvableNetwork`（MLP：128→64→action_size）
  - 適應度：
    - reward_mode == "global"：使用 `UnifiedRewardSystem.calculate_global_reward()`（整回合）
    - reward_mode == "step"：累積 step 獎勵總和（`total_reward`）

- 獎勵（UnifiedRewardSystem：`ai/unified_reward_system.py`）
  - 模式：`"step"` 與 `"global"` 兩種（`set_reward_mode()` 驗證）
  - Step（V7.0 增強）：`calculate_step_reward_v7()`
    - 特點：關鍵路口加權、能源效率加成、限速控制獎勵、擁堵管理、切換懲罰、等待懲罰、10 倍放大
    - 回傳同時更新 episode 統計（`_update_episode_stats`）
  - Global（V5.1 結構化）：`calculate_global_reward()`
    - 公式要點：`完成數×completion_bonus` 作為分子；分母包含 `總能耗/scale + 總時間×time_penalty + 溢出懲罰×weight (+ ε)`；若無溢出加 `no_spillback_bonus`
    - 支援 `spillback_penalty` 跨 tick 累積（`update_spillback_penalty()`）

- 狀態空間（State）
  - `NEController.get_state()` 與 `DQNController.get_state()` 一致：17 維
    - 當前路口 8 維（方向編碼、上次切換時間、兩向機器人數、兩向平均等待、兩向高優先比例）
    - 相鄰路口 8 維（鄰接數、鄰接機器/優先者數、鄰接平均等待、鄰接方向分布、負載均衡指標）
    - 全域 1 維（揀貨台排隊長度經正規化）
  - 自適應正規化：`TrafficStateNormalizer`（`ai/adaptive_normalizer.py`）

- 動作空間（Action）
  - NERL：action_size=6（方向決策 + 限速行為）
    - 0: 保持；1/2: 切換方向；3: 限速 30%；4: 限速 50%；5: 移除限速
    - 限速由 `speed_limit_manager` 作用於路廊（`_handle_speed_action()`）
  - DQN：也建構為 action_size=6，但 `get_direction()` 僅使用 0/1/2 三個方向動作，未處理 3/4/5（行為空間不對等）

- 安全規則與穩定機制（兩控制器皆有）
  - 最小綠燈時間、急迫長等待強制放行、區域性擁堵/卍字鎖死檢測、長時間同向輪轉打破

- 配置現況（global/step 與 a/b）
  - `NEController` 建構子預設 `reward_mode="global"`，但 `train.py` 的命令列參數預設 `--reward_mode step`
  - DQN 預設 `step` 並在 `global` 時警告效果可能不佳
  - `variant`（a/b）只在 `train.py` 用於調整 NERL 的 `mutation_rate/strength`：
    - a（探索型）：0.3 / 0.2
    - b（利用型）：0.1 / 0.05

- 發現的設計不一致/風險點（需後續修復，但本次不改碼）
  - 動作到方向的對應矛盾（兩控制器皆出現）：

```524:530:ai/controllers/nerl_controller.py
        if action == 0:  # 保持當前方向
            return intersection.allowed_direction if intersection.allowed_direction else "Horizontal"
        elif action == 1:  # 垂直方向
            return "Vertical"
        else:  # action == 2, 水平方向
            return "Horizontal"
```

```543:551:ai/controllers/nerl_controller.py
        if action == 0:  # 保持
            return self.intersection_last_directions.get(intersection_id, "Horizontal")
        elif action == 1:  # 切換到水平
            self.intersection_last_directions[intersection_id] = "Horizontal"
            return "Horizontal"
        else:  # 切換到垂直 (action == 2)
            self.intersection_last_directions[intersection_id] = "Vertical"
            return "Vertical"
```

```386:392:ai/controllers/dqn_controller.py
        if action == 0:  # 保持當前方向
            return intersection.allowed_direction if intersection.allowed_direction else "Horizontal"
        elif action == 1:  # 切換到水平方向
            return "Horizontal"
        else:  # 切換到垂直方向 (action == 2)
            return "Vertical"
```

```409:414:ai/controllers/dqn_controller.py
        if action == 0:  # 保持
            return self.intersection_last_directions.get(intersection_id, "Horizontal")
        elif action == 1:  # 垂直
            self.intersection_last_directions[intersection_id] = "Vertical"
            return "Vertical"
        else:  # 水平 (action == 2)
            self.intersection_last_directions[intersection_id] = "Horizontal"
            return "Horizontal"
```

  - DQN 的 `action_size=6` 但未實作 3/4/5（限速）對應邏輯，導致輸出維度與可用行為不一致
  - NERL 預設 global、CLI 預設 step，可能造成實驗配置不一致

---

### 二、初步改造建議（未參照外部文獻前）

- 統一獎勵模式（global vs step）
  - 建議在 NERL 僅保留一種模式以簡化實驗，優先推薦：
    - 建議採用「Global-only」：
      - 與演化式一次一集的評估天然對齊，易於聚合多目標（完成率/能耗/時間/溢出）
      - 與你在 `THESIS_REVISION_PLAN.md` 的「穩定性與能源效率」定位一致
    - 替代方案「Step-only」：若要更即時地引導限速動作學習，建議簡化 step 獎勵，聚焦 3 項即可（通過獎勵、等待成本、限速/擁堵抑制獎勵），並把穩定性（如 max-wait）作為 episode 級別的度量而非單步強放大
  - 建議保留 DQN 的 step（其學習機制需要），但在跨方法對比時，明確標示不同學習范式，避免「統一一種 reward 模式跨演算法」的誤導

- 統一 a/b 的激進程度（探索/利用）
  - 用一個連續參數 `aggression_level ∈ [0,1]` 取代離散 `variant a/b`，統一可比性：
    - `mutation_rate = 0.1 + 0.2 * aggression_level`
    - `mutation_strength = 0.05 + 0.15 * aggression_level`
  - 訓練輸出與資料夾命名帶上 `agl{0-100}`，方便復現與比較（例如 `..._nerl_global_agl50`）
  - 若需跨演算法統一「激進程度」概念，對 DQN 可將 `aggression_level` 對映為 `epsilon` 初值/衰減速率，但建議先專注 NERL 端統一

- 動作空間的統一策略
  - 研究主軸是 NERL，保留其 6 動作（含限速）是其差異化價值
  - 若要與 DQN 公平對比：
    - 方案 A：擴充 DQN 至 6 動作並實作 3/4/5 的限速機制
    - 方案 B：在特定對比實驗中讓 NERL 禁用 3/4/5（只比 0/1/2），另外再提供「含限速」的獨立分析章節
  - 無論選 A/B，都要先修正兩控制器的動作→方向對應矛盾（否則資料解釋會失真）

- 狀態空間與穩定性訊號
  - 若採用 Global-only，建議維持現有 17 維設計即可；穩定性主要由 episode 指標（max_wait、spillback、stop&go）承擔
  - 若採 Step-only，考慮將「鄰接方向分布、負載不均衡」簡化，並在 step 獎勵中加入「擁堵抑制」與「切換成本」即可，避免過多訊號噪音

- 超參數與評估
  - `population_size` 10–20、`elite_ratio` 0.2、`tournament_size` 3–4 可維持
  - `evolution_interval` 應長於短暫波動期，建議 ≥ 1000 ticks（現值 1000）
  - 指標集集中於：完成率、每單能耗、max_wait、stop&go、signal_switch_count、擁堵度（均值/最大值）、動作使用分布（特別是限速）

- 實驗配置統一建議（便於重現）
  - NERL：`reward_mode=global`、`aggression_level={0.25,0.5,0.75}`、`eval_ticks≥2000`、重複 5 次
  - DQN：維持 step，單獨報告；如需公平基準，採「NERL 僅 0/1/2 動作」的對照組

- 文件與日誌
  - 建議之後將 `train.py` 預設的 `--reward_mode` 對齊到 NERL 推薦模式，避免實驗混用
  - 將 `variant` 命名換成 `aggression_level`，以數字化提升可比性

---

### 三、與你的目標的對齊（回應你的兩點）

- 只用一種配置（global vs step）：建議 NERL 統一採用 Global-only；若你更想要即時調控行為，則改採 Step-only（簡化版）
- a/b 激進程度統一：以 `aggression_level` 連續參數統一，替代 a/b，並在訓練與輸出命名中寫清數值

---

### 四、後續可執行檢查清單（不改碼版）

- 實驗層級先行：
  - 明確固定 NERL 的 reward 模式（global 或簡化 step），並在所有 run 的輸出資料夾命名體現
  - 用 `aggression_level` 取代 a/b 的敘述與試驗設計（先從記錄命名與表格開始）
- 風險提示：在正式統一前，請避免混用 `--reward_mode` 預設值與 `NEController` 預設值，否則容易跑出不同配置的結果

---

若你同意以上方向，我可以再依你之後蒐集的文獻逐項調整具體獎勵項與係數設計，並補上對應的實驗矩陣與評估表單。
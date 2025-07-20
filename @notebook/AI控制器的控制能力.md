  🧠 AI 模型能看到什麼（狀態空間 - 16維）

  當前路口狀態（8維）：

  1. 方向編碼：當前允許的通行方向（0=無，0.5=垂直，1=水平）
  2. 時間間隔：自上次信號變化以來的時間
  3. 水平隊列長度：水平方向等待的機器人數量
  4. 垂直隊列長度：垂直方向等待的機器人數量
  5. 水平優先級比例：delivering_pod 狀態的機器人佔比
  6. 垂直優先級比例：delivering_pod 狀態的機器人佔比
  7. 水平平均等待時間：水平方向機器人的平均等待時間
  8. 垂直平均等待時間：垂直方向機器人的平均等待時間

  相鄰路口狀態（8維）：

  9. 鄰居數量：相鄰路口的數量（最多4個）
  10. 鄰居總機器人數：所有相鄰路口的機器人總數
  11. 鄰居優先機器人數：相鄰路口的優先級機器人總數
  12. 鄰居優先級比例：相鄰路口的優先級機器人比例
  13. 鄰居平均等待時間：相鄰路口的平均等待時間
  14. 水平方向鄰居比例：相鄰路口中允許水平通行的比例
  15. 垂直方向鄰居比例：相鄰路口中允許垂直通行的比例
  16. 負載均衡指標：相鄰路口間的機器人分布差異

  🎮 AI 模型能做什麼（動作空間 - 3個動作）

  1. 保持當前方向（Stay）
  2. 切換到水平方向（Switch to Horizontal）
  3. 切換到垂直方向（Switch to Vertical）

  💰 獎勵機制（7個維度）(有更新了參考 AI控制器新系統獎勵及逞罰.md )

  即時獎勵（Step Reward）：

  1. 等待時間改善：+0.5 × (前後等待時間差)
  2. 方向切換懲罰：-2.0（如果切換方向）
  3. 機器人通過獎勵：+1.0 × 通過的機器人數
  4. 能源消耗懲罰：-0.1 × 能源消耗量
  5. 停止啟動懲罰：-0.5 × 停走次數
  6. 公平性獎勵：+0.5 × (基於等待時間方差)
  7. 死鎖懲罰：-5.0（如果檢測到死鎖）

  全局獎勵（Global Reward）：

  - 考慮整個評估期間的總體表現
  - 包括訂單完成率、平均等待時間、總能源消耗等

  🗺️ 機器人路徑規劃方式

  1. 路徑計算算法：

  # 使用 Dijkstra 算法（實際實現用 Bellman-Ford）
  if self.robot_manager.warehouse.zoning:
      # 有分區時，考慮區域懲罰
      node_routes = graph.dijkstraModified(start, end, penalties, zone_boundary, nodes_to_avoid)
  else:
      # 基礎路徑規劃
      node_routes = graph.dijkstra(start, end, nodes_to_avoid)

  2. 路徑權重設置：

  - 普通路徑：權重 = 1
  - 靠近站點的路徑：權重 = 3（避免擁擠）
  - 轉彎處：權重 = 5（減少轉彎）
  - 路口：權重 = 4
  - 要避開的節點：權重 + 1000

  3. 機器人狀態轉換：

  idle → taking_pod → delivering_pod → station_processing → returning_pod → idle

  4. 路徑重規劃觸發：

  - 檢測到潛在碰撞
  - 等待時間超過閾值（30 ticks）
  - 站點要求改變路徑
   💡 我的改善方案

  方案 1：擴展 AI 的觀察範圍

  # 新增全局交通流信息
  additional_state = [
      global_congestion_level,        # 全局擁塞程度
      main_corridor_load,             # 主幹道負載
      station_area_density,           # 站點區域密度
      predicted_future_congestion     # 預測未來擁塞
  ]

  方案 2：增加新的動作

  # 擴展動作空間
  actions = [
      "stay",
      "switch_horizontal",
      "switch_vertical",
      "suggest_reroute",      # 新增：建議重規劃
      "set_priority_mode",    # 新增：設置優先模式
      "adjust_timing"         # 新增：調整信號時間
  ]

  方案 3：動態路徑權重系統

  def get_dynamic_weight(edge, base_weight, tick):
      # 考慮歷史擁塞數據
      historical_congestion = get_historical_congestion(edge, tick)

      # 考慮當前實時負載
      current_load = get_current_load(edge)

      # 預測未來擁塞
      future_congestion = predict_congestion(edge, tick + 10)

      # 動態調整權重
      dynamic_weight = base_weight * (1 +
          0.3 * historical_congestion +
          0.5 * current_load +
          0.2 * future_congestion)

      return dynamic_weight

  方案 4：多路徑策略

  def plan_multiple_paths(start, end, graph):
      # 計算主路徑
      primary_path = dijkstra(start, end)

      # 計算備選路徑（避開主路徑的關鍵節點）
      avoid_nodes = get_critical_nodes(primary_path)
      secondary_path = dijkstra(start, end, avoid=avoid_nodes)

      # 計算應急路徑（考慮較長但穩定的路線）
      emergency_path = dijkstra_with_stability_priority(start, end)

      return {
          'primary': primary_path,
          'secondary': secondary_path,
          'emergency': emergency_path
      }

  方案 5：協同決策機制

  # 讓相鄰路口可以協同決策
  def collaborative_decision(intersection, neighbors):
      # 收集鄰居意圖
      neighbor_intentions = []
      for neighbor in neighbors:
          intention = neighbor.get_planned_action()
          neighbor_intentions.append(intention)

      # 協調決策避免衝突
      if will_cause_deadlock(intersection.action, neighbor_intentions):
          return find_alternative_action(intersection, neighbor_intentions)

      return intersection.action

  方案 6：預測性控制

  # 加入預測機制
  def predictive_control(intersection, horizon=10):
      # 預測未來交通流
      future_states = []
      for t in range(horizon):
          predicted_arrivals = predict_robot_arrivals(intersection, t)
          future_states.append(predicted_arrivals)

      # 基於預測優化當前決策
      optimal_action = optimize_for_future(future_states)
      return optimal_action

  這些改善方案的核心思想是：
  1. 增加信息量：讓 AI 看到更多全局信息
  2. 擴展能力：讓 AI 不只控制信號，還能影響路徑
  3. 動態適應：根據實時情況調整策略
  4. 協同合作：多個路口協調決策
  5. 預測未來：基於預測做出更好的決策

        
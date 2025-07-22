import numpy as np
from typing import Dict, List, Union, Optional
from ai.reward_helpers import get_robot_task_priority


class UnifiedRewardSystem:
    """
    統一獎勵系統
    
    為DQN和NERL提供一致的多維度獎勵計算，支持即時獎勵和全局獎勵兩種模式
    """
    
    def __init__(self, reward_mode="step", weights=None):
        """
        初始化統一獎勵系統 - V7.0 增強版本
        
        Args:
            reward_mode (str): 獎勵模式，"step"為改進的即時獎勵，"global"為全局獎勵
            weights (dict): 各維度獎勵的權重配置
        """
        self.reward_mode = reward_mode
        
        # V7.0: 定義關鍵路口（通往主幹道的入口）
        self.critical_intersections = [0, 6, 12, 18, 24, 30, 36, 42, 48, 54, 60]
        self.critical_weight = 2.0  # 降低關鍵路口權重，避免過度優化
        
        # V5.1 權重結構 - 結構性手術修復
        default_weights = {
            # Global 模式權重 - V5.1 新架構
            'completion_bonus': 200.0,             # 提高完成獎勵
            'energy_scale_factor': 100.0,          # 新增：能源縮放係數
            'time_penalty_per_tick': 0.1,
            'spillback_penalty_weight': 0.1,       # 適度的溢出懲罰權重
            'no_spillback_bonus': 5.0,             # 大幅降低無溢出獎勵（從 100.0 降到 5.0）
            'spillback_queue_threshold': 5.0,      # 降低觸發懲罰的隊列長度閾值（從 15.0 到 5.0）
            
            # Step 模式權重保持不變 (V3)
            'pass_high_priority': 1.0,
            'pass_medium_priority': 0.7,
            'pass_low_priority': 0.5,
            'wait_time_cost_high_priority': 0.05,
            'wait_time_cost_medium_priority': 0.02,
            'wait_time_cost_low_priority': 0.01,
            'switch_penalty': 0.1,
            
            # 修復：添加缺失的里程碑權重
            'milestone_delivery': 5.0,  # 護送至揀貨區里程碑獎勵
            'milestone_return': 3.0     # 釋放揀貨區里程碑獎勵
        }
        
        self.weights = default_weights
        if weights:
            self.weights.update(weights)
        
        # V5.0: 溢出懲罰累加器
        self._spillback_penalty_accumulator = 0.0
        
        # 擴展的統計數據 - 包含更多直觀指標
        self.episode_data = {
            'total_reward': 0.0,    # 累積即時獎勵
            'ticks_count': 0,       # 總時間步數
            
            # 核心業務指標
            'completed_orders': 0,
            'total_orders': 0,
            'completion_rate': 0.0,
            'avg_order_processing_time': 0.0,
            'total_completion_time': 0,
            
            # 時間效率指標
            'execution_time': 0.0,       # 實際執行時間（秒）
            'avg_wait_time': 0.0,
            'max_wait_time': 0.0,
            'total_wait_time': 0.0,
            
            # 能源效率指標
            'total_energy': 0.0,
            'energy_per_order': 0.0,
            
            # 系統性能指標
            'robot_utilization': 0.0,
            'total_stop_go': 0,
            'avg_traffic_rate': 0.0,
            'avg_intersection_congestion': 0.0,
            'max_intersection_congestion': 0.0,
            
            # 其他指標
            'spillback_penalty_total': 0.0,
            'switch_count': 0
        }
        
        # 追蹤上一次的路口方向狀態 (用於檢測切換)
        self.previous_directions = {}
        
        # V6.0: 混合式Step獎勵 - 追蹤歷史指標用於相對改善計算
        self.previous_metrics = {}  # 存儲每個路口的歷史指標
        self.warehouse = None  # 將在第一次調用時設置
        
    def reset_episode(self):
        """重置一個評估回合的統計數據"""
        self.episode_data = {
            'total_reward': 0.0,
            'ticks_count': 0,
            
            # 核心業務指標
            'completed_orders': 0,
            'total_orders': 0,
            'completion_rate': 0.0,
            'avg_order_processing_time': 0.0,
            'total_completion_time': 0,
            
            # 時間效率指標
            'execution_time': 0.0,
            'avg_wait_time': 0.0,
            'max_wait_time': 0.0,
            'total_wait_time': 0.0,
            
            # 能源效率指標
            'total_energy': 0.0,
            'energy_per_order': 0.0,
            
            # 系統性能指標
            'robot_utilization': 0.0,
            'total_stop_go': 0,
            'avg_traffic_rate': 0.0,
            'avg_intersection_congestion': 0.0,
            'max_intersection_congestion': 0.0,
            
            # 其他指標
            'spillback_penalty_total': 0.0,
            'switch_count': 0
        }
        self.previous_directions.clear()
        # V6.0: 重置歷史指標
        self.previous_metrics.clear()
        
    def reset(self):
        """重置內部狀態"""
        self._spillback_penalty_accumulator = 0.0
        
    def update_spillback_penalty(self, warehouse):
        """V5.1: 在每個tick調用此方法，以累加溢出懲罰（將用於分母計算）"""
        queue_length = warehouse.picking_station_queue_length
        threshold = self.weights['spillback_queue_threshold']
        
        # V5.1: 使用統一的懲罰計算，不再依賴 spillback_penalty_per_tick
        # 計算當前tick的懲罰基礎值（將在分母中乘以 spillback_penalty_weight）
        current_tick_penalty = max(0, queue_length - threshold)
        self._spillback_penalty_accumulator += current_tick_penalty
    
    def calculate_step_reward(self, intersection, passed_robots, waiting_robots, signal_switched) -> float:
        """
        計算基於V3.0設計的、單個路口的即時獎勵
        
        Args:
            intersection: 交叉路口對象
            passed_robots: 通過的機器人列表
            waiting_robots: 等待的機器人列表
            signal_switched: 是否發生信號切換
            
        Returns:
            float: 即時獎勵值
        """
        pass_reward = 0
        wait_time_cost = 0

        # 1. 計算通過獎勵 (R_pass)
        for robot in passed_robots:
            priority = get_robot_task_priority(robot)
            if priority == 'high':
                pass_reward += self.weights['pass_high_priority']
            elif priority == 'medium':
                pass_reward += self.weights['pass_medium_priority']
            elif priority == 'low':
                pass_reward += self.weights['pass_low_priority']

        # 2. 計算時間等待成本 (C_wait_time)
        for robot in waiting_robots:
            priority = get_robot_task_priority(robot)
            if priority == 'high':
                wait_time_cost += self.weights['wait_time_cost_high_priority']
            elif priority == 'medium':
                wait_time_cost += self.weights['wait_time_cost_medium_priority']
            elif priority == 'low':
                wait_time_cost += self.weights['wait_time_cost_low_priority']
        
        # 3. 計算切換成本 (C_switch)
        switch_cost = self.weights['switch_penalty'] if signal_switched else 0.0

        # 4. 組合並裁剪
        total_reward = pass_reward - wait_time_cost - switch_cost
        return max(-1.0, min(1.0, total_reward))  # Clip
    
    def calculate_step_reward_v7(self, intersection, passed_robots, waiting_robots, signal_switched, tick, speed_limit_active=False) -> float:
        """
        V7.0: 增強Step獎勵 - 加入關鍵路口權重、能源效率和限速控制
        
        特點：
        - 關鍵路口5倍權重
        - 能源效率獎勵
        - 限速控制獎勵
        - 擁堵管理機制
        - 10倍信號放大
        
        Args:
            intersection: 交叉路口對象
            passed_robots: 通過的機器人列表
            waiting_robots: 等待的機器人列表
            signal_switched: 是否發生信號切換
            tick: 當前時間步
            speed_limit_active: 是否啟用限速
            
        Returns:
            float: 增強獎勵值
        """
        # 1. 獲取路口權重
        intersection_weight = self.critical_weight if intersection.id in self.critical_intersections else 1.0
        
        # 2. 流通獎勵（考慮權重）
        flow_reward = 0
        energy_bonus = 0
        order_completion_bonus = 0
        
        for robot in passed_robots:
            # 基礎通過獎勵
            priority = get_robot_task_priority(robot)
            base_reward = self.weights[f'pass_{priority}_priority']
            
            # V7.1: 訂單完成獎勵 - 簡化版本
            if hasattr(robot, 'current_state') and robot.current_state == "delivering_pod":
                # 正在運送貨物的機器人給予額外獎勵
                order_completion_bonus += 2.0 * intersection_weight
            
            # 能源效率加成
            if hasattr(robot, 'velocity'):
                # 低速通過獎勵（節能）
                if robot.velocity < 2.0:  # 假設最大速度約3.0
                    energy_bonus += 0.2
            
            if hasattr(robot, 'current_tick_energy'):
                # 低能耗獎勵
                if robot.current_tick_energy < 5.0:  # 低於平均能耗
                    energy_bonus += 0.3
            
            flow_reward += base_reward * intersection_weight
        
        # 3. 等待成本（非關鍵路口減少懲罰）
        wait_cost = 0
        for robot in waiting_robots:
            priority = get_robot_task_priority(robot)
            base_cost = self.weights[f'wait_time_cost_{priority}_priority']
            # 非關鍵路口等待成本減半
            if intersection_weight == 1.0:
                base_cost *= 0.5
            wait_cost += base_cost
        
        # 4. 切換成本（關鍵路口減少懲罰）
        switch_cost = self.weights['switch_penalty'] if signal_switched else 0
        if intersection_weight > 1:
            switch_cost *= 0.5  # 關鍵路口切換懲罰減半
        
        # 5. 揀貨站擁堵管理獎勵
        congestion_bonus = 0
        if self.warehouse and hasattr(self.warehouse, 'picking_station_queue_length'):
            queue_length = self.warehouse.picking_station_queue_length
            if queue_length > 5:
                # 擁堵時獎勵讓低優先級機器人等待
                low_priority_waiting = sum(1 for r in waiting_robots 
                                         if get_robot_task_priority(r) == 'low')
                congestion_bonus = low_priority_waiting * 0.3
        
        # 6. 限速控制獎勵
        speed_control_bonus = 0
        if speed_limit_active:
            # 如果啟用限速且揀貨站擁堵，給予獎勵
            if self.warehouse and self.warehouse.picking_station_queue_length > 5:
                speed_control_bonus = 1.0
                # 額外獎勵：如果限速期間能源消耗降低
                avg_energy = sum(getattr(r, 'current_tick_energy', 0) for r in passed_robots) / max(len(passed_robots), 1)
                if avg_energy < 3.0:
                    speed_control_bonus += 0.5
        
        # 7. 總獎勵計算（降低放大倍數，避免過度波動）
        total_reward = (flow_reward + energy_bonus + order_completion_bonus + congestion_bonus + speed_control_bonus - wait_cost - switch_cost) * 5
        
        # 8. 調試輸出（每100步輸出關鍵路口）
        if tick % 100 == 0 and intersection.id in self.critical_intersections:
            print(f"[V7 Reward] Tick {tick}, Critical Intersection {intersection.id}:")
            print(f"  Flow: {flow_reward:.2f} (weight={intersection_weight}), Energy: {energy_bonus:.2f}")
            print(f"  Congestion: {congestion_bonus:.2f}, Speed Control: {speed_control_bonus:.2f}")
            print(f"  Total: {total_reward:.2f}")
        
        return total_reward
    
    def calculate_step_reward_hybrid(self, intersection, passed_robots, waiting_robots, signal_switched, tick) -> float:
        """V6.0 保留以便向後兼容"""
        # 直接調用V7版本
        return self.calculate_step_reward_v7(intersection, passed_robots, waiting_robots, signal_switched, tick, False)
    
    def calculate_global_reward(self, warehouse, episode_ticks: int) -> float:
        """
        計算全局獎勵 - V5.1 結構性手術版本
        
        V5.1 公式：
        R_global = (N_orders_completed × W_completion) / 
                   ((E_total / C_E_scale) + (T_python_ticks × W_time) + P_spillback + ε) + B_no_spillback
        
        Args:
            warehouse: 倉庫對象
            episode_ticks: 評估回合的總時間步數
            
        Returns:
            float: 全局獎勵值
        """
        if episode_ticks == 0:
            return 0.0
        
        # 1. 獲取核心KPI數據
        completed_orders = len(warehouse.order_manager.finished_orders)
        total_energy = getattr(warehouse, 'total_energy', 0)
        
        # 2. 獲取總溢出懲罰（V5.1：移入分母）
        total_spillback_penalty = self._spillback_penalty_accumulator
        
        # 3. V5.1 公式實現
        epsilon = 1e-6
        
        # 分子：完成訂單獎勵
        numerator = completed_orders * self.weights['completion_bonus']
        
        # 分母：總成本（能源 + 時間 + 溢出懲罰）
        energy_cost = total_energy / self.weights['energy_scale_factor']  # 使用縮放係數
        time_cost = episode_ticks * self.weights['time_penalty_per_tick']
        spillback_cost = total_spillback_penalty * self.weights['spillback_penalty_weight']
        
        denominator = energy_cost + time_cost + spillback_cost + epsilon
        
        # 效率得分
        efficiency_score = numerator / denominator
        
        # 4. 無溢出獎勵（V5.1 新增）
        no_spillback_bonus = 0.0
        if total_spillback_penalty == 0:
            no_spillback_bonus = self.weights['no_spillback_bonus']
        
        # 5. 最終獎勵 = 效率得分 + 無溢出獎勵
        final_reward = efficiency_score + no_spillback_bonus
        
        self.reset()  # 重置累加器
        return final_reward
    
    def _update_episode_stats(self, reward_value: float, intersection, tick: int):
        """更新評估回合的統計數據 - 簡化版本"""
        # 累積即時獎勵
        self.episode_data['total_reward'] += reward_value
        
        # 更新時間步數
        self.episode_data['ticks_count'] += 1
    
    def get_reward(self, intersection, prev_state, action, current_state, tick, warehouse, **kwargs) -> float:
        """
        根據配置的模式計算獎勵
        
        Args:
            intersection: 交叉路口對象
            prev_state: 之前的狀態
            action: 執行的動作
            current_state: 當前狀態
            tick: 當前時間刻
            warehouse: 倉庫對象
            **kwargs: 額外參數，用於全局獎勵模式
            
        Returns:
            float: 獎勵值
        """
        if self.reward_mode == "step":
            # 設置warehouse參考（第一次調用時）
            if self.warehouse is None:
                self.warehouse = warehouse
            
            # 為新的 calculate_step_reward 方法準備數據
            passed_robots = getattr(intersection, 'previous_horizontal_robots', []) + getattr(intersection, 'previous_vertical_robots', [])
            waiting_robots = list(getattr(intersection, 'horizontal_robots', {}).values()) + list(getattr(intersection, 'vertical_robots', {}).values())
            
            # 檢查是否發生信號切換
            intersection_id = id(intersection)
            current_direction = getattr(intersection, 'allowed_direction', None)
            signal_switched = False
            
            if intersection_id in self.previous_directions:
                if self.previous_directions[intersection_id] != current_direction:
                    signal_switched = True
            
            self.previous_directions[intersection_id] = current_direction
            
            # V7.0: 使用增強版獎勵系統
            # 檢查是否有限速動作（從kwargs獲取）
            speed_limit_active = kwargs.get('speed_limit_active', False)
            
            step_reward = self.calculate_step_reward_v7(intersection, passed_robots, waiting_robots, 
                                                       signal_switched, tick, speed_limit_active)
            
            # 啟動時輸出一次確認消息
            if not hasattr(self, '_v7_confirmed'):
                print(f"[V7.0] Using enhanced step reward with critical intersection weighting at tick {tick}")
                print(f"[V7.0] Critical intersections: {self.critical_intersections}")
                self._v7_confirmed = True
            
            # 更新統計數據
            self._update_episode_stats(step_reward, intersection, tick)
            
            return step_reward
        elif self.reward_mode == "global":
            # 全局模式下，每步返回 0，只在回合結束時計算全局獎勵
            
            # 仍然需要更新統計數據
            self._update_episode_stats(0.0, intersection, tick)
            
            # 檢查是否為回合結束
            episode_ticks = kwargs.get('episode_ticks', 0)
            if episode_ticks > 0:
                return self.calculate_global_reward(warehouse, episode_ticks)
            else:
                return 0.0  # 每步返回0，只在回合結束時計算全局獎勵
        else:
            raise ValueError(f"Unknown reward mode: {self.reward_mode}")
    
    def set_reward_mode(self, mode: str):
        """設置獎勵模式"""
        if mode not in ["step", "global"]:
            raise ValueError(f"Invalid reward mode: {mode}. Must be 'step' or 'global'")
        self.reward_mode = mode
    
    def get_episode_summary(self) -> Dict:
        """獲取當前評估回合的統計摘要"""
        return self.episode_data.copy()
    
    def update_episode_metrics(self, warehouse, execution_time=None):
        """更新評估回合的統計指標"""
        # 更新核心業務指標
        self.episode_data['completed_orders'] = len(warehouse.order_manager.finished_orders)
        self.episode_data['total_orders'] = len(warehouse.order_manager.orders)
        if self.episode_data['total_orders'] > 0:
            self.episode_data['completion_rate'] = self.episode_data['completed_orders'] / self.episode_data['total_orders']
        
        # 更新訂單處理時間指標
        if warehouse.order_manager.finished_orders:
            total_completion_time = 0
            valid_orders = 0
            
            for order in warehouse.order_manager.finished_orders:
                # 確保兩個值都是數字且有效
                if (order.order_complete_time != -1 and 
                    isinstance(order.order_complete_time, (int, float)) and 
                    isinstance(order.order_arrival, (int, float))):
                    completion_time = float(order.order_complete_time) - float(order.order_arrival)
                    total_completion_time += completion_time
                    valid_orders += 1
                elif order.order_complete_time != -1:
                    # 記錄問題但不中斷
                    self.logger.warning(f"Invalid order time data: complete_time={order.order_complete_time} (type={type(order.order_complete_time)}), arrival={order.order_arrival} (type={type(order.order_arrival)})")
            
            self.episode_data['total_completion_time'] = total_completion_time
            if valid_orders > 0:
                self.episode_data['avg_order_processing_time'] = total_completion_time / valid_orders
            else:
                self.episode_data['avg_order_processing_time'] = 0.0
        
        # 更新時間指標
        if execution_time is not None:
            self.episode_data['execution_time'] = execution_time
        
        # 更新能源指標
        self.episode_data['total_energy'] = warehouse.total_energy if hasattr(warehouse, 'total_energy') else 0.0
        if self.episode_data['completed_orders'] > 0:
            self.episode_data['energy_per_order'] = self.episode_data['total_energy'] / self.episode_data['completed_orders']
        
        # 更新系統性能指標
        self._update_system_metrics(warehouse)
        
        # 更新溢出懲罰總計
        self.episode_data['spillback_penalty_total'] = self._spillback_penalty_accumulator
    
    def _update_system_metrics(self, warehouse):
        """更新系統性能指標"""
        # 計算機器人利用率（基於時間的真正利用率）
        total_robots = 0
        total_utilization = 0.0
        current_tick = warehouse._tick
        total_wait_time = 0.0
        max_wait_time = 0.0
        
        for obj in warehouse.getMovableObjects():
            if obj.object_type == "robot":
                total_robots += 1
                
                # 計算累積活動時間
                accumulated_active_time = obj.total_active_time
                
                # 如果機器人目前處於非閒置狀態，加上從上次狀態變化到現在的時間
                if obj.current_state != 'idle' and obj.last_state_change_time > 0:
                    accumulated_active_time += current_tick - obj.last_state_change_time
                
                # 計算利用率（避免除零）
                if current_tick > 0:
                    robot_utilization = accumulated_active_time / current_tick
                    total_utilization += min(robot_utilization, 1.0)  # 確保不超過100%
        
        if total_robots > 0:
            self.episode_data['robot_utilization'] = total_utilization / total_robots
        else:
            self.episode_data['robot_utilization'] = 0.0
        
        # 計算交叉口等待時間和擁堵指標
        intersection_congestion = []
        all_robot_wait_times = []
        
        # 改進：遍歷所有機器人來計算等待時間
        for robot in warehouse.robot_manager.robots:
            if hasattr(robot, 'intersection_wait_time') and robot.intersection_wait_time:
                # 累加所有交叉口的等待時間
                for intersection_id, wait_time in robot.intersection_wait_time.items():
                    if wait_time > 0:
                        all_robot_wait_times.append(wait_time)
                        total_wait_time += wait_time
                        max_wait_time = max(max_wait_time, wait_time)
        
        # 計算交叉口擁堵指標
        for intersection in warehouse.intersection_manager.intersections:
            # 獲取水平方向機器人隊列
            h_robots = list(intersection.horizontal_robots.values())
            v_robots = list(intersection.vertical_robots.values())
            
            total_robots_at_intersection = len(h_robots) + len(v_robots)
            if total_robots_at_intersection > 0:
                intersection_congestion.append(total_robots_at_intersection)
        
        if intersection_congestion:
            self.episode_data['avg_intersection_congestion'] = np.mean(intersection_congestion)
            self.episode_data['max_intersection_congestion'] = max(intersection_congestion)
        
        # 更新等待時間指標
        self.episode_data['total_wait_time'] = total_wait_time
        self.episode_data['max_wait_time'] = max_wait_time
        if len(all_robot_wait_times) > 0:
            self.episode_data['avg_wait_time'] = total_wait_time / len(all_robot_wait_times)
        else:
            self.episode_data['avg_wait_time'] = 0.0
        
        # 更新停止-啟動計數（從 warehouse 獲取）
        self.episode_data['total_stop_go'] = getattr(warehouse, 'stop_and_go', 0)
        
        # 更新信號切換計數（從 intersection 物件獲取）
        total_switch_count = 0
        for intersection in warehouse.intersection_manager.intersections:
            if hasattr(intersection, 'signal_switch_count'):
                total_switch_count += intersection.signal_switch_count
        self.episode_data['signal_switch_count'] = total_switch_count
        
        # 更新平均交通流量率（從 intersection 物件獲取）
        traffic_rates = []
        for intersection in warehouse.intersection_manager.intersections:
            if hasattr(intersection, 'getAverageTrafficRate'):
                try:
                    flow_rate = intersection.getAverageTrafficRate(warehouse._tick)
                    if flow_rate > 0:
                        traffic_rates.append(flow_rate)
                except:
                    pass  # 忽略計算錯誤
        
        if traffic_rates:
            self.episode_data['avg_traffic_rate'] = sum(traffic_rates) / len(traffic_rates)
        else:
            self.episode_data['avg_traffic_rate'] = 0.0
    
    def set_weights(self, weights: Dict):
        """更新獎勵權重"""
        self.weights.update(weights)
        
    def increment_switch_count(self):
        """增加信號切換次數"""
        self.episode_data['switch_count'] += 1
    
    def increment_stop_go_count(self):
        """增加停止-啟動次數"""
        self.episode_data['total_stop_go'] += 1
    
    def _log_milestone_event(self, reward_value):
        """修復：添加缺失的里程碑事件記錄方法"""
        # 這個方法被 reward_helpers.py 中的 check_and_log_milestones 調用
        # 可以在這裡添加里程碑事件的記錄邏輯
        self.episode_data['total_reward'] += reward_value
        
        # 可選：記錄里程碑事件到日誌
        # logger.info(f"里程碑事件記錄，獎勵值: {reward_value}")
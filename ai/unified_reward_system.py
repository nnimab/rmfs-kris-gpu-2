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
        初始化統一獎勵系統 - V6.0 改進版本
        
        Args:
            reward_mode (str): 獎勵模式，"step"為改進的即時獎勵，"global"為全局獎勵
            weights (dict): 各維度獎勵的權重配置
        """
        self.reward_mode = reward_mode
        
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
    
    def calculate_step_reward_hybrid(self, intersection, passed_robots, waiting_robots, signal_switched, tick) -> float:
        """
        V6.0: 混合式Step獎勵 - 結合絕對值獎勵與相對改善獎勵
        
        公式：R_final = 0.5 * R_current + 0.5 * R_improvement
        
        其中：
        - R_current: 原有的絕對值獎勵
        - R_improvement: 相對改善獎勵 (0.4*Rw + 0.2*Ra + 0.2*Re + 0.2*Rq)
        
        Args:
            intersection: 交叉路口對象
            passed_robots: 通過的機器人列表
            waiting_robots: 等待的機器人列表
            signal_switched: 是否發生信號切換
            tick: 當前時間步
            
        Returns:
            float: 混合獎勵值
        """
        intersection_id = id(intersection)
        
        # 1. 計算現有絕對值獎勵
        R_current = self.calculate_step_reward(intersection, passed_robots, waiting_robots, signal_switched)
        
        # 2. 計算當前指標
        # 等待時間
        current_avg_wait = 0
        if waiting_robots:
            wait_times = []
            for robot in waiting_robots:
                if hasattr(robot, 'current_intersection_start_time') and robot.current_intersection_start_time is not None:
                    wait_time = tick - robot.current_intersection_start_time
                    wait_times.append(wait_time)
            current_avg_wait = sum(wait_times) / max(len(wait_times), 1) if wait_times else 0
        
        # 能源消耗（本步驟通過的機器人能源）
        current_energy = sum(getattr(r, 'current_tick_energy', 0) for r in passed_robots)
        
        # 排隊長度（從倉庫獲取）
        current_queue = 0
        if self.warehouse:
            current_queue = getattr(self.warehouse, 'picking_station_queue_length', 0)
        
        # 3. 獲取歷史數據（如果沒有，使用當前值作為基準）
        prev_data = self.previous_metrics.get(intersection_id, {
            'avg_wait': current_avg_wait,
            'energy': current_energy,
            'queue': current_queue
        })
        
        # 4. 計算相對改善獎勵
        # Rw: 等待時間改善（40%）
        Rw = 1.0 if current_avg_wait < prev_data['avg_wait'] else -1.0
        
        # Ra: 切換懲罰（20%）
        Ra = -1.0 if signal_switched else 0.0
        
        # Re: 能源效率改善（20%）
        Re = 1.0 if current_energy < prev_data['energy'] else -1.0
        
        # Rq: 排隊長度改善（20%）
        Rq = 1.0 if current_queue < prev_data['queue'] else -1.0
        
        # 相對改善總分（提高全局改善權重）
        R_improvement = 0.2 * Rw + 0.1 * Ra + 0.3 * Re + 0.4 * Rq  # 更重視排隊和能源
        
        # 5. 混合獎勵（降低原始獎勵權重）
        R_final = 0.3 * R_current + 0.7 * R_improvement  # 更重視相對改善
        
        # 6. 新增：進度獎勵（鼓勵任何正向行為）
        progress_bonus = 0.0
        if len(passed_robots) > 0:
            # 鼓勵機器人移動
            progress_bonus += 0.1 * len(passed_robots)
            
            # 特別獎勵運送任務的機器人
            delivering_count = sum(1 for r in passed_robots if getattr(r, 'current_state', '') == 'delivering_pod')
            progress_bonus += 0.2 * delivering_count
        
        R_final += progress_bonus
        
        # 6. 更新歷史記錄
        self.previous_metrics[intersection_id] = {
            'avg_wait': current_avg_wait,
            'energy': current_energy,
            'queue': current_queue
        }
        
        # V6.0: 詳細調試輸出 - 確保所有數值正確
        debug_info = {
            'intersection_id': intersection_id,
            'tick': tick,
            'R_current': R_current,
            'R_improvement': R_improvement,
            'R_final': R_final,
            'current_avg_wait': current_avg_wait,
            'current_energy': current_energy,
            'current_queue': current_queue,
            'prev_avg_wait': prev_data['avg_wait'],
            'prev_energy': prev_data['energy'],
            'prev_queue': prev_data['queue'],
            'Rw': Rw,
            'Ra': Ra,
            'Re': Re,
            'Rq': Rq,
            'signal_switched': signal_switched,
            'passed_robots_count': len(passed_robots),
            'waiting_robots_count': len(waiting_robots)
        }
        
        # 每10步輸出一次調試信息（更頻繁以便觀察）
        if tick % 10 == 0:
            print(f"[Hybrid Reward Debug] Tick {tick}, Intersection {intersection_id}: "
                  f"R_final={R_final:.3f} (Current={R_current:.3f} + Improvement={R_improvement:.3f})")
            print(f"  Metrics: wait={current_avg_wait:.1f}({prev_data['avg_wait']:.1f}), "
                  f"energy={current_energy:.1f}({prev_data['energy']:.1f}), "
                  f"queue={current_queue}({prev_data['queue']})")
            print(f"  Rewards: Rw={Rw}, Ra={Ra}, Re={Re}, Rq={Rq}, "
                  f"switch={signal_switched}, passed={len(passed_robots)}, waiting={len(waiting_robots)}")
        
        # 檢查異常值
        if abs(R_final) > 10:
            print(f"[WARNING] Abnormal reward value: {R_final:.3f} at tick {tick}")
            print(f"  Debug info: {debug_info}")
        
        # 檢查是否有NaN或inf
        if not (-10 <= R_final <= 10):
            print(f"[ERROR] Invalid reward value: {R_final} at tick {tick}")
            print(f"  Debug info: {debug_info}")
            R_final = 0.0  # 安全回復
        
        return R_final
    
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
            
            # V6.0: Step 模式現在默認使用改進的混合式獎勵
            step_reward = self.calculate_step_reward_hybrid(intersection, passed_robots, waiting_robots, signal_switched, tick)
            
            # 啟動時輸出一次確認消息
            if not hasattr(self, '_hybrid_confirmed'):
                print(f"[V6.0] Using improved hybrid step reward at tick {tick}")
                self._hybrid_confirmed = True
            
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
            total_completion_time = sum(
                order.order_complete_time - order.order_arrival 
                for order in warehouse.order_manager.finished_orders
                if order.order_complete_time != -1
            )
            self.episode_data['total_completion_time'] = total_completion_time
            self.episode_data['avg_order_processing_time'] = total_completion_time / len(warehouse.order_manager.finished_orders)
        
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
        current_tick = warehouse.current_tick
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
            if hasattr(intersection, 'calculateAverageFlow'):
                try:
                    flow_rate = intersection.calculateAverageFlow(warehouse._tick)
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
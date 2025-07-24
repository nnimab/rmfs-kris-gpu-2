from ai.traffic_controller import TrafficController
from ai.deep_q_network import DeepQNetwork
from ai.adaptive_normalizer import TrafficStateNormalizer
from ai.unified_reward_system import UnifiedRewardSystem
import numpy as np
import torch
import os
import json
from datetime import datetime
from lib.logger import get_logger

# --- GPU 優化: 步驟 6 ---
from ai.utils import get_device
# --- GPU 優化結束 ---


class DQNController(TrafficController):
    """
    基於深度強化學習的交通控制器
    
    結合了基於隊列控制器的規則邏輯與深度Q網絡的強化學習能力
    可以適應不同交通模式並優化控制決策
    """
    
    def __init__(self, min_green_time=1, bias_factor=1.5, state_size=17, action_size=6, 
                 max_wait_threshold=50, model_name=None, reward_mode="step", 
                 training_dir=None, log_file_path=None, batch_size=8192, memory_size=50000, **kwargs):
        """
        初始化DQN控制器
        
        Args:
            min_green_time (int): 最小綠燈持續時間，避免頻繁切換
            bias_factor (float): 方向偏好因子，調整水平和垂直方向的權重
            state_size (int): 狀態空間維度
            action_size (int): 動作空間維度
            max_wait_threshold (int): 機器人最大等待時間閾值，用於防鎖死
            model_name (str): 模型名稱，用於保存和加載模型
            **kwargs: 其他參數
        """
        super().__init__(controller_name="DQN控制器")
        self.logger = get_logger(log_file_path=log_file_path)
        
        # --- GPU 優化: 步驟 6 ---
        self.device = get_device()
        self.logger.info(f"DQN Controller initialized on device: {self.device}")
        # --- GPU 優化結束 ---

        self.min_green_time = min_green_time
        self.bias_factor = bias_factor
        self.state_size = state_size
        self.action_size = action_size
        self.max_wait_threshold = max_wait_threshold
        # 根據 reward_mode 設定預設 model_name
        if model_name is None:
            self.model_name = f"dqn_{reward_mode}"
        else:
            self.model_name = model_name
        
        # --- GPU 優化: 步驟 5 (批次大小) ---
        self.batch_size = batch_size
        # --- GPU 優化結束 ---
        
        # 訓練目錄路徑
        self.training_dir = training_dir
        
        # 定義任務優先級權重 (從隊列控制器繼承)
        self.priority_weights = {
            "delivering_pod": 3.0,  # 送pod去撿貨站 (最高優先級)
            "returning_pod": 2.0,   # 將pod送回倉庫 (次高優先級)
            "taking_pod": 1.0,      # 空車機器人去倉庫拿pod (一般優先級)
            "idle": 0.5,            # 閒置狀態 (最低優先級)
            "station_processing": 0.0  # 在站台處理中的機器人不需要考慮
        }
        
        # 初始化深度Q網絡
        self.dqn = DeepQNetwork(
            state_size=state_size, 
            action_size=action_size, 
            device=self.device,
            model_name=self.model_name,  # 使用包含 reward_mode 的 model_name
            memory_size=memory_size,
            batch_size=self.batch_size,
            reward_mode=reward_mode
        )
        
        # 初始化自適應正規化器
        self.normalizer = TrafficStateNormalizer(window_size=1000)
        
        # 初始化統一獎勵系統
        self.reward_system = UnifiedRewardSystem(reward_mode=reward_mode)
        self.logger.info(f"DQNController initialized with reward_mode: {reward_mode} (V6.0 改進版)")
        
        # 如果使用全局獎勵模式，給出警告
        if reward_mode == "global":
            self.logger.warning("WARNING: DQN typically requires immediate rewards for effective learning. "
                              "Global reward mode may result in poor performance.")
        
        # 用於存儲每個交叉路口的先前狀態和動作
        self.previous_states = {}
        self.previous_actions = {}
        
        # 是否處於訓練模式
        self.is_training = True

        # 用於追蹤每個交叉口的最後方向，以便實現"保持"動作
        self.intersection_last_directions = {}
        
        # 訓練數據記錄
        self.training_history = {
            'steps': [],  # 每步的數據
            'episodes': [],  # 每個 episode 的總結
            'checkpoints': []  # 定期檢查點
        }
        self.current_episode_data = {
            'steps': 0,
            'total_reward': 0.0,
            'losses': [],
            'q_values': [],
            'actions': []
        }
        self.last_checkpoint_tick = 0
    
    def get_state(self, intersection, tick, warehouse):
        """
        獲取交叉路口的當前狀態向量（16維，包含相鄰路口信息）
        
        Args:
            intersection: 交叉路口對象
            tick: 當前時間刻
            warehouse: 倉庫對象
            
        Returns:
            numpy.ndarray: 表示當前狀態的16維向量
        """
        # 1. 當前路口基礎信息（8維）
        
        # 當前允許方向編碼
        dir_code = 0
        if intersection.allowed_direction == "Vertical":
            dir_code = 1
        elif intersection.allowed_direction == "Horizontal":
            dir_code = 2
        
        # 自上次信號變化以來的時間
        time_since_change = intersection.durationSinceLastChange(tick)
        
        # 各方向機器人數量
        h_count = len(intersection.horizontal_robots)
        v_count = len(intersection.vertical_robots)
        
        # 優先級機器人數量 (delivering_pod 狀態)
        h_priority = len([robot for robot in intersection.horizontal_robots.values() 
                          if robot.current_state == "delivering_pod"])
        v_priority = len([robot for robot in intersection.vertical_robots.values() 
                          if robot.current_state == "delivering_pod"])
        
        # 計算平均等待時間
        h_wait_time, v_wait_time = intersection.calculateAverageWaitingTimePerDirection(tick)
        
        # 2. 相鄰路口信息（8維）
        neighbors = warehouse.intersection_manager.get_neighboring_intersections(intersection)
        
        # 相鄰路口的平均等待時間
        neighbor_avg_wait = 0.0
        if neighbors['count'] > 0:
            total_wait = 0.0
            for neighbor in neighbors['intersections']:
                n_h_wait, n_v_wait = neighbor.calculateAverageWaitingTimePerDirection(tick)
                total_wait += (n_h_wait + n_v_wait) / 2.0
            neighbor_avg_wait = total_wait / neighbors['count']
        
        # V5.0: 獲取全局揀貨台排隊長度
        # warehouse 已經作為參數傳入
        picking_queue_length = warehouse.picking_station_queue_length if hasattr(warehouse, 'picking_station_queue_length') else 0
        
        # 原始特徵值（用於統計更新）
        raw_features = {
            'time_since_change': time_since_change,
            'h_count': h_count,
            'v_count': v_count,
            'h_wait_time': h_wait_time,
            'v_wait_time': v_wait_time,
            'neighbor_robots': neighbors['total_robots'],
            'neighbor_priority': neighbors['total_priority_robots'],
            'neighbor_wait': neighbor_avg_wait,
            'picking_queue': picking_queue_length  # V5.0: 新增揀貨台排隊特徵
        }
        
        # 更新正規化器的統計數據
        self.normalizer.update_statistics(raw_features)
        
        # 使用自適應正規化
        normalized = self.normalizer.normalize_features(raw_features)
        
        # V5.0: 揀貨台容量常數（用於歸一化）
        MAX_PICKING_QUEUE_CAPACITY = 10.0
        
        # 構建17維狀態向量（V5.0：新增第17維）
        state = [
            # 當前路口狀態（8維）
            dir_code / 2.0,  # 歸一化到[0,1]
            normalized['time_since_change'],
            normalized['h_count'],
            normalized['v_count'],
            h_priority / max(h_count, 1),  # 優先機器人比例
            v_priority / max(v_count, 1),
            normalized['h_wait_time'],
            normalized['v_wait_time'],
            
            # 相鄰路口狀態（8維）
            neighbors['count'] / 4.0,  # 相鄰路口數量（最多4個）
            normalized['neighbor_robots'],
            normalized['neighbor_priority'],
            neighbors['total_priority_robots'] / max(neighbors['total_robots'], 1),  # 相鄰路口優先級比例
            normalized['neighbor_wait'],
            # 擴展特徵：相鄰路口的方向分佈
            len([n for n in neighbors['intersections'] if n.allowed_direction == "Horizontal"]) / max(neighbors['count'], 1),
            len([n for n in neighbors['intersections'] if n.allowed_direction == "Vertical"]) / max(neighbors['count'], 1),
            # 相鄰路口的負載均衡指標
            (max([len(n.horizontal_robots) + len(n.vertical_robots) for n in neighbors['intersections']] + [0]) - 
             min([len(n.horizontal_robots) + len(n.vertical_robots) for n in neighbors['intersections']] + [0])) / max(neighbors['total_robots'], 1),
            
            # V5.0: 全局揀貨台排隊特徵（第17維）
            normalized['picking_queue'] / MAX_PICKING_QUEUE_CAPACITY
        ]
        
        return np.array(state)
    
    def get_direction(self, intersection, tick, warehouse):
        """
        根據當前狀態決定交通方向
        
        結合防鎖死機制、最小綠燈時間約束和DQN決策
        
        Args:
            intersection: 交叉路口對象
            tick: 當前時間刻
            warehouse: 倉庫對象
            
        Returns:
            str: 允許通行的方向 "Horizontal" 或 "Vertical"
        """
        intersection_id = intersection.id
        
        # 防鎖死機制檢查 - 計算每個方向的最大等待時間
        max_wait_time_h = 0
        max_wait_time_v = 0
        
        for robot in intersection.horizontal_robots.values():
            if robot.current_intersection_start_time is not None:
                wait_time = tick - robot.current_intersection_start_time
                max_wait_time_h = max(max_wait_time_h, wait_time)
        
        for robot in intersection.vertical_robots.values():
            if robot.current_intersection_start_time is not None:
                wait_time = tick - robot.current_intersection_start_time
                max_wait_time_v = max(max_wait_time_v, wait_time)
        
        # === 新增：多層防鎖死機制 ===
        
        # 1. 緊急防鎖死：任一方向等待時間過長
        emergency_threshold = self.max_wait_threshold
        if max_wait_time_h > emergency_threshold:
            self.logger.warning(f"Intersection {intersection.id}: EMERGENCY - Horizontal wait time {max_wait_time_h} > {emergency_threshold}")
            if self.is_training:
                state = self.get_state(intersection, tick, warehouse)
                self.previous_states[intersection_id] = state
                self.previous_actions[intersection_id] = 2
            return "Horizontal"
        
        if max_wait_time_v > emergency_threshold:
            self.logger.warning(f"Intersection {intersection.id}: EMERGENCY - Vertical wait time {max_wait_time_v} > {emergency_threshold}")
            if self.is_training:
                state = self.get_state(intersection, tick, warehouse)
                self.previous_states[intersection_id] = state
                self.previous_actions[intersection_id] = 1
            return "Vertical"
        
        # 2. 卍字鎖死檢測：四個方向都有機器人且等待時間較長
        deadlock_threshold = self.max_wait_threshold * 0.6  # 30 ticks
        h_robots = len(intersection.horizontal_robots)
        v_robots = len(intersection.vertical_robots)
        
        if (h_robots > 0 and v_robots > 0 and 
            max_wait_time_h > deadlock_threshold and max_wait_time_v > deadlock_threshold):
            
            # 檢查鄰近交叉口是否也有擁堵
            neighboring_congestion = self._check_neighboring_congestion(intersection, warehouse)
            
            if neighboring_congestion:
                self.logger.warning(f"Intersection {intersection.id}: DEADLOCK DETECTED - Using priority break strategy")
                # 優先讓delivery任務通行
                h_priority = sum(1 for robot in intersection.horizontal_robots.values() 
                               if robot.current_state == "delivering_pod")
                v_priority = sum(1 for robot in intersection.vertical_robots.values() 
                               if robot.current_state == "delivering_pod")
                
                if h_priority > v_priority:
                    direction = "Horizontal"
                    action_code = 2
                elif v_priority > h_priority:
                    direction = "Vertical"
                    action_code = 1
                else:
                    # 如果優先級相同，選擇等待時間更長的方向
                    direction = "Horizontal" if max_wait_time_h > max_wait_time_v else "Vertical"
                    action_code = 2 if direction == "Horizontal" else 1
                
                if self.is_training:
                    state = self.get_state(intersection, tick, warehouse)
                    self.previous_states[intersection_id] = state
                    self.previous_actions[intersection_id] = action_code
                
                return direction
        
        # 3. 輪轉防鎖死：長時間保持同一方向
        direction_hold_time = intersection.durationSinceLastChange(tick)
        max_hold_time = self.max_wait_threshold * 1.5  # 75 ticks
        
        if (direction_hold_time > max_hold_time and 
            intersection.allowed_direction is not None):
            
            # 強制切換到另一個方向（如果該方向有機器人）
            opposite_direction = "Vertical" if intersection.allowed_direction == "Horizontal" else "Horizontal"
            
            if ((opposite_direction == "Horizontal" and h_robots > 0) or
                (opposite_direction == "Vertical" and v_robots > 0)):
                
                self.logger.warning(f"Intersection {intersection.id}: ROTATION BREAK - Switching to {opposite_direction} after {direction_hold_time} ticks")
                
                if self.is_training:
                    state = self.get_state(intersection, tick, warehouse)
                    self.previous_states[intersection_id] = state
                    self.previous_actions[intersection_id] = 2 if opposite_direction == "Horizontal" else 1
                
                return opposite_direction
        
        # === 原有邏輯繼續 ===
        
        # 檢查最小綠燈時間，避免頻繁切換
        if intersection.allowed_direction is not None and \
           intersection.durationSinceLastChange(tick) < self.min_green_time:
            # 即使保持當前方向，也記錄狀態用於學習
            if self.is_training:
                state = self.get_state(intersection, tick, warehouse)
                self.previous_states[intersection_id] = state
                # 設置動作為保持當前方向
                self.previous_actions[intersection_id] = 0  # 保持當前方向的動作編碼
            return intersection.allowed_direction
        
        # 如果兩個方向都沒有機器人，保持當前狀態
        if len(intersection.horizontal_robots) == 0 and len(intersection.vertical_robots) == 0:
            # 沒有機器人的情況，不適合用於訓練，不記錄狀態
            return intersection.allowed_direction
        
        # 如果一個方向沒有機器人，另一個方向有，則選擇有機器人的方向
        if len(intersection.horizontal_robots) == 0:
            # 記錄狀態和動作，因為這是有意義的決策
            if self.is_training:
                state = self.get_state(intersection, tick, warehouse)
                self.previous_states[intersection_id] = state
                self.previous_actions[intersection_id] = 1  # 垂直方向的動作編碼
            return "Vertical"
        if len(intersection.vertical_robots) == 0:
            # 記錄狀態和動作，因為這是有意義的決策
            if self.is_training:
                state = self.get_state(intersection, tick, warehouse)
                self.previous_states[intersection_id] = state
                self.previous_actions[intersection_id] = 2  # 水平方向的動作編碼
            return "Horizontal"
        
        # 使用DQN選擇動作
        state = self.get_state(intersection, tick, warehouse)
        
        # 保存當前狀態用於後續學習
        if self.is_training:
            self.previous_states[intersection_id] = state
            
            action = self.dqn.act(state)
            self.previous_actions[intersection_id] = action
        else:
            # 推理模式 - 只選擇最佳動作，不保存狀態
            self.dqn.epsilon = 0.0  # 在推理模式下關閉探索
            action = self.dqn.act(state)
        
        # 將動作轉換為方向
        if action == 0:  # 保持當前方向
            return intersection.allowed_direction if intersection.allowed_direction else "Horizontal"
        elif action == 1:  # 切換到水平方向
            return "Horizontal"
        else:  # 切換到垂直方向 (action == 2)
            return "Vertical"

    def action_to_direction(self, action, intersection_id):
        """
        將動作編碼轉換為方向字符串。

        Args:
            action (int): 動作編碼 (0, 1, or 2)。
            intersection_id (int): 交叉口的ID。

        Returns:
            str: "Horizontal" 或 "Vertical"。
        """
        if action == 0:  # 保持
            # 如果我們有記錄這個交叉口的最後方向，就使用它
            # 否則，默認為水平方向
            return self.intersection_last_directions.get(intersection_id, "Horizontal")
        elif action == 1:  # 垂直
            self.intersection_last_directions[intersection_id] = "Vertical"
            return "Vertical"
        else:  # 水平 (action == 2)
            self.intersection_last_directions[intersection_id] = "Horizontal"
            return "Horizontal"
    
    def _check_neighboring_congestion(self, intersection, warehouse):
        """
        檢查鄰近交叉口的擁堵情況
        
        Args:
            intersection: 當前交叉口
            warehouse: 倉庫對象
            
        Returns:
            bool: 是否存在鄰近擁堵
        """
        congested_neighbors = 0
        total_neighbors = 0
        
        # 檢查上下左右相鄰的交叉口
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]  # 上、下、右、左
        
        for dx, dy in directions:
            neighbor_x = intersection.pos_x + dx
            neighbor_y = intersection.pos_y + dy
            
            neighbor = warehouse.intersection_manager.getIntersectionByCoordinate(neighbor_x, neighbor_y)
            if neighbor is not None:
                total_neighbors += 1
                
                # 檢查鄰近交叉口是否擁堵
                neighbor_h_robots = len(neighbor.horizontal_robots)
                neighbor_v_robots = len(neighbor.vertical_robots)
                
                if neighbor_h_robots > 2 or neighbor_v_robots > 2:  # 擁堵閾值
                    congested_neighbors += 1
        
        # 如果超過一半的鄰近交叉口都擁堵，認為存在區域性擁堵
        return total_neighbors > 0 and (congested_neighbors / total_neighbors) > 0.5
    
    def get_reward(self, intersection, prev_state, action, current_state, tick, warehouse):
        """
        使用統一獎勵系統計算獎勵值
        
        Args:
            intersection: 交叉路口對象
            prev_state: 之前的狀態
            action: 執行的動作
            current_state: 當前狀態
            tick: 當前時間刻
            warehouse: 倉庫對象
            
        Returns:
            float: 獎勵值
        """
        return self.reward_system.get_reward(
            intersection=intersection,
            prev_state=prev_state,
            action=action,
            current_state=current_state,
            tick=tick,
            warehouse=warehouse
        )
    
    def train(self, intersection, tick, warehouse):
        """
        訓練DQN模型
        
        Args:
            intersection: 交叉路口對象
            tick: 當前時間刻
            warehouse: 倉庫對象
        """
        intersection_id = intersection.id
        
        # 只有在有先前狀態時才進行訓練
        if intersection_id not in self.previous_states or intersection_id not in self.previous_actions:
            # 添加診斷日誌，每100個tick記錄一次
            if tick % 100 == 0:
                missing_states = intersection_id not in self.previous_states
                missing_actions = intersection_id not in self.previous_actions
                self.logger.debug(f"Intersection {intersection_id} - Missing states: {missing_states}, Missing actions: {missing_actions}")
            return
        
        prev_state = self.previous_states[intersection_id]
        prev_action = self.previous_actions[intersection_id]
        
        # 獲取當前狀態
        current_state = self.get_state(intersection, tick, warehouse)
        
        # 計算獎勵
        reward = self.get_reward(intersection, prev_state, prev_action, current_state, tick, warehouse)
        
        # 判斷是否為結束狀態 (如果沒有機器人，或是定期重置)
        done = (len(intersection.horizontal_robots) == 0 and len(intersection.vertical_robots) == 0) or (tick % 1000 == 0)
        
        # 存儲經驗
        self.dqn.remember(prev_state, prev_action, reward, current_state, done)
        
        # 記錄訓練數據
        self.current_episode_data['total_reward'] += reward
        self.current_episode_data['steps'] += 1
        self.current_episode_data['actions'].append(prev_action)
        
        # 清除先前狀態
        if done:
            del self.previous_states[intersection_id]
            del self.previous_actions[intersection_id]
        else:
            # 更新先前狀態
            self.previous_states[intersection_id] = current_state
        
        # 每32個tick進行一次批次訓練（更頻繁的訓練以充分利用GPU）
        if tick % 32 == 0:
            if len(self.dqn.memory) >= self.batch_size:
                metrics = self.dqn.replay()
                if metrics:
                    self.current_episode_data['losses'].append(metrics['loss'])
                    self.current_episode_data['q_values'].append(metrics['avg_q_value'])
                self.logger.debug(f"DQN replay performed with batch_size {self.batch_size}, memory size: {len(self.dqn.memory)}")
            else:
                self.logger.debug(f"Insufficient memory for DQN replay, current size: {len(self.dqn.memory)}/{self.batch_size}")
        
        # 每500個tick回報epsilon值和保存檢查點
        if tick % 500 == 0:
            self.logger.debug(f"Current epsilon: {self.dqn.epsilon:.4f}")
            self.save_training_checkpoint(tick, warehouse)
        
        # 每1000個tick更新目標網絡和保存 episode 總結
        if tick % 1000 == 0:
            self.dqn.update_target_model()
            self.logger.debug(f"Target network updated")
            self.save_episode_summary(tick, warehouse)
            
        # 每5000個tick保存模型
        if tick % 5000 == 0 and tick > 0:
            self.dqn.save_model(tick=tick)
    
    def set_training_mode(self, is_training):
        """
        設置是否處於訓練模式
        
        Args:
            is_training (bool): 是否處於訓練模式
        """
        self.is_training = is_training
        if not is_training:
            self.dqn.epsilon = 0.0  # 關閉探索
        
    def load_model(self, model_path=None, tick=None):
        """
        加載預訓練模型
        
        Args:
            model_path (str, optional): 模型路徑
            tick (int, optional): 特定時間點的模型
            
        Returns:
            bool: 是否成功加載模型
        """
        if tick is not None:
            model_path = f"models/{self.model_name}_{tick}.pth"
        
        return self.dqn.load_model(model_path)
    
    def set_reward_mode(self, mode: str):
        """
        設置獎勵模式
        
        Args:
            mode (str): 獎勵模式，"step"為即時獎勵，"global"為全局獎勵
        """
        self.reward_system.set_reward_mode(mode)
    
    def save_model(self, tick=None, is_final=False):
        """
        保存模型
        
        Args:
            tick (int, optional): 當前時間節點
            is_final (bool): 是否為最終模型
        """
        if self.dqn:
            self.dqn.save_model(model_name=self.model_name, tick=tick, is_final=is_final)
    
    def process_episode_end(self, warehouse, episode_ticks):
        """
        處理 episode 結束（僅用於 global 模式）
        
        計算全局獎勵並將其分配給 episode 中的所有轉換
        
        Args:
            warehouse: 倉庫對象
            episode_ticks: episode 的總時間步數
        """
        if self.reward_system.reward_mode != "global":
            return
            
        # 計算全局獎勵
        global_reward = self.reward_system.calculate_global_reward(warehouse, episode_ticks)
        
        # 將全局獎勵分配給 episode buffer 中的所有轉換
        self.dqn.process_episode_end(global_reward)
        
        self.logger.info(f"Episode ended with global reward: {global_reward:.4f}")
    
    def save_metadata(self, start_time, end_time, config, final_results):
        """
        保存訓練元資料
        
        Args:
            start_time (str): 訓練開始時間
            end_time (str): 訓練結束時間
            config (dict): 訓練配置
            final_results (dict): 最終結果
        """
        if not self.training_dir:
            return
            
        metadata_file = os.path.join(self.training_dir, "metadata.json")
        try:
            metadata = {
                "controller_type": "dqn",
                "reward_mode": self.reward_system.reward_mode,
                "start_time": start_time,
                "end_time": end_time,
                "config": config,
                "results": final_results
            }
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2)
            self.logger.info(f"Training metadata saved: {metadata_file}")
        except Exception as e:
            self.logger.error(f"Error saving metadata: {e}")
        
    def reset_episode_stats(self):
        """重置評估回合統計數據"""
        self.reward_system.reset_episode()
        
    def get_episode_summary(self):
        """獲取評估回合統計摘要"""
        return self.reward_system.get_episode_summary()
    
    def save_training_checkpoint(self, tick, warehouse):
        """
        保存訓練檢查點數據
        
        Args:
            tick: 當前時間步
            warehouse: 倉庫對象
        """
        if not self.training_dir or not self.is_training:
            return
            
        # 只在間隔時間保存
        if tick - self.last_checkpoint_tick < 500:
            return
            
        self.last_checkpoint_tick = tick
        
        # 計算當前統計
        completed_orders = len([j for j in warehouse.job_manager.jobs if j.is_finished])
        total_orders = len(warehouse.job_manager.jobs)
        
        checkpoint_data = {
            'tick': tick,
            'epsilon': self.dqn.epsilon,
            'memory_size': len(self.dqn.memory),
            'episode_reward': self.current_episode_data['total_reward'],
            'episode_steps': self.current_episode_data['steps'],
            'avg_loss': np.mean(self.current_episode_data['losses']) if self.current_episode_data['losses'] else 0.0,
            'avg_q_value': np.mean(self.current_episode_data['q_values']) if self.current_episode_data['q_values'] else 0.0,
            'completed_orders': completed_orders,
            'total_orders': total_orders,
            'completion_rate': completed_orders / total_orders if total_orders > 0 else 0.0
        }
        
        self.training_history['checkpoints'].append(checkpoint_data)
        
        # 定期保存到文件
        if len(self.training_history['checkpoints']) % 10 == 0:
            self.save_training_history()
    
    def save_episode_summary(self, tick, warehouse):
        """
        保存 episode 總結
        
        Args:
            tick: 當前時間步
            warehouse: 倉庫對象
        """
        if not self.training_dir or not self.is_training:
            return
            
        # 獲取系統指標
        episode_summary = self.reward_system.get_episode_summary()
        
        episode_data = {
            'end_tick': tick,
            'total_reward': self.current_episode_data['total_reward'],
            'steps': self.current_episode_data['steps'],
            'avg_loss': np.mean(self.current_episode_data['losses']) if self.current_episode_data['losses'] else 0.0,
            'avg_q_value': np.mean(self.current_episode_data['q_values']) if self.current_episode_data['q_values'] else 0.0,
            'action_distribution': dict(zip(*np.unique(self.current_episode_data['actions'], return_counts=True))) if self.current_episode_data['actions'] else {},
            'system_metrics': episode_summary
        }
        
        self.training_history['episodes'].append(episode_data)
        
        # 重置 episode 數據
        self.current_episode_data = {
            'steps': 0,
            'total_reward': 0.0,
            'losses': [],
            'q_values': [],
            'actions': []
        }
        
        # 保存到文件
        self.save_training_history()
    
    def save_training_history(self):
        """保存訓練歷史到文件"""
        if not self.training_dir:
            return
            
        history_file = os.path.join(self.training_dir, "training_history.json")
        try:
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(self.training_history, f, indent=2)
            self.logger.debug(f"Training history saved: {history_file}")
        except Exception as e:
            self.logger.error(f"Error saving training history: {e}")

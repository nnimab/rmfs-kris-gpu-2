from ai.traffic_controller import TrafficController
from ai.adaptive_normalizer import TrafficStateNormalizer
from ai.unified_reward_system import UnifiedRewardSystem
import torch
import torch.nn as nn
import numpy as np
import random
import os
import copy
from multiprocessing import Pool
import time
import json
import logging
from lib.logger import get_logger

# --- GPU 優化: 步驟 4 ---
from ai.utils import get_device
# --- GPU 優化結束 ---


# 使用與DQN相同的QNetwork架構，但用於進化算法而非梯度下降
class EvolvableNetwork(nn.Module):
    """可進化的神經網絡模型 - 統一架構版本"""
    
    def __init__(self, state_size, action_size, device):
        """
        初始化可進化網絡
        
        Args:
            state_size (int): 狀態空間維度
            action_size (int): 動作空間維度
            device: 計算設備 (CPU or GPU)
        """
        super(EvolvableNetwork, self).__init__()
        self.device = device
        
        # 增強版架構 - 更強的表達能力
        self.layers = nn.Sequential(
            nn.Linear(state_size, 128),
            nn.ReLU(),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, action_size)
        )
        self.to(self.device)

    def forward(self, x):
        """
        前向傳播
        
        Args:
            x (Tensor): 輸入狀態張量
            
        Returns:
            Tensor: 策略輸出張量
        """
        return self.layers(x)
    
    def get_weights_as_vector(self):
        """
        將神經網絡權重提取為一維向量
        
        Returns:
            numpy.ndarray: 包含所有權重的一維數組
        """
        weights = []
        for param in self.parameters():
            weights.append(param.data.view(-1).cpu().numpy())
        return np.concatenate(weights)
    
    def set_weights_from_vector(self, weight_vector):
        """
        從一維向量設置神經網絡權重
        
        Args:
            weight_vector (numpy.ndarray): 包含所有權重的一維數組
        """
        start = 0
        for param in self.parameters():
            param_size = param.numel()
            param.data = torch.tensor(
                weight_vector[start:start+param_size],
                dtype=param.dtype,
                device=self.device # 確保張量在正確的設備上
            ).view_as(param.data)
            start += param_size


class NEController(TrafficController):
    """
    基於神經進化的交通控制器
    
    使用進化算法而非梯度下降來訓練神經網絡策略
    """
    
    def __init__(self, min_green_time=1, bias_factor=1.5, state_size=17, action_size=3, 
                 max_wait_threshold=50, model_name=None, 
                 population_size=20, elite_ratio=0.2, elite_size=None, tournament_size=4,
                 crossover_rate=0.8, mutation_rate=0.2, mutation_strength=0.15,  # 提高探索性
                 evolution_interval=1000, reward_mode="global", training_dir=None, log_file_path=None, **kwargs):
        """
        初始化NERL控制器
        
        Args:
            min_green_time (int): 最小綠燈時間
            bias_factor (float): 偏向因子
            state_size (int): 狀態空間大小
            action_size (int): 動作空間大小
            max_wait_threshold (int): 最大等待時間閾值
            model_name (str): 模型名稱
            population_size (int): 族群大小 (降低到20以提高訓練速度)
            elite_ratio (float): 精英保留比例 (預設0.2 = 20%)
            tournament_size (int): 錦標賽選擇大小
            crossover_rate (float): 交叉機率
            mutation_rate (float): 突變機率
            mutation_strength (float): 突變強度
            evolution_interval (int): 進化間隔 (修正：從100改為1000)
        """
        super().__init__(controller_name="NERL控制器")
        # --- 【修改點 2：在呼叫 get_logger 時傳入 log_file_path】 ---
        # 設置 NERL 控制器的日誌級別為 DEBUG，確保所有訊息都能顯示
        self.logger = get_logger(name="NERL-Controller", level=logging.DEBUG, log_file_path=log_file_path)
        # 添加調試訊息確認 log_file_path 是否正確傳遞
        print(f"DEBUG: NEController initialized with log_file_path: {log_file_path}")
        # --- 【修改結束】 ---
        
        # 基礎屬性
        self.min_green_time = min_green_time
        self.bias_factor = bias_factor
        
        # --- GPU 優化: 步驟 4 ---
        self.device = get_device()
        # --- GPU 優化結束 ---
        
        # NERL特有參數
        self.state_size = state_size
        self.action_size = action_size
        self.max_wait_threshold = max_wait_threshold
        # 根據 reward_mode 設定預設 model_name
        if model_name is None:
            self.model_name = f"nerl_{reward_mode}"
        else:
            self.model_name = model_name
        
        # 訓練目錄路徑
        self.training_dir = training_dir
        self.training_start_time = None
        
        # 進化算法參數 - 修正關鍵參數
        self.population_size = population_size  # 減少族群大小
        self.elite_ratio = elite_ratio          # 精英保留比例
        
        # 向後兼容：如果提供了 elite_size，使用它；否則使用 elite_ratio
        if elite_size is not None:
            self.elite_size = max(1, min(elite_size, population_size))
        else:
            self.elite_size = max(1, int(population_size * elite_ratio))  # 計算實際精英數量
        self.tournament_size = tournament_size
        self.crossover_rate = crossover_rate
        self.mutation_rate = mutation_rate
        self.mutation_strength = mutation_strength
        self.evolution_interval = evolution_interval  # 關鍵修正：增加評估時間
        
        self.logger.info(f"NERL Controller initialized with evolution_interval={evolution_interval}")
        self.logger.info(f"Population size: {self.population_size}, Elite size: {self.elite_size} ({self.elite_size/self.population_size*100:.1f}%)")
        print(f"NERL Controller initialized with evolution_interval={evolution_interval}")  # 強制輸出
        print(f"Population size: {self.population_size}, Elite size: {self.elite_size} ({self.elite_size/self.population_size*100:.1f}%)")  # 強制輸出
        
        # 初始化自適應正規化器
        self.normalizer = TrafficStateNormalizer(window_size=1000)
        
        # 初始化統一獎勵系統
        self.reward_system = UnifiedRewardSystem(reward_mode=reward_mode)
        self.logger.info(f"NEController initialized with reward_mode: {reward_mode} (V6.0 改進版)")
        print(f"NEController initialized with reward_mode: {reward_mode} (V6.0 改進版)")  # 強制輸出
        
        # 初始化族群
        self.population = self._initialize_population()
        self.fitness_scores = [0.0] * self.population_size
        
        # 當前個體索引和最佳個體
        self.current_individual_idx = 0
        self.best_individual = None
        self.best_fitness = float('-inf')
        
        # 歷史記錄
        self.fitness_history = []
        self.generation_count = 0
        
        # 狀態追蹤
        self.previous_states = {}
        self.previous_actions = {}
        
        # 評估計數器
        self.steps_since_evolution = 0
        self.evaluation_episodes = {}  # 用於跟踪每個個體的評估數據
        
        # 新增的參數，用於追蹤評估狀態
        self.consecutive_no_evaluation = 0  # 連續沒有評估的次數
        self.individual_eval_time = 0  # 當前個體的評估時間
        
        # 是否處於訓練模式
        self.is_training = True
        
        self.active_individual = None

        # 用於追蹤每個交叉口的最後方向，以便實現"保持"動作
        self.intersection_last_directions = {}
        
        # 不要在初始化時自動載入模型！訓練時需要隨機初始化
        # self.load_model()  # 移除這行，只有在評估時才需要載入
    
    def _initialize_population(self):
        """
        初始化族群
        
        Returns:
            list: 包含population_size個神經網絡的列表
        """
        population = []
        for _ in range(self.population_size):
            network = EvolvableNetwork(self.state_size, self.action_size, self.device)
            # 使用Xavier初始化權重
            for param in network.parameters():
                if len(param.shape) > 1:
                    nn.init.xavier_uniform_(param)
            population.append(network)
        return population
    
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
        # 與DQN控制器使用完全相同的狀態表示
        
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
        
        Args:
            intersection: 交叉路口對象
            tick: 當前時間刻
            warehouse: 倉庫對象
            
        Returns:
            str: 允許通行的方向 "Horizontal" 或 "Vertical"
        """
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
        
        # === 增強防鎖死機制 ===
        
        # 1. 緊急防鎖死：任一方向等待時間過長
        emergency_threshold = self.max_wait_threshold
        if max_wait_time_h > emergency_threshold:
            self.logger.warning(f"Intersection {intersection.id}: NERL EMERGENCY - Horizontal wait time {max_wait_time_h} > {emergency_threshold}")
            return "Horizontal"
        
        if max_wait_time_v > emergency_threshold:
            self.logger.warning(f"Intersection {intersection.id}: NERL EMERGENCY - Vertical wait time {max_wait_time_v} > {emergency_threshold}")
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
                self.logger.warning(f"Intersection {intersection.id}: NERL DEADLOCK DETECTED - Using priority break strategy")
                # 優先讓delivery任務通行
                h_priority = sum(1 for robot in intersection.horizontal_robots.values() 
                               if robot.current_state == "delivering_pod")
                v_priority = sum(1 for robot in intersection.vertical_robots.values() 
                               if robot.current_state == "delivering_pod")
                
                if h_priority > v_priority:
                    return "Horizontal"
                elif v_priority > h_priority:
                    return "Vertical"
                else:
                    # 如果優先級相同，選擇等待時間更長的方向
                    return "Horizontal" if max_wait_time_h > max_wait_time_v else "Vertical"
        
        # 3. 輪轉防鎖死：長時間保持同一方向
        direction_hold_time = intersection.durationSinceLastChange(tick)
        max_hold_time = self.max_wait_threshold * 1.5  # 75 ticks
        
        if (direction_hold_time > max_hold_time and 
            intersection.allowed_direction is not None):
            
            # 強制切換到另一個方向（如果該方向有機器人）
            opposite_direction = "Vertical" if intersection.allowed_direction == "Horizontal" else "Horizontal"
            
            if ((opposite_direction == "Horizontal" and h_robots > 0) or
                (opposite_direction == "Vertical" and v_robots > 0)):
                
                self.logger.warning(f"Intersection {intersection.id}: NERL ROTATION BREAK - Switching to {opposite_direction} after {direction_hold_time} ticks")
                return opposite_direction
        
        # === 原有NERL邏輯繼續 ===
        
        # 檢查最小綠燈時間，避免頻繁切換
        if intersection.allowed_direction is not None and \
           intersection.durationSinceLastChange(tick) < self.min_green_time:
            return intersection.allowed_direction
        
        # 如果兩個方向都沒有機器人，保持當前狀態
        if len(intersection.horizontal_robots) == 0 and len(intersection.vertical_robots) == 0:
            return intersection.allowed_direction
        
        # 如果一個方向沒有機器人，另一個方向有，則選擇有機器人的方向
        if len(intersection.horizontal_robots) == 0:
            return "Vertical"
        if len(intersection.vertical_robots) == 0:
            return "Horizontal"
        
        # 使用當前評估的神經網絡選擇動作
        state = self.get_state(intersection, tick, warehouse)
        
        # 保存當前狀態用於後續學習
        intersection_id = intersection.id
        self.previous_states[intersection_id] = state
        
        # 選擇當前使用的神經網絡
        if self.active_individual is not None:
            # 如果有設置活躍個體（評估模式），使用它
            network = self.active_individual
        elif self.is_training:
            network = self.population[self.current_individual_idx]
        else:
            network = self.best_individual if self.best_individual is not None else self.population[0]
        
        # 使用網絡預測動作
        state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)
        network.eval()  # 切換到評估模式，解決 BatchNorm1d 在單樣本時的問題
        with torch.no_grad():
            q_values = network(state_tensor)
            action = torch.argmax(q_values).item()
        
        self.previous_actions[intersection_id] = action
        
        # 將動作轉換為方向
        if action == 0:  # 保持當前方向
            return intersection.allowed_direction if intersection.allowed_direction else "Horizontal"
        elif action == 1:  # 垂直方向
            return "Vertical"
        else:  # 水平方向
            return "Horizontal"

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
        elif action == 1:  # 切換到水平
            self.intersection_last_directions[intersection_id] = "Horizontal"
            return "Horizontal"
        else:  # 切換到垂直 (action == 2)
            self.intersection_last_directions[intersection_id] = "Vertical"
            return "Vertical"
    
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
    
    def set_active_individual(self, network):
        """設置當前用於決策的個體網絡。"""
        self.active_individual = network.to(self.device)

    def get_actions_for_states(self, states):
        """
        為一批狀態決定動作。

        Args:
            states (dict): {intersection_id: state_vector} 的字典。

        Returns:
            dict: {intersection_id: action} 的字典。
        """
        actions = {}
        if not self.active_individual:
            # 如果沒有激活的個體，返回空動作或默認動作
            return actions

        for intersection_id, state_list in states.items():
            state_tensor = torch.FloatTensor(state_list).unsqueeze(0).to(self.device)
            with torch.no_grad():
                q_values = self.active_individual(state_tensor)
                action = torch.argmax(q_values).item()
            actions[intersection_id] = action
        return actions

    def evolve_with_fitness(self, fitness_scores, episode_summaries=None, generation=None):
        """
        使用外部傳入的適應度分數列表來執行一代進化。

        Args:
            fitness_scores (list): 包含所有個體適應度分數的列表。
            episode_summaries (list, optional): 包含所有個體評估摘要的列表。
            generation (int, optional): 當前代數，用於保存每代資訊

        Returns:
            float: 這一代中的最佳適應度分數。
        """
        self.fitness_scores = fitness_scores

        # 找出並更新全局最佳個體
        current_best_idx = np.argmax(self.fitness_scores)
        current_best_fitness = self.fitness_scores[current_best_idx]
        
        # 獲取最佳個體的統計摘要
        best_episode_summary = None
        if episode_summaries and current_best_idx < len(episode_summaries):
            best_episode_summary = episode_summaries[current_best_idx]
        
        # 保存當代最佳個體和適應度資訊
        if generation is not None and self.training_dir:
            self.save_generation_best(generation, current_best_idx, current_best_fitness, fitness_scores, best_episode_summary)

        if current_best_fitness > self.best_fitness:
            self.best_fitness = current_best_fitness
            self.best_individual = copy.deepcopy(self.population[current_best_idx])
            self.logger.info(f"New global best individual found with fitness: {self.best_fitness:.4f}")
            # 立刻保存更優的模型
            self.save_model()

        # 創建新一代
        new_population = self._create_new_generation()
        self.population = new_population

        # 重置內部狀態，為下一代做準備
        self.fitness_scores = [0.0] * self.population_size
        self.generation_count += 1
        
        return self.best_fitness 

    def _tournament_selection(self, k=3):
        """
        錦標賽選擇
        
        Args:
            k (int): 錦標賽大小
            
        Returns:
            int: 選中的個體索引
        """
        # 隨機選擇k個個體
        selected_indices = np.random.choice(self.population_size, size=k, replace=False)
        # 返回適應度最高的
        return selected_indices[np.argmax([self.fitness_scores[i] for i in selected_indices])]
    
    def _crossover(self, parent1, parent2):
        """
        均勻交叉兩個父代個體
        
        Args:
            parent1: 第一個父代個體
            parent2: 第二個父代個體
            
        Returns:
            EvolvableNetwork: 子代個體
        """
        child = EvolvableNetwork(self.state_size, self.action_size, self.device)
        
        # 獲取父代權重
        p1_weights = parent1.get_weights_as_vector()
        p2_weights = parent2.get_weights_as_vector()
        
        # 均勻交叉
        mask = np.random.random(p1_weights.shape) < 0.5
        child_weights = np.where(mask, p1_weights, p2_weights)
        
        # 設置子代權重
        child.set_weights_from_vector(child_weights)
        
        return child
    
    def _mutate(self, individual):
        """
        高斯變異
        
        Args:
            individual: 要變異的個體
            
        Returns:
            EvolvableNetwork: 變異後的個體
        """
        # 獲取權重
        weights = individual.get_weights_as_vector()
        
        # 生成變異遮罩 (選擇哪些權重進行變異)
        mutation_mask = np.random.random(weights.shape) < self.mutation_rate
        
        # 生成高斯噪聲
        noise = np.random.normal(0, self.mutation_strength, weights.shape)
        
        # 應用變異
        weights = weights + mutation_mask * noise
        
        # 設置變異後的權重
        individual.set_weights_from_vector(weights)
        
        return individual
    
    def _create_new_generation(self):
        """
        創建新一代族群
        
        Returns:
            list: 新族群
        """
        new_population = []
        
        # 精英保留 - 直接複製最佳個體
        # 確保精英數量不超過族群大小
        actual_elite_size = min(self.elite_size, len(self.population))
        elite_indices = np.argsort(self.fitness_scores)[-actual_elite_size:]
        for idx in elite_indices:
            new_population.append(copy.deepcopy(self.population[idx]))
        
        # 填充剩餘族群
        while len(new_population) < self.population_size:
            # 決定是否進行交叉
            if random.random() < self.crossover_rate and len(new_population) + 1 < self.population_size:
                # 交叉
                parent1_idx = self._tournament_selection(self.tournament_size)
                parent2_idx = self._tournament_selection(self.tournament_size)
                
                child1 = self._crossover(self.population[parent1_idx], self.population[parent2_idx])
                child2 = self._crossover(self.population[parent2_idx], self.population[parent1_idx])
                
                # 變異
                child1 = self._mutate(child1)
                child2 = self._mutate(child2)
                
                new_population.append(child1)
                if len(new_population) < self.population_size:
                    new_population.append(child2)
            else:
                # 只複製和變異
                parent_idx = self._tournament_selection(self.tournament_size)
                child = copy.deepcopy(self.population[parent_idx])
                child = self._mutate(child)
                new_population.append(child)
        
        return new_population
    
    def save_generation_best(self, generation, best_idx, best_fitness, fitness_scores, episode_summary=None):
        """
        保存當代最佳個體和適應度資訊
        
        Args:
            generation (int): 當前代數
            best_idx (int): 最佳個體索引
            best_fitness (float): 最佳適應度
            fitness_scores (list): 所有個體的適應度分數
            episode_summary (dict, optional): 最佳個體的詳細統計信息
        """
        if not self.training_dir:
            return
            
        # 創建代數目錄
        gen_dir = os.path.join(self.training_dir, f"gen{generation:03d}")
        os.makedirs(gen_dir, exist_ok=True)
        
        # 保存最佳個體模型
        best_model_path = os.path.join(gen_dir, f"best_idx{best_idx:03d}_fit{best_fitness:.2f}.pth")
        try:
            torch.save(self.population[best_idx].state_dict(), best_model_path)
            self.logger.info(f"Generation {generation} best model saved: {best_model_path}")
        except Exception as e:
            self.logger.error(f"Error saving generation best model: {e}")
        
        # 保存適應度分數和詳細統計信息
        fitness_file = os.path.join(gen_dir, "fitness_scores.json")
        try:
            with open(fitness_file, 'w', encoding='utf-8') as f:
                # 轉換 numpy 類型為 Python 原生類型
                fitness_data = {
                    "generation": int(generation),
                    "best_idx": int(best_idx),
                    "best_fitness": float(best_fitness),
                    "all_fitness": [float(score) for score in fitness_scores]
                }
                
                # 如果有詳細統計信息，也保存它
                if episode_summary:
                    fitness_data["best_individual_metrics"] = {
                        # 核心業務指標
                        "completed_orders": episode_summary.get('completed_orders', 0),
                        "total_orders": episode_summary.get('total_orders', 0),
                        "completion_rate": episode_summary.get('completion_rate', 0.0),
                        "avg_order_processing_time": episode_summary.get('avg_order_processing_time', 0.0),
                        "total_completion_time": episode_summary.get('total_completion_time', 0),
                        
                        # 時間效率指標
                        "execution_time_seconds": episode_summary.get('execution_time', 0.0),
                        "avg_wait_time": episode_summary.get('avg_wait_time', 0.0),
                        "max_wait_time": episode_summary.get('max_wait_time', 0.0),
                        "total_wait_time": episode_summary.get('total_wait_time', 0.0),
                        "evaluation_ticks": episode_summary.get('ticks_count', 0),
                        
                        # 能源效率指標
                        "total_energy_consumed": episode_summary.get('total_energy', 0.0),
                        "energy_per_order": episode_summary.get('energy_per_order', 0.0),
                        
                        # 系統性能指標
                        "robot_utilization": episode_summary.get('robot_utilization', 0.0),
                        "total_stop_go_events": episode_summary.get('total_stop_go', 0),
                        "avg_traffic_rate": episode_summary.get('avg_traffic_rate', 0.0),
                        "avg_intersection_congestion": episode_summary.get('avg_intersection_congestion', 0.0),
                        "max_intersection_congestion": episode_summary.get('max_intersection_congestion', 0.0),
                        
                        # 其他指標
                        "spillback_penalty_total": episode_summary.get('spillback_penalty_total', 0.0),
                        "signal_switch_count": episode_summary.get('signal_switch_count', 0),
                        "total_reward": episode_summary.get('total_reward', 0.0)
                    }
                
                json.dump(fitness_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"Error saving fitness scores: {e}")
    
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
                "controller_type": "nerl",
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

    def save_model(self, model_name=None, tick=None, is_final=False):
        """
        保存最佳模型
        
        Args:
            model_name (str, optional): 模型名稱，默認為None使用self.model_name
            tick (int, optional): 當前時間節點，用於標識保存的模型版本
            is_final (bool): 是否為最終模型
        """
        if self.best_individual is None:
            self.logger.warning("No best individual to save yet")
            return
            
        # 確定保存路徑
        if is_final:
            # 保存到 final_models 目錄
            os.makedirs("models/final_models", exist_ok=True)
            save_path = f"models/final_models/{self.model_name}_best.pth"
        else:
            # 保存到訓練目錄（如果有指定）
            if self.training_dir:
                save_path = os.path.join(self.training_dir, f"best_model.pth")
            else:
                # 向後相容：保存到原始位置
                os.makedirs("models", exist_ok=True)
                save_name = model_name if model_name else self.model_name
                if tick is not None:
                    save_name = f"{save_name}_{tick}"
                save_path = f"models/{save_name}.pth"
        
        try:
            torch.save(self.best_individual.state_dict(), save_path)
            self.logger.info(f"NERL model saved: {save_path}")
        except Exception as e:
            self.logger.error(f"Error saving NERL model: {e}")
    
    def set_training_mode(self, is_training):
        """
        設置是否處於訓練模式
        
        Args:
            is_training (bool): 是否處於訓練模式
        """
        self.is_training = is_training
        # NERL 在非訓練模式下總是使用最佳個體進行決策
        if not is_training and self.best_individual is not None:
            self.active_individual = self.best_individual.to(self.device)
            self.logger.info("NERL: Switched to evaluation mode, using best individual")
        else:
            self.logger.info(f"NERL: Training mode set to {is_training}")

    def load_model(self, model_path=None, tick=None):
        """
        加載已保存的模型
        
        Args:
            model_path (str, optional): 完整模型路徑，如果未提供則使用默認模型
            tick (int, optional): 時間刻，用於加載特定時間點的模型
            
        Returns:
            bool: 是否成功加載模型
        """
        if not model_path:
            model_path = f"models/{self.model_name}.pth"
            if tick is not None:
                model_path = f"models/{self.model_name}_{tick}.pth"
                
        if os.path.isfile(model_path):
            try:
                # 加載最佳個體
                network = EvolvableNetwork(self.state_size, self.action_size, self.device)
                network.load_state_dict(torch.load(model_path, map_location=self.device))
                self.best_individual = network
                self.logger.info(f"NERL model loaded: {model_path}")
                return True
            except Exception as e:
                self.logger.error(f"Error loading NERL model: {e}")
                return False
        else:
            self.logger.warning(f"NERL model file not found: {model_path}")
            return False
    
    def set_reward_mode(self, mode: str):
        """
        設置獎勵模式
        
        Args:
            mode (str): 獎勵模式，"step"為即時獎勵，"global"為全局獎勵
        """
        self.reward_system.set_reward_mode(mode)
        
    def reset_episode_stats(self):
        """重置評估回合統計數據"""
        self.reward_system.reset_episode()
        
    def get_episode_summary(self):
        """獲取評估回合統計摘要"""
        return self.reward_system.get_episode_summary()
        
    def calculate_individual_fitness(self, warehouse, episode_ticks: int) -> float:
        """
        計算個體的適應度分數
        
        Args:
            warehouse: 倉庫對象
            episode_ticks: 評估回合的總時間步數
            
        Returns:
            float: 適應度分數
        """
        if self.reward_system.reward_mode == "global":
            return self.reward_system.calculate_global_reward(warehouse, episode_ticks)
        else:
            # 即時獎勵模式下，使用累積獎勵作為適應度
            summary = self.reward_system.get_episode_summary()
            total_reward = summary.get('total_reward', 0.0)
                
            # 添加調試信息
            self.logger.info(f"Individual fitness calculation - total_reward: {total_reward}, "
                           f"passed_robots: {summary.get('total_passed_robots', 0)}, "
                           f"avg_wait: {summary.get('total_wait_time', 0) / max(summary.get('ticks_count', 1), 1):.2f}")
                
            return total_reward
    
    def train(self, intersection, tick, warehouse):
        """
        收集獎勵數據用於評估（不執行實際的神經網絡訓練）
        
        這個方法與DQN的train方法類似，但NERL使用進化算法而非梯度下降，
        所以這裡只收集獎勵數據，實際的網絡更新在進化過程中進行。
        
        Args:
            intersection: 交叉路口對象
            tick: 當前時間刻
            warehouse: 倉庫對象
        """
        intersection_id = intersection.id
        
        # 只有在有先前狀態時才計算獎勵
        if intersection_id not in self.previous_states or intersection_id not in self.previous_actions:
            return
        
        prev_state = self.previous_states[intersection_id]
        prev_action = self.previous_actions[intersection_id]
        
        # 獲取當前狀態
        current_state = self.get_state(intersection, tick, warehouse)
        
        # 計算獎勵（統一獎勵系統會自動累積）
        reward = self.get_reward(intersection, prev_state, prev_action, current_state, tick, warehouse)
        
        # 判斷是否為結束狀態
        done = (len(intersection.horizontal_robots) == 0 and len(intersection.vertical_robots) == 0) or (tick % 1000 == 0)
        
        # 清除或更新先前狀態
        if done:
            del self.previous_states[intersection_id]
            del self.previous_actions[intersection_id]
        else:
            self.previous_states[intersection_id] = current_state
    
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
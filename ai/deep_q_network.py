import os
import random
from collections import deque
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from lib.logger import get_logger

class DeepQNetwork:
    """深度Q學習網絡管理器"""
    
    def __init__(self, state_size, action_size, device, model_name=None, learning_rate=5e-4, gamma=0.95, 
                 epsilon=1.0, epsilon_min=0.01, epsilon_decay=0.999, memory_size=100000, batch_size=8192, reward_mode="step"):
        """
        初始化深度Q網絡
        
        Args:
            state_size (int): 狀態空間維度
            action_size (int): 動作空間維度
            device (torch.device): 計算設備 (CPU or GPU)
            model_name (str): 模型名稱，用於保存和加載
            learning_rate (float): 學習率
            gamma (float): 折扣因子
            epsilon (float): 初始探索率
            epsilon_min (float): 最小探索率
            epsilon_decay (float): epsilon 的衰減率
            memory_size (int): 記憶庫大小
            batch_size (int): 訓練時的批次大小
        """
        self.state_size = state_size
        self.action_size = action_size
        
        # 如果未提供 device，則預設為 CPU
        if device is None:
            self.device = torch.device("cpu")
        else:
            self.device = device
        
        self.memory = deque(maxlen=memory_size)
        self.gamma = gamma
        self.epsilon = epsilon
        self.epsilon_min = epsilon_min
        self.epsilon_decay = epsilon_decay
        self.learning_rate = learning_rate
        self.batch_size = batch_size # 新增
        self.model_name = "dqn_model" if model_name is None else model_name
        self.logger = get_logger()
        self.reward_mode = reward_mode
        
        # Global 模式專用：儲存單個 episode 的所有轉換
        self.episode_buffer = []
        
        # 初始化策略網絡和目標網絡
        self.policy_net = self._build_model().to(self.device) # 將模型移至GPU
        self.target_net = self._build_model().to(self.device) # 將模型移至GPU
        self.update_target_model()
        
        # Adam 優化器
        self.optimizer = optim.Adam(self.policy_net.parameters(), lr=self.learning_rate)
        
        # 均方誤差損失函數
        self.criterion = nn.MSELoss()
    
    def _build_model(self):
        """
        構建Q網絡模型 - 統一架構版本
        
        Returns:
            nn.Module: Q網絡模型
        """
        # 簡化的統一架構 (V-Final)
        model = nn.Sequential(
            nn.Linear(self.state_size, 64),
            nn.ReLU(),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Linear(32, self.action_size)
        )
        return model
    
    def update_target_model(self):
        """更新目標網絡權重為主網絡權重"""
        self.target_net.load_state_dict(self.policy_net.state_dict())
    
    def remember(self, state, action, reward, next_state, done):
        """
        將經驗存入記憶庫
        
        Args:
            state: 當前狀態
            action: 執行的動作
            reward: 獲得的獎勵
            next_state: 下一狀態
            done: 是否結束
        """
        if self.reward_mode == "global":
            # Global 模式：先存入 episode buffer
            self.episode_buffer.append((state, action, reward, next_state, done))
        else:
            # Step 模式：直接存入記憶庫
            self.memory.append((state, action, reward, next_state, done))
        
    def act(self, state):
        """
        根據當前狀態選擇動作
        
        Args:
            state: 當前狀態
            
        Returns:
            int: 選擇的動作
        """
        if np.random.rand() <= self.epsilon:
            return random.randrange(self.action_size)
        
        # 將狀態轉換為張量並移至GPU
        state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)
        self.policy_net.eval()  # 設置為評估模式
        with torch.no_grad():
            action_values = self.policy_net(state_tensor)
        self.policy_net.train() # 設置回訓練模式
        
        return np.argmax(action_values.cpu().numpy())
    
    def replay(self):
        """
        從記憶庫中抽樣進行經驗回放和網絡訓練
        """
        # 如果記憶庫中樣本不足，直接返回
        if len(self.memory) < self.batch_size:
            return
            
        minibatch = random.sample(self.memory, self.batch_size)
        
        # 將經驗從 (state, action, reward, next_state, done) 轉換為批次
        states = np.array([transition[0] for transition in minibatch])
        actions = np.array([transition[1] for transition in minibatch])
        rewards = np.array([transition[2] for transition in minibatch])
        next_states = np.array([transition[3] for transition in minibatch])
        dones = np.array([transition[4] for transition in minibatch])
        
        # 將 NumPy 數組轉換為張量並移至GPU
        state_batch = torch.FloatTensor(states).to(self.device)
        action_batch = torch.LongTensor(actions).unsqueeze(1).to(self.device)
        reward_batch = torch.FloatTensor(rewards).unsqueeze(1).to(self.device)
        next_state_batch = torch.FloatTensor(next_states).to(self.device)
        done_batch = torch.FloatTensor(dones).unsqueeze(1).to(self.device)
        
        # 獲取當前狀態的Q值
        # policy_net(state_batch) 返回所有動作的Q值
        # .gather(1, action_batch) 提取已執行動作的Q值
        q_values = self.policy_net(state_batch).gather(1, action_batch)
        
        # 計算下一個狀態的Q值
        with torch.no_grad():
            # target_net(next_state_batch) 預測下一狀態的所有動作的Q值
            # .max(1) 返回每個樣本的最大Q值和其索引
            next_q_values = self.target_net(next_state_batch).max(1)[0].unsqueeze(1)
        
        # 計算期望的Q值 (貝爾曼方程)
        # 如果狀態是結束狀態(done), 則期望Q值就是獎勵
        expected_q_values = reward_batch + (1 - done_batch) * self.gamma * next_q_values
        
        # 計算損失
        loss = self.criterion(q_values, expected_q_values)
        
        # 優化模型
        self.optimizer.zero_grad()
        loss.backward()
        # 梯度裁剪，防止梯度爆炸
        torch.nn.utils.clip_grad_norm_(self.policy_net.parameters(), max_norm=1.0)
        self.optimizer.step()
        
        # 更新 epsilon
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay
            
        # 返回訓練指標
        return {
            'loss': loss.item(),
            'avg_q_value': q_values.mean().item(),
            'epsilon': self.epsilon
        }
            
    def load_model(self, model_path=None):
        """
        加載預訓練模型
        
        Args:
            model_path (str, optional): 完整模型路徑，如果未提供則使用默認模型
            
        Returns:
            bool: 是否成功加載模型
        """
        if not model_path:
            model_path = f"models/{self.model_name}.pth"
            
        if os.path.isfile(model_path):
            try:
                # 使用 map_location 將模型加載到正確的設備
                self.policy_net.load_state_dict(torch.load(model_path, map_location=self.device))
                self.update_target_model()
                self.logger.info(f"DQN model loaded from {model_path} to {self.device}")
                return True
            except Exception as e:
                self.logger.error(f"Error loading DQN model: {e}")
                return False
        else:
            self.logger.warning(f"DQN model file not found: {model_path}")
            return False

    def save_model(self, model_name=None, tick=None, is_final=False):
        """
        保存模型
        
        Args:
            model_name (str, optional): 模型名稱，默認為None使用self.model_name
            tick (int, optional): 當前時間節點，用於標識保存的模型版本
            is_final (bool): 是否為最終模型
        """
        if not model_name:
            save_name = self.model_name
        else:
            save_name = model_name

        if tick is not None:
            save_name = f"{save_name}_{tick}"
        
        if is_final:
            save_name = f"{save_name}_final"

        save_path = f"models/{save_name}.pth"
        
        try:
            torch.save(self.policy_net.state_dict(), save_path)
            self.logger.info(f"DQN model saved: {save_path}")
        except Exception as e:
            self.logger.error(f"Error saving DQN model: {e}")
    
    def process_episode_end(self, global_reward):
        """
        處理 episode 結束時的全局獎勵分配（僅用於 global 模式）
        
        在 global 模式下，將累積的 episode buffer 中的所有轉換
        使用全局獎勵進行回溯性分配，然後存入主記憶庫
        
        Args:
            global_reward (float): episode 結束時計算的全局獎勵
        """
        if self.reward_mode != "global":
            return
            
        if not self.episode_buffer:
            self.logger.warning("Episode buffer is empty, nothing to process")
            return
            
        # 計算每個轉換應得的獎勵
        # 選項 1: 平均分配
        # reward_per_step = global_reward / len(self.episode_buffer)
        
        # 選項 2: 使用折扣因子進行時間衰減分配
        # 後期的動作對最終結果影響更大，應該得到更多獎勵
        discounted_rewards = []
        running_reward = global_reward
        for i in range(len(self.episode_buffer) - 1, -1, -1):
            discounted_rewards.insert(0, running_reward)
            running_reward *= self.gamma
        
        # 將 episode buffer 中的轉換與分配的獎勵一起存入主記憶庫
        for i, (state, action, _, next_state, done) in enumerate(self.episode_buffer):
            # 使用分配的獎勵替換原本的 0 獎勵
            self.memory.append((state, action, discounted_rewards[i], next_state, done))
        
        self.logger.info(f"Processed episode with {len(self.episode_buffer)} steps, global reward: {global_reward:.4f}")
        
        # 清空 episode buffer 為下一個 episode 做準備
        self.episode_buffer = []

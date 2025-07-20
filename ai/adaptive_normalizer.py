import numpy as np
from collections import deque


class AdaptiveNormalizer:
    """
    自適應正規化器
    
    使用運行時統計數據動態調整正規化參數，替代硬編碼的固定值
    """
    
    def __init__(self, feature_names, window_size=1000, percentile=95):
        """
        初始化自適應正規化器
        
        Args:
            feature_names (list): 特徵名稱列表
            window_size (int): 統計窗口大小，控制記憶長度
            percentile (int): 使用的百分位數作為最大值（避免極值影響）
        """
        self.feature_names = feature_names
        self.window_size = window_size
        self.percentile = percentile
        
        # 為每個特徵維護統計數據
        self.feature_data = {}
        for name in feature_names:
            self.feature_data[name] = {
                'values': deque(maxlen=window_size),
                'min_val': 0.0,
                'max_val': 1.0,  # 初始最大值設為1
                'mean': 0.0,
                'std': 1.0
            }
    
    def update_statistics(self, feature_dict):
        """
        更新特徵統計數據
        
        Args:
            feature_dict (dict): 特徵名稱到值的映射
        """
        for name, value in feature_dict.items():
            if name in self.feature_data:
                data = self.feature_data[name]
                data['values'].append(value)
                
                # 重新計算統計數據
                if len(data['values']) > 10:  # 至少需要10個樣本
                    values_array = np.array(data['values'])
                    data['min_val'] = np.min(values_array)
                    data['max_val'] = np.percentile(values_array, self.percentile)
                    data['mean'] = np.mean(values_array)
                    data['std'] = np.std(values_array) if np.std(values_array) > 0 else 1.0
    
    def normalize_feature(self, feature_name, value):
        """
        正規化單個特徵值
        
        Args:
            feature_name (str): 特徵名稱
            value (float): 原始值
            
        Returns:
            float: 正規化後的值 [0, 1]
        """
        if feature_name not in self.feature_data:
            return min(value, 1.0)  # 默認情況下限制在[0,1]
        
        data = self.feature_data[feature_name]
        
        # 使用min-max正規化，並限制在[0,1]範圍
        if data['max_val'] > data['min_val']:
            normalized = (value - data['min_val']) / (data['max_val'] - data['min_val'])
        else:
            normalized = 0.0
        
        return min(max(normalized, 0.0), 1.0)  # 確保結果在[0,1]範圍內
    
    def normalize_features(self, feature_dict):
        """
        正規化多個特徵值
        
        Args:
            feature_dict (dict): 特徵名稱到值的映射
            
        Returns:
            dict: 正規化後的特徵字典
        """
        normalized = {}
        for name, value in feature_dict.items():
            normalized[name] = self.normalize_feature(name, value)
        return normalized
    
    def get_statistics_summary(self):
        """
        獲取當前統計數據摘要
        
        Returns:
            dict: 統計摘要
        """
        summary = {}
        for name, data in self.feature_data.items():
            summary[name] = {
                'samples': len(data['values']),
                'min': data['min_val'],
                'max': data['max_val'],
                'mean': data['mean'],
                'std': data['std']
            }
        return summary
    
    def reset_statistics(self):
        """重置所有統計數據"""
        for name in self.feature_names:
            data = self.feature_data[name]
            data['values'].clear()
            data['min_val'] = 0.0
            data['max_val'] = 1.0
            data['mean'] = 0.0
            data['std'] = 1.0


class TrafficStateNormalizer(AdaptiveNormalizer):
    """
    專門用於交通狀態正規化的自適應正規化器
    """
    
    def __init__(self, window_size=1000):
        # 定義交通狀態的所有特徵
        feature_names = [
            'time_since_change',    # 自上次信號變化的時間
            'h_count',             # 水平方向機器人數量
            'v_count',             # 垂直方向機器人數量
            'h_wait_time',         # 水平方向平均等待時間
            'v_wait_time',         # 垂直方向平均等待時間
            'neighbor_robots',     # 相鄰路口機器人總數
            'neighbor_priority',   # 相鄰路口優先級機器人數
            'neighbor_wait'        # 相鄰路口平均等待時間
        ]
        
        super().__init__(feature_names, window_size)
        
        # 為交通特徵設置合理的初始最大值
        self.feature_data['time_since_change']['max_val'] = 100.0
        self.feature_data['h_count']['max_val'] = 20.0
        self.feature_data['v_count']['max_val'] = 20.0
        self.feature_data['h_wait_time']['max_val'] = 100.0
        self.feature_data['v_wait_time']['max_val'] = 100.0
        self.feature_data['neighbor_robots']['max_val'] = 50.0
        self.feature_data['neighbor_priority']['max_val'] = 30.0
        self.feature_data['neighbor_wait']['max_val'] = 100.0
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
隔離管理器

負責為每個測試創建完全隔離的工作環境，確保並行執行的測試不會互相干擾。
"""

import os
import shutil
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging
import json
from datetime import datetime


class IsolationManager:
    """測試隔離管理器，負責創建和管理隔離的測試環境"""
    
    def __init__(self, base_output_dir: Path, logger: logging.Logger):
        """
        初始化隔離管理器
        
        Args:
            base_output_dir: 基礎輸出目錄
            logger: 日誌記錄器
        """
        self.base_output_dir = Path(base_output_dir)
        self.logger = logger
        self.workspaces = {}  # test_id -> workspace_info
        
        # 需要隔離的檔案和目錄
        self.isolated_files = [
            'assign_order.csv',
            'order-finished.csv', 
            'intersection-energy-consumption.csv'
        ]
        
        self.isolated_dirs = [
            'states',
            'data/orders',
            'data/pods'
        ]
        
        self.logger.info("隔離管理器初始化完成")
    
    def create_isolated_workspace(self, robot_count: int, test_id: str) -> Dict[str, str]:
        """
        為特定測試創建隔離的工作空間
        
        Args:
            robot_count: 機器人數量
            test_id: 測試唯一 ID
            
        Returns:
            包含所有隔離路徑的字典
        """
        workspace_root = self.base_output_dir / "workspaces" / f"{test_id}_robots_{robot_count}"
        workspace_root.mkdir(parents=True, exist_ok=True)
        
        # 創建各個隔離目錄  
        isolated_paths = {
            'workspace_root': str(workspace_root),
            'test_id': test_id,
            'robot_count': robot_count
        }
        
        # 創建狀態檔案目錄
        states_dir = workspace_root / 'states'
        states_dir.mkdir(exist_ok=True)
        isolated_paths['states_dir'] = str(states_dir)
        isolated_paths['state_file'] = str(states_dir / f'netlogo_{test_id}.state')
        
        # 創建 CSV 檔案目錄
        csv_dir = workspace_root / 'csv_files'
        csv_dir.mkdir(exist_ok=True)
        isolated_paths['csv_dir'] = str(csv_dir)
        
        # 設定 CSV 檔案路徑
        for csv_file in self.isolated_files:
            isolated_paths[csv_file.replace('-', '_').replace('.csv', '_file')] = str(csv_dir / csv_file)
        
        # 創建資料目錄
        data_dir = workspace_root / 'data'
        data_dir.mkdir(exist_ok=True)
        isolated_paths['data_dir'] = str(data_dir)
        
        # 創建訂單和 Pod 目錄
        orders_dir = data_dir / 'orders'
        orders_dir.mkdir(exist_ok=True)
        isolated_paths['orders_dir'] = str(orders_dir)
        
        pods_dir = data_dir / 'pods'  
        pods_dir.mkdir(exist_ok=True)
        isolated_paths['pods_dir'] = str(pods_dir)
        
        # 創建結果目錄
        results_dir = workspace_root / 'results'
        results_dir.mkdir(exist_ok=True)
        isolated_paths['results_dir'] = str(results_dir)
        
        # 創建日誌目錄
        logs_dir = workspace_root / 'logs'
        logs_dir.mkdir(exist_ok=True)
        isolated_paths['logs_dir'] = str(logs_dir)
        
        # 複製必要的基礎資料檔案
        self._copy_base_data_files(isolated_paths, robot_count)
        
        # 記錄工作空間資訊
        workspace_info = {
            'test_id': test_id,
            'robot_count': robot_count,
            'workspace_root': str(workspace_root),
            'created_time': datetime.now().isoformat(),
            'isolated_paths': isolated_paths
        }
        
        self.workspaces[test_id] = workspace_info
        
        # 保存工作空間配置
        config_file = workspace_root / 'workspace_config.json'
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(workspace_info, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"已創建隔離工作空間: {test_id} (機器人數量: {robot_count})")
        self.logger.debug(f"工作空間路徑: {workspace_root}")
        
        return isolated_paths
    
    def _copy_base_data_files(self, isolated_paths: Dict[str, str], robot_count: int):
        """
        複製基礎資料檔案到隔離工作空間
        
        Args:
            isolated_paths: 隔離路徑字典
            robot_count: 機器人數量
        """
        project_root = Path(__file__).parent.parent
        
        try:
            # 複製訂單資料檔案（如果存在）
            source_orders_dir = project_root / 'data' / 'orders'
            if source_orders_dir.exists():
                target_orders_dir = Path(isolated_paths['orders_dir'])
                for order_file in source_orders_dir.glob('*.csv'):
                    shutil.copy2(order_file, target_orders_dir / order_file.name)
                    self.logger.debug(f"已複製訂單檔案: {order_file.name}")
            
            # 複製 Pod 資料檔案（如果存在）
            source_pods_dir = project_root / 'data' / 'pods'
            if source_pods_dir.exists():
                target_pods_dir = Path(isolated_paths['pods_dir'])
                for pod_file in source_pods_dir.glob('*.csv'):
                    shutil.copy2(pod_file, target_pods_dir / pod_file.name)
                    self.logger.debug(f"已複製 Pod 檔案: {pod_file.name}")
            
            # 如果需要根據機器人數量調整配置檔案，在這裡處理
            self._adjust_config_for_robot_count(isolated_paths, robot_count)
            
        except Exception as e:
            self.logger.warning(f"複製基礎資料檔案時發生錯誤: {e}")
    
    def _adjust_config_for_robot_count(self, isolated_paths: Dict[str, str], robot_count: int):
        """
        根據機器人數量調整配置
        
        Args:
            isolated_paths: 隔離路徑字典
            robot_count: 機器人數量
        """
        # 這裡可以根據需要調整機器人數量相關的配置
        # 例如創建特定的配置檔案或修改現有配置
        
        config_file = Path(isolated_paths['workspace_root']) / 'robot_config.json'
        robot_config = {
            'robot_count': robot_count,
            'test_mode': 'capacity_test',
            'controller_type': 'none'
        }
        
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(robot_config, f, indent=2, ensure_ascii=False)
        
        self.logger.debug(f"已創建機器人配置檔案，數量: {robot_count}")
    
    def get_isolated_env_vars(self, test_id: str) -> Dict[str, str]:
        """
        獲取特定測試的隔離環境變數
        
        Args:
            test_id: 測試 ID
            
        Returns:
            環境變數字典
        """
        if test_id not in self.workspaces:
            raise ValueError(f"找不到工作空間: {test_id}")
        
        workspace_info = self.workspaces[test_id]
        isolated_paths = workspace_info['isolated_paths']
        
        env_vars = {
            # 設定模擬 ID 以區分不同測試
            'SIMULATION_ID': test_id,
            
            # 設定機器人數量
            'ROBOT_COUNT': str(workspace_info['robot_count']),
            
            # 設定隔離的檔案路徑
            'NETLOGO_STATE_DIR': isolated_paths['states_dir'],
            'NETLOGO_STATE_FILE': isolated_paths['state_file'],
            
            # CSV 檔案路徑
            'ASSIGN_ORDER_CSV': isolated_paths.get('assign_order_file', ''),
            'ORDER_FINISHED_CSV': isolated_paths.get('order_finished_file', ''),  
            'ENERGY_CONSUMPTION_CSV': isolated_paths.get('intersection_energy_consumption_file', ''),
            
            # 資料目錄
            'DATA_DIR': isolated_paths['data_dir'],
            'ORDERS_DIR': isolated_paths['orders_dir'],
            'PODS_DIR': isolated_paths['pods_dir'],
            
            # 結果和日誌目錄
            'RESULTS_DIR': isolated_paths['results_dir'],
            'LOGS_DIR': isolated_paths['logs_dir'],
            
            # 工作空間根目錄
            'WORKSPACE_ROOT': isolated_paths['workspace_root'],
            
            # 測試模式標識
            'TEST_MODE': 'capacity_test',
            'CONTROLLER_TYPE': 'none'
        }
        
        return env_vars
    
    def cleanup_workspace(self, test_id: str, keep_results: bool = True) -> bool:
        """
        清理特定測試的工作空間
        
        Args:
            test_id: 測試 ID
            keep_results: 是否保留結果檔案
            
        Returns:
            是否成功清理
        """
        if test_id not in self.workspaces:
            self.logger.warning(f"找不到工作空間: {test_id}")
            return False
        
        workspace_info = self.workspaces[test_id]
        workspace_root = Path(workspace_info['workspace_root'])
        
        try:
            if keep_results:
                # 只清理臨時檔案，保留結果
                temp_dirs = ['states', 'csv_files', 'logs']
                for temp_dir in temp_dirs:
                    temp_path = workspace_root / temp_dir
                    if temp_path.exists():
                        shutil.rmtree(temp_path)
                        self.logger.debug(f"已清理臨時目錄: {temp_path}")
            else:
                # 完全清理工作空間
                if workspace_root.exists():
                    shutil.rmtree(workspace_root)
                    self.logger.debug(f"已完全清理工作空間: {workspace_root}")
            
            # 從追蹤列表中移除
            del self.workspaces[test_id]
            
            self.logger.info(f"已清理工作空間: {test_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"清理工作空間 {test_id} 時發生錯誤: {e}")
            return False
    
    def cleanup_all_workspaces(self, keep_results: bool = True) -> int:
        """
        清理所有工作空間
        
        Args:
            keep_results: 是否保留結果檔案
            
        Returns:
            成功清理的工作空間數量
        """
        cleaned_count = 0
        test_ids = list(self.workspaces.keys())  # 創建副本以避免迭代時修改字典
        
        for test_id in test_ids:
            if self.cleanup_workspace(test_id, keep_results):
                cleaned_count += 1
        
        self.logger.info(f"已清理 {cleaned_count} 個工作空間")
        return cleaned_count
    
    def get_workspace_info(self, test_id: str) -> Optional[Dict[str, Any]]:
        """
        獲取工作空間資訊
        
        Args:
            test_id: 測試 ID
            
        Returns:
            工作空間資訊字典，如果不存在則返回 None
        """
        return self.workspaces.get(test_id)
    
    def list_all_workspaces(self) -> List[Dict[str, Any]]:
        """
        列出所有工作空間資訊
        
        Returns:
            所有工作空間資訊的列表
        """
        return list(self.workspaces.values())
    
    def get_workspace_size(self, test_id: str) -> int:
        """
        獲取工作空間佔用的磁盤空間大小（位元組）
        
        Args:
            test_id: 測試 ID
            
        Returns:
            磁盤空間大小，如果工作空間不存在則返回 0
        """
        if test_id not in self.workspaces:
            return 0
        
        workspace_root = Path(self.workspaces[test_id]['workspace_root'])
        
        if not workspace_root.exists():
            return 0
        
        total_size = 0
        try:
            for file_path in workspace_root.rglob('*'):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
        except Exception as e:
            self.logger.warning(f"計算工作空間 {test_id} 大小時發生錯誤: {e}")
        
        return total_size
    
    def validate_workspace(self, test_id: str) -> bool:
        """
        驗證工作空間的完整性
        
        Args:
            test_id: 測試 ID
            
        Returns:
            工作空間是否有效
        """
        if test_id not in self.workspaces:
            return False
        
        workspace_info = self.workspaces[test_id]
        workspace_root = Path(workspace_info['workspace_root'])
        
        if not workspace_root.exists():
            return False
        
        # 檢查必要目錄是否存在
        required_dirs = ['states', 'csv_files', 'data', 'results', 'logs']
        for dir_name in required_dirs:
            if not (workspace_root / dir_name).exists():
                self.logger.warning(f"工作空間 {test_id} 缺少必要目錄: {dir_name}")
                return False
        
        # 檢查配置檔案是否存在
        config_file = workspace_root / 'workspace_config.json'
        if not config_file.exists():
            self.logger.warning(f"工作空間 {test_id} 缺少配置檔案")
            return False
        
        return True
"""
修復並行執行問題的工具模組
========================

主要功能：
1. 為每個實驗創建獨立的工作目錄
2. 複製必要的資料檔案
3. 修改路徑使用獨立的檔案
"""

import os
import shutil
import tempfile
from pathlib import Path
from datetime import datetime
import json

class ParallelExecutionFixer:
    """修復並行執行問題的工具類"""
    
    def __init__(self, base_dir):
        self.base_dir = Path(base_dir)
        self.temp_dirs = []
        
    def create_isolated_workspace(self, experiment_id: str) -> Path:
        """
        為實驗創建獨立的工作空間
        
        Args:
            experiment_id: 實驗識別符
            
        Returns:
            Path: 獨立工作目錄的路徑
        """
        # 創建臨時目錄
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        temp_dir = self.base_dir / "temp_workspaces" / f"{experiment_id}_{timestamp}"
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        # 創建必要的子目錄結構
        (temp_dir / "data" / "input").mkdir(parents=True, exist_ok=True)
        (temp_dir / "data" / "output").mkdir(parents=True, exist_ok=True)
        (temp_dir / "result").mkdir(parents=True, exist_ok=True)
        
        # 複製必要的輸入檔案
        original_files = [
            "data/input/assign_order.csv",
            "data/output/generated_order.csv",
            "data/input/generated_backlog.csv"
        ]
        
        for file_path in original_files:
            src = self.base_dir / file_path
            if src.exists():
                dst = temp_dir / file_path
                shutil.copy2(src, dst)
                print(f"複製檔案: {file_path} -> {dst}")
        
        # 記錄臨時目錄
        self.temp_dirs.append(temp_dir)
        
        # 創建配置檔案，記錄路徑映射
        config = {
            "experiment_id": experiment_id,
            "original_base": str(self.base_dir),
            "temp_base": str(temp_dir),
            "created_at": timestamp
        }
        
        config_path = temp_dir / "workspace_config.json"
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        return temp_dir
    
    def cleanup_workspace(self, temp_dir: Path):
        """
        清理臨時工作空間
        
        Args:
            temp_dir: 要清理的臨時目錄
        """
        if temp_dir.exists() and temp_dir in self.temp_dirs:
            # 先保存重要結果
            self._save_results(temp_dir)
            
            # 刪除臨時目錄
            shutil.rmtree(temp_dir)
            self.temp_dirs.remove(temp_dir)
            print(f"清理臨時工作空間: {temp_dir}")
    
    def _save_results(self, temp_dir: Path):
        """保存實驗結果到主目錄"""
        # 讀取配置
        config_path = temp_dir / "workspace_config.json"
        if not config_path.exists():
            return
            
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        experiment_id = config['experiment_id']
        
        # 複製結果檔案
        result_files = list((temp_dir / "result").glob("**/*"))
        if result_files:
            target_dir = self.base_dir / "result" / f"parallel_{experiment_id}"
            target_dir.mkdir(parents=True, exist_ok=True)
            
            for file in result_files:
                if file.is_file():
                    relative = file.relative_to(temp_dir / "result")
                    target = target_dir / relative
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(file, target)
            
            print(f"保存結果到: {target_dir}")
    
    def cleanup_all(self):
        """清理所有臨時工作空間"""
        for temp_dir in self.temp_dirs.copy():
            self.cleanup_workspace(temp_dir)


def create_parallel_train_command(agent: str, reward_mode: str, config: dict, workspace: Path) -> str:
    """
    創建使用獨立工作空間的訓練命令
    
    Args:
        agent: 代理類型 (dqn/nerl)
        reward_mode: 獎勵模式
        config: 訓練配置
        workspace: 工作空間路徑
        
    Returns:
        str: 訓練命令
    """
    # 設置環境變數來指定工作目錄
    env_prefix = f"RMFS_WORKSPACE={workspace}"
    
    if agent == "dqn":
        cmd = f"{env_prefix} python train.py --agent dqn --reward_mode {reward_mode}"
        cmd += f" --training_ticks {config.get('ticks', 10000)}"
    else:  # nerl
        cmd = f"{env_prefix} python train.py --agent nerl --reward_mode {reward_mode}"
        cmd += f" --generations {config.get('generations', 20)}"
        cmd += f" --population {config.get('population', 20)}"
        cmd += f" --eval_ticks {config.get('eval_ticks', 2000)}"
    
    return cmd


def modify_warehouse_for_parallel():
    """
    修改 warehouse.py 以支援並行執行
    
    這個函數會生成一個修改版本的程式碼片段
    """
    modification = '''
# 在 warehouse.py 的開頭加入：
import os

# 獲取工作空間路徑（如果有設定的話）
WORKSPACE_PATH = os.environ.get('RMFS_WORKSPACE', PARENT_DIRECTORY)

# 修改所有的檔案路徑，例如：
# 原本：file_path = PARENT_DIRECTORY + "/data/input/assign_order.csv"
# 改為：file_path = WORKSPACE_PATH + "/data/input/assign_order.csv"
'''
    
    return modification
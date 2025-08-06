"""
並行執行輔助工具
===============

簡單的解決方案：在執行前複製 CSV，執行後刪除
"""

import os
import shutil
from pathlib import Path
from datetime import datetime
import uuid

class CSVIsolator:
    """CSV 檔案隔離器"""
    
    @staticmethod
    def create_isolated_csv(base_path: str) -> tuple:
        """
        創建獨立的 CSV 檔案副本
        
        Returns:
            tuple: (新檔案路徑, 備份ID)
        """
        base_path = Path(base_path)
        unique_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        
        # 創建備份目錄
        backup_dir = base_path.parent.parent / "temp_csv_backups" / unique_id
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        # 備份原始檔案
        original_csv = base_path.parent.parent / "data" / "input" / "assign_order.csv"
        if original_csv.exists():
            backup_csv = backup_dir / "assign_order_original.csv"
            shutil.copy2(original_csv, backup_csv)
        
        return str(backup_dir), unique_id
    
    @staticmethod  
    def restore_csv(backup_dir: str):
        """恢復原始 CSV 檔案"""
        backup_dir = Path(backup_dir)
        if backup_dir.exists():
            shutil.rmtree(backup_dir)


def wrap_training_for_parallel(train_func):
    """
    包裝訓練函數以支援並行執行
    
    使用裝飾器模式包裝原有的訓練函數
    """
    def wrapper(*args, **kwargs):
        # 創建獨立的 CSV 環境
        backup_dir, backup_id = CSVIsolator.create_isolated_csv(Path.cwd())
        
        # 設置環境變數
        original_env = os.environ.get('RMFS_CSV_ID', '')
        os.environ['RMFS_CSV_ID'] = backup_id
        
        try:
            # 執行原始訓練函數
            result = train_func(*args, **kwargs)
            return result
        finally:
            # 清理
            os.environ['RMFS_CSV_ID'] = original_env
            CSVIsolator.restore_csv(backup_dir)
    
    return wrapper


# 快速修復方案：直接修改檔案名稱
def quick_fix_csv_conflict():
    """
    快速修復：為每個進程使用不同的 CSV 檔案名稱
    
    在 warehouse.py 中搜尋替換：
    "/data/input/assign_order.csv" 
    替換為：
    f"/data/input/assign_order_{os.getpid()}.csv"
    """
    
    print("""
    快速修復步驟：
    
    1. 在 warehouse.py 開頭加入：
       import os
       
    2. 搜尋所有的：
       file_path = PARENT_DIRECTORY + "/data/input/assign_order.csv"
       
    3. 替換為：
       file_path = PARENT_DIRECTORY + f"/data/input/assign_order_{os.getpid()}.csv"
       
    4. 這樣每個進程會使用自己的 CSV 檔案，避免衝突
    
    5. 訓練結束後清理臨時檔案：
       for f in Path("data/input").glob("assign_order_*.csv"):
           if f.name != "assign_order.csv":
               f.unlink()
    """)


# 最佳解決方案：使用記憶體資料結構
class InMemoryOrderAssignment:
    """
    在記憶體中管理訂單分配，完全避免檔案 I/O
    """
    
    def __init__(self):
        self._data = {}
        self._lock = None  # 如果需要線程安全可以加鎖
    
    def load_from_csv(self, path):
        """從 CSV 載入初始資料"""
        import pandas as pd
        if Path(path).exists():
            df = pd.read_csv(path)
            self._data = df.to_dict('records')
    
    def save_to_csv(self, path):
        """保存到 CSV（僅在需要時）"""
        import pandas as pd
        df = pd.DataFrame(self._data)
        df.to_csv(path, index=False)
    
    def update_order_status(self, order_id, item_id, status):
        """更新訂單狀態（在記憶體中）"""
        for record in self._data:
            if record['order_id'] == order_id and record['item_id'] == item_id:
                record['status'] = status
                break
    
    def get_orders(self):
        """獲取所有訂單"""
        return self._data
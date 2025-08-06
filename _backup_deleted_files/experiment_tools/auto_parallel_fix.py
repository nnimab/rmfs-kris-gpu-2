"""
自動修復並行執行問題的模組
======================

自動整合到實驗腳本中，無需手動操作
"""

import os
import re
import shutil
from pathlib import Path
from datetime import datetime

class AutoParallelFixer:
    """自動修復並行問題的工具類"""
    
    def __init__(self):
        self.fixed_files = []
        self.backup_dir = Path("backups") / datetime.now().strftime("%Y%m%d_%H%M%S")
        
    def check_and_fix(self):
        """檢查並自動修復並行問題"""
        print("\n🔍 檢查並行執行環境...")
        
        # 檢查是否已經修復過
        if self._is_already_fixed():
            print("✅ 系統已經支援並行執行")
            return True
        
        print("⚠️  檢測到 CSV 衝突問題，開始自動修復...")
        
        # 創建備份目錄
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # 修復各個檔案
        success = True
        success &= self._fix_warehouse()
        success &= self._fix_generator()
        success &= self._fix_netlogo()
        
        if success:
            print("✅ 並行環境修復完成！")
            return True
        else:
            print("❌ 修復失敗，請手動檢查")
            return False
    
    def _is_already_fixed(self):
        """檢查是否已經修復過"""
        warehouse_path = Path("world/warehouse.py")
        if warehouse_path.exists():
            with open(warehouse_path, 'r', encoding='utf-8') as f:
                content = f.read()
                return "os.getpid()" in content
        return False
    
    def _backup_file(self, file_path):
        """備份檔案"""
        if file_path.exists():
            backup_path = self.backup_dir / file_path.name
            shutil.copy2(file_path, backup_path)
            return backup_path
        return None
    
    def _fix_warehouse(self):
        """修復 warehouse.py"""
        file_path = Path("world/warehouse.py")
        if not file_path.exists():
            return False
        
        # 備份
        self._backup_file(file_path)
        
        # 讀取內容
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 添加 import os（如果需要）
        if "import os" not in content.split('\n')[:50]:
            import_match = re.search(r'(import .+\n)+', content)
            if import_match:
                insert_pos = import_match.end()
                content = content[:insert_pos] + "import os\n" + content[insert_pos:]
        
        # 修改 CSV 路徑
        pattern = r'file_path = PARENT_DIRECTORY \+ "/data/input/assign_order\.csv"'
        replacement = 'file_path = PARENT_DIRECTORY + f"/data/input/assign_order_{os.getpid()}.csv"'
        content = re.sub(pattern, replacement, content)
        
        # 寫回
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        self.fixed_files.append(str(file_path))
        return True
    
    def _fix_generator(self):
        """修復 warehouse_generator.py"""
        file_path = Path("lib/generator/warehouse_generator.py")
        if not file_path.exists():
            return True  # 不是必須的檔案
        
        # 備份
        self._backup_file(file_path)
        
        # 讀取內容
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 修改 CSV 路徑
        pattern = r'file_path = PARENT_DIRECTORY \+ "/data/input/assign_order\.csv"'
        replacement = 'file_path = PARENT_DIRECTORY + f"/data/input/assign_order_{os.getpid()}.csv"'
        content = re.sub(pattern, replacement, content)
        
        # 寫回
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        self.fixed_files.append(str(file_path))
        return True
    
    def _fix_netlogo(self):
        """修復 netlogo.py"""
        file_path = Path("netlogo.py")
        if not file_path.exists():
            return False
        
        # 備份
        self._backup_file(file_path)
        
        # 讀取內容
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 修改 CSV 路徑
        pattern = r'assignment_path = PARENT_DIRECTORY \+ "/data/input/assign_order\.csv"'
        replacement = 'assignment_path = PARENT_DIRECTORY + f"/data/input/assign_order_{os.getpid()}.csv"'
        content = re.sub(pattern, replacement, content)
        
        # 寫回
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        self.fixed_files.append(str(file_path))
        return True
    
    def cleanup_temp_csv(self):
        """清理臨時 CSV 檔案"""
        csv_dir = Path("data/input")
        if csv_dir.exists():
            temp_files = list(csv_dir.glob("assign_order_*.csv"))
            for f in temp_files:
                if f.name != "assign_order.csv":
                    try:
                        f.unlink()
                    except:
                        pass
    
    def restore_backups(self):
        """還原備份（如果需要）"""
        if self.backup_dir.exists():
            print(f"備份檔案位於: {self.backup_dir}")
            # 這裡不自動還原，讓使用者手動處理


# 單例模式，確保只初始化一次
_fixer_instance = None

def get_fixer():
    """獲取修復器實例"""
    global _fixer_instance
    if _fixer_instance is None:
        _fixer_instance = AutoParallelFixer()
    return _fixer_instance
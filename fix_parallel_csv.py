#!/usr/bin/env python3
"""
快速修復 CSV 並行衝突問題
======================

這個腳本會自動修改 warehouse.py 和相關檔案
讓每個進程使用獨立的 CSV 檔案
"""

import os
import re
from pathlib import Path
import shutil
from datetime import datetime

def backup_file(file_path):
    """備份原始檔案"""
    backup_path = f"{file_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(file_path, backup_path)
    print(f"✅ 備份檔案: {backup_path}")
    return backup_path

def fix_warehouse_csv_conflict():
    """修復 warehouse.py 中的 CSV 衝突"""
    
    warehouse_path = Path("world/warehouse.py")
    if not warehouse_path.exists():
        print("❌ 找不到 world/warehouse.py")
        return False
    
    # 備份原始檔案
    backup_file(warehouse_path)
    
    # 讀取檔案內容
    with open(warehouse_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 檢查是否已經修復過
    if "os.getpid()" in content:
        print("⚠️  檔案已經修復過了")
        return True
    
    # 在檔案開頭加入 import（如果還沒有）
    if "import os" not in content.split('\n')[:50]:
        # 找到其他 import 語句的位置
        import_match = re.search(r'(import .+\n)+', content)
        if import_match:
            insert_pos = import_match.end()
            content = content[:insert_pos] + "import os\n" + content[insert_pos:]
        else:
            content = "import os\n" + content
    
    # 修改 CSV 路徑
    # 原始模式：file_path = PARENT_DIRECTORY + "/data/input/assign_order.csv"
    pattern = r'file_path = PARENT_DIRECTORY \+ "/data/input/assign_order\.csv"'
    replacement = 'file_path = PARENT_DIRECTORY + f"/data/input/assign_order_{os.getpid()}.csv"'
    
    content = re.sub(pattern, replacement, content)
    
    # 寫回檔案
    with open(warehouse_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ 修復 warehouse.py 完成")
    print(f"   - 每個進程現在會使用 assign_order_{{進程ID}}.csv")
    
    return True

def fix_generator_csv_conflict():
    """修復 warehouse_generator.py 中的 CSV 衝突"""
    
    generator_path = Path("lib/generator/warehouse_generator.py")
    if not generator_path.exists():
        print("⚠️  找不到 lib/generator/warehouse_generator.py")
        return False
    
    # 備份原始檔案
    backup_file(generator_path)
    
    # 讀取檔案內容
    with open(generator_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 檢查是否已經修復過
    if "os.getpid()" in content:
        print("⚠️  warehouse_generator.py 已經修復過了")
        return True
    
    # 修改 CSV 路徑
    pattern = r'file_path = PARENT_DIRECTORY \+ "/data/input/assign_order\.csv"'
    replacement = 'file_path = PARENT_DIRECTORY + f"/data/input/assign_order_{os.getpid()}.csv"'
    
    content = re.sub(pattern, replacement, content)
    
    # 寫回檔案
    with open(generator_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ 修復 warehouse_generator.py 完成")
    
    return True

def fix_netlogo_csv_conflict():
    """修復 netlogo.py 中的 CSV 衝突"""
    
    netlogo_path = Path("netlogo.py")
    if not netlogo_path.exists():
        print("❌ 找不到 netlogo.py")
        return False
    
    # 備份原始檔案
    backup_file(netlogo_path)
    
    # 讀取檔案內容
    with open(netlogo_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 檢查是否已經修復過
    if "os.getpid()" in content:
        print("⚠️  netlogo.py 已經修復過了")
        return True
    
    # 修改 CSV 路徑
    pattern = r'assignment_path = PARENT_DIRECTORY \+ "/data/input/assign_order\.csv"'
    replacement = 'assignment_path = PARENT_DIRECTORY + f"/data/input/assign_order_{os.getpid()}.csv"'
    
    content = re.sub(pattern, replacement, content)
    
    # 寫回檔案
    with open(netlogo_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ 修復 netlogo.py 完成")
    
    return True

def create_cleanup_script():
    """創建清理臨時 CSV 檔案的腳本"""
    
    cleanup_script = '''#!/usr/bin/env python3
"""清理臨時 CSV 檔案"""
from pathlib import Path

def cleanup_temp_csv():
    """清理所有臨時的 assign_order_*.csv 檔案"""
    
    csv_dir = Path("data/input")
    if not csv_dir.exists():
        print("找不到 data/input 目錄")
        return
    
    temp_files = list(csv_dir.glob("assign_order_*.csv"))
    
    if not temp_files:
        print("沒有找到臨時 CSV 檔案")
        return
    
    print(f"找到 {len(temp_files)} 個臨時檔案")
    
    for f in temp_files:
        if f.name != "assign_order.csv":  # 不要刪除原始檔案
            f.unlink()
            print(f"刪除: {f}")
    
    print("清理完成！")

if __name__ == "__main__":
    cleanup_temp_csv()
'''
    
    with open("cleanup_csv.py", 'w') as f:
        f.write(cleanup_script)
    
    print("✅ 創建清理腳本: cleanup_csv.py")

def main():
    """主函數"""
    print("="*60)
    print("🔧 開始修復 CSV 並行衝突問題")
    print("="*60)
    
    # 修復各個檔案
    success = True
    success &= fix_warehouse_csv_conflict()
    success &= fix_generator_csv_conflict()
    success &= fix_netlogo_csv_conflict()
    
    if success:
        print("\n✅ 修復完成！")
        print("\n現在可以安全地並行執行實驗了")
        print("每個進程會使用獨立的 CSV 檔案")
        
        # 創建清理腳本
        create_cleanup_script()
        
        print("\n使用方法：")
        print("1. 在實驗腳本中選擇並行執行")
        print("2. 實驗結束後執行: python cleanup_csv.py")
        
        print("\n⚠️  注意事項：")
        print("- 每個進程會創建 assign_order_{進程ID}.csv")
        print("- 實驗結束後記得清理臨時檔案")
        print("- 如果要還原，使用 .backup 檔案")
    else:
        print("\n❌ 修復過程中出現問題")
        print("請檢查錯誤訊息並手動修復")

if __name__ == "__main__":
    main()
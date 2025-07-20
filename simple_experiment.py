#!/usr/bin/env python3
"""
RMFS 簡潔實驗管理系統 - 快速入口
================================

快速啟動簡潔實驗管理系統的入口腳本

使用方法:
python simple_experiment.py

功能:
- 🤖 AI模型訓練
- 📊 效能驗證 (6個控制器)
- 📈 數據分析與圖表  
- 🚀 完整實驗流程
- ⚙️ 自定義參數設置
"""

import sys
from pathlib import Path

# 添加experiment_tools路徑
current_dir = Path(__file__).parent
experiment_tools_dir = current_dir / "experiment_tools"
sys.path.insert(0, str(current_dir))

try:
    from experiment_tools.simple_experiment_manager import main
    
    if __name__ == "__main__":
        main()
        
except ImportError as e:
    print(f"❌ 導入失敗: {e}")
    print(f"請確保 experiment_tools 目錄存在並包含所有必要文件")
    print(f"當前目錄: {current_dir}")
    print(f"尋找目錄: {experiment_tools_dir}")
    
    if experiment_tools_dir.exists():
        print("✅ experiment_tools 目錄存在")
        files = list(experiment_tools_dir.glob("*.py"))
        print(f"包含文件: {[f.name for f in files]}")
    else:
        print("❌ experiment_tools 目錄不存在")
    
    sys.exit(1)
except Exception as e:
    print(f"❌ 執行錯誤: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
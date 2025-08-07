#!/usr/bin/env python3
"""
測試基準模型並行執行
"""

import sys
from pathlib import Path

# 加入專案根目錄到 Python 路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from test.baseline_test_controller import BaselineTestController

def test_parallel_execution():
    """測試並行執行功能"""
    print("測試基準模型並行執行...")
    
    # 創建控制器
    controller = BaselineTestController()
    
    # 使用小規模測試參數
    robot_counts = [30]
    time_ratios = ["60:40", "70:30"]
    runs_per_config = 2
    test_ticks = 1000  # 使用較少的 ticks 進行快速測試
    
    print(f"測試配置:")
    print(f"- 機器人數量: {robot_counts}")
    print(f"- 時間配比: {time_ratios}")
    print(f"- 每個配置運行次數: {runs_per_config}")
    print(f"- 測試 ticks: {test_ticks}")
    print(f"- 總測試數: {len(robot_counts) * len(time_ratios) * runs_per_config}")
    
    try:
        # 執行並行測試
        print("\n開始並行測試...")
        summary = controller.run_time_based_sweep(
            robot_counts=robot_counts,
            time_ratios=time_ratios,
            runs_per_config=runs_per_config,
            test_ticks=test_ticks,
            parallel=True,
            max_parallel=2
        )
        
        print("\n✅ 並行測試成功完成!")
        print(f"完成測試: {summary['completed_tests']}/{summary['total_tests']}")
        print(f"失敗測試: {summary['failed_tests']}")
        print(f"總執行時間: {summary['total_execution_time']:.1f} 秒")
        print(f"結果目錄: {summary['output_dir']}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 並行測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_parallel_execution()
    sys.exit(0 if success else 1)
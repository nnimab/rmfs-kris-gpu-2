#!/usr/bin/env python3
"""
測試多run容量測試功能
"""
import sys
from pathlib import Path

# 加入專案根目錄到 Python 路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from test.capacity_test_controller import CapacityTestController


def test_multi_run():
    """測試多run功能"""
    print("=" * 60)
    print("開始測試多run容量測試功能")
    print("=" * 60)
    
    # 初始化控制器
    controller = CapacityTestController()
    
    # 測試參數
    robot_counts = [20, 25]  # 只測試兩個數量以節省時間
    runs_per_config = 3  # 每個配置運行3次
    test_ticks = 1000  # 較短的測試時間
    
    print(f"\n測試配置:")
    print(f"- 機器人數量: {robot_counts}")
    print(f"- 每個配置運行次數: {runs_per_config}")
    print(f"- 測試 ticks: {test_ticks}")
    print(f"- 總測試數: {len(robot_counts) * runs_per_config}")
    
    # 執行測試
    try:
        summary = controller.run_capacity_test(
            robot_counts=robot_counts,
            parallel=False,  # 使用串行執行以確保隔離
            test_ticks=test_ticks,
            runs_per_config=runs_per_config
        )
        
        # 顯示結果
        print("\n" + "=" * 60)
        print("測試結果摘要:")
        print(f"- 總測試數: {summary['total_tests']}")
        print(f"- 成功測試: {summary['completed_tests']}")
        print(f"- 失敗測試: {summary['failed_tests']}")
        print(f"- 總執行時間: {summary['total_execution_time']:.1f} 秒")
        
        # 顯示各個機器人數量的結果
        if 'results_by_robot_count' in summary:
            print("\n各機器人數量的測試結果:")
            for robot_count in sorted(summary['results_by_robot_count'].keys()):
                results = summary['results_by_robot_count'][robot_count]
                completed = len([r for r in results if r['status'] == 'completed'])
                print(f"\n機器人數量 {robot_count}:")
                print(f"  - 成功: {completed}/{len(results)}")
                
                # 顯示每次運行的狀態
                for i, result in enumerate(results):
                    print(f"  - 第 {i+1} 次運行: {result['status']}")
        
        print("\n" + "=" * 60)
        print(f"詳細結果保存在: {controller.base_output_dir}")
        
    except Exception as e:
        print(f"\n錯誤: 測試執行失敗 - {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = test_multi_run()
    sys.exit(0 if success else 1)
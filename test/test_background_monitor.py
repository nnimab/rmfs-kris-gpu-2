#!/usr/bin/env python3
"""
測試背景執行和監控功能
"""
import sys
import time
from pathlib import Path

# 加入專案根目錄到 Python 路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from test.capacity_test_controller import CapacityTestController


def test_background_with_monitor():
    """測試背景執行和監控功能"""
    print("=" * 60)
    print("測試背景執行和監控功能")
    print("=" * 60)
    
    # 初始化控制器（啟用監控）
    controller = CapacityTestController(enable_monitor=True)
    
    # 測試參數
    robot_counts = [20]  # 只測試一個數量
    runs_per_config = 2  # 運行2次
    test_ticks = 1000  # 短時間測試
    
    print(f"\n測試配置:")
    print(f"- 機器人數量: {robot_counts}")
    print(f"- 每個配置運行次數: {runs_per_config}")
    print(f"- 測試 ticks: {test_ticks}")
    
    try:
        # 在背景執行測試
        session_id = controller.run_capacity_test_background(
            robot_counts=robot_counts,
            parallel=False,
            test_ticks=test_ticks,
            runs_per_config=runs_per_config
        )
        
        print(f"\n✅ 測試已在背景開始執行")
        print(f"📌 會話ID: {session_id}")
        
        # 監控測試進度
        print("\n開始監控測試進度...")
        print("-" * 60)
        
        monitor_count = 0
        while True:
            # 獲取所有測試狀態
            status_list = controller.test_monitor.get_all_test_status()
            
            # 顯示狀態
            print(f"\n[監控更新 #{monitor_count + 1}]")
            for status in status_list:
                print(f"測試 {status['test_id']}:")
                print(f"  - 機器人數量: {status['robot_count']}")
                print(f"  - 運行: 第 {status['run_index'] + 1} 次")
                print(f"  - 狀態: {status['status']}")
                print(f"  - 進度: {status['progress']['percentage']:.1f}%")
                print(f"  - 完成訂單: {status['progress']['completed_orders']}/{status['progress']['total_orders']}")
                print(f"  - 執行時間: {status['elapsed_time']:.1f}s")
                
                # 獲取輸出
                stdout_lines, stderr_lines = controller.test_monitor.get_test_output(
                    status['test_id'], max_lines=3
                )
                
                if stdout_lines:
                    print(f"  - 最新輸出: {stdout_lines[-1] if stdout_lines else 'N/A'}")
            
            # 檢查是否所有測試都已完成
            if all(s['status'] in ['已完成', '失敗', '已取消'] for s in status_list):
                print("\n✅ 所有測試已完成")
                break
            
            # 每5秒更新一次
            time.sleep(5)
            monitor_count += 1
            
            # 限制監控次數避免無限循環
            if monitor_count > 100:
                print("\n⚠️ 達到最大監控次數限制")
                break
        
        # 保存監控狀態
        controller.test_monitor.save_monitor_state()
        print(f"\n監控狀態已保存至: {controller.base_output_dir}/monitor_state.json")
        
        # 清理
        controller.test_monitor.cleanup()
        
    except Exception as e:
        print(f"\n錯誤: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = test_background_with_monitor()
    sys.exit(0 if success else 1)
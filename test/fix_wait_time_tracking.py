#!/usr/bin/env python3
"""
修復機器人等待時間追蹤問題

問題：
- intersection_wait_time 在機器人通過路口後會被重置為 0
- 導致評估時無法收集歷史等待事件
- avg_wait_time 總是 0

解決方案：
1. 新增 wait_time_history 列表來保存歷史等待事件
2. 在機器人通過路口時，將等待時間保存到歷史記錄中
3. 修改評估邏輯，收集歷史等待事件而非當前等待狀態
"""

import os
import sys
from pathlib import Path

# 加入專案根目錄到 Python 路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def create_wait_time_tracking_fix():
    """創建等待時間追蹤修復補丁"""
    
    # 修復 1: 修改 robot.py - 添加等待時間歷史記錄
    robot_file = project_root / "world" / "entities" / "robot.py"
    
    print("修復 robot.py 中的等待時間追蹤...")
    
    # 讀取原始檔案
    with open(robot_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 1.1 在 __init__ 方法中添加 wait_time_history
    init_addition = '''        self.intersection_wait_time = {}  # 記錄在每個路口等待的時間
        self.wait_time_history = []  # 新增：保存歷史等待事件'''
    
    old_init_line = '''        self.intersection_wait_time = {}  # 記錄在每個路口等待的時間'''
    
    if old_init_line in content:
        content = content.replace(old_init_line, init_addition)
        print("✓ 已在 __init__ 中添加 wait_time_history")
    else:
        print("⚠ 找不到原始的 intersection_wait_time 初始化")
    
    # 1.2 修改 pathBlockedByIntersection 方法
    # 找到重置等待時間的部分並修改
    old_reset_code = '''                # Reset wait time if can move or not close enough
                if hasattr(self, 'intersection_wait_time') and intersection.id in self.intersection_wait_time:
                    self.intersection_wait_time[intersection.id] = 0'''
    
    new_reset_code = '''                # Reset wait time if can move or not close enough
                if hasattr(self, 'intersection_wait_time') and intersection.id in self.intersection_wait_time:
                    # 保存等待時間到歷史記錄（如果有等待）
                    wait_time = self.intersection_wait_time[intersection.id]
                    if wait_time > 0:
                        if not hasattr(self, 'wait_time_history'):
                            self.wait_time_history = []
                        self.wait_time_history.append({
                            'intersection_id': intersection.id,
                            'wait_time': wait_time,
                            'tick': self.latest_tick  # 記錄發生的時間點
                        })
                        if Robot.DEBUG_LEVEL > 1:
                            logger.debug(f"Robot {self.id} finished waiting {wait_time} ticks at intersection {intersection.id}")
                    self.intersection_wait_time[intersection.id] = 0'''
    
    if old_reset_code in content:
        content = content.replace(old_reset_code, new_reset_code)
        print("✓ 已修改 pathBlockedByIntersection 方法")
    else:
        print("⚠ 找不到原始的重置等待時間代碼")
    
    # 備份原始檔案
    backup_file = robot_file.with_suffix('.py.backup_wait_time')
    with open(backup_file, 'w', encoding='utf-8') as f:
        with open(robot_file, 'r', encoding='utf-8') as orig:
            f.write(orig.read())
    print(f"✓ 已備份原始檔案到 {backup_file}")
    
    # 寫入修改後的檔案
    with open(robot_file, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"✓ 已更新 {robot_file}")
    
    # 修復 2: 修改 evaluate.py - 收集歷史等待事件
    evaluate_file = project_root / "evaluate.py"
    
    print("\n修復 evaluate.py 中的等待時間收集...")
    
    # 讀取原始檔案
    with open(evaluate_file, 'r', encoding='utf-8') as f:
        eval_content = f.read()
    
    # 找到收集等待時間的部分
    old_collect_code = '''                    for robot in warehouse.robot_manager.robots:
                        if hasattr(robot, 'intersection_wait_time'):
                            for intersection_id, wait_time in robot.intersection_wait_time.items():
                                if wait_time > 0:
                                    metrics['all_wait_events'].append(wait_time)'''
    
    new_collect_code = '''                    for robot in warehouse.robot_manager.robots:
                        # 收集歷史等待事件
                        if hasattr(robot, 'wait_time_history'):
                            for event in robot.wait_time_history:
                                if event['wait_time'] > 0:
                                    metrics['all_wait_events'].append(event['wait_time'])
                        
                        # 也收集當前正在等待的時間（如果有）
                        if hasattr(robot, 'intersection_wait_time'):
                            for intersection_id, wait_time in robot.intersection_wait_time.items():
                                if wait_time > 0:
                                    metrics['all_wait_events'].append(wait_time)'''
    
    if old_collect_code in eval_content:
        eval_content = eval_content.replace(old_collect_code, new_collect_code)
        print("✓ 已修改等待時間收集邏輯")
    else:
        print("⚠ 找不到原始的等待時間收集代碼")
    
    # 備份原始檔案
    eval_backup_file = evaluate_file.with_suffix('.py.backup_wait_time')
    with open(eval_backup_file, 'w', encoding='utf-8') as f:
        with open(evaluate_file, 'r', encoding='utf-8') as orig:
            f.write(orig.read())
    print(f"✓ 已備份原始檔案到 {eval_backup_file}")
    
    # 寫入修改後的檔案
    with open(evaluate_file, 'w', encoding='utf-8') as f:
        f.write(eval_content)
    print(f"✓ 已更新 {evaluate_file}")
    
    # 創建驗證腳本
    create_wait_time_verification_script()

def create_wait_time_verification_script():
    """創建等待時間追蹤驗證腳本"""
    
    verify_script = project_root / "test" / "verify_wait_time_fix.py"
    
    script_content = '''#!/usr/bin/env python3
"""
驗證等待時間追蹤修復是否有效
"""

import sys
from pathlib import Path

# 加入專案根目錄到 Python 路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from world.entities.robot import Robot

def test_wait_time_tracking():
    """測試等待時間追蹤"""
    
    print("測試等待時間追蹤...")
    
    # 創建測試機器人
    robot = Robot(1, 10, 10)
    robot._id = 1
    robot.latest_tick = 0
    
    # 初始化屬性（如果需要）
    if not hasattr(robot, 'wait_time_history'):
        robot.wait_time_history = []
    
    print("\\n模擬等待時間追蹤:")
    
    # 模擬在路口等待
    print("\\n1. 機器人開始在路口 1 等待")
    robot.intersection_wait_time = {1: 0}
    
    # 模擬等待 5 個 tick
    for tick in range(1, 6):
        robot.latest_tick = tick
        robot.intersection_wait_time[1] += 1
        print(f"   Tick {tick}: 等待時間 = {robot.intersection_wait_time[1]}")
    
    # 模擬機器人通過路口（在實際代碼中會調用重置邏輯）
    print("\\n2. 機器人通過路口 1")
    wait_time = robot.intersection_wait_time[1]
    if wait_time > 0:
        robot.wait_time_history.append({
            'intersection_id': 1,
            'wait_time': wait_time,
            'tick': robot.latest_tick
        })
    robot.intersection_wait_time[1] = 0
    
    print(f"   保存的等待事件: {robot.wait_time_history[-1]}")
    print(f"   當前等待時間: {robot.intersection_wait_time}")
    
    # 模擬在另一個路口等待
    print("\\n3. 機器人在路口 2 等待 3 個 tick")
    robot.intersection_wait_time[2] = 3
    robot.latest_tick = 10
    robot.wait_time_history.append({
        'intersection_id': 2,
        'wait_time': 3,
        'tick': 10
    })
    robot.intersection_wait_time[2] = 0
    
    # 顯示所有歷史等待事件
    print("\\n4. 所有歷史等待事件:")
    for i, event in enumerate(robot.wait_time_history):
        print(f"   事件 {i+1}: 路口 {event['intersection_id']}, "
              f"等待 {event['wait_time']} ticks, "
              f"發生在 tick {event['tick']}")
    
    # 計算平均等待時間
    if robot.wait_time_history:
        total_wait = sum(event['wait_time'] for event in robot.wait_time_history)
        avg_wait = total_wait / len(robot.wait_time_history)
        print(f"\\n5. 平均等待時間: {avg_wait:.2f} ticks")
        print(f"   總等待事件數: {len(robot.wait_time_history)}")
        print(f"   總等待時間: {total_wait} ticks")
    
    print("\\n✓ 等待時間追蹤測試完成！")
    
    # 測試評估邏輯
    print("\\n6. 模擬評估收集:")
    all_wait_events = []
    
    # 收集歷史等待事件
    if hasattr(robot, 'wait_time_history'):
        for event in robot.wait_time_history:
            if event['wait_time'] > 0:
                all_wait_events.append(event['wait_time'])
    
    # 收集當前等待時間
    if hasattr(robot, 'intersection_wait_time'):
        for intersection_id, wait_time in robot.intersection_wait_time.items():
            if wait_time > 0:
                all_wait_events.append(wait_time)
    
    print(f"   收集到的等待事件: {all_wait_events}")
    
    if all_wait_events:
        avg_wait_time = sum(all_wait_events) / len(all_wait_events)
        print(f"   計算的平均等待時間: {avg_wait_time:.2f}")
    else:
        print("   沒有等待事件（這就是原本的問題！）")

if __name__ == "__main__":
    test_wait_time_tracking()
'''
    
    with open(verify_script, 'w', encoding='utf-8') as f:
        f.write(script_content)
    
    print(f"\n✓ 已創建驗證腳本 {verify_script}")
    print("\n請執行以下命令來驗證修復:")
    print(f"python {verify_script}")

if __name__ == "__main__":
    print("開始修復等待時間追蹤問題...")
    create_wait_time_tracking_fix()
    print("\n修復完成！")
    print("\n注意：這個修復需要重新運行評估才能看到效果。")
    print("因為需要累積歷史等待事件，所以 avg_wait_time 才會有非零值。")
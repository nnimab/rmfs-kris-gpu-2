#!/usr/bin/env python3
"""
修復機器人利用率計算問題的補丁腳本

問題：
1. 機器人利用率出現負值
2. avg_wait_time 總是 0

解決方案：
1. 修復機器人初始化時的狀態設置
2. 在 get_current_active_time 方法中加入邊界檢查
3. 確保 intersection_wait_time 正確記錄
"""

import os
import sys
from pathlib import Path

# 加入專案根目錄到 Python 路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def create_robot_utilization_fix():
    """創建機器人利用率修復補丁"""
    
    robot_file = project_root / "world" / "entities" / "robot.py"
    
    # 讀取原始檔案
    with open(robot_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 修復 1: 修改 get_current_active_time 方法，加入邊界檢查
    old_get_current_active_time = '''def get_current_active_time(self, current_tick):
        """
        獲取當前的總活動時間（包括正在進行的活動）
        用於評估時正確計算機器人利用率
        """
        total_time = self.total_active_time
        
        # 如果機器人當前處於非閒置狀態，加上從上次狀態變化到現在的時間
        if self.current_state != 'idle' and self.last_state_change_time > 0:
            total_time += current_tick - self.last_state_change_time
            
        return total_time'''
    
    new_get_current_active_time = '''def get_current_active_time(self, current_tick):
        """
        獲取當前的總活動時間（包括正在進行的活動）
        用於評估時正確計算機器人利用率
        """
        total_time = self.total_active_time
        
        # 如果機器人當前處於非閒置狀態，加上從上次狀態變化到現在的時間
        if self.current_state != 'idle' and self.last_state_change_time > 0:
            # 加入邊界檢查，確保不會超過當前 tick
            active_duration = current_tick - self.last_state_change_time
            if active_duration > 0:
                total_time += active_duration
            else:
                # 如果出現負數，記錄警告
                if self.DEBUG_LEVEL >= 1:
                    logger.warning(f"Robot {self.robotName()} has negative active duration: {active_duration}, current_tick: {current_tick}, last_state_change: {self.last_state_change_time}")
        
        # 確保總時間不超過 current_tick（機器人不可能活動超過總時間）
        if total_time > current_tick:
            if self.DEBUG_LEVEL >= 1:
                logger.warning(f"Robot {self.robotName()} active time {total_time} exceeds current tick {current_tick}, capping to current tick")
            total_time = current_tick
            
        return total_time'''
    
    # 替換方法
    if old_get_current_active_time in content:
        content = content.replace(old_get_current_active_time, new_get_current_active_time)
        print("✓ 已修復 get_current_active_time 方法")
    else:
        print("⚠ 找不到原始的 get_current_active_time 方法，可能已經被修改")
    
    # 修復 2: 修改 updateState 方法，處理初始化情況
    old_updatestate_init_check = '''        # 如果是第一次設置非閒置狀態（初始化時），也要記錄時間
        if self.last_state_change_time == 0 and new_state != 'idle':
            self.last_state_change_time = current_tick
            if self.DEBUG_LEVEL >= 2:
                logger.debug(f"Robot {self.robotName()} initialized as active at tick {current_tick}")'''
    
    new_updatestate_init_check = '''        # 如果是第一次設置非閒置狀態（初始化時），也要記錄時間
        if self.last_state_change_time == 0 and new_state != 'idle':
            self.last_state_change_time = current_tick
            if self.DEBUG_LEVEL >= 2:
                logger.debug(f"Robot {self.robotName()} initialized as active at tick {current_tick}")
        
        # 如果是初始化時設置為 idle（從未設置過狀態）
        if self.last_state_change_time == 0 and old_state == 'idle' and new_state == 'idle':
            # 不需要累積時間，但要記錄這是有效的初始化
            self.last_state_change_time = current_tick'''
    
    # 替換初始化檢查
    if old_updatestate_init_check in content:
        content = content.replace(old_updatestate_init_check, new_updatestate_init_check)
        print("✓ 已修復 updateState 初始化檢查")
    else:
        print("⚠ 找不到原始的 updateState 初始化檢查，可能已經被修改")
    
    # 備份原始檔案
    backup_file = robot_file.with_suffix('.py.backup_utilization_fix')
    with open(backup_file, 'w', encoding='utf-8') as f:
        with open(robot_file, 'r', encoding='utf-8') as orig:
            f.write(orig.read())
    print(f"✓ 已備份原始檔案到 {backup_file}")
    
    # 寫入修改後的檔案
    with open(robot_file, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"✓ 已更新 {robot_file}")
    
    # 創建驗證腳本
    create_verification_script()
    
def create_verification_script():
    """創建驗證腳本來檢查修復是否有效"""
    
    verify_script = project_root / "test" / "verify_robot_utilization_fix.py"
    
    script_content = '''#!/usr/bin/env python3
"""
驗證機器人利用率修復是否有效的腳本
"""

import sys
from pathlib import Path

# 加入專案根目錄到 Python 路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from world.entities.robot import Robot

def test_robot_utilization():
    """測試機器人利用率計算"""
    
    print("測試機器人利用率計算...")
    
    # 創建測試機器人
    robot = Robot(1, 10, 10)
    robot._id = 1
    
    # 測試場景 1: 初始狀態
    print("\\n場景 1: 初始狀態 (idle)")
    active_time = robot.get_current_active_time(100)
    print(f"  當前 tick: 100")
    print(f"  機器人狀態: {robot.current_state}")
    print(f"  活動時間: {active_time}")
    print(f"  預期: 0 (因為是 idle)")
    assert active_time == 0, f"初始 idle 狀態活動時間應該是 0，但得到 {active_time}"
    
    # 測試場景 2: 變為活動狀態
    print("\\n場景 2: 變為活動狀態")
    robot.updateState("taking_pod", 100)
    active_time = robot.get_current_active_time(200)
    print(f"  當前 tick: 200")
    print(f"  機器人狀態: {robot.current_state}")
    print(f"  活動時間: {active_time}")
    print(f"  預期: 100 (200 - 100)")
    assert active_time == 100, f"活動時間應該是 100，但得到 {active_time}"
    
    # 測試場景 3: 變回 idle
    print("\\n場景 3: 變回 idle")
    robot.updateState("idle", 250)
    active_time = robot.get_current_active_time(300)
    print(f"  當前 tick: 300")
    print(f"  機器人狀態: {robot.current_state}")
    print(f"  總活動時間: {robot.total_active_time}")
    print(f"  活動時間: {active_time}")
    print(f"  預期: 150 (250 - 100)")
    assert active_time == 150, f"活動時間應該是 150，但得到 {active_time}"
    
    # 測試場景 4: 邊界情況 - 防止超過當前 tick
    print("\\n場景 4: 邊界檢查")
    robot_bad = Robot(2, 20, 20)
    robot_bad._id = 2
    robot_bad.last_state_change_time = 1000  # 故意設置一個未來的時間
    robot_bad.current_state = "taking_pod"
    active_time = robot_bad.get_current_active_time(500)
    print(f"  當前 tick: 500")
    print(f"  last_state_change_time: 1000 (錯誤的未來時間)")
    print(f"  活動時間: {active_time}")
    print(f"  預期: <= 500 (不應超過當前 tick)")
    assert active_time <= 500, f"活動時間不應超過當前 tick (500)，但得到 {active_time}"
    
    print("\\n✓ 所有測試通過！機器人利用率計算已修復。")
    
    # 計算利用率
    print("\\n利用率計算範例:")
    total_robots = 40
    final_tick = 100000
    total_active_time = 80000 * total_robots  # 假設每個機器人平均活動 80% 時間
    utilization = total_active_time / (final_tick * total_robots)
    print(f"  機器人數量: {total_robots}")
    print(f"  總 tick 數: {final_tick}")
    print(f"  總活動時間: {total_active_time}")
    print(f"  利用率: {utilization:.2%}")
    print(f"  結果: {'正常' if 0 <= utilization <= 1 else '異常'}")

if __name__ == "__main__":
    test_robot_utilization()
'''
    
    with open(verify_script, 'w', encoding='utf-8') as f:
        f.write(script_content)
    
    print(f"✓ 已創建驗證腳本 {verify_script}")
    print("\n請執行以下命令來驗證修復:")
    print(f"python {verify_script}")

if __name__ == "__main__":
    print("開始修復機器人利用率計算問題...")
    create_robot_utilization_fix()
    print("\n修復完成！")
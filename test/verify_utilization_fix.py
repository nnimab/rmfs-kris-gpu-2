#!/usr/bin/env python3
"""
驗證機器人利用率計算修復
"""

import sys
from pathlib import Path

# 加入專案根目錄到 Python 路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from world.entities.robot import Robot


def test_utilization_calculation():
    """測試利用率計算的各種情況"""
    print("=== 測試機器人利用率計算 ===\n")
    
    # 測試案例 1: 機器人從開始就一直活動
    print("測試案例 1: 機器人從開始就一直活動")
    robot1 = Robot(1, 10, 10)
    robot1.current_state = 'moving'
    robot1.last_state_change_time = 0  # 從未記錄過狀態變化
    
    # 在 tick 1000 計算活動時間
    active_time = robot1.get_current_active_time(1000)
    print(f"  當前 tick: 1000")
    print(f"  last_state_change_time: {robot1.last_state_change_time}")
    print(f"  total_active_time: {robot1.total_active_time}")
    print(f"  計算的活動時間: {active_time}")
    print(f"  利用率: {active_time / 1000:.2%}\n")
    
    # 測試案例 2: 機器人在 tick 100 開始活動
    print("測試案例 2: 機器人在 tick 100 開始活動")
    robot2 = Robot(2, 20, 20)
    robot2.updateState('moving', 100)
    
    # 在 tick 1000 計算活動時間
    active_time = robot2.get_current_active_time(1000)
    print(f"  當前 tick: 1000")
    print(f"  last_state_change_time: {robot2.last_state_change_time}")
    print(f"  total_active_time: {robot2.total_active_time}")
    print(f"  計算的活動時間: {active_time}")
    print(f"  利用率: {active_time / 1000:.2%}\n")
    
    # 測試案例 3: 機器人有多次狀態切換
    print("測試案例 3: 機器人有多次狀態切換")
    robot3 = Robot(3, 30, 30)
    robot3.updateState('moving', 0)      # 開始活動
    robot3.updateState('idle', 200)      # 停止活動
    robot3.updateState('moving', 400)    # 再次活動
    robot3.updateState('idle', 600)      # 再次停止
    robot3.updateState('moving', 800)    # 最後一次活動
    
    # 在 tick 1000 計算活動時間
    active_time = robot3.get_current_active_time(1000)
    print(f"  當前 tick: 1000")
    print(f"  last_state_change_time: {robot3.last_state_change_time}")
    print(f"  total_active_time: {robot3.total_active_time}")
    print(f"  計算的活動時間: {active_time}")
    print(f"  利用率: {active_time / 1000:.2%}")
    print(f"  預期活動時間: {200 + 200 + 200} = 600")
    print(f"  是否正確: {'YES' if active_time == 600 else 'NO'}")
    
    # 測試案例 4: 邊界情況 - 負數防護
    print("測試案例 4: 邊界情況測試")
    robot4 = Robot(4, 40, 40)
    robot4.current_state = 'moving'
    robot4.last_state_change_time = 2000  # 故意設置一個未來的時間
    
    # 在 tick 1000 計算活動時間（應該返回 0，而不是負數）
    active_time = robot4.get_current_active_time(1000)
    print(f"  當前 tick: 1000")
    print(f"  last_state_change_time: {robot4.last_state_change_time} (未來時間)")
    print(f"  計算的活動時間: {active_time}")
    print(f"  是否為非負數: {'YES' if active_time >= 0 else 'NO'}")
    
    print("=== 測試完成 ===")


def analyze_baseline_results():
    """分析基準測試結果中的利用率問題"""
    print("\n=== 分析基準測試結果 ===\n")
    
    # 示例數據（來自之前的分析）
    print("問題數據示例:")
    print("  機器人數: 30")
    print("  評估 ticks: 10000")
    print("  total_robot_active_time: -150000 (負數)")
    print("  計算的利用率: -150000 / (10000 * 30) = -0.5\n")
    
    print("可能的原因:")
    print("1. last_state_change_time 未正確初始化")
    print("2. 機器人從未進入過 idle 狀態，導致 total_active_time 從未更新")
    print("3. 時間計算邏輯有錯誤\n")
    
    print("修復後的行為:")
    print("1. 如果機器人從未記錄狀態變化，假設從 tick 0 開始活動")
    print("2. 確保活動時間計算永遠不會返回負數")
    print("3. 防禦性編程：檢查計算的時間差是否為正數")


if __name__ == '__main__':
    test_utilization_calculation()
    analyze_baseline_results()
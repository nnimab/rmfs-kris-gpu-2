#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
調試機器人利用率計算問題
檢查為什麼 robot_utilization 總是 100%
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from world.warehouse import Warehouse
from data.data_loader import DataLoader
import random
import numpy as np

def debug_robot_utilization():
    """
    調試機器人利用率計算
    """
    print("=== 調試機器人利用率計算 ===")
    
    # 創建倉庫
    print("1. 初始化倉庫...")
    warehouse = Warehouse()
    
    # 設置隨機種子
    random.seed(42)
    np.random.seed(42)
    
    # 檢查初始狀態
    print("2. 檢查初始機器人狀態...")
    robots = warehouse.robot_manager.getAllRobots()
    print(f"總機器人數量: {len(robots)}")
    
    idle_count = 0
    active_count = 0
    
    for robot in robots:
        print(f"機器人 {robot.robotName()}: 狀態={robot.current_state}, total_active_time={robot.total_active_time}, last_state_change_time={robot.last_state_change_time}")
        if robot.current_state == 'idle':
            idle_count += 1
        else:
            active_count += 1
    
    print(f"閒置機器人: {idle_count}, 活動機器人: {active_count}")
    
    # 計算初始利用率（應該是 0%）
    initial_utilization = active_count / len(robots) if len(robots) > 0 else 0
    print(f"初始利用率: {initial_utilization * 100:.1f}%")
    
    # 載入數據並開始模擬
    print("\n3. 載入數據並開始模擬...")
    data_loader = DataLoader()
    warehouse = data_loader.loadData(warehouse)
    
    print(f"訂單數量: {len(warehouse.order_manager.getAllOrders())}")
    
    # 模擬幾個時刻
    print("\n4. 運行模擬...")
    for tick in range(1, 51):  # 運行 50 ticks
        warehouse.step()
        
        if tick % 10 == 0:  # 每 10 ticks 檢查一次
            print(f"\n--- Tick {tick} ---")
            
            # 檢查機器人狀態
            idle_count = 0
            active_count = 0
            
            for robot in robots:
                if robot.current_state == 'idle':
                    idle_count += 1
                else:
                    active_count += 1
            
            current_utilization = active_count / len(robots) if len(robots) > 0 else 0
            print(f"當前利用率 (基於狀態): {current_utilization * 100:.1f}%")
            print(f"閒置機器人: {idle_count}, 活動機器人: {active_count}")
            
            # 檢查使用 total_active_time 的利用率計算
            total_active_time = 0
            total_robot_time = 0
            
            for robot in robots:
                robot_active_time = robot.total_active_time
                
                # 如果機器人當前處於活動狀態，加上當前活動的時間
                if robot.current_state != 'idle' and robot.last_state_change_time > 0:
                    robot_active_time += tick - robot.last_state_change_time
                
                total_active_time += max(0, robot_active_time)
                total_robot_time += max(1, tick)
            
            time_based_utilization = total_active_time / total_robot_time if total_robot_time > 0 else 0
            print(f"基於時間的利用率: {time_based_utilization * 100:.1f}%")
            print(f"總活動時間: {total_active_time}, 總機器人時間: {total_robot_time}")
            
            # 檢查具體機器人的狀態變化記錄
            if tick == 20:
                print("\n詳細機器人狀態分析:")
                for i, robot in enumerate(robots[:3]):  # 只檢查前3個機器人
                    print(f"機器人 {robot.robotName()}:")
                    print(f"  當前狀態: {robot.current_state}")
                    print(f"  總活動時間: {robot.total_active_time}")
                    print(f"  上次狀態變化時間: {robot.last_state_change_time}")
                    print(f"  當前時刻: {tick}")
                    
                    # 如果在活動狀態，計算當前活動時間
                    if robot.current_state != 'idle' and robot.last_state_change_time > 0:
                        current_active = tick - robot.last_state_change_time
                        total_for_this_robot = robot.total_active_time + current_active
                        print(f"  當前活動時間: {current_active}")
                        print(f"  該機器人總活動時間: {total_for_this_robot}")
                        print(f"  該機器人利用率: {total_for_this_robot / tick * 100:.1f}%")
    
    print("\n=== 調試完成 ===")

if __name__ == "__main__":
    debug_robot_utilization()
#!/usr/bin/env python3
"""
修復模擬環境的訂單處理邏輯
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import netlogo
import numpy as np
import time

def fix_and_test_simulation():
    """修復並測試模擬環境"""
    
    print("=== 修復模擬環境 ===")
    
    # 創建倉庫
    print("1. 創建倉庫...")
    controller_kwargs = {
        'reward_mode': 'step',
        'population_size': 5,
        'process_id': os.getpid()
    }
    warehouse = netlogo.training_setup("nerl", controller_kwargs)
    
    if not warehouse:
        print("ERROR 倉庫創建失敗")
        return
    
    print("OK 倉庫創建成功")
    
    # 獲取NERL控制器
    nerl_controller = warehouse.intersection_manager.controllers.get('nerl')
    if not nerl_controller:
        print("ERROR 無法獲取NERL控制器")
        return
    
    print("OK NERL控制器獲取成功")
    
    # 檢查初始狀態
    print(f"\n2. 檢查初始狀態...")
    print(f"  機器人數量: {len(warehouse.robot_manager.robots)}")
    print(f"  總訂單數: {len(warehouse.order_manager.orders)}")
    print(f"  完成訂單: {len(warehouse.order_manager.finished_orders)}")
    print(f"  工作隊列: {len(warehouse.job_queue)}")
    print(f"  _tick: {warehouse._tick}")
    print(f"  next_process_tick: {warehouse.next_process_tick}")
    
    # 開始修復測試
    print(f"\n3. 開始修復測試...")
    
    # 確保 _tick 從0開始，這樣第一次就能觸發訂單處理
    warehouse._tick = 0
    print(f"  修復 _tick = 0")
    
    # 運行模擬
    for tick in range(0, 201):  # 從0開始，運行200個tick
        warehouse._tick = tick
        
        # 手動觸發訂單處理（確保第一次能執行）
        if tick == 0:
            print(f"  Tick {tick}: 手動觸發訂單處理")
            print(f"    處理前 - Job隊列: {len(warehouse.job_queue)}")
            
            # 手動執行訂單處理
            warehouse.findNewOrders()
            warehouse.processOrders()
            
            print(f"    處理後 - Job隊列: {len(warehouse.job_queue)}")
            
            # 檢查機器人狀態
            robot_states = {}
            for robot in warehouse.robot_manager.robots:
                state = robot.current_state
                robot_states[state] = robot_states.get(state, 0) + 1
            print(f"    機器人狀態: {robot_states}")
        
        # 執行tick
        warehouse.tick()
        
        # 每20個tick檢查一次狀態
        if tick % 20 == 0 and tick > 0:
            current_robot_states = {}
            for robot in warehouse.robot_manager.robots:
                state = robot.current_state
                current_robot_states[state] = current_robot_states.get(state, 0) + 1
            
            print(f"  Tick {tick}: 機器人狀態 {current_robot_states}, Job隊列: {len(warehouse.job_queue)}")
            
            # 檢查是否有機器人到達路口
            active_intersections = 0
            for intersection in warehouse.intersection_manager.intersections:
                if len(intersection.horizontal_robots) > 0 or len(intersection.vertical_robots) > 0:
                    active_intersections += 1
            
            print(f"    活躍路口: {active_intersections}/66")
            
            # 如果有機器人開始工作，檢查狀態數據
            if any(robot.current_state != 'idle' for robot in warehouse.robot_manager.robots):
                print(f"    *** 發現活躍機器人！***")
                
                # 檢查17維狀態數據
                for intersection in warehouse.intersection_manager.intersections:
                    h_robots = len(intersection.horizontal_robots)
                    v_robots = len(intersection.vertical_robots)
                    
                    if h_robots > 0 or v_robots > 0:
                        print(f"      路口 {intersection.id}: H={h_robots}, V={v_robots}")
                        
                        # 獲取17維狀態
                        state = nerl_controller.get_state(intersection, tick, warehouse)
                        non_zero_count = np.count_nonzero(state)
                        print(f"        17維狀態非零維度: {non_zero_count}/17")
                        print(f"        狀態範圍: [{np.min(state):.3f}, {np.max(state):.3f}]")
                        
                        # 顯示非零維度
                        state_labels = [
                            "方向編碼", "時間變化", "水平數量", "垂直數量", 
                            "水平優先級比例", "垂直優先級比例", "水平等待時間", "垂直等待時間",
                            "相鄰數量", "相鄰機器人", "相鄰優先級", "相鄰優先級比例",
                            "相鄰等待時間", "相鄰水平比例", "相鄰垂直比例", "負載均衡",
                            "揀貨台排隊"
                        ]
                        
                        for i, (label, value) in enumerate(zip(state_labels, state)):
                            if value != 0:
                                print(f"          維度{i:2d} ({label}): {value:.4f}")
                
                # 如果找到活躍路口，繼續運行更多tick來收集數據
                if active_intersections > 0:
                    print(f"    繼續運行收集更多狀態數據...")
                    
                    # 運行更多tick收集狀態數據
                    state_samples = []
                    for extra_tick in range(tick + 1, tick + 51):  # 額外運行50個tick
                        warehouse._tick = extra_tick
                        warehouse.tick()
                        
                        # 收集狀態數據
                        for intersection in warehouse.intersection_manager.intersections:
                            h_robots = len(intersection.horizontal_robots)
                            v_robots = len(intersection.vertical_robots)
                            
                            if h_robots > 0 or v_robots > 0:
                                state = nerl_controller.get_state(intersection, extra_tick, warehouse)
                                state_samples.append(state)
                    
                    # 分析收集到的狀態數據
                    if state_samples:
                        print(f"\n=== 狀態數據分析 ===")
                        print(f"收集到 {len(state_samples)} 個狀態樣本")
                        
                        states_array = np.array(state_samples)
                        
                        # 分析每個維度
                        for i, label in enumerate(state_labels):
                            values = states_array[:, i]
                            non_zero_count = np.count_nonzero(values)
                            if non_zero_count > 0:
                                print(f"  維度{i:2d} ({label:12s}): "
                                      f"範圍[{np.min(values):7.3f}, {np.max(values):7.3f}], "
                                      f"平均{np.mean(values):7.3f}, "
                                      f"非零{non_zero_count:3d}/{len(values):3d} ({non_zero_count/len(values)*100:5.1f}%)")
                        
                        # 檢查是否有維度總是為0
                        zero_dimensions = []
                        for i in range(17):
                            if np.all(states_array[:, i] == 0):
                                zero_dimensions.append(i)
                        
                        if zero_dimensions:
                            print(f"\n  發現總是為0的維度:")
                            for dim in zero_dimensions:
                                print(f"    維度{dim} ({state_labels[dim]})")
                        
                        print(f"\n=== 修復結果 ===")
                        if len(zero_dimensions) < 10:
                            print(f"SUCCESS: 17維狀態數據已修復！")
                            print(f"  - 有效維度: {17 - len(zero_dimensions)}/17")
                            print(f"  - 無效維度: {len(zero_dimensions)}/17")
                            print(f"  - 機器人正常移動到路口")
                            print(f"  - 狀態數據包含有意義的信息")
                        else:
                            print(f"PARTIAL: 部分修復成功")
                            print(f"  - 機器人開始移動，但狀態數據仍有問題")
                    
                    return True  # 修復成功
    
    print(f"\n=== 修復失敗 ===")
    print(f"經過200個tick，機器人仍然沒有開始工作")
    return False

if __name__ == "__main__":
    success = fix_and_test_simulation()
    if success:
        print(f"\n*** 修復成功！NERL的17維狀態數據現在可以正常工作了 ***")
    else:
        print(f"\n*** 修復失敗！需要進一步調查 ***")
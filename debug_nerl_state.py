#!/usr/bin/env python3
"""
檢查 NERL 控制器的17維狀態數據是否真的有效
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from world.warehouse import Warehouse
from ai.controllers.nerl_controller import NEController
import numpy as np
import time
import netlogo

def debug_nerl_state():
    """檢查 NERL 控制器的狀態數據"""
    
    print("=== NERL 17維狀態數據檢查 ===")
    
    # 創建倉庫和控制器 - 使用正確的初始化方法
    print("使用 training_setup 創建倉庫...")
    controller_kwargs = {
        'reward_mode': 'step',
        'population_size': 5,
        'process_id': os.getpid()
    }
    warehouse = netlogo.training_setup("nerl", controller_kwargs)
    
    if not warehouse:
        print("錯誤：無法創建倉庫")
        return
    
    # 從倉庫獲取NERL控制器
    nerl_controller = warehouse.intersection_manager.controllers.get('nerl')
    if not nerl_controller:
        print("錯誤：無法獲取NERL控制器")
        return
    
    # 運行一小段時間來收集數據
    print("運行模擬收集狀態數據...")
    
    state_samples = []
    tick_samples = []
    
    # 確保 _tick 從0開始，這樣第一次就能觸發訂單處理
    warehouse._tick = 0
    
    for tick in range(0, 2001):  # 從0開始運行2000個tick
        warehouse._tick = tick
        
        # 手動觸發訂單處理（確保第一次能執行）
        if tick == 0:
            warehouse.findNewOrders()
            warehouse.processOrders()
        
        warehouse.tick()
        
        # 每100個tick記錄一次狀態
        if tick % 100 == 0:
            print(f"\nTick {tick}:")
            
            # 檢查所有路口的狀態，但只詳細顯示有機器人的路口
            intersection_states = []
            active_intersections = []
            
            for intersection in warehouse.intersection_manager.intersections:
                # 檢查基本信息
                h_robots = len(intersection.horizontal_robots)
                v_robots = len(intersection.vertical_robots)
                
                # 獲取17維狀態
                state = nerl_controller.get_state(intersection, tick, warehouse)
                intersection_states.append(state)
                
                # 只顯示有機器人的路口
                if h_robots > 0 or v_robots > 0:
                    active_intersections.append(intersection)
                    print(f"  *** 活躍路口 {intersection.id} ({intersection.pos_x}, {intersection.pos_y}) ***")
                    print(f"    水平機器人: {h_robots}, 垂直機器人: {v_robots}")
                    print(f"    允許方向: {intersection.allowed_direction}")
                    print(f"    上次切換時間: {intersection.durationSinceLastChange(tick)}")
                    
                    # 機器人詳情
                    print(f"    水平機器人詳情:")
                    for robot_name, robot in intersection.horizontal_robots.items():
                        print(f"      {robot_name}: {robot.current_state}")
                    
                    print(f"    垂直機器人詳情:")
                    for robot_name, robot in intersection.vertical_robots.items():
                        print(f"      {robot_name}: {robot.current_state}")
                    
                    print(f"    17維狀態: {state}")
                    print(f"    狀態範圍: [{np.min(state):.3f}, {np.max(state):.3f}]")
                    print(f"    非零維度: {np.count_nonzero(state)}/17")
                    
                    # 詳細檢查每一維
                    state_labels = [
                        "方向編碼", "時間變化", "水平數量", "垂直數量", 
                        "水平優先級比例", "垂直優先級比例", "水平等待時間", "垂直等待時間",
                        "相鄰數量", "相鄰機器人", "相鄰優先級", "相鄰優先級比例",
                        "相鄰等待時間", "相鄰水平比例", "相鄰垂直比例", "負載均衡",
                        "揀貨台排隊"
                    ]
                    
                    for i, (label, value) in enumerate(zip(state_labels, state)):
                        if value != 0:
                            print(f"      維度{i:2d} ({label}): {value:.4f}")
                    
                    state_samples.append(state)
                    tick_samples.append(tick)
            
            # 顯示活躍路口數量
            print(f"  活躍路口數量: {len(active_intersections)}/66")
            
            # 顯示機器人總體狀態
            print(f"  機器人狀態分佈:")
            robot_states = {}
            for robot in warehouse.robot_manager.robots:
                state = robot.current_state
                robot_states[state] = robot_states.get(state, 0) + 1
            for state, count in robot_states.items():
                print(f"    {state}: {count}")
            
            # 如果有活躍路口，顯示一些狀態統計
            if intersection_states:
                states_array = np.array(intersection_states)
                non_zero_counts = [np.count_nonzero(states_array[:, i]) for i in range(17)]
                print(f"  各維度非零路口數量: {non_zero_counts}")
                print(f"  各維度平均值: {np.mean(states_array, axis=0)}")
                print(f"  各維度最大值: {np.max(states_array, axis=0)}")
                
                # 如果找到活躍路口，提前結束
                if len(active_intersections) > 0:
                    print(f"  *** 發現活躍路口！在tick {tick} ***")
                    break
    
    print(f"\n=== 總結 ===")
    print(f"收集到 {len(state_samples)} 個有效狀態樣本")
    
    # 如果沒有找到有效樣本，說明問題很嚴重
    if len(state_samples) == 0:
        print("⚠️  致命問題：在整個2000 tick期間沒有找到任何機器人到達路口！")
        print("這說明：")
        print("1. 機器人沒有移動")
        print("2. 機器人沒有被分配到訂單")
        print("3. 路口檢測邏輯有問題")
        print("4. 模擬環境初始化有問題")
    
    if state_samples:
        # 轉換為numpy陣列進行分析
        states_array = np.array(state_samples)
        
        print(f"\n各維度統計:")
        state_labels = [
            "方向編碼", "時間變化", "水平數量", "垂直數量", 
            "水平優先級比例", "垂直優先級比例", "水平等待時間", "垂直等待時間",
            "相鄰數量", "相鄰機器人", "相鄰優先級", "相鄰優先級比例",
            "相鄰等待時間", "相鄰水平比例", "相鄰垂直比例", "負載均衡",
            "揀貨台排隊"
        ]
        
        for i, label in enumerate(state_labels):
            values = states_array[:, i]
            non_zero_count = np.count_nonzero(values)
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
            print(f"\n警告: 發現總是為0的維度:")
            for dim in zero_dimensions:
                print(f"    維度{dim} ({state_labels[dim]})")
        
        # 檢查是否有維度總是相同
        constant_dimensions = []
        for i in range(17):
            if np.std(states_array[:, i]) < 1e-6:
                constant_dimensions.append(i)
        
        if constant_dimensions:
            print(f"\n警告: 發現總是相同值的維度:")
            for dim in constant_dimensions:
                print(f"    維度{dim} ({state_labels[dim]}): {states_array[0, dim]:.6f}")
        
        # 檢查相鄰路口數據
        print(f"\n相鄰路口數據檢查:")
        print(f"  相鄰路口數量範圍: [{np.min(states_array[:, 8]):.3f}, {np.max(states_array[:, 8]):.3f}]")
        print(f"  相鄰機器人數量範圍: [{np.min(states_array[:, 9]):.3f}, {np.max(states_array[:, 9]):.3f}]")
        
        # 檢查揀貨台數據
        print(f"\n揀貨台數據檢查:")
        print(f"  揀貨台排隊範圍: [{np.min(states_array[:, 16]):.3f}, {np.max(states_array[:, 16]):.3f}]")
        
        # 檢查歸一化是否有問題
        print(f"\n歸一化檢查:")
        for i in range(17):
            values = states_array[:, i]
            if np.max(np.abs(values)) > 1.0:
                print(f"  警告: 維度{i} ({state_labels[i]}) 超出歸一化範圍: {np.max(np.abs(values)):.3f}")
        
    else:
        print("警告: 沒有收集到任何有效狀態樣本！")
    
    # 檢查倉庫基本數據
    print(f"\n=== 倉庫基本數據檢查 ===")
    print(f"機器人數量: {len(warehouse.robot_manager.robots)}")
    print(f"路口數量: {len(warehouse.intersection_manager.intersections)}")
    print(f"訂單總數: {len(warehouse.order_manager.orders)}")
    print(f"完成訂單: {len(warehouse.order_manager.finished_orders)}")
    
    # 檢查機器人狀態
    if len(warehouse.robot_manager.robots) > 0:
        print(f"\n機器人狀態分佈:")
        robot_states = {}
        for robot in warehouse.robot_manager.robots:
            state = robot.current_state
            robot_states[state] = robot_states.get(state, 0) + 1
        for state, count in robot_states.items():
            print(f"  {state}: {count}")
    
    # 檢查路口狀態
    print(f"\n路口狀態檢查:")
    total_robots_at_intersections = 0
    for intersection in warehouse.intersection_manager.intersections:
        robot_count = len(intersection.horizontal_robots) + len(intersection.vertical_robots)
        total_robots_at_intersections += robot_count
        if robot_count > 0:
            print(f"  路口{intersection.id}: {robot_count} 機器人")
    print(f"  路口總機器人數: {total_robots_at_intersections}")
    
    # 檢查是否有揀貨台排隊屬性
    if hasattr(warehouse, 'picking_station_queue_length'):
        print(f"揀貨台排隊長度: {warehouse.picking_station_queue_length}")
    else:
        print("警告: 倉庫沒有 picking_station_queue_length 屬性")
    
    # 檢查相鄰路口管理器
    print(f"\n=== 相鄰路口管理器檢查 ===")
    for intersection in warehouse.intersection_manager.intersections[:3]:  # 只檢查前3個
        neighbors = warehouse.intersection_manager.get_neighboring_intersections(intersection)
        print(f"路口 {intersection.id}:")
        print(f"  相鄰路口數量: {neighbors['count']}")
        print(f"  相鄰機器人總數: {neighbors['total_robots']}")
        print(f"  相鄰優先級機器人: {neighbors['total_priority_robots']}")

if __name__ == "__main__":
    debug_nerl_state()
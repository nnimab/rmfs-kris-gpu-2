#!/usr/bin/env python3
"""
診斷模擬環境為什麼沒有正常運作
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import netlogo
import numpy as np
import time

def diagnose_simulation():
    """診斷模擬環境問題"""
    
    print("=== 模擬環境診斷 ===")
    
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
    
    # 檢查初始狀態
    print("\n2. 檢查初始狀態...")
    print(f"  機器人數量: {len(warehouse.robot_manager.robots)}")
    print(f"  路口數量: {len(warehouse.intersection_manager.intersections)}")
    print(f"  總訂單數: {len(warehouse.order_manager.orders)}")
    print(f"  完成訂單: {len(warehouse.order_manager.finished_orders)}")
    print(f"  工作隊列: {len(warehouse.job_queue)}")
    
    # 檢查機器人狀態
    print("\n3. 檢查機器人狀態...")
    robot_states = {}
    for robot in warehouse.robot_manager.robots:
        state = robot.current_state
        robot_states[state] = robot_states.get(state, 0) + 1
    
    for state, count in robot_states.items():
        print(f"  {state}: {count}")
    
    # 檢查前幾個機器人的詳細信息
    print("\n4. 檢查前3個機器人的詳細信息...")
    for i, robot in enumerate(warehouse.robot_manager.robots[:3]):
        print(f"  機器人{i} ({robot.robotName()}):")
        print(f"    狀態: {robot.current_state}")
        print(f"    位置: ({robot.pos_x}, {robot.pos_y})")
        print(f"    有Pod: {hasattr(robot, 'pod') and robot.pod is not None}")
        print(f"    當前Job: {getattr(robot, 'current_job', 'None')}")
        print(f"    是否有路徑: {hasattr(robot, 'route_stop_points') and robot.route_stop_points}")
    
    # 檢查訂單狀態
    print("\n5. 檢查訂單狀態...")
    if warehouse.order_manager.orders:
        print(f"  前3個訂單:")
        orders_list = warehouse.order_manager.orders if isinstance(warehouse.order_manager.orders, list) else list(warehouse.order_manager.orders.values())
        for i, order in enumerate(orders_list[:3]):
            print(f"    訂單{i} (ID: {order.id}):")
            print(f"      到達時間: {order.order_arrival}")
            print(f"      狀態: {order.status}")
            print(f"      分配站台: {order.station_id}")
            print(f"      SKU數量: {len(order.skus)}")
    
    # 檢查job_queue
    print("\n6. 檢查job_queue...")
    if warehouse.job_queue:
        print(f"  前3個Job:")
        for i, job in enumerate(warehouse.job_queue[:3]):
            print(f"    Job{i}: {job}")
    else:
        print("  Job隊列為空")
    
    # 檢查倉庫配置
    print("\n7. 檢查倉庫配置...")
    print(f"  next_process_tick: {warehouse.next_process_tick}")
    print(f"  _tick: {warehouse._tick}")
    print(f"  update_intersection_using_RL: {warehouse.update_intersection_using_RL}")
    
    # 檢查站台
    print("\n8. 檢查站台...")
    stations = warehouse.station_manager.getAllStations()
    if stations:
        print(f"  站台數量: {len(stations)}")
        picker_stations = [s for s in stations if s.isPickerStation()]
        print(f"  揀貨站台數量: {len(picker_stations)}")
        
        for i, station in enumerate(picker_stations[:3]):
            print(f"    站台{i} (ID: {station.id}):")
            print(f"      位置: ({station.pos_x}, {station.pos_y})")
            print(f"      機器人數量: {len(station.robot_ids)}")
            print(f"      是否可用: {getattr(station, 'available', 'N/A')}")
    
    # 嘗試運行一些tick，看看是否有變化
    print("\n9. 運行模擬測試...")
    
    for tick in range(1, 101):
        warehouse._tick = tick
        
        # 檢查是否需要處理訂單
        if tick == warehouse.next_process_tick:
            print(f"  Tick {tick}: 需要處理訂單")
            print(f"    處理前job_queue大小: {len(warehouse.job_queue)}")
        
        warehouse.tick()
        
        # 每10個tick檢查一次狀態變化
        if tick % 10 == 0:
            current_robot_states = {}
            for robot in warehouse.robot_manager.robots:
                state = robot.current_state
                current_robot_states[state] = current_robot_states.get(state, 0) + 1
            
            print(f"  Tick {tick}: 機器人狀態 {current_robot_states}, Job隊列: {len(warehouse.job_queue)}")
            
            # 如果有狀態變化，顯示詳細信息
            if current_robot_states != robot_states:
                print(f"    OK 機器人狀態發生變化！")
                robot_states = current_robot_states
                
                # 顯示非idle機器人的詳細信息
                for robot in warehouse.robot_manager.robots:
                    if robot.current_state != 'idle':
                        print(f"    活躍機器人 {robot.robotName()}: {robot.current_state}")
                        print(f"      位置: ({robot.pos_x}, {robot.pos_y})")
                        print(f"      有Pod: {hasattr(robot, 'pod') and robot.pod is not None}")
                        break
                
                # 如果找到活躍機器人，提前結束
                if any(robot.current_state != 'idle' for robot in warehouse.robot_manager.robots):
                    print(f"    *** 發現活躍機器人！在tick {tick} ***")
                    break
    
    # 最終狀態檢查
    print("\n10. 最終狀態檢查...")
    final_robot_states = {}
    for robot in warehouse.robot_manager.robots:
        state = robot.current_state
        final_robot_states[state] = final_robot_states.get(state, 0) + 1
    
    print(f"  最終機器人狀態: {final_robot_states}")
    print(f"  最終Job隊列大小: {len(warehouse.job_queue)}")
    print(f"  最終完成訂單: {len(warehouse.order_manager.finished_orders)}")
    
    # 判斷問題類型
    print("\n=== 問題診斷結果 ===")
    if len(warehouse.job_queue) == 0:
        print("ERROR 問題：沒有產生任何Job")
        print("可能原因：")
        print("  1. 訂單處理邏輯有問題")
        print("  2. findNewOrders() 沒有正常運作")
        print("  3. processOrders() 沒有正常運作")
        print("  4. 訂單數據有問題")
    elif all(robot.current_state == 'idle' for robot in warehouse.robot_manager.robots):
        print("ERROR 問題：有Job但機器人沒有被分配")
        print("可能原因：")
        print("  1. 機器人分配邏輯有問題")
        print("  2. Job分配邏輯有問題")
        print("  3. 機器人狀態管理有問題")
    else:
        print("OK 機器人開始工作，但可能有其他問題")
        print("需要進一步檢查路口到達邏輯")

if __name__ == "__main__":
    diagnose_simulation()
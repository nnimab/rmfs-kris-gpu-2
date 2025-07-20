#!/usr/bin/env python3
"""
檢查揀貨台排隊長度為0的問題
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import netlogo
import numpy as np
import time

def debug_picking_station():
    """調試揀貨台排隊長度計算"""
    
    print("=== 揀貨台排隊長度調試 ===")
    
    # 創建倉庫
    print("創建倉庫...")
    controller_kwargs = {
        'reward_mode': 'step',
        'population_size': 5,
        'process_id': os.getpid()
    }
    warehouse = netlogo.training_setup("nerl", controller_kwargs)
    
    if not warehouse:
        print("錯誤：無法創建倉庫")
        return
    
    print("倉庫創建成功")
    
    # 確保 _tick 從0開始
    warehouse._tick = 0
    
    # 運行一些tick讓機器人開始工作
    print("運行模擬讓機器人開始工作...")
    for tick in range(0, 201):
        warehouse._tick = tick
        
        # 手動觸發訂單處理
        if tick == 0:
            warehouse.findNewOrders()
            warehouse.processOrders()
        
        warehouse.tick()
        
        # 每20個tick檢查一次
        if tick % 20 == 0:
            print(f"\\nTick {tick}:")
            print(f"  揀貨台排隊長度: {warehouse.picking_station_queue_length}")
            
            # 檢查所有揀貨台的詳細信息
            print("  揀貨台詳細信息:")
            total_robots_in_stations = 0
            for station in warehouse.station_manager.getAllStations():
                if station.isPickerStation():
                    robot_count = len(station.robot_ids)
                    total_robots_in_stations += robot_count
                    print(f"    揀貨台 {station.id}: {robot_count} 個機器人")
                    if robot_count > 0:
                        print(f"      機器人ID: {list(station.robot_ids.keys())}")
            
            print(f"  總計在揀貨台的機器人: {total_robots_in_stations}")
            
            # 檢查機器人狀態
            robot_states = {}
            robots_at_station = []
            for robot in warehouse.robot_manager.robots:
                state = robot.current_state
                robot_states[state] = robot_states.get(state, 0) + 1
                
                # 檢查是否有機器人在揀貨台相關狀態
                if state in ['station_processing', 'returning_pod']:
                    robots_at_station.append(robot.robotName())
            
            print(f"  機器人狀態分佈: {robot_states}")
            if robots_at_station:
                print(f"  在揀貨台的機器人: {robots_at_station}")
            
            # 檢查job queue
            print(f"  Job隊列長度: {len(warehouse.job_queue)}")
            
            # 檢查訂單狀態
            print(f"  未完成訂單數: {len(warehouse.order_manager.unfinished_orders)}")
            print(f"  已完成訂單數: {len(warehouse.order_manager.finished_orders)}")
            
            # 如果揀貨台排隊長度不為0，顯示詳細信息
            if warehouse.picking_station_queue_length > 0:
                print(f"  *** 發現揀貨台排隊！長度: {warehouse.picking_station_queue_length} ***")
                for station in warehouse.station_manager.getAllStations():
                    if station.isPickerStation() and len(station.robot_ids) > 0:
                        print(f"    揀貨台 {station.id} 詳細:")
                        print(f"      位置: ({station.pos_x}, {station.pos_y})")
                        print(f"      機器人數: {len(station.robot_ids)}")
                        print(f"      訂單數: {len(station.orders)}")
                        print(f"      incoming_pod: {station.incoming_pod}")
                break
    
    print("\\n=== 揀貨台和機器人關係檢查 ===")
    
    # 檢查揀貨台數量和類型
    picking_stations = []
    for station in warehouse.station_manager.getAllStations():
        if station.isPickerStation():
            picking_stations.append(station)
    
    print(f"揀貨台數量: {len(picking_stations)}")
    for station in picking_stations:
        print(f"  揀貨台 {station.id}: 位置({station.pos_x}, {station.pos_y})")
    
    # 檢查機器人工作流程
    print("\\n機器人工作流程分析:")
    for robot in warehouse.robot_manager.robots:
        if robot.job is not None:
            print(f"  機器人 {robot.robotName()}:")
            print(f"    當前狀態: {robot.current_state}")
            print(f"    任務: {robot.job}")
            print(f"    任務站點ID: {robot.job.station_id}")
            print(f"    任務是否完成: {robot.job.is_finished}")
            break  # 只顯示第一個有任務的機器人
    
    # 檢查是否有機器人真正到達揀貨台
    print("\\n=== 機器人到達揀貨台檢查 ===")
    for station in picking_stations:
        if len(station.robot_ids) > 0:
            print(f"揀貨台 {station.id} 有 {len(station.robot_ids)} 個機器人:")
            for robot_id in station.robot_ids.keys():
                print(f"  - {robot_id}")
        else:
            print(f"揀貨台 {station.id} 沒有機器人")

if __name__ == "__main__":
    debug_picking_station()
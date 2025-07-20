#!/usr/bin/env python3
"""
檢查機器人路線進度和狀態轉換
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import netlogo
import numpy as np
import time

def debug_robot_routes():
    """調試機器人路線和狀態轉換"""
    
    print("=== 機器人路線進度調試 ===")
    
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
    print("運行模擬...")
    for tick in range(0, 301):
        warehouse._tick = tick
        
        # 手動觸發訂單處理
        if tick == 0:
            warehouse.findNewOrders()
            warehouse.processOrders()
        
        warehouse.tick()
        
        # 每50個tick檢查一次
        if tick % 50 == 0:
            print(f"\\nTick {tick}:")
            print(f"  揀貨台排隊長度: {warehouse.picking_station_queue_length}")
            
            # 檢查機器人狀態和路線進度
            robot_states = {}
            robots_with_jobs = []
            
            for robot in warehouse.robot_manager.robots:
                state = robot.current_state
                robot_states[state] = robot_states.get(state, 0) + 1
                
                # 檢查有任務的機器人
                if robot.job is not None:
                    route_progress = len(robot.route_stop_points) if robot.route_stop_points else 0
                    robots_with_jobs.append({
                        'name': robot.robotName(),
                        'state': state,
                        'route_points_left': route_progress,
                        'position': (robot.pos_x, robot.pos_y),
                        'station_id': robot.job.station_id,
                        'job_finished': robot.job.is_finished
                    })
            
            print(f"  機器人狀態分佈: {robot_states}")
            print(f"  有任務的機器人: {len(robots_with_jobs)}")
            
            # 顯示前5個機器人的詳細信息
            if robots_with_jobs:
                print("  機器人詳細信息（前5個）:")
                for i, robot_info in enumerate(robots_with_jobs[:5]):
                    print(f"    {robot_info['name']}: 狀態={robot_info['state']}, " +
                          f"剩餘路線點={robot_info['route_points_left']}, " +
                          f"位置=({robot_info['position'][0]:.1f}, {robot_info['position'][1]:.1f}), " +
                          f"目標站台={robot_info['station_id']}")
                    
                    # 如果路線點為0，說明應該進入下一個狀態
                    if robot_info['route_points_left'] == 0 and robot_info['state'] == 'delivering_pod':
                        print(f"      *** 警告：{robot_info['name']} 應該進入 station_processing 狀態！***")
            
            # 檢查是否有機器人到達揀貨台
            picking_stations = [s for s in warehouse.station_manager.getAllStations() if s.isPickerStation()]
            stations_with_robots = []
            for station in picking_stations:
                if len(station.robot_ids) > 0:
                    stations_with_robots.append({
                        'id': station.id,
                        'robot_count': len(station.robot_ids),
                        'robot_names': list(station.robot_ids.keys())
                    })
            
            if stations_with_robots:
                print(f"  揀貨台有機器人:")
                for station_info in stations_with_robots:
                    print(f"    站台 {station_info['id']}: {station_info['robot_count']} 個機器人 {station_info['robot_names']}")
            
            # 如果發現有機器人到達揀貨台，提前結束
            if warehouse.picking_station_queue_length > 0:
                print(f"  *** 發現揀貨台排隊！長度: {warehouse.picking_station_queue_length} ***")
                
                # 顯示詳細的維度16數據
                nerl_controller = warehouse.intersection_manager.controllers.get('nerl')
                if nerl_controller:
                    # 隨便選一個路口測試維度16
                    test_intersection = warehouse.intersection_manager.intersections[0]
                    state = nerl_controller.get_state(test_intersection, tick, warehouse)
                    print(f"  維度16（揀貨台排隊）: {state[16]}")
                
                break
    
    print(f"\\n=== 最終狀態檢查 ===")
    print(f"揀貨台排隊長度: {warehouse.picking_station_queue_length}")
    
    # 最終機器人狀態統計
    final_robot_states = {}
    for robot in warehouse.robot_manager.robots:
        state = robot.current_state
        final_robot_states[state] = final_robot_states.get(state, 0) + 1
    
    print(f"最終機器人狀態分佈: {final_robot_states}")
    
    # 檢查是否有機器人在站台處理中
    processing_robots = [r for r in warehouse.robot_manager.robots if r.current_state == 'station_processing']
    if processing_robots:
        print(f"在站台處理中的機器人: {len(processing_robots)}")
        for robot in processing_robots[:3]:  # 顯示前3個
            print(f"  {robot.robotName()}: 站台 {robot.job.station_id}")
    
    # 檢查揀貨台機器人ID
    for station in warehouse.station_manager.getAllStations():
        if station.isPickerStation() and len(station.robot_ids) > 0:
            print(f"站台 {station.id} 的機器人: {list(station.robot_ids.keys())}")

if __name__ == "__main__":
    debug_robot_routes()
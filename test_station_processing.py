#!/usr/bin/env python3
"""
測試機器人是否最終會到達station_processing狀態
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import netlogo
import time

def test_station_processing():
    """測試機器人到達station_processing狀態"""
    
    print("=== 測試機器人到達station_processing狀態 ===")
    
    # 創建倉庫
    controller_kwargs = {
        'reward_mode': 'step',
        'population_size': 5,
        'process_id': os.getpid()
    }
    warehouse = netlogo.training_setup("nerl", controller_kwargs)
    
    if not warehouse:
        print("錯誤：無法創建倉庫")
        return
    
    # 確保 _tick 從0開始
    warehouse._tick = 0
    
    # 運行更長時間，直到找到station_processing狀態
    max_ticks = 1000
    found_station_processing = False
    
    for tick in range(0, max_ticks):
        warehouse._tick = tick
        
        # 手動觸發訂單處理
        if tick == 0:
            warehouse.findNewOrders()
            warehouse.processOrders()
        
        warehouse.tick()
        
        # 每100個tick檢查一次
        if tick % 100 == 0:
            robot_states = {}
            for robot in warehouse.robot_manager.robots:
                state = robot.current_state
                robot_states[state] = robot_states.get(state, 0) + 1
            
            print(f"Tick {tick}: 機器人狀態 {robot_states}, 揀貨台排隊: {warehouse.picking_station_queue_length}")
            
            # 檢查是否有機器人在station_processing狀態
            if 'station_processing' in robot_states:
                found_station_processing = True
                print(f"*** 發現 station_processing 狀態！在 tick {tick} ***")
                print(f"揀貨台排隊長度: {warehouse.picking_station_queue_length}")
                
                # 顯示在station_processing狀態的機器人
                for robot in warehouse.robot_manager.robots:
                    if robot.current_state == 'station_processing':
                        print(f"  機器人 {robot.robotName()} 在站台 {robot.job.station_id} 處理中")
                
                # 檢查揀貨台的robot_ids
                for station in warehouse.station_manager.getAllStations():
                    if station.isPickerStation() and len(station.robot_ids) > 0:
                        print(f"  站台 {station.id} 的robot_ids: {list(station.robot_ids.keys())}")
                
                # 測試維度16
                nerl_controller = warehouse.intersection_manager.controllers.get('nerl')
                if nerl_controller:
                    test_intersection = warehouse.intersection_manager.intersections[0]
                    state = nerl_controller.get_state(test_intersection, tick, warehouse)
                    print(f"  維度16（揀貨台排隊）: {state[16]}")
                
                break
        
        # 檢查是否有機器人完成路線（route_stop_points為空）
        if tick % 50 == 0:
            robots_ready_to_advance = []
            for robot in warehouse.robot_manager.robots:
                if robot.current_state == 'delivering_pod' and robot.job is not None:
                    route_points = len(robot.route_stop_points) if robot.route_stop_points else 0
                    if route_points <= 1:  # 即將完成路線
                        robots_ready_to_advance.append({
                            'name': robot.robotName(),
                            'route_points': route_points,
                            'position': (robot.pos_x, robot.pos_y)
                        })
            
            if robots_ready_to_advance:
                print(f"  Tick {tick}: 即將完成路線的機器人:")
                for robot_info in robots_ready_to_advance:
                    print(f"    {robot_info['name']}: 剩餘 {robot_info['route_points']} 個路線點")
    
    if not found_station_processing:
        print(f"\\n運行了 {max_ticks} 個tick，沒有發現 station_processing 狀態")
        print("可能的原因：")
        print("1. 機器人路線太長，沒有在時間內到達")
        print("2. 機器人被卡在路口交通中")
        print("3. 路線計算有問題")
    
    return found_station_processing

if __name__ == "__main__":
    success = test_station_processing()
    if success:
        print("\\n*** 成功找到 station_processing 狀態，維度16應該可以工作了！***")
    else:
        print("\\n*** 需要進一步調查機器人路線問題 ***")
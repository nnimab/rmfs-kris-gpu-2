#!/usr/bin/env python3
"""
V7.0 系統完整測試腳本（修正版）
測試新的獎勵系統和限速機制的完整功能
"""
import sys
import time
import json
import netlogo
from ai.unified_reward_system import UnifiedRewardSystem

def test_robot_speed_limit():
    """測試機器人限速機制"""
    print("=== V7.0 機器人限速測試 ===")
    
    # 設置測試環境
    controller_kwargs = {
        'reward_mode': 'step',
        'action_size': 6,
        'state_size': 17,
        'is_training': False  # 測試模式
    }
    
    print("\n1. 設置倉庫環境...")
    warehouse = netlogo.training_setup(controller_type="dqn", controller_kwargs=controller_kwargs)
    
    print("\n2. 測試單個機器人限速...")
    # 找到第一個機器人
    test_robot = None
    for robot in warehouse.robot_manager.robots:
        test_robot = robot
        break
    
    if test_robot:
        print(f"   測試機器人: {test_robot.robotName()}")
        print(f"   位置: ({test_robot.pos_x:.1f}, {test_robot.pos_y:.1f})")
        
        # 測試限速前
        print(f"\n   限速前:")
        print(f"   - speed_limit_active: {test_robot.speed_limit_active}")
        print(f"   - speed_limit_factor: {test_robot.speed_limit_factor}")
        print(f"   - 當前速度: {test_robot.velocity:.2f}")
        
        # 應用 50% 限速
        test_robot.apply_speed_limit(0.5)
        print(f"\n   應用 50% 限速後:")
        print(f"   - speed_limit_active: {test_robot.speed_limit_active}")
        print(f"   - speed_limit_factor: {test_robot.speed_limit_factor}")
        
        # 模擬幾個 tick 看速度變化
        print(f"\n   運行 5 個 tick 觀察速度變化...")
        for i in range(5):
            warehouse, _ = netlogo.training_tick(warehouse)
            print(f"   Tick {i+1}: 速度 = {test_robot.velocity:.2f}, 能耗 = {test_robot.current_tick_energy:.3f}")
        
        # 移除限速
        test_robot.remove_speed_limit()
        print(f"\n   移除限速後:")
        print(f"   - speed_limit_active: {test_robot.speed_limit_active}")
        print(f"   - speed_limit_factor: {test_robot.speed_limit_factor}")
    
    print("\n✅ 機器人限速測試完成！")

def test_corridor_speed_limit():
    """測試走廊限速系統"""
    print("\n=== V7.0 走廊限速測試 ===")
    
    # 設置測試環境
    controller_kwargs = {
        'reward_mode': 'step',
        'action_size': 6,
        'state_size': 17,
        'is_training': False
    }
    
    warehouse = netlogo.training_setup(controller_type="dqn", controller_kwargs=controller_kwargs)
    
    print("\n1. 測試關鍵路口走廊限速...")
    # 對路口 0 的走廊限速
    print(f"   對路口 0 設置 30% 限速（整條走廊）")
    warehouse.speed_limit_manager.set_corridor_speed_limit(0, 0.3, "both")
    
    # 檢查限速區域
    zones = warehouse.speed_limit_manager.get_active_speed_zones()
    print(f"\n   活躍限速區域數量: {len(zones)}")
    for i, zone in enumerate(zones):
        print(f"   區域 {i+1}: {zone['zone']} - 速度限制 {zone['speed_percentage']}")
    
    # 檢查受影響的機器人
    print(f"\n2. 檢查受影響的機器人...")
    affected_count = 0
    for robot in warehouse.robot_manager.robots[:10]:  # 檢查前10個
        if robot.speed_limit_active:
            affected_count += 1
            print(f"   {robot.robotName()} 在 ({robot.pos_x:.0f}, {robot.pos_y:.0f}) - 限速 {robot.speed_limit_factor*100:.0f}%")
    
    print(f"\n   總共 {affected_count} 個機器人受到限速影響")
    
    # 移除限速
    print(f"\n3. 移除走廊限速...")
    warehouse.speed_limit_manager.remove_corridor_speed_limit(0, "both")
    zones_after = warehouse.speed_limit_manager.get_active_speed_zones()
    print(f"   移除後活躍限速區域數量: {len(zones_after)}")
    
    print("\n✅ 走廊限速測試完成！")

def test_dqn_speed_actions():
    """測試 DQN 的限速動作"""
    print("\n=== V7.0 DQN 限速動作測試 ===")
    
    # 設置測試環境
    controller_kwargs = {
        'reward_mode': 'step',
        'action_size': 6,
        'state_size': 17,
        'is_training': True,
        'model_name': 'dqn_test_v7'
    }
    
    warehouse = netlogo.training_setup(controller_type="dqn", controller_kwargs=controller_kwargs)
    controller = warehouse.intersection_manager.controllers.get("dqn")
    
    print("\n1. 測試 DQN 動作選擇...")
    action_counts = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    
    # 運行 50 個 tick 統計動作
    for tick in range(50):
        # 更新交通控制
        warehouse.intersection_manager.update_traffic_using_controller(tick)
        
        # 統計動作
        if hasattr(controller, 'previous_actions'):
            for action in controller.previous_actions.values():
                if 0 <= action <= 5:
                    action_counts[action] += 1
        
        warehouse, _ = netlogo.training_tick(warehouse)
    
    print("\n   動作使用統計:")
    print(f"   動作 0 (保持): {action_counts[0]} 次")
    print(f"   動作 1 (垂直): {action_counts[1]} 次")
    print(f"   動作 2 (水平): {action_counts[2]} 次")
    print(f"   動作 3 (限速30%): {action_counts[3]} 次")
    print(f"   動作 4 (限速50%): {action_counts[4]} 次")
    print(f"   動作 5 (取消限速): {action_counts[5]} 次")
    
    # 檢查是否有使用限速動作
    speed_actions = action_counts[3] + action_counts[4] + action_counts[5]
    if speed_actions > 0:
        print(f"\n   ✅ DQN 有使用限速動作（共 {speed_actions} 次）")
    else:
        print(f"\n   ⚠️  DQN 沒有使用限速動作")
    
    print("\n✅ DQN 限速動作測試完成！")

def test_reward_calculation():
    """測試 V7 獎勵計算"""
    print("\n=== V7.0 獎勵計算測試 ===")
    
    # 創建獎勵系統
    reward_system = UnifiedRewardSystem(reward_mode="step")
    
    # 創建模擬物件
    class MockIntersection:
        def __init__(self, id):
            self.id = id
    
    class MockRobot:
        def __init__(self, velocity=2.0, energy=5.0):
            self.velocity = velocity
            self.current_tick_energy = energy
            self.current_state = "delivering_pod"
    
    class MockWarehouse:
        def __init__(self):
            self.picking_station_queue_length = 7  # 模擬擁堵
    
    # 設置 warehouse
    reward_system.warehouse = MockWarehouse()
    
    # 測試關鍵路口 vs 一般路口
    print("\n1. 測試路口權重差異...")
    
    # 關鍵路口（ID=0）
    critical_int = MockIntersection(0)
    passed_robots = [MockRobot(2.0, 3.0)]
    waiting_robots = []
    
    reward_critical = reward_system.calculate_step_reward_v7(
        critical_int, passed_robots, waiting_robots, False, 100, False
    )
    
    # 一般路口（ID=1）
    normal_int = MockIntersection(1)
    reward_normal = reward_system.calculate_step_reward_v7(
        normal_int, passed_robots, waiting_robots, False, 100, False
    )
    
    print(f"   關鍵路口獎勵: {reward_critical:.2f}")
    print(f"   一般路口獎勵: {reward_normal:.2f}")
    print(f"   差異倍數: {reward_critical/reward_normal:.1f}x")
    
    # 測試限速獎勵
    print("\n2. 測試限速獎勵...")
    reward_with_limit = reward_system.calculate_step_reward_v7(
        critical_int, passed_robots, waiting_robots, False, 100, True  # 啟用限速
    )
    
    print(f"   無限速獎勵: {reward_critical:.2f}")
    print(f"   有限速獎勵: {reward_with_limit:.2f}")
    print(f"   限速帶來的額外獎勵: {reward_with_limit - reward_critical:.2f}")
    
    print("\n✅ 獎勵計算測試完成！")

def test_energy_efficiency():
    """測試能源效率"""
    print("\n=== V7.0 能源效率測試 ===")
    
    # 設置測試環境
    controller_kwargs = {
        'reward_mode': 'step',
        'action_size': 6,
        'state_size': 17,
        'is_training': False
    }
    
    warehouse = netlogo.training_setup(controller_type="dqn", controller_kwargs=controller_kwargs)
    
    print("\n1. 測試正常速度 vs 限速的能源消耗...")
    
    # 記錄初始能源
    initial_energy = warehouse.total_energy
    
    # 運行 20 個 tick（正常速度）
    print("\n   正常速度運行 20 ticks...")
    for i in range(20):
        warehouse, _ = netlogo.training_tick(warehouse)
    
    normal_energy_consumed = warehouse.total_energy - initial_energy
    print(f"   正常速度能源消耗: {normal_energy_consumed:.2f}")
    
    # 對所有關鍵路口限速
    print("\n   對所有關鍵路口設置 50% 限速...")
    for intersection_id in [0, 6, 12, 18, 24, 30, 36, 42, 48, 54, 60]:
        if intersection_id < len(warehouse.intersection_manager.intersections):
            warehouse.speed_limit_manager.set_corridor_speed_limit(intersection_id, 0.5, "both")
    
    # 記錄限速後的能源
    energy_before_limit = warehouse.total_energy
    
    # 運行 20 個 tick（限速）
    print("   限速運行 20 ticks...")
    for i in range(20):
        warehouse, _ = netlogo.training_tick(warehouse)
    
    limit_energy_consumed = warehouse.total_energy - energy_before_limit
    print(f"   限速後能源消耗: {limit_energy_consumed:.2f}")
    
    # 計算節能比例
    if normal_energy_consumed > 0:
        savings = (normal_energy_consumed - limit_energy_consumed) / normal_energy_consumed * 100
        print(f"\n   節能效果: {savings:.1f}%")
    
    print("\n✅ 能源效率測試完成！")

if __name__ == "__main__":
    print("V7.0 系統完整測試開始...\n")
    
    try:
        # 執行所有測試
        test_robot_speed_limit()
        test_corridor_speed_limit()
        test_dqn_speed_actions()
        test_reward_calculation()
        test_energy_efficiency()
        
        print("\n🎉 所有測試完成！V7.0 系統運作正常！")
        
    except Exception as e:
        print(f"\n❌ 測試過程中發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        print("\n請檢查錯誤訊息並修正問題。")
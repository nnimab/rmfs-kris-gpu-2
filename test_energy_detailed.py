#!/usr/bin/env python3
"""
V7.0 詳細能源測試
確保有機器人移動並測試限速效果
"""
import netlogo
import time

def test_energy_with_moving_robots():
    """詳細測試能源與限速"""
    print("=== V7.0 詳細能源測試 ===\n")
    
    # 設置測試環境
    controller_kwargs = {
        'reward_mode': 'step',
        'action_size': 6,
        'state_size': 17,
        'is_training': False
    }
    
    warehouse = netlogo.training_setup(controller_type="dqn", controller_kwargs=controller_kwargs)
    
    # 先運行一段時間讓系統穩定
    print("1. 讓系統運行 50 ticks 以確保有機器人在移動...")
    for i in range(50):
        warehouse, _ = netlogo.training_tick(warehouse)
        if i % 10 == 0:
            active_robots = sum(1 for r in warehouse.robot_manager.robots if r.velocity > 0)
            print(f"   Tick {i}: {active_robots} 個機器人在移動")
    
    # 找到所有正在運送貨物的機器人
    print("\n2. 尋找正在運送貨物的機器人...")
    delivering_robots = []
    for robot in warehouse.robot_manager.robots:
        if robot.current_state == "delivering_pod" and robot.velocity > 0:
            delivering_robots.append(robot)
    
    print(f"   找到 {len(delivering_robots)} 個正在運送貨物的機器人")
    
    # 選擇前5個進行測試
    test_robots = delivering_robots[:5]
    if not test_robots:
        # 如果沒有運送貨物的，就選任何移動的機器人
        test_robots = [r for r in warehouse.robot_manager.robots if r.velocity > 0][:5]
    
    if not test_robots:
        print("   ⚠️ 沒有找到移動中的機器人！")
        return
    
    print(f"   選擇 {len(test_robots)} 個機器人進行測試\n")
    
    # 測試正常速度
    print("3. 測試正常速度能耗（20 ticks）...")
    initial_warehouse_energy = warehouse.total_energy
    robot_energy_start = {r.robotName(): r.energy_consumption for r in test_robots}
    
    normal_tick_energies = []
    for tick in range(20):
        warehouse, _ = netlogo.training_tick(warehouse)
        tick_energy = sum(r.current_tick_energy for r in test_robots if r.current_tick_energy > 0)
        if tick_energy > 0:
            normal_tick_energies.append(tick_energy)
    
    robot_energy_normal = {r.robotName(): r.energy_consumption - robot_energy_start[r.robotName()] 
                          for r in test_robots}
    warehouse_energy_normal = warehouse.total_energy - initial_warehouse_energy
    
    print(f"   倉庫總能耗增加: {warehouse_energy_normal:.2f}")
    print("   個別機器人能耗:")
    for name, energy in robot_energy_normal.items():
        print(f"     - {name}: {energy:.4f}")
    
    if normal_tick_energies:
        avg_normal = sum(normal_tick_energies) / len(normal_tick_energies)
        print(f"   平均每 tick 能耗: {avg_normal:.4f}")
    
    # 應用限速
    print("\n4. 對測試機器人應用 50% 限速...")
    for robot in test_robots:
        robot.apply_speed_limit(0.5)
        print(f"   - {robot.robotName()}: 速度 {robot.velocity:.2f} -> 限速 50%")
    
    # 測試限速後能耗
    print("\n5. 測試限速能耗（20 ticks）...")
    initial_warehouse_energy_2 = warehouse.total_energy
    robot_energy_start_2 = {r.robotName(): r.energy_consumption for r in test_robots}
    
    limited_tick_energies = []
    for tick in range(20):
        warehouse, _ = netlogo.training_tick(warehouse)
        tick_energy = sum(r.current_tick_energy for r in test_robots if r.current_tick_energy > 0)
        if tick_energy > 0:
            limited_tick_energies.append(tick_energy)
    
    robot_energy_limited = {r.robotName(): r.energy_consumption - robot_energy_start_2[r.robotName()] 
                           for r in test_robots}
    warehouse_energy_limited = warehouse.total_energy - initial_warehouse_energy_2
    
    print(f"   倉庫總能耗增加: {warehouse_energy_limited:.2f}")
    print("   個別機器人能耗:")
    for name, energy in robot_energy_limited.items():
        print(f"     - {name}: {energy:.4f}")
    
    if limited_tick_energies:
        avg_limited = sum(limited_tick_energies) / len(limited_tick_energies)
        print(f"   平均每 tick 能耗: {avg_limited:.4f}")
    
    # 分析結果
    print("\n6. 能源效率分析...")
    
    # 個別機器人分析
    print("   個別機器人節能:")
    for name in robot_energy_normal:
        if robot_energy_normal[name] > 0 and name in robot_energy_limited:
            savings = (robot_energy_normal[name] - robot_energy_limited[name]) / robot_energy_normal[name] * 100
            print(f"     - {name}: {savings:.1f}% 節能")
    
    # 整體分析
    if normal_tick_energies and limited_tick_energies:
        avg_normal = sum(normal_tick_energies) / len(normal_tick_energies)
        avg_limited = sum(limited_tick_energies) / len(limited_tick_energies)
        if avg_normal > 0:
            overall_savings = (avg_normal - avg_limited) / avg_normal * 100
            print(f"\n   整體節能效果: {overall_savings:.1f}%")
            print(f"   理論節能 (50%速度): {(1 - 0.5**1.5) * 100:.1f}%")
            
            if overall_savings > 30:
                print("\n   ✅ 限速確實節省能源！")
            elif overall_savings > 0:
                print("\n   ⚠️ 有節能效果，但低於預期")
            else:
                print("\n   ❌ 限速反而增加能耗，需要檢查")
    
    print("\n✅ 詳細能源測試完成！")

if __name__ == "__main__":
    test_energy_with_moving_robots()
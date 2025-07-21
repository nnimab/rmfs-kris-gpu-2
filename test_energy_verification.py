#!/usr/bin/env python3
"""
V7.0 能源計算驗證腳本
確保能源計算正確，特別是限速的影響
"""
import netlogo

def test_energy_calculation():
    """詳細測試能源計算"""
    print("=== V7.0 能源計算驗證 ===\n")
    
    # 設置測試環境
    controller_kwargs = {
        'reward_mode': 'step',
        'action_size': 6,
        'state_size': 17,
        'is_training': False
    }
    
    warehouse = netlogo.training_setup(controller_type="dqn", controller_kwargs=controller_kwargs)
    
    # 找幾個移動中的機器人
    print("1. 尋找移動中的機器人...")
    moving_robots = []
    for robot in warehouse.robot_manager.robots[:20]:
        if robot.velocity > 0:
            moving_robots.append(robot)
            if len(moving_robots) >= 3:
                break
    
    if not moving_robots:
        print("   警告：沒有找到移動中的機器人，運行幾個 tick...")
        for _ in range(10):
            warehouse, _ = netlogo.training_tick(warehouse)
        
        # 再次尋找
        for robot in warehouse.robot_manager.robots[:20]:
            if robot.velocity > 0:
                moving_robots.append(robot)
                if len(moving_robots) >= 3:
                    break
    
    print(f"   找到 {len(moving_robots)} 個移動中的機器人\n")
    
    # 測試正常速度的能耗
    print("2. 測試正常速度能耗（10 ticks）...")
    normal_energy_data = {robot.robotName(): [] for robot in moving_robots}
    
    for tick in range(10):
        warehouse, _ = netlogo.training_tick(warehouse)
        for robot in moving_robots:
            if robot.current_tick_energy > 0:
                normal_energy_data[robot.robotName()].append(robot.current_tick_energy)
    
    # 計算平均能耗
    print("   正常速度能耗統計：")
    normal_avg = {}
    for robot_name, energies in normal_energy_data.items():
        if energies:
            avg = sum(energies) / len(energies)
            normal_avg[robot_name] = avg
            print(f"   - {robot_name}: 平均 {avg:.4f} / tick")
    
    # 應用 50% 限速
    print("\n3. 應用 50% 限速...")
    for robot in moving_robots:
        robot.apply_speed_limit(0.5)
        print(f"   - {robot.robotName()}: 限速設定為 {robot.speed_limit_factor*100:.0f}%")
    
    # 測試限速後的能耗
    print("\n4. 測試限速能耗（10 ticks）...")
    limited_energy_data = {robot.robotName(): [] for robot in moving_robots}
    
    for tick in range(10):
        warehouse, _ = netlogo.training_tick(warehouse)
        for robot in moving_robots:
            if robot.current_tick_energy > 0:
                limited_energy_data[robot.robotName()].append(robot.current_tick_energy)
    
    # 計算限速後平均能耗
    print("   限速後能耗統計：")
    limited_avg = {}
    for robot_name, energies in limited_energy_data.items():
        if energies:
            avg = sum(energies) / len(energies)
            limited_avg[robot_name] = avg
            print(f"   - {robot_name}: 平均 {avg:.4f} / tick")
    
    # 比較結果
    print("\n5. 能源節省分析：")
    total_savings = []
    for robot_name in normal_avg:
        if robot_name in limited_avg and normal_avg[robot_name] > 0:
            savings = (normal_avg[robot_name] - limited_avg[robot_name]) / normal_avg[robot_name] * 100
            total_savings.append(savings)
            print(f"   - {robot_name}: 節省 {savings:.1f}%")
            
            # 理論值：50% 速度應該節省約 65% 能源 (0.5^1.5 = 0.35)
            expected_savings = (1 - 0.5**1.5) * 100
            print(f"     (理論值: {expected_savings:.1f}%)")
    
    if total_savings:
        avg_savings = sum(total_savings) / len(total_savings)
        print(f"\n   平均節能效果: {avg_savings:.1f}%")
        
        if avg_savings > 30:
            print("   ✅ 能源計算正確！限速確實節省能源")
        else:
            print("   ⚠️  能源節省效果低於預期")
    
    # 測試總能耗
    print("\n6. 測試倉庫總能耗...")
    initial_total = warehouse.total_energy
    print(f"   初始總能耗: {initial_total:.2f}")
    
    # 運行 20 ticks
    for _ in range(20):
        warehouse, _ = netlogo.training_tick(warehouse)
    
    final_total = warehouse.total_energy
    energy_increase = final_total - initial_total
    print(f"   最終總能耗: {final_total:.2f}")
    print(f"   20 ticks 能耗增加: {energy_increase:.2f}")
    print(f"   平均每 tick: {energy_increase/20:.3f}")
    
    print("\n✅ 能源計算驗證完成！")

if __name__ == "__main__":
    test_energy_calculation()
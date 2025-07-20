#!/usr/bin/env python3
"""
V6.0 混合式 Step 獎勵測試腳本
驗證新的獎勵函數是否正確運作，確保所有數值非零且合理
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ai.unified_reward_system import UnifiedRewardSystem
import numpy as np

class MockRobot:
    """模擬機器人對象"""
    def __init__(self, current_tick_energy=0.5, current_intersection_start_time=None):
        self.current_tick_energy = current_tick_energy
        self.current_intersection_start_time = current_intersection_start_time
        self.current_state = "delivering_pod"

class MockWarehouse:
    """模擬倉庫對象"""
    def __init__(self, queue_length=3):
        self.picking_station_queue_length = queue_length
        self._tick = 100

class MockIntersection:
    """模擬交叉口對象"""
    def __init__(self, intersection_id=1):
        self.id = intersection_id
        self.allowed_direction = "Horizontal"

def test_hybrid_reward_system():
    """測試混合式獎勵系統"""
    print("=" * 60)
    print("V6.0 混合式 Step 獎勵測試")
    print("=" * 60)
    
    # 1. 初始化系統
    reward_system = UnifiedRewardSystem(
        reward_mode="step", 
        use_hybrid_step=True
    )
    
    # 2. 模擬對象
    warehouse = MockWarehouse(queue_length=5)
    reward_system.warehouse = warehouse
    
    intersection = MockIntersection(intersection_id=12345)
    
    # 3. 測試多個場景
    test_scenarios = [
        {
            'name': '場景1: 有機器人通過，無等待',
            'passed_robots': [MockRobot(current_tick_energy=0.3)],
            'waiting_robots': [],
            'signal_switched': False,
            'tick': 50
        },
        {
            'name': '場景2: 無機器人通過，有等待',
            'passed_robots': [],
            'waiting_robots': [MockRobot(current_intersection_start_time=45)],
            'signal_switched': False,
            'tick': 100
        },
        {
            'name': '場景3: 信號切換',
            'passed_robots': [MockRobot(current_tick_energy=0.8)],
            'waiting_robots': [MockRobot(current_intersection_start_time=95)],
            'signal_switched': True,
            'tick': 150
        },
        {
            'name': '場景4: 能源消耗改善',
            'passed_robots': [MockRobot(current_tick_energy=0.1)],  # 能源降低
            'waiting_robots': [],
            'signal_switched': False,
            'tick': 200
        },
        {
            'name': '場景5: 排隊改善',
            'passed_robots': [MockRobot(current_tick_energy=0.4)],
            'waiting_robots': [MockRobot(current_intersection_start_time=195)],
            'signal_switched': False,
            'tick': 250
        }
    ]
    
    # 在場景5前改善排隊狀況
    warehouse.picking_station_queue_length = 2  # 從5降到2
    
    print("\n開始測試各種場景...")
    
    for i, scenario in enumerate(test_scenarios):
        print(f"\n--- {scenario['name']} ---")
        
        # 計算獎勵
        reward = reward_system.calculate_step_reward_hybrid(
            intersection=intersection,
            passed_robots=scenario['passed_robots'],
            waiting_robots=scenario['waiting_robots'],
            signal_switched=scenario['signal_switched'],
            tick=scenario['tick']
        )
        
        print(f"最終獎勵: {reward:.4f}")
        
        # 驗證獎勵值合理性
        if reward == 0:
            print("WARNING: 獎勵值為0，可能存在問題")
        elif abs(reward) > 5:
            print(f"WARNING: 獎勵值異常 ({reward:.4f})，可能太大")
        else:
            print("OK: 獎勵值在合理範圍內")
    
    # 4. 測試對比：原始 vs 混合式
    print("\n" + "=" * 60)
    print("對比測試：原始 Step 獎勵 vs 混合式 Step 獎勵")
    print("=" * 60)
    
    # 原始獎勵系統
    original_system = UnifiedRewardSystem(reward_mode="step", use_hybrid_step=False)
    
    test_case = {
        'passed_robots': [MockRobot(current_tick_energy=0.5)],
        'waiting_robots': [MockRobot(current_intersection_start_time=295)],
        'signal_switched': False,
        'tick': 300
    }
    
    original_reward = original_system.calculate_step_reward(
        intersection=intersection,
        passed_robots=test_case['passed_robots'],
        waiting_robots=test_case['waiting_robots'],
        signal_switched=test_case['signal_switched']
    )
    
    hybrid_reward = reward_system.calculate_step_reward_hybrid(
        intersection=intersection,
        passed_robots=test_case['passed_robots'],
        waiting_robots=test_case['waiting_robots'],
        signal_switched=test_case['signal_switched'],
        tick=test_case['tick']
    )
    
    print(f"原始 Step 獎勵: {original_reward:.4f}")
    print(f"混合式 Step 獎勵: {hybrid_reward:.4f}")
    print(f"差異: {hybrid_reward - original_reward:.4f}")
    
    # 5. 數值驗證
    print("\n" + "=" * 60)
    print("數值驗證檢查")
    print("=" * 60)
    
    checks = [
        ("原始獎勵非零", original_reward != 0),
        ("混合式獎勵非零", hybrid_reward != 0),
        ("原始獎勵合理範圍", -2 <= original_reward <= 2),
        ("混合式獎勵合理範圍", -3 <= hybrid_reward <= 3),
        ("混合式獎勵有差異", abs(hybrid_reward - original_reward) > 0.001)
    ]
    
    for check_name, result in checks:
        status = "PASS" if result else "FAIL"
        print(f"{check_name}: {status}")
    
    print("\n" + "=" * 60)
    print("測試完成！")
    print("=" * 60)

if __name__ == "__main__":
    test_hybrid_reward_system()
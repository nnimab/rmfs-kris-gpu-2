#!/usr/bin/env python3
"""
V7.0 簡單測試腳本
測試獎勵系統和限速機制的基本功能
"""
import sys
import time
import netlogo
from ai.unified_reward_system import UnifiedRewardSystem

def test_reward_system():
    """測試 V7 獎勵系統"""
    print("=== V7.0 獎勵系統測試 ===")
    
    # 創建獎勵系統
    reward_system = UnifiedRewardSystem(reward_mode="step")
    
    print(f"\n1. 關鍵路口設定:")
    print(f"   關鍵路口 ID: {reward_system.critical_intersections}")
    print(f"   關鍵路口權重: {reward_system.critical_weight}")
    
    print(f"\n2. 測試權重設定:")
    print(f"   一般路口權重: 1.0")
    print(f"   關鍵路口權重: {reward_system.critical_weight}")
    
    # 測試獎勵計算
    print(f"\n3. 測試獎勵計算邏輯:")
    
    # 模擬一個關鍵路口
    class MockIntersection:
        def __init__(self, id):
            self.id = id
    
    # 模擬機器人
    class MockRobot:
        def __init__(self, priority="medium", velocity=2.0, energy=5.0):
            self.priority = priority
            self.velocity = velocity
            self.current_tick_energy = energy
    
    # 測試關鍵路口 vs 一般路口
    critical_intersection = MockIntersection(0)  # 關鍵路口
    normal_intersection = MockIntersection(1)    # 一般路口
    
    passed_robots = [MockRobot("high", 2.0, 3.0)]
    waiting_robots = [MockRobot("low", 0, 0)]
    
    # 計算獎勵（需要模擬 get_robot_task_priority）
    print("   關鍵路口 0 的權重應該是 5.0")
    print("   一般路口 1 的權重應該是 1.0")
    
    print("\n✅ 獎勵系統測試完成！")

def test_speed_limit_concepts():
    """測試限速概念"""
    print("\n=== V7.0 限速機制概念測試 ===")
    
    print("\n1. 動作空間擴展:")
    print("   動作 0: 保持當前方向")
    print("   動作 1: 切換到垂直")
    print("   動作 2: 切換到水平")
    print("   動作 3: 限速 30%")
    print("   動作 4: 限速 50%")
    print("   動作 5: 取消限速")
    
    print("\n2. 能源與速度關係:")
    print("   正常速度 (100%): 能源消耗 = 1.0")
    print("   限速 50%: 能源消耗 ≈ 0.35 (50%^1.5)")
    print("   限速 30%: 能源消耗 ≈ 0.16 (30%^1.5)")
    
    print("\n3. 整條路限速設計:")
    print("   - 當選擇限速動作時，整條走廊都會被限速")
    print("   - 不只是單個路口，而是整條路")
    print("   - 可以分別控制水平/垂直走廊")
    
    print("\n✅ 限速概念測試完成！")

def test_integration():
    """測試整合功能"""
    print("\n=== V7.0 整合測試 ===")
    
    # 設置 DQN 參數
    controller_kwargs = {
        'reward_mode': 'step',
        'action_size': 6,  # V7.0: 6個動作
        'state_size': 17,
        'is_training': True
    }
    
    print("\n1. 設置倉庫環境...")
    try:
        warehouse = netlogo.training_setup(controller_type="dqn", controller_kwargs=controller_kwargs)
        print("   ✅ 倉庫設置成功")
        
        # 檢查速度限制管理器
        if hasattr(warehouse, 'speed_limit_manager'):
            print("   ✅ 速度限制管理器已初始化")
        else:
            print("   ❌ 警告：速度限制管理器未找到")
        
        # 檢查路口數量
        num_intersections = len(warehouse.intersection_manager.intersections)
        print(f"   路口總數: {num_intersections}")
        
        # 執行幾個 tick
        print("\n2. 執行模擬測試...")
        for i in range(5):
            warehouse, status = netlogo.training_tick(warehouse)
            if status == "finished":
                break
            print(f"   Tick {i+1} 完成")
        
        print("\n✅ 整合測試完成！")
        
    except Exception as e:
        print(f"\n❌ 整合測試失敗: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("V7.0 系統簡單測試\n")
    
    # 執行測試
    test_reward_system()
    test_speed_limit_concepts()
    test_integration()
    
    print("\n所有測試完成！")
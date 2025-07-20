"""
NERL 適應度為 0 的問題分析與解決方案

問題分析：
1. 評估時間太短（200 ticks）導致沒有訂單完成
2. 沒有訂單完成 → 完成獎勵為 0
3. 沒有里程碑事件觸發 → 里程碑獎勵為 0  
4. 最終適應度 = 0

解決方案：
"""

from ai.unified_reward_system import UnifiedRewardSystem

def test_different_eval_times():
    """測試不同評估時間對適應度的影響"""
    
    system = UnifiedRewardSystem(reward_mode='global')
    
    # 模擬不同的評估時間
    eval_times = [200, 500, 1000, 2000, 5000]
    
    for eval_ticks in eval_times:
        print(f"\n=== 評估時間: {eval_ticks} ticks ===")
        
        # 模擬訂單完成情況
        class MockOrder:
            def __init__(self, order_id, complete_time=-1):
                self.id = order_id
                self.order_complete_time = complete_time
        
        class MockOrderManager:
            def __init__(self, eval_ticks):
                self.orders = []
                # 根據評估時間模擬訂單完成
                if eval_ticks >= 500:
                    self.orders.append(MockOrder(1, int(eval_ticks * 0.3)))  # 30% 時完成
                if eval_ticks >= 1000:
                    self.orders.append(MockOrder(2, int(eval_ticks * 0.6)))  # 60% 時完成
                if eval_ticks >= 2000:
                    self.orders.append(MockOrder(3, int(eval_ticks * 0.8)))  # 80% 時完成
                
                # 添加一些未完成的訂單
                for i in range(4, 8):
                    self.orders.append(MockOrder(i, -1))
        
        class MockWarehouse:
            def __init__(self, eval_ticks):
                self.total_energy = eval_ticks * 2  # 能源消耗與時間成正比
                self.order_manager = MockOrderManager(eval_ticks)
        
        warehouse = MockWarehouse(eval_ticks)
        
        # 計算適應度
        fitness = system.calculate_global_reward(warehouse, eval_ticks)
        completed_orders = len([order for order in warehouse.order_manager.orders if order.order_complete_time != -1 and order.id >= 0])
        
        print(f"完成訂單數: {completed_orders}")
        print(f"總能源消耗: {warehouse.total_energy}")
        print(f"適應度分數: {fitness:.4f}")
        
        # 建議
        if fitness > 0:
            print("✅ 適應度正常，可以進行有效訓練")
        else:
            print("❌ 適應度為 0，訓練無效")

def recommend_eval_ticks():
    """推薦合適的評估時間"""
    print("\n" + "="*50)
    print("推薦的 NERL 評估時間設置：")
    print("="*50)
    print("🔸 快速測試: --eval_ticks 1000")
    print("🔸 標準訓練: --eval_ticks 2000") 
    print("🔸 高品質訓練: --eval_ticks 5000")
    print("\n原因：")
    print("- 200 ticks 太短，無法完成訂單")
    print("- 至少需要 500-1000 ticks 才能看到訂單完成")
    print("- 2000+ ticks 可以獲得穩定的適應度分數")
    print("\n使用方法：")
    print("python train.py --agent nerl --reward_mode global --eval_ticks 2000")

if __name__ == "__main__":
    test_different_eval_times()
    recommend_eval_ticks()
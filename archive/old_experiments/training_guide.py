import netlogo
import time
import os

class TrainingGuide:
    """AI 系統訓練指南"""
    
    def __init__(self):
        self.training_results = {}
    
    def dqn_training_workflow(self, target_ticks=20000, save_interval=5000):
        """
        DQN 訓練工作流程
        
        Args:
            target_ticks: 目標訓練時間
            save_interval: 保存間隔
        """
        print("=== DQN 訓練工作流程 ===")
        
        # 1. 設置DQN控制器
        print("1. 設置DQN控制器...")
        netlogo.set_dqn_controller(exploration_rate=0.8)  # 高探索率開始
        
        # 2. 開始訓練
        print(f"2. 開始訓練，目標: {target_ticks} ticks")
        start_time = time.time()
        
        for current_tick in range(0, target_ticks, 100):
            # 每100 ticks檢查一次
            for _ in range(100):
                netlogo.tick()
            
            # 進度報告
            progress = (current_tick / target_ticks) * 100
            elapsed = time.time() - start_time
            print(f"進度: {progress:.1f}% ({current_tick}/{target_ticks} ticks) - 用時: {elapsed/60:.1f}分鐘")
            
            # 階段性調整探索率
            if current_tick == 5000:
                print("降低探索率到 0.5")
                netlogo.set_dqn_controller(exploration_rate=0.5)
            elif current_tick == 10000:
                print("降低探索率到 0.2")
                netlogo.set_dqn_controller(exploration_rate=0.2)
            elif current_tick == 15000:
                print("降低探索率到 0.1")
                netlogo.set_dqn_controller(exploration_rate=0.1)
        
        # 3. 生成最終報告
        print("3. 生成訓練報告...")
        netlogo.generate_report()
        
        total_time = time.time() - start_time
        print(f"DQN訓練完成！總用時: {total_time/60:.1f}分鐘")
        
        return True
    
    def nerl_training_workflow(self, target_generations=200):
        """
        NERL 訓練工作流程
        
        Args:
            target_generations: 目標進化代數
        """
        print("=== NERL 訓練工作流程 ===")
        
        # 1. 設置NERL控制器
        print("1. 設置NERL控制器...")
        netlogo.set_nerl_controller()
        netlogo.set_nerl_training_mode(is_training=True)
        
        # 2. 開始進化訓練
        print(f"2. 開始進化訓練，目標: {target_generations} 代")
        start_time = time.time()
        
        evolution_interval = 100  # 每100 ticks進化一次
        target_ticks = target_generations * evolution_interval
        
        for generation in range(0, target_generations, 10):
            # 每10代檢查一次
            current_ticks = generation * evolution_interval
            for _ in range(10 * evolution_interval):
                netlogo.tick()
            
            # 進度報告
            progress = (generation / target_generations) * 100
            elapsed = time.time() - start_time
            print(f"進度: {progress:.1f}% (第{generation}代/{target_generations}代) - 用時: {elapsed/60:.1f}分鐘")
        
        # 3. 切換到評估模式
        print("3. 切換到評估模式...")
        netlogo.set_nerl_training_mode(is_training=False)
        
        # 4. 生成最終報告
        print("4. 生成訓練報告...")
        netlogo.generate_report()
        
        total_time = time.time() - start_time
        print(f"NERL訓練完成！總用時: {total_time/60:.1f}分鐘")
        
        return True
    
    def load_and_test_model(self, controller_type, model_tick, test_duration=1000):
        """
        加載並測試已訓練的模型
        
        Args:
            controller_type: "dqn" 或 "nerl"
            model_tick: 要加載的模型時間點
            test_duration: 測試持續時間
        """
        print(f"=== 測試 {controller_type.upper()} 模型 (tick {model_tick}) ===")
        
        # 1. 加載模型
        if controller_type == "dqn":
            success = netlogo.set_dqn_controller(exploration_rate=0.0, load_model_tick=model_tick)
        elif controller_type == "nerl":
            success = netlogo.set_nerl_controller(load_model_tick=model_tick)
            netlogo.set_nerl_training_mode(is_training=False)
        else:
            print("錯誤：未知的控制器類型")
            return False
        
        if not success:
            print("模型加載失敗！")
            return False
        
        print(f"模型加載成功！開始測試...")
        
        # 2. 運行測試
        start_time = time.time()
        for _ in range(test_duration):
            netlogo.tick()
        
        # 3. 生成測試報告
        netlogo.generate_report()
        
        test_time = time.time() - start_time
        print(f"測試完成！用時: {test_time/60:.1f}分鐘")
        
        return True
    
    def compare_models(self, models_info, test_duration=1000):
        """
        比較多個模型的性能
        
        Args:
            models_info: [{"type": "dqn", "tick": 10000}, {"type": "nerl", "tick": 15000}]
            test_duration: 每個模型的測試時間
        """
        print("=== 模型性能比較 ===")
        
        results = []
        
        for i, model_info in enumerate(models_info):
            print(f"\n測試模型 {i+1}/{len(models_info)}: {model_info}")
            
            # 重置環境
            netlogo.setup()
            
            # 測試模型
            success = self.load_and_test_model(
                model_info["type"], 
                model_info["tick"], 
                test_duration
            )
            
            if success:
                results.append(f"模型 {i+1} 測試完成")
            else:
                results.append(f"模型 {i+1} 測試失敗")
        
        print("\n=== 比較結果 ===")
        for result in results:
            print(result)
        
        print("請查看 result/reports/ 和 result/charts/ 資料夾中的詳細報告")
        
        return True
    
    def estimate_training_time(self, controller_type, target_performance="good"):
        """
        估算訓練時間
        
        Args:
            controller_type: "dqn" 或 "nerl"
            target_performance: "basic", "good", "excellent"
        """
        print(f"=== {controller_type.upper()} 訓練時間估算 ===")
        
        time_estimates = {
            "dqn": {
                "basic": {"ticks": 5000, "time_hours": 1},
                "good": {"ticks": 20000, "time_hours": 4},
                "excellent": {"ticks": 50000, "time_hours": 10}
            },
            "nerl": {
                "basic": {"ticks": 5000, "time_hours": 1.5},
                "good": {"ticks": 20000, "time_hours": 5},
                "excellent": {"ticks": 50000, "time_hours": 12}
            }
        }
        
        if controller_type in time_estimates and target_performance in time_estimates[controller_type]:
            estimate = time_estimates[controller_type][target_performance]
            print(f"目標性能: {target_performance}")
            print(f"預估需要: {estimate['ticks']} ticks")
            print(f"預估時間: {estimate['time_hours']} 小時")
            print(f"建議: 分階段訓練，每{estimate['ticks']//4} ticks檢查一次進度")
        else:
            print("無法提供估算，請使用 'basic', 'good', 或 'excellent'")
        
        return True

# 使用範例
if __name__ == "__main__":
    guide = TrainingGuide()
    
    # 查看可用模型
    print("可用的模型:")
    netlogo.list_available_models()
    
    # 估算訓練時間
    guide.estimate_training_time("dqn", "good")
    guide.estimate_training_time("nerl", "good")
    
    # 開始訓練（請根據需要選擇）
    # guide.dqn_training_workflow(target_ticks=10000)
    # guide.nerl_training_workflow(target_generations=100)
    
    # 測試已有模型（如果存在）
    # guide.load_and_test_model("dqn", 5000)
    # guide.load_and_test_model("nerl", 10000) 
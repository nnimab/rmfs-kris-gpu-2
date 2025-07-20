#!/usr/bin/env python3
"""
快速實驗腳本 - 緊急研究專用
修正後的NERL和DQN控制器測試

使用方法：
python fast_experiment.py

包含：
1. 增強的防鎖死機制
2. 修正的NERL參數
3. 快速訓練和對比
"""

import os
import sys
import time
import json
from datetime import datetime

# 添加項目根目錄到路徑
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from netlogo import setup, go


def quick_test_controller(controller_type, ticks=1000, is_training=False):
    """
    快速測試單個控制器
    
    Args:
        controller_type (str): 控制器類型
        ticks (int): 測試步數
        is_training (bool): 是否訓練模式
    
    Returns:
        dict: 性能結果
    """
    print(f"🔧 測試 {controller_type.upper()} 控制器 ({'訓練' if is_training else '測試'}模式)")
    
    start_time = time.time()
    
    try:
        # 初始化
        warehouse = setup(controller_type=controller_type, 
                         is_training=is_training,
                         enable_gui=False)
        
        print(f"   ✅ 初始化完成")
        
        # 運行模擬
        for tick in range(ticks):
            go(warehouse, tick)
            
            # 每200步顯示進度
            if (tick + 1) % 200 == 0:
                progress = (tick + 1) / ticks * 100
                print(f"   進度: {tick+1}/{ticks} ({progress:.1f}%)")
        
        # 收集結果
        result = collect_metrics(warehouse, controller_type)
        
        execution_time = time.time() - start_time
        result['execution_time'] = execution_time
        
        print(f"   ✅ 完成，耗時: {execution_time:.1f}秒")
        print(f"   📊 總能源: {result['total_energy']:.2f}, 完成訂單: {result['completed_orders']}")
        
        return result
        
    except Exception as e:
        print(f"   ❌ 測試失敗: {e}")
        return None


def collect_metrics(warehouse, controller_name):
    """收集性能指標"""
    try:
        # 基本指標
        total_energy = sum(robot.total_energy_consumed for robot in warehouse.robot_manager.robots.values())
        completed_orders = len([order for order in warehouse.order_manager.orders.values() 
                              if order.status == "completed"])
        total_orders = len(warehouse.order_manager.orders)
        
        # 機器人狀態統計
        robot_states = {}
        for robot in warehouse.robot_manager.robots.values():
            state = robot.current_state
            robot_states[state] = robot_states.get(state, 0) + 1
        
        # 平均等待時間
        wait_times = []
        deadlock_count = 0
        
        for intersection in warehouse.intersection_manager.intersections.values():
            h_wait, v_wait = intersection.calculateAverageWaitingTimePerDirection(warehouse.tick)
            wait_times.extend([h_wait, v_wait])
            
            # 檢查是否有潛在死鎖
            h_robots = len(intersection.horizontal_robots)
            v_robots = len(intersection.vertical_robots)
            if h_robots > 3 and v_robots > 3:
                deadlock_count += 1
        
        avg_wait_time = sum(wait_times) / len(wait_times) if wait_times else 0
        max_wait_time = max(wait_times) if wait_times else 0
        
        # 效率指標
        completion_rate = completed_orders / total_orders if total_orders > 0 else 0
        energy_per_order = total_energy / completed_orders if completed_orders > 0 else float('inf')
        
        return {
            'controller': controller_name,
            'total_energy': total_energy,
            'completed_orders': completed_orders,
            'total_orders': total_orders,
            'completion_rate': completion_rate,
            'avg_wait_time': avg_wait_time,
            'max_wait_time': max_wait_time,
            'energy_per_order': energy_per_order,
            'robot_states': robot_states,
            'potential_deadlocks': deadlock_count,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"❌ 指標收集失敗: {e}")
        return {'controller': controller_name, 'error': str(e)}


def run_comparative_experiment():
    """運行對比實驗"""
    print("🚀 開始快速對比實驗")
    print("=" * 50)
    
    controllers = ["time", "queue", "dqn", "nerl"]
    all_results = []
    
    # 階段1: 快速測試所有控制器
    print("\n📊 階段1: 快速測試所有控制器")
    for controller in controllers:
        result = quick_test_controller(controller, ticks=1000, is_training=False)
        if result:
            all_results.append(result)
    
    # 階段2: 短期訓練AI控制器
    print("\n🔥 階段2: 短期訓練AI控制器")
    ai_controllers = ["dqn", "nerl"]
    
    for controller in ai_controllers:
        print(f"\n   訓練 {controller.upper()} 控制器...")
        result = quick_test_controller(controller, ticks=3000, is_training=True)
        if result:
            result['phase'] = 'training'
            all_results.append(result)
    
    # 階段3: 測試訓練後的AI控制器
    print("\n🧪 階段3: 測試訓練後的AI控制器")
    for controller in ai_controllers:
        result = quick_test_controller(controller, ticks=1000, is_training=False)
        if result:
            result['phase'] = 'post_training'
            all_results.append(result)
    
    # 保存和分析結果
    save_results(all_results)
    analyze_results(all_results)
    
    return all_results


def save_results(results):
    """保存結果"""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"fast_experiment_results_{timestamp}.json"
        
        results_dir = os.path.join(project_root, "result")
        os.makedirs(results_dir, exist_ok=True)
        
        filepath = os.path.join(results_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 結果已保存到: {filepath}")
        
    except Exception as e:
        print(f"❌ 保存結果失敗: {e}")


def analyze_results(results):
    """分析結果"""
    print("\n📈 結果分析")
    print("-" * 30)
    
    # 按控制器分組
    by_controller = {}
    for result in results:
        if 'error' in result:
            continue
            
        controller = result['controller']
        phase = result.get('phase', 'test')
        
        if controller not in by_controller:
            by_controller[controller] = {}
        
        by_controller[controller][phase] = result
    
    # 顯示對比結果
    print(f"{'控制器':<8} {'總能源':<10} {'完成訂單':<8} {'完成率':<8} {'平均等待':<10}")
    print("-" * 55)
    
    for controller, phases in by_controller.items():
        test_result = phases.get('test', phases.get('post_training'))
        if test_result:
            print(f"{controller:<8} "
                  f"{test_result['total_energy']:<10.1f} "
                  f"{test_result['completed_orders']:<8} "
                  f"{test_result['completion_rate']:<8.2f} "
                  f"{test_result['avg_wait_time']:<10.2f}")
    
    # 找出最佳表現
    test_results = []
    for controller, phases in by_controller.items():
        test_result = phases.get('test', phases.get('post_training'))
        if test_result:
            test_results.append(test_result)
    
    if test_results:
        print("\n🏆 最佳表現:")
        
        # 最低能源
        best_energy = min(test_results, key=lambda x: x['total_energy'])
        print(f"   最低能源消耗: {best_energy['controller']} ({best_energy['total_energy']:.1f})")
        
        # 最多訂單
        best_orders = max(test_results, key=lambda x: x['completed_orders'])
        print(f"   最多完成訂單: {best_orders['controller']} ({best_orders['completed_orders']})")
        
        # 最短等待
        best_wait = min(test_results, key=lambda x: x['avg_wait_time'])
        print(f"   最短平均等待: {best_wait['controller']} ({best_wait['avg_wait_time']:.2f})")
        
        # 最高效率
        best_efficiency = min(test_results, key=lambda x: x['energy_per_order'])
        print(f"   最高能源效率: {best_efficiency['controller']} ({best_efficiency['energy_per_order']:.2f})")
    
    # 死鎖檢測結果
    print("\n⚠️ 死鎖風險分析:")
    for controller, phases in by_controller.items():
        test_result = phases.get('test', phases.get('post_training'))
        if test_result:
            deadlocks = test_result.get('potential_deadlocks', 0)
            max_wait = test_result.get('max_wait_time', 0)
            status = "🟢 良好" if deadlocks == 0 and max_wait < 100 else "🟡 注意" if deadlocks < 3 else "🔴 風險"
            print(f"   {controller}: {status} (潛在死鎖: {deadlocks}, 最長等待: {max_wait:.1f})")


def main():
    """主函數"""
    print("🎯 RMFS 快速實驗 - 修正版本")
    print("時間:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("=" * 50)
    
    print("📋 實驗配置:")
    print("   - 增強防鎖死機制: ✅")
    print("   - NERL進化間隔: 1000 ticks")
    print("   - 族群大小: 20")
    print("   - 測試輪數: 每個控制器1000 ticks")
    print("   - AI訓練: 3000 ticks")
    
    try:
        results = run_comparative_experiment()
        
        print("\n🎉 實驗完成！")
        print("💡 檢查結果文件以獲取詳細數據")
        
        return results
        
    except KeyboardInterrupt:
        print("\n⏹️ 實驗被用戶中斷")
    except Exception as e:
        print(f"\n❌ 實驗失敗: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main() 
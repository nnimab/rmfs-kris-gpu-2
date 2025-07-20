#!/usr/bin/env python3
"""
RMFS 控制器評估腳本
用於比較不同控制器的性能
"""

import argparse
import os
import json
import time
import numpy as np
import pandas as pd
from datetime import datetime
from pathlib import Path
import matplotlib.pyplot as plt

# 導入必要的模組
import netlogo
from ai.controllers.dqn_controller import DQNController
from ai.controllers.nerl_controller import NEController
from ai.controllers.queue_based_controller import QueueBasedController
from ai.controllers.time_based_controller import TimeBasedController
from lib.logger import get_logger

class ControllerEvaluator:
    def __init__(self, evaluation_ticks=5000, num_runs=3, output_dir="evaluation_results"):
        self.evaluation_ticks = evaluation_ticks
        self.num_runs = num_runs
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # 設置日誌
        log_file = self.output_dir / "evaluation.log"
        self.logger = get_logger(log_file_path=str(log_file))
        
        # 存儲結果
        self.results = {}
        
    def load_trained_models(self):
        """載入所有訓練好的模型"""
        models = {}
        training_runs_dir = Path("models/training_runs")
        
        if not training_runs_dir.exists():
            self.logger.warning("未找到訓練結果目錄")
            return models
            
        for run_dir in training_runs_dir.iterdir():
            if not run_dir.is_dir():
                continue
                
            metadata_file = run_dir / "metadata.json"
            if not metadata_file.exists():
                continue
                
            try:
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                
                controller_type = metadata.get('controller_type')
                reward_mode = metadata.get('reward_mode')
                
                # 尋找最佳模型文件
                model_file = None
                if controller_type == 'nerl':
                    model_file = run_dir / "best_model.pth"
                elif controller_type == 'dqn':
                    # 尋找final模型
                    for file in run_dir.glob("*.pth"):
                        if "final" in file.name:
                            model_file = file
                            break
                
                if model_file and model_file.exists():
                    model_name = f"{controller_type}_{reward_mode}"
                    models[model_name] = {
                        'type': controller_type,
                        'reward_mode': reward_mode,
                        'model_path': str(model_file),
                        'metadata': metadata,
                        'run_dir': run_dir
                    }
                    self.logger.info(f"找到模型: {model_name}")
                    
            except Exception as e:
                self.logger.warning(f"載入模型時出錯 {run_dir}: {e}")
                
        return models
    
    def evaluate_controller(self, controller_name, controller_config, run_id=0):
        """評估單個控制器"""
        self.logger.info(f"開始評估 {controller_name} (運行 {run_id + 1}/{self.num_runs})")
        
        try:
            # 創建倉庫環境
            if controller_config['type'] in ['nerl', 'dqn']:
                # AI控制器
                controller_kwargs = {
                    'reward_mode': controller_config['reward_mode'],
                    'log_file_path': None  # 評估時不需要詳細日誌
                }
                warehouse = netlogo.training_setup(
                    controller_type=controller_config['type'], 
                    controller_kwargs=controller_kwargs
                )
                
                # 載入訓練好的模型
                if controller_config['type'] == 'nerl':
                    controller = warehouse.intersection_manager.controllers.get('nerl')
                    if controller and controller.best_individual:
                        # 載入最佳個體
                        import torch
                        state_dict = torch.load(controller_config['model_path'], map_location='cpu')
                        controller.best_individual.load_state_dict(state_dict)
                        controller.set_active_individual(controller.best_individual)
                        controller.set_training_mode(False)
                        
                elif controller_config['type'] == 'dqn':
                    controller = warehouse.intersection_manager.controllers.get('dqn')
                    if controller:
                        controller.load_model(controller_config['model_path'])
                        controller.set_training_mode(False)
                        
            else:
                # 傳統控制器
                controller_kwargs = {}
                if controller_config['type'] == 'queue_based':
                    warehouse = netlogo.training_setup(controller_type="queue_based", controller_kwargs=controller_kwargs)
                elif controller_config['type'] == 'time_based':
                    warehouse = netlogo.training_setup(controller_type="time_based", controller_kwargs=controller_kwargs)
            
            if not warehouse:
                self.logger.error(f"無法創建倉庫環境: {controller_name}")
                return None
                
            # 記錄開始時間
            start_time = time.time()
            
            # 運行評估
            for tick in range(self.evaluation_ticks):
                if tick % 1000 == 0:
                    self.logger.info(f"{controller_name} 評估進度: {tick}/{self.evaluation_ticks}")
                
                warehouse, status = netlogo.training_tick(warehouse)
                
                if status != "OK":
                    self.logger.warning(f"{controller_name} 模擬狀態: {status}")
                    if "critical" in status.lower():
                        break
            
            # 計算執行時間
            execution_time = time.time() - start_time
            
            # 收集結果
            completed_orders = len([j for j in warehouse.job_manager.jobs if j.is_finished])
            total_orders = len(warehouse.job_manager.jobs)
            completion_rate = completed_orders / total_orders if total_orders > 0 else 0
            
            # 計算等待時間統計
            wait_times = []
            total_robots_waiting = 0
            max_wait_time = 0
            
            for intersection in warehouse.intersection_manager.intersections:
                for robot in list(intersection.horizontal_robots.values()) + list(intersection.vertical_robots.values()):
                    total_robots_waiting += 1
                    if hasattr(robot, 'current_intersection_start_time') and robot.current_intersection_start_time:
                        wait_time = warehouse._tick - robot.current_intersection_start_time
                        wait_times.append(wait_time)
                        max_wait_time = max(max_wait_time, wait_time)
            
            avg_wait_time = np.mean(wait_times) if wait_times else 0
            
            # 計算能源效率
            total_energy = getattr(warehouse, 'total_energy', 0)
            energy_per_order = total_energy / completed_orders if completed_orders > 0 else 0
            
            # 計算機器人利用率（基於時間的真正利用率）
            total_robots = 0
            total_utilization = 0.0
            current_tick = warehouse.current_tick
            
            for obj in warehouse.getMovableObjects():
                if obj.object_type == "robot":
                    total_robots += 1
                    
                    # 計算累積活動時間
                    accumulated_active_time = obj.total_active_time
                    
                    # 如果機器人目前處於非閒置狀態，加上從上次狀態變化到現在的時間
                    if obj.current_state != 'idle' and obj.last_state_change_time > 0:
                        accumulated_active_time += current_tick - obj.last_state_change_time
                    
                    # 計算利用率（避免除零）
                    if current_tick > 0:
                        robot_utilization_individual = accumulated_active_time / current_tick
                        total_utilization += min(robot_utilization_individual, 1.0)  # 確保不超過100%
            
            robot_utilization = total_utilization / total_robots if total_robots > 0 else 0.0
            
            # 計算交叉口擁堵
            intersection_congestion = []
            for intersection in warehouse.intersection_manager.intersections:
                h_robots = len(intersection.horizontal_robots)
                v_robots = len(intersection.vertical_robots)
                total_at_intersection = h_robots + v_robots
                if total_at_intersection > 0:
                    intersection_congestion.append(total_at_intersection)
            
            avg_congestion = np.mean(intersection_congestion) if intersection_congestion else 0
            max_congestion = max(intersection_congestion) if intersection_congestion else 0
            
            result = {
                'controller_name': controller_name,
                'run_id': run_id,
                'execution_time': execution_time,
                'evaluation_ticks': self.evaluation_ticks,
                
                # 核心性能指標
                'completed_orders': completed_orders,
                'total_orders': total_orders,
                'completion_rate': completion_rate,
                
                # 時間效率指標
                'avg_wait_time': avg_wait_time,
                'max_wait_time': max_wait_time,
                'total_robots_waiting': total_robots_waiting,
                
                # 能源效率指標
                'total_energy': total_energy,
                'energy_per_order': energy_per_order,
                
                # 系統效率指標
                'robot_utilization': robot_utilization,
                'avg_intersection_congestion': avg_congestion,
                'max_intersection_congestion': max_congestion,
                
                # 其他指標
                'stop_and_go_events': getattr(warehouse, 'stop_and_go', 0),
                'warehouse_final_tick': warehouse._tick
            }
            
            self.logger.info(f"{controller_name} 運行 {run_id + 1} 完成: "
                           f"完成率 {completion_rate*100:.1f}%, "
                           f"平均等待 {avg_wait_time:.1f} ticks")
            
            return result
            
        except Exception as e:
            self.logger.error(f"評估 {controller_name} 時發生錯誤: {e}", exc_info=True)
            return None
    
    def run_evaluation(self):
        """運行完整評估"""
        self.logger.info("開始控制器性能評估")
        
        # 載入訓練好的模型
        trained_models = self.load_trained_models()
        
        # 添加傳統控制器
        controllers_to_evaluate = {
            **trained_models,
            'queue_based': {
                'type': 'queue_based',
                'reward_mode': None,
                'model_path': None,
                'metadata': {'controller_type': 'queue_based'}
            },
            'time_based': {
                'type': 'time_based', 
                'reward_mode': None,
                'model_path': None,
                'metadata': {'controller_type': 'time_based'}
            }
        }
        
        self.logger.info(f"將評估 {len(controllers_to_evaluate)} 個控制器")
        
        # 評估每個控制器
        all_results = []
        
        for controller_name, controller_config in controllers_to_evaluate.items():
            self.logger.info(f"開始評估控制器: {controller_name}")
            
            controller_results = []
            for run_id in range(self.num_runs):
                result = self.evaluate_controller(controller_name, controller_config, run_id)
                if result:
                    controller_results.append(result)
                    all_results.append(result)
            
            # 計算該控制器的平均性能
            if controller_results:
                avg_result = self.calculate_average_performance(controller_results)
                self.results[controller_name] = {
                    'individual_runs': controller_results,
                    'average_performance': avg_result,
                    'config': controller_config
                }
        
        # 保存結果
        self.save_results(all_results)
        
        # 生成比較圖表
        self.generate_comparison_charts()
        
        # 生成報告
        self.generate_evaluation_report()
        
        self.logger.info("評估完成")
        return self.results
    
    def calculate_average_performance(self, results):
        """計算平均性能"""
        if not results:
            return None
            
        avg_result = {}
        numeric_fields = [
            'execution_time', 'completed_orders', 'completion_rate',
            'avg_wait_time', 'max_wait_time', 'total_energy', 'energy_per_order',
            'robot_utilization', 'avg_intersection_congestion', 'max_intersection_congestion'
        ]
        
        for field in numeric_fields:
            values = [r[field] for r in results if field in r and r[field] is not None]
            if values:
                avg_result[field] = np.mean(values)
                avg_result[f'{field}_std'] = np.std(values)
            else:
                avg_result[field] = 0
                avg_result[f'{field}_std'] = 0
        
        avg_result['num_runs'] = len(results)
        return avg_result
    
    def save_results(self, all_results):
        """保存評估結果"""
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        
        # 保存詳細結果
        results_file = self.output_dir / f"evaluation_results_{timestamp}.json"
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump({
                'evaluation_config': {
                    'evaluation_ticks': self.evaluation_ticks,
                    'num_runs': self.num_runs,
                    'timestamp': timestamp
                },
                'results': self.results
            }, f, indent=2, ensure_ascii=False)
        
        # 保存CSV格式
        df = pd.DataFrame(all_results)
        csv_file = self.output_dir / f"evaluation_results_{timestamp}.csv"
        df.to_csv(csv_file, index=False, encoding='utf-8')
        
        self.logger.info(f"結果已保存: {results_file}, {csv_file}")
    
    def generate_comparison_charts(self):
        """生成比較圖表"""
        if not self.results:
            return
            
        # 準備數據
        controllers = []
        completion_rates = []
        avg_wait_times = []
        energy_per_orders = []
        robot_utilizations = []
        
        for name, data in self.results.items():
            avg_perf = data['average_performance']
            controllers.append(name)
            completion_rates.append(avg_perf['completion_rate'] * 100)
            avg_wait_times.append(avg_perf['avg_wait_time'])
            energy_per_orders.append(avg_perf['energy_per_order'])
            robot_utilizations.append(avg_perf['robot_utilization'] * 100)
        
        # 創建比較圖表
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('控制器性能評估比較', fontsize=16, fontweight='bold')
        
        # 設置顏色
        colors = plt.cm.Set3(np.linspace(0, 1, len(controllers)))
        
        # 完成率比較
        bars1 = axes[0,0].bar(controllers, completion_rates, color=colors)
        axes[0,0].set_title('訂單完成率比較', fontweight='bold')
        axes[0,0].set_ylabel('完成率 (%)')
        axes[0,0].tick_params(axis='x', rotation=45)
        
        # 添加數值標籤
        for bar, rate in zip(bars1, completion_rates):
            height = bar.get_height()
            axes[0,0].text(bar.get_x() + bar.get_width()/2., height + 0.5,
                          f'{rate:.1f}%', ha='center', va='bottom', fontweight='bold')
        
        # 平均等待時間比較
        bars2 = axes[0,1].bar(controllers, avg_wait_times, color=colors)
        axes[0,1].set_title('平均等待時間比較', fontweight='bold')
        axes[0,1].set_ylabel('等待時間 (ticks)')
        axes[0,1].tick_params(axis='x', rotation=45)
        
        for bar, wait in zip(bars2, avg_wait_times):
            height = bar.get_height()
            axes[0,1].text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                          f'{wait:.1f}', ha='center', va='bottom', fontweight='bold')
        
        # 能源效率比較
        bars3 = axes[1,0].bar(controllers, energy_per_orders, color=colors)
        axes[1,0].set_title('能源效率比較', fontweight='bold')
        axes[1,0].set_ylabel('每訂單能源消耗')
        axes[1,0].tick_params(axis='x', rotation=45)
        
        for bar, energy in zip(bars3, energy_per_orders):
            height = bar.get_height()
            if height > 0:
                axes[1,0].text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                              f'{energy:.0f}', ha='center', va='bottom', fontweight='bold')
        
        # 機器人利用率比較
        bars4 = axes[1,1].bar(controllers, robot_utilizations, color=colors)
        axes[1,1].set_title('機器人利用率比較', fontweight='bold')
        axes[1,1].set_ylabel('利用率 (%)')
        axes[1,1].tick_params(axis='x', rotation=45)
        
        for bar, util in zip(bars4, robot_utilizations):
            height = bar.get_height()
            axes[1,1].text(bar.get_x() + bar.get_width()/2., height + 1,
                          f'{util:.1f}%', ha='center', va='bottom', fontweight='bold')
        
        plt.tight_layout()
        
        # 保存圖表
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        chart_file = self.output_dir / f"evaluation_comparison_{timestamp}.png"
        plt.savefig(chart_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        self.logger.info(f"比較圖表已保存: {chart_file}")
    
    def generate_evaluation_report(self):
        """生成評估報告"""
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        report_file = self.output_dir / f"evaluation_report_{timestamp}.txt"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("="*60 + "\n")
            f.write("RMFS 控制器性能評估報告\n")
            f.write("="*60 + "\n")
            f.write(f"評估時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"評估時長: {self.evaluation_ticks} ticks\n")
            f.write(f"重複運行: {self.num_runs} 次\n\n")
            
            # 性能排名
            if self.results:
                # 按完成率排序
                sorted_by_completion = sorted(
                    self.results.items(),
                    key=lambda x: x[1]['average_performance']['completion_rate'],
                    reverse=True
                )
                
                f.write("1. 訂單完成率排名\n")
                f.write("-" * 30 + "\n")
                for i, (name, data) in enumerate(sorted_by_completion, 1):
                    avg_perf = data['average_performance']
                    f.write(f"{i}. {name}: {avg_perf['completion_rate']*100:.1f}% "
                           f"(±{avg_perf['completion_rate_std']*100:.1f}%)\n")
                
                # 按等待時間排序（越低越好）
                sorted_by_wait = sorted(
                    self.results.items(),
                    key=lambda x: x[1]['average_performance']['avg_wait_time']
                )
                
                f.write("\n2. 平均等待時間排名 (越低越好)\n")
                f.write("-" * 30 + "\n")
                for i, (name, data) in enumerate(sorted_by_wait, 1):
                    avg_perf = data['average_performance']
                    f.write(f"{i}. {name}: {avg_perf['avg_wait_time']:.1f} ticks "
                           f"(±{avg_perf['avg_wait_time_std']:.1f})\n")
                
                # 詳細性能分析
                f.write("\n3. 詳細性能分析\n")
                f.write("-" * 30 + "\n")
                
                for name, data in self.results.items():
                    avg_perf = data['average_performance']
                    f.write(f"\n{name}:\n")
                    f.write(f"  完成率: {avg_perf['completion_rate']*100:.1f}% (±{avg_perf['completion_rate_std']*100:.1f}%)\n")
                    f.write(f"  平均等待時間: {avg_perf['avg_wait_time']:.1f} ticks (±{avg_perf['avg_wait_time_std']:.1f})\n")
                    f.write(f"  機器人利用率: {avg_perf['robot_utilization']*100:.1f}% (±{avg_perf['robot_utilization_std']*100:.1f}%)\n")
                    f.write(f"  平均執行時間: {avg_perf['execution_time']:.1f} 秒 (±{avg_perf['execution_time_std']:.1f})\n")
                    
                    if avg_perf['energy_per_order'] > 0:
                        f.write(f"  每訂單能源消耗: {avg_perf['energy_per_order']:.0f} (±{avg_perf['energy_per_order_std']:.0f})\n")
                
                # 結論和建議
                f.write("\n4. 結論和建議\n")
                f.write("-" * 30 + "\n")
                
                best_controller = sorted_by_completion[0]
                f.write(f"• 最佳整體性能: {best_controller[0]} "
                       f"(完成率 {best_controller[1]['average_performance']['completion_rate']*100:.1f}%)\n")
                
                fastest_controller = sorted_by_wait[0]
                f.write(f"• 最低等待時間: {fastest_controller[0]} "
                       f"(平均等待 {fastest_controller[1]['average_performance']['avg_wait_time']:.1f} ticks)\n")
                
                f.write("\n建議:\n")
                f.write("• 如果追求最高完成率，建議使用 " + best_controller[0] + "\n")
                f.write("• 如果追求最低延遲，建議使用 " + fastest_controller[0] + "\n")
                f.write("• 考慮結合多種控制策略的混合方法\n")
        
        self.logger.info(f"評估報告已保存: {report_file}")

def main():
    parser = argparse.ArgumentParser(description="RMFS控制器性能評估")
    parser.add_argument('--eval_ticks', type=int, default=5000,
                       help='評估時長 (ticks)')
    parser.add_argument('--num_runs', type=int, default=3,
                       help='每個控制器的重複運行次數')
    parser.add_argument('--output_dir', default='evaluation_results',
                       help='結果輸出目錄')
    
    args = parser.parse_args()
    
    evaluator = ControllerEvaluator(
        evaluation_ticks=args.eval_ticks,
        num_runs=args.num_runs,
        output_dir=args.output_dir
    )
    
    results = evaluator.run_evaluation()
    
    print("\n" + "="*50)
    print("📊 評估完成！")
    print(f"結果保存在: {evaluator.output_dir}")
    print("="*50)
    
    return results

if __name__ == "__main__":
    main()
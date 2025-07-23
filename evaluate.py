#!/usr/bin/env python3
"""
RMFS 控制器評估腳本
用於比較不同控制器的性能
"""

import argparse
import os
import json
import time
import signal
import sys
import numpy as np
import pandas as pd
from datetime import datetime
from pathlib import Path
import matplotlib.pyplot as plt
from concurrent.futures import ProcessPoolExecutor, as_completed
from multiprocessing import cpu_count

# 設置 matplotlib 字體
try:
    from fix_matplotlib_font import setup_matplotlib_font, get_chart_labels
    chinese_support = setup_matplotlib_font()
except:
    # 如果無法載入修復模組，使用基本設置
    import matplotlib
    matplotlib.rcParams['font.sans-serif'] = ['DejaVu Sans']
    matplotlib.rcParams['axes.unicode_minus'] = False
    chinese_support = False
    
    def get_chart_labels(chinese_support=True):
        if chinese_support:
            return {
                'title': '控制器性能評估比較',
                'completion_rate': '訂單完成率比較',
                'wait_time': '平均等待時間比較',
                'energy': '能源效率比較',
                'utilization': '機器人利用率比較',
                'completion_rate_y': '完成率 (%)',
                'wait_time_y': '等待時間 (ticks)',
                'energy_y': '每訂單能源消耗',
                'utilization_y': '利用率 (%)'
            }
        else:
            return {
                'title': 'Controller Performance Comparison',
                'completion_rate': 'Order Completion Rate',
                'wait_time': 'Average Wait Time',
                'energy': 'Energy Efficiency',
                'utilization': 'Robot Utilization',
                'completion_rate_y': 'Completion Rate (%)',
                'wait_time_y': 'Wait Time (ticks)',
                'energy_y': 'Energy per Order',
                'utilization_y': 'Utilization (%)'
            }

# 全域變數用於追蹤中斷
interrupted = False

def signal_handler(sig, frame):
    """處理中斷信號"""
    global interrupted
    interrupted = True
    print("\n\n⚠️  收到中斷信號，正在安全停止評估...")
    print("請稍候，正在保存已完成的結果...")
    # 不立即退出，讓程序有機會保存結果

# 設置信號處理器
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

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
            current_tick = warehouse._tick
            
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
            
            # 計算信號切換總數
            total_signal_switches = 0
            for intersection in warehouse.intersection_manager.intersections:
                if hasattr(intersection, 'signal_switch_count'):
                    total_signal_switches += intersection.signal_switch_count
            
            # 計算平均交通流量率
            traffic_rates = []
            for intersection in warehouse.intersection_manager.intersections:
                if hasattr(intersection, 'getAverageTrafficRate'):
                    rate = intersection.getAverageTrafficRate(warehouse._tick)
                    if rate > 0:
                        traffic_rates.append(rate)
            avg_traffic_rate = np.mean(traffic_rates) if traffic_rates else 0
            
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
                
                # 交通控制指標
                'signal_switch_count': total_signal_switches,
                'avg_traffic_rate': avg_traffic_rate,
                
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
    
    def parse_controller_specs(self, controller_specs):
        """解析控制器規格列表"""
        controllers = {}
        
        for spec in controller_specs:
            if ':' in spec:
                # AI模型格式: type:path
                controller_type, model_path = spec.split(':', 1)
                
                # 從路徑推斷 reward_mode
                reward_mode = 'step' if 'step' in model_path else 'global'
                
                controller_name = f"{controller_type}_{reward_mode}_custom"
                controllers[controller_name] = {
                    'type': controller_type,
                    'reward_mode': reward_mode,
                    'model_path': model_path,
                    'metadata': {
                        'controller_type': controller_type,
                        'source': 'custom_path'
                    }
                }
            else:
                # 傳統控制器
                if spec in ['time_based', 'queue_based']:
                    controllers[spec] = {
                        'type': spec,
                        'reward_mode': None,
                        'model_path': None,
                        'metadata': {'controller_type': spec}
                    }
                else:
                    self.logger.warning(f"未知的控制器類型: {spec}")
        
        return controllers
    
    def run_evaluation(self, controller_specs=None, parallel=False):
        """運行完整評估"""
        self.logger.info("開始控制器性能評估")
        
        if controller_specs:
            # 使用指定的控制器
            controllers_to_evaluate = self.parse_controller_specs(controller_specs)
            self.logger.info(f"解析控制器規格: {controller_specs}")
            self.logger.info(f"解析結果: {list(controllers_to_evaluate.keys())}")
        else:
            # 載入所有可用的控制器
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
        
        if parallel:
            # 併行評估
            self.logger.info(f"使用併行模式評估 (最多 {cpu_count()} 進程)")
            self._run_parallel_evaluation(controllers_to_evaluate, all_results)
        else:
            # 串行評估
            for controller_name, controller_config in controllers_to_evaluate.items():
                # 檢查是否被中斷
                if interrupted:
                    self.logger.warning("評估被用戶中斷")
                    break
                    
                self.logger.info(f"開始評估控制器: {controller_name}")
                
                controller_results = []
                for run_id in range(self.num_runs):
                    # 檢查是否被中斷
                    if interrupted:
                        self.logger.warning(f"在運行 {run_id + 1}/{self.num_runs} 時被中斷")
                        break
                        
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
        
        # 保存結果（即使被中斷也要保存）
        if all_results:
            self.save_results(all_results)
            
            # 只有在沒被中斷的情況下才生成完整報告
            if not interrupted:
                # 生成比較圖表
                self.generate_comparison_charts()
                
                # 生成報告
                self.generate_evaluation_report()
                
                self.logger.info("評估完成")
            else:
                self.logger.warning("評估被中斷，已保存部分結果")
                # 保存中斷狀態
                interrupt_file = self.output_dir / "evaluation_interrupted.txt"
                with open(interrupt_file, 'w', encoding='utf-8') as f:
                    f.write(f"評估在 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} 被中斷\n")
                    f.write(f"已完成的評估: {len(all_results)} 個運行\n")
                    f.write(f"已評估的控制器: {', '.join(self.results.keys())}\n")
        else:
            self.logger.error("沒有完成任何評估")
            
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
    
    def _run_parallel_evaluation(self, controllers_to_evaluate, all_results):
        """併行運行評估"""
        max_workers = min(cpu_count(), len(controllers_to_evaluate) * self.num_runs)
        
        self.logger.info(f"併行評估配置: {len(controllers_to_evaluate)} 個控制器, "
                        f"每個運行 {self.num_runs} 次, 使用 {max_workers} 個進程")
        
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有評估任務
            future_to_task = {}
            
            for controller_name, controller_config in controllers_to_evaluate.items():
                for run_id in range(self.num_runs):
                    future = executor.submit(
                        self.evaluate_controller,
                        controller_name,
                        controller_config,
                        run_id
                    )
                    future_to_task[future] = (controller_name, run_id)
            
            # 收集結果
            controller_results_map = {name: [] for name in controllers_to_evaluate}
            
            for future in as_completed(future_to_task):
                # 檢查是否被中斷
                if interrupted:
                    self.logger.warning("併行評估被用戶中斷")
                    # 取消所有待處理的任務
                    for f in future_to_task:
                        f.cancel()
                    break
                    
                controller_name, run_id = future_to_task[future]
                try:
                    result = future.result()
                    if result:
                        controller_results_map[controller_name].append(result)
                        all_results.append(result)
                        self.logger.info(f"完成: {controller_name} (運行 {run_id + 1}/{self.num_runs})")
                except Exception as exc:
                    self.logger.error(f"評估失敗 {controller_name} (運行 {run_id + 1}): {exc}")
            
            # 計算平均性能
            for controller_name, controller_results in controller_results_map.items():
                if controller_results:
                    avg_result = self.calculate_average_performance(controller_results)
                    self.results[controller_name] = {
                        'individual_runs': controller_results,
                        'average_performance': avg_result,
                        'config': controllers_to_evaluate[controller_name]
                    }
    
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
        
        # 保存評估摘要（供評估管理器使用）
        summary_file = self.output_dir / "evaluation_summary.json"
        summary_data = {
            'timestamp': timestamp,
            'evaluation_ticks': self.evaluation_ticks,
            'num_runs': self.num_runs,
            'controllers_evaluated': list(self.results.keys()),
            'best_completion_rate': None,
            'best_controller': None
        }
        
        if self.results:
            best_controller = max(
                self.results.items(),
                key=lambda x: x[1]['average_performance']['completion_rate']
            )
            summary_data['best_controller'] = best_controller[0]
            summary_data['best_completion_rate'] = best_controller[1]['average_performance']['completion_rate']
        
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary_data, f, indent=2, ensure_ascii=False)
        
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
        
        # 獲取圖表標籤
        labels = get_chart_labels(chinese_support)
        
        # 創建比較圖表
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle(labels['title'], fontsize=16, fontweight='bold')
        
        # 設置顏色
        colors = plt.cm.Set3(np.linspace(0, 1, len(controllers)))
        
        # 完成率比較
        bars1 = axes[0,0].bar(controllers, completion_rates, color=colors)
        axes[0,0].set_title(labels['completion_rate'], fontweight='bold')
        axes[0,0].set_ylabel(labels['completion_rate_y'])
        axes[0,0].tick_params(axis='x', rotation=45)
        
        # 添加數值標籤
        for bar, rate in zip(bars1, completion_rates):
            height = bar.get_height()
            axes[0,0].text(bar.get_x() + bar.get_width()/2., height + 0.5,
                          f'{rate:.1f}%', ha='center', va='bottom', fontweight='bold')
        
        # 平均等待時間比較
        bars2 = axes[0,1].bar(controllers, avg_wait_times, color=colors)
        axes[0,1].set_title(labels['wait_time'], fontweight='bold')
        axes[0,1].set_ylabel(labels['wait_time_y'])
        axes[0,1].tick_params(axis='x', rotation=45)
        
        for bar, wait in zip(bars2, avg_wait_times):
            height = bar.get_height()
            axes[0,1].text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                          f'{wait:.1f}', ha='center', va='bottom', fontweight='bold')
        
        # 能源效率比較
        bars3 = axes[1,0].bar(controllers, energy_per_orders, color=colors)
        axes[1,0].set_title(labels['energy'], fontweight='bold')
        axes[1,0].set_ylabel(labels['energy_y'])
        axes[1,0].tick_params(axis='x', rotation=45)
        
        for bar, energy in zip(bars3, energy_per_orders):
            height = bar.get_height()
            if height > 0:
                axes[1,0].text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                              f'{energy:.0f}', ha='center', va='bottom', fontweight='bold')
        
        # 機器人利用率比較
        bars4 = axes[1,1].bar(controllers, robot_utilizations, color=colors)
        axes[1,1].set_title(labels['utilization'], fontweight='bold')
        axes[1,1].set_ylabel(labels['utilization_y'])
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
        
        # 保存簡化版本的摘要（供評估管理器顯示）
        summary_txt = self.output_dir / "evaluation_summary.txt"
        with open(summary_txt, 'w', encoding='utf-8') as f:
            f.write(f"評估時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"評估時長: {self.evaluation_ticks} ticks\n")
            f.write(f"重複次數: {self.num_runs} 次\n")
            f.write(f"評估控制器數: {len(self.results)} 個\n\n")
            
            if self.results and sorted_by_completion:
                f.write("最佳控制器排名:\n")
                for i, (name, data) in enumerate(sorted_by_completion[:3], 1):
                    avg_perf = data['average_performance']
                    f.write(f"{i}. {name}: 完成率 {avg_perf['completion_rate']*100:.1f}%\n")

def main():
    parser = argparse.ArgumentParser(description="RMFS控制器性能評估")
    parser.add_argument('--eval_ticks', type=int, default=5000,
                       help='評估時長 (ticks)')
    parser.add_argument('--num_runs', type=int, default=3,
                       help='每個控制器的重複運行次數')
    parser.add_argument('--output_dir', default='evaluation_results',
                       help='結果輸出目錄')
    parser.add_argument('--controllers', nargs='+', 
                       help='指定要評估的控制器列表 (例如: time_based queue_based dqn:path/to/model.pth)')
    parser.add_argument('--parallel', action='store_true',
                       help='啟用併行評估模式')
    
    args = parser.parse_args()
    
    evaluator = ControllerEvaluator(
        evaluation_ticks=args.eval_ticks,
        num_runs=args.num_runs,
        output_dir=args.output_dir
    )
    
    results = evaluator.run_evaluation(
        controller_specs=args.controllers,
        parallel=args.parallel
    )
    
    print("\n" + "="*50)
    print("📊 評估完成！")
    print(f"結果保存在: {evaluator.output_dir}")
    print("="*50)
    
    return results

if __name__ == "__main__":
    main()
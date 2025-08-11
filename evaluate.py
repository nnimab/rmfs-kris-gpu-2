#!/usr/bin/env python3
"""
RMFS 控制器評估腳本（簡化版）
用於執行單次評估運行並保存原始數據
"""

import argparse
import os
import json
import time
import signal
import sys
import numpy as np
from lib.constant import TICK_TO_SECOND
import pandas as pd
import pickle
from datetime import datetime
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
from multiprocessing import cpu_count

# 全域變數用於追蹤中斷
interrupted = False

def signal_handler(sig, frame):
    """處理中斷信號"""
    global interrupted
    interrupted = True
    print("[WARNING] 收到中斷信號，正在安全停止評估...")
    print("請稍候，正在保存已完成的結果...")
    # 不立即退出，讓程序有機會保存結果

# 設置信號處理器
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# 導入必要的模組
import netlogo
from lib.logger import get_logger

class ControllerEvaluator:
    def __init__(self, evaluation_ticks=5000, num_runs=3, output_dir=None):
        self.evaluation_ticks = evaluation_ticks
        self.num_runs = num_runs
        
        # 如果沒有指定輸出目錄，創建帶時間戳的子目錄
        if output_dir is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_dir = Path("result/evaluations")
            base_dir.mkdir(parents=True, exist_ok=True)
            
            # 包含 SIMULATION_ID 在目錄名稱中
            sim_id = os.environ.get('SIMULATION_ID', '')
            if sim_id:
                self.output_dir = base_dir / f"EVAL_{sim_id}_{timestamp}_{evaluation_ticks}ticks"
            else:
                self.output_dir = base_dir / f"EVAL_{timestamp}_{evaluation_ticks}ticks"
        else:
            # 如果指定了輸出目錄，也要檢查是否需要加上 SIMULATION_ID
            sim_id = os.environ.get('SIMULATION_ID', '')
            if sim_id and not str(output_dir).endswith(sim_id):
                # 在指定的目錄後面加上 SIMULATION_ID
                self.output_dir = Path(output_dir) / sim_id
            else:
                self.output_dir = Path(output_dir)
        
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
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
            self.logger.warning(f"找不到訓練模型目錄: {training_runs_dir}")
            return models
            
        # 掃描所有訓練運行目錄
        for run_dir in training_runs_dir.iterdir():
            if not run_dir.is_dir():
                continue
                
            # 尋找最佳模型
            best_model_path = run_dir / "best_model.pth"
            metadata_path = run_dir / "metadata.json"
            
            if best_model_path.exists() and metadata_path.exists():
                try:
                    with open(metadata_path, 'r') as f:
                        metadata = json.load(f)
                    
                    agent_type = metadata.get('agent_type', 'unknown')
                    reward_mode = metadata.get('reward_mode', 'unknown')
                    
                    # 創建模型標識符
                    model_key = f"{agent_type}_{reward_mode}"
                    
                    models[model_key] = {
                        'type': agent_type,
                        'reward_mode': reward_mode,
                        'model_path': str(best_model_path),
                        'metadata': metadata
                    }
                    
                    self.logger.info(f"載入模型: {model_key} from {best_model_path}")
                    
                except Exception as e:
                    self.logger.error(f"載入模型失敗 {run_dir}: {e}")
                    
        return models
        
    def evaluate_controller(self, controller_name, controller_config, run_id=0):
        """評估單個控制器"""
        self.logger.info(f"開始評估 {controller_name} (運行 {run_id + 1}/{self.num_runs})")
        
        # 檢查是否被中斷
        if interrupted:
            self.logger.warning("評估被中斷")
            return None
        
        start_time = time.time()
        
        try:
            # 初始化NetLogo模型
            # 使用 netlogo.py 的 setup 函數
            netlogo.setup()
            
            # 載入 warehouse 狀態（與 netlogo.get_state_filename() 保持一致）
            import pickle
            state_file = os.environ.get('NETLOGO_STATE_FILE')
            if not state_file:
                state_dir_env = os.environ.get('NETLOGO_STATE_DIR')
                sim_id = os.environ.get('SIMULATION_ID', '')
                if state_dir_env:
                    os.makedirs(state_dir_env, exist_ok=True)
                    state_file = os.path.join(state_dir_env, f'netlogo_{sim_id}.state') if sim_id else os.path.join(state_dir_env, 'netlogo.state')
                else:
                    state_dir = 'states'
                    os.makedirs(state_dir, exist_ok=True)
                    state_file = os.path.join(state_dir, f'netlogo_{sim_id}.state') if sim_id else os.path.join(state_dir, 'netlogo.state')
            with open(state_file, 'rb') as file:
                warehouse = pickle.load(file)
            
            # 創建控制器實例
            controller_type = controller_config['type']
            controller = None
            
            if controller_type == 'dqn':
                # 延遲載入，避免非 DQN 情境下依賴 torch
                from ai.controllers.dqn_controller import DQNController
                controller = DQNController(
                    model_path=controller_config['model_path'],
                    reward_mode=controller_config['reward_mode']
                )
            elif controller_type == 'nerl':
                from ai.controllers.nerl_controller import NEController
                controller = NEController(
                    model_path=controller_config['model_path'],
                    reward_mode=controller_config['reward_mode']
                )
            elif controller_type == 'queue_based':
                # 檢查是否有參數值
                from ai.controllers.queue_based_controller import QueueBasedController
                if 'param_value' in controller_config:
                    # 假設參數值是 min_green_time
                    min_green_time = int(controller_config['param_value'])
                    controller = QueueBasedController(min_green_time=min_green_time)
                else:
                    controller = QueueBasedController()
            elif controller_type == 'time_based':
                # 檢查是否有參數值
                from ai.controllers.time_based_controller import TimeBasedController
                if 'param_value' in controller_config:
                    # 參數值格式是 "60:40"，解析為水平和垂直時間
                    ratio_parts = controller_config['param_value'].split(':')
                    horizontal_time = int(ratio_parts[0])
                    vertical_time = int(ratio_parts[1])
                    controller = TimeBasedController(
                        horizontal_green_time=horizontal_time,
                        vertical_green_time=vertical_time
                    )
                else:
                    controller = TimeBasedController()
            elif controller_type == 'none':
                # 無控制器模式
                controller = None
                self.logger.info("使用無控制器模式 - 不進行交通控制")
            else:
                raise ValueError(f"未知的控制器類型: {controller_type}")
            
            # 設置控制器（如果有的話）
            if controller is not None:
                # 使用 warehouse 的 set_traffic_controller 方法
                warehouse.set_traffic_controller(controller_type, model_path=controller_config.get('model_path'))
            else:
                # 無控制器模式 - 不啟用交通控制
                warehouse.update_intersection_using_RL = False
                warehouse.current_controller = "none"
            
            # 運行評估
            self.logger.info(f"開始運行 {self.evaluation_ticks} ticks...")
            
            # 初始化統計變數
            metrics = {
                'completed_orders': 0,
                'total_orders': 0,
                'total_wait_time': 0,
                'total_robots': 0,
                'total_robot_active_time': 0,
                'total_energy_consumed': 0,
                'signal_switch_count': 0,
                'avg_traffic_rate': 0.0,
                'time_per_tick': []
            }
            
            # 主評估循環
            tick_interval = 100  # 每100個tick記錄一次
            save_interval = 5000  # 每5000個tick保存一次狀態（減少I/O）
            
            for tick in range(self.evaluation_ticks):
                # 檢查是否被中斷
                if interrupted:
                    self.logger.warning(f"在 tick {tick} 被中斷")
                    break
                    
                tick_start = time.time()
                
                # 執行一個tick
                warehouse.tick()
                
                # 只在特定間隔或最後一個tick時保存狀態
                if tick % save_interval == 0 or tick == self.evaluation_ticks - 1:
                    with open(state_file, 'wb') as file:
                        pickle.dump(warehouse, file)
                    self.logger.debug(f"保存狀態在 tick {tick}")
                
                # 記錄時間
                tick_time = time.time() - tick_start
                metrics['time_per_tick'].append(tick_time)
                
                # 定期收集統計
                if tick % tick_interval == 0 or tick == self.evaluation_ticks - 1:
                    # 收集當前統計
                    current_completed = len(warehouse.order_manager.finished_orders)
                    current_total = len(warehouse.order_manager.orders)
                    
                    # 容量測試模式下，輸出到 stdout 供監控器使用
                    if os.environ.get('CAPACITY_TEST_MODE') == '1' and tick % 100 == 0:
                        print(f"Tick: {tick}/{self.evaluation_ticks} | 完成訂單: {current_completed}/{current_total} | 機器人: {len(warehouse.robot_manager.robots)}", flush=True)
                    
                    # 更新累計統計
                    metrics['completed_orders'] = current_completed
                    metrics['total_orders'] = current_total
                    
                    # 收集機器人統計
                    total_robots = len(warehouse.robot_manager.robots)
                    working_robots = len([r for r in warehouse.robot_manager.robots if hasattr(r, 'route_stop_points') and len(r.route_stop_points) > 0])
                    
                    metrics['total_robots'] = total_robots
                    
                    # 收集機器人活動時間
                    total_active_time = 0
                    current_tick = warehouse._tick
                    for robot in warehouse.robot_manager.robots:
                        if hasattr(robot, 'get_current_active_time'):
                            # 使用新方法獲取包含當前活動的總時間
                            total_active_time += robot.get_current_active_time(current_tick)
                        elif hasattr(robot, 'total_active_time'):
                            # 向後相容：如果沒有新方法，使用舊屬性
                            total_active_time += robot.total_active_time
                    metrics['total_robot_active_time'] = total_active_time

                    #（移除抽樣狀態占比邏輯）
                    
                    # 收集等待時間（以事件累積為準）
                    if 'all_wait_events' not in metrics:
                        metrics['all_wait_events'] = []
                    if 'total_wait_time' not in metrics:
                        metrics['total_wait_time'] = 0
                    if 'wait_event_cursor' not in metrics:
                        metrics['wait_event_cursor'] = {}
                    # 讀取各路口的事件紀錄
                    try:
                        for inter in warehouse.intersection_manager.intersections:
                            if hasattr(inter, 'waiting_time_records') and inter.waiting_time_records:
                                prev_n = metrics['wait_event_cursor'].get(inter.id, 0)
                                records = inter.waiting_time_records
                                if prev_n < len(records):
                                    new_records = records[prev_n:]
                                    for _, wt in new_records:
                                        if wt > 0:
                                            metrics['all_wait_events'].append(wt)
                                            metrics['total_wait_time'] += wt
                                    metrics['wait_event_cursor'][inter.id] = len(records)
                    except Exception:
                        # 相容舊版：退回以快照估計（不再作累積）
                        current_tick_wait = sum(
                            sum(robot.intersection_wait_time.values())
                            for robot in warehouse.robot_manager.robots
                            if hasattr(robot, 'intersection_wait_time')
                        )
                        metrics['total_wait_time'] += current_tick_wait
                    
                    # 收集能源消耗
                    # 使用 warehouse.total_energy 而非機器人累計，以保持與歷史評估的一致性
                    metrics['total_energy_consumed'] = warehouse.total_energy
                    
                    # 收集交通控制統計
                    # 從所有路口收集信號切換次數
                    total_signal_switches = 0
                    for intersection in warehouse.intersection_manager.intersections:
                        if hasattr(intersection, 'signal_switch_count'):
                            total_signal_switches += intersection.signal_switch_count
                    metrics['signal_switch_count'] = total_signal_switches
                    
                    # 收集平均交通流率（如果控制器支援）
                    if controller is not None and hasattr(controller, 'getAverageTrafficRate'):
                        metrics['avg_traffic_rate'] = controller.getAverageTrafficRate()
                    else:
                        # 計算平均交通流率：總通過機器人數 / 總路口數 / 時間
                        total_passed = 0
                        for intersection in warehouse.intersection_manager.intersections:
                            total_passed += intersection.total_robots_passed
                        if len(warehouse.intersection_manager.intersections) > 0 and tick > 0:
                            metrics['avg_traffic_rate'] = total_passed / len(warehouse.intersection_manager.intersections) / tick
                        else:
                            metrics['avg_traffic_rate'] = 0.0
                    
                    # 記錄進度
                    if tick % 1000 == 0:
                        # 容量測試模式下，同時輸出到 stdout 供監控器讀取
                        if os.environ.get('CAPACITY_TEST_MODE') == '1':
                            print(f"進度: {tick}/{self.evaluation_ticks} ticks, 完成訂單: {current_completed}/{current_total}", flush=True)
                        self.logger.info(f"  進度: {tick}/{self.evaluation_ticks} ticks, "
                                       f"完成訂單: {current_completed}/{current_total}")
            
            # 計算最終統計
            execution_time = time.time() - start_time
            final_tick = warehouse._tick
            
            # 計算衍生指標
            completion_rate = metrics['completed_orders'] / metrics['total_orders'] if metrics['total_orders'] > 0 else 0
            
            # 平均等待時間計算（與訓練保持一致，採用事件累積）
            if 'all_wait_events' in metrics and len(metrics['all_wait_events']) > 0:
                avg_wait_time = sum(metrics['all_wait_events']) / len(metrics['all_wait_events'])
            else:
                avg_wait_time = 0
            robot_utilization = metrics['total_robot_active_time'] / (final_tick * metrics['total_robots']) if metrics['total_robots'] > 0 else 0
            # 單位校正：步數/秒 → 乘上 TICK_TO_SECOND（例如 0.15），讓結果落在 0~1 範圍
            robot_utilization = robot_utilization * TICK_TO_SECOND
            energy_per_order = metrics['total_energy_consumed'] / metrics['completed_orders'] if metrics['completed_orders'] > 0 else 0
            
            # 組裝結果
            result = {
                'controller_name': controller_name,
                'controller_type': controller_type,
                'run_id': run_id,
                'evaluation_ticks': self.evaluation_ticks,
                'warehouse_final_tick': final_tick,
                'completed_orders': metrics['completed_orders'],
                'total_orders': metrics['total_orders'],
                'completion_rate': completion_rate,
                'avg_wait_time': avg_wait_time,
                'max_wait_time': (max(metrics['all_wait_events']) if ('all_wait_events' in metrics and metrics['all_wait_events']) else 0),
                'total_wait_time': metrics.get('total_wait_time', 0),
                'robot_utilization': robot_utilization,
                'total_energy': metrics['total_energy_consumed'],
                'energy_per_order': energy_per_order,
                'signal_switch_count': metrics['signal_switch_count'],
                'avg_traffic_rate': metrics['avg_traffic_rate'],
                'execution_time': execution_time,
                'avg_tick_time': np.mean(metrics['time_per_tick']) if metrics['time_per_tick'] else 0,
                'timestamp': datetime.now().isoformat()
            }
            
            # 添加元數據
            if 'metadata' in controller_config:
                result['controller_metadata'] = controller_config['metadata']
            
            self.logger.info(f"評估完成: {controller_name} (運行 {run_id + 1}), "
                           f"完成率: {completion_rate*100:.1f}%, "
                           f"執行時間: {execution_time:.1f}秒")
            
            # 清理
            # 清理臨時檔案（僅在沒有要求保留時）
            if os.environ.get('KEEP_STATE_FILE') != '1' and os.path.exists(state_file):
                try:
                    os.remove(state_file)
                except Exception:
                    pass
            
            return result
            
        except Exception as e:
            self.logger.error(f"評估 {controller_name} 失敗: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def parse_controller_specs(self, controller_specs):
        """解析控制器規格"""
        controllers = {}
        
        for spec in controller_specs:
            if ':' in spec:
                parts = spec.split(':', 1)
                controller_type = parts[0]
                
                if controller_type in ['time_based', 'queue_based']:
                    # 基準控制器格式: time_based:60:40 或 queue_based:3
                    param_value = parts[1]
                    controller_name = f"{controller_type}_{param_value.replace(':', '')}"
                    
                    controllers[controller_name] = {
                        'type': controller_type,
                        'reward_mode': None,
                        'model_path': None,
                        'param_value': param_value,
                        'metadata': {
                            'controller_type': controller_type,
                            'param_value': param_value
                        }
                    }
                else:
                    # AI模型格式: type:path/to/model.pth
                    model_path = parts[1]
                    
                    # 從路徑中提取名稱
                    model_name = Path(model_path).stem
                    controller_name = f"{controller_type}_{model_name}"
                    
                    # 嘗試推斷reward_mode
                    if 'step' in model_name:
                        reward_mode = 'step'
                    elif 'global' in model_name:
                        reward_mode = 'global'
                    else:
                        reward_mode = 'unknown'
                    
                    controllers[controller_name] = {
                        'type': controller_type,
                        'reward_mode': reward_mode,
                        'model_path': model_path,
                        'metadata': {
                            'controller_type': controller_type,
                            'model_path': model_path
                        }
                    }
            else:
                # 傳統控制器
                controllers[spec] = {
                    'type': spec,
                    'reward_mode': None,
                    'model_path': None,
                    'metadata': {'controller_type': spec}
                }
        
        return controllers
    
    def run_evaluation(self, controller_specs=None, parallel=False):
        """運行完整評估"""
        self.logger.info("開始控制器性能評估")
        
        if controller_specs is not None:
            # 使用指定的控制器
            controllers_to_evaluate = self.parse_controller_specs(controller_specs)
            self.logger.info(f"解析控制器規格: {controller_specs}")
            self.logger.info(f"解析結果: {list(controllers_to_evaluate.keys())}")
        else:
            # 無控制器模式
            self.logger.info("未指定控制器，將執行無控制器評估模式")
            controllers_to_evaluate = {
                'no_controller': {
                    'type': 'none',
                    'reward_mode': None,
                    'model_path': None,
                    'metadata': {'controller_type': 'none'}
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
                
                # 保存該控制器的結果
                if controller_results:
                    self.results[controller_name] = {
                        'individual_runs': controller_results,
                        'config': controller_config
                    }
        
        # 保存結果（即使被中斷也要保存）
        if all_results:
            self.save_results(all_results)
            
            if not interrupted:
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
                        self.logger.info(f"完成: {controller_name} (運行 {run_id + 1})")
                except Exception as e:
                    self.logger.error(f"評估失敗 {controller_name} (運行 {run_id + 1}): {e}")
            
            # 整理結果
            for controller_name, controller_results in controller_results_map.items():
                if controller_results:
                    self.results[controller_name] = {
                        'individual_runs': controller_results,
                        'config': controllers_to_evaluate[controller_name]
                    }
    
    def save_results(self, all_results):
        """保存評估結果"""
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        
        # 保存詳細結果
        results_file = self.output_dir / "evaluation_results.json"
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump({
                'evaluation_config': {
                    'evaluation_ticks': self.evaluation_ticks,
                    'num_runs': self.num_runs,
                    'timestamp': timestamp
                },
                'results': all_results,
                'controllers_evaluated': list(self.results.keys())
            }, f, indent=2, ensure_ascii=False)
        
        # 保存CSV格式
        df = pd.DataFrame(all_results)
        csv_file = self.output_dir / "evaluation_results.csv"
        df.to_csv(csv_file, index=False, encoding='utf-8')
        
        # 保存評估摘要
        summary_file = self.output_dir / "evaluation_summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump({
                'timestamp': timestamp,
                'evaluation_ticks': self.evaluation_ticks,
                'num_runs': self.num_runs,
                'controllers_evaluated': list(self.results.keys()),
                'total_runs_completed': len(all_results),
                'interrupted': interrupted
            }, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"結果已保存: {results_file}, {csv_file}")

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
    parser.add_argument('--seed', type=int, default=42,
                       help='隨機種子')
    parser.add_argument('--robot-count', type=int, default=20,
                       help='機器人數量 (預設: 20)')
    # 為了向後相容，同時支援兩種參數格式
    parser.add_argument('--ticks', type=int, dest='eval_ticks',
                       help='評估時長 (ticks) - 與 --eval_ticks 相同')
    parser.add_argument('--runs', type=int, dest='num_runs',
                       help='重複運行次數 - 與 --num_runs 相同')
    parser.add_argument('--output-dir', dest='output_dir',
                       help='結果輸出目錄 - 與 --output_dir 相同')
    
    args = parser.parse_args()
    
    # 設置隨機種子
    np.random.seed(args.seed)
    
    # 設置環境變數以傳遞機器人數量
    os.environ['ROBOT_COUNT'] = str(args.robot_count)
    
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
    print("[INFO] 評估完成！")
    print(f"結果保存在: {evaluator.output_dir}")
    print("="*50)
    
    return results

if __name__ == "__main__":
    main()
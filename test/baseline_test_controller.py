#!/usr/bin/env python3
"""
基準模型參數掃描控制器
用於執行 Time-Based 和 Queue-Based 控制器的參數優化測試
"""

import os
import sys
import json
import time
import uuid
import subprocess
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
from concurrent.futures import ProcessPoolExecutor, as_completed

# 加入專案根目錄到 Python 路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from lib.logger import get_logger

class BaselineTestController:
    """基準模型測試控制器"""
    
    def __init__(self, base_output_dir: Optional[str] = None):
        """
        初始化控制器
        
        Args:
            base_output_dir: 基礎輸出目錄路徑，如果為 None 則使用預設路徑
        """
        self.instance_id = str(uuid.uuid4())[:8]
        self.test_start_time = datetime.now()
        
        # 設定輸出目錄 - 使用與容量測試相同的結構
        if base_output_dir is None:
            timestamp = self.test_start_time.strftime("%Y%m%d_%H%M%S")
            self.base_output_dir = Path(__file__).parent / "results" / f"baseline_{timestamp}_{self.instance_id}"
        else:
            self.base_output_dir = Path(base_output_dir)
        
        self.base_output_dir.mkdir(parents=True, exist_ok=True)
        
        # 設置日誌
        log_file = self.base_output_dir / "baseline_test.log"
        self.logger = get_logger(log_file_path=str(log_file))
        
        # 初始化隔離管理器
        from test.isolation_manager import IsolationManager
        self.isolation_manager = IsolationManager(self.base_output_dir, self.logger)
        
        # 測試結果儲存
        self.test_results = {}
        
        self.logger.info(f"基準模型測試控制器初始化完成")
        self.logger.info(f"實例 ID: {self.instance_id}")
        self.logger.info(f"輸出目錄: {self.base_output_dir}")
    
    def run_time_based_sweep(self, 
                           robot_counts: List[int],
                           time_ratios: List[str],
                           runs_per_config: int = 3,
                           test_ticks: int = 100000,
                           parallel: bool = True,
                           max_parallel: Optional[int] = None) -> Dict[str, Any]:
        """
        執行 Time-Based 控制器參數掃描
        
        Args:
            robot_counts: 機器人數量列表
            time_ratios: 時間配比列表 (如 ["60:40", "70:30"])
            runs_per_config: 每個配置的運行次數
            test_ticks: 測試 tick 數
            parallel: 是否並行執行
            max_parallel: 最大並行數
            
        Returns:
            測試結果摘要
        """
        self.logger.info("開始 Time-Based 參數掃描")
        self.logger.info(f"機器人數量: {robot_counts}")
        self.logger.info(f"時間配比: {time_ratios}")
        self.logger.info(f"每個配置運行次數: {runs_per_config}")
        
        # 創建測試會話目錄
        session_dir = self.base_output_dir / "time_based"
        session_dir.mkdir(parents=True, exist_ok=True)
        
        # 準備所有測試配置
        test_configs = []
        for robot_count in robot_counts:
            for time_ratio in time_ratios:
                for run_idx in range(runs_per_config):
                    test_id = f"tb_r{robot_count}_t{time_ratio.replace(':', '')}_run{run_idx}"
                    config = {
                        'test_id': test_id,
                        'robot_count': robot_count,
                        'controller': 'time_based',
                        'time_ratio': time_ratio,
                        'run_index': run_idx,
                        'test_ticks': test_ticks,
                        'base_output_dir': str(self.base_output_dir)
                    }
                    test_configs.append(config)
        
        # 執行測試
        results = self._execute_tests(test_configs, parallel, max_parallel)
        
        # 生成摘要
        summary = self._generate_summary(results, session_dir, "time_based")
        summary['time_ratios'] = time_ratios
        summary['robot_counts'] = robot_counts
        
        return summary
    
    def run_queue_based_sweep(self,
                            robot_counts: List[int],
                            queue_thresholds: List[int],
                            runs_per_config: int = 3,
                            test_ticks: int = 100000,
                            parallel: bool = True,
                            max_parallel: Optional[int] = None) -> Dict[str, Any]:
        """
        執行 Queue-Based 控制器參數掃描
        
        Args:
            robot_counts: 機器人數量列表
            queue_thresholds: 隊列閾值列表
            runs_per_config: 每個配置的運行次數
            test_ticks: 測試 tick 數
            parallel: 是否並行執行
            max_parallel: 最大並行數
            
        Returns:
            測試結果摘要
        """
        self.logger.info("開始 Queue-Based 參數掃描")
        self.logger.info(f"機器人數量: {robot_counts}")
        self.logger.info(f"隊列閾值: {queue_thresholds}")
        self.logger.info(f"每個配置運行次數: {runs_per_config}")
        
        # 創建測試會話目錄
        session_dir = self.base_output_dir / "queue_based"
        session_dir.mkdir(parents=True, exist_ok=True)
        
        # 準備所有測試配置
        test_configs = []
        for robot_count in robot_counts:
            for threshold in queue_thresholds:
                for run_idx in range(runs_per_config):
                    test_id = f"qb_r{robot_count}_q{threshold}_run{run_idx}"
                    config = {
                        'test_id': test_id,
                        'robot_count': robot_count,
                        'controller': 'queue_based',
                        'queue_threshold': threshold,
                        'run_index': run_idx,
                        'test_ticks': test_ticks,
                        'base_output_dir': str(self.base_output_dir)
                    }
                    test_configs.append(config)
        
        # 執行測試
        results = self._execute_tests(test_configs, parallel, max_parallel)
        
        # 生成摘要
        summary = self._generate_summary(results, session_dir, "queue_based")
        summary['queue_thresholds'] = queue_thresholds
        summary['robot_counts'] = robot_counts
        
        return summary
    
    def _execute_tests(self, test_configs: List[Dict[str, Any]], 
                      parallel: bool, max_parallel: Optional[int]) -> List[Dict[str, Any]]:
        """執行測試配置"""
        if max_parallel is None:
            max_parallel = max(1, os.cpu_count() // 2) if parallel else 1
        
        self.logger.info(f"開始執行測試，總數: {len(test_configs)}, 並行: {parallel}, 最大並行數: {max_parallel}")
        
        all_results = []
        start_time = time.time()
        
        if parallel and max_parallel > 1:
            # 並行執行
            # 在 Windows 下需要使用頂層函數
            import platform
            if platform.system() == 'Windows':
                # Windows 下使用包裝函數
                from test.baseline_test_controller import run_single_test_wrapper
                with ProcessPoolExecutor(max_workers=max_parallel) as executor:
                    future_to_config = {
                        executor.submit(run_single_test_wrapper, config): config
                        for config in test_configs
                    }
                    
                    for future in as_completed(future_to_config):
                        config = future_to_config[future]
                        try:
                            result = future.result()
                            all_results.append(result)
                            self.logger.info(f"完成測試: {config['test_id']}")
                        except Exception as e:
                            self.logger.error(f"測試失敗 {config['test_id']}: {e}")
                            error_result = {
                                'test_id': config['test_id'],
                                'robot_count': config['robot_count'],
                                'status': 'failed',
                                'error': str(e),
                                **config
                            }
                            all_results.append(error_result)
            else:
                # 其他平台可以直接使用方法
                with ProcessPoolExecutor(max_workers=max_parallel) as executor:
                    future_to_config = {
                        executor.submit(self._run_single_test, config): config
                        for config in test_configs
                    }
                    
                    for future in as_completed(future_to_config):
                        config = future_to_config[future]
                        try:
                            result = future.result()
                            all_results.append(result)
                            self.logger.info(f"完成測試: {config['test_id']}")
                        except Exception as e:
                            self.logger.error(f"測試失敗 {config['test_id']}: {e}")
                            error_result = {
                                'test_id': config['test_id'],
                                'robot_count': config['robot_count'],
                                'status': 'failed',
                                'error': str(e),
                                **config
                            }
                            all_results.append(error_result)
        else:
            # 串行執行
            for config in test_configs:
                result = self._run_single_test(config)
                all_results.append(result)
        
        total_time = time.time() - start_time
        self.logger.info(f"所有測試完成，總時間: {total_time:.1f} 秒")
        
        return all_results
    
    def _run_single_test(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """執行單個測試"""
        test_id = config['test_id']
        robot_count = config['robot_count']
        
        try:
            self.logger.info(f"開始測試: {test_id}")
            
            # 創建隔離工作空間
            isolated_paths = self.isolation_manager.create_isolated_workspace(robot_count, test_id)
            
            # 設置環境變數
            env = os.environ.copy()
            env.update(self.isolation_manager.get_isolated_env_vars(test_id))
            
            # 準備評估命令
            python_exe = sys.executable
            
            # 構建控制器參數
            if config['controller'] == 'time_based':
                controller_args = f"time_based:{config['time_ratio']}"
            else:  # queue_based
                controller_args = f"queue_based:{config['queue_threshold']}"
            
            eval_args = [
                python_exe, 'evaluate.py',
                '--controllers', controller_args,
                '--ticks', str(config['test_ticks']),
                '--runs', '1',
                '--output-dir', isolated_paths['results_dir'],
                '--robot-count', str(robot_count)
            ]
            
            # 執行評估
            start_time = time.time()
            process = subprocess.Popen(
                eval_args,
                env=env,
                cwd=str(project_root),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            stdout, stderr = process.communicate()
            execution_time = time.time() - start_time
            
            if process.returncode == 0:
                # 嘗試讀取評估結果
                result = {
                    'test_id': test_id,
                    'robot_count': robot_count,
                    'status': 'completed',
                    'execution_time': execution_time,
                    'workspace_path': isolated_paths['workspace_root'],
                    **config
                }
                
                # 讀取評估結果文件
                results_file = Path(isolated_paths['results_dir']) / 'evaluation_results.json'
                if results_file.exists():
                    with open(results_file, 'r', encoding='utf-8') as f:
                        eval_results = json.load(f)
                    if eval_results.get('results'):
                        # 提取關鍵指標
                        metrics = eval_results['results'][0]
                        result['completion_rate'] = metrics.get('completion_rate', 0)
                        result['avg_wait_time'] = metrics.get('avg_wait_time', 0)
                        result['robot_utilization'] = metrics.get('robot_utilization', 0)
                        result['total_energy'] = metrics.get('total_energy', 0)
                
                self.logger.info(f"測試完成: {test_id}, 完成率: {result.get('completion_rate', 0):.1%}")
                
            else:
                result = {
                    'test_id': test_id,
                    'robot_count': robot_count,
                    'status': 'failed',
                    'execution_time': execution_time,
                    'error_code': process.returncode,
                    'stderr': stderr,
                    'workspace_path': isolated_paths['workspace_root'],
                    **config
                }
                self.logger.error(f"測試失敗: {test_id}, 錯誤碼: {process.returncode}")
                self.logger.error(f"錯誤輸出: {stderr}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"執行測試時發生異常 {test_id}: {e}")
            return {
                'test_id': test_id,
                'robot_count': robot_count,
                'status': 'error',
                'error': str(e),
                **config
            }
    
    def _generate_summary(self, results: List[Dict[str, Any]], 
                         session_dir: Path, test_type: str) -> Dict[str, Any]:
        """生成測試摘要"""
        completed_tests = len([r for r in results if r['status'] == 'completed'])
        failed_tests = len([r for r in results if r['status'] != 'completed'])
        total_execution_time = sum(r.get('execution_time', 0) for r in results)
        
        # 按參數分組結果
        results_by_parameter = {}
        for result in results:
            robot_count = result['robot_count']
            if test_type == 'time_based':
                param_value = result['time_ratio']
            else:
                param_value = result['queue_threshold']
            
            key = (robot_count, param_value)
            if key not in results_by_parameter:
                results_by_parameter[key] = []
            results_by_parameter[key].append(result)
        
        # 生成摘要
        summary = {
            'test_type': test_type,
            'session_id': self.base_output_dir.name,
            'total_tests': len(results),
            'completed_tests': completed_tests,
            'failed_tests': failed_tests,
            'total_execution_time': total_execution_time,
            'start_time': datetime.now().isoformat(),
            'output_dir': str(session_dir),
            'results': results,
            'results_by_parameter': results_by_parameter
        }
        
        # 保存摘要
        summary_file = session_dir / 'baseline_test_summary.json'
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"測試摘要已保存: {summary_file}")
        
        return summary

# 定義一個頂層函數來支援 Windows 下的多進程
def run_single_test_wrapper(config: Dict[str, Any]) -> Dict[str, Any]:
    """包裝函數，用於在 Windows 下支援多進程"""
    # 從配置中取得基礎輸出目錄
    base_dir = config.get('base_output_dir')
    controller = BaselineTestController(base_output_dir=base_dir)
    return controller._run_single_test(config)


def main():
    """主函數，用於命令列執行"""
    import argparse
    
    parser = argparse.ArgumentParser(description='基準模型參數掃描')
    parser.add_argument('--robot-counts', nargs='+', type=int, default=[30, 35],
                       help='要測試的機器人數量列表')
    parser.add_argument('--ticks', type=int, default=100000,
                       help='每個測試的 tick 數')
    parser.add_argument('--runs', type=int, default=3,
                       help='每個配置的運行次數')
    parser.add_argument('--type', choices=['time_based', 'queue_based'], required=True,
                       help='測試類型')
    
    args = parser.parse_args()
    
    # 創建測試控制器
    controller = BaselineTestController()
    
    try:
        if args.type == 'time_based':
            # 執行 Time-Based 測試
            summary = controller.run_time_based_sweep(
                robot_counts=args.robot_counts,
                time_ratios=["50:50", "60:40", "65:35", "70:30", "75:25", "80:20"],
                runs_per_config=args.runs,
                test_ticks=args.ticks,
                parallel=True
            )
        else:
            # 執行 Queue-Based 測試
            summary = controller.run_queue_based_sweep(
                robot_counts=args.robot_counts,
                queue_thresholds=[2, 3, 4, 5, 6],
                runs_per_config=args.runs,
                test_ticks=args.ticks,
                parallel=True
            )
        
        print(f"\n=== {args.type} 測試完成 ===")
        print(f"成功測試: {summary['completed_tests']}/{summary['total_tests']}")
        print(f"總執行時間: {summary['total_execution_time']:.1f} 秒")
        print(f"結果目錄: {summary['output_dir']}")
        
    except KeyboardInterrupt:
        print("\n測試被用戶中斷")
    except Exception as e:
        print(f"測試執行時發生錯誤: {e}")
        controller.logger.error(f"測試執行時發生錯誤: {e}")


if __name__ == '__main__':
    main()

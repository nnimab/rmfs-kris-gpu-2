#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RMFS 系統容量壓力測試控制器

主要功能：
1. 跨平台支援（Windows 和 Linux）
2. 並行執行多個機器人數量測試
3. 完全資源隔離（狀態檔案、CSV檔案等）
4. 長時間運行支援（100,000+ ticks）
"""

import uuid
import platform
import os
import sys
import json
import time
import logging
import subprocess
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
import shutil
import signal
import threading

# 加入專案根目錄到 Python 路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from test.isolation_manager import IsolationManager
from test.test_monitor import TestMonitor
from lib.logger import get_logger


class CapacityTestController:
    """RMFS 系統容量壓力測試控制器"""
    
    def __init__(self, base_output_dir: Optional[str] = None, enable_monitor: bool = True):
        """
        初始化測試控制器
        
        Args:
            base_output_dir: 基礎輸出目錄路徑，如果為 None 則使用預設路徑
            enable_monitor: 是否啟用測試監控器
        """
        self.instance_id = str(uuid.uuid4())[:8]
        self.platform = platform.system()
        self.test_start_time = datetime.now()
        
        # 設定輸出目錄
        if base_output_dir is None:
            timestamp = self.test_start_time.strftime("%Y%m%d_%H%M%S")  
            self.base_output_dir = Path(__file__).parent / "results" / f"capacity_test_{timestamp}_{self.instance_id}"
        else:
            self.base_output_dir = Path(base_output_dir)
        
        self.base_output_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化日誌
        log_file = self.base_output_dir / "capacity_test.log"
        self.logger = get_logger(log_file_path=str(log_file))
        
        # 初始化隔離管理器
        self.isolation_manager = IsolationManager(self.base_output_dir, self.logger)
        
        # 初始化測試監控器
        self.enable_monitor = enable_monitor
        self.test_monitor = None
        if self.enable_monitor:
            self.test_monitor = TestMonitor(self.base_output_dir)
        
        # 測試狀態追蹤
        self.running_tests = {}  # test_id -> process_info
        self.completed_tests = {}  # test_id -> result
        self.failed_tests = {}  # test_id -> error_info
        
        # 背景執行標記
        self.background_mode = False
        self.background_thread = None
        
        # 設定信號處理器
        self._setup_signal_handlers()
        
        self.logger.info(f"容量測試控制器初始化完成")
        self.logger.info(f"實例 ID: {self.instance_id}")
        self.logger.info(f"平台: {self.platform}")
        self.logger.info(f"輸出目錄: {self.base_output_dir}")
        self.logger.info(f"監控器: {'啟用' if self.enable_monitor else '停用'}")
    
    def _setup_signal_handlers(self):
        """設定信號處理器以優雅地停止測試"""
        def signal_handler(signum, frame):
            self.logger.warning(f"收到信號 {signum}，正在停止所有測試...")
            self.stop_all_tests()
            sys.exit(0)
        
        if hasattr(signal, 'SIGINT'):
            signal.signal(signal.SIGINT, signal_handler)
        if hasattr(signal, 'SIGTERM'):
            signal.signal(signal.SIGTERM, signal_handler)
    
    def get_isolated_paths(self, robot_count: int, test_id: str) -> Dict[str, str]:
        """
        為特定測試產生隔離的檔案路徑
        
        Args:
            robot_count: 機器人數量
            test_id: 測試唯一 ID
            
        Returns:
            包含所有隔離路徑的字典
        """
        return self.isolation_manager.create_isolated_workspace(robot_count, test_id)
    
    def _prepare_test_environment(self, robot_count: int, test_id: str, 
                                test_ticks: int = 100000) -> Dict[str, Any]:
        """
        準備測試環境
        
        Args:
            robot_count: 機器人數量
            test_id: 測試 ID
            test_ticks: 測試 tick 數
            
        Returns:
            測試配置字典
        """
        # 創建隔離工作空間
        isolated_paths = self.get_isolated_paths(robot_count, test_id)
        
        # 創建測試配置
        test_config = {
            'robot_count': robot_count,
            'test_id': test_id,
            'test_ticks': test_ticks,
            'controller_type': 'none',  # 無控制器模式
            'isolated_paths': isolated_paths,
            'start_time': datetime.now().isoformat(),
            'platform': self.platform,
            'instance_id': self.instance_id
        }
        
        # 保存測試配置
        config_file = Path(isolated_paths['workspace_root']) / 'test_config.json'
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(test_config, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"測試環境準備完成 - 機器人數量: {robot_count}, ID: {test_id}")
        
        return test_config
    
    def _run_single_test(self, test_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        執行單個容量測試
        
        Args:
            test_config: 測試配置
            
        Returns:
            測試結果
        """
        test_id = test_config['test_id']
        robot_count = test_config['robot_count']
        
        try:
            self.logger.info(f"開始執行測試 {test_id} (機器人數量: {robot_count})")
            
            # 設定環境變數
            env = os.environ.copy()
            env.update(self.isolation_manager.get_isolated_env_vars(test_id))
            # 標記為容量測試模式，讓 evaluate.py 輸出進度到 stdout
            env['CAPACITY_TEST_MODE'] = '1'
            # 使用既有訂單資料，禁止在並行時重生/合併訂單
            env['USE_EXISTING_ORDERS'] = '1'
            
            # 準備評估參數

            
            # 確保使用 venv 的 Python（如果存在）

            
            python_exe = sys.executable

            
            if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):

            
                # 在虛擬環境中，確保使用正確的 Python

            
                python_exe = sys.executable

            
            else:

            
                # 不在虛擬環境中，嘗試找 venv

            
                venv_python = Path(project_root) / '.venv' / 'Scripts' / 'python.exe'

            
                if venv_python.exists():

            
                    python_exe = str(venv_python)

            
                    self.logger.info(f"使用 venv Python: {python_exe}")

            
            
            eval_args = [
                python_exe, 'evaluate.py',
                '--controller', 'none',
                '--ticks', str(test_config['test_ticks']),
                '--runs', '1',  # 單次運行
                '--output-dir', test_config['isolated_paths']['results_dir'],
                '--robot-count', str(robot_count)  # 我們需要在 evaluate.py 中添加這個參數
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
                # 測試成功
                result = {
                    'test_id': test_id,
                    'robot_count': robot_count,
                    'status': 'completed',
                    'execution_time': execution_time,
                    'end_time': datetime.now().isoformat(),
                    'stdout': stdout,
                    'stderr': stderr
                }
                
                # 嘗試讀取評估結果
                try:
                    results_file = Path(test_config['isolated_paths']['results_dir']) / 'evaluation_results.json'
                    if results_file.exists():
                        with open(results_file, 'r', encoding='utf-8') as f:
                            eval_results = json.load(f)
                        result['evaluation_results'] = eval_results
                except Exception as e:
                    self.logger.warning(f"無法讀取評估結果檔案: {e}")
                
                self.logger.info(f"測試 {test_id} 完成，執行時間: {execution_time:.1f} 秒")
                
            else:
                # 測試失敗
                result = {
                    'test_id': test_id,
                    'robot_count': robot_count,
                    'status': 'failed',
                    'execution_time': execution_time,
                    'end_time': datetime.now().isoformat(),
                    'error_code': process.returncode,
                    'stdout': stdout,
                    'stderr': stderr
                }
                
                self.logger.error(f"測試 {test_id} 失敗，錯誤碼: {process.returncode}")
                self.logger.error(f"錯誤輸出: {stderr}")
            
            return result
            
        except Exception as e:
            error_result = {
                'test_id': test_id,
                'robot_count': robot_count,
                'status': 'error',
                'end_time': datetime.now().isoformat(),
                'error': str(e)
            }
            
            self.logger.error(f"測試 {test_id} 執行時發生異常: {e}")
            return error_result
    
    def run_capacity_test(self, robot_counts: List[int] = None, 
                         parallel: bool = True, test_ticks: int = 100000,
                         max_parallel_tests: Optional[int] = None,
                         runs_per_config: int = 1) -> Dict[str, Any]:
        """
        執行容量測試
        
        Args:
            robot_counts: 要測試的機器人數量列表
            parallel: 是否並行執行測試
            test_ticks: 每個測試的 tick 數
            max_parallel_tests: 最大並行測試數量
            runs_per_config: 每個機器人數量配置要執行的次數
            
        Returns:
            測試結果摘要
        """
        if robot_counts is None:
            robot_counts = [20, 25, 30, 35, 40]
        
        # 設定最大並行數
        if max_parallel_tests is None:
            if parallel:
                # 預設為 CPU 核心數的一半，但不超過測試數量
                total_tests = len(robot_counts) * runs_per_config
                max_parallel_tests = min(total_tests, max(1, os.cpu_count() // 2))
            else:
                max_parallel_tests = 1
        
        self.logger.info(f"開始容量測試")
        self.logger.info(f"測試機器人數量: {robot_counts}")
        self.logger.info(f"每個配置運行次數: {runs_per_config}")
        self.logger.info(f"並行執行: {parallel}")
        self.logger.info(f"每個測試 tick 數: {test_ticks}")
        self.logger.info(f"最大並行測試數: {max_parallel_tests}")
        
        # 準備所有測試配置
        test_configs = []
        for robot_count in robot_counts:
            for run_idx in range(runs_per_config):
                # 為每個運行創建唯一的測試ID，包含運行索引
                test_id = f"robots_{robot_count}_run{run_idx}_{uuid.uuid4().hex[:8]}"
                test_config = self._prepare_test_environment(robot_count, test_id, test_ticks)
                # 添加運行索引信息
                test_config['run_index'] = run_idx
                test_configs.append(test_config)
        
        self.logger.info(f"總測試數量: {len(test_configs)}")
        
        # 執行測試
        all_results = []
        start_time = time.time()
        
        if parallel and max_parallel_tests > 1:
            # 並行執行
            # 如果啟用監控，使用執行緒池而非進程池（因為 monitor 無法被 pickle）
            if self.enable_monitor and self.test_monitor:
                executor_class = ThreadPoolExecutor
            else:
                executor_class = ProcessPoolExecutor
            
            with executor_class(max_workers=max_parallel_tests) as executor:
                # 提交所有測試
                future_to_config = {
                    executor.submit(
                        self._run_single_test_with_monitor if (self.test_monitor and isinstance(executor, ThreadPoolExecutor)) else self._run_single_test, 
                        config
                    ): config 
                    for config in test_configs
                }
                
                # 收集結果
                for future in as_completed(future_to_config):
                    config = future_to_config[future]
                    try:
                        result = future.result()
                        # 添加運行索引信息到結果
                        result['run_index'] = config['run_index']
                        all_results.append(result)
                        
                        if result['status'] == 'completed':
                            self.completed_tests[result['test_id']] = result
                        else:
                            self.failed_tests[result['test_id']] = result
                            
                    except Exception as e:
                        error_result = {
                            'test_id': config['test_id'],
                            'robot_count': config['robot_count'],
                            'run_index': config['run_index'],
                            'status': 'exception',
                            'error': str(e)
                        }
                        all_results.append(error_result)
                        self.failed_tests[config['test_id']] = error_result
                        self.logger.error(f"測試 {config['test_id']} 發生異常: {e}")
        else:
            # 串行執行
            for config in test_configs:
                result = self._run_single_test_with_monitor(config) if self.test_monitor else self._run_single_test(config)
                # 添加運行索引信息到結果
                result['run_index'] = config['run_index']
                all_results.append(result)
                
                if result['status'] == 'completed':
                    self.completed_tests[result['test_id']] = result
                else:
                    self.failed_tests[result['test_id']] = result
        
        total_time = time.time() - start_time
        
        # 生成測試摘要
        completed_count = len([r for r in all_results if r['status'] == 'completed'])
        failed_count = len(all_results) - completed_count
        
        # 按機器人數量分組結果
        results_by_robot_count = {}
        for result in all_results:
            robot_count = result['robot_count']
            if robot_count not in results_by_robot_count:
                results_by_robot_count[robot_count] = []
            results_by_robot_count[robot_count].append(result)
        
        summary = {
            'test_session_id': self.instance_id,
            'start_time': self.test_start_time.isoformat(),
            'end_time': datetime.now().isoformat(),
            'total_execution_time': total_time,
            'robot_counts_tested': robot_counts,
            'runs_per_config': runs_per_config,
            'total_tests': len(all_results),
            'completed_tests': completed_count,
            'failed_tests': failed_count,
            'test_ticks': test_ticks,
            'parallel_execution': parallel,
            'max_parallel_tests': max_parallel_tests,
            'platform': self.platform,
            'results': all_results,
            'results_by_robot_count': results_by_robot_count
        }
        
        # 保存測試摘要
        summary_file = self.base_output_dir / 'capacity_test_summary.json'
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"容量測試完成")
        self.logger.info(f"總執行時間: {total_time:.1f} 秒")
        self.logger.info(f"成功測試: {completed_count}/{len(all_results)}")
        self.logger.info(f"測試摘要已保存至: {summary_file}")
        
        return summary

    def run_capacity_test_background(self, robot_counts: List[int] = None, 
                                   parallel: bool = True, test_ticks: int = 100000,
                                   max_parallel_tests: Optional[int] = None,
                                   runs_per_config: int = 1) -> str:
        """
        在背景執行容量測試
        
        Args:
            與 run_capacity_test 相同
            
        Returns:
            測試會話ID
        """
        if self.background_thread and self.background_thread.is_alive():
            raise RuntimeError("已有測試在背景執行中")
        
        self.background_mode = True
        
        # 在背景執行緒中執行測試
        self.background_thread = threading.Thread(
            target=self._run_capacity_test_thread,
            args=(robot_counts, parallel, test_ticks, max_parallel_tests, runs_per_config),
            daemon=True
        )
        self.background_thread.start()
        
        return self.instance_id
        
    def _run_capacity_test_thread(self, robot_counts, parallel, test_ticks, 
                                max_parallel_tests, runs_per_config):
        """背景執行緒中執行測試"""
        try:
            self.run_capacity_test(
                robot_counts=robot_counts,
                parallel=parallel,
                test_ticks=test_ticks,
                max_parallel_tests=max_parallel_tests,
                runs_per_config=runs_per_config
            )
        except Exception as e:
            self.logger.error(f"背景測試執行失敗: {e}")
            import traceback
            traceback.print_exc()
    
    def _run_single_test_with_monitor(self, test_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        執行單個容量測試（支援監控）
        
        Args:
            test_config: 測試配置
            
        Returns:
            測試結果
        """
        test_id = test_config['test_id']
        robot_count = test_config['robot_count']
        
        try:
            self.logger.info(f"開始執行測試 {test_id} (機器人數量: {robot_count})")
            
            # 設定環境變數
            env = os.environ.copy()
            env.update(self.isolation_manager.get_isolated_env_vars(test_id))
            # 標記為容量測試模式，讓 evaluate.py 輸出進度到 stdout
            env['CAPACITY_TEST_MODE'] = '1'
            
            # 準備評估參數

            
            # 確保使用 venv 的 Python（如果存在）

            
            python_exe = sys.executable

            
            if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):

            
                # 在虛擬環境中，確保使用正確的 Python

            
                python_exe = sys.executable

            
            else:

            
                # 不在虛擬環境中，嘗試找 venv

            
                venv_python = Path(project_root) / '.venv' / 'Scripts' / 'python.exe'

            
                if venv_python.exists():

            
                    python_exe = str(venv_python)

            
                    self.logger.info(f"使用 venv Python: {python_exe}")

            
            
            eval_args = [
                python_exe, 'evaluate.py',
                '--controller', 'none',
                '--ticks', str(test_config['test_ticks']),
                '--runs', '1',  # 單次運行
                '--output-dir', test_config['isolated_paths']['results_dir'],
                '--robot-count', str(robot_count)  # 我們需要在 evaluate.py 中添加這個參數
            ]
            
            # 執行評估
            start_time = time.time()
            
            # 如果啟用監控器，使用 Popen 並添加到監控
            if self.test_monitor:
                # 獲取日誌文件路徑
                log_file = Path(test_config['isolated_paths']['logs_dir']) / f"{test_id}_evaluation.log"
                
                process = subprocess.Popen(
                    eval_args,
                    env=env,
                    cwd=str(project_root),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=1  # 行緩衝
                )
                
                # 添加到監控器
                self.test_monitor.add_test_process(
                    test_id=test_id,
                    robot_count=robot_count,
                    run_index=test_config.get('run_index', 0),
                    process=process,
                    workspace_dir=Path(test_config['isolated_paths']['workspace_root']),
                    log_file=log_file
                )
                
                # 等待進程結束
                stdout, stderr = process.communicate()
                execution_time = time.time() - start_time
                
                if process.returncode == 0:
                    result = self._create_success_result(test_id, robot_count, execution_time, 
                                                       stdout, stderr, test_config)
                else:
                    result = self._create_failure_result(test_id, robot_count, execution_time,
                                                       process.returncode, stdout, stderr)
            else:
                # 使用原始方法（不監控）
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
                    result = self._create_success_result(test_id, robot_count, execution_time,
                                                       stdout, stderr, test_config)
                else:
                    result = self._create_failure_result(test_id, robot_count, execution_time,
                                                       process.returncode, stdout, stderr)
            
            return result
            
        except Exception as e:
            return self._create_error_result(test_id, robot_count, str(e))
    
    def _create_success_result(self, test_id, robot_count, execution_time, 
                             stdout, stderr, test_config):
        """創建成功結果"""
        result = {
            'test_id': test_id,
            'robot_count': robot_count,
            'status': 'completed',
            'execution_time': execution_time,
            'end_time': datetime.now().isoformat(),
            'stdout': stdout,
            'stderr': stderr
        }
        
        # 嘗試讀取評估結果
        try:
            results_file = Path(test_config['isolated_paths']['results_dir']) / 'evaluation_results.json'
            if results_file.exists():
                with open(results_file, 'r', encoding='utf-8') as f:
                    eval_results = json.load(f)
                result['evaluation_results'] = eval_results
        except Exception as e:
            self.logger.warning(f"無法讀取評估結果檔案: {e}")
        
        self.logger.info(f"測試 {test_id} 完成，執行時間: {execution_time:.1f} 秒")
        return result
    
    def _create_failure_result(self, test_id, robot_count, execution_time,
                             error_code, stdout, stderr):
        """創建失敗結果"""
        result = {
            'test_id': test_id,
            'robot_count': robot_count,
            'status': 'failed',
            'execution_time': execution_time,
            'end_time': datetime.now().isoformat(),
            'error_code': error_code,
            'stdout': stdout,
            'stderr': stderr
        }
        
        self.logger.error(f"測試 {test_id} 失敗，錯誤碼: {error_code}")
        self.logger.error(f"錯誤輸出: {stderr}")
        return result
    
    def _create_error_result(self, test_id, robot_count, error):
        """創建錯誤結果"""
        error_result = {
            'test_id': test_id,
            'robot_count': robot_count,
            'status': 'error',
            'end_time': datetime.now().isoformat(),
            'error': error
        }
        
        self.logger.error(f"測試 {test_id} 執行時發生異常: {error}")
        return error_result
    
    def get_test_progress(self) -> Dict[str, Any]:
        """
        獲取測試進度
        
        Returns:
            測試進度資訊
        """
        return {
            'running_tests': len(self.running_tests),
            'completed_tests': len(self.completed_tests),
            'failed_tests': len(self.failed_tests),
            'running_test_details': list(self.running_tests.keys()),
            'completed_test_details': list(self.completed_tests.keys()),
            'failed_test_details': list(self.failed_tests.keys())
        }
    
    def stop_all_tests(self):
        """停止所有正在運行的測試"""
        self.logger.info("正在停止所有測試...")
        
        for test_id, process_info in self.running_tests.items():
            try:
                if 'process' in process_info and process_info['process'].poll() is None:
                    process_info['process'].terminate()
                    self.logger.info(f"已終止測試 {test_id}")
            except Exception as e:
                self.logger.error(f"終止測試 {test_id} 時發生錯誤: {e}")
        
        self.running_tests.clear()
    
    def cleanup_test_files(self, keep_results: bool = True):
        """
        清理測試產生的臨時檔案
        
        Args:
            keep_results: 是否保留結果檔案
        """
        self.logger.info("開始清理測試檔案...")
        
        cleaned_count = self.isolation_manager.cleanup_all_workspaces(keep_results)
        
        self.logger.info(f"已清理 {cleaned_count} 個工作空間")
    
    def generate_capacity_analysis(self) -> str:
        """
        生成容量分析報告
        
        Returns:
            報告檔案路徑
        """
        try:
            from test.capacity_analyzer import CapacityAnalyzer
            
            analyzer = CapacityAnalyzer(self.base_output_dir)
            report_path = analyzer.generate_analysis_report()
            
            self.logger.info(f"容量分析報告已生成: {report_path}")
            return report_path
            
        except ImportError:
            self.logger.error("找不到 CapacityAnalyzer，請確保已實作 capacity_analyzer.py")
            return ""
        except Exception as e:
            self.logger.error(f"生成容量分析報告時發生錯誤: {e}")
            return ""


def main():
    """主函數，用於命令列執行"""
    import argparse
    
    parser = argparse.ArgumentParser(description='RMFS 系統容量壓力測試控制器')
    parser.add_argument('--robot-counts', nargs='+', type=int, default=[20, 25, 30, 35, 40],
                       help='要測試的機器人數量列表')
    parser.add_argument('--ticks', type=int, default=100000,
                       help='每個測試的 tick 數')
    parser.add_argument('--parallel', action='store_true', default=True,
                       help='是否並行執行測試')
    parser.add_argument('--max-parallel', type=int, default=None,
                       help='最大並行測試數量')
    parser.add_argument('--output-dir', type=str, default=None,
                       help='輸出目錄路徑')
    
    args = parser.parse_args()
    
    # 創建測試控制器
    controller = CapacityTestController(args.output_dir)
    
    try:
        # 執行容量測試
        summary = controller.run_capacity_test(
            robot_counts=args.robot_counts,
            parallel=args.parallel,
            test_ticks=args.ticks,
            max_parallel_tests=args.max_parallel
        )
        
        # 生成分析報告
        report_path = controller.generate_capacity_analysis()
        
        print(f"\n=== 容量測試完成 ===")
        print(f"成功測試: {summary['completed_tests']}/{summary['total_tests']}")
        print(f"總執行時間: {summary['total_execution_time']:.1f} 秒")
        print(f"結果目錄: {controller.base_output_dir}")
        if report_path:
            print(f"分析報告: {report_path}")
        
    except KeyboardInterrupt:
        print("\n測試被用戶中斷")
        controller.stop_all_tests()
    except Exception as e:
        print(f"測試執行時發生錯誤: {e}")
        controller.logger.error(f"測試執行時發生錯誤: {e}")
    

if __name__ == '__main__':
    main()
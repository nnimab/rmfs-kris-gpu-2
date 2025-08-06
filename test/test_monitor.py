#!/usr/bin/env python3
"""
測試進度監控器
用於實時監控和顯示容量測試的進度
"""
import sys
import time
import threading
import subprocess
import queue
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

# 加入專案根目錄到 Python 路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from lib.logger import get_logger


class TestStatus(Enum):
    """測試狀態枚舉"""
    PENDING = "待執行"
    RUNNING = "執行中"
    COMPLETED = "已完成"
    FAILED = "失敗"
    CANCELLED = "已取消"


@dataclass
class TestProcess:
    """測試進程資訊"""
    test_id: str
    robot_count: int
    run_index: int
    process: subprocess.Popen
    start_time: datetime
    status: TestStatus
    output_queue: queue.Queue
    error_queue: queue.Queue
    workspace_dir: Path
    log_file: Path


class TestMonitor:
    """測試監控器"""
    
    def __init__(self, base_output_dir: Path):
        """
        初始化測試監控器
        
        Args:
            base_output_dir: 基礎輸出目錄
        """
        self.base_output_dir = base_output_dir
        self.logger = get_logger()
        
        # 測試進程管理
        self.test_processes: Dict[str, TestProcess] = {}
        self.process_lock = threading.Lock()
        
        # 監控執行緒
        self.monitor_threads: Dict[str, threading.Thread] = {}
        self.running = True
        
        # 進度資訊
        self.progress_data: Dict[str, Dict[str, Any]] = {}
        self.progress_lock = threading.Lock()
        
    def add_test_process(self, test_id: str, robot_count: int, run_index: int,
                         process: subprocess.Popen, workspace_dir: Path, log_file: Path):
        """
        添加測試進程到監控
        
        Args:
            test_id: 測試ID
            robot_count: 機器人數量
            run_index: 運行索引
            process: 子進程對象
            workspace_dir: 工作空間目錄
            log_file: 日誌文件路徑
        """
        output_queue = queue.Queue()
        error_queue = queue.Queue()
        
        test_process = TestProcess(
            test_id=test_id,
            robot_count=robot_count,
            run_index=run_index,
            process=process,
            start_time=datetime.now(),
            status=TestStatus.RUNNING,
            output_queue=output_queue,
            error_queue=error_queue,
            workspace_dir=workspace_dir,
            log_file=log_file
        )
        
        with self.process_lock:
            self.test_processes[test_id] = test_process
        
        # 啟動輸出監控執行緒
        monitor_thread = threading.Thread(
            target=self._monitor_process_output,
            args=(test_id,),
            daemon=True
        )
        monitor_thread.start()
        self.monitor_threads[test_id] = monitor_thread
        
    def _monitor_process_output(self, test_id: str):
        """
        監控進程輸出
        
        Args:
            test_id: 測試ID
        """
        with self.process_lock:
            test_process = self.test_processes.get(test_id)
            
        if not test_process:
            return
            
        process = test_process.process
        
        # 創建輸出讀取執行緒
        def read_stdout():
            for line in iter(process.stdout.readline, ''):
                if not self.running:
                    break
                if line:
                    test_process.output_queue.put(line.strip())
                    self._update_progress_from_output(test_id, line.strip())
                    
        def read_stderr():
            for line in iter(process.stderr.readline, ''):
                if not self.running:
                    break
                if line:
                    test_process.error_queue.put(line.strip())
        
        stdout_thread = threading.Thread(target=read_stdout, daemon=True)
        stderr_thread = threading.Thread(target=read_stderr, daemon=True)
        
        stdout_thread.start()
        stderr_thread.start()
        
        # 等待進程結束
        process.wait()
        
        # 更新狀態
        with self.process_lock:
            if process.returncode == 0:
                test_process.status = TestStatus.COMPLETED
            else:
                test_process.status = TestStatus.FAILED
                
        # 等待輸出執行緒結束
        stdout_thread.join(timeout=5)
        stderr_thread.join(timeout=5)
        
    def _update_progress_from_output(self, test_id: str, line: str):
        """
        從輸出行更新進度資訊
        
        Args:
            test_id: 測試ID
            line: 輸出行
        """
        with self.progress_lock:
            if test_id not in self.progress_data:
                self.progress_data[test_id] = {
                    'current_tick': 0,
                    'total_ticks': 0,
                    'completed_orders': 0,
                    'total_orders': 0,
                    'last_update': datetime.now()
                }
            
            progress = self.progress_data[test_id]
            
            # 解析進度資訊
            if "進度:" in line:
                # 格式: "進度: 1000/10000 ticks, 完成訂單: 10/50"
                try:
                    parts = line.split(",")
                    if len(parts) >= 2:
                        # 解析 tick 進度
                        tick_part = parts[0].split(":")[-1].strip()
                        if "/" in tick_part:
                            current, total = tick_part.replace("ticks", "").strip().split("/")
                            progress['current_tick'] = int(current)
                            progress['total_ticks'] = int(total)
                        
                        # 解析訂單進度
                        order_part = parts[1].split(":")[-1].strip()
                        if "/" in order_part:
                            completed, total = order_part.split("/")
                            progress['completed_orders'] = int(completed)
                            progress['total_orders'] = int(total)
                            
                    progress['last_update'] = datetime.now()
                except Exception:
                    pass
                    
    def get_test_output(self, test_id: str, max_lines: int = 50) -> Tuple[List[str], List[str]]:
        """
        獲取測試輸出
        
        Args:
            test_id: 測試ID
            max_lines: 最大行數
            
        Returns:
            (標準輸出行列表, 錯誤輸出行列表)
        """
        with self.process_lock:
            test_process = self.test_processes.get(test_id)
            
        if not test_process:
            return [], []
            
        stdout_lines = []
        stderr_lines = []
        
        # 獲取標準輸出
        while not test_process.output_queue.empty() and len(stdout_lines) < max_lines:
            try:
                line = test_process.output_queue.get_nowait()
                stdout_lines.append(line)
            except queue.Empty:
                break
                
        # 獲取錯誤輸出
        while not test_process.error_queue.empty() and len(stderr_lines) < max_lines:
            try:
                line = test_process.error_queue.get_nowait()
                stderr_lines.append(line)
            except queue.Empty:
                break
                
        return stdout_lines, stderr_lines
        
    def get_all_test_status(self) -> List[Dict[str, Any]]:
        """
        獲取所有測試的狀態
        
        Returns:
            測試狀態列表
        """
        status_list = []
        
        with self.process_lock:
            for test_id, test_process in self.test_processes.items():
                progress = self.progress_data.get(test_id, {})
                
                status = {
                    'test_id': test_id,
                    'robot_count': test_process.robot_count,
                    'run_index': test_process.run_index,
                    'status': test_process.status.value,
                    'start_time': test_process.start_time.isoformat(),
                    'elapsed_time': (datetime.now() - test_process.start_time).total_seconds(),
                    'progress': {
                        'current_tick': progress.get('current_tick', 0),
                        'total_ticks': progress.get('total_ticks', 0),
                        'completed_orders': progress.get('completed_orders', 0),
                        'total_orders': progress.get('total_orders', 0),
                        'percentage': self._calculate_progress_percentage(progress)
                    }
                }
                
                status_list.append(status)
                
        return sorted(status_list, key=lambda x: (x['robot_count'], x['run_index']))
        
    def _calculate_progress_percentage(self, progress: Dict[str, Any]) -> float:
        """
        計算進度百分比
        
        Args:
            progress: 進度資料
            
        Returns:
            進度百分比 (0-100)
        """
        if progress.get('total_ticks', 0) > 0:
            return (progress.get('current_tick', 0) / progress['total_ticks']) * 100
        return 0.0
        
    def cancel_test(self, test_id: str) -> bool:
        """
        取消測試
        
        Args:
            test_id: 測試ID
            
        Returns:
            是否成功取消
        """
        with self.process_lock:
            test_process = self.test_processes.get(test_id)
            
        if not test_process or test_process.status != TestStatus.RUNNING:
            return False
            
        try:
            test_process.process.terminate()
            test_process.status = TestStatus.CANCELLED
            return True
        except Exception as e:
            self.logger.error(f"取消測試 {test_id} 失敗: {e}")
            return False
            
    def cancel_all_tests(self):
        """取消所有執行中的測試"""
        with self.process_lock:
            test_ids = list(self.test_processes.keys())
            
        for test_id in test_ids:
            self.cancel_test(test_id)
            
    def cleanup(self):
        """清理資源"""
        self.running = False
        self.cancel_all_tests()
        
        # 等待所有監控執行緒結束
        for thread in self.monitor_threads.values():
            thread.join(timeout=5)
            
    def save_monitor_state(self):
        """保存監控狀態到文件"""
        state_file = self.base_output_dir / "monitor_state.json"
        
        state = {
            'timestamp': datetime.now().isoformat(),
            'tests': self.get_all_test_status()
        }
        
        with open(state_file, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
"""
工作流程執行器
==============

實現訓練、評估、分析的具體執行邏輯，支援並行處理
"""

import os
import sys
import time
import subprocess
import glob
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Tuple, Optional, Any

class Colors:
    """控制台顏色"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    MAGENTA = '\033[95m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    WARNING = '\033[93m'  # 新增 WARNING 屬性
    END = '\033[0m'

class WorkflowRunner:
    """實驗工作流程執行器"""
    
    def __init__(self, project_root: str = None):
        """
        初始化工作流程執行器
        
        Args:
            project_root: 專案根目錄路徑
        """
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.models_dir = self.project_root / "models"
        self.results_dir = self.project_root / "result"
        
        # 確保目錄存在
        self.models_dir.mkdir(exist_ok=True)
        self.results_dir.mkdir(exist_ok=True)
        
        # 執行統計
        self.execution_stats = {
            "start_time": None,
            "end_time": None,
            "total_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "results": {}
        }
        
        # 並行配置
        self.parallel_config = {}
        
        # 訓練腳本路徑和 Python 可執行檔
        self.train_script_path = self.project_root / "train.py"
        self.python_executable = sys.executable
        # 調試：顯示 Python 執行檔路徑
        print(f"DEBUG: Python executable path: '{self.python_executable}'")
        self.log_level = "INFO"  # 預設日誌級別
    
    def print_header(self, text: str, color: str = Colors.BLUE):
        """打印標題"""
        print(f"\n{color}{Colors.BOLD}{'='*60}")
        print(f"  {text}")
        print(f"{'='*60}{Colors.END}")
    
    def print_success(self, text: str):
        """打印成功訊息"""
        print(f"{Colors.GREEN}[SUCCESS] {text}{Colors.END}")
    
    def print_error(self, text: str):
        """打印錯誤訊息"""
        print(f"{Colors.RED}[ERROR] {text}{Colors.END}")
    
    def print_warning(self, text: str):
        """打印警告訊息"""
        print(f"{Colors.YELLOW}[WARNING] {text}{Colors.END}")
    
    def print_info(self, text: str):
        """打印信息"""
        print(f"{Colors.CYAN}[INFO] {text}{Colors.END}")
    
    def print_progress(self, current: int, total: int, description: str):
        """打印進度條"""
        if total == 0:
            return
        
        percentage = (current / total) * 100
        bar_length = 30
        filled_length = int(bar_length * current // total)
        bar = '█' * filled_length + '-' * (bar_length - filled_length)
        
        print(f"\r{Colors.BLUE}[{bar}] {percentage:.1f}% - {description}{Colors.END}", end='', flush=True)
        if current == total:
            print()  # 換行
    
    def run_command(self, cmd: str, description: str, timeout: int = 600, 
                   open_new_window: bool = False, window_title: str = None) -> Tuple[bool, str]:
        """
        執行命令
        
        Args:
            cmd: 要執行的命令
            description: 描述
            timeout: 超時時間（秒）
            open_new_window: 是否在新視窗中執行
            window_title: 新視窗標題
            
        Returns:
            tuple: (是否成功, 輸出/錯誤訊息)
        """
        self.print_info(f"執行: {description}")
        print(f"命令: {cmd}")
        
        if open_new_window:
            # 在新的終端視窗中執行命令
            if not window_title:
                window_title = description
            
            # Windows CMD 新視窗命令
            # 使用 /K 保持視窗開啟，顯示結果
            # 創建一個臨時檔案來標記完成狀態
            import tempfile
            temp_dir = tempfile.gettempdir()
            done_flag = os.path.join(temp_dir, f"rmfs_done_{window_title.replace(' ', '_')}.flag")
            
            # 刪除舊的標記檔案（如果存在）
            if os.path.exists(done_flag):
                os.remove(done_flag)
            
            # 修改命令，無論成功或失敗都創建標記檔案（包含結果）
            window_cmd = f'''start "{window_title}" cmd /K "cd /d {self.project_root} && ({cmd} && echo SUCCESS > "{done_flag}" || echo FAILED > "{done_flag}") && echo. && echo 執行完成，按任意鍵關閉視窗... && pause"'''
            
            try:
                # 啟動新視窗
                process = subprocess.Popen(window_cmd, shell=True, cwd=str(self.project_root))
                self.print_success(f"已在新視窗啟動: {window_title}")
                
                # 等待訓練完成（檢查標記檔案）
                self.print_info(f"等待 {window_title} 完成...")
                start_time = time.time()
                check_interval = 5  # 每5秒檢查一次
                
                while True:
                    if os.path.exists(done_flag):
                        # 訓練完成，讀取結果
                        with open(done_flag, 'r') as f:
                            result = f.read().strip()
                        os.remove(done_flag)  # 清理標記檔案
                        elapsed = time.time() - start_time
                        print()  # 換行，清除進度顯示
                        
                        if result == "SUCCESS":
                            self.print_success(f"{window_title} 已成功完成 (耗時: {elapsed:.1f}秒)")
                            return True, f"Process completed successfully in window: {window_title}"
                        else:
                            self.print_error(f"{window_title} 執行失敗 (耗時: {elapsed:.1f}秒)")
                            return False, f"Process failed in window: {window_title}"
                    
                    # 檢查是否超時
                    if time.time() - start_time > timeout:
                        self.print_error(f"{window_title} 執行超時")
                        return False, "Timeout"
                    
                    # 顯示等待進度
                    elapsed = int(time.time() - start_time)
                    print(f"\r等待中... {elapsed}秒 / {timeout}秒", end='', flush=True)
                    time.sleep(check_interval)
                    
                return True, f"Process started in new window: {window_title}"
            except Exception as e:
                self.print_error(f"無法開啟新視窗: {str(e)}")
                return False, str(e)
        else:
            # 原本的執行方式（捕獲輸出）
            try:
                start_time = time.time()
                result = subprocess.run(
                    cmd, shell=True, capture_output=True, 
                    text=True, timeout=timeout, cwd=str(self.project_root)
                )
                elapsed_time = time.time() - start_time
                
                if result.returncode == 0:
                    self.print_success(f"完成 (耗時: {elapsed_time:.1f}秒)")
                    return True, result.stdout
                else:
                    self.print_error(f"失敗 (返回碼: {result.returncode})")
                    if result.stderr:
                        print(f"錯誤: {result.stderr}")
                    return False, result.stderr
                    
            except subprocess.TimeoutExpired:
                self.print_error(f"超時 (超過 {timeout} 秒)")
                return False, "Timeout"
            except Exception as e:
                self.print_error(f"異常: {str(e)}")
                return False, str(e)
    
    def run_training_workflow(self, training_config: Dict, parallel_config: Dict) -> Dict[str, bool]:
        """
        執行帶有雙層並行控制的訓練工作流程。
        外層並行：控制同時執行多少個獨立的訓練任務
        內層並行：控制每個NERL任務內部使用多少個評估進程
        """
        self.print_header("開始AI模型訓練工作流程（雙層並行調度器）", Colors.MAGENTA)
        self.log_level = parallel_config.get('log_level', 'INFO')

        # 1. 準備所有任務列表
        all_tasks = list(training_config.items())
        
        # 2. 獲取外層並行數量
        max_concurrent_tasks = parallel_config.get('max_workers', 2)
        if not parallel_config.get('enabled', True):
            max_concurrent_tasks = 1  # 如果未啟用並行，則強制為1

        self.print_info(f"調度器設定：將以最多 {max_concurrent_tasks} 個任務並行的方式執行。")
        self.print_info(f"總任務數: {len(all_tasks)} 個 ({len([n for n, _ in all_tasks if 'nerl' in n])} NERL + {len([n for n, _ in all_tasks if 'dqn' in n])} DQN)")
        
        # 3. 真正的分批執行任務以控制並行數量
        results = {}
        
        # 分批處理
        for i in range(0, len(all_tasks), max_concurrent_tasks):
            current_batch = all_tasks[i:i+max_concurrent_tasks]
            
            self.print_info(f"啟動第 {i//max_concurrent_tasks + 1} 批任務（{len(current_batch)} 個）...")
            
            # 啟動當前批次的所有任務
            batch_processes = []
            for name, params in current_batch:
                try:
                    process = self._build_and_run_command(name, params, parallel_config, return_process=True)
                    if process:
                        batch_processes.append((name, process))
                        results[name] = True
                        self.print_success(f"✅ 已啟動任務: {name}")
                    else:
                        results[name] = False
                        self.print_error(f"❌ 任務啟動失敗: {name}")
                except Exception as exc:
                    self.print_error(f"任務 '{name}' 在執行調度中產生例外: {exc}")
                    results[name] = False
            
            # 如果還有剩餘任務，等待當前批次完全完成
            if i + max_concurrent_tasks < len(all_tasks):
                remaining_tasks = len(all_tasks) - i - max_concurrent_tasks
                
                self.print_info(f"已啟動 {len(current_batch)} 個任務，等待它們完成訓練...")
                self.print_info(f"剩餘 {remaining_tasks} 個任務將在當前批次完成後啟動")
                
                # 等待當前批次的所有進程完成
                self._wait_for_batch_completion(batch_processes)
                
                self.print_info("當前批次訓練已完成，準備啟動下一批...")
                    
        successful_count = sum(1 for v in results.values() if v)
        self.print_header(f"所有訓練任務已執行完畢 ({successful_count}/{len(all_tasks)} 成功啟動)", Colors.GREEN)
        
        if successful_count > 0:
            self.print_info("✨ 成功啟動的訓練視窗將持續運行，您可以在各個視窗中監控訓練進度")
        
        return results
    
    def _run_task_group(self, task_dict: Dict[str, Dict], use_new_windows: bool = True, task_type: str = "") -> Dict[str, bool]:
        """
        執行一組訓練任務
        
        Args:
            task_dict: 任務字典 {task_name: task_params}
            use_new_windows: 是否使用新視窗
            task_type: 任務類型描述
            
        Returns:
            dict: 執行結果 {task_name: success}
        """
        results = {}
        task_list = list(task_dict.items())
        
        self.print_info(f"開始執行 {len(task_list)} 個 {task_type.upper()} 任務...")
        
        for task_name, task_params in task_list:
            try:
                self.print_info(f"開始執行任務: {task_name}")
                
                # 設置視窗模式
                task_params_copy = task_params.copy()
                task_params_copy['use_new_windows'] = use_new_windows
                task_params_copy['log_level'] = self.log_level
                
                success = self._build_and_run_command(task_name, task_params_copy)
                results[task_name] = success
                
                if success:
                    self.print_success(f"任務 {task_name} 完成")
                else:
                    self.print_error(f"任務 {task_name} 失敗")
                    
            except Exception as e:
                self.print_error(f"任務 {task_name} 執行異常: {e}")
                results[task_name] = False
        
        return results
    
    def _wait_for_batch_completion(self, batch_processes):
        """等待當前批次的所有任務完成"""
        if not batch_processes:
            return
        
        import time
        import os
        import tempfile
        
        self.print_info(f"正在監控 {len(batch_processes)} 個訓練任務的完成狀態...")
        
        # 使用任務名稱而不是進程對象
        task_names = [task_name for task_name, _ in batch_processes]
        completed_tasks = set()
        
        # 創建完成標記文件的目錄
        temp_dir = tempfile.gettempdir()
        completion_dir = os.path.join(temp_dir, "rmfs_completion_flags")
        os.makedirs(completion_dir, exist_ok=True)
        
        # 清理舊的完成標記文件
        for task_name in task_names:
            completion_file = os.path.join(completion_dir, f"{task_name}.completed")
            if os.path.exists(completion_file):
                os.remove(completion_file)
        
        # 每 10 秒檢查一次
        while len(completed_tasks) < len(task_names):
            # 檢查完成標記文件
            for task_name in task_names:
                if task_name not in completed_tasks:
                    completion_file = os.path.join(completion_dir, f"{task_name}.completed")
                    if os.path.exists(completion_file):
                        completed_tasks.add(task_name)
                        self.print_success(f"✅ 任務 '{task_name}' 訓練完成")
                        # 清理完成標記文件
                        try:
                            os.remove(completion_file)
                        except:
                            pass
            
            # 顯示進度
            completed_count = len(completed_tasks)
            total_count = len(task_names)
            if completed_count < total_count:
                remaining = total_count - completed_count
                running_tasks = [name for name in task_names if name not in completed_tasks]
                print(f"\r等待中... {completed_count}/{total_count} 個任務已完成，還有 {remaining} 個正在訓練: {running_tasks}", end='', flush=True)
                time.sleep(10)  # 每 10 秒檢查一次
        
        print()  # 換行
        self.print_success(f"當前批次的 {len(task_names)} 個任務全部完成！")
    
    def _build_and_run_command(self, task_name: str, params: Dict, parallel_config: Dict, return_process=False):
        """根據任務名稱和參數，構建並在新視窗中執行訓練命令。"""
        
        # 1. 解析 agent 和 reward_mode
        parts = task_name.split('_')
        agent = parts[0]
        reward_mode = parts[1]
        
        # 處理變體後綴（如 nerl_step_a -> agent=nerl, reward_mode=step, variant=a）
        variant = None
        if len(parts) > 2:
            variant = parts[2]

        # 2. 構建基礎指令
        cmd_list = [
            self.python_executable, 
            str(self.train_script_path),
            '--agent', agent,
            '--reward_mode', reward_mode,
            '--log_level', self.log_level
        ]
        
        # 如果有變體，添加變體參數
        if variant:
            cmd_list.extend(['--variant', variant])

        # 3. 從 params 字典動態添加所有參數
        # 定義 train.py 支援的參數列表（基於 train.py 的 argparse 定義）
        valid_params = {
            'generations', 'population', 'eval_ticks', 'training_ticks', 
            'parallel_workers', 'netlogo', 'ticks'
        }
        
        for key, value in params.items():
            # 只處理 train.py 支援的參數，忽略其他元數據
            if key in valid_params:
                # 跳過 parallel_workers 參數，我們將根據雙層並行邏輯處理
                if key == 'parallel_workers':
                    continue
                # 特殊處理 netlogo 參數
                elif key == 'netlogo' and value:
                    cmd_list.append('--netlogo')
                # 特殊處理 DQN 的 ticks 參數，轉換為 training_ticks
                elif key == 'ticks' and agent == 'dqn':
                    cmd_list.append('--training_ticks')
                    cmd_list.append(str(value))
                elif key != 'netlogo':  # 其他非 boolean 參數
                    cmd_list.append(f"--{key}")
                    cmd_list.append(str(value))

        # --- 【核心修改點：正確設定 NERL 的內層並行參數】 ---
        if agent == 'nerl':
            # 調試信息：檢查 parallel_config 內容
            self.print_info(f"[DEBUG] parallel_config 內容: {parallel_config}")
            # 從全域並行配置中獲取 NERL 應使用的內部核心數
            internal_workers = parallel_config.get('nerl_internal_workers', 4)
            cmd_list.extend(['--parallel_workers', str(internal_workers)])
            self.print_info(f"NERL任務 '{task_name}' 將使用 {internal_workers} 個內部並行進程")
        # --- 【修改結束】 ---

        # 4. 在新視窗中執行
        try:
            # 確保所有命令參數都是字串
            cmd_list_str = [str(item) for item in cmd_list]
            self.print_info(f"為任務 '{task_name}' 準備指令: {' '.join(cmd_list_str)}")

            # 根據作業系統使用不同的指令來開啟新視窗
            if os.name == 'nt': # Windows
                # /c 會執行完命令後關閉視窗，/k 會保留視窗
                # 使用 /k 保留視窗，這樣可以看到錯誤信息和訓練結果
                process = subprocess.Popen(['start', f'Training - {task_name}', 'cmd', '/k'] + cmd_list_str, shell=True, cwd=self.project_root)
            else: # macOS & Linux
                # 這裡需要根據您的非 Windows 環境進行調整，例如使用 'gnome-terminal' 或 'xterm'
                process = subprocess.Popen(['gnome-terminal', '--', 'bash', '-c', f"{' '.join(cmd_list_str)}; exec bash"], cwd=self.project_root)
            
            # Popen 是非阻塞的，指令發出後立即返回
            self.print_success(f"已在新視窗中成功啟動任務: {task_name}")
            
            if return_process:
                return process
            else:
                return True

        except Exception as e:
            self.print_error(f"啟動任務 '{task_name}' 時發生錯誤: {e}")
            import traceback
            traceback.print_exc()
            if return_process:
                return None
            else:
                return False
    
    def _run_training_batch_execution(self, training_tasks: List[Tuple]) -> Dict[str, bool]:
        """
        分批執行訓練任務：先執行 NERL 任務，再執行 DQN 任務
        
        Args:
            training_tasks: 訓練任務列表
            
        Returns:
            dict: 執行結果
        """
        results = {}
        
        # 分組任務
        nerl_tasks = [task for task in training_tasks if task[0] == 'nerl']
        dqn_tasks = [task for task in training_tasks if task[0] == 'dqn']
        
        # 第一批：執行 NERL 任務
        if nerl_tasks:
            self.print_header(f"第一批：執行 {len(nerl_tasks)} 個 NERL 訓練任務", Colors.BLUE)
            nerl_results = self._run_task_group(nerl_tasks, "NERL")
            results.update(nerl_results)
        
        # 第二批：執行 DQN 任務
        if dqn_tasks:
            self.print_header(f"第二批：執行 {len(dqn_tasks)} 個 DQN 訓練任務", Colors.BLUE)
            dqn_results = self._run_task_group(dqn_tasks, "DQN")
            results.update(dqn_results)
        
        return results
    
    
    def run_evaluation_workflow(self, config: Dict, parallel: bool = True) -> Dict[str, bool]:
        """
        執行評估工作流程
        
        Args:
            config: 評估配置
            parallel: 是否並行執行
            
        Returns:
            dict: 執行結果
        """
        self.print_header("開始效能評估", Colors.CYAN)
        
        # 準備評估任務
        evaluation_tasks = self._prepare_evaluation_tasks(config)
        
        if not evaluation_tasks:
            self.print_warning("沒有可執行的評估任務")
            return {}
        
        results = {}
        self.execution_stats["total_tasks"] += len(evaluation_tasks)
        
        if parallel and len(evaluation_tasks) > 1:
            self.print_info(f"並行執行 {len(evaluation_tasks)} 個評估實驗...")
            results = self._run_evaluation_parallel(evaluation_tasks)
        else:
            self.print_info("順序執行所有評估實驗...")
            results = self._run_evaluation_sequential(evaluation_tasks)
        
        # 統計結果
        successful = sum(1 for success in results.values() if success)
        self.execution_stats["completed_tasks"] += successful
        self.execution_stats["failed_tasks"] += len(results) - successful
        self.execution_stats["results"]["evaluation"] = results
        
        color = Colors.GREEN if successful == len(results) else Colors.YELLOW
        self.print_header(f"評估完成: {successful}/{len(results)} 個實驗成功", color)
        
        return results
    
    def _prepare_evaluation_tasks(self, config: Dict) -> List[Dict]:
        """準備評估任務列表"""
        tasks = []
        
        # 檢查可用控制器
        controllers = config.get('controllers', 'auto')
        if controllers == 'auto':
            controllers = self._detect_available_controllers()
        
        if len(controllers) < 2:
            self.print_warning("控制器數量不足，需要至少2個控制器進行對比")
            return []
        
        self.print_info(f"將評估的控制器: {', '.join(controllers)}")
        
        # 準備不同類型的評估實驗
        base_config = {
            "ticks": config.get('ticks', 15000),
            "description": config.get('description', 'experiment'),
            "output_dir": config.get('output_dir', None)
        }
        
        seeds = config.get('seeds', [42, 123, 789])
        
        # 為每個隨機種子創建任務
        for i, seed in enumerate(seeds):
            task = base_config.copy()
            task['controllers'] = controllers
            task['seed'] = seed
            task['description'] = f"{base_config['description']}_seed{seed}"
            task['run_name'] = f"實驗運行 {i+1}/{len(seeds)} (seed={seed})"
            # 傳遞 use_new_windows 設置
            task['use_new_windows'] = config.get('use_new_windows', True)
            # 傳遞 use_netlogo 設置
            task['use_netlogo'] = config.get('use_netlogo', False)
            # 傳遞日誌級別設置
            task['log_level'] = config.get('log_level', 'INFO')
            tasks.append(task)
        
        return tasks
    
    def _detect_available_controllers(self) -> List[str]:
        """檢測可用的控制器"""
        available = []
        
        # 傳統控制器總是可用
        available.extend(["time_based", "queue_based"])
        
        # 檢查AI控制器的模型文件
        ai_controllers = ["dqn_step", "dqn_global", "nerl_step", "nerl_global"]
        for controller in ai_controllers:
            model_path = self.models_dir / f"{controller}.pth"
            if model_path.exists():
                available.append(controller)
        
        return available
    
    def _run_evaluation_parallel(self, evaluation_tasks: List[Dict]) -> Dict[str, bool]:
        """並行執行評估任務"""
        results = {}
        max_workers = min(3, len(evaluation_tasks))
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_task = {
                executor.submit(self._run_single_evaluation, task): task
                for task in evaluation_tasks
            }
            
            for i, future in enumerate(as_completed(future_to_task)):
                task = future_to_task[future]
                task_key = task["description"]
                
                try:
                    success, output = future.result()
                    results[task_key] = success
                    
                    if success:
                        self.print_success(f"✓ {task['run_name']} 完成")
                    else:
                        self.print_error(f"✗ {task['run_name']} 失敗")
                        
                except Exception as e:
                    self.print_error(f"✗ {task['run_name']} 異常: {e}")
                    results[task_key] = False
                
                self.print_progress(i + 1, len(evaluation_tasks), f"已完成 {i + 1}/{len(evaluation_tasks)} 個實驗")
        
        return results
    
    def _run_evaluation_sequential(self, evaluation_tasks: List[Dict]) -> Dict[str, bool]:
        """順序執行評估任務"""
        results = {}
        
        for i, task in enumerate(evaluation_tasks):
            self.print_progress(i, len(evaluation_tasks), f"正在執行 {task['run_name']}")
            
            success, output = self._run_single_evaluation(task)
            results[task["description"]] = success
            
            if success:
                self.print_success(f"✓ {task['run_name']} 完成")
            else:
                self.print_error(f"✗ {task['run_name']} 失敗")
            
            self.print_progress(i + 1, len(evaluation_tasks), f"已完成 {i + 1}/{len(evaluation_tasks)} 個實驗")
        
        return results
    
    def _run_single_evaluation(self, task: Dict) -> Tuple[bool, str]:
        """執行單個評估任務"""
        controllers_str = " ".join(task["controllers"])
        cmd = f"python evaluate.py --controllers {controllers_str}"
        cmd += f" --ticks {task['ticks']}"
        cmd += f" --seed {task['seed']}"
        cmd += f" --description \"{task['description']}\""
        
        if task.get('output_dir'):
            cmd += f" --output \"{task['output_dir']}\""
        
        # 添加 NetLogo 參數（如果任務配置中指定）
        if task.get('use_netlogo', False):
            cmd += " --netlogo"
        
        # 添加日誌級別參數
        log_level = task.get('log_level', 'INFO')
        cmd += f" --log_level {log_level}"
        
        timeout = max(1200, task['ticks'] // 10)
        window_title = f"評估 {task['run_name']}"
        
        # 檢查是否使用新視窗（從任務配置中獲取，預設為True）
        use_new_window = task.get('use_new_windows', True)
        
        # 執行評估
        return self.run_command(cmd, f"評估實驗: {task['description']}", timeout,
                              open_new_window=use_new_window,
                              window_title=window_title)
    
    def run_analysis_workflow(self, config: Dict = None, specific_eval_dir: str = None) -> Dict[str, bool]:
        """
        執行數據分析工作流程
        
        Args:
            config: 分析配置
            specific_eval_dir: 特定的評估目錄名稱（如果提供，只分析這個目錄）
            
        Returns:
            dict: 執行結果
        """
        self.print_header("開始數據分析與圖表生成", Colors.YELLOW)
        
        # 找到評估結果目錄
        if specific_eval_dir:
            # 只分析特定目錄
            eval_path = self.results_dir / "evaluations" / specific_eval_dir
            if eval_path.exists():
                eval_dirs = [eval_path]
            else:
                self.print_error(f"找不到指定的評估目錄: {specific_eval_dir}")
                return {}
        else:
            # 分析所有目錄
            eval_dirs = list(self.results_dir.glob("evaluations/EVAL_*"))
        
        if not eval_dirs:
            self.print_warning("沒有找到評估結果目錄")
            return {}
        
        results = {}
        self.execution_stats["total_tasks"] += len(eval_dirs)
        
        # 為每個結果目錄生成圖表
        for i, eval_dir in enumerate(eval_dirs):
            self.print_progress(i, len(eval_dirs), f"正在分析 {eval_dir.name}")
            
            success, output = self._generate_charts_for_result(eval_dir, config)
            results[eval_dir.name] = success
            
            if success:
                self.print_success(f"✓ {eval_dir.name} 圖表生成完成")
            else:
                self.print_error(f"✗ {eval_dir.name} 圖表生成失敗")
            
            self.print_progress(i + 1, len(eval_dirs), f"已完成 {i + 1}/{len(eval_dirs)} 個分析")
        
        # 統計結果
        successful = sum(1 for success in results.values() if success)
        self.execution_stats["completed_tasks"] += successful
        self.execution_stats["failed_tasks"] += len(results) - successful
        self.execution_stats["results"]["analysis"] = results
        
        color = Colors.GREEN if successful == len(results) else Colors.YELLOW
        self.print_header(f"分析完成: {successful}/{len(results)} 個圖表成功", color)
        
        return results
    
    def _generate_charts_for_result(self, eval_dir: Path, config: Dict = None) -> Tuple[bool, str]:
        """為評估結果生成圖表"""
        cmd = f"python visualization_generator.py \"{eval_dir}\""
        
        if config:
            chart_types = config.get('types', 'all')
            if isinstance(chart_types, list):
                chart_types = ','.join(chart_types)
            cmd += f" --chart {chart_types}"
        else:
            cmd += " --chart all"
        
        return self.run_command(cmd, f"生成圖表: {eval_dir.name}", timeout=180)
    
    def run_complete_workflow(self, config: Dict, parallel: bool = True) -> Dict:
        """
        執行完整實驗工作流程
        
        Args:
            config: 完整實驗配置
            parallel: 是否並行執行
            
        Returns:
            dict: 執行結果
        """
        self.print_header("開始完整實驗流程", Colors.GREEN)
        self.execution_stats["start_time"] = datetime.now()
        
        complete_results = {}
        
        # 階段1：模型訓練
        if 'training' in config:
            self.print_info("階段1：AI模型訓練")
            training_results = self.run_training_workflow(config['training'], parallel)
            complete_results['training'] = training_results
        
        # 階段2：效能評估
        if 'evaluation' in config:
            self.print_info("階段2：效能評估")
            evaluation_results = self.run_evaluation_workflow(config['evaluation'], parallel)
            complete_results['evaluation'] = evaluation_results
        
        # 階段3：數據分析
        if 'analysis' in config or config.get('auto_analysis', True):
            self.print_info("階段3：數據分析與圖表")
            analysis_config = config.get('analysis', config.get('charts', {}))
            analysis_results = self.run_analysis_workflow(analysis_config)
            complete_results['analysis'] = analysis_results
        
        self.execution_stats["end_time"] = datetime.now()
        
        # 顯示最終統計
        self._show_final_statistics(complete_results)
        
        return complete_results
    
    def _show_final_statistics(self, results: Dict):
        """顯示最終統計結果"""
        self.print_header("實驗完成統計", Colors.GREEN)
        
        total_time = None
        if self.execution_stats["start_time"] and self.execution_stats["end_time"]:
            total_time = (self.execution_stats["end_time"] - self.execution_stats["start_time"]).total_seconds() / 60
        
        print(f"{Colors.WHITE}執行統計:{Colors.END}")
        if total_time:
            print(f"  總耗時: {total_time:.1f} 分鐘")
        print(f"  總任務數: {self.execution_stats['total_tasks']}")
        print(f"  成功任務: {self.execution_stats['completed_tasks']}")
        print(f"  失敗任務: {self.execution_stats['failed_tasks']}")
        
        success_rate = (self.execution_stats['completed_tasks'] / max(1, self.execution_stats['total_tasks'])) * 100
        color = Colors.GREEN if success_rate >= 80 else Colors.YELLOW if success_rate >= 50 else Colors.RED
        print(f"  {color}成功率: {success_rate:.1f}%{Colors.END}")
        
        # 詳細結果
        for stage, stage_results in results.items():
            if stage_results:
                successful = sum(1 for success in stage_results.values() if success)
                total = len(stage_results)
                stage_rate = (successful / total) * 100 if total > 0 else 0
                stage_color = Colors.GREEN if stage_rate >= 80 else Colors.YELLOW if stage_rate >= 50 else Colors.RED
                
                stage_name = {"training": "模型訓練", "evaluation": "效能評估", "analysis": "數據分析"}.get(stage, stage)
                print(f"  {stage_color}{stage_name}: {successful}/{total} ({stage_rate:.1f}%){Colors.END}")
        
        # 顯示結果位置
        print(f"\n{Colors.WHITE}結果文件位置:{Colors.END}")
        
        if 'evaluation' in results:
            eval_dirs = list(self.results_dir.glob("evaluations/EVAL_*"))
            if eval_dirs:
                latest_eval = max(eval_dirs, key=lambda x: x.stat().st_mtime)
                print(f"  📊 最新評估結果: {latest_eval}")
        
        if 'analysis' in results:
            print(f"  📈 圖表文件: result/evaluations/*/charts/")
        
        print(f"\n{Colors.CYAN}🎉 實驗流程完成！{Colors.END}")
    
    def get_execution_stats(self) -> Dict:
        """獲取執行統計資訊"""
        return self.execution_stats.copy()
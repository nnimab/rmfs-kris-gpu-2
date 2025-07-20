#!/usr/bin/env python3
"""
RMFS 實驗自動化管理系統
====================

自動化實驗流程管理工具，整合訓練、評估和圖表生成
支持多線程執行和智能參數配置

作者: Claude
版本: 1.0
日期: 2025-07-09
"""

import os
import sys
import time
import json
import subprocess
import threading
import glob
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional, Tuple
from pathlib import Path

class Colors:
    """控制台顏色輸出"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    MAGENTA = '\033[95m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    END = '\033[0m'

class ExperimentManager:
    """實驗管理器主類"""
    
    def __init__(self):
        self.project_root = Path.cwd()
        self.models_dir = self.project_root / "models"
        self.results_dir = self.project_root / "result"
        
        # 實驗配置
        self.config = {
            "training": {
                "dqn_ticks": 10000,
                "nerl_generations": 20,
                "nerl_population": 20,
                "nerl_eval_ticks": 2000
            },
            "evaluation": {
                "ticks": 20000,
                "repeats": 3,
                "seeds": [42, 123, 789, 456, 999][:3]  # 取前3個作為預設
            },
            "parallel": {
                "training": True,
                "evaluation": True,
                "max_workers": 4
            }
        }
        
        # 控制器配置
        self.controllers = {
            "traditional": ["time_based", "queue_based"],
            "ai_training": [
                ("dqn", "step"), ("dqn", "global"),
                ("nerl", "step"), ("nerl", "global")
            ],
            "ai_models": [
                "dqn_step", "dqn_global", 
                "nerl_step", "nerl_global"
            ]
        }
        
        # 狀態追蹤
        self.current_session = None
        self.session_start_time = None
        
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
    
    def print_progress(self, step: int, total: int, description: str):
        """打印進度"""
        percentage = (step / total) * 100
        bar_length = 30
        filled_length = int(bar_length * step // total)
        bar = '█' * filled_length + '-' * (bar_length - filled_length)
        print(f"\r{Colors.BLUE}[{bar}] {percentage:.1f}% - {description}{Colors.END}", end='', flush=True)
        if step == total:
            print()  # 換行
    
    def check_dependencies(self) -> Dict[str, bool]:
        """檢查實驗依賴項"""
        self.print_info("檢查實驗依賴項...")
        
        deps = {
            "train.py": (self.project_root / "train.py").exists(),
            "evaluate.py": (self.project_root / "evaluate.py").exists(),
            "visualization_generator.py": (self.project_root / "visualization_generator.py").exists(),
            "models_dir": self.models_dir.exists(),
            "results_dir": True  # 結果目錄會自動創建
        }
        
        # 檢查模型文件
        model_files = {}
        for model in self.controllers["ai_models"]:
            model_path = self.models_dir / f"{model}.pth"
            model_files[f"model_{model}"] = model_path.exists()
        
        deps.update(model_files)
        
        # 報告狀態
        for dep, status in deps.items():
            if status:
                self.print_success(f"✓ {dep}")
            else:
                self.print_warning(f"✗ {dep}")
        
        return deps
    
    def run_command(self, cmd: str, description: str, timeout: int = 600) -> Tuple[bool, str]:
        """執行命令並返回結果"""
        self.print_info(f"執行: {description}")
        print(f"命令: {cmd}")
        
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
    
    def train_single_model(self, agent: str, reward_mode: str, config: Dict) -> Tuple[bool, str]:
        """訓練單個模型"""
        if agent == "dqn":
            cmd = f"python train.py --agent dqn --reward_mode {reward_mode} --training_ticks {config['dqn_ticks']}"
            timeout = max(600, config['dqn_ticks'] // 10)  # 至少10分鐘
        elif agent == "nerl":
            cmd = f"python train.py --agent nerl --reward_mode {reward_mode} --generations {config['nerl_generations']} --population {config['nerl_population']} --eval_ticks {config['nerl_eval_ticks']}"
            timeout = max(1200, config['nerl_generations'] * 60)  # 每代至少1分鐘
        else:
            return False, f"未知的代理類型: {agent}"
        
        description = f"{agent.upper()} {reward_mode} 模式訓練"
        success, output = self.run_command(cmd, description, timeout)
        
        # 自動重命名模型文件
        if success:
            self.rename_model_file(agent, reward_mode)
        
        return success, output
    
    def rename_model_file(self, agent: str, reward_mode: str):
        """自動重命名模型文件"""
        target_name = f"{agent}_{reward_mode}.pth"
        target_path = self.models_dir / target_name
        
        if target_path.exists():
            self.print_info(f"模型文件已存在: {target_name}")
            return
        
        # 查找最新的模型文件
        if agent == "dqn":
            pattern = f"dqn_traffic_*.pth"
        else:  # nerl
            pattern = f"nerl_traffic*.pth"
        
        model_files = list(self.models_dir.glob(pattern))
        if not model_files:
            self.print_warning(f"找不到 {agent} 的模型文件")
            return
        
        # 選擇最新的文件
        latest_file = max(model_files, key=lambda x: x.stat().st_mtime)
        
        try:
            import shutil
            shutil.copy2(latest_file, target_path)
            self.print_success(f"重命名模型: {latest_file.name} -> {target_name}")
        except Exception as e:
            self.print_error(f"重命名失敗: {e}")
    
    def train_all_models(self, parallel: bool = True) -> Dict[str, bool]:
        """訓練所有AI模型"""
        self.print_header("開始訓練所有AI模型", Colors.MAGENTA)
        
        # 根據配置決定要訓練的模型
        agents_to_train = self.config["training"].get("agents_to_train", ["dqn", "nerl"])
        reward_modes = self.config["training"].get("reward_modes", ["step", "global"])
        
        # 構建訓練任務列表
        training_tasks = []
        for agent in agents_to_train:
            for mode in reward_modes:
                training_tasks.append((agent, mode))
        
        results = {}
        
        if parallel and len(training_tasks) > 1:
            self.print_info(f"並行訓練 {len(training_tasks)} 個模型...")
            
            with ThreadPoolExecutor(max_workers=min(4, len(training_tasks))) as executor:
                future_to_task = {
                    executor.submit(
                        self.train_single_model, 
                        agent, reward_mode, self.config["training"]
                    ): (agent, reward_mode)
                    for agent, reward_mode in training_tasks
                }
                
                for i, future in enumerate(as_completed(future_to_task)):
                    agent, reward_mode = future_to_task[future]
                    task_name = f"{agent}_{reward_mode}"
                    
                    try:
                        success, output = future.result()
                        results[task_name] = success
                        
                        if success:
                            self.print_success(f"✓ {task_name} 訓練完成")
                        else:
                            self.print_error(f"✗ {task_name} 訓練失敗")
                            
                    except Exception as e:
                        self.print_error(f"✗ {task_name} 訓練異常: {e}")
                        results[task_name] = False
                    
                    self.print_progress(i + 1, len(training_tasks), f"已完成 {i + 1}/{len(training_tasks)} 個模型")
        else:
            self.print_info("順序訓練所有模型...")
            
            for i, (agent, reward_mode) in enumerate(training_tasks):
                task_name = f"{agent}_{reward_mode}"
                self.print_progress(i, len(training_tasks), f"正在訓練 {task_name}")
                
                success, output = self.train_single_model(agent, reward_mode, self.config["training"])
                results[task_name] = success
                
                if success:
                    self.print_success(f"✓ {task_name} 訓練完成")
                else:
                    self.print_error(f"✗ {task_name} 訓練失敗")
                
                self.print_progress(i + 1, len(training_tasks), f"已完成 {i + 1}/{len(training_tasks)} 個模型")
        
        # 總結訓練結果
        successful = sum(1 for success in results.values() if success)
        self.print_header(f"訓練總結: {successful}/{len(results)} 個模型成功", Colors.GREEN if successful == len(results) else Colors.YELLOW)
        
        return results
    
    def run_evaluation(self, controllers: List[str], description: str, seed: int = 42) -> Tuple[bool, str]:
        """運行評估實驗"""
        controllers_str = " ".join(controllers)
        cmd = f"python evaluate.py --controllers {controllers_str} --ticks {self.config['evaluation']['ticks']} --seed {seed}"
        
        # 添加描述（如果配置中有）
        eval_desc = self.config["evaluation"].get("description")
        if eval_desc:
            cmd += f" --description \"{eval_desc}_{description}\""
        else:
            cmd += f" --description \"{description}\""
        
        # 添加輸出目錄（如果配置中有）
        output_dir = self.config["evaluation"].get("output_dir")
        if output_dir:
            cmd += f" --output \"{output_dir}\""
        
        # 如果是分析模式
        if self.config["evaluation"].get("analysis_only", False):
            existing_dir = self.config["evaluation"].get("existing_results_dir")
            if existing_dir:
                cmd = f"python evaluate.py --analysis-only --output \"{existing_dir}\""
        
        timeout = max(1200, self.config['evaluation']['ticks'] // 10)  # 至少20分鐘
        return self.run_command(cmd, f"評估實驗: {description}", timeout)
    
    def run_all_evaluations(self, parallel: bool = True) -> Dict[str, bool]:
        """運行所有評估實驗"""
        self.print_header("開始性能評估實驗", Colors.CYAN)
        
        # 如果是分析模式，直接執行分析
        if self.config["evaluation"].get("analysis_only", False):
            existing_dir = self.config["evaluation"].get("existing_results_dir")
            if existing_dir:
                self.print_info(f"執行分析模式，分析目錄: {existing_dir}")
                success, output = self.run_evaluation([], "analysis_only", 0)
                return {"analysis_only": success}
            else:
                self.print_error("分析模式需要指定已有結果目錄")
                return {}
        
        # 決定要評估的控制器
        controllers_config = self.config["evaluation"].get("controllers_to_evaluate", "auto")
        
        if controllers_config == "auto":
            # 檢查可用控制器
            available_controllers = self.check_available_controllers()
        else:
            # 使用配置中指定的控制器
            available_controllers = controllers_config
            # 檢查這些控制器是否真的可用
            actual_available = self.check_available_controllers()
            available_controllers = [c for c in available_controllers if c in actual_available]
        
        self.print_info(f"將評估的控制器: {', '.join(available_controllers)}")
        
        if len(available_controllers) < 2:
            self.print_warning("控制器數量不足，需要至少2個控制器進行對比")
            return {}
        
        # 定義評估實驗
        evaluation_tasks = []
        
        # 基礎實驗：所有可用控制器
        evaluation_tasks.append({
            "controllers": available_controllers,
            "description": "complete_comparison",
            "name": "完整對比實驗"
        })
        
        # 傳統控制器基準測試
        traditional_available = [c for c in self.controllers["traditional"] if c in available_controllers]
        if len(traditional_available) >= 2:
            evaluation_tasks.append({
                "controllers": traditional_available,
                "description": "traditional_baseline",
                "name": "傳統控制器基準測試"
            })
        
        # AI控制器對比
        ai_available = [c for c in self.controllers["ai_models"] if c in available_controllers]
        if len(ai_available) >= 2:
            evaluation_tasks.append({
                "controllers": ai_available,
                "description": "ai_comparison",
                "name": "AI控制器對比"
            })
        
        # DQN對比（如果兩種模式都可用）
        dqn_controllers = [c for c in ai_available if c.startswith("dqn")]
        if len(dqn_controllers) >= 2:
            evaluation_tasks.append({
                "controllers": dqn_controllers,
                "description": "dqn_comparison",
                "name": "DQN獎勵模式對比"
            })
        
        # NERL對比（如果兩種模式都可用）
        nerl_controllers = [c for c in ai_available if c.startswith("nerl")]
        if len(nerl_controllers) >= 2:
            evaluation_tasks.append({
                "controllers": nerl_controllers,
                "description": "nerl_comparison",
                "name": "NERL獎勵模式對比"
            })
        
        results = {}
        seeds = self.config["evaluation"]["seeds"]
        
        # 對每個實驗進行多次重複
        all_tasks = []
        for task in evaluation_tasks:
            for i, seed in enumerate(seeds):
                task_copy = task.copy()
                task_copy["seed"] = seed
                task_copy["description"] = f"{task['description']}_seed{seed}"
                task_copy["full_name"] = f"{task['name']} (第{i+1}次, seed={seed})"
                all_tasks.append(task_copy)
        
        if parallel and len(all_tasks) > 1:
            self.print_info(f"並行執行 {len(all_tasks)} 個評估實驗...")
            
            with ThreadPoolExecutor(max_workers=min(3, len(all_tasks))) as executor:
                future_to_task = {
                    executor.submit(
                        self.run_evaluation,
                        task["controllers"],
                        task["description"],
                        task["seed"]
                    ): task
                    for task in all_tasks
                }
                
                for i, future in enumerate(as_completed(future_to_task)):
                    task = future_to_task[future]
                    task_key = task["description"]
                    
                    try:
                        success, output = future.result()
                        results[task_key] = success
                        
                        if success:
                            self.print_success(f"✓ {task['full_name']} 完成")
                        else:
                            self.print_error(f"✗ {task['full_name']} 失敗")
                            
                    except Exception as e:
                        self.print_error(f"✗ {task['full_name']} 異常: {e}")
                        results[task_key] = False
                    
                    self.print_progress(i + 1, len(all_tasks), f"已完成 {i + 1}/{len(all_tasks)} 個實驗")
        else:
            self.print_info("順序執行所有評估實驗...")
            
            for i, task in enumerate(all_tasks):
                self.print_progress(i, len(all_tasks), f"正在執行 {task['full_name']}")
                
                success, output = self.run_evaluation(
                    task["controllers"],
                    task["description"],
                    task["seed"]
                )
                results[task["description"]] = success
                
                if success:
                    self.print_success(f"✓ {task['full_name']} 完成")
                else:
                    self.print_error(f"✗ {task['full_name']} 失敗")
                
                self.print_progress(i + 1, len(all_tasks), f"已完成 {i + 1}/{len(all_tasks)} 個實驗")
        
        # 總結評估結果
        successful = sum(1 for success in results.values() if success)
        self.print_header(f"評估總結: {successful}/{len(results)} 個實驗成功", Colors.GREEN if successful == len(results) else Colors.YELLOW)
        
        return results
    
    def check_available_controllers(self) -> List[str]:
        """檢查可用的控制器"""
        available = []
        
        # 傳統控制器總是可用
        available.extend(self.controllers["traditional"])
        
        # 檢查AI控制器的模型文件
        for model in self.controllers["ai_models"]:
            model_path = self.models_dir / f"{model}.pth"
            if model_path.exists():
                available.append(model)
        
        return available
    
    def generate_all_charts(self) -> Dict[str, bool]:
        """生成所有實驗的圖表"""
        self.print_header("開始生成實驗圖表", Colors.YELLOW)
        
        # 找到所有評估結果目錄
        eval_dirs = list(self.results_dir.glob("evaluations/EVAL_*"))
        
        if not eval_dirs:
            self.print_warning("沒有找到評估結果目錄")
            return {}
        
        results = {}
        
        # 獲取圖表配置
        chart_config = self.config.get("charts", {})
        chart_types = chart_config.get("chart_types", "all")
        
        for i, eval_dir in enumerate(eval_dirs):
            self.print_progress(i, len(eval_dirs), f"正在生成 {eval_dir.name} 的圖表")
            
            # 構建命令
            if chart_types == "all":
                cmd = f"python visualization_generator.py {eval_dir} --chart all"
            elif isinstance(chart_types, list):
                # 為每種圖表類型生成
                for chart_type in chart_types:
                    cmd = f"python visualization_generator.py {eval_dir} --chart {chart_type}"
                    success, output = self.run_command(
                        cmd, f"生成 {chart_type} 圖表: {eval_dir.name}", timeout=180
                    )
                    results[f"{eval_dir.name}_{chart_type}"] = success
                continue
            else:
                cmd = f"python visualization_generator.py {eval_dir} --chart {chart_types}"
            
            success, output = self.run_command(
                cmd, f"生成圖表: {eval_dir.name}", timeout=180
            )
            
            results[eval_dir.name] = success
            
            if success:
                self.print_success(f"✓ {eval_dir.name} 圖表生成完成")
            else:
                self.print_error(f"✗ {eval_dir.name} 圖表生成失敗")
            
            self.print_progress(i + 1, len(eval_dirs), f"已完成 {i + 1}/{len(eval_dirs)} 個圖表")
        
        # 總結圖表生成結果
        successful = sum(1 for success in results.values() if success)
        self.print_header(f"圖表總結: {successful}/{len(results)} 個圖表成功", Colors.GREEN if successful == len(results) else Colors.YELLOW)
        
        return results
    
    def save_session_summary(self, training_results: Dict, evaluation_results: Dict, chart_results: Dict):
        """保存實驗會話總結"""
        if not self.current_session:
            return
        
        summary = {
            "session_id": self.current_session,
            "start_time": self.session_start_time.isoformat() if self.session_start_time else None,
            "end_time": datetime.now().isoformat(),
            "config": self.config,
            "results": {
                "training": training_results,
                "evaluation": evaluation_results,
                "charts": chart_results
            },
            "statistics": {
                "training_success_rate": sum(1 for success in training_results.values() if success) / len(training_results) if training_results else 0,
                "evaluation_success_rate": sum(1 for success in evaluation_results.values() if success) / len(evaluation_results) if evaluation_results else 0,
                "chart_success_rate": sum(1 for success in chart_results.values() if success) / len(chart_results) if chart_results else 0
            }
        }
        
        # 保存總結文件
        summary_dir = self.results_dir / "session_summaries"
        summary_dir.mkdir(exist_ok=True)
        
        summary_file = summary_dir / f"{self.current_session}_summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        self.print_success(f"實驗會話總結已保存: {summary_file}")

class ExperimentInterface:
    """實驗管理界面"""
    
    def __init__(self):
        self.manager = ExperimentManager()
        self.presets = {
            "快速模式": {
                "training": {
                    "dqn_ticks": 5000,
                    "nerl_generations": 10,
                    "nerl_population": 15,
                    "nerl_eval_ticks": 1000
                },
                "evaluation": {
                    "ticks": 10000,
                    "repeats": 2,
                    "seeds": [42, 123]
                }
            },
            "標準模式": {
                "training": {
                    "dqn_ticks": 10000,
                    "nerl_generations": 20,
                    "nerl_population": 20,
                    "nerl_eval_ticks": 2000
                },
                "evaluation": {
                    "ticks": 20000,
                    "repeats": 3,
                    "seeds": [42, 123, 789]
                }
            },
            "論文模式": {
                "training": {
                    "dqn_ticks": 20000,
                    "nerl_generations": 50,
                    "nerl_population": 25,
                    "nerl_eval_ticks": 3000
                },
                "evaluation": {
                    "ticks": 30000,
                    "repeats": 5,
                    "seeds": [42, 123, 789, 456, 999]
                }
            }
        }
    
    def show_banner(self):
        """顯示系統橫幅"""
        banner = f"""
{Colors.CYAN}{Colors.BOLD}
╔══════════════════════════════════════════════════════════════╗
║                RMFS 實驗自動化管理系統                         ║
║                  Experiment Manager v1.0                    ║
║                                                            ║
║  🤖 自動化訓練 AI 控制器                                        ║
║  📊 批量性能評估實驗                                           ║
║  📈 智能圖表生成                                              ║
║  🚀 多線程並行執行                                            ║
║                                                            ║
║  作者: Claude AI Assistant                                  ║
║  日期: {datetime.now().strftime('%Y-%m-%d')}                                       ║
╚══════════════════════════════════════════════════════════════╝
{Colors.END}"""
        print(banner)
    
    def show_main_menu(self):
        """顯示主選單"""
        self.manager.print_header("主選單", Colors.BLUE)
        
        menu_options = [
            ("1", "完整實驗流程", "🚀 訓練 → 評估 → 圖表 (推薦新手)"),
            ("2", "模型訓練階段", "🤖 訓練所有 AI 控制器"),
            ("3", "性能評估階段", "📊 評估控制器性能對比"),
            ("4", "圖表生成階段", "📈 生成實驗視覺化圖表"),
            ("5", "系統狀態檢查", "🔍 檢查依賴項和模型狀態"),
            ("6", "配置參數設置", "⚙️  自定義實驗參數"),
            ("7", "查看實驗歷史", "📋 查看過往實驗記錄"),
            ("", "─" * 50, ""),
            ("Q", "退出系統", "👋 結束並退出")
        ]
        
        for option, title, description in menu_options:
            if option == "":
                print(description)
            else:
                print(f"{Colors.WHITE}[{Colors.CYAN}{option}{Colors.WHITE}] {Colors.BOLD}{title}{Colors.END}")
                print(f"    {Colors.YELLOW}{description}{Colors.END}")
                print()
    
    def get_user_choice(self, prompt: str = "您的選擇", valid_choices: List[str] = None) -> str:
        """獲取用戶選擇"""
        if valid_choices is None:
            valid_choices = ["1", "2", "3", "4", "5", "6", "7", "Q", "q"]
        
        while True:
            choice = input(f"\n{Colors.CYAN}{prompt}: {Colors.END}").strip()
            
            if choice.upper() in [c.upper() for c in valid_choices]:
                return choice.upper()
            else:
                self.manager.print_error(f"無效選擇，請輸入: {', '.join(valid_choices)}")
    
    def show_preset_menu(self):
        """顯示預設配置選單"""
        self.manager.print_header("選擇實驗模式", Colors.MAGENTA)
        
        print(f"{Colors.WHITE}可用的預設配置:{Colors.END}\n")
        
        presets_info = {
            "快速模式": ("⚡", "適合測試和驗證", "約 1-2 小時"),
            "標準模式": ("🎯", "平衡的性能和時間", "約 3-4 小時"),
            "論文模式": ("🎓", "高品質學術結果", "約 6-8 小時")
        }
        
        choices = ["1", "2", "3", "4"]
        for i, (preset_name, preset_config) in enumerate(self.presets.items(), 1):
            icon, desc, time_est = presets_info[preset_name]
            print(f"{Colors.WHITE}[{Colors.CYAN}{i}{Colors.WHITE}] {icon} {Colors.BOLD}{preset_name}{Colors.END}")
            print(f"    {Colors.YELLOW}{desc} - {time_est}{Colors.END}")
            
            # 顯示具體配置
            training = preset_config["training"]
            evaluation = preset_config["evaluation"]
            print(f"    訓練: DQN {training['dqn_ticks']} ticks, NERL {training['nerl_generations']} 代 ({training['nerl_eval_ticks']} eval ticks)")
            print(f"    評估: {evaluation['ticks']} ticks × {evaluation['repeats']} 次重複")
            print()
        
        print(f"{Colors.WHITE}[{Colors.CYAN}4{Colors.WHITE}] ⚙️  {Colors.BOLD}自定義配置{Colors.END}")
        print(f"    {Colors.YELLOW}手動設置所有參數{Colors.END}")
        print()
        
        choice = self.get_user_choice("選擇配置模式", choices)
        
        if choice in ["1", "2", "3"]:
            preset_name = list(self.presets.keys())[int(choice) - 1]
            self.manager.config.update(self.presets[preset_name])
            self.manager.print_success(f"已選擇: {preset_name}")
            return preset_name
        else:
            return self.custom_configuration()
    
    def custom_configuration(self):
        """自定義配置 - 分頁式進階配置"""
        while True:
            self.manager.print_header("自定義實驗配置", Colors.YELLOW)
            
            print(f"{Colors.WHITE}配置類別選擇:{Colors.END}\n")
            
            menu_options = [
                ("1", "基本配置", "🎯 快速設置常用參數"),
                ("2", "進階訓練配置", "🤖 詳細訓練參數設置"),
                ("3", "進階評估配置", "📊 詳細評估參數設置"),
                ("4", "進階圖表配置", "📈 圖表生成參數設置"),
                ("5", "並行執行配置", "⚡ 多線程設置"),
                ("6", "配置管理", "💾 保存/載入配置"),
                ("", "─" * 50, ""),
                ("0", "完成配置", "✅ 返回主選單")
            ]
            
            for option, title, description in menu_options:
                if option == "":
                    print(description)
                else:
                    print(f"{Colors.WHITE}[{Colors.CYAN}{option}{Colors.WHITE}] {Colors.BOLD}{title}{Colors.END}")
                    print(f"    {Colors.YELLOW}{description}{Colors.END}")
                    print()
            
            choice = self.get_user_choice("選擇配置類別", ["1", "2", "3", "4", "5", "6", "0"])
            
            if choice == "1":
                self.basic_configuration()
            elif choice == "2":
                self.advanced_training_configuration()
            elif choice == "3":
                self.advanced_evaluation_configuration()
            elif choice == "4":
                self.advanced_chart_configuration()
            elif choice == "5":
                self.parallel_configuration()
            elif choice == "6":
                self.config_management()
            elif choice == "0":
                self.manager.print_success("自定義配置完成")
                return "自定義模式"
    
    def basic_configuration(self):
        """基本配置 - 原有的簡化配置"""
        self.manager.print_header("基本配置", Colors.CYAN)
        
        print(f"{Colors.WHITE}請設置訓練參數:{Colors.END}")
        
        # DQN 訓練配置
        current_dqn = self.manager.config["training"]["dqn_ticks"]
        dqn_ticks = input(f"DQN 訓練時長 [預設: {current_dqn}]: ").strip()
        if dqn_ticks.isdigit():
            self.manager.config["training"]["dqn_ticks"] = int(dqn_ticks)
        
        # NERL 訓練配置
        current_nerl_gen = self.manager.config["training"]["nerl_generations"]
        nerl_gen = input(f"NERL 進化代數 [預設: {current_nerl_gen}]: ").strip()
        if nerl_gen.isdigit():
            self.manager.config["training"]["nerl_generations"] = int(nerl_gen)
        
        current_nerl_pop = self.manager.config["training"]["nerl_population"]
        nerl_pop = input(f"NERL 族群大小 [預設: {current_nerl_pop}]: ").strip()
        if nerl_pop.isdigit():
            self.manager.config["training"]["nerl_population"] = int(nerl_pop)
        
        current_nerl_eval = self.manager.config["training"]["nerl_eval_ticks"]
        nerl_eval = input(f"NERL 評估時長 [預設: {current_nerl_eval}]: ").strip()
        if nerl_eval.isdigit():
            self.manager.config["training"]["nerl_eval_ticks"] = int(nerl_eval)
        
        print(f"\n{Colors.WHITE}請設置評估參數:{Colors.END}")
        
        # 評估配置
        current_eval = self.manager.config["evaluation"]["ticks"]
        eval_ticks = input(f"評估時長 [預設: {current_eval}]: ").strip()
        if eval_ticks.isdigit():
            self.manager.config["evaluation"]["ticks"] = int(eval_ticks)
        
        current_repeats = self.manager.config["evaluation"]["repeats"]
        repeats = input(f"重複次數 [預設: {current_repeats}]: ").strip()
        if repeats.isdigit():
            self.manager.config["evaluation"]["repeats"] = int(repeats)
            # 更新隨機種子列表
            base_seeds = [42, 123, 789, 456, 999, 111, 222, 333, 444, 555]
            self.manager.config["evaluation"]["seeds"] = base_seeds[:int(repeats)]
        
        self.manager.print_success("基本配置完成")
        input(f"\n{Colors.CYAN}按 Enter 繼續...{Colors.END}")
    
    def advanced_training_configuration(self):
        """進階訓練配置"""
        self.manager.print_header("進階訓練配置", Colors.MAGENTA)
        
        # 初始化訓練配置（如果不存在）
        if "agents_to_train" not in self.manager.config["training"]:
            self.manager.config["training"]["agents_to_train"] = ["dqn", "nerl"]
        if "reward_modes" not in self.manager.config["training"]:
            self.manager.config["training"]["reward_modes"] = ["step", "global"]
        
        print(f"{Colors.WHITE}1. 選擇要訓練的代理:{Colors.END}")
        print(f"   當前選擇: {', '.join(self.manager.config['training']['agents_to_train'])}")
        print(f"   [1] DQN only")
        print(f"   [2] NERL only")
        print(f"   [3] Both (預設)")
        agent_choice = input(f"選擇 [1-3, Enter跳過]: ").strip()
        
        if agent_choice == "1":
            self.manager.config["training"]["agents_to_train"] = ["dqn"]
        elif agent_choice == "2":
            self.manager.config["training"]["agents_to_train"] = ["nerl"]
        elif agent_choice == "3":
            self.manager.config["training"]["agents_to_train"] = ["dqn", "nerl"]
        
        print(f"\n{Colors.WHITE}2. 選擇獎勵模式:{Colors.END}")
        print(f"   當前選擇: {', '.join(self.manager.config['training']['reward_modes'])}")
        print(f"   [1] Step only (即時獎勵)")
        print(f"   [2] Global only (全局獎勵)")
        print(f"   [3] Both (預設)")
        reward_choice = input(f"選擇 [1-3, Enter跳過]: ").strip()
        
        if reward_choice == "1":
            self.manager.config["training"]["reward_modes"] = ["step"]
        elif reward_choice == "2":
            self.manager.config["training"]["reward_modes"] = ["global"]
        elif reward_choice == "3":
            self.manager.config["training"]["reward_modes"] = ["step", "global"]
        
        # DQN 詳細參數（如果選擇了DQN）
        if "dqn" in self.manager.config["training"]["agents_to_train"]:
            print(f"\n{Colors.WHITE}3. DQN 訓練參數:{Colors.END}")
            
            current_dqn = self.manager.config["training"]["dqn_ticks"]
            dqn_ticks = input(f"   訓練時長 [預設: {current_dqn}]: ").strip()
            if dqn_ticks.isdigit():
                self.manager.config["training"]["dqn_ticks"] = int(dqn_ticks)
            
            # 可以添加更多DQN特定參數，如學習率、批次大小等
        
        # NERL 詳細參數（如果選擇了NERL）
        if "nerl" in self.manager.config["training"]["agents_to_train"]:
            print(f"\n{Colors.WHITE}4. NERL 訓練參數:{Colors.END}")
            
            current_nerl_gen = self.manager.config["training"]["nerl_generations"]
            nerl_gen = input(f"   進化代數 [預設: {current_nerl_gen}]: ").strip()
            if nerl_gen.isdigit():
                self.manager.config["training"]["nerl_generations"] = int(nerl_gen)
            
            current_nerl_pop = self.manager.config["training"]["nerl_population"]
            nerl_pop = input(f"   族群大小 [預設: {current_nerl_pop}]: ").strip()
            if nerl_pop.isdigit():
                self.manager.config["training"]["nerl_population"] = int(nerl_pop)
            
            current_nerl_eval = self.manager.config["training"]["nerl_eval_ticks"]
            nerl_eval = input(f"   個體評估時長 [預設: {current_nerl_eval}]: ").strip()
            if nerl_eval.isdigit():
                self.manager.config["training"]["nerl_eval_ticks"] = int(nerl_eval)
        
        # 模型保存設置
        print(f"\n{Colors.WHITE}5. 模型保存設置:{Colors.END}")
        if "model_save_dir" not in self.manager.config["training"]:
            self.manager.config["training"]["model_save_dir"] = "models"
        
        current_save_dir = self.manager.config["training"]["model_save_dir"]
        save_dir = input(f"   模型保存目錄 [預設: {current_save_dir}]: ").strip()
        if save_dir:
            self.manager.config["training"]["model_save_dir"] = save_dir
        
        self.manager.print_success("進階訓練配置完成")
        input(f"\n{Colors.CYAN}按 Enter 繼續...{Colors.END}")
    
    def advanced_evaluation_configuration(self):
        """進階評估配置"""
        self.manager.print_header("進階評估配置", Colors.CYAN)
        
        # 初始化評估配置
        if "controllers_to_evaluate" not in self.manager.config["evaluation"]:
            self.manager.config["evaluation"]["controllers_to_evaluate"] = "auto"
        if "output_dir" not in self.manager.config["evaluation"]:
            self.manager.config["evaluation"]["output_dir"] = None
        if "description" not in self.manager.config["evaluation"]:
            self.manager.config["evaluation"]["description"] = None
        if "analysis_only" not in self.manager.config["evaluation"]:
            self.manager.config["evaluation"]["analysis_only"] = False
        
        print(f"{Colors.WHITE}1. 選擇要評估的控制器:{Colors.END}")
        print(f"   [1] 自動檢測所有可用控制器 (預設)")
        print(f"   [2] 只評估傳統控制器")
        print(f"   [3] 只評估AI控制器")
        print(f"   [4] 自定義選擇")
        
        controller_choice = input(f"選擇 [1-4, Enter跳過]: ").strip()
        
        if controller_choice == "2":
            self.manager.config["evaluation"]["controllers_to_evaluate"] = ["time_based", "queue_based"]
        elif controller_choice == "3":
            self.manager.config["evaluation"]["controllers_to_evaluate"] = ["dqn_step", "dqn_global", "nerl_step", "nerl_global"]
        elif controller_choice == "4":
            # 顯示所有可能的控制器
            all_controllers = ["time_based", "queue_based", "dqn_step", "dqn_global", "nerl_step", "nerl_global"]
            print(f"\n   可用控制器:")
            for i, controller in enumerate(all_controllers, 1):
                print(f"   [{i}] {controller}")
            
            selected = input(f"   輸入要評估的控制器編號（用逗號分隔，如: 1,3,5）: ").strip()
            if selected:
                try:
                    indices = [int(x.strip()) - 1 for x in selected.split(",")]
                    self.manager.config["evaluation"]["controllers_to_evaluate"] = [
                        all_controllers[i] for i in indices if 0 <= i < len(all_controllers)
                    ]
                except:
                    print(f"   {Colors.YELLOW}輸入無效，保持預設設置{Colors.END}")
        else:
            self.manager.config["evaluation"]["controllers_to_evaluate"] = "auto"
        
        print(f"\n{Colors.WHITE}2. 評估參數設置:{Colors.END}")
        
        # 評估時長
        current_ticks = self.manager.config["evaluation"]["ticks"]
        eval_ticks = input(f"   評估時長 [預設: {current_ticks}]: ").strip()
        if eval_ticks.isdigit():
            self.manager.config["evaluation"]["ticks"] = int(eval_ticks)
        
        # 重複次數和隨機種子
        current_repeats = self.manager.config["evaluation"]["repeats"]
        repeats = input(f"   重複次數 [預設: {current_repeats}]: ").strip()
        if repeats.isdigit():
            self.manager.config["evaluation"]["repeats"] = int(repeats)
            
            # 自定義隨機種子
            print(f"\n{Colors.WHITE}3. 隨機種子設置:{Colors.END}")
            print(f"   [1] 使用預設種子列表")
            print(f"   [2] 自定義種子列表")
            seed_choice = input(f"選擇 [1-2]: ").strip()
            
            if seed_choice == "2":
                seeds_input = input(f"   輸入種子列表（用逗號分隔）: ").strip()
                try:
                    custom_seeds = [int(x.strip()) for x in seeds_input.split(",")]
                    if len(custom_seeds) >= int(repeats):
                        self.manager.config["evaluation"]["seeds"] = custom_seeds[:int(repeats)]
                    else:
                        print(f"   {Colors.YELLOW}種子數量不足，已補充預設種子{Colors.END}")
                        base_seeds = [42, 123, 789, 456, 999, 111, 222, 333, 444, 555]
                        all_seeds = custom_seeds + base_seeds
                        self.manager.config["evaluation"]["seeds"] = all_seeds[:int(repeats)]
                except:
                    print(f"   {Colors.YELLOW}種子格式無效，使用預設種子{Colors.END}")
                    base_seeds = [42, 123, 789, 456, 999, 111, 222, 333, 444, 555]
                    self.manager.config["evaluation"]["seeds"] = base_seeds[:int(repeats)]
            else:
                # 使用預設種子
                base_seeds = [42, 123, 789, 456, 999, 111, 222, 333, 444, 555]
                self.manager.config["evaluation"]["seeds"] = base_seeds[:int(repeats)]
        
        # 輸出設置
        print(f"\n{Colors.WHITE}4. 輸出設置:{Colors.END}")
        
        output_dir = input(f"   結果輸出目錄 [留空使用自動命名]: ").strip()
        if output_dir:
            self.manager.config["evaluation"]["output_dir"] = output_dir
        
        description = input(f"   評估描述 [用於目錄命名]: ").strip()
        if description:
            self.manager.config["evaluation"]["description"] = description
        
        # 分析模式
        print(f"\n{Colors.WHITE}5. 分析模式:{Colors.END}")
        print(f"   [1] 完整分析（包含對比分析）")
        print(f"   [2] 僅分析，不重新評估")
        analysis_choice = input(f"選擇 [1-2, Enter跳過]: ").strip()
        
        if analysis_choice == "2":
            self.manager.config["evaluation"]["analysis_only"] = True
        else:
            self.manager.config["evaluation"]["analysis_only"] = False
        
        self.manager.print_success("進階評估配置完成")
        input(f"\n{Colors.CYAN}按 Enter 繼續...{Colors.END}")
    
    def advanced_chart_configuration(self):
        """進階圖表配置"""
        self.manager.print_header("進階圖表配置", Colors.YELLOW)
        
        # 初始化圖表配置
        if "charts" not in self.manager.config:
            self.manager.config["charts"] = {
                "chart_types": "all",
                "dpi": 300,
                "format": "png",
                "style": "whitegrid"
            }
        
        print(f"{Colors.WHITE}1. 選擇要生成的圖表類型:{Colors.END}")
        print(f"   [1] 所有圖表 (預設)")
        print(f"   [2] 性能對比雷達圖")
        print(f"   [3] 算法對比圖表")
        print(f"   [4] 獎勵機制對比圖")
        print(f"   [5] 性能排行榜圖")
        print(f"   [6] 綜合熱力圖")
        chart_choice = input(f"選擇 [1-6, Enter跳過]: ").strip()
        
        chart_map = {
            "1": "all",
            "2": "radar",
            "3": "algorithm",
            "4": "reward",
            "5": "rankings",
            "6": "heatmap"
        }
        
        if chart_choice in chart_map:
            self.manager.config["charts"]["chart_types"] = chart_map[chart_choice]
        
        print(f"\n{Colors.WHITE}2. 圖表品質設置:{Colors.END}")
        
        # DPI設置
        current_dpi = self.manager.config["charts"]["dpi"]
        dpi = input(f"   圖表解析度 DPI [預設: {current_dpi}]: ").strip()
        if dpi.isdigit():
            self.manager.config["charts"]["dpi"] = int(dpi)
        
        print(f"\n{Colors.WHITE}3. 圖表格式:{Colors.END}")
        print(f"   [1] PNG (預設)")
        print(f"   [2] PDF")
        print(f"   [3] SVG")
        format_choice = input(f"選擇 [1-3, Enter跳過]: ").strip()
        
        format_map = {"1": "png", "2": "pdf", "3": "svg"}
        if format_choice in format_map:
            self.manager.config["charts"]["format"] = format_map[format_choice]
        
        print(f"\n{Colors.WHITE}4. 圖表風格:{Colors.END}")
        print(f"   [1] Whitegrid (預設)")
        print(f"   [2] Darkgrid")
        print(f"   [3] White")
        print(f"   [4] Dark")
        style_choice = input(f"選擇 [1-4, Enter跳過]: ").strip()
        
        style_map = {"1": "whitegrid", "2": "darkgrid", "3": "white", "4": "dark"}
        if style_choice in style_map:
            self.manager.config["charts"]["style"] = style_map[style_choice]
        
        self.manager.print_success("進階圖表配置完成")
        input(f"\n{Colors.CYAN}按 Enter 繼續...{Colors.END}")
    
    def parallel_configuration(self):
        """並行執行配置"""
        self.manager.print_header("並行執行配置", Colors.GREEN)
        
        print(f"{Colors.WHITE}1. 訓練並行設置:{Colors.END}")
        current_train = "開" if self.manager.config["parallel"]["training"] else "關"
        print(f"   當前設置: {current_train}")
        train_choice = input(f"   啟用訓練並行? [Y/n]: ").strip().lower()
        self.manager.config["parallel"]["training"] = train_choice not in ['n', 'no', '否']
        
        print(f"\n{Colors.WHITE}2. 評估並行設置:{Colors.END}")
        current_eval = "開" if self.manager.config["parallel"]["evaluation"] else "關"
        print(f"   當前設置: {current_eval}")
        eval_choice = input(f"   啟用評估並行? [Y/n]: ").strip().lower()
        self.manager.config["parallel"]["evaluation"] = eval_choice not in ['n', 'no', '否']
        
        print(f"\n{Colors.WHITE}3. 最大並行數:{Colors.END}")
        current_workers = self.manager.config["parallel"]["max_workers"]
        workers = input(f"   最大並行工作數 [預設: {current_workers}]: ").strip()
        if workers.isdigit():
            self.manager.config["parallel"]["max_workers"] = int(workers)
        
        self.manager.print_success("並行執行配置完成")
        input(f"\n{Colors.CYAN}按 Enter 繼續...{Colors.END}")
    
    def config_management(self):
        """配置管理 - 保存和載入配置"""
        self.manager.print_header("配置管理", Colors.MAGENTA)
        
        print(f"{Colors.WHITE}配置操作:{Colors.END}\n")
        print(f"[1] 保存當前配置")
        print(f"[2] 載入配置文件")
        print(f"[3] 查看當前配置")
        print(f"[4] 重置為預設配置")
        print(f"[0] 返回")
        
        choice = self.get_user_choice("選擇操作", ["1", "2", "3", "4", "0"])
        
        if choice == "1":
            # 保存配置
            config_name = input(f"\n配置名稱 [預設: custom_config]: ").strip() or "custom_config"
            config_dir = Path("configs")
            config_dir.mkdir(exist_ok=True)
            
            config_file = config_dir / f"{config_name}.json"
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(self.manager.config, f, ensure_ascii=False, indent=2)
            
            self.manager.print_success(f"配置已保存至: {config_file}")
            
        elif choice == "2":
            # 載入配置
            config_dir = Path("configs")
            if config_dir.exists():
                config_files = list(config_dir.glob("*.json"))
                if config_files:
                    print(f"\n可用的配置文件:")
                    for i, file in enumerate(config_files, 1):
                        print(f"[{i}] {file.name}")
                    
                    file_choice = input(f"\n選擇配置文件 [1-{len(config_files)}]: ").strip()
                    if file_choice.isdigit() and 1 <= int(file_choice) <= len(config_files):
                        selected_file = config_files[int(file_choice) - 1]
                        
                        with open(selected_file, 'r', encoding='utf-8') as f:
                            loaded_config = json.load(f)
                        
                        self.manager.config.update(loaded_config)
                        self.manager.print_success(f"已載入配置: {selected_file.name}")
                else:
                    self.manager.print_warning("沒有找到配置文件")
            else:
                self.manager.print_warning("配置目錄不存在")
                
        elif choice == "3":
            # 查看當前配置
            print(f"\n{Colors.WHITE}當前配置:{Colors.END}")
            print(json.dumps(self.manager.config, ensure_ascii=False, indent=2))
            
        elif choice == "4":
            # 重置配置
            confirm = input(f"\n確定要重置所有配置嗎? [y/N]: ").strip().lower()
            if confirm in ['y', 'yes', '是']:
                self.manager.__init__()  # 重新初始化
                self.manager.print_success("配置已重置為預設值")
        
        input(f"\n{Colors.CYAN}按 Enter 繼續...{Colors.END}")
    
    def parallel_configuration(self):
        """並行執行配置"""
        self.manager.print_header("並行執行配置", Colors.GREEN)
        
        print(f"{Colors.WHITE}1. 訓練並行設置:{Colors.END}")
        current_train = "開" if self.manager.config["parallel"]["training"] else "關"
        print(f"   當前設置: {current_train}")
        train_choice = input(f"   啟用訓練並行? [Y/n]: ").strip().lower()
        self.manager.config["parallel"]["training"] = train_choice not in ['n', 'no', '否']
        
        print(f"\n{Colors.WHITE}2. 評估並行設置:{Colors.END}")
        current_eval = "開" if self.manager.config["parallel"]["evaluation"] else "關"
        print(f"   當前設置: {current_eval}")
        eval_choice = input(f"   啟用評估並行? [Y/n]: ").strip().lower()
        self.manager.config["parallel"]["evaluation"] = eval_choice not in ['n', 'no', '否']
        
        print(f"\n{Colors.WHITE}3. 最大並行數:{Colors.END}")
        current_workers = self.manager.config["parallel"]["max_workers"]
        workers = input(f"   最大並行工作數 [預設: {current_workers}]: ").strip()
        if workers.isdigit():
            self.manager.config["parallel"]["max_workers"] = int(workers)
        
        self.manager.print_success("並行執行配置完成")
        input(f"\n{Colors.CYAN}按 Enter 繼續...{Colors.END}")
    
    def config_management(self):
        """配置管理 - 保存和載入配置"""
        self.manager.print_header("配置管理", Colors.MAGENTA)
        
        print(f"{Colors.WHITE}配置操作:{Colors.END}\n")
        print(f"[1] 保存當前配置")
        print(f"[2] 載入配置文件")
        print(f"[3] 查看當前配置")
        print(f"[4] 重置為預設配置")
        print(f"[0] 返回")
        
        choice = self.get_user_choice("選擇操作", ["1", "2", "3", "4", "0"])
        
        if choice == "1":
            # 保存配置
            config_name = input(f"\n配置名稱 [預設: custom_config]: ").strip() or "custom_config"
            config_dir = Path("configs")
            config_dir.mkdir(exist_ok=True)
            
            config_file = config_dir / f"{config_name}.json"
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(self.manager.config, f, ensure_ascii=False, indent=2)
            
            self.manager.print_success(f"配置已保存至: {config_file}")
            
        elif choice == "2":
            # 載入配置
            config_dir = Path("configs")
            if config_dir.exists():
                config_files = list(config_dir.glob("*.json"))
                if config_files:
                    print(f"\n可用的配置文件:")
                    for i, file in enumerate(config_files, 1):
                        print(f"[{i}] {file.name}")
                    
                    file_choice = input(f"\n選擇配置文件 [1-{len(config_files)}]: ").strip()
                    if file_choice.isdigit() and 1 <= int(file_choice) <= len(config_files):
                        selected_file = config_files[int(file_choice) - 1]
                        
                        with open(selected_file, 'r', encoding='utf-8') as f:
                            loaded_config = json.load(f)
                        
                        self.manager.config.update(loaded_config)
                        self.manager.print_success(f"已載入配置: {selected_file.name}")
                else:
                    self.manager.print_warning("沒有找到配置文件")
            else:
                self.manager.print_warning("配置目錄不存在")
                
        elif choice == "3":
            # 查看當前配置
            print(f"\n{Colors.WHITE}當前配置:{Colors.END}")
            print(json.dumps(self.manager.config, ensure_ascii=False, indent=2))
            
        elif choice == "4":
            # 重置配置
            confirm = input(f"\n確定要重置所有配置嗎? [y/N]: ").strip().lower()
            if confirm in ['y', 'yes', '是']:
                self.manager.__init__()  # 重新初始化
                self.manager.print_success("配置已重置為預設值")
        
        input(f"\n{Colors.CYAN}按 Enter 繼續...{Colors.END}")
    
    def show_status(self):
        """顯示系統狀態"""
        self.manager.print_header("系統狀態檢查", Colors.CYAN)
        
        # 檢查依賴項
        deps = self.manager.check_dependencies()
        
        # 檢查可用控制器
        available_controllers = self.manager.check_available_controllers()
        
        print(f"\n{Colors.WHITE}可用控制器 ({len(available_controllers)} 個):{Colors.END}")
        for controller in available_controllers:
            if controller in self.manager.controllers["traditional"]:
                print(f"  {Colors.GREEN}✓{Colors.END} {controller} (傳統控制器)")
            else:
                print(f"  {Colors.GREEN}✓{Colors.END} {controller} (AI控制器)")
        
        # 顯示缺失的控制器
        all_possible = self.manager.controllers["traditional"] + self.manager.controllers["ai_models"]
        missing = [c for c in all_possible if c not in available_controllers]
        
        if missing:
            print(f"\n{Colors.WHITE}缺失的控制器 ({len(missing)} 個):{Colors.END}")
            for controller in missing:
                if controller in self.manager.controllers["ai_models"]:
                    model_path = self.manager.models_dir / f"{controller}.pth"
                    print(f"  {Colors.RED}✗{Colors.END} {controller} (缺少模型: {model_path})")
        
        # 顯示當前配置
        print(f"\n{Colors.WHITE}當前配置:{Colors.END}")
        print(f"  訓練: DQN {self.manager.config['training']['dqn_ticks']} ticks, NERL {self.manager.config['training']['nerl_generations']} 代 ({self.manager.config['training']['nerl_eval_ticks']} eval ticks)")
        print(f"  評估: {self.manager.config['evaluation']['ticks']} ticks × {self.manager.config['evaluation']['repeats']} 次")
        print(f"  並行: 訓練={'是' if self.manager.config['parallel']['training'] else '否'}, 評估={'是' if self.manager.config['parallel']['evaluation'] else '否'}")
        
        input(f"\n{Colors.CYAN}按 Enter 繼續...{Colors.END}")
    
    def show_experiment_history(self):
        """顯示實驗歷史"""
        self.manager.print_header("實驗歷史記錄", Colors.YELLOW)
        
        summary_dir = self.manager.results_dir / "session_summaries"
        
        if not summary_dir.exists():
            self.manager.print_info("還沒有實驗歷史記錄")
            input(f"\n{Colors.CYAN}按 Enter 繼續...{Colors.END}")
            return
        
        summary_files = list(summary_dir.glob("*_summary.json"))
        
        if not summary_files:
            self.manager.print_info("還沒有實驗歷史記錄")
            input(f"\n{Colors.CYAN}按 Enter 繼續...{Colors.END}")
            return
        
        # 按時間排序
        summary_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        print(f"找到 {len(summary_files)} 個實驗會話記錄:\n")
        
        for i, summary_file in enumerate(summary_files[:10]):  # 只顯示最近10個
            try:
                with open(summary_file, 'r', encoding='utf-8') as f:
                    summary = json.load(f)
                
                session_id = summary.get("session_id", "未知")
                start_time = summary.get("start_time", "未知")
                stats = summary.get("statistics", {})
                
                print(f"{Colors.WHITE}[{i+1}] {session_id}{Colors.END}")
                print(f"    開始時間: {start_time}")
                print(f"    成功率: 訓練 {stats.get('training_success_rate', 0)*100:.1f}%, 評估 {stats.get('evaluation_success_rate', 0)*100:.1f}%, 圖表 {stats.get('chart_success_rate', 0)*100:.1f}%")
                print()
                
            except Exception as e:
                print(f"讀取 {summary_file.name} 失敗: {e}")
        
        input(f"\n{Colors.CYAN}按 Enter 繼續...{Colors.END}")
    
    def confirm_experiment(self, experiment_type: str) -> bool:
        """確認實驗執行"""
        self.manager.print_header(f"確認 {experiment_type}", Colors.YELLOW)
        
        # 估算時間
        training_time = 0
        evaluation_time = 0
        chart_time = 0
        
        if experiment_type in ["完整實驗流程", "模型訓練階段"]:
            # 估算訓練時間
            dqn_time = self.manager.config["training"]["dqn_ticks"] / 1000 * 2  # 每1000 ticks約2分鐘
            nerl_time = self.manager.config["training"]["nerl_generations"] * 3  # 每代約3分鐘
            training_time = (dqn_time * 2 + nerl_time * 2)  # 4個模型
            
            if not self.manager.config["parallel"]["training"]:
                training_time *= 1.0  # 順序執行不增加時間
            else:
                training_time *= 0.4  # 並行執行節省時間
        
        if experiment_type in ["完整實驗流程", "性能評估階段"]:
            # 估算評估時間
            eval_single = self.manager.config["evaluation"]["ticks"] / 1000 * 3  # 每1000 ticks約3分鐘
            eval_count = self.manager.config["evaluation"]["repeats"] * 5  # 約5個實驗組
            evaluation_time = eval_single * eval_count
            
            if self.manager.config["parallel"]["evaluation"]:
                evaluation_time *= 0.5  # 並行執行節省時間
        
        if experiment_type in ["完整實驗流程", "圖表生成階段"]:
            chart_time = 10  # 約10分鐘
        
        total_time = training_time + evaluation_time + chart_time
        
        print(f"{Colors.WHITE}實驗配置摘要:{Colors.END}")
        print(f"  實驗類型: {experiment_type}")
        
        if training_time > 0:
            print(f"  訓練時間: 約 {training_time:.0f} 分鐘")
            print(f"    - DQN: {self.manager.config['training']['dqn_ticks']} ticks × 2 模式")
            print(f"    - NERL: {self.manager.config['training']['nerl_generations']} 代 × 2 模式 ({self.manager.config['training']['nerl_eval_ticks']} eval ticks)")
        
        if evaluation_time > 0:
            print(f"  評估時間: 約 {evaluation_time:.0f} 分鐘")
            print(f"    - 評估時長: {self.manager.config['evaluation']['ticks']} ticks")
            print(f"    - 重複次數: {self.manager.config['evaluation']['repeats']} 次")
        
        if chart_time > 0:
            print(f"  圖表生成: 約 {chart_time:.0f} 分鐘")
        
        print(f"\n  {Colors.BOLD}預估總時間: 約 {total_time:.0f} 分鐘 ({total_time/60:.1f} 小時){Colors.END}")
        print(f"  並行執行: 訓練={'開' if self.manager.config['parallel']['training'] else '關'}, 評估={'開' if self.manager.config['parallel']['evaluation'] else '關'}")
        
        choice = input(f"\n{Colors.CYAN}確認開始實驗? [Y/n]: {Colors.END}").strip().lower()
        return choice not in ['n', 'no', '否']
    
    def run_complete_experiment(self):
        """運行完整實驗流程"""
        if not self.confirm_experiment("完整實驗流程"):
            self.manager.print_info("已取消實驗")
            return
        
        # 設置會話ID
        self.manager.current_session = f"complete_exp_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.manager.session_start_time = datetime.now()
        
        self.manager.print_header("開始完整實驗流程", Colors.GREEN)
        
        # 第一步：模型訓練
        self.manager.print_info("第一步：訓練所有AI模型")
        training_results = self.manager.train_all_models(
            parallel=self.manager.config["parallel"]["training"]
        )
        
        # 第二步：性能評估
        self.manager.print_info("第二步：執行性能評估")
        evaluation_results = self.manager.run_all_evaluations(
            parallel=self.manager.config["parallel"]["evaluation"]
        )
        
        # 第三步：圖表生成
        self.manager.print_info("第三步：生成實驗圖表")
        chart_results = self.manager.generate_all_charts()
        
        # 保存會話總結
        self.manager.save_session_summary(training_results, evaluation_results, chart_results)
        
        # 顯示最終結果
        self.show_final_results(training_results, evaluation_results, chart_results)
    
    def show_final_results(self, training_results: Dict, evaluation_results: Dict, chart_results: Dict):
        """顯示最終實驗結果"""
        self.manager.print_header("實驗完成總結", Colors.GREEN)
        
        # 計算成功率
        training_success = sum(1 for success in training_results.values() if success) if training_results else 0
        training_total = len(training_results) if training_results else 0
        training_rate = (training_success / training_total * 100) if training_total > 0 else 0
        
        evaluation_success = sum(1 for success in evaluation_results.values() if success) if evaluation_results else 0
        evaluation_total = len(evaluation_results) if evaluation_results else 0
        evaluation_rate = (evaluation_success / evaluation_total * 100) if evaluation_total > 0 else 0
        
        chart_success = sum(1 for success in chart_results.values() if success) if chart_results else 0
        chart_total = len(chart_results) if chart_results else 0
        chart_rate = (chart_success / chart_total * 100) if chart_total > 0 else 0
        
        print(f"{Colors.WHITE}實驗結果統計:{Colors.END}")
        
        if training_results:
            color = Colors.GREEN if training_rate >= 80 else Colors.YELLOW if training_rate >= 50 else Colors.RED
            print(f"  {color}🤖 模型訓練: {training_success}/{training_total} ({training_rate:.1f}%){Colors.END}")
        
        if evaluation_results:
            color = Colors.GREEN if evaluation_rate >= 80 else Colors.YELLOW if evaluation_rate >= 50 else Colors.RED
            print(f"  {color}📊 性能評估: {evaluation_success}/{evaluation_total} ({evaluation_rate:.1f}%){Colors.END}")
        
        if chart_results:
            color = Colors.GREEN if chart_rate >= 80 else Colors.YELLOW if chart_rate >= 50 else Colors.RED
            print(f"  {color}📈 圖表生成: {chart_success}/{chart_total} ({chart_rate:.1f}%){Colors.END}")
        
        # 顯示結果位置
        print(f"\n{Colors.WHITE}結果文件位置:{Colors.END}")
        
        if evaluation_results:
            eval_dirs = list(self.manager.results_dir.glob("evaluations/EVAL_*"))
            if eval_dirs:
                latest_eval = max(eval_dirs, key=lambda x: x.stat().st_mtime)
                print(f"  📊 最新評估結果: {latest_eval}")
        
        if chart_results:
            print(f"  📈 圖表文件: result/evaluations/*/charts/")
        
        if self.manager.current_session:
            summary_file = self.manager.results_dir / "session_summaries" / f"{self.manager.current_session}_summary.json"
            if summary_file.exists():
                print(f"  📋 實驗總結: {summary_file}")
        
        total_time = (datetime.now() - self.manager.session_start_time).total_seconds() / 60 if self.manager.session_start_time else 0
        print(f"\n{Colors.CYAN}🎉 實驗完成！總耗時: {total_time:.1f} 分鐘{Colors.END}")
        
        input(f"\n{Colors.CYAN}按 Enter 繼續...{Colors.END}")
    
    def run_training_only(self):
        """只運行訓練階段"""
        if not self.confirm_experiment("模型訓練階段"):
            self.manager.print_info("已取消訓練")
            return
        
        self.manager.current_session = f"training_only_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.manager.session_start_time = datetime.now()
        
        training_results = self.manager.train_all_models(
            parallel=self.manager.config["parallel"]["training"]
        )
        
        self.show_final_results(training_results, {}, {})
    
    def run_evaluation_only(self):
        """只運行評估階段"""
        if not self.confirm_experiment("性能評估階段"):
            self.manager.print_info("已取消評估")
            return
        
        self.manager.current_session = f"evaluation_only_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.manager.session_start_time = datetime.now()
        
        evaluation_results = self.manager.run_all_evaluations(
            parallel=self.manager.config["parallel"]["evaluation"]
        )
        
        self.show_final_results({}, evaluation_results, {})
    
    def run_charts_only(self):
        """只運行圖表生成"""
        chart_results = self.manager.generate_all_charts()
        self.show_final_results({}, {}, chart_results)
    
    def run(self):
        """運行主界面"""
        try:
            self.show_banner()
            
            while True:
                self.show_main_menu()
                choice = self.get_user_choice()
                
                if choice == "1":
                    # 完整實驗流程
                    preset = self.show_preset_menu()
                    self.run_complete_experiment()
                    
                elif choice == "2":
                    # 模型訓練階段
                    preset = self.show_preset_menu()
                    self.run_training_only()
                    
                elif choice == "3":
                    # 性能評估階段
                    preset = self.show_preset_menu()
                    self.run_evaluation_only()
                    
                elif choice == "4":
                    # 圖表生成階段
                    self.run_charts_only()
                    
                elif choice == "5":
                    # 系統狀態檢查
                    self.show_status()
                    
                elif choice == "6":
                    # 配置參數設置
                    self.custom_configuration()
                    
                elif choice == "7":
                    # 查看實驗歷史
                    self.show_experiment_history()
                    
                elif choice == "Q":
                    # 退出系統
                    print(f"\n{Colors.CYAN}感謝使用 RMFS 實驗管理系統！{Colors.END}")
                    print(f"{Colors.YELLOW}如有問題請查看文檔或聯繫開發者。{Colors.END}\n")
                    break
        
        except KeyboardInterrupt:
            print(f"\n\n{Colors.YELLOW}程序被用戶中斷{Colors.END}")
        except Exception as e:
            print(f"\n{Colors.RED}發生未預期的錯誤: {e}{Colors.END}")
            import traceback
            traceback.print_exc()


def main():
    """主函數"""
    interface = ExperimentInterface()
    interface.run()


if __name__ == "__main__":
    main()
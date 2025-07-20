#!/usr/bin/env python3
"""
RMFS 簡潔實驗管理系統
====================

專注於核心功能的實驗自動化管理工具
- 🤖 AI模型訓練
- 📊 效能驗證  
- 📈 數據分析與圖表
- 🚀 完整實驗流程
- ⚙️ 自定義參數設置

作者: Claude AI Assistant
版本: 1.0
日期: 2025-07-09
"""

import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

# 添加父目錄到路徑
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
sys.path.insert(0, str(parent_dir))

try:
    from experiment_tools.presets import list_presets, get_preset, format_preset_summary
    from experiment_tools.config_manager import ConfigManager
    from experiment_tools.workflow_runner import WorkflowRunner, Colors
    from experiment_tools.auto_parallel_fix import get_fixer
except ImportError as e:
    print(f"❌ 導入模組失敗: {e}")
    print("請確保所有依賴文件都在正確的位置")
    sys.exit(1)

class SimpleExperimentManager:
    """簡潔實驗管理器主類"""
    
    def __init__(self):
        """初始化管理器"""
        # 確保使用正確的專案根目錄
        current_file = Path(__file__).parent
        project_root = current_file.parent  # 從 experiment_tools 往上一層
        
        self.config_manager = ConfigManager()
        self.workflow_runner = WorkflowRunner(str(project_root))
        self.current_config = {}
        
    def show_banner(self):
        """顯示系統橫幅"""
        banner = f"""
{Colors.CYAN}{Colors.BOLD}
╔═══════════════════════════════════════════════╗
║            RMFS 實驗自動化系統                  ║
║               Simple Manager v1.0             ║
║                                             ║
║  🤖 AI模型訓練                               ║
║  📊 效能驗證 (6個控制器)                      ║  
║  📈 數據分析與圖表                            ║
║  🚀 完整實驗流程                              ║
║  ⚙️ 自定義參數設置                            ║
║                                             ║
║  作者: Claude AI Assistant                   ║
║  日期: {datetime.now().strftime('%Y-%m-%d')}                           ║
╚═══════════════════════════════════════════════╝
{Colors.END}"""
        print(banner)
    
    def show_main_menu(self):
        """顯示主選單"""
        print(f"\n{Colors.BLUE}{Colors.BOLD}{'='*50}")
        print("              主選單")
        print(f"{'='*50}{Colors.END}")
        
        print(f"\n{Colors.WHITE}[1] 🤖 訓練AI模型{Colors.END}")
        print(f"    - 訓練 DQN 和 NERL 模型")
        
        print(f"\n{Colors.WHITE}[2] 📊 效能驗證{Colors.END}")
        print(f"    - 測試所有6個控制器性能")
        
        print(f"\n{Colors.WHITE}[3] 📈 數據分析與圖表{Colors.END}")
        print(f"    - 生成已有結果的圖表")
        
        print(f"\n{Colors.WHITE}[4] 🚀 完整實驗流程{Colors.END}")
        print(f"    - 自動執行 訓練→驗證→分析")
        
        print(f"\n{Colors.WHITE}[5] ⚙️  自定義參數設置{Colors.END}")
        print(f"    - 手動設置所有訓練/評估參數")
        
        print(f"\n{Colors.WHITE}[0] 退出{Colors.END}")
    
    def get_user_choice(self, prompt: str = "請選擇", valid_choices: List[str] = None) -> str:
        """獲取用戶選擇"""
        if valid_choices is None:
            valid_choices = ["1", "2", "3", "4", "5", "0"]
        
        while True:
            choice = input(f"\n{Colors.CYAN}{prompt} [{'/'.join(valid_choices)}]: {Colors.END}").strip()
            
            if choice in valid_choices:
                return choice
            else:
                print(f"{Colors.RED}❌ 無效選擇，請輸入: {', '.join(valid_choices)}{Colors.END}")
    
    def show_preset_menu(self, workflow_type: str) -> str:
        """
        顯示預設配置選單
        
        Args:
            workflow_type: 工作流程類型 ('training', 'evaluation', 'complete')
            
        Returns:
            str: 選擇的預設配置名稱
        """
        title_map = {
            'training': '訓練AI模型',
            'evaluation': '效能驗證', 
            'complete': '完整實驗流程'
        }
        
        print(f"\n{Colors.MAGENTA}{Colors.BOLD}{'='*50}")
        print(f"              {title_map.get(workflow_type, '選擇實驗強度')}")
        print(f"{'='*50}{Colors.END}")
        
        if workflow_type == 'evaluation':
            print(f"\n{Colors.WHITE}將測試以下6個控制器:{Colors.END}")
            print(f"{Colors.GREEN}✓ time_based, queue_based (傳統){Colors.END}")
            print(f"{Colors.GREEN}✓ dqn_step, dqn_global, nerl_step, nerl_global (AI){Colors.END}")
        
        print(f"\n{Colors.WHITE}選擇實驗強度:{Colors.END}\n")
        
        # 獲取預設配置列表
        presets = list_presets()
        choices = []
        
        for i, preset in enumerate(presets, 1):
            choices.append(str(i))
            print(f"{Colors.WHITE}[{i}] {format_preset_summary(preset['key'])}{Colors.END}\n")
        
        print(f"{Colors.WHITE}[{len(presets) + 1}] 🔧 自定義參數{Colors.END}")
        print(f"    - 手動設置所有參數")
        choices.append(str(len(presets) + 1))
        
        print(f"\n{Colors.WHITE}[0] 返回主選單{Colors.END}")
        choices.append("0")
        
        choice = self.get_user_choice("選擇強度", choices)
        
        if choice == "0":
            return None
        elif choice == str(len(presets) + 1):
            return "custom"
        else:
            preset_idx = int(choice) - 1
            return presets[preset_idx]['key']
    
    def confirm_execution(self, workflow_type: str, preset_name: str, config: Dict) -> bool:
        """確認執行配置"""
        title_map = {
            'training': '訓練AI模型',
            'evaluation': '效能驗證',
            'complete': '完整實驗流程'
        }
        
        print(f"\n{Colors.YELLOW}{Colors.BOLD}{'='*50}")
        print(f"              確認執行配置")
        print(f"{'='*50}{Colors.END}")
        
        print(f"\n{Colors.WHITE}實驗類型:{Colors.END} {title_map.get(workflow_type, workflow_type)}")
        print(f"{Colors.WHITE}配置模式:{Colors.END} {preset_name}")
        
        # 顯示配置摘要
        if 'training' in config:
            training = config['training']
            print(f"\n{Colors.WHITE}🤖 訓練配置:{Colors.END}")
            
            # 檢查是否為新格式（論文級實驗）
            if any('_' in task_name for task_name in training.keys()):
                # 新格式：直接列出任務
                dqn_tasks = [name for name in training.keys() if name.startswith('dqn_')]
                nerl_tasks = [name for name in training.keys() if name.startswith('nerl_')]
                
                print(f"  - DQN 任務: {len(dqn_tasks)} 個 ({', '.join(dqn_tasks)})")
                print(f"  - NERL 任務: {len(nerl_tasks)} 個 ({', '.join(nerl_tasks)})")
                
                # 顯示總評估步數
                if 'total_eval_steps' in config:
                    steps = config['total_eval_steps']
                    print(f"  - 總評估步數: {steps:,} 步 ({steps/1e6:.1f}M)")
            else:
                # 舊格式
                print(f"  - DQN: {training.get('dqn_ticks', 'N/A')} ticks")
                print(f"  - NERL: {training.get('nerl_generations', 'N/A')}代, {training.get('nerl_population', 'N/A')}個體")
        
        if 'evaluation' in config:
            evaluation = config['evaluation']
            print(f"\n{Colors.WHITE}📊 評估配置:{Colors.END}")
            print(f"  - 評估時長: {evaluation.get('ticks', 'N/A')} ticks")
            print(f"  - 重複次數: {evaluation.get('repeats', 'N/A')} 次")
            print(f"  - 控制器數: 6個 (time_based, queue_based, dqn_step, dqn_global, nerl_step, nerl_global)")
        
        # 並行執行設置
        parallel_config = self.config_manager.ask_parallel_execution()
        config['parallel'] = parallel_config
        
        # 資源負載預估（在用戶確認並行設置後顯示）
        if workflow_type == 'training':
            self.config_manager.calculate_and_display_process_load(config)
        
        # NetLogo 視覺化設置
        use_netlogo = self.config_manager.ask_netlogo_mode()
        config['netlogo'] = use_netlogo
        
        # 日誌級別設置
        log_level = self.config_manager.ask_log_level()
        config['log_level'] = log_level
        print(f"{Colors.CYAN}[DEBUG] 設置的日誌級別: {log_level}{Colors.END}")
        
        # 預估時間
        estimated_time = self._estimate_execution_time(config)
        print(f"\n{Colors.BOLD}⏱️  預估執行時間: {estimated_time}{Colors.END}")
        
        choice = input(f"\n{Colors.CYAN}確認開始執行? [Y/n]: {Colors.END}").strip().lower()
        return choice not in ['n', 'no', '否']
    
    def _estimate_execution_time(self, config: Dict) -> str:
        """預估執行時間"""
        total_minutes = 0
        
        if 'training' in config:
            # 訓練時間估算
            dqn_time = config['training'].get('dqn_ticks', 0) / 1000 * 2  # 每1000 ticks約2分鐘
            nerl_time = config['training'].get('nerl_generations', 0) * 3  # 每代約3分鐘
            training_time = (dqn_time * 2 + nerl_time * 2)  # 4個模型
            
            if config.get('parallel', {}).get('enabled', True):
                training_time *= 0.4  # 並行執行節省時間
            
            total_minutes += training_time
        
        if 'evaluation' in config:
            # 評估時間估算
            eval_single = config['evaluation'].get('ticks', 0) / 1000 * 3  # 每1000 ticks約3分鐘
            eval_count = config['evaluation'].get('repeats', 1)
            evaluation_time = eval_single * eval_count
            
            if config.get('parallel', {}).get('enabled', True):
                evaluation_time *= 0.5  # 並行執行節省時間
            
            total_minutes += evaluation_time
        
        if 'analysis' in config or config.get('auto_analysis', True):
            total_minutes += 10  # 圖表生成約10分鐘
        
        if total_minutes < 60:
            return f"約 {total_minutes:.0f} 分鐘"
        else:
            hours = total_minutes / 60
            return f"約 {hours:.1f} 小時"
    
    def run_training_workflow(self):
        """執行訓練工作流程"""
        preset_name = self.show_preset_menu('training')
        if not preset_name:
            return
        
        if preset_name == "custom":
            # 自定義訓練配置
            custom_config = self.config_manager.interactive_training_config()
            preset_display = "自定義配置"
            
            # 將舊格式轉換為新格式
            training_config = {}
            if 'configs' in custom_config:
                # 從 configs 字典中提取任務
                for task_name, task_config in custom_config['configs'].items():
                    training_config[task_name] = task_config
            else:
                # 如果沒有 configs，說明是直接格式，直接使用
                training_config = custom_config
        else:
            # 使用預設配置
            preset = get_preset(preset_name)
            preset_display = preset['name']
            
            # 檢查是否為新格式（論文級實驗）
            if any('_' in task_name for task_name in preset['training'].keys()):
                # 新格式：直接使用預設中定義的任務
                training_config = preset['training'].copy()
            else:
                # 舊格式：基於 reward_modes 生成配置
                training_config = {
                    'agents': ['dqn', 'nerl'],
                    'reward_modes': preset['training']['reward_modes'],
                    'configs': {
                        'dqn_step': self.config_manager.get_training_config('dqn', 'step', **preset['training']),
                        'dqn_global': self.config_manager.get_training_config('dqn', 'global', **preset['training']),
                        'nerl_step': self.config_manager.get_training_config('nerl', 'step', **preset['training']),
                        'nerl_global': self.config_manager.get_training_config('nerl', 'global', **preset['training'])
                    }
                }
        
        # 構建完整配置
        config = {'training': training_config}
        
        # 複製其他預設配置信息（如果是預設配置）
        if preset_name != "custom":
            for key in ['evaluation', 'charts', 'parallel', 'total_eval_steps']:
                if key in preset:
                    config[key] = preset[key]
        
        if self.confirm_execution('training', preset_display, config):
            parallel = config.get('parallel', {}).get('enabled', True)
            print(f"[DEBUG] 初始並行設置: {parallel}")
            # 將 use_new_windows 設置傳遞到每個訓練配置中
            use_new_windows = config.get('parallel', {}).get('use_new_windows', True)
            print(f"[DEBUG] 新視窗模式: {use_new_windows}")
            
            # 移除新視窗模式下的並行執行警告
            # 讓用戶自行決定是否使用並行執行
            
            print(f"[DEBUG] 最終並行設置: {parallel}")
            
            # 修正：確保頂層的日誌級別被傳遞到每個子配置中
            log_level = config.get('log_level', 'INFO')
            print(f"{Colors.CYAN}[DEBUG] 傳遞給子配置的日誌級別: {log_level}{Colors.END}")
            
            # 檢查配置格式並相應地設置參數
            if 'configs' in training_config:
                # 舊格式
                for key in training_config['configs'].keys():
                    training_config['configs'][key]['use_new_windows'] = use_new_windows
                    training_config['configs'][key]['use_netlogo'] = config.get('netlogo', False)
                    training_config['configs'][key]['log_level'] = log_level
                    print(f"{Colors.CYAN}[DEBUG] {key} 的日誌級別設置為: {training_config['configs'][key]['log_level']}{Colors.END}")
            else:
                # 新格式：直接設置任務配置
                for task_name, task_config in training_config.items():
                    if isinstance(task_config, dict):
                        task_config['use_new_windows'] = use_new_windows
                        task_config['use_netlogo'] = config.get('netlogo', False)
                        task_config['log_level'] = log_level
                        print(f"{Colors.CYAN}[DEBUG] {task_name} 的日誌級別設置為: {task_config['log_level']}{Colors.END}")

            # 構建並行配置字典
            parallel_config = config.get('parallel', {})
            parallel_config.update({
                'enabled': parallel,
                'use_new_windows': use_new_windows,
                'log_level': log_level
            })
            
            results = self.workflow_runner.run_training_workflow(training_config, parallel_config)
            self._show_workflow_results('training', results)
    
    def run_evaluation_workflow(self):
        """執行評估工作流程"""
        preset_name = self.show_preset_menu('evaluation')
        if not preset_name:
            return
        
        if preset_name == "custom":
            # 自定義評估配置
            evaluation_config = self.config_manager.interactive_evaluation_config()
            preset_display = "自定義配置"
        else:
            # 使用預設配置
            preset = get_preset(preset_name)
            evaluation_config = self.config_manager.get_evaluation_config(**preset['evaluation'])
            preset_display = preset['name']
        
        config = {'evaluation': evaluation_config}
        
        if self.confirm_execution('evaluation', preset_display, config):
            parallel = config.get('parallel', {}).get('enabled', True)
            # 將 use_new_windows 設置傳遞到評估配置中
            use_new_windows = config.get('parallel', {}).get('use_new_windows', True)
            
            # 如果使用新視窗，建議關閉並行執行
            if use_new_windows and parallel:
                print(f"\n{Colors.WARNING}⚠️  注意：新視窗模式下建議關閉並行執行{Colors.END}")
                print("因為每個評估都會等待完成，並行執行無法發揮效果")
                choice = input(f"\n{Colors.CYAN}是否關閉並行執行？[Y/n]: {Colors.END}").strip().lower()
                if choice != 'n':
                    parallel = False
                    print(f"{Colors.CYAN}已關閉並行執行{Colors.END}")
                    
            evaluation_config['use_new_windows'] = use_new_windows
            # 傳遞 NetLogo 設置
            evaluation_config['use_netlogo'] = config.get('netlogo', False)
            # 傳遞日誌級別設置
            evaluation_config['log_level'] = config.get('log_level', 'INFO')
            results = self.workflow_runner.run_evaluation_workflow(evaluation_config, parallel)
            self._show_workflow_results('evaluation', results)
    
    def run_analysis_workflow(self):
        """執行分析工作流程"""
        print(f"\n{Colors.YELLOW}{Colors.BOLD}{'='*50}")
        print("              數據分析與圖表")
        print(f"{'='*50}{Colors.END}")
        
        # 檢查是否有評估結果
        results_dir = self.workflow_runner.results_dir / "evaluations"
        eval_dirs = list(results_dir.glob("EVAL_*")) if results_dir.exists() else []
        
        if not eval_dirs:
            print(f"\n{Colors.WARNING}❌ 沒有找到評估結果{Colors.END}")
            print("請先執行 [2] 效能驗證 或 [4] 完整實驗流程")
            input(f"\n{Colors.CYAN}按 Enter 繼續...{Colors.END}")
            return
        
        print(f"\n{Colors.WHITE}找到以下實驗結果:{Colors.END}\n")
        
        # 顯示可用結果
        choices = []
        for i, eval_dir in enumerate(eval_dirs[-5:], 1):  # 顯示最近5個結果
            choices.append(str(i))
            mod_time = datetime.fromtimestamp(eval_dir.stat().st_mtime)
            print(f"{Colors.WHITE}[{i}] {eval_dir.name}{Colors.END}")
            print(f"    生成時間: {mod_time.strftime('%Y-%m-%d %H:%M')}")
            print()
        
        print(f"{Colors.WHITE}[{len(choices) + 1}] 📊 為所有結果生成圖表{Colors.END}")
        choices.append(str(len(choices) + 1))
        
        print(f"{Colors.WHITE}[{len(choices) + 1}] 🔧 自定義圖表設置{Colors.END}")
        choices.append(str(len(choices) + 1))
        
        print(f"\n{Colors.WHITE}[0] 返回主選單{Colors.END}")
        choices.append("0")
        
        choice = self.get_user_choice("選擇操作", choices)
        
        if choice == "0":
            return
        elif choice == str(len(eval_dirs) + 1):
            # 為所有結果生成圖表
            chart_config = {}
            results = self.workflow_runner.run_analysis_workflow(chart_config)
        elif choice == str(len(eval_dirs) + 2):
            # 自定義圖表設置
            chart_config = self.config_manager.interactive_chart_config()
            results = self.workflow_runner.run_analysis_workflow(chart_config)
        else:
            # 單個結果分析
            selected_idx = int(choice) - 1
            if 0 <= selected_idx < len(eval_dirs):
                selected_dir = eval_dirs[selected_idx].name
                print(f"\n{Colors.CYAN}分析選定的實驗: {selected_dir}{Colors.END}")
                results = self.workflow_runner.run_analysis_workflow({}, selected_dir)
            else:
                print(f"{Colors.RED}無效的選擇{Colors.END}")
                return
        
        self._show_workflow_results('analysis', results)
    
    def run_complete_workflow(self):
        """執行完整實驗流程"""
        preset_name = self.show_preset_menu('complete')
        if not preset_name:
            return
        
        if preset_name == "custom":
            print(f"\n{Colors.CYAN}自定義完整實驗配置...{Colors.END}")
            
            # 逐步配置各階段
            print(f"\n{Colors.WHITE}步驟1: 配置訓練參數{Colors.END}")
            training_config = self.config_manager.interactive_training_config()
            
            print(f"\n{Colors.WHITE}步驟2: 配置評估參數{Colors.END}")
            evaluation_config = self.config_manager.interactive_evaluation_config()
            
            print(f"\n{Colors.WHITE}步驟3: 配置圖表參數{Colors.END}")
            chart_config = self.config_manager.interactive_chart_config()
            
            config = {
                'training': training_config,
                'evaluation': evaluation_config,
                'analysis': chart_config,
                'auto_analysis': True
            }
            preset_display = "自定義完整配置"
        else:
            # 使用預設配置
            preset = get_preset(preset_name)
            
            # 構建完整配置
            training_config = {
                'agents': ['dqn', 'nerl'],
                'reward_modes': preset['training']['reward_modes'],
                'configs': {
                    'dqn_step': self.config_manager.get_training_config('dqn', 'step', **preset['training']),
                    'dqn_global': self.config_manager.get_training_config('dqn', 'global', **preset['training']),
                    'nerl_step': self.config_manager.get_training_config('nerl', 'step', **preset['training']),
                    'nerl_global': self.config_manager.get_training_config('nerl', 'global', **preset['training'])
                }
            }
            
            evaluation_config = self.config_manager.get_evaluation_config(**preset['evaluation'])
            chart_config = self.config_manager.get_chart_config(**preset.get('charts', {}))
            
            config = {
                'training': training_config,
                'evaluation': evaluation_config,
                'analysis': chart_config,
                'auto_analysis': True
            }
            preset_display = preset['name']
        
        if self.confirm_execution('complete', preset_display, config):
            parallel = config.get('parallel', {}).get('enabled', True)
            results = self.workflow_runner.run_complete_workflow(config, parallel)
            self._show_complete_results(results)
    
    def run_custom_config(self):
        """執行自定義參數設置"""
        print(f"\n{Colors.YELLOW}{Colors.BOLD}{'='*50}")
        print("              自定義參數設置")
        print(f"{'='*50}{Colors.END}")
        
        print(f"\n{Colors.WHITE}[1] 🤖 自定義訓練參數{Colors.END}")
        print(f"    - DQN訓練時長、NERL代數、族群大小等")
        
        print(f"\n{Colors.WHITE}[2] 📊 自定義評估參數{Colors.END}")
        print(f"    - 評估時長、重複次數、隨機種子等")
        
        print(f"\n{Colors.WHITE}[3] 📈 自定義圖表參數{Colors.END}")
        print(f"    - 圖表類型、解析度、格式等")
        
        print(f"\n{Colors.WHITE}[4] ⚡ 並行執行設置{Colors.END}")
        print(f"    - 是否啟用多線程、最大並行數等")
        
        print(f"\n{Colors.WHITE}[5] 💾 載入/保存配置{Colors.END}")
        print(f"    - 保存當前設置或載入已保存的配置")
        
        print(f"\n{Colors.WHITE}[0] 返回主選單{Colors.END}")
        
        choice = self.get_user_choice("選擇操作", ["1", "2", "3", "4", "5", "0"])
        
        if choice == "0":
            return
        elif choice == "1":
            self.config_manager.interactive_training_config()
        elif choice == "2":
            self.config_manager.interactive_evaluation_config()
        elif choice == "3":
            self.config_manager.interactive_chart_config()
        elif choice == "4":
            self.config_manager.ask_parallel_execution()
        elif choice == "5":
            self.config_manager.interactive_config_management()
        
        input(f"\n{Colors.CYAN}按 Enter 繼續...{Colors.END}")
    
    def _show_workflow_results(self, workflow_type: str, results: Dict):
        """顯示工作流程結果"""
        title_map = {
            'training': '訓練結果',
            'evaluation': '評估結果',
            'analysis': '分析結果'
        }
        
        print(f"\n{Colors.GREEN}{Colors.BOLD}{'='*50}")
        print(f"              {title_map.get(workflow_type, '執行結果')}")
        print(f"{'='*50}{Colors.END}")
        
        if not results:
            print(f"\n{Colors.WARNING}❌ 沒有執行結果{Colors.END}")
            input(f"\n{Colors.CYAN}按 Enter 繼續...{Colors.END}")
            return
        
        successful = sum(1 for success in results.values() if success)
        total = len(results)
        success_rate = (successful / total) * 100 if total > 0 else 0
        
        color = Colors.GREEN if success_rate >= 80 else Colors.YELLOW if success_rate >= 50 else Colors.RED
        
        print(f"\n{Colors.WHITE}執行統計:{Colors.END}")
        print(f"  {color}成功: {successful}/{total} ({success_rate:.1f}%){Colors.END}")
        
        print(f"\n{Colors.WHITE}詳細結果:{Colors.END}")
        for task_name, success in results.items():
            status_icon = "✅" if success else "❌"
            status_color = Colors.GREEN if success else Colors.RED
            print(f"  {status_color}{status_icon} {task_name}{Colors.END}")
        
        input(f"\n{Colors.CYAN}按 Enter 繼續...{Colors.END}")
    
    def _show_complete_results(self, results: Dict):
        """顯示完整實驗結果"""
        print(f"\n{Colors.GREEN}{Colors.BOLD}{'='*60}")
        print("                  完整實驗結果")
        print(f"{'='*60}{Colors.END}")
        
        stage_names = {
            'training': '🤖 模型訓練',
            'evaluation': '📊 效能評估',
            'analysis': '📈 數據分析'
        }
        
        overall_stats = {'total': 0, 'successful': 0}
        
        for stage, stage_results in results.items():
            if stage_results:
                successful = sum(1 for success in stage_results.values() if success)
                total = len(stage_results)
                success_rate = (successful / total) * 100 if total > 0 else 0
                
                overall_stats['total'] += total
                overall_stats['successful'] += successful
                
                color = Colors.GREEN if success_rate >= 80 else Colors.YELLOW if success_rate >= 50 else Colors.RED
                stage_name = stage_names.get(stage, stage)
                
                print(f"\n{Colors.WHITE}{stage_name}:{Colors.END}")
                print(f"  {color}成功率: {successful}/{total} ({success_rate:.1f}%){Colors.END}")
        
        # 整體成功率
        if overall_stats['total'] > 0:
            overall_rate = (overall_stats['successful'] / overall_stats['total']) * 100
            overall_color = Colors.GREEN if overall_rate >= 80 else Colors.YELLOW if overall_rate >= 50 else Colors.RED
            
            print(f"\n{Colors.BOLD}📊 整體成功率: {overall_color}{overall_stats['successful']}/{overall_stats['total']} ({overall_rate:.1f}%){Colors.END}")
        
        # 顯示結果位置
        print(f"\n{Colors.WHITE}結果文件位置:{Colors.END}")
        if 'evaluation' in results:
            eval_dirs = list(self.workflow_runner.results_dir.glob("evaluations/EVAL_*"))
            if eval_dirs:
                latest_eval = max(eval_dirs, key=lambda x: x.stat().st_mtime)
                print(f"  📊 最新評估結果: {latest_eval}")
        
        if 'analysis' in results:
            print(f"  📈 圖表文件: result/evaluations/*/charts/")
        
        # 執行統計
        stats = self.workflow_runner.get_execution_stats()
        if stats.get('start_time') and stats.get('end_time'):
            total_time = (stats['end_time'] - stats['start_time']).total_seconds() / 60
            print(f"  ⏱️  總耗時: {total_time:.1f} 分鐘")
        
        print(f"\n{Colors.CYAN}🎉 完整實驗流程執行完成！{Colors.END}")
        input(f"\n{Colors.CYAN}按 Enter 繼續...{Colors.END}")
    
    def run(self):
        """運行主程序"""
        try:
            self.show_banner()
            
            while True:
                self.show_main_menu()
                choice = self.get_user_choice()
                
                if choice == "1":
                    self.run_training_workflow()
                
                elif choice == "2":
                    self.run_evaluation_workflow()
                
                elif choice == "3":
                    self.run_analysis_workflow()
                
                elif choice == "4":
                    self.run_complete_workflow()
                
                elif choice == "5":
                    self.run_custom_config()
                
                elif choice == "0":
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
    # 檢查Python版本
    if sys.version_info < (3, 6):
        print("❌ 需要 Python 3.6 或更高版本")
        sys.exit(1)
    
    # 檢查是否在正確的目錄
    expected_files = ['train.py', 'evaluate.py', 'visualization_generator.py']
    missing_files = [f for f in expected_files if not Path(f).exists()]
    
    if missing_files:
        print(f"❌ 找不到必要的文件: {', '.join(missing_files)}")
        print("請確保在正確的專案目錄中運行此腳本")
        sys.exit(1)
    
    # 啟動管理器
    manager = SimpleExperimentManager()
    manager.run()

if __name__ == "__main__":
    main()
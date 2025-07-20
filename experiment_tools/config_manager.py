"""
配置管理器
==========

處理自定義參數設置、配置保存和載入
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from .presets import get_preset, get_custom_template, AVAILABLE_CONTROLLERS

class Colors:
    """終端顏色常數"""
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    WARNING = '\033[33m'
    END = '\033[0m'

class ConfigManager:
    """實驗配置管理器"""
    
    def __init__(self, config_dir: str = "experiment_configs"):
        """
        初始化配置管理器
        
        Args:
            config_dir: 配置文件保存目錄
        """
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        self.current_config = {}
        
    def load_preset_config(self, preset_name: str) -> Dict:
        """
        載入預設配置
        
        Args:
            preset_name: 預設配置名稱
            
        Returns:
            dict: 配置字典
        """
        self.current_config = get_preset(preset_name)
        return self.current_config.copy()
    
    def get_training_config(self, agent: str, reward_mode: str, **kwargs) -> Dict:
        """
        構建訓練配置
        
        Args:
            agent: AI代理類型 ('dqn' 或 'nerl')
            reward_mode: 獎勵模式 ('step' 或 'global')
            **kwargs: 其他自定義參數
            
        Returns:
            dict: 訓練配置
        """
        # 獲取基礎範本
        template = get_custom_template("training", agent)
        
        # 設置基本參數
        config = template.copy()
        config["agent"] = agent
        config["reward_mode"] = reward_mode
        
        # 應用自定義參數
        for key, value in kwargs.items():
            if key in config:
                config[key] = value
            # 處理參數名稱差異：預設配置使用 dqn_ticks，但模板使用 training_ticks
            elif agent == "dqn" and key == "dqn_ticks" and "training_ticks" in config:
                config["training_ticks"] = value
            # 處理 NERL 參數名稱差異
            elif agent == "nerl":
                if key == "nerl_generations" and "generations" in config:
                    config["generations"] = value
                elif key == "nerl_population" and "population" in config:
                    config["population"] = value
                elif key == "nerl_eval_ticks" and "eval_ticks" in config:
                    config["eval_ticks"] = value
        
        return config
    
    def get_evaluation_config(self, **kwargs) -> Dict:
        """
        構建評估配置
        
        Args:
            **kwargs: 自定義評估參數
            
        Returns:
            dict: 評估配置
        """
        template = get_custom_template("evaluation")
        config = template.copy()
        
        # 應用自定義參數
        for key, value in kwargs.items():
            if key in config:
                config[key] = value
        
        return config
    
    def get_chart_config(self, **kwargs) -> Dict:
        """
        構建圖表配置
        
        Args:
            **kwargs: 自定義圖表參數
            
        Returns:
            dict: 圖表配置
        """
        template = get_custom_template("charts")
        config = template.copy()
        
        # 應用自定義參數
        for key, value in kwargs.items():
            if key in config:
                config[key] = value
        
        return config
    
    def interactive_training_config(self) -> Dict:
        """
        互動式訓練配置設置
        
        Returns:
            dict: 配置字典
        """
        print("\n" + "="*50)
        print("🤖 自定義訓練參數設置")
        print("="*50)
        
        configs = {}
        
        # 選擇要訓練的代理
        print("\n選擇要訓練的AI代理：")
        print("[1] DQN only")
        print("[2] NERL only") 
        print("[3] Both DQN and NERL [預設]")
        
        agent_choice = input("請選擇 [1-3]: ").strip() or "3"
        
        if agent_choice == "1":
            agents = ["dqn"]
        elif agent_choice == "2":
            agents = ["nerl"]
        else:
            agents = ["dqn", "nerl"]
        
        # 選擇獎勵模式
        print("\n選擇獎勵模式：")
        print("[1] Step mode only (即時獎勵)")
        print("[2] Global mode only (全局獎勵)")
        print("[3] Both modes [預設]")
        
        reward_choice = input("請選擇 [1-3]: ").strip() or "3"
        
        if reward_choice == "1":
            reward_modes = ["step"]
        elif reward_choice == "2":
            reward_modes = ["global"]
        else:
            reward_modes = ["step", "global"]
        
        # 為每個代理和模式組合設置參數
        for agent in agents:
            for reward_mode in reward_modes:
                config_key = f"{agent}_{reward_mode}"
                print(f"\n--- {agent.upper()} {reward_mode.upper()} 模式參數 ---")
                
                if agent == "dqn":
                    configs[config_key] = self._get_dqn_config(reward_mode)
                else:  # nerl
                    configs[config_key] = self._get_nerl_config(reward_mode)
        
        return {
            "agents": agents,
            "reward_modes": reward_modes,
            "configs": configs
        }
    
    def _get_dqn_config(self, reward_mode: str) -> Dict:
        """獲取DQN配置"""
        template = get_custom_template("training", "dqn")
        
        ticks = input(f"訓練時長 (ticks) [預設: {template['training_ticks']}]: ").strip()
        if ticks.isdigit():
            template['training_ticks'] = int(ticks)
        
        template['reward_mode'] = reward_mode
        return template
    
    def _get_nerl_config(self, reward_mode: str) -> Dict:
        """獲取NERL配置"""
        template = get_custom_template("training", "nerl")
        
        generations = input(f"進化代數 [預設: {template['generations']}]: ").strip()
        if generations.isdigit():
            template['generations'] = int(generations)
        
        population = input(f"族群大小 [預設: {template['population']}]: ").strip()
        if population.isdigit():
            template['population'] = int(population)
        
        eval_ticks = input(f"個體評估時長 [預設: {template['eval_ticks']}]: ").strip()
        if eval_ticks.isdigit():
            template['eval_ticks'] = int(eval_ticks)
        
        template['reward_mode'] = reward_mode
        return template
    
    def interactive_evaluation_config(self) -> Dict:
        """
        互動式評估配置設置
        
        Returns:
            dict: 評估配置
        """
        print("\n" + "="*50)
        print("📊 自定義評估參數設置")
        print("="*50)
        
        template = get_custom_template("evaluation")
        
        # 選擇要評估的控制器
        print("\n選擇要評估的控制器：")
        print("[1] 自動檢測所有可用控制器 [預設]")
        print("[2] 只評估傳統控制器")
        print("[3] 只評估AI控制器")
        print("[4] 自定義選擇")
        
        controller_choice = input("請選擇 [1-4]: ").strip() or "1"
        
        if controller_choice == "2":
            template['controllers'] = AVAILABLE_CONTROLLERS['traditional']
        elif controller_choice == "3":
            template['controllers'] = AVAILABLE_CONTROLLERS['ai']
        elif controller_choice == "4":
            template['controllers'] = self._select_controllers()
        else:
            template['controllers'] = "auto"
        
        # 評估參數
        print("\n評估參數設置：")
        
        ticks = input(f"評估時長 (ticks) [預設: {template['ticks']}]: ").strip()
        if ticks.isdigit():
            template['ticks'] = int(ticks)
        
        repeats = input(f"重複次數 [預設: {template['repeats']}]: ").strip()
        if repeats.isdigit():
            template['repeats'] = int(repeats)
            # 更新隨機種子
            base_seeds = [42, 123, 789, 456, 999, 111, 222, 333, 444, 555]
            template['seeds'] = base_seeds[:int(repeats)]
        
        description = input(f"實驗描述 [預設: {template['description']}]: ").strip()
        if description:
            template['description'] = description
        
        return template
    
    def _select_controllers(self) -> List[str]:
        """選擇控制器"""
        all_controllers = AVAILABLE_CONTROLLERS['all']
        print("\n可用控制器：")
        
        for i, controller in enumerate(all_controllers, 1):
            print(f"[{i}] {controller}")
        
        selected = input("輸入要評估的控制器編號（用逗號分隔，如: 1,3,5）: ").strip()
        
        try:
            indices = [int(x.strip()) - 1 for x in selected.split(",")]
            return [all_controllers[i] for i in indices if 0 <= i < len(all_controllers)]
        except:
            print("輸入格式錯誤，使用自動檢測")
            return "auto"
    
    def interactive_chart_config(self) -> Dict:
        """
        互動式圖表配置設置
        
        Returns:
            dict: 圖表配置
        """
        print("\n" + "="*50)
        print("📈 自定義圖表參數設置")
        print("="*50)
        
        template = get_custom_template("charts")
        
        # 圖表類型
        print("\n選擇圖表類型：")
        print("[1] 所有圖表 [預設]")
        print("[2] 基礎圖表")
        print("[3] 自定義選擇")
        
        chart_choice = input("請選擇 [1-3]: ").strip() or "1"
        
        if chart_choice == "2":
            template['types'] = 'basic'
        elif chart_choice == "3":
            print("可用圖表類型：performance_comparison, algorithm_comparison, reward_comparison, performance_rankings, comprehensive_heatmap")
            custom_types = input("輸入要生成的圖表類型（用逗號分隔）: ").strip()
            if custom_types:
                template['types'] = [t.strip() for t in custom_types.split(",")]
        
        # 圖表質量
        dpi = input(f"圖表解析度 (DPI) [預設: {template['dpi']}]: ").strip()
        if dpi.isdigit():
            template['dpi'] = int(dpi)
        
        # 圖表格式
        print(f"\n圖表格式 [當前: {template['format']}]：")
        print("[1] PNG [預設]")
        print("[2] PDF")
        print("[3] SVG")
        
        format_choice = input("請選擇 [1-3]: ").strip()
        format_map = {"1": "png", "2": "pdf", "3": "svg"}
        if format_choice in format_map:
            template['format'] = format_map[format_choice]
        
        return template
    
    def ask_parallel_execution(self) -> Dict:
        """
        詢問是否啟用並行執行
        
        Returns:
            dict: 並行執行配置
        """
        print("\n" + "="*50)
        print("⚡ 並行執行設置")
        print("="*50)
        
        print("\n是否啟用多線程並行執行？")
        print("\n✅ 優點：")
        print("- 顯著縮短實驗時間 (節省40-60%)")
        print("- 同時訓練/評估多個模型")
        print("\n⚠️  注意：")
        print("- 需要較多CPU和記憶體資源")
        print("- 可能影響其他程式運行")
        
        choice = input("\n[Y] 是，啟用並行執行 [推薦]\n[n] 否，順序執行\n\n請選擇 [Y/n]: ").strip().lower()
        
        parallel_config = {
            "enabled": choice not in ['n', 'no', '否']
        }
        
        if parallel_config["enabled"]:
            # 自動檢查並修復並行環境
            try:
                from experiment_tools.auto_parallel_fix import get_fixer
                fixer = get_fixer()
                if not fixer.check_and_fix():
                    print("\n❌ 並行環境設置失敗，將使用順序執行")
                    parallel_config["enabled"] = False
                    return parallel_config
            except ImportError:
                print("\n⚠️  無法載入並行修復模組，繼續執行...")
            
            # --- 【雙層並行控制：外層並行設置】 ---
            print("\n" + "="*50)
            print("🔄 外層並行設置（任務級並行）")
            print("="*50)
            print("外層並行控制同時執行多少個獨立的訓練任務")
            print("例如：同時啟動 dqn_step, nerl_step_a, nerl_global_b 等任務")
            print("建議值：2-4（取決於您的CPU核心數和記憶體）")
            
            max_workers = input("\n最大並行訓練任務數 [預設: 2]: ").strip()
            if max_workers.isdigit():
                parallel_config["max_workers"] = int(max_workers)
            else:
                parallel_config["max_workers"] = 2
            
            # --- 【雙層並行控制：內層並行設置】 ---
            print("\n" + "="*50)
            print("🧠 內層並行設置（NERL內部並行）")
            print("="*50)
            print("內層並行控制每個NERL任務內部使用多少個進程來評估個體")
            print("這只影響NERL任務，DQN任務不受影響")
            print("建議值：CPU核心數的一半（例如8核CPU設置4）")
            
            nerl_workers = input("\n每個NERL任務的內部並行進程數 [預設: 4]: ").strip()
            if nerl_workers.isdigit():
                parallel_config["nerl_internal_workers"] = int(nerl_workers)
            else:
                parallel_config["nerl_internal_workers"] = 4
            
            # 新增：詢問分批啟動等待設置
            print("\n" + "="*50)
            print("⏱️  分批啟動等待設置")
            print("="*50)
            print("\n每批任務之間的等待策略：")
            print("- 30 秒：短暫等待（快速啟動）")
            print("- 60 秒：標準等待（推薦，確保穩定啟動）")
            print("- 120 秒：較長等待（適合資源有限的系統）")
            print("\n這個時間用來等待前一批任務完全啟動並穩定運行")
            
            startup_wait = input("\n每批任務啟動等待時間（秒）[預設: 60]: ").strip()
            if startup_wait.isdigit():
                parallel_config["startup_wait"] = int(startup_wait)
            else:
                parallel_config["startup_wait"] = 60
        
        # 新增：詢問是否在新視窗顯示
        print("\n" + "="*50)
        print("🖼️  執行顯示設置")
        print("="*50)
        print("\n是否在獨立視窗中顯示每個訓練/評估過程？")
        print("\n✅ 優點：")
        print("- 可以即時看到訓練進度和錯誤訊息")
        print("- 每個任務有獨立的輸出視窗")
        print("\n⚠️  注意：")
        print("- 會開啟多個CMD視窗")
        print("- 需要手動關閉完成的視窗")
        
        window_choice = input("\n[Y] 是，使用獨立視窗 [推薦]\n[n] 否，在背景執行\n\n請選擇 [Y/n]: ").strip().lower()
        parallel_config["use_new_windows"] = window_choice not in ['n', 'no', '否']
        
        return parallel_config
    
    def ask_netlogo_mode(self) -> bool:
        """
        詢問是否啟動 NetLogo 視覺化界面
        
        Returns:
            bool: 是否啟動 NetLogo
        """
        print("\n" + "="*50)
        print("🔍 NetLogo 視覺化設置")
        print("="*50)
        
        print("\n是否啟動 NetLogo GUI 視覺化界面？")
        print("\n✅ 啟動的好處：")
        print("- 可以即時觀察機器人運作狀況")
        print("- 方便調試機器人卡住或鎖死問題")
        print("- 視覺化倉儲系統運作流程")
        print("\n⚠️  注意事項：")
        print("- 需要安裝 NetLogo 軟體")
        print("- 會開啟額外的 GUI 視窗")
        print("- 可能會降低訓練/評估速度")
        
        choice = input("\n[y] 是，啟動 NetLogo\n[N] 否，不需要視覺化 [預設]\n\n請選擇 [y/N]: ").strip().lower()
        
        return choice in ['y', 'yes', '是']
    
    def ask_log_level(self) -> str:
        """
        詢問日誌級別設置
        
        Returns:
            str: 日誌級別 ('DEBUG', 'INFO', 'WARNING', 'ERROR')
        """
        print("\n" + "="*50)
        print("📝 日誌級別設置")
        print("="*50)
        
        print("\n選擇日誌輸出級別：")
        print("\n[1] 🔇 WARNING - 最少輸出（最快）")
        print("    - 只顯示警告和錯誤")
        print("    - 訓練速度最快")
        print("\n[2] 📊 INFO - 標準輸出 [預設]")
        print("    - 顯示訓練進度和重要事件")
        print("    - 平衡速度和資訊量")
        print("\n[3] 🔍 DEBUG - 詳細輸出")
        print("    - 顯示所有調試資訊")
        print("    - 訓練速度較慢")
        
        choice = input("\n請選擇 [1-3]: ").strip() or "2"
        
        level_map = {
            "1": "WARNING",
            "2": "INFO",
            "3": "DEBUG"
        }
        
        return level_map.get(choice, "INFO")
    
    def calculate_and_display_process_load(self, config: Dict) -> int:
        """
        計算並顯示預計的雙層並行進程負載
        
        Args:
            config: 完整的實驗配置
            
        Returns:
            int: 預計的總進程數
        """
        nerl_tasks = 0
        dqn_tasks = 0
        
        # 檢查是否有新格式的配置（論文級實驗）
        if 'training' in config and isinstance(config['training'], dict):
            training_config = config['training']
            
            # 處理新格式：直接定義每個任務的參數
            if any('nerl_' in task_name for task_name in training_config.keys()):
                for task_name, params in training_config.items():
                    if 'nerl' in task_name:
                        nerl_tasks += 1
                    elif 'dqn' in task_name:
                        dqn_tasks += 1
            else:
                # 處理舊格式：基於 reward_modes 生成任務
                reward_modes = training_config.get('reward_modes', ['step', 'global'])
                agents = []
                
                # 檢查哪些代理將被訓練
                if 'dqn_ticks' in training_config:
                    agents.append('dqn')
                if 'nerl_generations' in training_config:
                    agents.append('nerl')
                
                for agent in agents:
                    for reward_mode in reward_modes:
                        if agent == 'nerl':
                            nerl_tasks += 1
                        elif agent == 'dqn':
                            dqn_tasks += 1

        print(f"\n{Colors.YELLOW}{Colors.BOLD}--- 雙層並行資源負載預估 ---{Colors.END}")
        print(f"{Colors.WHITE}本次實驗將啟動 {dqn_tasks} 個DQN訓練任務和 {nerl_tasks} 個NERL訓練任務。{Colors.END}")

        # 檢查並行執行策略
        parallel_config = config.get('parallel', {})
        
        if parallel_config.get('enabled', True):
            # --- 【雙層並行負載計算】 ---
            max_workers = parallel_config.get('max_workers', 2)
            nerl_internal_workers = parallel_config.get('nerl_internal_workers', 4)
            
            print(f"\n{Colors.BLUE}外層並行設置：{Colors.END}")
            print(f"  最大並行任務數: {max_workers}")
            print(f"  任務調度策略: 先啟動最多 {max_workers} 個任務，完成後啟動下一批")
            
            print(f"\n{Colors.BLUE}內層並行設置：{Colors.END}")
            print(f"  每個NERL任務的內部並行進程數: {nerl_internal_workers}")
            print(f"  DQN任務不使用內部並行")
            
            # 計算不同情況下的進程負載
            print(f"\n{Colors.CYAN}進程負載情況分析：{Colors.END}")
            
            # 情況1：如果同時運行的都是DQN任務
            if dqn_tasks > 0:
                max_dqn_concurrent = min(max_workers, dqn_tasks)
                print(f"  當同時運行 {max_dqn_concurrent} 個DQN任務時: {max_dqn_concurrent} 個進程")
            
            # 情況2：如果同時運行的都是NERL任務  
            if nerl_tasks > 0:
                max_nerl_concurrent = min(max_workers, nerl_tasks)
                nerl_total_processes = max_nerl_concurrent * (1 + nerl_internal_workers)
                print(f"  當同時運行 {max_nerl_concurrent} 個NERL任務時: {nerl_total_processes} 個進程")
                print(f"    = {max_nerl_concurrent} 個主進程 + {max_nerl_concurrent * nerl_internal_workers} 個工作進程")
            
            # 情況3：混合情況下的最大負載
            if nerl_tasks > 0 and dqn_tasks > 0:
                # 假設最壞情況：同時運行的都是NERL任務
                worst_case_processes = min(max_workers, nerl_tasks) * (1 + nerl_internal_workers)
                print(f"  最大可能進程數（全NERL情況）: {worst_case_processes} 個進程")
            
            # 硬體資源檢查（可選功能）
            try:
                import psutil
                cpu_count = psutil.cpu_count()
                memory_gb = round(psutil.virtual_memory().total / (1024**3))
                
                print(f"\n{Colors.WHITE}硬體資源參考：{Colors.END}")
                print(f"  CPU核心數: {cpu_count}")
                print(f"  記憶體: {memory_gb} GB")
                
                if nerl_tasks > 0:
                    max_possible_processes = min(max_workers, nerl_tasks) * (1 + nerl_internal_workers)
                    if max_possible_processes > cpu_count:
                        print(f"\n{Colors.YELLOW}⚠️  建議調整：{Colors.END}")
                        print(f"  最大可能進程數 ({max_possible_processes}) 超過CPU核心數 ({cpu_count})")
                        recommended_internal = max(1, cpu_count // max_workers - 1)
                        print(f"  建議將NERL內部並行數調整為: {recommended_internal}")
                    else:
                        print(f"\n{Colors.GREEN}✅ 資源配置合理{Colors.END}")
                        
            except ImportError:
                print(f"\n{Colors.YELLOW}硬體資源參考：{Colors.END}")
                print(f"  無法獲取詳細硬體資訊（缺少 psutil 模組）")
                print(f"  建議：確保並行設置不超過您的硬體能力")
                
                if nerl_tasks > 0:
                    max_possible_processes = min(max_workers, nerl_tasks) * (1 + nerl_internal_workers)
                    print(f"  最大可能進程數: {max_possible_processes}")
                    print(f"  請確保此數值不超過您的CPU核心數")
            
            return min(max_workers, nerl_tasks) * (1 + nerl_internal_workers) if nerl_tasks > 0 else max_workers
        else:
            print(f"\n{Colors.WHITE}並行執行已停用，將順序執行所有任務（1個進程）{Colors.END}")
            return 1
    
    def save_config(self, config: Dict, name: str) -> bool:
        """
        保存配置到文件
        
        Args:
            config: 配置字典
            name: 配置名稱
            
        Returns:
            bool: 是否保存成功
        """
        try:
            config_file = self.config_dir / f"{name}.json"
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            print(f"✅ 配置已保存至: {config_file}")
            return True
        except Exception as e:
            print(f"❌ 保存配置失敗: {e}")
            return False
    
    def load_config(self, name: str) -> Optional[Dict]:
        """
        從文件載入配置
        
        Args:
            name: 配置名稱
            
        Returns:
            dict or None: 配置字典，失敗時返回None
        """
        try:
            config_file = self.config_dir / f"{name}.json"
            if not config_file.exists():
                print(f"❌ 配置文件不存在: {config_file}")
                return None
            
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            print(f"✅ 已載入配置: {config_file}")
            return config
        except Exception as e:
            print(f"❌ 載入配置失敗: {e}")
            return None
    
    def list_saved_configs(self) -> List[str]:
        """
        列出所有已保存的配置
        
        Returns:
            list: 配置文件名稱列表
        """
        config_files = list(self.config_dir.glob("*.json"))
        return [f.stem for f in config_files]
    
    def interactive_config_management(self):
        """互動式配置管理"""
        print("\n" + "="*50)
        print("💾 配置管理")
        print("="*50)
        
        print("\n[1] 保存當前配置")
        print("[2] 載入已保存的配置")
        print("[3] 查看已保存的配置")
        print("[4] 刪除配置")
        print("[0] 返回")
        
        choice = input("\n請選擇 [1-4, 0]: ").strip()
        
        if choice == "1":
            name = input("配置名稱: ").strip()
            if name and self.current_config:
                self.save_config(self.current_config, name)
        
        elif choice == "2":
            configs = self.list_saved_configs()
            if configs:
                print("\n已保存的配置：")
                for i, name in enumerate(configs, 1):
                    print(f"[{i}] {name}")
                
                try:
                    idx = int(input("選擇要載入的配置: ").strip()) - 1
                    if 0 <= idx < len(configs):
                        config = self.load_config(configs[idx])
                        if config:
                            self.current_config = config
                except:
                    print("❌ 無效選擇")
            else:
                print("沒有已保存的配置")
        
        elif choice == "3":
            configs = self.list_saved_configs()
            if configs:
                print("\n已保存的配置：")
                for name in configs:
                    print(f"- {name}")
            else:
                print("沒有已保存的配置")
        
        elif choice == "4":
            configs = self.list_saved_configs()
            if configs:
                print("\n已保存的配置：")
                for i, name in enumerate(configs, 1):
                    print(f"[{i}] {name}")
                
                try:
                    idx = int(input("選擇要刪除的配置: ").strip()) - 1
                    if 0 <= idx < len(configs):
                        config_file = self.config_dir / f"{configs[idx]}.json"
                        config_file.unlink()
                        print(f"✅ 已刪除配置: {configs[idx]}")
                except:
                    print("❌ 無效選擇")
            else:
                print("沒有已保存的配置")
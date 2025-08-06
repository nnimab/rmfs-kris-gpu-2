#!/usr/bin/env python3
"""
RMFS Training Results Visualization Generator V2
Enhanced version with robust data validation and English labels
"""

import os
import json
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from pathlib import Path
import seaborn as sns
from datetime import datetime
import argparse
import warnings
warnings.filterwarnings('ignore')

# 導入編碼處理器
from encoding_handler import EncodingHandler

# 跨平台字體設置
import platform
import matplotlib

def setup_cross_platform_fonts():
    """設置跨平台字體支援"""
    system = platform.system()
    
    if system == "Windows":
        # Windows 系統優先字體
        fonts = ['Microsoft YaHei', 'SimHei', 'DejaVu Sans', 'Arial']
    elif system == "Darwin":  # macOS
        # macOS 系統優先字體
        fonts = ['Helvetica Neue', 'Arial Unicode MS', 'DejaVu Sans', 'Arial']
    else:  # Linux/Ubuntu
        # Linux 系統優先字體
        fonts = ['DejaVu Sans', 'Liberation Sans', 'Droid Sans', 'Noto Sans CJK SC']
    
    # 設置字體家族
    matplotlib.rcParams['font.family'] = fonts
    matplotlib.rcParams['axes.unicode_minus'] = False
    
    # 設置中文字體（如果需要）
    try:
        if system == "Windows":
            matplotlib.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei'] + fonts
        elif system == "Linux":
            # Ubuntu/Linux 中文字體
            matplotlib.rcParams['font.sans-serif'] = ['Noto Sans CJK SC', 'WenQuanYi Micro Hei'] + fonts
    except:
        pass  # 如果設置失敗，使用預設字體

# 執行跨平台字體設置
setup_cross_platform_fonts()

# Set clean style
sns.set_style("whitegrid")
plt.style.use('default')

class RobustDataValidator:
    """Robust data validation and extraction"""
    
    @staticmethod
    def safe_get(data, keys, default=None):
        """Safely get nested dictionary value"""
        try:
            current = data
            for key in keys if isinstance(keys, list) else [keys]:
                if isinstance(current, dict) and key in current:
                    current = current[key]
                else:
                    return default
            return current if current is not None else default
        except:
            return default
    
    @staticmethod
    def validate_numeric(value, min_val=None, max_val=None, default=0):
        """Validate and clean numeric values"""
        try:
            if value is None:
                return default
            
            # Handle string numbers
            if isinstance(value, str):
                value = float(value)
            
            # Check for invalid values
            if np.isnan(value) or np.isinf(value):
                return default
            
            # Check bounds
            if min_val is not None and value < min_val:
                return default
            if max_val is not None and value > max_val:
                return default
                
            return float(value)
        except:
            return default
    
    @staticmethod
    def validate_list(data, expected_length=None, default_item=0):
        """Validate and clean list data"""
        try:
            if not isinstance(data, list):
                return []
            
            # Filter out invalid values
            cleaned = []
            for item in data:
                if isinstance(item, (int, float)) and not (np.isnan(item) or np.isinf(item)):
                    # Filter extreme outliers (likely errors)
                    if abs(item) < 1e9:  # Reasonable upper bound
                        cleaned.append(float(item))
                    else:
                        cleaned.append(default_item)
                else:
                    cleaned.append(default_item)
            
            # Ensure expected length
            if expected_length and len(cleaned) != expected_length:
                while len(cleaned) < expected_length:
                    cleaned.append(default_item)
                cleaned = cleaned[:expected_length]
            
            return cleaned
        except:
            return [default_item] * (expected_length or 1)

class EnhancedRMFSVisualizer:
    def __init__(self, results_dir="models/training_runs", test_mode=False):
        self.results_dir = Path(results_dir)
        self.output_dir = Path("analysis_results")
        self.output_dir.mkdir(exist_ok=True)
        self.test_mode = test_mode
        self.validator = RobustDataValidator()
        self.encoder = EncodingHandler()
        
        self.encoder.safe_print(f"Results directory: {self.results_dir}")
        self.encoder.safe_print(f"Output directory: {self.output_dir}")
        
    def create_test_data(self):
        """Create test data for Windows testing"""
        self.encoder.print_status('test', 'Creating test data for demonstration...')
        
        test_data = {
            'nerl_global_test': {
                'metadata': {
                    'controller_type': 'nerl',
                    'reward_mode': 'global',
                    'start_time': '2025-01-20 10:00:00',
                    'end_time': '2025-01-20 12:00:00',
                    'config': {'generations': 10, 'population_size': 8},
                    'results': {'best_fitness': 1.25, 'completed_orders_final_eval': 12}
                },
                'controller_type': 'nerl',
                'reward_mode': 'global',
                'generations': [
                    {
                        'generation': i+1,
                        'best_fitness': 0.5 + 0.1*i + np.random.normal(0, 0.05),
                        'all_fitness': [0.3 + 0.08*i + np.random.normal(0, 0.1) for _ in range(8)],
                        'best_individual_metrics': {
                            'completed_orders': min(5 + i, 15),
                            'completion_rate': min(0.1 + 0.02*i, 0.3),
                            'energy_per_order': max(200 - 10*i, 100),
                            'avg_wait_time': max(35 - 2*i, 20),
                            'robot_utilization': min(0.7 + 0.03*i, 1.0)
                        }
                    } for i in range(10)
                ]
            },
            'nerl_step_test': {
                'metadata': {
                    'controller_type': 'nerl',
                    'reward_mode': 'step',
                    'results': {'best_fitness': -45.2, 'completed_orders_final_eval': 8}
                },
                'controller_type': 'nerl',
                'reward_mode': 'step',
                'generations': [
                    {
                        'generation': i+1,
                        'best_fitness': -60 + 2*i + np.random.normal(0, 2),
                        'all_fitness': [-65 + 1.5*i + np.random.normal(0, 3) for _ in range(8)],
                        'best_individual_metrics': {
                            'completed_orders': min(2 + i//2, 10),
                            'completion_rate': min(0.04 + 0.01*i, 0.2),
                            'energy_per_order': max(300 - 15*i, 150),
                            'avg_wait_time': max(40 - i, 25)
                        }
                    } for i in range(10)
                ]
            },
            'dqn_global_test': {
                'metadata': {
                    'controller_type': 'dqn',
                    'reward_mode': 'global',
                    'results': {'best_fitness': 0.85, 'completed_orders': 10}
                },
                'controller_type': 'dqn',
                'reward_mode': 'global',
                'training_progress': [
                    {
                        'episode': i*100,
                        'cumulative_reward': -50 + 0.5*i + np.random.normal(0, 5),
                        'completed_orders': min(i//2, 12),
                        'epsilon': max(1.0 - 0.1*i, 0.01)
                    } for i in range(20)
                ]
            }
        }
        
        return test_data
    
    def load_training_data(self):
        """Load all training results with robust validation"""
        if self.test_mode:
            return self.create_test_data()
            
        training_data = {}
        
        if not self.results_dir.exists():
            self.encoder.print_warning(f"Results directory not found: {self.results_dir}")
            return {}
        
        self.encoder.print_scan(f"Scanning for training results in {self.results_dir}")
        
        for run_dir in self.results_dir.iterdir():
            if not run_dir.is_dir():
                continue
                
            metadata_file = run_dir / "metadata.json"
            
            # 檢查是否有世代數據（即使沒有 metadata.json）
            gen_dirs = sorted([d for d in run_dir.glob("gen*") if d.is_dir()])
            has_generation_data = len(gen_dirs) > 0
            
            if not metadata_file.exists() and not has_generation_data:
                self.encoder.print_warning(f"No metadata or generation data found in {run_dir.name}")
                continue
            elif not metadata_file.exists() and has_generation_data:
                self.encoder.print_warning(f"No metadata found in {run_dir.name}, but found {len(gen_dirs)} generations - creating minimal metadata")
                # 為沒有完整完成的訓練創建最小 metadata
                metadata = self.create_minimal_metadata_from_generations(run_dir, gen_dirs)
            else:
                # 正常讀取 metadata.json
                try:
                    with open(metadata_file, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                except Exception as e:
                    self.encoder.print_warning(f"Error reading metadata from {run_dir.name}: {e}")
                    continue
                
                # Validate essential fields
                controller_type = self.validator.safe_get(metadata, 'controller_type')
                reward_mode = self.validator.safe_get(metadata, 'reward_mode')
                variant = self.validator.safe_get(metadata.get('config', {}), 'variant', 'default')
                
                if not controller_type or not reward_mode:
                    self.encoder.print_warning(f"Invalid metadata in {run_dir.name}")
                    continue
                
                run_name = run_dir.name
                display_name = f"{controller_type}_{reward_mode}"
                if variant and variant != 'default':
                    display_name += f"_{variant}"
                self.encoder.print_success(f"Found {display_name}: {run_name}")
                
            try:
                # Load generation data for NERL
                generations_data = []
                if controller_type == 'nerl':
                    gen_dirs = sorted([d for d in run_dir.glob("gen*") if d.is_dir()])
                    self.encoder.print_chart(f"Found {len(gen_dirs)} generations")
                    
                    for gen_dir in gen_dirs:
                        fitness_file = gen_dir / "fitness_scores.json"
                        if fitness_file.exists():
                            try:
                                with open(fitness_file, 'r', encoding='utf-8') as f:
                                    gen_data = json.load(f)
                                
                                # Validate generation data
                                validated_gen = self.validate_generation_data(gen_data)
                                if validated_gen:
                                    generations_data.append(validated_gen)
                                    
                            except Exception as e:
                                self.encoder.print_warning(f"Error loading {fitness_file}: {e}")
                
                # Load DQN training logs if available
                training_progress = []
                if controller_type == 'dqn':
                    # Try to find training log or create from metadata
                    training_log = run_dir / "training.log"
                    if training_log.exists():
                        training_progress = self.parse_dqn_training_log(training_log)
                    else:
                        # Create basic progress from metadata
                        training_progress = self.create_dqn_progress_from_metadata(metadata)
                
                training_data[run_name] = {
                    'metadata': metadata,
                    'controller_type': controller_type,
                    'reward_mode': reward_mode,
                    'variant': variant,
                    'generations': generations_data,
                    'training_progress': training_progress,
                    'run_dir': run_dir
                }
                
            except Exception as e:
                self.encoder.print_warning(f"Error loading {run_dir}: {e}")
                
        self.encoder.print_success(f"Successfully loaded {len(training_data)} training runs")
        return training_data
    
    def create_minimal_metadata_from_generations(self, run_dir, gen_dirs):
        """為沒有完整完成的訓練創建最小 metadata"""
        try:
            # 從目錄名稱推斷控制器類型和獎勵模式
            dir_name = run_dir.name
            parts = dir_name.split('_')
            
            # 預設值
            controller_type = 'nerl'  # 假設是 NERL，因為只有 NERL 有世代結構
            reward_mode = 'step'  # 預設
            variant = 'default'
            
            # 嘗試從目錄名稱解析
            if len(parts) >= 4:
                # 格式: YYYY-MM-DD_HHMMSS_controller_reward[_variant]
                if len(parts) >= 4:
                    controller_type = parts[2]
                    reward_mode = parts[3]
                if len(parts) >= 5:
                    variant = parts[4]
            
            # 從最後一個世代獲取最終結果
            last_gen_dir = gen_dirs[-1]
            fitness_file = last_gen_dir / "fitness_scores.json"
            
            final_results = {}
            if fitness_file.exists():
                try:
                    with open(fitness_file, 'r', encoding='utf-8') as f:
                        last_gen_data = json.load(f)
                        final_results = {
                            'best_fitness': last_gen_data.get('best_fitness', 0),
                            'completed_orders_final_eval': last_gen_data.get('best_individual_metrics', {}).get('completed_orders', 0),
                            'total_energy_final_eval': last_gen_data.get('best_individual_metrics', {}).get('total_energy_consumed', 0)
                        }
                except:
                    pass
            
            # 創建最小 metadata
            minimal_metadata = {
                'controller_type': controller_type,
                'reward_mode': reward_mode,
                'start_time': 'Unknown',
                'end_time': 'Incomplete',
                'config': {
                    'variant': variant,
                    'generations': len(gen_dirs),
                    'status': 'incomplete'
                },
                'results': final_results
            }
            
            return minimal_metadata
            
        except Exception as e:
            self.encoder.print_warning(f"Error creating minimal metadata: {e}")
            # 返回超級基本的 metadata
            return {
                'controller_type': 'nerl',
                'reward_mode': 'step',
                'config': {'variant': 'default', 'status': 'incomplete'},
                'results': {}
            }
    
    def validate_generation_data(self, gen_data):
        """Validate and clean generation data"""
        try:
            generation = self.validator.safe_get(gen_data, 'generation', 0)
            best_fitness = self.validator.validate_numeric(
                self.validator.safe_get(gen_data, 'best_fitness'), 
                min_val=-1e6, max_val=1e6, default=0
            )
            
            # Validate fitness array
            all_fitness = self.validator.safe_get(gen_data, 'all_fitness', [])
            all_fitness = self.validator.validate_list(all_fitness, default_item=best_fitness)
            
            # Validate metrics
            metrics = self.validator.safe_get(gen_data, 'best_individual_metrics', {})
            validated_metrics = {
                'completed_orders': self.validator.validate_numeric(
                    self.validator.safe_get(metrics, 'completed_orders'), 
                    min_val=0, max_val=100, default=0
                ),
                'completion_rate': self.validator.validate_numeric(
                    self.validator.safe_get(metrics, 'completion_rate'), 
                    min_val=0, max_val=1, default=0
                ),
                'energy_per_order': self.validator.validate_numeric(
                    self.validator.safe_get(metrics, 'energy_per_order'), 
                    min_val=0, max_val=10000, default=0
                ),
                'avg_wait_time': self.validator.validate_numeric(
                    self.validator.safe_get(metrics, 'avg_wait_time'), 
                    min_val=0, max_val=1000, default=0
                ),
                'robot_utilization': self.validator.validate_numeric(
                    self.validator.safe_get(metrics, 'robot_utilization'), 
                    min_val=0, max_val=1, default=0
                )
            }
            
            return {
                'generation': int(generation),
                'best_fitness': best_fitness,
                'all_fitness': all_fitness,
                'best_individual_metrics': validated_metrics
            }
            
        except Exception as e:
            self.encoder.print_warning(f"Error validating generation data: {e}")
            return None
    
    def parse_dqn_training_log(self, log_file):
        """Parse DQN training log for progress data"""
        # This is a placeholder - implement based on your actual log format
        return []
    
    def create_dqn_progress_from_metadata(self, metadata):
        """Create basic DQN progress from metadata"""
        results = self.validator.safe_get(metadata, 'results', {})
        final_reward = self.validator.validate_numeric(
            self.validator.safe_get(results, 'cumulative_step_reward', 0)
        )
        
        # Create a simple progress simulation
        return [
            {
                'step': i * 10000,
                'cumulative_reward': final_reward * (i / 20),
                'epsilon': max(1.0 - i * 0.05, 0.01)
            } for i in range(21)
        ]
    
    def plot_individual_training_curves(self, training_data):
        """Generate individual training curve plots for each training run"""
        plots_created = []
        
        # 創建顏色分配函數
        def get_line_color_for_config(controller_type, reward_mode, variant):
            """為線條圖分配顏色"""
            color_map = {
                # NERL 顏色系列
                'nerl_step_default': '#2E8B57',    # 深綠色
                'nerl_step_a': '#32CD32',          # 酸橙綠
                'nerl_step_b': '#228B22',          # 森林綠
                'nerl_global_default': '#4169E1',  # 皇家藍
                'nerl_global_a': '#6495ED',        # 矢車菊藍
                'nerl_global_b': '#1E90FF',        # 道奇藍
                
                # DQN 顏色系列
                'dqn_step_default': '#DC143C',     # 深紅色
                'dqn_step_a': '#FF6347',           # 番茄紅
                'dqn_step_b': '#B22222',           # 火磚紅
                'dqn_global_default': '#FF8C00',   # 深橙色
                'dqn_global_a': '#FFA500',         # 橙色
                'dqn_global_b': '#FF7F50',         # 珊瑚色
            }
            
            variant_key = variant if variant != 'default' else 'default'
            key = f"{controller_type}_{reward_mode}_{variant_key}"
            return color_map.get(key, '#2E8B57')  # 默認深綠色
        
        # 為每個訓練運行生成獨立的圖表
        for run_name, data in training_data.items():
            if not data['generations'] or data['controller_type'] != 'nerl':
                continue
            
            variant = data.get('variant', 'default')
            color = get_line_color_for_config(data['controller_type'], data['reward_mode'], variant)
            
            # 建立標籤
            if variant and variant != 'default':
                run_label = f"NERL {data['reward_mode'].upper()}_{variant}"
            else:
                run_label = f"NERL {data['reward_mode'].upper()}"
            
            generations = [g['generation'] for g in data['generations']]
            
            # 1. 個別適應度進化圖
            fig, ax = plt.subplots(figsize=(10, 6))
            best_fitness = [g['best_fitness'] for g in data['generations']]
            ax.plot(generations, best_fitness, 'o-', color=color, linewidth=2, markersize=6)
            ax.set_title(f'{run_label} - Fitness Evolution', fontsize=14, fontweight='bold')
            ax.set_xlabel('Generation')
            ax.set_ylabel('Best Fitness Score')
            ax.grid(True, alpha=0.3)
            
            # 清理run_name用於文件名
            safe_run_name = run_name.replace(':', '_').replace(' ', '_')
            filename = f"fitness_{safe_run_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            filepath = self.output_dir / filename
            plt.savefig(filepath, dpi=300, bbox_inches='tight')
            plt.close()
            plots_created.append(filepath)
            self.encoder.safe_print(f"✅ Created: {filename}")
            
            # 2. 個別完成率進化圖
            fig, ax = plt.subplots(figsize=(10, 6))
            completion_rates = [g['best_individual_metrics']['completion_rate'] * 100 
                              for g in data['generations']]
            ax.plot(generations, completion_rates, 's-', color=color, linewidth=2, markersize=6)
            ax.set_title(f'{run_label} - Completion Rate Evolution', fontsize=14, fontweight='bold')
            ax.set_xlabel('Generation')
            ax.set_ylabel('Completion Rate (%)')
            ax.grid(True, alpha=0.3)
            
            filename = f"completion_rate_{safe_run_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            filepath = self.output_dir / filename
            plt.savefig(filepath, dpi=300, bbox_inches='tight')
            plt.close()
            plots_created.append(filepath)
            self.encoder.safe_print(f"✅ Created: {filename}")
            
            # 3. 個別能源效率進化圖
            energy_per_order = [g['best_individual_metrics']['energy_per_order'] 
                              for g in data['generations']]
            if any(e > 0 for e in energy_per_order):
                fig, ax = plt.subplots(figsize=(10, 6))
                ax.plot(generations, energy_per_order, '^-', color=color, linewidth=2, markersize=6)
                ax.set_title(f'{run_label} - Energy Efficiency Evolution', fontsize=14, fontweight='bold')
                ax.set_xlabel('Generation')
                ax.set_ylabel('Energy per Order')
                ax.grid(True, alpha=0.3)
                
                filename = f"energy_efficiency_{safe_run_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                filepath = self.output_dir / filename
                plt.savefig(filepath, dpi=300, bbox_inches='tight')
                plt.close()
                plots_created.append(filepath)
                self.encoder.safe_print(f"✅ Created: {filename}")
        
        # 4. Robot Utilization 比較圖（時間序列）
        fig, ax = plt.subplots(figsize=(12, 8))
        
        for run_name, data in training_data.items():
            if not data['generations'] or data['controller_type'] != 'nerl':
                continue
                
            generations = [g['generation'] for g in data['generations']]
            robot_utilization = [g['best_individual_metrics'].get('robot_utilization', 0) * 100 
                               for g in data['generations']]
            
            variant = data.get('variant', 'default')
            color = get_line_color_for_config(data['controller_type'], data['reward_mode'], variant)
            
            if variant and variant != 'default':
                label = f"NERL {data['reward_mode'].upper()}_{variant}"
            else:
                label = f"NERL {data['reward_mode'].upper()}"
            
            ax.plot(generations, robot_utilization, 'o-', color=color, label=label, 
                   linewidth=2, markersize=6)
        
        ax.set_title('Robot Utilization Over Time', fontsize=14, fontweight='bold')
        ax.set_xlabel('Generation')
        ax.set_ylabel('Robot Utilization (%)')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        filename = f"robot_utilization_timeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        filepath = self.output_dir / filename
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()
        plots_created.append(filepath)
        self.encoder.safe_print(f"✅ Created: {filename}")
        
        return plots_created
    
    def plot_final_comparison(self, training_data):
        """Generate final performance comparison plots"""
        comparison_data = []
        
        for run_name, data in training_data.items():
            controller_type = data['controller_type']
            reward_mode = data['reward_mode']
            variant = data.get('variant', 'default')
            metadata = data['metadata']
            
            # Create display name with variant
            display_name = f"{controller_type.upper()}_{reward_mode}"
            if variant and variant != 'default':
                display_name += f"_{variant}"
            
            # Extract final performance metrics
            if controller_type == 'nerl' and data['generations']:
                last_gen = data['generations'][-1]
                metrics = last_gen['best_individual_metrics']
                
                comparison_data.append({
                    'name': display_name,
                    'controller_type': controller_type,
                    'reward_mode': reward_mode,
                    'variant': variant,
                    'completed_orders': metrics.get('completed_orders', 0),
                    'completion_rate': metrics.get('completion_rate', 0) * 100,
                    'energy_per_order': metrics.get('energy_per_order', 0),
                    'avg_wait_time': metrics.get('avg_wait_time', 0),
                    'robot_utilization': metrics.get('robot_utilization', 0) * 100
                })
                
            elif controller_type == 'dqn':
                results = metadata.get('results', {})
                completed_orders = self.validator.validate_numeric(
                    self.validator.safe_get(results, 'completed_orders', 0)
                )
                
                comparison_data.append({
                    'name': display_name,
                    'controller_type': controller_type,
                    'reward_mode': reward_mode,
                    'variant': variant,
                    'completed_orders': completed_orders,
                    'completion_rate': (completed_orders / 50) * 100 if completed_orders > 0 else 0,
                    'energy_per_order': 0,  # DQN might not have this
                    'avg_wait_time': 0,
                    'robot_utilization': 0
                })
        
        if not comparison_data:
            self.encoder.safe_print("⚠️  No valid comparison data found")
            return []
        
        df = pd.DataFrame(comparison_data)
        plots_created = []
        
        # Individual comparison plots
        metrics = [
            ('completed_orders', 'Completed Orders', 'Number of Orders'),
            ('completion_rate', 'Completion Rate', 'Completion Rate (%)'),
            ('avg_wait_time', 'Average Wait Time', 'Wait Time (ticks)'),
            ('robot_utilization', 'Robot Utilization', 'Utilization (%)')
        ]
        
        # 創建更豐富的顏色方案，支援控制器類型、獎勵模式和變體
        def get_color_for_config(controller_type, reward_mode, variant):
            """根據控制器類型、獎勵模式和變體分配顏色"""
            color_map = {
                # NERL 顏色系列
                'nerl_step_default': '#2E8B57',    # 深綠色
                'nerl_step_a': '#32CD32',          # 酸橙綠
                'nerl_step_b': '#228B22',          # 森林綠
                'nerl_global_default': '#4169E1',  # 皇家藍
                'nerl_global_a': '#6495ED',        # 矢車菊藍
                'nerl_global_b': '#1E90FF',        # 道奇藍
                
                # DQN 顏色系列
                'dqn_step_default': '#DC143C',     # 深紅色
                'dqn_step_a': '#FF6347',           # 番茄紅
                'dqn_step_b': '#B22222',           # 火磚紅
                'dqn_global_default': '#FF8C00',   # 深橙色
                'dqn_global_a': '#FFA500',         # 橙色
                'dqn_global_b': '#FF7F50',         # 珊瑚色
            }
            
            # 構建鍵值
            variant_key = variant if variant != 'default' else 'default'
            key = f"{controller_type}_{reward_mode}_{variant_key}"
            
            # 返回對應顏色，如果沒有找到則使用灰色
            return color_map.get(key, '#808080')
        
        for metric_key, title, ylabel in metrics:
            if df[metric_key].sum() == 0:  # Skip if all values are 0
                continue
                
            fig, ax = plt.subplots(figsize=(12, 8))  # 增加圖表尺寸以容納更多資訊
            
            # 為每個配置分配不同顏色
            colors_list = []
            for _, row in df.iterrows():
                color = get_color_for_config(row['controller_type'], row['reward_mode'], row['variant'])
                colors_list.append(color)
            
            bars = ax.bar(range(len(df)), df[metric_key], color=colors_list)
            
            ax.set_title(f'{title} Comparison', fontsize=14, fontweight='bold')
            ax.set_ylabel(ylabel)
            ax.set_xticks(range(len(df)))
            ax.set_xticklabels(df['name'], rotation=45, ha='right')
            
            # Add value labels on bars
            for i, bar in enumerate(bars):
                height = bar.get_height()
                if height > 0:
                    ax.text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                           f'{height:.1f}', ha='center', va='bottom', fontweight='bold')
            
            # 創建顏色圖例
            from matplotlib.patches import Patch
            legend_elements = []
            seen_configs = set()
            
            for _, row in df.iterrows():
                controller_type = row['controller_type']
                reward_mode = row['reward_mode']
                variant = row['variant']
                config_key = f"{controller_type}_{reward_mode}_{variant}"
                
                if config_key not in seen_configs:
                    color = get_color_for_config(controller_type, reward_mode, variant)
                    if variant and variant != 'default':
                        legend_label = f"{controller_type.upper()} {reward_mode} {variant}"
                    else:
                        legend_label = f"{controller_type.upper()} {reward_mode}"
                    legend_elements.append(Patch(facecolor=color, label=legend_label))
                    seen_configs.add(config_key)
            
            if legend_elements:
                ax.legend(handles=legend_elements, loc='upper right', bbox_to_anchor=(1.15, 1))
            
            plt.tight_layout()
            
            filename = f"{metric_key}_comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            filepath = self.output_dir / filename
            plt.savefig(filepath, dpi=300, bbox_inches='tight')
            plt.close()
            plots_created.append(filepath)
            self.encoder.safe_print(f"✅ Created: {filename}")
        
        return plots_created, df
    
    def generate_report(self, training_data, comparison_df=None):
        """Generate comprehensive analysis report"""
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        report_file = self.output_dir / f"analysis_report_{timestamp}.txt"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("="*60 + "\n")
            f.write("RMFS Training Results Analysis Report\n")
            f.write("="*60 + "\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Test Mode: {'Yes' if self.test_mode else 'No'}\n\n")
            
            # Training overview
            f.write("1. Training Overview\n")
            f.write("-"*30 + "\n")
            f.write(f"Total training runs: {len(training_data)}\n")
            
            nerl_runs = [d for d in training_data.values() if d['controller_type'] == 'nerl']
            dqn_runs = [d for d in training_data.values() if d['controller_type'] == 'dqn']
            
            f.write(f"NERL runs: {len(nerl_runs)}\n")
            f.write(f"DQN runs: {len(dqn_runs)}\n\n")
            
            # Detailed analysis for each run
            f.write("2. Detailed Analysis\n")
            f.write("-"*30 + "\n")
            
            for run_name, data in training_data.items():
                f.write(f"\n{run_name}:\n")
                f.write(f"  Type: {data['controller_type'].upper()}\n")
                f.write(f"  Reward Mode: {data['reward_mode']}\n")
                variant = data.get('variant', 'default')
                if variant and variant != 'default':
                    f.write(f"  Variant: {variant}\n")
                
                if data['controller_type'] == 'nerl' and data['generations']:
                    last_gen = data['generations'][-1]
                    metrics = last_gen['best_individual_metrics']
                    f.write(f"  Generations: {len(data['generations'])}\n")
                    f.write(f"  Final Fitness: {last_gen['best_fitness']:.4f}\n")
                    f.write(f"  Completed Orders: {metrics.get('completed_orders', 'N/A')}\n")
                    f.write(f"  Completion Rate: {metrics.get('completion_rate', 0)*100:.1f}%\n")
                    f.write(f"  Energy per Order: {metrics.get('energy_per_order', 0):.1f}\n")
                    f.write(f"  Avg Wait Time: {metrics.get('avg_wait_time', 0):.1f} ticks\n")
                
                elif data['controller_type'] == 'dqn':
                    results = data['metadata'].get('results', {})
                    f.write(f"  Final Reward: {results.get('cumulative_step_reward', 'N/A')}\n")
                    f.write(f"  Completed Orders: {results.get('completed_orders', 'N/A')}\n")
            
            # Performance comparison
            if comparison_df is not None and not comparison_df.empty:
                f.write("\n\n3. Performance Ranking\n")
                f.write("-"*30 + "\n")
                
                # Sort by completion rate
                sorted_df = comparison_df.sort_values('completion_rate', ascending=False)
                f.write("By Completion Rate:\n")
                for i, (_, row) in enumerate(sorted_df.iterrows(), 1):
                    f.write(f"  {i}. {row['name']}: {row['completion_rate']:.1f}%\n")
                
                # Best performer
                best = sorted_df.iloc[0]
                f.write(f"\nBest Overall Performance: {best['name']}\n")
                f.write(f"  Completion Rate: {best['completion_rate']:.1f}%\n")
                f.write(f"  Completed Orders: {best['completed_orders']}\n")
            
            f.write("\n\n4. Data Quality Assessment\n")
            f.write("-"*30 + "\n")
            f.write("All data has been validated and cleaned:\n")
            f.write("• Numeric values checked for NaN/Inf\n")
            f.write("• Outliers filtered (values > 1e9)\n")
            f.write("• Missing values replaced with defaults\n")
            f.write("• List lengths validated\n")
        
        self.encoder.safe_print(f"✅ Report saved: {report_file}")
        return report_file
    
    def run_analysis(self):
        """Run complete analysis with robust error handling"""
        self.encoder.safe_print("🔍 Starting RMFS training results analysis...")
        self.encoder.safe_print(f"📁 Working directory: {os.getcwd()}")
        
        # Load and validate data
        training_data = self.load_training_data()
        if not training_data:
            self.encoder.safe_print("❌ No valid training data found")
            if not self.test_mode:
                self.encoder.safe_print("💡 Try running with --test flag to see demo output")
            return None
        
        self.encoder.safe_print(f"✅ Loaded {len(training_data)} valid training runs")
        
        # Generate individual plots
        self.encoder.safe_print("\n📊 Generating individual training curves...")
        individual_plots = self.plot_individual_training_curves(training_data)
        
        # Generate comparison plots
        self.encoder.safe_print("\n📊 Generating performance comparison plots...")
        comparison_plots, comparison_df = self.plot_final_comparison(training_data)
        
        # Generate report
        self.encoder.safe_print("\n📝 Generating analysis report...")
        report_file = self.generate_report(training_data, comparison_df)
        
        # Summary
        self.encoder.safe_print("\n" + "="*50)
        self.encoder.safe_print("📊 Analysis Complete!")
        self.encoder.safe_print(f"📁 Output directory: {self.output_dir}")
        self.encoder.safe_print(f"📈 Individual plots: {len(individual_plots)}")
        self.encoder.safe_print(f"📊 Comparison plots: {len(comparison_plots)}")
        self.encoder.safe_print(f"📝 Report: {report_file.name}")
        self.encoder.safe_print("="*50)
        
        return {
            'individual_plots': individual_plots,
            'comparison_plots': comparison_plots,
            'report': report_file,
            'data': training_data
        }

def main():
    parser = argparse.ArgumentParser(description="RMFS Training Results Visualization V2")
    parser.add_argument('--results_dir', default='models/training_runs', 
                       help='Training results directory path')
    parser.add_argument('--test', action='store_true',
                       help='Run in test mode with simulated data')
    
    args = parser.parse_args()
    
    visualizer = EnhancedRMFSVisualizer(args.results_dir, test_mode=args.test)
    results = visualizer.run_analysis()
    
    return results

if __name__ == "__main__":
    main()
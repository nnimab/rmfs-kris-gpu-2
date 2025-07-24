#!/usr/bin/env python3
"""
RMFS 評估數據分析器
用於聚合多次獨立運行的結果並進行統計分析
"""

import argparse
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from datetime import datetime
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

# 設置圖表樣式
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

# 設置字體以支援英文
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['font.size'] = 10
plt.rcParams['axes.unicode_minus'] = False

class PaperAnalyzer:
    def __init__(self, root_dir, output_dir=None):
        """
        初始化分析器
        
        Args:
            root_dir: 包含評估結果的根目錄（可能是批次目錄）
            output_dir: 輸出目錄，如果為None則使用root_dir/aggregated_results
        """
        self.root_dir = Path(root_dir)
        self.output_dir = Path(output_dir) if output_dir else self.root_dir / "aggregated_results"
        self.output_dir.mkdir(exist_ok=True)
        
        # 儲存所有有效數據
        self.all_data = []
        self.controller_data = {}
        
    def load_all_results(self):
        """遞歸加載所有評估結果"""
        print(f"Scanning directory: {self.root_dir}")
        
        # 搜尋所有 evaluation_results.json 檔案
        json_files = list(self.root_dir.rglob("evaluation_results.json"))
        print(f"Found {len(json_files)} evaluation result files")
        
        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # 提取結果
                if 'results' in data:
                    results = data['results']
                    eval_config = data.get('evaluation_config', {})
                    
                    # 為每個結果添加來源資訊
                    for result in results:
                        result['source_file'] = str(json_file)
                        result['eval_ticks_config'] = eval_config.get('evaluation_ticks', 0)
                        self.all_data.append(result)
                        
                print(f"  Loaded {len(results)} runs from {json_file.parent.name}")
                        
            except Exception as e:
                print(f"  Error loading {json_file}: {e}")
        
        print(f"\nTotal runs loaded: {len(self.all_data)}")
        
        # 按控制器分組
        self._group_by_controller()
        
    def _group_by_controller(self):
        """將數據按控制器分組"""
        self.controller_data = {}
        
        for result in self.all_data:
            controller_name = result.get('controller_name', 'unknown')
            
            # 統一控制器名稱格式
            if ':' in controller_name:
                # 處理 "dqn:models/xxx.pth" 格式
                parts = controller_name.split(':', 1)
                controller_type = parts[0]
                model_path = parts[1]
                
                # 從路徑提取模型資訊
                if 'step' in model_path:
                    controller_name = f"{controller_type}_step"
                elif 'global' in model_path:
                    controller_name = f"{controller_type}_global"
                else:
                    # 使用檔名作為識別
                    model_name = Path(model_path).stem
                    controller_name = f"{controller_type}_{model_name}"
            
            if controller_name not in self.controller_data:
                self.controller_data[controller_name] = []
            
            self.controller_data[controller_name].append(result)
        
        print(f"\nControllers found: {list(self.controller_data.keys())}")
        for controller, runs in self.controller_data.items():
            print(f"  {controller}: {len(runs)} runs")
    
    def validate_and_clean_data(self):
        """驗證並清洗數據"""
        print("\n=== Data Validation and Cleaning ===")
        
        cleaned_controller_data = {}
        
        for controller_name, runs in self.controller_data.items():
            valid_runs = []
            
            for run in runs:
                # 檢查關鍵欄位是否存在
                required_fields = ['warehouse_final_tick', 'evaluation_ticks', 
                                 'robot_utilization', 'completed_orders']
                
                if not all(field in run for field in required_fields):
                    print(f"  Skipping run: missing required fields")
                    continue
                
                # 務實混合策略驗證
                eval_ticks = run.get('evaluation_ticks', 0)
                final_tick = run.get('warehouse_final_tick', 0)
                
                # 檢查是否達到95%的評估時長
                if final_tick < eval_ticks * 0.95:
                    print(f"  Warning: {controller_name} run only reached {final_tick}/{eval_ticks} ticks "
                          f"({final_tick/eval_ticks*100:.1f}%)")
                    # 不直接跳過，但標記為可能有問題
                    run['incomplete'] = True
                
                # 檢查機器人利用率是否合理
                robot_util = run.get('robot_utilization', 0)
                if not 0 <= robot_util <= 1:
                    print(f"  Warning: Invalid robot utilization: {robot_util}")
                    # 嘗試修正
                    if robot_util > 1:
                        run['robot_utilization'] = robot_util / 100  # 可能是百分比
                    else:
                        run['robot_utilization'] = 0
                
                valid_runs.append(run)
            
            if valid_runs:
                cleaned_controller_data[controller_name] = valid_runs
                print(f"  {controller_name}: {len(valid_runs)}/{len(runs)} runs validated")
            else:
                print(f"  {controller_name}: No valid runs")
        
        self.controller_data = cleaned_controller_data
        
    def calculate_statistics(self):
        """計算統計數據"""
        print("\n=== Statistical Analysis ===")
        
        self.statistics = {}
        
        for controller_name, runs in self.controller_data.items():
            if not runs:
                continue
                
            # 提取數值
            metrics = {
                'completed_orders': [r['completed_orders'] for r in runs],
                'completion_rate': [r.get('completion_rate', 0) for r in runs],
                'avg_wait_time': [r.get('avg_wait_time', 0) for r in runs],
                'energy_per_order': [r.get('energy_per_order', 0) for r in runs],
                'robot_utilization': [r.get('robot_utilization', 0) for r in runs],
                'signal_switch_count': [r.get('signal_switch_count', 0) for r in runs],
                'avg_traffic_rate': [r.get('avg_traffic_rate', 0) for r in runs]
            }
            
            # 計算吞吐量 (completed_orders / evaluation_ticks)
            throughput = []
            for run in runs:
                ticks = run.get('evaluation_ticks', 1)
                orders = run.get('completed_orders', 0)
                throughput.append(orders / ticks * 1000)  # 訂單/1000 ticks
            
            metrics['throughput'] = throughput
            
            # 計算統計量
            stats_dict = {
                'n': len(runs),
                'metrics': {}
            }
            
            for metric_name, values in metrics.items():
                if values:
                    stats_dict['metrics'][metric_name] = {
                        'mean': np.mean(values),
                        'std': np.std(values, ddof=1) if len(values) > 1 else 0,
                        'min': np.min(values),
                        'max': np.max(values),
                        'median': np.median(values),
                        'values': values  # 保存原始值用於統計檢驗
                    }
            
            self.statistics[controller_name] = stats_dict
            
            # 打印摘要
            print(f"\n{controller_name} (n={stats_dict['n']}):")
            for metric, stats in stats_dict['metrics'].items():
                print(f"  {metric}: {stats['mean']:.2f} ± {stats['std']:.2f}")
    
    def perform_statistical_tests(self):
        """執行統計顯著性檢驗"""
        print("\n=== Statistical Significance Tests ===")
        
        controllers = list(self.statistics.keys())
        n_controllers = len(controllers)
        
        if n_controllers < 2:
            print("Need at least 2 controllers for comparison")
            return
        
        # 對每個指標進行成對比較
        metrics_to_test = ['completion_rate', 'avg_wait_time', 'throughput', 'energy_per_order']
        
        self.significance_results = {}
        
        for metric in metrics_to_test:
            print(f"\n{metric}:")
            metric_results = {}
            
            for i in range(n_controllers):
                for j in range(i+1, n_controllers):
                    controller1 = controllers[i]
                    controller2 = controllers[j]
                    
                    # 獲取數據
                    data1 = self.statistics[controller1]['metrics'].get(metric, {}).get('values', [])
                    data2 = self.statistics[controller2]['metrics'].get(metric, {}).get('values', [])
                    
                    if len(data1) >= 2 and len(data2) >= 2:
                        # 執行 t-test
                        t_stat, p_value = stats.ttest_ind(data1, data2)
                        
                        # 計算效應量 (Cohen's d)
                        pooled_std = np.sqrt((np.var(data1, ddof=1) + np.var(data2, ddof=1)) / 2)
                        cohens_d = (np.mean(data1) - np.mean(data2)) / pooled_std if pooled_std > 0 else 0
                        
                        result = {
                            't_statistic': t_stat,
                            'p_value': p_value,
                            'cohens_d': cohens_d,
                            'significant': p_value < 0.05
                        }
                        
                        key = f"{controller1}_vs_{controller2}"
                        metric_results[key] = result
                        
                        significance = "***" if p_value < 0.001 else "**" if p_value < 0.01 else "*" if p_value < 0.05 else "ns"
                        print(f"  {controller1} vs {controller2}: p={p_value:.4f} {significance}, d={cohens_d:.2f}")
            
            self.significance_results[metric] = metric_results
    
    def generate_performance_table(self):
        """生成性能總表"""
        print("\n=== Generating Performance Table ===")
        
        # 準備表格數據
        table_data = []
        
        for controller, stats in self.statistics.items():
            row = {
                'Controller': controller,
                'N': stats['n'],
                'Completion Rate (%)': f"{stats['metrics']['completion_rate']['mean']*100:.1f} ± {stats['metrics']['completion_rate']['std']*100:.1f}",
                'Throughput (orders/1000 ticks)': f"{stats['metrics']['throughput']['mean']:.1f} ± {stats['metrics']['throughput']['std']:.1f}",
                'Avg Wait Time (ticks)': f"{stats['metrics']['avg_wait_time']['mean']:.1f} ± {stats['metrics']['avg_wait_time']['std']:.1f}",
                'Energy per Order': f"{stats['metrics']['energy_per_order']['mean']:.0f} ± {stats['metrics']['energy_per_order']['std']:.0f}",
                'Signal Switches': f"{stats['metrics']['signal_switch_count']['mean']:.0f} ± {stats['metrics']['signal_switch_count']['std']:.0f}",
                'Traffic Rate': f"{stats['metrics']['avg_traffic_rate']['mean']:.2f} ± {stats['metrics']['avg_traffic_rate']['std']:.2f}"
            }
            table_data.append(row)
        
        # 轉換為 DataFrame
        df = pd.DataFrame(table_data)
        
        # 按完成率排序
        df['_sort_key'] = df['Controller'].apply(
            lambda x: self.statistics[x]['metrics']['completion_rate']['mean']
        )
        df = df.sort_values('_sort_key', ascending=False).drop('_sort_key', axis=1)
        
        # 保存為 CSV
        csv_file = self.output_dir / "performance_table.csv"
        df.to_csv(csv_file, index=False)
        print(f"Performance table saved to: {csv_file}")
        
        # 保存為 Markdown
        md_file = self.output_dir / "performance_table.md"
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write("# RMFS Controller Performance Comparison\n\n")
            f.write(df.to_markdown(index=False))
            f.write("\n\n## Statistical Significance\n\n")
            f.write("- \\*\\*\\*: p < 0.001\n")
            f.write("- \\*\\*: p < 0.01\n")
            f.write("- \\*: p < 0.05\n")
            f.write("- ns: not significant\n")
        
        print(f"Markdown table saved to: {md_file}")
        
        # 保存為 LaTeX
        tex_file = self.output_dir / "performance_table.tex"
        with open(tex_file, 'w', encoding='utf-8') as f:
            f.write(df.to_latex(index=False, caption="RMFS Controller Performance Comparison"))
        
        print(f"LaTeX table saved to: {tex_file}")
        
        return df
    
    def generate_comparison_charts(self):
        """生成比較圖表"""
        print("\n=== Generating Comparison Charts ===")
        
        # 準備數據
        controllers = []
        metrics_data = {
            'completion_rate': {'values': [], 'errors': [], 'ylabel': 'Completion Rate (%)'},
            'throughput': {'values': [], 'errors': [], 'ylabel': 'Throughput (orders/1000 ticks)'},
            'avg_wait_time': {'values': [], 'errors': [], 'ylabel': 'Average Wait Time (ticks)'},
            'energy_per_order': {'values': [], 'errors': [], 'ylabel': 'Energy per Order'}
        }
        
        # 按完成率排序控制器
        sorted_controllers = sorted(
            self.statistics.items(),
            key=lambda x: x[1]['metrics']['completion_rate']['mean'],
            reverse=True
        )
        
        for controller, stats in sorted_controllers:
            controllers.append(controller)
            for metric in metrics_data:
                mean = stats['metrics'][metric]['mean']
                std = stats['metrics'][metric]['std']
                
                if metric == 'completion_rate':
                    metrics_data[metric]['values'].append(mean * 100)
                    metrics_data[metric]['errors'].append(std * 100)
                else:
                    metrics_data[metric]['values'].append(mean)
                    metrics_data[metric]['errors'].append(std)
        
        # 創建圖表
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('RMFS Controller Performance Comparison', fontsize=16, fontweight='bold')
        
        # 設置顏色
        colors = plt.cm.Set3(np.linspace(0, 1, len(controllers)))
        
        # 繪製每個指標
        for idx, (metric, data) in enumerate(metrics_data.items()):
            ax = axes[idx // 2, idx % 2]
            
            # 創建條形圖
            bars = ax.bar(controllers, data['values'], yerr=data['errors'] if any(data['errors']) else None,
                          color=colors, capsize=5, alpha=0.8, edgecolor='black', linewidth=1)
            
            # 設置標題和標籤
            ax.set_title(metric.replace('_', ' ').title(), fontsize=14, fontweight='bold')
            ax.set_ylabel(data['ylabel'], fontsize=12)
            ax.set_xlabel('Controller', fontsize=12)
            
            # 旋轉x軸標籤
            ax.tick_params(axis='x', rotation=45)
            
            # 添加數值標籤
            for bar, value, error in zip(bars, data['values'], data['errors']):
                height = bar.get_height()
                if error > 0:
                    label = f'{value:.1f}\n±{error:.1f}'
                else:
                    label = f'{value:.1f}'
                ax.text(bar.get_x() + bar.get_width()/2., height + max(data['errors']) * 0.1,
                       label, ha='center', va='bottom', fontsize=9)
            
            # 添加網格
            ax.grid(True, axis='y', alpha=0.3)
        
        plt.tight_layout()
        
        # 保存圖表
        chart_file = self.output_dir / "performance_comparison.png"
        plt.savefig(chart_file, dpi=300, bbox_inches='tight')
        print(f"Comparison chart saved to: {chart_file}")
        
        # 生成統計顯著性熱力圖
        self._generate_significance_heatmap()
        
        plt.close('all')
    
    def _generate_significance_heatmap(self):
        """生成統計顯著性熱力圖"""
        if not hasattr(self, 'significance_results'):
            return
        
        # 為完成率創建熱力圖
        metric = 'completion_rate'
        if metric not in self.significance_results:
            return
        
        controllers = list(self.statistics.keys())
        n = len(controllers)
        
        # 創建矩陣
        p_matrix = np.ones((n, n))
        
        for i in range(n):
            for j in range(i+1, n):
                key = f"{controllers[i]}_vs_{controllers[j]}"
                if key in self.significance_results[metric]:
                    p_value = self.significance_results[metric][key]['p_value']
                    p_matrix[i, j] = p_value
                    p_matrix[j, i] = p_value
        
        # 創建圖表
        plt.figure(figsize=(10, 8))
        
        # 使用自定義顏色映射
        mask = np.triu(np.ones_like(p_matrix, dtype=bool))
        
        # 轉換p值為顯著性等級
        sig_matrix = np.zeros_like(p_matrix)
        sig_matrix[p_matrix < 0.001] = 3  # ***
        sig_matrix[(p_matrix >= 0.001) & (p_matrix < 0.01)] = 2  # **
        sig_matrix[(p_matrix >= 0.01) & (p_matrix < 0.05)] = 1  # *
        sig_matrix[p_matrix >= 0.05] = 0  # ns
        
        # 繪製熱力圖
        ax = sns.heatmap(sig_matrix, mask=mask, cmap='RdYlGn_r', vmin=0, vmax=3,
                        xticklabels=controllers, yticklabels=controllers,
                        square=True, linewidths=1, cbar_kws={'label': 'Significance Level'},
                        annot=p_matrix, fmt='.3f')
        
        plt.title('Statistical Significance Matrix - Completion Rate', fontsize=14, fontweight='bold')
        plt.tight_layout()
        
        # 保存圖表
        heatmap_file = self.output_dir / "significance_heatmap.png"
        plt.savefig(heatmap_file, dpi=300, bbox_inches='tight')
        print(f"Significance heatmap saved to: {heatmap_file}")
    
    def save_aggregated_results(self):
        """保存聚合後的結果"""
        print("\n=== Saving Aggregated Results ===")
        
        # 保存統計摘要
        summary_file = self.output_dir / "statistical_summary.json"
        
        summary_data = {
            'analysis_timestamp': datetime.now().isoformat(),
            'root_directory': str(self.root_dir),
            'total_runs_analyzed': len(self.all_data),
            'controllers': {}
        }
        
        for controller, stats in self.statistics.items():
            controller_summary = {
                'n_runs': stats['n'],
                'metrics': {}
            }
            
            for metric, metric_stats in stats['metrics'].items():
                controller_summary['metrics'][metric] = {
                    'mean': metric_stats['mean'],
                    'std': metric_stats['std'],
                    'min': metric_stats['min'],
                    'max': metric_stats['max'],
                    'median': metric_stats['median']
                }
            
            summary_data['controllers'][controller] = controller_summary
        
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary_data, f, indent=2, ensure_ascii=False)
        
        print(f"Statistical summary saved to: {summary_file}")
        
        # 保存詳細的聚合數據
        detailed_file = self.output_dir / "aggregated_raw_data.json"
        with open(detailed_file, 'w', encoding='utf-8') as f:
            json.dump(self.controller_data, f, indent=2, ensure_ascii=False)
        
        print(f"Aggregated raw data saved to: {detailed_file}")
    
    def run_analysis(self):
        """執行完整的分析流程"""
        print("="*60)
        print("RMFS Evaluation Data Analysis")
        print("="*60)
        
        # 1. 加載數據
        self.load_all_results()
        
        if not self.all_data:
            print("\nNo data found to analyze!")
            return
        
        # 2. 驗證和清洗數據
        self.validate_and_clean_data()
        
        if not self.controller_data:
            print("\nNo valid data after cleaning!")
            return
        
        # 3. 計算統計量
        self.calculate_statistics()
        
        # 4. 執行統計檢驗
        self.perform_statistical_tests()
        
        # 5. 生成表格
        self.generate_performance_table()
        
        # 6. 生成圖表
        self.generate_comparison_charts()
        
        # 7. 保存結果
        self.save_aggregated_results()
        
        print("\n" + "="*60)
        print("Analysis Complete!")
        print(f"Results saved in: {self.output_dir}")
        print("="*60)


def parse_dqn_log_line(line):
    """解析單行DQN訓練日誌，返回一個包含指標的字典。"""
    if "Episode" not in line or "Total Reward" not in line:
        return None
    
    try:
        parts = line.split(',')
        data = {}
        for part in parts:
            if ':' in part:
                key_val = part.split(':', 1)
                key = key_val[0].strip()
                # 清理鍵名
                if "Episode #" in key:
                    key = "episode"
                elif "Total Reward" in key:
                    key = "reward"
                elif "Avg Loss" in key:
                    key = "loss"
                elif "Avg Q-Value" in key:
                    key = "q_value"
                else:
                    continue  # 忽略不關心的指標
                
                data[key] = float(key_val[1])
        
        if all(k in data for k in ['episode', 'reward', 'loss', 'q_value']):
            return data
    except (ValueError, IndexError) as e:
        print(f"Warning: Could not parse line: {line.strip()}. Error: {e}")
    return None

def parse_dqn_log_line_as_json(line):
    """
    試圖將日誌行中的一部分解析為JSON。
    日誌行格式通常為 'TIMESTAMP - LEVEL - LOGGER - MESSAGE'。
    MESSAGE 部分可能是一個 JSON 字串。
    """
    try:
        # 尋找第一個 '{'，假設這是 JSON 字串的開始
        json_start_index = line.find('{')
        if json_start_index != -1:
            json_str = line[json_start_index:]
            data = json.loads(json_str)
            
            # 驗證是否為我們需要的 episode summary
            required_keys = ['end_tick', 'total_reward', 'steps', 'avg_loss', 'avg_q_value']
            if all(key in data for key in required_keys):
                return data
    except (json.JSONDecodeError, TypeError):
        # 忽略無法解析為JSON的行
        pass
    return None

def analyze_dqn_training(log_file, title, output_dir):
    """分析DQN訓練日誌並生成圖表，日誌中包含JSON格式的摘要。"""
    print(f"Analyzing DQN training log with JSON parsing: {log_file}")
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)
    
    episodes_data = []
    try:
        # 使用 'latin-1' 編碼來避免 UnicodeDecodeError
        with open(log_file, 'r', encoding='latin-1') as f:
            for line in f:
                parsed_data = parse_dqn_log_line_as_json(line)
                if parsed_data:
                    episodes_data.append(parsed_data)
    except FileNotFoundError:
        print(f"Error: Log file not found at {log_file}")
        return

    if not episodes_data:
        print("No valid JSON summary data found in log file.")
        return

    # 添加 episode 序號
    for i, episode in enumerate(episodes_data):
        episode['episode_num'] = i + 1

    df = pd.DataFrame(episodes_data)
    
    # 處理 global reward。在 global 模式下，'total_reward' 欄位可能是0，
    # 真正的獎勵可能記錄在別處或需要從其他指標計算。
    # 這裡我們先繪製它，如果全為0，會在圖上顯示。
    # 在論文分析時，需要特別說明 global reward 的評估方式。
    
    # 重命名列以匹配繪圖函數的期望
    df = df.rename(columns={
        'episode_num': 'episode',
        'total_reward': 'reward',
        'avg_loss': 'loss',
        'avg_q_value': 'q_value'
    })

    # 確保所有需要的列都存在
    required_cols = ['episode', 'reward', 'loss', 'q_value']
    if not all(col in df.columns for col in required_cols):
        print(f"Missing one of the required columns in the data: {required_cols}")
        return

    # 清理 'loss' 中的極端值以便於觀察
    if not df['loss'].empty and df['loss'].quantile(0.99) > 0 :
        q99 = df['loss'].quantile(0.99)
        df_plot = df[df['loss'] <= q99].copy()
    else:
        df_plot = df.copy()

    # 將 episode 設為索引
    df_plot.set_index('episode', inplace=True)
    
    # 重新命名列以供繪圖函數使用
    df_plot.rename(columns={
        'reward': 'Total Reward',
        'loss': 'Average Loss',
        'q_value': 'Average Q-Value'
    }, inplace=True)


    plot_dqn_training_from_data(df_plot, title, output_dir)


def plot_dqn_training_from_data(df, title, output_dir):
    """從DataFrame生成DQN訓練圖表。"""
    fig, axes = plt.subplots(3, 1, figsize=(14, 20), sharex=True)
    fig.suptitle(f'DQN Training Progression: {title}', fontsize=18, fontweight='bold')

    # 1. 總獎勵 (Total Reward)
    ax1 = axes[0]
    ax1.plot(df.index, df['Total Reward'], label='Total Reward per Episode', color='royalblue')
    reward_moving_avg = df['Total Reward'].rolling(window=50, min_periods=1).mean()
    ax1.plot(df.index, reward_moving_avg, label='50-Episode Moving Average', color='cyan', linestyle='--')
    ax1.set_ylabel('Total Reward')
    ax1.set_title('Episode Reward')
    ax1.legend()
    ax1.grid(True, which='both', linestyle='--', linewidth=0.5)

    # 2. 平均損失 (Average Loss)
    ax2 = axes[1]
    ax2.plot(df.index, df['Average Loss'], label='Average Loss per Episode', color='orangered', alpha=0.6)
    loss_moving_avg = df['Average Loss'].rolling(window=50, min_periods=1).mean()
    ax2.plot(df.index, loss_moving_avg, label='50-Episode Moving Average', color='darkorange', linestyle='--')
    ax2.set_ylabel('Average Loss')
    ax2.set_title('Training Loss')
    # 損失通常跨越多個數量級，使用對數座標軸，但要處理0或負值
    if (df['Average Loss'] > 0).all():
        ax2.set_yscale('log')
    ax2.legend()
    ax2.grid(True, which='both', linestyle='--', linewidth=0.5)

    # 3. 平均Q值 (Average Q-Value)
    ax3 = axes[2]
    ax3.plot(df.index, df['Average Q-Value'], label='Average Q-Value per Episode', color='forestgreen')
    q_moving_avg = df['Average Q-Value'].rolling(window=50, min_periods=1).mean()
    ax3.plot(df.index, q_moving_avg, label='50-Episode Moving Average', color='lime', linestyle='--')
    ax3.set_xlabel('Episode Number')
    ax3.set_ylabel('Average Q-Value')
    ax3.set_title('Average Q-Value')
    ax3.legend()
    ax3.grid(True, which='both', linestyle='--', linewidth=0.5)

    plt.tight_layout(rect=[0, 0.03, 1, 0.96])
    
    file_title = title.replace(" ", "_").replace("(", "").replace(")", "")
    output_path = output_dir / f'DQN_Training_{file_title}.png'
    plt.savefig(output_path, dpi=300)
    plt.close()
    print(f"DQN training plot saved to {output_path}")


def analyze_nerl_evolution(experiment_dir, title, output_dir):
    """分析單個NERL實驗的演化過程。"""
    print(f"Analyzing NERL evolution for: {title}")
    experiment_path = Path(experiment_dir)
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    generation_data = []
    for gen_dir in sorted(experiment_path.glob('gen???')):
        fitness_file = gen_dir / 'fitness_scores.json'
        if fitness_file.exists():
            try:
                with open(fitness_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                generation = data.get('generation')
                all_fitness = data.get('all_fitness')
                
                if generation is not None and all_fitness:
                    generation_data.append({
                        'generation': generation,
                        'max_fitness': np.max(all_fitness),
                        'mean_fitness': np.mean(all_fitness),
                        'min_fitness': np.min(all_fitness),
                        'std_fitness': np.std(all_fitness)
                    })
            except (json.JSONDecodeError, TypeError) as e:
                print(f"  Warning: Could not process {fitness_file}. Error: {e}")

    if not generation_data:
        print("  No valid generation data found.")
        return

    df = pd.DataFrame(generation_data).sort_values('generation')

    # Plotting the evolution curve
    plt.figure(figsize=(15, 8))
    
    # Plotting the mean fitness
    plt.plot(df['generation'], df['mean_fitness'], label='Mean Fitness', color='b', marker='o')
    
    # Filling the area between max and min fitness to show diversity
    plt.fill_between(df['generation'], df['min_fitness'], df['max_fitness'], 
                     alpha=0.2, color='lightblue', label='Fitness Range (Min-Max)')
    
    # Plotting the max fitness for each generation
    plt.plot(df['generation'], df['max_fitness'], label='Max Fitness', color='g', linestyle='--', marker='^', markersize=4)

    plt.title(f'NERL Evolutionary Process: {title}', fontsize=16)
    plt.xlabel('Generation')
    plt.ylabel('Fitness Score')
    plt.legend()
    plt.grid(True)
    
    file_title = title.replace(" ", "_").replace("/", "_").replace("(", "").replace(")", "")
    plot_save_path = output_path / f'NERL_Evolution_{file_title}.png'
    plt.savefig(plot_save_path, dpi=300)
    plt.close()
    
    print(f"  Evolution plot saved to {plot_save_path}")


def analyze_nerl_elite_evolution(experiment_dir, title, output_dir):
    """
    分析單個NERL實驗中，每一代精英個體的KPI演化過程。
    為每個KPI生成獨立的圖表，並計算線性回歸趨勢。
    """
    print(f"Analyzing NERL elite evolution for: {title}")
    experiment_path = Path(experiment_dir)
    # 為每個實驗創建一個專屬的子目錄
    exp_output_dir = Path(output_dir) / f"Elite_KPI_Evolution_{title}"
    exp_output_dir.mkdir(exist_ok=True)

    elite_kpi_data = []
    for gen_dir in sorted(experiment_path.glob('gen???')):
        fitness_file = gen_dir / 'fitness_scores.json'
        if fitness_file.exists():
            try:
                with open(fitness_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                generation = data.get('generation')
                best_metrics = data.get('best_individual_metrics')
                best_fitness = data.get('best_fitness')
                
                if generation is not None and best_metrics and best_fitness is not None:
                    record = {'generation': generation, 'best_fitness': best_fitness}
                    record.update(best_metrics)
                    elite_kpi_data.append(record)
                else:
                    print(f"  Warning: Skipping gen {generation or 'N/A'}. Missing data.")
            except (json.JSONDecodeError, TypeError) as e:
                print(f"  Warning: Could not process {fitness_file}. Error: {e}. Skipping.")

    if not elite_kpi_data:
        print("  No valid elite KPI data found.")
        return

    df = pd.DataFrame(elite_kpi_data).sort_values('generation')
    
    kpis_to_plot = {
        'best_fitness': 'Best Fitness',
        'completion_rate': 'Completion Rate',
        'energy_per_order': 'Energy per Order',
        'total_stop_go_events': 'Total Stop-Go Events',
        'signal_switch_count': 'Signal Switch Count',
        'avg_intersection_congestion': 'Avg. Intersection Congestion'
    }

    # 定義趨勢的好壞 (True: 越高越好, False: 越低越好)
    kpi_trend_is_good_if_positive = {
        'best_fitness': True,
        'completion_rate': True,
        'energy_per_order': False,
        'total_stop_go_events': False,
        'signal_switch_count': False,
        'avg_intersection_congestion': False
    }

    trend_report_lines = [f"Trend Analysis Report for: {title}\n" + "="*50]

    for kpi_key, kpi_title in kpis_to_plot.items():
        if kpi_key not in df.columns or df[kpi_key].isnull().all():
            continue

        plt.figure(figsize=(12, 7))
        ax = plt.gca()

        # 原始數據點
        ax.plot(df['generation'], df[kpi_key], marker='.', linestyle='-', label=kpi_title, alpha=0.6)
        
        # 5代移動平均線
        moving_avg = df[kpi_key].rolling(window=5, min_periods=1).mean()
        ax.plot(df['generation'], moving_avg, linestyle='--', label='5-Gen Moving Avg.')

        # 線性回歸趨勢線
        x = df['generation']
        y = df[kpi_key]
        # 忽略NaN值進行回歸計算
        valid_indices = ~np.isnan(y)
        if np.any(valid_indices):
            m, b = np.polyfit(x[valid_indices], y[valid_indices], 1)
            ax.plot(x, m*x + b, 'r--', label=f'Linear Trend (Slope: {m:.4f})')
            
            # 判斷趨勢好壞
            is_positive_good = kpi_trend_is_good_if_positive[kpi_key]
            if (m > 0 and is_positive_good) or (m < 0 and not is_positive_good):
                trend_assessment = "Desirable Trend (正向發展)"
            elif m == 0:
                trend_assessment = "Neutral Trend (趨勢持平)"
            else:
                trend_assessment = "Undesirable Trend (逆向發展)"
            
            trend_report_lines.append(f"\n- {kpi_title}:")
            trend_report_lines.append(f"  - Slope: {m:.6f}")
            trend_report_lines.append(f"  - Assessment: {trend_assessment}")


        ax.set_title(f'Elite KPI Evolution: {kpi_title}\n({title})', fontsize=16)
        ax.set_xlabel('Generation')
        ax.set_ylabel(kpi_title)
        ax.grid(True, which='both', linestyle='--', linewidth=0.5)
        ax.legend()
        
        plt.tight_layout()
        plot_save_path = exp_output_dir / f'{kpi_key}.png'
        plt.savefig(plot_save_path, dpi=300)
        plt.close()

    # 保存趨勢報告
    report_path = exp_output_dir / 'trend_report.txt'
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(trend_report_lines))

    print(f"  Individual KPI plots and trend report saved to {exp_output_dir}")


def analyze_nerl_final_comparison(root_log_dir, output_dir):
    """
    比較所有NERL實驗組最終一代（冠軍模型）的KPI。
    """
    print("Analyzing final generation KPIs for all NERL experiments...")
    root_path = Path(root_log_dir)
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    final_kpi_data = []
    # 遍歷所有NERL實驗目錄
    for exp_dir in sorted(root_path.glob('*nerl*')):
        if not exp_dir.is_dir():
            continue

        # 定位到最後一代的目錄
        gen_dirs = sorted(exp_dir.glob('gen???'))
        if not gen_dirs:
            print(f"  Warning: No generation directories found in {exp_dir.name}. Skipping.")
            continue
        last_gen_dir = gen_dirs[-1]
        
        fitness_file = last_gen_dir / 'fitness_scores.json'
        if fitness_file.exists():
            try:
                with open(fitness_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                best_metrics = data.get('best_individual_metrics')
                best_fitness = data.get('best_fitness')

                if best_metrics and best_fitness is not None:
                    record = {'experiment': exp_dir.name}
                    record.update(best_metrics)
                    record['best_fitness'] = best_fitness
                    final_kpi_data.append(record)
                else:
                    print(f"  Warning: No final metrics for {exp_dir.name}. Skipping.")
            except (json.JSONDecodeError, TypeError) as e:
                print(f"  Warning: Could not process {fitness_file}. Error: {e}")

    if not final_kpi_data:
        print("No final KPI data found for any experiment.")
        return

    df = pd.DataFrame(final_kpi_data)

    # --- Plotting ---
    kpis_to_plot = {
        'best_fitness': 'Best Fitness',
        'completion_rate': 'Completion Rate',
        'energy_per_order': 'Energy per Order',
        'total_stop_go_events': 'Total Stop-Go Events',
        'signal_switch_count': 'Signal Switch Count',
        'avg_intersection_congestion': 'Avg. Intersection Congestion'
    }

    # 顏色編碼
    def get_color(name):
        if 'global' in name: # Global reward -> Green series
            return 'seagreen' if 'a' in name else 'limegreen'
        else: # Step reward -> Blue series
            return 'royalblue' if 'a' in name else 'skyblue'
    
    # 樣式編碼 for ticks
    def get_hatch(name):
        return '/' if '8000' in name else ''

    for kpi, title in kpis_to_plot.items():
        if kpi not in df.columns:
            continue
        
        plt.figure(figsize=(18, 10))
        # 排序以獲得更好的視覺效果
        df_sorted = df.sort_values(by=kpi, ascending=False if kpi != 'energy_per_order' else True)
        
        bars = plt.bar(df_sorted['experiment'], df_sorted[kpi], 
                       color=[get_color(name) for name in df_sorted['experiment']],
                       hatch=[get_hatch(name) for name in df_sorted['experiment']],
                       edgecolor='black')

        plt.title(f'Final Elite Model Comparison: {title}', fontsize=16)
        plt.ylabel(title)
        plt.xlabel('Experiment Group')
        plt.xticks(rotation=45, ha="right")
        plt.grid(axis='y', linestyle='--', alpha=0.7)

        # 添加圖例說明
        from matplotlib.patches import Patch
        legend_elements = [
            Patch(facecolor='royalblue', edgecolor='black', label='Step Reward (Variant A)'),
            Patch(facecolor='skyblue', edgecolor='black', label='Step Reward (Variant B)'),
            Patch(facecolor='seagreen', edgecolor='black', label='Global Reward (Variant A)'),
            Patch(facecolor='limegreen', edgecolor='black', label='Global Reward (Variant B)'),
            Patch(facecolor='white', edgecolor='black', hatch='/', label='8000 Ticks Evaluation')
        ]
        plt.legend(handles=legend_elements, bbox_to_anchor=(1.05, 1), loc='upper left')

        plt.tight_layout()
        plot_save_path = output_path / f'NERL_Final_Comparison_{kpi}.png'
        plt.savefig(plot_save_path, dpi=300)
        plt.close()
        print(f"  Comparison plot for {kpi} saved to {plot_save_path}")

def main():
    parser = argparse.ArgumentParser(description="RMFS 數據分析與視覺化工具")
    parser.add_argument('analysis_type', choices=['eval', 'training', 'nerl-evolution', 'nerl-elite-kpi', 'nerl-final-comparison'], help='要執行的分析類型')
    parser.add_argument('--root_dir', '-r', help='評估結果的根目錄 (用於 "eval" 分析)')
    parser.add_argument('--output', '-o', help='輸出目錄')
    parser.add_argument('--log_file', '-l', help='訓練日誌檔案路徑 (用於 "training" 分析)')
    parser.add_argument('--title', '-t', default='Training Analysis', help='圖表標題 (用於 "training" 分析)')
    parser.add_argument('--exp_dir', help='單個實驗目錄 (用於 "nerl-evolution" 分析)')
    parser.add_argument('--log_dir', help='包含所有NERL實驗日誌的根目錄 (用於 "nerl-final-comparison")')
    
    args = parser.parse_args()
    
    if args.analysis_type == 'eval':
        if not args.root_dir:
            parser.error('"eval" 分析需要 --root_dir 參數。')
        output_dir = args.output if args.output else Path(args.root_dir) / "aggregated_results"
        analyzer = PaperAnalyzer(args.root_dir, output_dir)
        analyzer.run_analysis()
    
    elif args.analysis_type == 'training':
        if not args.log_file:
            parser.error('"training" 分析需要 --log_file 參數。')
        output_dir = args.output if args.output else Path(args.log_file).parent / "analysis_results"
        # 假設是DQN日誌，未來可以擴充
        analyze_dqn_training(args.log_file, args.title, output_dir)

    elif args.analysis_type == 'nerl-evolution':
        if not args.exp_dir:
            parser.error('"nerl-evolution" 分析需要 --exp_dir 參數。')
        output_dir = args.output if args.output else Path(args.exp_dir).parent / "analysis_results"
        title = args.title if args.title else Path(args.exp_dir).name
        analyze_nerl_evolution(args.exp_dir, title, output_dir)

    elif args.analysis_type == 'nerl-elite-kpi':
        if not args.exp_dir:
            parser.error('"nerl-elite-kpi" 分析需要 --exp_dir 參數。')
        output_dir = args.output if args.output else Path(args.exp_dir).parent / "analysis_results"
        title = args.title if args.title else Path(args.exp_dir).name
        analyze_nerl_elite_evolution(args.exp_dir, title, output_dir)

    elif args.analysis_type == 'nerl-final-comparison':
        if not args.log_dir:
            parser.error('"nerl-final-comparison" 分析需要 --log_dir 參數。')
        output_dir = args.output if args.output else Path(args.log_dir) / "analysis_results"
        analyze_nerl_final_comparison(args.log_dir, output_dir)


if __name__ == "__main__":
    main()
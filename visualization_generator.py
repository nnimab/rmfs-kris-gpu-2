#!/usr/bin/env python3
"""
RMFS 訓練結果可視化生成器
自動生成論文需要的所有圖表
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

# 設置中文字體和圖表風格
plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False
sns.set_style("whitegrid")
plt.style.use('seaborn-v0_8')

class RMFSVisualizer:
    def __init__(self, results_dir="models/training_runs"):
        self.results_dir = Path(results_dir)
        self.output_dir = Path("analysis_results")
        self.output_dir.mkdir(exist_ok=True)
        
    def load_training_data(self):
        """載入所有訓練結果數據"""
        training_data = {}
        
        for run_dir in self.results_dir.iterdir():
            if not run_dir.is_dir():
                continue
                
            metadata_file = run_dir / "metadata.json"
            if not metadata_file.exists():
                continue
                
            try:
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                
                # 解析運行名稱
                run_name = run_dir.name
                controller_type = metadata.get('controller_type', 'unknown')
                reward_mode = metadata.get('reward_mode', 'unknown')
                
                # 載入世代數據（如果是NERL）
                generations_data = []
                if controller_type == 'nerl':
                    for gen_dir in sorted(run_dir.glob("gen*")):
                        fitness_file = gen_dir / "fitness_scores.json"
                        if fitness_file.exists():
                            with open(fitness_file, 'r', encoding='utf-8') as f:
                                gen_data = json.load(f)
                                generations_data.append(gen_data)
                
                training_data[run_name] = {
                    'metadata': metadata,
                    'controller_type': controller_type,
                    'reward_mode': reward_mode,
                    'generations': generations_data,
                    'run_dir': run_dir
                }
                
            except Exception as e:
                print(f"警告: 無法載入 {run_dir}: {e}")
                
        return training_data
    
    def plot_nerl_training_progress(self, training_data):
        """繪製NERL訓練進度圖"""
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('NERL 訓練進度分析', fontsize=16, fontweight='bold')
        
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']
        color_idx = 0
        
        for run_name, data in training_data.items():
            if data['controller_type'] != 'nerl' or not data['generations']:
                continue
                
            generations = data['generations']
            gen_numbers = [g['generation'] for g in generations]
            best_fitness = [g['best_fitness'] for g in generations]
            avg_fitness = [np.mean(g['all_fitness']) for g in generations]
            completed_orders = [g.get('best_individual_metrics', {}).get('completed_orders', 0) for g in generations]
            energy_per_order = [g.get('best_individual_metrics', {}).get('energy_per_order', 0) for g in generations]
            
            color = colors[color_idx % len(colors)]
            label = f"{data['reward_mode'].upper()}"
            
            # 子圖1: 適應度變化
            axes[0,0].plot(gen_numbers, best_fitness, 'o-', color=color, label=f'{label} (最佳)', linewidth=2, markersize=6)
            axes[0,0].plot(gen_numbers, avg_fitness, '--', color=color, alpha=0.7, label=f'{label} (平均)')
            
            # 子圖2: 完成訂單數
            axes[0,1].plot(gen_numbers, completed_orders, 's-', color=color, label=label, linewidth=2, markersize=6)
            
            # 子圖3: 能源效率
            if any(e > 0 for e in energy_per_order):
                axes[1,0].plot(gen_numbers, energy_per_order, '^-', color=color, label=label, linewidth=2, markersize=6)
            
            # 子圖4: 適應度分佈（最後一代）
            if generations:
                last_gen_fitness = generations[-1]['all_fitness']
                # 過濾掉極端值
                filtered_fitness = [f for f in last_gen_fitness if f > -1000000]
                if filtered_fitness:
                    axes[1,1].hist(filtered_fitness, alpha=0.6, label=label, bins=10, color=color)
            
            color_idx += 1
        
        # 設置子圖
        axes[0,0].set_title('適應度進化曲線', fontweight='bold')
        axes[0,0].set_xlabel('世代數')
        axes[0,0].set_ylabel('適應度分數')
        axes[0,0].legend()
        axes[0,0].grid(True, alpha=0.3)
        
        axes[0,1].set_title('訂單完成數進化', fontweight='bold')
        axes[0,1].set_xlabel('世代數')
        axes[0,1].set_ylabel('完成訂單數')
        axes[0,1].legend()
        axes[0,1].grid(True, alpha=0.3)
        
        axes[1,0].set_title('能源效率進化', fontweight='bold')
        axes[1,0].set_xlabel('世代數')
        axes[1,0].set_ylabel('每訂單能源消耗')
        axes[1,0].legend()
        axes[1,0].grid(True, alpha=0.3)
        
        axes[1,1].set_title('最終世代適應度分佈', fontweight='bold')
        axes[1,1].set_xlabel('適應度分數')
        axes[1,1].set_ylabel('個體數量')
        axes[1,1].legend()
        axes[1,1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # 保存圖表
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        filename = f"nerl_analysis_{timestamp}.png"
        filepath = self.output_dir / filename
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        print(f"✅ NERL訓練進度圖已保存: {filepath}")
        
        return filepath
    
    def plot_final_comparison(self, training_data):
        """繪製最終性能比較圖"""
        # 收集所有控制器的最終性能數據
        comparison_data = []
        
        for run_name, data in training_data.items():
            controller_type = data['controller_type']
            reward_mode = data['reward_mode']
            metadata = data['metadata']
            
            # 獲取最終結果
            results = metadata.get('results', {})
            
            if controller_type == 'nerl':
                completed_orders = results.get('completed_orders_final_eval', 0)
                total_energy = results.get('total_energy_final_eval', 0)
                best_fitness = results.get('best_fitness', 0)
                
                # 從最後一代獲取詳細指標
                if data['generations']:
                    last_gen = data['generations'][-1]
                    metrics = last_gen.get('best_individual_metrics', {})
                    completion_rate = metrics.get('completion_rate', 0)
                    avg_wait_time = metrics.get('avg_wait_time', 0)
                    energy_per_order = metrics.get('energy_per_order', 0) if completed_orders > 0 else 0
                else:
                    completion_rate = completed_orders / 50 if completed_orders > 0 else 0
                    avg_wait_time = 0
                    energy_per_order = total_energy / completed_orders if completed_orders > 0 else 0
                    
            elif controller_type == 'dqn':
                completed_orders = results.get('completed_orders', 0)
                total_energy = 0  # DQN結果中可能沒有這個
                best_fitness = results.get('cumulative_step_reward', 0)
                completion_rate = completed_orders / 50 if completed_orders > 0 else 0
                avg_wait_time = 0
                energy_per_order = 0
            
            comparison_data.append({
                'name': f"{controller_type.upper()}_{reward_mode}",
                'controller_type': controller_type,
                'reward_mode': reward_mode,
                'completed_orders': completed_orders,
                'completion_rate': completion_rate * 100,  # 轉換為百分比
                'total_energy': total_energy,
                'energy_per_order': energy_per_order,
                'avg_wait_time': avg_wait_time,
                'best_fitness': best_fitness
            })
        
        if not comparison_data:
            print("警告: 沒有找到可比較的數據")
            return None
        
        # 創建比較圖表
        fig, axes = plt.subplots(2, 3, figsize=(18, 12))
        fig.suptitle('控制器性能比較分析', fontsize=16, fontweight='bold')
        
        df = pd.DataFrame(comparison_data)
        
        # 設置顏色
        colors = {'nerl': '#2E8B57', 'dqn': '#4169E1'}
        
        # 子圖1: 訂單完成數
        ax1 = axes[0,0]
        bars1 = ax1.bar(range(len(df)), df['completed_orders'], 
                       color=[colors.get(ct, '#808080') for ct in df['controller_type']])
        ax1.set_title('訂單完成數比較', fontweight='bold')
        ax1.set_ylabel('完成訂單數')
        ax1.set_xticks(range(len(df)))
        ax1.set_xticklabels(df['name'], rotation=45, ha='right')
        
        # 添加數值標籤
        for i, bar in enumerate(bars1):
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                    f'{int(height)}', ha='center', va='bottom', fontweight='bold')
        
        # 子圖2: 完成率
        ax2 = axes[0,1]
        bars2 = ax2.bar(range(len(df)), df['completion_rate'],
                       color=[colors.get(ct, '#808080') for ct in df['controller_type']])
        ax2.set_title('訂單完成率比較', fontweight='bold')
        ax2.set_ylabel('完成率 (%)')
        ax2.set_xticks(range(len(df)))
        ax2.set_xticklabels(df['name'], rotation=45, ha='right')
        
        for i, bar in enumerate(bars2):
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                    f'{height:.1f}%', ha='center', va='bottom', fontweight='bold')
        
        # 子圖3: 能源效率（如果有數據）
        ax3 = axes[0,2]
        energy_data = df[df['energy_per_order'] > 0]
        if not energy_data.empty:
            bars3 = ax3.bar(range(len(energy_data)), energy_data['energy_per_order'],
                           color=[colors.get(ct, '#808080') for ct in energy_data['controller_type']])
            ax3.set_title('能源效率比較', fontweight='bold')
            ax3.set_ylabel('每訂單能源消耗')
            ax3.set_xticks(range(len(energy_data)))
            ax3.set_xticklabels(energy_data['name'], rotation=45, ha='right')
            
            for i, bar in enumerate(bars3):
                height = bar.get_height()
                ax3.text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                        f'{height:.0f}', ha='center', va='bottom', fontweight='bold')
        else:
            ax3.text(0.5, 0.5, '暫無能源數據', ha='center', va='center', transform=ax3.transAxes)
            ax3.set_title('能源效率比較', fontweight='bold')
        
        # 子圖4: 適應度比較
        ax4 = axes[1,0]
        bars4 = ax4.bar(range(len(df)), df['best_fitness'],
                       color=[colors.get(ct, '#808080') for ct in df['controller_type']])
        ax4.set_title('最佳適應度比較', fontweight='bold')
        ax4.set_ylabel('適應度分數')
        ax4.set_xticks(range(len(df)))
        ax4.set_xticklabels(df['name'], rotation=45, ha='right')
        
        for i, bar in enumerate(bars4):
            height = bar.get_height()
            ax4.text(bar.get_x() + bar.get_width()/2., height + abs(height)*0.01,
                    f'{height:.2f}', ha='center', va='bottom', fontweight='bold')
        
        # 子圖5: 控制器類型分組比較
        ax5 = axes[1,1]
        nerl_data = df[df['controller_type'] == 'nerl']
        dqn_data = df[df['controller_type'] == 'dqn']
        
        if not nerl_data.empty and not dqn_data.empty:
            categories = ['完成訂單數', '完成率(%)']
            nerl_avg = [nerl_data['completed_orders'].mean(), nerl_data['completion_rate'].mean()]
            dqn_avg = [dqn_data['completed_orders'].mean(), dqn_data['completion_rate'].mean()]
            
            x = np.arange(len(categories))
            width = 0.35
            
            ax5.bar(x - width/2, nerl_avg, width, label='NERL', color=colors['nerl'])
            ax5.bar(x + width/2, dqn_avg, width, label='DQN', color=colors['dqn'])
            
            ax5.set_title('NERL vs DQN 平均性能', fontweight='bold')
            ax5.set_xticks(x)
            ax5.set_xticklabels(categories)
            ax5.legend()
            
            # 添加數值標籤
            for i, (n, d) in enumerate(zip(nerl_avg, dqn_avg)):
                ax5.text(i - width/2, n + n*0.01, f'{n:.1f}', ha='center', va='bottom')
                ax5.text(i + width/2, d + d*0.01, f'{d:.1f}', ha='center', va='bottom')
        
        # 子圖6: 獎勵模式比較
        ax6 = axes[1,2]
        step_data = df[df['reward_mode'] == 'step']
        global_data = df[df['reward_mode'] == 'global']
        
        if not step_data.empty and not global_data.empty:
            categories = ['完成訂單數', '完成率(%)']
            step_avg = [step_data['completed_orders'].mean(), step_data['completion_rate'].mean()]
            global_avg = [global_data['completed_orders'].mean(), global_data['completion_rate'].mean()]
            
            x = np.arange(len(categories))
            width = 0.35
            
            ax6.bar(x - width/2, step_avg, width, label='Step Reward', color='#FF6B6B')
            ax6.bar(x + width/2, global_avg, width, label='Global Reward', color='#4ECDC4')
            
            ax6.set_title('Step vs Global 獎勵模式比較', fontweight='bold')
            ax6.set_xticks(x)
            ax6.set_xticklabels(categories)
            ax6.legend()
            
            # 添加數值標籤
            for i, (s, g) in enumerate(zip(step_avg, global_avg)):
                ax6.text(i - width/2, s + s*0.01, f'{s:.1f}', ha='center', va='bottom')
                ax6.text(i + width/2, g + g*0.01, f'{g:.1f}', ha='center', va='bottom')
        
        plt.tight_layout()
        
        # 保存圖表
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        filename = f"final_comparison_{timestamp}.png"
        filepath = self.output_dir / filename
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        print(f"✅ 最終比較圖已保存: {filepath}")
        
        return filepath, df
    
    def generate_report(self, training_data, comparison_df=None):
        """生成文字報告"""
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        report_file = self.output_dir / f"nerl_report_{timestamp}.txt"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("="*60 + "\n")
            f.write("RMFS 神經演化強化學習 (NERL) 訓練報告\n")
            f.write("="*60 + "\n")
            f.write(f"報告生成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # 訓練概況
            f.write("1. 訓練概況\n")
            f.write("-"*30 + "\n")
            f.write(f"總訓練運行數: {len(training_data)}\n")
            
            nerl_runs = [d for d in training_data.values() if d['controller_type'] == 'nerl']
            dqn_runs = [d for d in training_data.values() if d['controller_type'] == 'dqn']
            
            f.write(f"NERL 訓練: {len(nerl_runs)} 次\n")
            f.write(f"DQN 訓練: {len(dqn_runs)} 次\n\n")
            
            # NERL 詳細分析
            if nerl_runs:
                f.write("2. NERL 訓練詳細分析\n")
                f.write("-"*30 + "\n")
                
                for run_name, data in training_data.items():
                    if data['controller_type'] != 'nerl':
                        continue
                        
                    metadata = data['metadata']
                    config = metadata.get('config', {})
                    results = metadata.get('results', {})
                    
                    f.write(f"\n運行: {run_name}\n")
                    f.write(f"  獎勵模式: {data['reward_mode']}\n")
                    f.write(f"  訓練時間: {metadata.get('start_time')} - {metadata.get('end_time')}\n")
                    f.write(f"  世代數: {config.get('generations', 'N/A')}\n")
                    f.write(f"  族群大小: {config.get('population_size', 'N/A')}\n")
                    f.write(f"  評估時長: {config.get('evaluation_ticks', 'N/A')} ticks\n")
                    f.write(f"  最佳適應度: {results.get('best_fitness', 'N/A'):.4f}\n")
                    f.write(f"  完成訂單數: {results.get('completed_orders_final_eval', 'N/A')}\n")
                    f.write(f"  總能源消耗: {results.get('total_energy_final_eval', 'N/A'):.2f}\n")
                    
                    if data['generations']:
                        last_gen = data['generations'][-1]
                        metrics = last_gen.get('best_individual_metrics', {})
                        f.write(f"  完成率: {metrics.get('completion_rate', 0)*100:.1f}%\n")
                        f.write(f"  平均等待時間: {metrics.get('avg_wait_time', 0):.1f} ticks\n")
                        f.write(f"  機器人利用率: {metrics.get('robot_utilization', 0)*100:.1f}%\n")
            
            # 性能比較
            if comparison_df is not None:
                f.write("\n\n3. 性能比較總結\n")
                f.write("-"*30 + "\n")
                
                best_completion = comparison_df.loc[comparison_df['completed_orders'].idxmax()]
                best_rate = comparison_df.loc[comparison_df['completion_rate'].idxmax()]
                
                f.write(f"最佳完成訂單數: {best_completion['name']} ({int(best_completion['completed_orders'])} 訂單)\n")
                f.write(f"最佳完成率: {best_rate['name']} ({best_rate['completion_rate']:.1f}%)\n")
                
                # 獎勵模式比較
                step_data = comparison_df[comparison_df['reward_mode'] == 'step']
                global_data = comparison_df[comparison_df['reward_mode'] == 'global']
                
                if not step_data.empty and not global_data.empty:
                    f.write(f"\nStep Reward 平均完成率: {step_data['completion_rate'].mean():.1f}%\n")
                    f.write(f"Global Reward 平均完成率: {global_data['completion_rate'].mean():.1f}%\n")
                    
                    if global_data['completion_rate'].mean() > step_data['completion_rate'].mean():
                        f.write("結論: Global Reward 模式表現更佳\n")
                    else:
                        f.write("結論: Step Reward 模式表現更佳\n")
            
            # 建議
            f.write("\n\n4. 改進建議\n")
            f.write("-"*30 + "\n")
            f.write("• 增加訓練世代數以獲得更好的收斂\n")
            f.write("• 調整獎勵函數權重以提高完成率\n")
            f.write("• 考慮增加族群大小以提高探索能力\n")
            f.write("• 實施更複雜的防死鎖機制\n")
            
        print(f"✅ 訓練報告已保存: {report_file}")
        return report_file
    
    def run_analysis(self):
        """運行完整分析"""
        print("🔍 開始分析訓練結果...")
        
        # 載入數據
        training_data = self.load_training_data()
        if not training_data:
            print("❌ 未找到訓練數據")
            return
            
        print(f"✅ 載入了 {len(training_data)} 個訓練運行")
        
        # 生成圖表
        nerl_chart = self.plot_nerl_training_progress(training_data)
        comparison_chart, comparison_df = self.plot_final_comparison(training_data)
        
        # 生成報告
        report_file = self.generate_report(training_data, comparison_df)
        
        print("\n" + "="*50)
        print("📊 分析完成！生成的文件:")
        print(f"  • NERL訓練圖表: {nerl_chart}")
        print(f"  • 性能比較圖表: {comparison_chart}")
        print(f"  • 詳細報告: {report_file}")
        print("="*50)
        
        return {
            'nerl_chart': nerl_chart,
            'comparison_chart': comparison_chart,
            'report': report_file,
            'data': training_data
        }

def main():
    parser = argparse.ArgumentParser(description="RMFS訓練結果可視化分析")
    parser.add_argument('--results_dir', default='models/training_runs', 
                       help='訓練結果目錄路徑')
    
    args = parser.parse_args()
    
    visualizer = RMFSVisualizer(args.results_dir)
    results = visualizer.run_analysis()
    
    return results

if __name__ == "__main__":
    main()
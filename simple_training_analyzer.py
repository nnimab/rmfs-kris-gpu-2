#!/usr/bin/env python3
"""
簡單的訓練結果分析工具

直接讀取 models/training_runs/ 下的數據，生成學習曲線
"""

import os
import json
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from datetime import datetime
import argparse

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False

def find_training_runs():
    """尋找所有訓練結果"""
    training_runs_dir = Path("models/training_runs")
    
    if not training_runs_dir.exists():
        print("❌ 未找到 models/training_runs 目錄")
        return []
    
    training_runs = []
    for subdir in training_runs_dir.iterdir():
        if subdir.is_dir():
            # 檢查是否有適應度數據或訓練日誌
            fitness_files = list(subdir.glob("gen*/fitness_scores.json"))
            log_files = list(subdir.glob("training.log"))
            
            if fitness_files or log_files:
                training_runs.append({
                    'name': subdir.name,
                    'path': subdir,
                    'fitness_files': sorted(fitness_files),
                    'log_files': log_files,
                    'timestamp': subdir.stat().st_mtime,
                    'agent_type': 'nerl' if 'nerl' in subdir.name else 'dqn'
                })
    
    return sorted(training_runs, key=lambda x: x['timestamp'], reverse=True)

def analyze_nerl_training(training_run):
    """分析 NERL 訓練結果"""
    print(f"\n🧬 分析 NERL 訓練: {training_run['name']}")
    
    if not training_run['fitness_files']:
        print("❌ 沒有適應度數據")
        return None
    
    # 讀取所有世代的適應度數據
    generations_data = []
    for fitness_file in training_run['fitness_files']:
        try:
            with open(fitness_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                generations_data.append(data)
        except Exception as e:
            print(f"❌ 讀取失敗 {fitness_file}: {e}")
            continue
    
    if not generations_data:
        return None
    
    # 整理數據
    df_data = []
    for gen_data in generations_data:
        generation = gen_data.get('generation', 0)
        best_fitness = gen_data.get('best_fitness', 0)
        all_fitness = gen_data.get('all_fitness', [])
        
        metrics = gen_data.get('best_individual_metrics', {})
        
        df_data.append({
            'generation': generation,
            'best_fitness': best_fitness,
            'avg_fitness': np.mean(all_fitness) if all_fitness else 0,
            'worst_fitness': min(all_fitness) if all_fitness else 0,
            'fitness_std': np.std(all_fitness) if all_fitness else 0,
            'diversity': np.std(all_fitness) / (abs(np.mean(all_fitness)) + 1e-6) if all_fitness else 0,
            'completed_orders': metrics.get('completed_orders', 0),
            'completion_rate': metrics.get('completion_rate', 0),
            'total_energy': metrics.get('total_energy_consumed', 0),
            'energy_per_order': metrics.get('energy_per_order', 0)
        })
    
    df = pd.DataFrame(df_data).sort_values('generation')
    
    # 生成圖表
    plot_nerl_results(training_run['name'], df)
    
    # 生成簡單報告
    generate_nerl_report(training_run['name'], df)
    
    return df

def plot_nerl_results(training_name, df):
    """繪製 NERL 結果"""
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    fig.suptitle(f'NERL 訓練分析 - {training_name}', fontsize=16)
    
    # 1. 適應度演化
    axes[0, 0].plot(df['generation'], df['best_fitness'], 'r-', linewidth=2, label='最佳適應度')
    axes[0, 0].plot(df['generation'], df['avg_fitness'], 'b--', alpha=0.7, label='平均適應度')
    axes[0, 0].fill_between(df['generation'], 
                           df['avg_fitness'] - df['fitness_std'],
                           df['avg_fitness'] + df['fitness_std'],
                           alpha=0.3, label='±1標準差')
    axes[0, 0].set_title('適應度演化')
    axes[0, 0].set_xlabel('世代')
    axes[0, 0].set_ylabel('適應度')
    axes[0, 0].legend()
    axes[0, 0].grid(True, alpha=0.3)
    
    # 2. 族群多樣性
    axes[0, 1].plot(df['generation'], df['diversity'], 'purple', linewidth=2)
    axes[0, 1].set_title('族群多樣性')
    axes[0, 1].set_xlabel('世代')
    axes[0, 1].set_ylabel('多樣性指數')
    axes[0, 1].grid(True, alpha=0.3)
    
    # 3. 完成訂單數
    if df['completed_orders'].sum() > 0:
        axes[0, 2].plot(df['generation'], df['completed_orders'], 'green', linewidth=2)
        axes[0, 2].set_title('完成訂單數')
        axes[0, 2].set_xlabel('世代')
        axes[0, 2].set_ylabel('完成訂單數')
        axes[0, 2].grid(True, alpha=0.3)
    else:
        axes[0, 2].text(0.5, 0.5, '無訂單完成數據', ha='center', va='center', 
                       transform=axes[0, 2].transAxes)
    
    # 4. 完成率
    if df['completion_rate'].sum() > 0:
        axes[1, 0].plot(df['generation'], df['completion_rate'], 'teal', linewidth=2)
        axes[1, 0].set_title('訂單完成率')
        axes[1, 0].set_xlabel('世代')
        axes[1, 0].set_ylabel('完成率')
        axes[1, 0].grid(True, alpha=0.3)
    else:
        axes[1, 0].text(0.5, 0.5, '無完成率數據', ha='center', va='center', 
                       transform=axes[1, 0].transAxes)
    
    # 5. 改進率
    if len(df) > 1:
        improvement_rates = df['best_fitness'].diff().fillna(0)
        axes[1, 1].bar(df['generation'], improvement_rates, 
                      color=['green' if x > 0 else 'red' for x in improvement_rates],
                      alpha=0.7)
        axes[1, 1].set_title('每代適應度改進')
        axes[1, 1].set_xlabel('世代')
        axes[1, 1].set_ylabel('適應度變化')
        axes[1, 1].axhline(y=0, color='black', linestyle='-', alpha=0.3)
        axes[1, 1].grid(True, alpha=0.3)
    
    # 6. 統計信息
    axes[1, 2].axis('off')
    stats_text = f"""
    訓練統計:
    總世代數: {len(df)}
    最佳適應度: {df['best_fitness'].max():.2f}
    最終適應度: {df['best_fitness'].iloc[-1]:.2f}
    平均改進: {(df['best_fitness'].iloc[-1] - df['best_fitness'].iloc[0]) / len(df):.2f}
    
    最終多樣性: {df['diversity'].iloc[-1]:.3f}
    """
    
    if df['completed_orders'].sum() > 0:
        stats_text += f"\n最多完成訂單: {df['completed_orders'].max()}"
        stats_text += f"\n最終完成訂單: {df['completed_orders'].iloc[-1]}"
    
    axes[1, 2].text(0.1, 0.9, stats_text, transform=axes[1, 2].transAxes, 
                   fontsize=10, verticalalignment='top')
    
    plt.tight_layout()
    
    # 保存圖表
    output_dir = Path("analysis_results")
    output_dir.mkdir(exist_ok=True)
    filename = f"nerl_analysis_{training_name}.png"
    filepath = output_dir / filename
    plt.savefig(filepath, dpi=300, bbox_inches='tight')
    print(f"📊 圖表已保存: {filepath}")
    plt.show()

def generate_nerl_report(training_name, df):
    """生成 NERL 文字報告"""
    output_dir = Path("analysis_results")
    output_dir.mkdir(exist_ok=True)
    
    report_path = output_dir / f"nerl_report_{training_name}.txt"
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(f"NERL 訓練分析報告\n")
        f.write(f"訓練: {training_name}\n")
        f.write(f"生成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("="*50 + "\n\n")
        
        # 基本統計
        f.write("基本統計:\n")
        f.write(f"  總世代數: {len(df)}\n")
        f.write(f"  最佳適應度: {df['best_fitness'].max():.4f}\n")
        f.write(f"  最終適應度: {df['best_fitness'].iloc[-1]:.4f}\n")
        f.write(f"  初始適應度: {df['best_fitness'].iloc[0]:.4f}\n")
        f.write(f"  總體改進: {df['best_fitness'].iloc[-1] - df['best_fitness'].iloc[0]:.4f}\n")
        f.write(f"  平均每代改進: {(df['best_fitness'].iloc[-1] - df['best_fitness'].iloc[0]) / len(df):.4f}\n\n")
        
        # 收斂性分析
        f.write("收斂性分析:\n")
        if len(df) >= 5:
            recent_improvement = df['best_fitness'].iloc[-1] - df['best_fitness'].iloc[-5]
            f.write(f"  最近5代改進: {recent_improvement:.4f}\n")
            
            if recent_improvement < 0.01:
                f.write("  狀態: 可能已收斂或停滯\n")
            else:
                f.write("  狀態: 仍在改進中\n")
        
        f.write(f"  最終多樣性: {df['diversity'].iloc[-1]:.4f}\n")
        if df['diversity'].iloc[-1] < 0.1:
            f.write("  多樣性: 較低，可能早熟收斂\n")
        else:
            f.write("  多樣性: 良好\n")
        
        f.write("\n")
        
        # 業務指標
        if df['completed_orders'].sum() > 0:
            f.write("業務指標:\n")
            f.write(f"  最多完成訂單: {df['completed_orders'].max()}\n")
            f.write(f"  最終完成訂單: {df['completed_orders'].iloc[-1]}\n")
            
            if df['completion_rate'].sum() > 0:
                f.write(f"  最高完成率: {df['completion_rate'].max():.2%}\n")
                f.write(f"  最終完成率: {df['completion_rate'].iloc[-1]:.2%}\n")
            f.write("\n")
        
        # 建議
        f.write("優化建議:\n")
        
        if recent_improvement < 0.01 and len(df) > 10:
            f.write("  - 適應度改進緩慢，考慮調整突變率或重啟訓練\n")
        
        if df['diversity'].iloc[-1] < 0.1:
            f.write("  - 族群多樣性低，建議增加突變率\n")
        
        if len(df) < 20:
            f.write("  - 訓練世代較少，建議增加訓練世代數\n")
        
        if df['completed_orders'].iloc[-1] == 0:
            f.write("  - 未完成任何訂單，檢查獎勵函數設計\n")
    
    print(f"📋 報告已保存: {report_path}")

def analyze_all_recent_trainings():
    """分析所有最近的訓練"""
    print("🔍 搜尋訓練結果...")
    
    training_runs = find_training_runs()
    print(f"找到 {len(training_runs)} 個訓練結果")
    
    if not training_runs:
        print("❌ 未找到任何訓練結果")
        return
    
    # 列出所有訓練
    print("\n📋 可用的訓練結果:")
    for i, run in enumerate(training_runs):
        timestamp = datetime.fromtimestamp(run['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
        fitness_count = len(run['fitness_files'])
        print(f"  {i+1}. {run['name']} ({run['agent_type'].upper()}) - {timestamp} - {fitness_count}個世代")
    
    # 分析每個 NERL 訓練
    nerl_runs = [run for run in training_runs if run['agent_type'] == 'nerl']
    
    if nerl_runs:
        print(f"\n🧬 開始分析 {len(nerl_runs)} 個 NERL 訓練...")
        
        for run in nerl_runs:
            try:
                df = analyze_nerl_training(run)
                if df is not None:
                    print(f"✅ {run['name']} 分析完成")
                else:
                    print(f"❌ {run['name']} 分析失敗")
            except Exception as e:
                print(f"❌ {run['name']} 分析出錯: {e}")
    
    # DQN 暫時跳過，主要關注 NERL
    dqn_runs = [run for run in training_runs if run['agent_type'] == 'dqn']
    if dqn_runs:
        print(f"\n📊 找到 {len(dqn_runs)} 個 DQN 訓練（暫時跳過分析）")

def main():
    parser = argparse.ArgumentParser(description='簡單訓練結果分析')
    parser.add_argument('--training', type=str, help='指定要分析的訓練名稱')
    args = parser.parse_args()
    
    if args.training:
        # 分析指定的訓練
        training_runs = find_training_runs()
        target_run = None
        for run in training_runs:
            if args.training in run['name']:
                target_run = run
                break
        
        if target_run:
            if target_run['agent_type'] == 'nerl':
                analyze_nerl_training(target_run)
            else:
                print("❌ 目前只支援 NERL 分析")
        else:
            print(f"❌ 未找到訓練: {args.training}")
    else:
        # 分析所有訓練
        analyze_all_recent_trainings()

if __name__ == "__main__":
    main()
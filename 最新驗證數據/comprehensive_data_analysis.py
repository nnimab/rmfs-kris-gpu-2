import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import warnings
import os
warnings.filterwarnings('ignore')

# 設定中文字體
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False

def load_and_prepare_data(file_path):
    """載入並準備數據"""
    df = pd.read_csv(file_path)
    return df

def calculate_statistics(df):
    """計算描述性統計"""
    # 定義要分析的指標
    metrics = {
        'completion_rate': ['Completion Rate (Run 1)', 'Completion Rate (Run 2)', 
                           'Completion Rate (Run 3)', 'Completion Rate (Run 4)'],
        'energy_per_order': ['Energy per Order (Run 1)', 'Energy per Order (Run 2)', 
                            'Energy per Order (Run 3)', 'Energy per Order (Run 4)'],
        'total_energy': ['Total Energy (Run 1)', 'Total Energy (Run 2)', 
                        'Total Energy (Run 3)', 'Total Energy (Run 4)'],
        'signal_switches': ['Signal Switches (Run 1)', 'Signal Switches (Run 2)', 
                           'Signal Switches (Run 3)', 'Signal Switches (Run 4)'],
        'completed_orders': ['Completed Orders (Run 1)', 'Completed Orders (Run 2)', 
                            'Completed Orders (Run 3)', 'Completed Orders (Run 4)']
    }
    
    # 計算統計量
    stats_results = {}
    for metric_name, columns in metrics.items():
        metric_data = df[columns].values
        stats_results[metric_name] = pd.DataFrame({
            'Experiment Group': df['Experiment Group'],
            'Mean': np.mean(metric_data, axis=1),
            'Std': np.std(metric_data, axis=1),
            'Min': np.min(metric_data, axis=1),
            'Max': np.max(metric_data, axis=1),
            'CV': np.std(metric_data, axis=1) / np.mean(metric_data, axis=1)  # 變異係數
        })
    
    return stats_results

def identify_anomalies(df):
    """識別異常值"""
    anomalies = []
    
    # 檢查time_based的Run 3
    time_based_idx = df[df['Experiment Group'] == 'time_based'].index[0]
    if df.loc[time_based_idx, 'Completed Orders (Run 3)'] < 50:
        anomalies.append({
            'group': 'time_based',
            'run': 'Run 3',
            'issue': f"只完成了 {df.loc[time_based_idx, 'Completed Orders (Run 3)']} 個訂單",
            'completion_rate': df.loc[time_based_idx, 'Completion Rate (Run 3)']
        })
    
    return anomalies

def calculate_composite_score(df):
    """計算綜合效能評分"""
    # 提取4次運行的數據
    completion_rates = df[['Completion Rate (Run 1)', 'Completion Rate (Run 2)', 
                          'Completion Rate (Run 3)', 'Completion Rate (Run 4)']].values
    energy_per_order = df[['Energy per Order (Run 1)', 'Energy per Order (Run 2)', 
                           'Energy per Order (Run 3)', 'Energy per Order (Run 4)']].values
    
    # 計算平均值
    avg_completion = np.mean(completion_rates, axis=1)
    avg_energy = np.mean(energy_per_order, axis=1)
    
    # 正規化（0-1範圍）
    norm_completion = (avg_completion - np.min(avg_completion)) / (np.max(avg_completion) - np.min(avg_completion))
    norm_energy = 1 - (avg_energy - np.min(avg_energy)) / (np.max(avg_energy) - np.min(avg_energy))  # 反向，因為能耗越低越好
    
    # 綜合評分（權重可調整）
    composite_score = 0.5 * norm_completion + 0.5 * norm_energy
    
    return pd.DataFrame({
        'Experiment Group': df['Experiment Group'],
        'Avg Completion Rate': avg_completion,
        'Avg Energy per Order': avg_energy,
        'Normalized Completion': norm_completion,
        'Normalized Energy': norm_energy,
        'Composite Score': composite_score
    }).sort_values('Composite Score', ascending=False)

def group_analysis(df):
    """分組分析"""
    # 添加分組標籤
    df_copy = df.copy()
    
    # 控制器類型
    df_copy['Controller Type'] = df_copy['Experiment Group'].apply(
        lambda x: 'Baseline' if x in ['time_based', 'queue_based', 'no_controller'] 
        else 'DQN' if 'dqn' in x 
        else 'NERL'
    )
    
    # NERL類型
    df_copy['NERL Type'] = df_copy['Experiment Group'].apply(
        lambda x: 'Global' if 'global' in x 
        else 'Step' if 'step' in x 
        else 'N/A'
    )
    
    # 訓練時長
    df_copy['Training Ticks'] = df_copy['Experiment Group'].apply(
        lambda x: '3000' if '3000' in x 
        else '8000' if '8000' in x 
        else 'N/A'
    )
    
    return df_copy

def create_visualizations(df, stats_results, output_dir):
    """創建視覺化圖表"""
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. 完成率比較圖
    plt.figure(figsize=(14, 8))
    experiments = df['Experiment Group']
    x = np.arange(len(experiments))
    width = 0.2
    
    for i in range(4):
        plt.bar(x + i*width, df[f'Completion Rate (Run {i+1})'], 
               width, label=f'Run {i+1}', alpha=0.8)
    
    plt.xlabel('實驗組別')
    plt.ylabel('完成率')
    plt.title('各控制器完成率比較（4次運行）')
    plt.xticks(x + 1.5*width, experiments, rotation=45, ha='right')
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'completion_rate_comparison.png'), dpi=300)
    plt.close()
    
    # 2. 能耗效率比較圖
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))
    
    # 每訂單能耗
    for i in range(4):
        ax1.plot(experiments, df[f'Energy per Order (Run {i+1})'], 
                marker='o', label=f'Run {i+1}', alpha=0.7)
    ax1.set_xlabel('實驗組別')
    ax1.set_ylabel('每訂單能耗 (EU)')
    ax1.set_title('每訂單能耗比較')
    ax1.legend()
    ax1.tick_params(axis='x', rotation=45)
    ax1.grid(True, alpha=0.3)
    
    # 總能耗
    for i in range(4):
        ax2.plot(experiments, df[f'Total Energy (Run {i+1})'], 
                marker='s', label=f'Run {i+1}', alpha=0.7)
    ax2.set_xlabel('實驗組別')
    ax2.set_ylabel('總能耗 (EU)')
    ax2.set_title('總能耗比較')
    ax2.legend()
    ax2.tick_params(axis='x', rotation=45)
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'energy_comparison.png'), dpi=300)
    plt.close()
    
    # 3. 穩定性分析（變異係數）
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    metrics_to_plot = ['completion_rate', 'energy_per_order', 'total_energy', 'completed_orders']
    titles = ['完成率變異係數', '每訂單能耗變異係數', '總能耗變異係數', '完成訂單數變異係數']
    
    for idx, (metric, title) in enumerate(zip(metrics_to_plot, titles)):
        ax = axes[idx//2, idx%2]
        cv_values = stats_results[metric]['CV'].values
        bars = ax.bar(experiments, cv_values)
        
        # 顏色編碼：CV越低越穩定（綠色），越高越不穩定（紅色）
        colors = plt.cm.RdYlGn_r(cv_values / max(cv_values))
        for bar, color in zip(bars, colors):
            bar.set_color(color)
        
        ax.set_xlabel('實驗組別')
        ax.set_ylabel('變異係數 (CV)')
        ax.set_title(title)
        ax.tick_params(axis='x', rotation=45)
        ax.axhline(y=0.1, color='r', linestyle='--', alpha=0.5, label='CV=0.1')
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'stability_analysis.png'), dpi=300)
    plt.close()

def generate_report(df, stats_results, anomalies, composite_scores):
    """生成分析報告"""
    report = []
    report.append("# 倉儲機器人交通控制系統 - 數據分析報告\n")
    report.append(f"分析日期：{pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # 1. 異常值報告
    report.append("\n## 1. 異常值檢測\n")
    if anomalies:
        for anomaly in anomalies:
            report.append(f"- **{anomaly['group']}** 在 {anomaly['run']} 中出現異常：{anomaly['issue']}")
            report.append(f"  - 完成率：{anomaly['completion_rate']:.2%}\n")
    else:
        report.append("未發現明顯異常值。\n")
    
    # 2. 最佳表現者
    report.append("\n## 2. 各指標最佳表現\n")
    
    # 完成率最高
    best_completion = stats_results['completion_rate'].loc[
        stats_results['completion_rate']['Mean'].idxmax()]
    report.append(f"- **最高平均完成率**：{best_completion['Experiment Group']} "
                 f"({best_completion['Mean']:.2%} ± {best_completion['Std']:.2%})")
    
    # 能耗最低
    best_energy = stats_results['energy_per_order'].loc[
        stats_results['energy_per_order']['Mean'].idxmin()]
    report.append(f"- **最低平均每訂單能耗**：{best_energy['Experiment Group']} "
                 f"({best_energy['Mean']:.2f} ± {best_energy['Std']:.2f} EU)")
    
    # 最穩定（CV最低）
    most_stable = stats_results['completion_rate'].loc[
        stats_results['completion_rate']['CV'].idxmin()]
    report.append(f"- **最穩定表現（完成率）**：{most_stable['Experiment Group']} "
                 f"(CV = {most_stable['CV']:.3f})")
    
    # 3. 綜合評分前三名
    report.append("\n## 3. 綜合效能評分（前5名）\n")
    for idx, row in composite_scores.head(5).iterrows():
        report.append(f"{idx+1}. **{row['Experiment Group']}**")
        report.append(f"   - 綜合評分：{row['Composite Score']:.3f}")
        report.append(f"   - 平均完成率：{row['Avg Completion Rate']:.2%}")
        report.append(f"   - 平均每訂單能耗：{row['Avg Energy per Order']:.2f} EU\n")
    
    # 4. 分組比較
    report.append("\n## 4. 分組比較分析\n")
    df_grouped = group_analysis(df)
    
    # 基線 vs DRL
    report.append("### 4.1 基線控制器 vs 深度學習控制器\n")
    for controller_type in ['Baseline', 'DQN', 'NERL']:
        group_data = df_grouped[df_grouped['Controller Type'] == controller_type]
        if len(group_data) > 0:
            completion_cols = [f'Completion Rate (Run {i})' for i in range(1, 5)]
            energy_cols = [f'Energy per Order (Run {i})' for i in range(1, 5)]
            
            avg_completion = np.mean(group_data[completion_cols].values)
            avg_energy = np.mean(group_data[energy_cols].values)
            
            report.append(f"- **{controller_type}** (n={len(group_data)})")
            report.append(f"  - 平均完成率：{avg_completion:.2%}")
            report.append(f"  - 平均每訂單能耗：{avg_energy:.2f} EU\n")
    
    # 5. 建議
    report.append("\n## 5. 結論與建議\n")
    report.append("基於分析結果，提供以下建議：\n")
    
    # 找出綜合評分最高的策略
    best_overall = composite_scores.iloc[0]
    report.append(f"1. **最佳整體表現**：{best_overall['Experiment Group']} "
                 f"在完成率和能耗效率之間達到最佳平衡。")
    
    # 特殊情況建議
    if any('time_based' in a['group'] for a in anomalies):
        report.append("\n2. **注意事項**：time_based 控制器在某些運行中表現異常，"
                     "建議進一步調查其穩定性問題。")
    
    return '\n'.join(report)

def main():
    # 設定路徑
    base_path = r"C:\Users\h2388\Desktop\論文簡報\最新驗證數據"
    data_file = os.path.join(base_path, "evaluation_summary_table.csv")
    output_dir = os.path.join(base_path, "analysis_results")
    
    # 載入數據
    print("載入數據...")
    df = load_and_prepare_data(data_file)
    
    # 計算統計量
    print("計算描述性統計...")
    stats_results = calculate_statistics(df)
    
    # 識別異常值
    print("檢測異常值...")
    anomalies = identify_anomalies(df)
    
    # 計算綜合評分
    print("計算綜合效能評分...")
    composite_scores = calculate_composite_score(df)
    
    # 創建視覺化
    print("生成視覺化圖表...")
    create_visualizations(df, stats_results, output_dir)
    
    # 生成報告
    print("生成分析報告...")
    report = generate_report(df, stats_results, anomalies, composite_scores)
    
    # 儲存報告
    report_file = os.path.join(output_dir, "analysis_report.md")
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    # 儲存統計結果
    excel_file = os.path.join(output_dir, "statistical_analysis.xlsx")
    with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
        # 原始數據
        df.to_excel(writer, sheet_name='原始數據', index=False)
        
        # 各指標統計
        for metric_name, metric_stats in stats_results.items():
            metric_stats.to_excel(writer, sheet_name=metric_name, index=False)
        
        # 綜合評分
        composite_scores.to_excel(writer, sheet_name='綜合評分', index=False)
    
    print(f"\n分析完成！")
    print(f"- 圖表已儲存至：{output_dir}")
    print(f"- 報告已儲存至：{report_file}")
    print(f"- 統計結果已儲存至：{excel_file}")
    
    return df, stats_results, composite_scores

if __name__ == "__main__":
    df, stats_results, composite_scores = main()
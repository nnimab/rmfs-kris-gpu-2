import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import warnings
import os
from pathlib import Path

# --- 設定 ---
# 設置圖表樣式與字體
plt.style.use('seaborn-v0_8-whitegrid')
# 移除中文字體設定，使用 Matplotlib 的預設英文字體
# plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False
sns.set_palette("colorblind")

# --- 檔案路徑 ---
# 使用Path物件來處理路徑，更具可讀性與跨平台兼容性
BASE_PATH = Path("./最新驗證數據")
DATA_FILE = BASE_PATH / "evaluation_summary_table.csv"
OUTPUT_DIR = BASE_PATH / "analysis_results_new"

# 確保輸出目錄存在
OUTPUT_DIR.mkdir(exist_ok=True)


def load_and_clean_data(file_path):
    """
    載入、清理並重塑數據。
    1. 載入CSV。
    2. 移除 time_based 的異常值。
    3. 將寬數據轉換為長數據 (Tidy Data)。
    """
    print("1. 載入並清理數據...")
    df_raw = pd.read_csv(file_path)

    # 處理 time_based 的異常值
    # 找到 time_based 實驗組的索引
    time_based_idx = df_raw[df_raw['Experiment Group'] == 'time_based'].index
    if not time_based_idx.empty:
        # 將異常的 Run 3 數據設置為 NaN
        cols_to_nullify = [col for col in df_raw.columns if '(Run 3)' in col]
        df_raw.loc[time_based_idx, cols_to_nullify] = np.nan
        print("  - 已移除 'time_based' 的 Run 3 異常數據。")

    # 將寬數據轉換為長數據
    id_vars = ['Experiment Group']
    value_vars = [col for col in df_raw.columns if col not in id_vars]
    
    df_long = pd.melt(df_raw, id_vars=id_vars, value_vars=value_vars, var_name='Metric_Run', value_name='Value')
    
    # 從 Metric_Run 中分離出指標名稱和運行次數
    df_long[['Metric', 'Run']] = df_long['Metric_Run'].str.extract(r'(.+?)\s*\(Run (\d+)\)')
    df_long['Run'] = pd.to_numeric(df_long['Run'])
    
    # 將數據從指標維度 pivot 回來
    df_tidy = df_long.pivot_table(index=['Experiment Group', 'Run'], columns='Metric', values='Value').reset_index()
    
    # 重新命名欄位以方便使用
    df_tidy.rename(columns={
        'Completion Rate': 'completion_rate',
        'Energy per Order': 'energy_per_order',
        'Total Energy': 'total_energy',
        'Signal Switches': 'signal_switches',
        'Completed Orders': 'completed_orders'
    }, inplace=True)
    
    print(f"  - 數據已成功轉換為 Tidy Format，共 {len(df_tidy)} 筆有效運行記錄。")
    return df_tidy

def calculate_statistics(df):
    """計算描述性統計，包括平均值、標準差和標準誤"""
    print("2. 計算描述性統計...")
    
    # 定義要分析的指標
    metrics = ['completion_rate', 'energy_per_order', 'signal_switches', 'completed_orders']
    
    # 分組計算統計量
    stats_df = df.groupby('Experiment Group')[metrics].agg(
        ['mean', 'std', lambda x: stats.sem(x, nan_policy='omit')]
    ).reset_index()
    
    # 整理欄位名稱
    stats_df.columns = ['_'.join(col).strip('_') for col in stats_df.columns.values]
    stats_df.rename(columns={'completion_rate_<lambda_0>': 'completion_rate_sem',
                             'energy_per_order_<lambda_0>': 'energy_per_order_sem'}, inplace=True)
    
    # 排序以便觀察
    stats_df = stats_df.sort_values(by='completion_rate_mean', ascending=False)
    
    # 保存為CSV
    output_file = OUTPUT_DIR / "performance_statistics.csv"
    stats_df.to_csv(output_file, index=False, float_format='%.4f')
    print(f"  - 統計結果已儲存至: {output_file}")
    
    return stats_df

def create_visualizations(df, stats_df):
    """
    執行主題式分析與視覺化。
    主題一：最終效能格局
    主題二：DRL vs. 基線
    主題三：NERL 內部對決
    主題四：穩定性分析
    """
    print("3. 生成主題式視覺化圖表...")
    
    # --- 主題一：最終效能格局 - 能效權衡散點圖 ---
    plt.figure(figsize=(12, 8))
    
    # 定義短名稱映射，用於圖表標註
    short_names_map = {
        'time_based': 'Baseline-T', 'queue_based': 'Baseline-Q', 'no_controller': 'Baseline-N',
        'dqn_dqn_model_step_55000': 'DQN-S', 'dqn_dqn_model_global_55000': 'DQN-G',
        'nerl_nerl_step_a3000ticks': 'NERL-S-A3', 'nerl_nerl_global_a3000ticks': 'NERL-G-A3',
        'nerl_nerl_step_b3000ticks': 'NERL-S-B3', 'nerl_nerl_global_b3000ticks': 'NERL-G-B3',
        'nerl_nerl_step_a8000ticks': 'NERL-S-A8', 'nerl_nerl_global_a8000ticks': 'NERL-G-A8',
        'nerl_nerl_step_b8000ticks': 'NERL-S-B8', 'nerl_nerl_global_b8000ticks': 'NERL-G-B8'
    }
    stats_df['short_name'] = stats_df['Experiment Group'].map(short_names_map)

    # 繪製散點圖
    sns.scatterplot(data=stats_df, x='energy_per_order_mean', y='completion_rate_mean', 
                    s=150, hue='short_name', style='short_name', legend='full',
                    palette='viridis', edgecolor='black', alpha=0.8)

    # 標註每個點
    for i, row in stats_df.iterrows():
        plt.text(row['energy_per_order_mean'], row['completion_rate_mean'] + 0.002, 
                 row['short_name'], fontsize=9, ha='center')

    plt.title('Fig. 4.3.1: Performance vs. Energy Efficiency Trade-off', fontsize=16, pad=20)
    plt.xlabel('Mean Energy per Order (EU) - Lower is Better', fontsize=12)
    plt.ylabel('Mean Completion Rate - Higher is Better', fontsize=12)
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', title='Controller')
    plt.grid(True, which='both', linestyle='--', linewidth=0.5)
    plt.tight_layout()
    
    # 標註象限
    mean_x = stats_df['energy_per_order_mean'].mean()
    mean_y = stats_df['completion_rate_mean'].mean()
    plt.axvline(mean_x, color='grey', linestyle=':', alpha=0.5)
    plt.axhline(mean_y, color='grey', linestyle=':', alpha=0.5)
    plt.text(stats_df['energy_per_order_mean'].min(), mean_y + 0.001, 'High Efficiency', color='green', fontsize=12, va='bottom', ha='left')
    plt.text(stats_df['energy_per_order_mean'].max(), mean_y - 0.005, 'Low Efficiency', color='red', fontsize=12, va='bottom', ha='right')

    plot_file = OUTPUT_DIR / "fig_4_3_1_tradeoff_plot.png"
    plt.savefig(plot_file, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  - 主題一圖表已儲存: {plot_file}")

    # --- 主題二：DRL vs. 基線 ---
    df['category'] = df['Experiment Group'].apply(
        lambda x: 'Baseline' if x in ['time_based', 'queue_based', 'no_controller']
        else 'DQN' if 'dqn' in x
        else 'NERL'
    )
    plt.figure(figsize=(10, 7))
    sns.boxplot(data=df, x='category', y='completion_rate', order=['Baseline', 'DQN', 'NERL'])
    sns.stripplot(data=df, x='category', y='completion_rate', order=['Baseline', 'DQN', 'NERL'], color='black', alpha=0.5, jitter=0.1)
    
    # 統計檢驗
    baseline_data = df[df['category'] == 'Baseline']['completion_rate'].dropna()
    drl_data = df[df['category'] != 'Baseline']['completion_rate'].dropna()
    # 執行 Welch's t-test，因為我們不假設兩組方差相等
    if len(baseline_data) > 1 and len(drl_data) > 1:
        t_stat, p_value = stats.ttest_ind(baseline_data, drl_data, equal_var=False) 
        stat_text = f"Welch's t-test (Baseline vs DRL): p-value = {p_value:.4f}"
    else:
        stat_text = "Not enough data for t-test"


    plt.title('Fig. 4.3.2: Completion Rate Comparison by Controller Type', fontsize=16, pad=20)
    plt.xlabel('Controller Category', fontsize=12)
    plt.ylabel('Completion Rate', fontsize=12)
    plt.figtext(0.5, -0.05, stat_text, ha="center", fontsize=10)
    plt.tight_layout()

    plot_file = OUTPUT_DIR / "fig_4_3_2_drl_vs_baseline.png"
    plt.savefig(plot_file, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  - 主題二圖表已儲存: {plot_file}")

    # --- 主題三：NERL 內部對決 ---
    df_nerl = df[df['category'] == 'NERL'].copy()
    df_nerl['reward_type'] = df_nerl['Experiment Group'].apply(lambda x: 'Global' if 'global' in x else 'Step')
    df_nerl['eval_ticks'] = df_nerl['Experiment Group'].apply(lambda x: '8000 Ticks' if '8000' in x else '3000 Ticks')
    df_nerl['variant'] = df_nerl['Experiment Group'].apply(lambda x: 'Variant A (Exploratory)' if '_a' in x else 'Variant B (Exploitative)')

    g = sns.catplot(
        data=df_nerl, x='reward_type', y='completion_rate',
        hue='variant', col='eval_ticks',
        kind='bar', errorbar='se', capsize=.1,
        height=6, aspect=0.8, palette='muted'
    )
    g.fig.suptitle('Fig. 4.3.3: NERL Hyperparameter Analysis on Completion Rate', y=1.03, fontsize=16)
    g.set_axis_labels("Reward Type", "Completion Rate")
    g.set_titles("Evaluation: {col_name}")
    g.legend.set_title("NERL Variant")
    plt.tight_layout()

    plot_file = OUTPUT_DIR / "fig_4_3_3_nerl_comparison.png"
    plt.savefig(plot_file, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  - 主題三圖表已儲存: {plot_file}")

    # --- 主題四：穩定性分析 ---
    stats_df['completion_rate_cv'] = stats_df['completion_rate_std'] / stats_df['completion_rate_mean']
    stats_df_sorted_cv = stats_df.sort_values('completion_rate_cv', ascending=True)

    plt.figure(figsize=(12, 7))
    bars = sns.barplot(data=stats_df_sorted_cv, x='short_name', y='completion_rate_cv', palette='coolwarm')
    plt.title('Fig. 4.3.4a: Stability of Completion Rate (Coefficient of Variation)', fontsize=16, pad=20)
    plt.xlabel('Controller', fontsize=12)
    plt.ylabel('CV of Completion Rate - Lower is More Stable', fontsize=12)
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()

    plot_file = OUTPUT_DIR / "fig_4_3_4a_completion_stability.png"
    plt.savefig(plot_file, dpi=300)
    plt.close()
    print(f"  - Stability chart (Completion Rate) saved to: {plot_file}")

    # --- 主題四b：能源穩定性分析 ---
    stats_df['energy_per_order_cv'] = stats_df['energy_per_order_std'] / stats_df['energy_per_order_mean']
    stats_df_sorted_energy_cv = stats_df.sort_values('energy_per_order_cv', ascending=True)

    plt.figure(figsize=(12, 7))
    bars = sns.barplot(data=stats_df_sorted_energy_cv, x='short_name', y='energy_per_order_cv', palette='viridis_r')
    plt.title('Fig. 4.3.4b: Stability of Energy Efficiency (Coefficient of Variation)', fontsize=16, pad=20)
    plt.xlabel('Controller', fontsize=12)
    plt.ylabel('CV of Energy per Order - Lower is More Stable', fontsize=12)
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()

    plot_file = OUTPUT_DIR / "fig_4_3_4b_energy_stability.png"
    plt.savefig(plot_file, dpi=300)
    plt.close()
    print(f"  - Stability chart (Energy Efficiency) saved to: {plot_file}")


def analyze_correlations(df):
    """計算並視覺化關鍵指標之間的關聯性"""
    print("4. 分析關鍵指標關聯性...")
    
    # 選擇要分析的指標
    metrics_for_corr = ['completion_rate', 'energy_per_order', 'signal_switches', 'completed_orders']
    df_corr = df[metrics_for_corr].dropna()
    
    # 計算皮爾遜相關係數
    corr_matrix = df_corr.corr(method='pearson')
    
    # 繪製熱力圖
    plt.figure(figsize=(10, 8))
    sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', fmt='.2f', linewidths=.5)
    plt.title('Fig. 4.3.5: Correlation Heatmap of Key Performance Indicators', fontsize=16, pad=20)
    plt.tight_layout()
    
    plot_file = OUTPUT_DIR / "fig_4_3_5_correlation_heatmap.png"
    plt.savefig(plot_file, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  - 主題五圖表已儲存: {plot_file}")
    
    return corr_matrix

def generate_summary_table(stats_df):
    """生成最終的關鍵發現總結表"""
    print("5. 生成關鍵發現總結表...")
    
    summary_data = []
    
    # 提取各類代表模型的數據
    # Baseline-Q: 基線代表
    # DQN-S: DQN代表
    # NERL-G-A8: 能效型NERL代表
    # NERL-S-B8: 均衡型NERL代表
    
    # 使用英文鍵名
    representatives_en = {
        'Baseline': 'queue_based',
        'DQN': 'dqn_dqn_model_step_55000',
        'NERL (High-Efficiency)': 'nerl_nerl_global_a8000ticks',
        'NERL (Balanced)': 'nerl_nerl_step_b8000ticks'
    }

    for category, exp_group in representatives_en.items():
        row_data = stats_df[stats_df['Experiment Group'] == exp_group]
        if not row_data.empty:
            summary_data.append({
                'Controller Category': category,
                'Representative Model': row_data['short_name'].values[0],
                'Mean Completion Rate (%)': f"{row_data['completion_rate_mean'].values[0] * 100:.1f}",
                'Mean Energy per Order (EU)': f"{row_data['energy_per_order_mean'].values[0]:.1f}",
                'Stability (CV)': f"{row_data['completion_rate_cv'].values[0]:.3f}"
            })

    df_summary = pd.DataFrame(summary_data)
    
    output_file = OUTPUT_DIR / "table_4_4_1_key_findings_en.csv"
    df_summary.to_csv(output_file, index=False)
    print(f"  - English summary table has been saved to: {output_file}")
    
    return df_summary


def main():
    """主執行函數"""
    # 階段一：數據載入與處理
    df_tidy = load_and_clean_data(DATA_FILE)
    
    # 階段二：計算統計數據
    stats_df = calculate_statistics(df_tidy)
    
    # 階段三：主題式視覺化
    create_visualizations(df_tidy, stats_df)
    
    # 階段四：關聯性分析
    analyze_correlations(df_tidy)
    
    # 階段五：生成總結表
    generate_summary_table(stats_df)
    
    print("\nAnalysis complete!")
    print(f"All results have been saved to: {OUTPUT_DIR.resolve()}")

if __name__ == "__main__":
    main() 
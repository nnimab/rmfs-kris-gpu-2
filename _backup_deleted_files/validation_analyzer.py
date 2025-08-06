
import argparse
import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

def setup_plot_style():
    """設定 Matplotlib/Seaborn 圖表的全域樣式。"""
    plt.style.use('seaborn-v0_8-darkgrid')
    sns.set_palette("husl")
    plt.rcParams['font.family'] = 'DejaVu Sans'
    plt.rcParams['font.size'] = 12
    plt.rcParams['axes.unicode_minus'] = False
    print("Plot style 'seaborn-v0_8-darkgrid' with 'husl' palette configured.")

def parse_evaluation_data(input_dir):
    """
    解析指定目錄下的所有評估結果檔案。
    
    Args:
        input_dir (Path): 包含各實驗驗證結果子目錄的根目錄。
    
    Returns:
        list: 一個包含所有實驗組 `run_id: 0` 數據的字典列表。
    """
    all_results_data = []
    print(f"Scanning for evaluation files in: {input_dir}")

    json_files = list(input_dir.rglob("evaluation_results*.json"))
    print(f"Found {len(json_files)} result files.")

    for json_file in json_files:
        experiment_name = json_file.parent.name
        print(f"  Processing: {experiment_name}")
        
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 取得 results 字典中的第一個控制器結果（通常只有一個）
            results_key = next(iter(data.get('results', {})))
            controller_results = data['results'][results_key]
            
            # 找到 run_id 為 0 的那一筆
            first_run = next((run for run in controller_results.get('individual_runs', []) if run.get('run_id') == 0), None)
            
            if first_run:
                # 加上實驗名稱
                first_run['experiment_name'] = experiment_name
                all_results_data.append(first_run)
                print(f"    -> Extracted data for run_id 0.")
            else:
                print(f"    -> WARNING: Could not find run_id 0 in {json_file}")

        except Exception as e:
            print(f"    -> ERROR: Failed to process {json_file}. Reason: {e}")
            
    return all_results_data

def generate_markdown_table(df, metrics, output_path):
    """
    根據指定的指標生成 Markdown 格式的比較表格。
    
    Args:
        df (pd.DataFrame): 包含所有實驗數據的 DataFrame。
        metrics (list): 要包含在表格中的欄位名稱。
        output_path (Path): Markdown 檔案的儲存路徑。
    """
    # 選取需要的欄位，並重新命名，使其更適合論文
    table_df = df[['experiment_name'] + metrics].copy()
    table_df.rename(columns={
        'experiment_name': '實驗組 (Experiment)',
        'completion_rate': '訂單完成率 (Completion Rate)',
        'energy_per_order': '單均能耗 (Energy per Order)',
        'total_energy': '總能耗 (Total Energy)',
        'signal_switch_count': '號誌切換次數 (Signal Switches)',
        'stop_and_go_events': '啟停事件數 (Stop-Go Events)',
        'completed_orders': '完成訂單數 (Completed Orders)'
    }, inplace=True)

    # 按完成率排序
    table_df = table_df.sort_values(by='訂單完成率 (Completion Rate)', ascending=False)
    
    # 格式化數字
    table_df['訂單完成率 (Completion Rate)'] = table_df['訂單完成率 (Completion Rate)'].apply(lambda x: f"{x:.2%}")
    for col in ['單均能耗 (Energy per Order)', '總能耗 (Total Energy)', '號誌切換次數 (Signal Switches)', '啟停事件數 (Stop-Go Events)', '完成訂單數 (Completed Orders)']:
        table_df[col] = table_df[col].apply(lambda x: f"{x:,.0f}")
        
    md_string = table_df.to_markdown(index=False)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("# 最終模型驗證效能比較總表\n\n")
        f.write(md_string)
        
    print(f"Performance table saved to: {output_path}")

def generate_comparison_charts(df, metrics, output_dir):
    """
    為每個指定指標生成橫向比較長條圖。
    
    Args:
        df (pd.DataFrame): 包含所有實驗數據的 DataFrame。
        metrics (list): 要為其生成圖表的指標名稱。
        output_dir (Path): 儲存圖檔的目錄。
    """
    # 簡化實驗名稱以利於圖表顯示
    df['display_name'] = df['experiment_name'].str.replace('_EVAL_', '_').str.replace('_55000', '').str.replace('nerl_', '')
    
    # 定義顏色和圖例
    def get_color(name):
        if 'time_based' in name: return 'grey'
        if 'queue_based' in name: return 'saddlebrown'
        if 'dqn' in name: return 'goldenrod'
        if 'global' in name: return 'seagreen'
        if 'step' in name: return 'royalblue'
        return 'black'

    for metric in metrics:
        is_ascending = 'energy' in metric # 能耗指標越低越好
        df_sorted = df.sort_values(by=metric, ascending=is_ascending)
        
        plt.figure(figsize=(16, 10))
        
        bars = plt.bar(df_sorted['display_name'], df_sorted[metric], 
                       color=[get_color(name) for name in df_sorted['experiment_name']],
                       edgecolor='black')
        
        # 格式化標題
        title = metric.replace('_', ' ').title()
        plt.title(f'Final Model Performance Comparison: {title}', fontsize=18, fontweight='bold')
        plt.ylabel(title, fontsize=14)
        plt.xlabel('Experiment Group', fontsize=14)
        plt.xticks(rotation=45, ha="right")
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        
        # 在條形圖上添加數值標籤
        for bar in bars:
            yval = bar.get_height()
            if yval > 1000:
                label = f'{yval:,.0f}'
            else:
                label = f'{yval:.2f}'
            plt.text(bar.get_x() + bar.get_width()/2.0, yval, label, ha='center', va='bottom', fontsize=10)

        plt.tight_layout()
        
        # 儲存圖檔
        chart_path = output_dir / f"comparison_{metric}.png"
        plt.savefig(chart_path, dpi=300)
        plt.close()
        print(f"Chart saved for {metric}: {chart_path}")


def main():
    parser = argparse.ArgumentParser(description="RMFS 最終模型驗證數據分析工具")
    parser.add_argument('--input_dir', '-i', required=True, help='包含所有實驗驗證結果的根目錄。')
    parser.add_argument('--output_dir', '-o', required=True, help='儲存分析結果 (圖表、表格) 的目錄。')
    args = parser.parse_args()

    input_path = Path(args.input_dir)
    output_path = Path(args.output_dir)
    output_path.mkdir(exist_ok=True)

    print("="*60)
    print("Starting Validation Data Analysis")
    print("="*60)

    # 1. 設定圖表樣式
    setup_plot_style()

    # 2. 解析數據
    results_data = parse_evaluation_data(input_path)
    if not results_data:
        print("No valid data found. Exiting.")
        return
        
    df = pd.DataFrame(results_data)

    # 3. 定義要分析的關鍵指標
    metrics_to_analyze = [
        'completion_rate',
        'energy_per_order',
        'total_energy',
        'signal_switch_count',
        'stop_and_go_events',
        'completed_orders'
    ]
    
    # 過濾掉數據中不存在的指標
    metrics_to_analyze = [m for m in metrics_to_analyze if m in df.columns]

    # 4. 生成 Markdown 表格
    generate_markdown_table(df, metrics_to_analyze, output_path / "validation_performance_table.md")

    # 5. 生成比較圖表
    generate_comparison_charts(df, metrics_to_analyze, output_path)

    print("\n" + "="*60)
    print("Analysis Complete!")
    print(f"Results saved in: {output_path}")
    print("="*60)

if __name__ == "__main__":
    main() 
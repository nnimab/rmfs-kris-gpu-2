#!/usr/bin/env python3
"""
分析容量測試的時間序列數據並生成圖表
"""
import sys
import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from datetime import datetime
import numpy as np

# 設置中文字體
plt.rcParams['font.sans-serif'] = ['DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

def extract_progress_data(log_file):
    """從日誌文件中提取進度數據（包含能源數據）"""
    progress_data = []
    energy_data = []
    
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            for line in f:
                if "進度:" in line and "ticks," in line:
                    # 格式: 2025-08-05 15:42:00,243 - INFO - rmfs_logger -   進度: 10000/20000 ticks, 完成訂單: 47/53
                    parts = line.strip().split(" - ")
                    if len(parts) >= 4:
                        timestamp = parts[0]
                        progress_info = parts[-1]
                        
                        # 解析tick和訂單信息
                        tick_part = progress_info.split(",")[0].split(":")[-1].strip()
                        order_part = progress_info.split(",")[1].split(":")[-1].strip()
                        
                        current_tick = int(tick_part.split("/")[0])
                        completed_orders = int(order_part.split("/")[0])
                        total_orders = int(order_part.split("/")[1])
                        
                        progress_data.append({
                            'timestamp': timestamp,
                            'tick': current_tick,
                            'completed_orders': completed_orders,
                            'total_orders': total_orders,
                            'completion_rate': completed_orders / total_orders if total_orders > 0 else 0
                        })
                
                # 提取能源消耗數據
                elif "平均能耗" in line or "energy_consumed" in line:
                    parts = line.strip().split(" - ")
                    if len(parts) >= 4:
                        timestamp = parts[0]
                        
                        # 嘗試解析能源值
                        import re
                        energy_match = re.search(r'(\d+\.?\d*)', parts[-1])
                        if energy_match:
                            energy_value = float(energy_match.group(1))
                            
                            # 找到對應的tick
                            tick_match = re.search(r'tick\s*[:=]\s*(\d+)', line)
                            if tick_match:
                                tick = int(tick_match.group(1))
                            else:
                                # 使用最後一個進度數據的tick
                                tick = progress_data[-1]['tick'] if progress_data else 0
                            
                            energy_data.append({
                                'timestamp': timestamp,
                                'tick': tick,
                                'energy': energy_value
                            })
    except Exception as e:
        print(f"Error reading log file: {e}")
    
    return progress_data, energy_data


def analyze_capacity_test_results(result_dir):
    """分析容量測試結果並生成圖表"""
    result_path = Path(result_dir)
    
    if not result_path.exists():
        print(f"結果目錄不存在: {result_dir}")
        return
    
    # 收集所有測試的時間序列數據
    all_data = {}
    
    # 遍歷所有工作空間
    workspaces_dir = result_path / "workspaces"
    for workspace in workspaces_dir.iterdir():
        if workspace.is_dir():
            # 解析機器人數量和運行次數
            parts = workspace.name.split("_")
            if len(parts) >= 4 and parts[0] == "robots":
                robot_count = int(parts[1])
                run_index = int(parts[2].replace("run", ""))
                
                # 查找日誌文件和結果文件
                log_files = list(workspace.rglob("evaluation.log"))
                result_files = list(workspace.rglob("evaluation_results.json"))
                
                if log_files:
                    log_file = log_files[0]
                    progress_data, energy_data = extract_progress_data(log_file)
                    
                    # 如果沒有從日誌中獲取到能源數據，嘗試從結果JSON中獲取
                    if not energy_data and result_files:
                        try:
                            with open(result_files[0], 'r') as f:
                                result_json = json.load(f)
                                final_energy = result_json.get('average_robot_energy_consumed', 0)
                                final_tick = result_json.get('warehouse_final_tick', 10000)
                                if final_energy > 0:
                                    energy_data = [{
                                        'timestamp': '',
                                        'tick': final_tick,
                                        'energy': final_energy * result_json.get('active_robots', robot_count)
                                    }]
                        except Exception as e:
                            print(f"Error reading result JSON: {e}")
                    
                    if progress_data:
                        key = f"{robot_count}_run{run_index}"
                        all_data[key] = {
                            'robot_count': robot_count,
                            'run_index': run_index,
                            'data': progress_data,
                            'energy_data': energy_data
                        }
    
    if not all_data:
        print("沒有找到時間序列數據")
        return
    
    # 創建圖表（增加到 2x3 佈局以包含能源圖表）
    fig, axes = plt.subplots(2, 3, figsize=(20, 12))
    fig.suptitle('Capacity Test Time Series Analysis', fontsize=16)
    
    # 1. 訂單完成進度圖
    ax1 = axes[0, 0]
    for key, test_data in all_data.items():
        robot_count = test_data['robot_count']
        run_index = test_data['run_index']
        data = test_data['data']
        
        if data:
            ticks = [d['tick'] for d in data]
            completed = [d['completed_orders'] for d in data]
            
            label = f"{robot_count} robots (run {run_index+1})"
            color = plt.cm.tab10(robot_count % 10)
            linestyle = '-' if run_index == 0 else '--'
            
            ax1.plot(ticks, completed, label=label, color=color, linestyle=linestyle)
    
    ax1.set_xlabel('Simulation Ticks')
    ax1.set_ylabel('Completed Orders')
    ax1.set_title('Order Completion Progress')
    ax1.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    ax1.grid(True, alpha=0.3)
    
    # 2. 完成率變化圖
    ax2 = axes[0, 1]
    for key, test_data in all_data.items():
        robot_count = test_data['robot_count']
        run_index = test_data['run_index']
        data = test_data['data']
        
        if data:
            ticks = [d['tick'] for d in data]
            rates = [d['completion_rate'] * 100 for d in data]
            
            color = plt.cm.tab10(robot_count % 10)
            linestyle = '-' if run_index == 0 else '--'
            
            ax2.plot(ticks, rates, color=color, linestyle=linestyle)
    
    ax2.set_xlabel('Simulation Ticks')
    ax2.set_ylabel('Completion Rate (%)')
    ax2.set_title('Order Completion Rate Over Time')
    ax2.grid(True, alpha=0.3)
    
    # 3. 按機器人數量分組的平均性能
    ax3 = axes[1, 0]
    robot_counts = sorted(set(test_data['robot_count'] for test_data in all_data.values()))
    avg_completion = []
    
    for count in robot_counts:
        completions = []
        for test_data in all_data.values():
            if test_data['robot_count'] == count and test_data['data']:
                # 取最後的完成數
                final_completion = test_data['data'][-1]['completed_orders']
                completions.append(final_completion)
        
        avg_completion.append(np.mean(completions) if completions else 0)
    
    bars = ax3.bar(robot_counts, avg_completion, color='skyblue', edgecolor='navy')
    ax3.set_xlabel('Number of Robots')
    ax3.set_ylabel('Average Completed Orders')
    ax3.set_title('Average Performance by Robot Count')
    ax3.grid(True, alpha=0.3, axis='y')
    
    # 在條形圖上添加數值
    for bar, val in zip(bars, avg_completion):
        height = bar.get_height()
        ax3.text(bar.get_x() + bar.get_width()/2., height,
                f'{val:.1f}', ha='center', va='bottom')
    
    # 4. 性能穩定性分析（標準差）
    ax4 = axes[1, 1]
    std_completion = []
    
    for count in robot_counts:
        completions = []
        for test_data in all_data.values():
            if test_data['robot_count'] == count and test_data['data']:
                final_completion = test_data['data'][-1]['completed_orders']
                completions.append(final_completion)
        
        std_completion.append(np.std(completions) if len(completions) > 1 else 0)
    
    bars = ax4.bar(robot_counts, std_completion, color='coral', edgecolor='darkred')
    ax4.set_xlabel('Number of Robots')
    ax4.set_ylabel('Standard Deviation')
    ax4.set_title('Performance Stability (Lower is Better)')
    ax4.grid(True, alpha=0.3, axis='y')
    
    # 在條形圖上添加數值
    for bar, val in zip(bars, std_completion):
        height = bar.get_height()
        if height > 0:
            ax4.text(bar.get_x() + bar.get_width()/2., height,
                    f'{val:.1f}', ha='center', va='bottom')
    
        # 5. 能源消耗趨勢圖
    ax5 = axes[1, 2]
    for key, test_data in all_data.items():
        robot_count = test_data['robot_count']
        run_index = test_data['run_index']
        energy_data = test_data.get('energy_data', [])
        
        if energy_data:
            ticks = [d['tick'] for d in energy_data]
            energy_values = [d['energy'] for d in energy_data]
            
            label = f"{robot_count} robots (run {run_index+1})"
            color = plt.cm.tab10(robot_count % 10)
            linestyle = '-' if run_index == 0 else '--'
            
            ax5.plot(ticks, energy_values, label=label, color=color, linestyle=linestyle)
    
    ax5.set_xlabel('Simulation Ticks')
    ax5.set_ylabel('Energy Consumption')
    ax5.set_title('Energy Consumption Over Time')
    ax5.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    ax5.grid(True, alpha=0.3)
    
    # 6. 平均能源效率（每個訂單的能源消耗）
    ax6 = axes[0, 2]
    robot_counts = sorted(set(test_data['robot_count'] for test_data in all_data.values()))
    avg_energy_per_order = []
    
    for count in robot_counts:
        energy_per_order_values = []
        for test_data in all_data.values():
            if test_data['robot_count'] == count:
                # 獲取最終能源和訂單數
                if test_data['data'] and test_data.get('energy_data'):
                    final_orders = test_data['data'][-1]['completed_orders']
                    if test_data['energy_data']:
                        final_energy = test_data['energy_data'][-1]['energy']
                        if final_orders > 0:
                            energy_per_order_values.append(final_energy / final_orders)
        
        avg_energy_per_order.append(np.mean(energy_per_order_values) if energy_per_order_values else 0)
    
    bars = ax6.bar(robot_counts, avg_energy_per_order, color='lightgreen', edgecolor='darkgreen')
    ax6.set_xlabel('Number of Robots')
    ax6.set_ylabel('Avg Energy per Order')
    ax6.set_title('Energy Efficiency by Robot Count')
    ax6.grid(True, alpha=0.3, axis='y')
    
    # 在條形圖上添加數值
    for bar, val in zip(bars, avg_energy_per_order):
        height = bar.get_height()
        if height > 0:
            ax6.text(bar.get_x() + bar.get_width()/2., height,
                    f'{val:.1f}', ha='center', va='bottom')
    
    plt.tight_layout()
    
    # 保存圖表
    output_file = result_path / 'time_series_analysis.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"圖表已保存至: {output_file}")
    
    # 生成摘要報告
    generate_summary_report(all_data, result_path)
    
    # plt.show()  # 註釋掉以避免阻塞

def generate_summary_report(all_data, result_path):
    """生成文字摘要報告"""
    report_lines = []
    report_lines.append("# 容量測試時間序列分析報告")
    report_lines.append(f"\n生成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append("\n## 測試摘要")
    
    # 按機器人數量分組統計
    robot_stats = {}
    for key, test_data in all_data.items():
        robot_count = test_data['robot_count']
        if robot_count not in robot_stats:
            robot_stats[robot_count] = []
        
        if test_data['data']:
            final_data = test_data['data'][-1]
            robot_stats[robot_count].append({
                'run_index': test_data['run_index'],
                'completed_orders': final_data['completed_orders'],
                'total_orders': final_data['total_orders'],
                'completion_rate': final_data['completion_rate']
            })
    
    report_lines.append("\n| 機器人數量 | 平均完成訂單 | 完成率範圍 | 穩定性評分 |")
    report_lines.append("|:---:|:---:|:---:|:---:|")
    
    for count in sorted(robot_stats.keys()):
        runs = robot_stats[count]
        completed_orders = [r['completed_orders'] for r in runs]
        completion_rates = [r['completion_rate'] for r in runs]
        
        avg_completed = np.mean(completed_orders)
        min_rate = min(completion_rates) * 100
        max_rate = max(completion_rates) * 100
        std_dev = np.std(completed_orders)
        
        # 穩定性評分（標準差越小越好）
        if std_dev == 0:
            stability = "極佳 ⭐⭐⭐"
        elif std_dev < 5:
            stability = "良好 ⭐⭐"
        elif std_dev < 20:
            stability = "一般 ⭐"
        else:
            stability = "差 ⚠️"
        
        report_lines.append(f"| {count} | {avg_completed:.1f} | {min_rate:.1f}% - {max_rate:.1f}% | {stability} |")
    
    # 保存報告
    report_file = result_path / 'time_series_report.md'
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report_lines))
    
    print(f"報告已保存至: {report_file}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        result_dir = sys.argv[1]
    else:
        # 使用最新的測試結果
        result_dir = "test/results/capacity_test_20250805_151357_76810197"
    
    analyze_capacity_test_results(result_dir)
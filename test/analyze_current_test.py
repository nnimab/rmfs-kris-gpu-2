#!/usr/bin/env python3
"""分析當前正在進行的容量測試"""

import json
import os
import glob
import pandas as pd
from pathlib import Path
import numpy as np

def analyze_capacity_test(test_dir):
    """分析容量測試結果"""
    
    # 收集所有評估結果
    result_files = glob.glob(os.path.join(test_dir, "**/evaluation_results.json"), recursive=True)
    
    all_results = []
    for file_path in result_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if 'results' in data and len(data['results']) > 0:
                    result = data['results'][0]
                    # 從路徑提取機器人數量
                    path_parts = file_path.split(os.sep)
                    for part in path_parts:
                        if part.startswith('robots_') and '_run' in part:
                            robot_count = int(part.split('_')[1])
                            result['robot_count'] = robot_count
                            result['run_index'] = int(part.split('_run')[1].split('_')[0])
                            break
                    all_results.append(result)
        except Exception as e:
            print(f"讀取 {file_path} 時出錯: {e}")
    
    if not all_results:
        print("沒有找到有效的結果數據")
        return
    
    # 轉換為 DataFrame
    df = pd.DataFrame(all_results)
    
    # 按機器人數量分組統計
    print("=" * 80)
    print("容量測試進度報告")
    print("=" * 80)
    print(f"測試目錄: {test_dir}")
    print(f"總測試數: {len(df)}")
    print()
    
    # 統計每個機器人數量的完成情況
    print("測試完成情況:")
    for robot_count in sorted(df['robot_count'].unique()):
        count = len(df[df['robot_count'] == robot_count])
        print(f"  {robot_count} 台機器人: {count}/10 完成")
    
    print("\n" + "=" * 80)
    print("性能指標統計表")
    print("=" * 80)
    
    # 創建統計表
    stats = []
    for robot_count in sorted(df['robot_count'].unique()):
        subset = df[df['robot_count'] == robot_count]
        
        stats.append({
            '機器人數量': robot_count,
            '測試次數': len(subset),
            '完成訂單(平均)': f"{subset['completed_orders'].mean():.1f}",
            '完成訂單(標準差)': f"{subset['completed_orders'].std():.1f}",
            '完成訂單(最小-最大)': f"{subset['completed_orders'].min()}-{subset['completed_orders'].max()}",
            '完成率(%)': f"{subset['completion_rate'].mean()*100:.1f}",
            '平均等待時間': f"{subset['avg_wait_time'].mean():.2f}",
            '機器人利用率': f"{subset['robot_utilization'].mean():.3f}",
            '每訂單能耗': f"{subset['energy_per_order'].mean():.1f}",
            '執行時間(秒)': f"{subset['execution_time'].mean():.0f}",
            '實際ticks': f"{subset['warehouse_final_tick'].mean():.0f}"
        })
    
    stats_df = pd.DataFrame(stats)
    print(stats_df.to_string(index=False))
    
    # 異常檢測
    print("\n" + "=" * 80)
    print("異常檢測")
    print("=" * 80)
    
    anomalies_found = False
    for robot_count in sorted(df['robot_count'].unique()):
        subset = df[df['robot_count'] == robot_count]
        if len(subset) > 1:
            # 檢查完成訂單數的變異係數
            mean_orders = subset['completed_orders'].mean()
            std_orders = subset['completed_orders'].std()
            cv = std_orders / mean_orders if mean_orders > 0 else 0
            
            if cv > 0.1:  # 變異係數大於10%
                anomalies_found = True
                print(f"\n[警告] {robot_count} 台機器人的測試結果變異較大:")
                print(f"   變異係數: {cv:.2%}")
                print(f"   完成訂單數分布: {sorted(subset['completed_orders'].values)}")
                
                # 找出異常的運行
                mean = subset['completed_orders'].mean()
                std = subset['completed_orders'].std()
                for _, row in subset.iterrows():
                    if abs(row['completed_orders'] - mean) > 2 * std:
                        print(f"   異常運行: run{row['run_index']} - {row['completed_orders']} 訂單")
    
    if not anomalies_found:
        print("未發現明顯異常")
    
    # 瓶頸分析
    print("\n" + "=" * 80)
    print("容量瓶頸分析")
    print("=" * 80)
    
    # 計算各指標隨機器人數量的變化
    robot_counts = sorted(df['robot_count'].unique())
    if len(robot_counts) >= 2:
        print("\n指標變化趨勢:")
        
        metrics = {
            '完成率': 'completion_rate',
            '每訂單能耗': 'energy_per_order',
            '執行時間': 'execution_time'
        }
        
        for metric_name, metric_col in metrics.items():
            values = []
            for rc in robot_counts:
                subset = df[df['robot_count'] == rc]
                values.append(subset[metric_col].mean())
            
            # 計算變化率
            if len(values) >= 2:
                changes = []
                for i in range(1, len(values)):
                    change = (values[i] - values[i-1]) / values[i-1] * 100
                    changes.append(f"{robot_counts[i-1]}→{robot_counts[i]}: {change:+.1f}%")
                
                print(f"\n{metric_name}變化:")
                for change in changes:
                    print(f"  {change}")
        
        # 判斷瓶頸
        print("\n瓶頸判斷:")
        completion_rates = [df[df['robot_count'] == rc]['completion_rate'].mean() for rc in robot_counts]
        
        for i, rc in enumerate(robot_counts):
            cr = completion_rates[i]
            if cr < 0.9:
                print(f"[警告] {rc} 台機器人: 完成率 {cr*100:.1f}% < 90%，可能存在瓶頸")
            elif cr < 0.95:
                print(f"[注意] {rc} 台機器人: 完成率 {cr*100:.1f}%，接近系統容量極限")
            else:
                print(f"[正常] {rc} 台機器人: 完成率 {cr*100:.1f}%，系統運行良好")

if __name__ == "__main__":
    test_dir = r"C:\Users\h2388\Desktop\RMFS\rmfs-kris-gpu-1\test\results\capacity_test_20250806_001849_e96aeaff"
    analyze_capacity_test(test_dir)
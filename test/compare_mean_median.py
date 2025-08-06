#!/usr/bin/env python3
"""
比較使用平均數和中位數的差異
"""

import json
import pandas as pd
from pathlib import Path
import numpy as np

def compare_statistics():
    """比較平均數和中位數的統計結果"""
    # 收集所有測試結果
    base_dir = Path("test/results/capacity_test_20250806_001849_e96aeaff")
    all_data = []
    
    # 遍歷所有測試結果
    for workspace_dir in base_dir.glob("workspaces/*"):
        if not workspace_dir.is_dir():
            continue
            
        # 提取機器人數量
        if "robots_30" in workspace_dir.name:
            robot_count = 30
        elif "robots_35" in workspace_dir.name:
            robot_count = 35
        else:
            continue
            
        # 讀取評估結果
        # 查找評估結果文件（可能在子目錄中）
        eval_files = list(workspace_dir.glob("results/*/evaluation_results.json"))
        if not eval_files:
            continue
        eval_file = eval_files[0]
        if eval_file.exists():
            try:
                with open(eval_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data.get('results'), list) and len(data['results']) > 0:
                        result = data['results'][0]
                        result['robot_count'] = robot_count
                        result['test_name'] = workspace_dir.name
                        all_data.append(result)
            except Exception as e:
                print(f"Error reading {eval_file}: {e}")
    
    # 轉換為DataFrame
    df = pd.DataFrame(all_data)
    
    if df.empty:
        print("No data found for comparison")
        return
    
    print(f"Found {len(df)} test results")
    print(f"Robot counts: {sorted(df['robot_count'].unique())}")
    
    # 資料清理（與 capacity_analyzer 相同的邏輯）
    # 第一階段：檢測訂單生成異常
    max_orders_by_robot = df.groupby('robot_count')['total_orders'].max()
    
    anomaly_records = []
    clean_records = []
    
    for robot_count in df['robot_count'].unique():
        group_df = df[df['robot_count'] == robot_count]
        max_orders = max_orders_by_robot[robot_count]
        threshold = max_orders * 0.9
        
        # 訂單生成異常
        order_anomaly_mask = group_df['total_orders'] < threshold
        order_anomaly_df = group_df[order_anomaly_mask]
        
        # 剩餘資料進行性能異常檢測
        df_after_order_filter = group_df[~order_anomaly_mask]
        
        # 性能異常（包含完成率 < 80%）
        performance_anomaly_mask = (
            (df_after_order_filter['completion_rate'] < 0.5) | 
            (df_after_order_filter['completed_orders'] < 100) |
            (df_after_order_filter['completion_rate'] < 0.8)
        )
        performance_anomaly_df = df_after_order_filter[performance_anomaly_mask]
        
        # 收集異常記錄
        for _, row in order_anomaly_df.iterrows():
            anomaly_records.append({
                'robot_count': robot_count,
                'test_name': row['test_name'],
                'reason': f'訂單生成異常 (總訂單: {row["total_orders"]} < {threshold:.0f})'
            })
        
        for _, row in performance_anomaly_df.iterrows():
            anomaly_records.append({
                'robot_count': robot_count,
                'test_name': row['test_name'],
                'reason': f'性能異常 (完成率: {row["completion_rate"]:.1%}, 完成訂單: {row["completed_orders"]})'
            })
        
        # 清理後的資料
        # 找出既不是訂單異常也不是性能異常的記錄
        all_anomaly_indices = set(order_anomaly_df.index) | set(performance_anomaly_df.index)
        clean_df = group_df[~group_df.index.isin(all_anomaly_indices)]
        clean_records.extend(clean_df.to_dict('records'))
    
    # 清理後的DataFrame
    df_clean = pd.DataFrame(clean_records)
    
    print("="*80)
    print("平均數 vs 中位數比較")
    print("="*80)
    
    # 比較不同統計方法
    for robot_count in [30, 35]:
        group_data = df_clean[df_clean['robot_count'] == robot_count]
        
        print(f"\n{robot_count} 台機器人 (n={len(group_data)}):")
        print("-"*60)
        
        # 總能耗
        energy_mean = group_data['total_energy'].mean()
        energy_median = group_data['total_energy'].median()
        energy_std = group_data['total_energy'].std()
        
        print(f"\n總能耗:")
        print(f"  平均數: {energy_mean:,.0f}")
        print(f"  中位數: {energy_median:,.0f}")
        print(f"  標準差: {energy_std:,.0f}")
        print(f"  差異: {abs(energy_mean - energy_median):,.0f} ({abs(energy_mean - energy_median)/energy_mean*100:.1f}%)")
        
        # 顯示具體數值分布
        energies = sorted(group_data['total_energy'].tolist())
        print(f"  具體數值: {[f'{e:,.0f}' for e in energies]}")
        
        # 能耗/訂單
        epo_mean = group_data['energy_per_order'].mean()
        epo_median = group_data['energy_per_order'].median()
        
        print(f"\n能耗/訂單:")
        print(f"  平均數: {epo_mean:.1f}")
        print(f"  中位數: {epo_median:.1f}")
        print(f"  差異: {abs(epo_mean - epo_median):.1f} ({abs(epo_mean - epo_median)/epo_mean*100:.1f}%)")
        
        # 完成率
        cr_mean = group_data['completion_rate'].mean()
        cr_median = group_data['completion_rate'].median()
        
        print(f"\n完成率:")
        print(f"  平均數: {cr_mean:.1%}")
        print(f"  中位數: {cr_median:.1%}")
        print(f"  差異: {abs(cr_mean - cr_median):.1%}")
    
    # 比較30和35的能耗
    print("\n" + "="*60)
    print("30 vs 35 機器人能耗比較")
    print("="*60)
    
    energy_30_mean = df_clean[df_clean['robot_count'] == 30]['total_energy'].mean()
    energy_30_median = df_clean[df_clean['robot_count'] == 30]['total_energy'].median()
    energy_35_mean = df_clean[df_clean['robot_count'] == 35]['total_energy'].mean()
    energy_35_median = df_clean[df_clean['robot_count'] == 35]['total_energy'].median()
    
    print(f"\n使用平均數:")
    print(f"  30台: {energy_30_mean:,.0f}")
    print(f"  35台: {energy_35_mean:,.0f}")
    print(f"  35台是否低於30台: {'是' if energy_35_mean < energy_30_mean else '否'}")
    
    print(f"\n使用中位數:")
    print(f"  30台: {energy_30_median:,.0f}")
    print(f"  35台: {energy_35_median:,.0f}")
    print(f"  35台是否低於30台: {'是' if energy_35_median < energy_30_median else '否'}")
    
    # 顯示被清理掉的資料
    print("\n" + "="*60)
    print("被清理的異常資料")
    print("="*60)
    
    anomaly_df = pd.DataFrame(anomaly_records)
    for robot_count in [30, 35]:
        anomalies = anomaly_df[anomaly_df['robot_count'] == robot_count]
        if len(anomalies) > 0:
            print(f"\n{robot_count}台機器人的異常資料 ({len(anomalies)}筆):")
            for _, row in anomalies.iterrows():
                print(f"  - {row['test_name']}: {row['reason']}")

if __name__ == "__main__":
    compare_statistics()
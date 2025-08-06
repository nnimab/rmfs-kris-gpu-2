#!/usr/bin/env python3
"""
比較30台和35台機器人的能耗數據
"""

import json
import pandas as pd
from pathlib import Path
from typing import Dict, List
import numpy as np

def analyze_robot_energy():
    """分析機器人能耗問題"""
    # 收集所有測試結果
    base_dir = Path("test/results")
    data_30 = []
    data_35 = []
    
    # 遍歷所有測試結果目錄
    for test_dir in base_dir.iterdir():
        if not test_dir.is_dir() or not test_dir.name.startswith("capacity_test_"):
            continue
            
        # 查找評估結果文件
        for eval_file in test_dir.rglob("evaluation_results.json"):
            if "robots_30" in str(eval_file):
                robot_count = 30
            elif "robots_35" in str(eval_file):
                robot_count = 35
            else:
                continue
                
            try:
                with open(eval_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                # 提取結果
                if 'results' in data:
                    if isinstance(data['results'], list):
                        results = data['results']
                    elif isinstance(data['results'], dict):
                        # 處理多控制器結果
                        results = []
                        for controller, ctrl_results in data['results'].items():
                            if isinstance(ctrl_results, list):
                                for r in ctrl_results:
                                    r['controller'] = controller
                                    results.extend(ctrl_results)
                    else:
                        continue
                        
                    for result in results:
                        result['file_path'] = str(eval_file)
                        result['test_name'] = eval_file.parent.name
                        
                        if robot_count == 30:
                            data_30.append(result)
                        else:
                            data_35.append(result)
                            
            except Exception as e:
                print(f"Error reading {eval_file}: {e}")
                
    # 轉換為DataFrame
    df_30 = pd.DataFrame(data_30) if data_30 else pd.DataFrame()
    df_35 = pd.DataFrame(data_35) if data_35 else pd.DataFrame()
    
    if df_30.empty or df_35.empty:
        print("No data found for comparison")
        return
        
    print("="*80)
    print("Energy Analysis: 30 vs 35 Robots")
    print("="*80)
    
    # 基本統計
    print("\n1. Basic Statistics")
    print("-"*60)
    print(f"\n30 Robots (n={len(df_30)}):")
    print(f"  Avg Total Energy: {df_30['total_energy'].mean():,.0f}")
    print(f"  Median Total Energy: {df_30['total_energy'].median():,.0f}")
    print(f"  Std Dev: {df_30['total_energy'].std():,.0f}")
    print(f"  Range: {df_30['total_energy'].min():,.0f} - {df_30['total_energy'].max():,.0f}")
    
    print(f"\n35 Robots (n={len(df_35)}):")
    print(f"  Avg Total Energy: {df_35['total_energy'].mean():,.0f}")
    print(f"  Median Total Energy: {df_35['total_energy'].median():,.0f}")
    print(f"  Std Dev: {df_35['total_energy'].std():,.0f}")
    print(f"  Range: {df_35['total_energy'].min():,.0f} - {df_35['total_energy'].max():,.0f}")
    
    # 能耗比率
    energy_ratio = df_35['total_energy'].mean() / df_30['total_energy'].mean()
    print(f"\nEnergy Ratio (35/30): {energy_ratio:.2f}")
    print(f"Expected Ratio: {35/30:.2f}")
    print(f"Deviation: {(energy_ratio - 35/30)*100:.1f}%")
    
    # 訂單完成分析
    print("\n2. Order Completion Analysis")
    print("-"*60)
    print(f"\n30 Robots:")
    print(f"  Avg Completed Orders: {df_30['completed_orders'].mean():.0f}")
    print(f"  Avg Total Orders: {df_30['total_orders'].mean():.0f}")
    print(f"  Avg Completion Rate: {df_30['completion_rate'].mean():.1%}")
    
    print(f"\n35 Robots:")
    print(f"  Avg Completed Orders: {df_35['completed_orders'].mean():.0f}")
    print(f"  Avg Total Orders: {df_35['total_orders'].mean():.0f}")
    print(f"  Avg Completion Rate: {df_35['completion_rate'].mean():.1%}")
    
    # 效率分析
    print("\n3. Efficiency Analysis")
    print("-"*60)
    print(f"\n30 Robots:")
    print(f"  Energy per Robot: {df_30['total_energy'].mean()/30:.0f}")
    print(f"  Energy per Order: {df_30['energy_per_order'].mean():.1f}")
    print(f"  Robot Utilization: {df_30['robot_utilization'].mean():.1%}")
    
    print(f"\n35 Robots:")
    print(f"  Energy per Robot: {df_35['total_energy'].mean()/35:.0f}")
    print(f"  Energy per Order: {df_35['energy_per_order'].mean():.1f}")
    print(f"  Robot Utilization: {df_35['robot_utilization'].mean():.1%}")
    
    # 找出異常案例
    print("\n4. Anomaly Detection")
    print("-"*60)
    
    # 35台機器人中能耗低於30台平均值的案例
    avg_energy_30 = df_30['total_energy'].mean()
    low_energy_35 = df_35[df_35['total_energy'] < avg_energy_30]
    
    if len(low_energy_35) > 0:
        print(f"\nFound {len(low_energy_35)} cases where 35 robots use less energy than 30 robot average:")
        print(f"That's {len(low_energy_35)/len(df_35)*100:.1f}% of all 35-robot tests")
        
        # 分析這些異常案例
        print("\nAnomaly case analysis:")
        print(f"  Avg Completed Orders: {low_energy_35['completed_orders'].mean():.0f}")
        print(f"  Avg Completion Rate: {low_energy_35['completion_rate'].mean():.1%}")
        print(f"  Avg Total Energy: {low_energy_35['total_energy'].mean():,.0f}")
        
        # 顯示前5個案例
        print("\nTop 5 anomaly cases:")
        for idx, row in low_energy_35.nsmallest(5, 'total_energy').iterrows():
            print(f"\n  Case: {row['test_name']}")
            print(f"    Total Energy: {row['total_energy']:,.0f}")
            print(f"    Completed Orders: {row['completed_orders']}/{row['total_orders']}")
            print(f"    Completion Rate: {row['completion_rate']:.1%}")
            print(f"    Energy per Order: {row['energy_per_order']:.1f}")
    
    # 結論
    print("\n5. Conclusions")
    print("-"*60)
    print("\nKey Findings:")
    print(f"1. 35-robot energy is {energy_ratio:.2f}x that of 30-robot (expected: 1.17x)")
    
    if energy_ratio < 1.1:
        print("2. ANOMALY DETECTED: 35 robots use less energy than expected!")
        print("   Possible causes:")
        print("   - Order generation issues")
        print("   - Traffic congestion causing robots to wait/idle")
        print("   - System deadlocks reducing robot activity")
        print("   - Performance issues preventing normal operation")
    else:
        print("2. Energy consumption scales roughly as expected")
        
    # 建議的數據清理閾值
    print("\n6. Data Cleaning Recommendations")
    print("-"*60)
    print("Based on the analysis, consider filtering out tests with:")
    print("- Completion rate < 80%")
    print("- Completed orders < 100")
    print("- Total orders < 90% of maximum")
    
    # 保存詳細報告
    report = {
        'summary': {
            '30_robots': {
                'count': len(df_30),
                'avg_energy': float(df_30['total_energy'].mean()),
                'avg_orders': float(df_30['completed_orders'].mean()),
                'avg_completion_rate': float(df_30['completion_rate'].mean())
            },
            '35_robots': {
                'count': len(df_35),
                'avg_energy': float(df_35['total_energy'].mean()),
                'avg_orders': float(df_35['completed_orders'].mean()),
                'avg_completion_rate': float(df_35['completion_rate'].mean())
            },
            'energy_ratio': float(energy_ratio),
            'anomaly_count': len(low_energy_35) if 'low_energy_35' in locals() else 0
        }
    }
    
    report_path = Path("test/results/energy_comparison_report.json")
    report_path.parent.mkdir(exist_ok=True)
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
        
    print(f"\nDetailed report saved to: {report_path}")

if __name__ == "__main__":
    analyze_robot_energy()
import json
import pandas as pd
from pathlib import Path
import sys
sys.path.append('.')

# 導入容量分析器
from capacity_analyzer import CapacityAnalyzer

# 初始化分析器
results_dir = Path(r"C:\Users\h2388\Desktop\RMFS\rmfs-kris-gpu-1\test\results\capacity_test_20250806_001849_e96aeaff")
analyzer = CapacityAnalyzer(results_dir)

# 載入和處理數據
if analyzer.load_test_data():
    if analyzer.process_data():
        # 檢查處理後的數據
        df = analyzer.processed_data.get('df')
        if df is not None:
            print("=== 圖表使用的數據（清洗後）===")
            
            # 按機器人數量分組計算平均值
            grouped = df.groupby('robot_count').agg({
                'total_energy': 'mean',
                'completed_orders': 'mean',
                'energy_per_order': 'mean'
            })
            
            print("\n機器人數量 | 平均總能源 | 平均完成訂單 | 平均每訂單能源")
            print("-" * 60)
            for robot_count, row in grouped.iterrows():
                print(f"{robot_count:10d} | {row['total_energy']:10.0f} | {row['completed_orders']:12.1f} | {row['energy_per_order']:14.1f}")
            
            # 檢查清洗統計
            print("\n=== 清洗統計 ===")
            for robot_count, stats in analyzer.cleaning_stats.items():
                if robot_count != 'overall':
                    print(f"\n{robot_count} 機器人：")
                    print(f"  原始: {stats['original_count']} 筆")
                    print(f"  清洗後: {stats['cleaned_count']} 筆")
                    print(f"  移除: {stats['removed_count']} 筆")
            
            # 檢查被移除的數據
            print("\n=== 被移除的數據 ===")
            for outlier in analyzer.outliers_removed:
                print(f"{outlier['robot_count']} 機器人: {outlier['reason']}")
                print(f"  完成: {outlier['completed_orders']}/{outlier['total_orders']} ({outlier['completion_rate']:.1%})")
        else:
            print("沒有處理後的數據")
    else:
        print("數據處理失敗")
else:
    print("數據載入失敗")
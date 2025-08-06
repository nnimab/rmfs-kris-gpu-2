import json
import glob
import numpy as np
import pandas as pd

# 查找所有評估結果
test_dir = r"C:\Users\h2388\Desktop\RMFS\rmfs-kris-gpu-1\test\results\capacity_test_20250806_001849_e96aeaff"
pattern = f"{test_dir}\\workspaces\\robots_*\\results\\*\\evaluation_results.json"
files = glob.glob(pattern)

print(f"找到 {len(files)} 個評估結果")
print("=" * 80)

# 收集所有數據
all_data = []
for file in files:
    try:
        with open(file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if 'results' in data and data['results']:
            result = data['results'][0]
            
            # 從路徑提取機器人數量和運行編號
            workspace_name = file.split('\\')[-4]  # e.g., robots_30_run0_b1500c8a_robots_30
            parts = workspace_name.split('_')
            robot_count = int(parts[1])
            
            all_data.append({
                'robot_count': robot_count,
                'run': workspace_name,
                'completed_orders': result.get('completed_orders', 0),
                'total_orders': result.get('total_orders', 0),
                'completion_rate': result.get('completion_rate', 0),
                'avg_tick_time': result.get('avg_tick_time', 0)
            })
    except Exception as e:
        continue

# 轉換為 DataFrame
df = pd.DataFrame(all_data)

# 標記訂單生成異常（總訂單 < 400）
df['order_generation_anomaly'] = df['total_orders'] < 400

print("\n### 訂單生成異常分析（總訂單 < 400）###\n")

# 按機器人數量分組統計
for robot_count in sorted(df['robot_count'].unique()):
    robot_df = df[df['robot_count'] == robot_count]
    anomaly_df = robot_df[robot_df['order_generation_anomaly']]
    
    print(f"\n{robot_count} 機器人配置：")
    print(f"  總運行數: {len(robot_df)}")
    print(f"  訂單生成異常數: {len(anomaly_df)} ({len(anomaly_df)/len(robot_df)*100:.0f}%)")
    
    if len(anomaly_df) > 0:
        print(f"  異常運行詳情:")
        for _, row in anomaly_df.iterrows():
            print(f"    - {row['run']}: {row['total_orders']} 訂單")

# 剔除訂單生成異常後的統計
print("\n### 剔除訂單生成異常後的統計 ###\n")

df_cleaned = df[~df['order_generation_anomaly']]

# 創建對比表格
comparison_data = []

for robot_count in sorted(df['robot_count'].unique()):
    # 原始數據
    robot_df_orig = df[df['robot_count'] == robot_count]
    # 清洗後數據
    robot_df_clean = df_cleaned[df_cleaned['robot_count'] == robot_count]
    
    comparison_data.append({
        'robot_count': robot_count,
        'orig_count': len(robot_df_orig),
        'clean_count': len(robot_df_clean),
        'removed_count': len(robot_df_orig) - len(robot_df_clean),
        'orig_avg_completed': robot_df_orig['completed_orders'].mean(),
        'clean_avg_completed': robot_df_clean['completed_orders'].mean() if len(robot_df_clean) > 0 else 0,
        'orig_avg_rate': robot_df_orig['completion_rate'].mean(),
        'clean_avg_rate': robot_df_clean['completion_rate'].mean() if len(robot_df_clean) > 0 else 0,
        'orig_std': robot_df_orig['completed_orders'].std(),
        'clean_std': robot_df_clean['completed_orders'].std() if len(robot_df_clean) > 1 else 0
    })

# 轉換為 DataFrame 並顯示
comp_df = pd.DataFrame(comparison_data)

print("| 機器人 | 原始數量 | 清洗後 | 移除 | 原始平均完成 | 清洗後平均完成 | 改善幅度 |")
print("|--------|----------|--------|------|--------------|----------------|----------|")
for _, row in comp_df.iterrows():
    improvement = ((row['clean_avg_completed'] - row['orig_avg_completed']) / row['orig_avg_completed'] * 100) if row['orig_avg_completed'] > 0 else 0
    print(f"| {int(row['robot_count']):6d} | {int(row['orig_count']):8d} | {int(row['clean_count']):6d} | {int(row['removed_count']):4d} | "
          f"{row['orig_avg_completed']:12.1f} | {row['clean_avg_completed']:14.1f} | {improvement:+7.1f}% |")

print("\n| 機器人 | 原始完成率 | 清洗後完成率 | 原始標準差 | 清洗後標準差 |")
print("|--------|------------|--------------|------------|--------------|")
for _, row in comp_df.iterrows():
    print(f"| {int(row['robot_count']):6d} | {row['orig_avg_rate']:10.1%} | {row['clean_avg_rate']:12.1%} | "
          f"{row['orig_std']:10.1f} | {row['clean_std']:12.1f} |")

# 特別分析 30 機器人
print("\n### 30 機器人配置詳細分析 ###\n")
robot_30_df = df[df['robot_count'] == 30]
print("原始數據（所有運行）：")
for _, row in robot_30_df.iterrows():
    anomaly_flag = " [訂單生成異常]" if row['order_generation_anomaly'] else ""
    print(f"  {row['run']}: {row['completed_orders']}/{row['total_orders']} "
          f"(完成率: {row['completion_rate']:.1%}){anomaly_flag}")

robot_30_clean = df_cleaned[df_cleaned['robot_count'] == 30]
print(f"\n剔除訂單生成異常後（剩餘 {len(robot_30_clean)} 筆）：")
print(f"  平均完成訂單: {robot_30_clean['completed_orders'].mean():.1f}")
print(f"  平均完成率: {robot_30_clean['completion_rate'].mean():.1%}")
print(f"  標準差: {robot_30_clean['completed_orders'].std():.1f}")

# 檢查執行時間異常
print("\n### 執行時間分析（可能的死鎖檢測）###")
# 只分析正常訂單生成的數據
df_normal = df[~df['order_generation_anomaly']]
# 計算每個機器人配置的平均 tick 時間
avg_tick_by_robot = df_normal.groupby('robot_count')['avg_tick_time'].agg(['mean', 'std', 'max'])
print("\n| 機器人 | 平均tick時間(秒) | 標準差 | 最大值 | 異常倍數 |")
print("|--------|------------------|--------|--------|----------|")
for robot_count, row in avg_tick_by_robot.iterrows():
    anomaly_factor = row['max'] / row['mean'] if row['mean'] > 0 else 0
    print(f"| {robot_count:6d} | {row['mean']:16.4f} | {row['std']:6.4f} | {row['max']:6.4f} | {anomaly_factor:8.1f}x |")
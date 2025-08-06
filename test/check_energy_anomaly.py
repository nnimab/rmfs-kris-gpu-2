import json
import glob
import pandas as pd
import numpy as np

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
            workspace_name = file.split('\\')[-4]
            parts = workspace_name.split('_')
            robot_count = int(parts[1])
            
            all_data.append({
                'robot_count': robot_count,
                'run': workspace_name,
                'completed_orders': result.get('completed_orders', 0),
                'total_orders': result.get('total_orders', 0),
                'total_energy': result.get('total_energy', 0),
                'energy_per_order': result.get('energy_per_order', 0),
                'warehouse_final_tick': result.get('warehouse_final_tick', 0),
                'evaluation_ticks': result.get('evaluation_ticks', 0)
            })
    except Exception as e:
        continue

# 轉換為 DataFrame
df = pd.DataFrame(all_data)

# 按機器人數量分組分析
print("\n### 各機器人配置的能源消耗分析 ###\n")
print("| 機器人 | 運行數 | 平均總能源 | 最小總能源 | 最大總能源 | 標準差 | 平均每訂單能源 |")
print("|--------|--------|-----------|-----------|-----------|--------|---------------|")

for robot_count in sorted(df['robot_count'].unique()):
    robot_df = df[df['robot_count'] == robot_count]
    
    avg_energy = robot_df['total_energy'].mean()
    min_energy = robot_df['total_energy'].min()
    max_energy = robot_df['total_energy'].max()
    std_energy = robot_df['total_energy'].std()
    avg_per_order = robot_df['energy_per_order'].mean()
    
    print(f"| {robot_count:6d} | {len(robot_df):6d} | {avg_energy:9.0f} | {min_energy:9.0f} | "
          f"{max_energy:9.0f} | {std_energy:6.0f} | {avg_per_order:13.1f} |")

# 特別分析 35 機器人
print("\n### 35 機器人詳細分析 ###\n")
robot_35_df = df[df['robot_count'] == 35].sort_values('total_energy')

print("所有 35 機器人運行的能源數據：")
for _, row in robot_35_df.iterrows():
    print(f"{row['run']}: ")
    print(f"  總能源: {row['total_energy']:,.0f}")
    print(f"  完成訂單: {row['completed_orders']}/{row['total_orders']}")
    print(f"  每訂單能源: {row['energy_per_order']:.1f}")
    print(f"  倉庫最終 tick: {row['warehouse_final_tick']:.0f}")
    print()

# 檢查是否有異常低的能源消耗
print("\n### 異常能源消耗檢測 ###\n")

# 計算預期的能源消耗趨勢
energy_by_robot = df.groupby('robot_count')['total_energy'].mean().sort_index()
print("平均總能源消耗趨勢：")
for rc, energy in energy_by_robot.items():
    print(f"  {rc} 機器人: {energy:,.0f}")

# 檢查 30 和 40 機器人的數據作為對比
print("\n### 30 機器人能源數據（對比）###")
robot_30_df = df[df['robot_count'] == 30]
print(f"30 機器人平均總能源: {robot_30_df['total_energy'].mean():,.0f}")
print(f"30 機器人總能源範圍: {robot_30_df['total_energy'].min():,.0f} - {robot_30_df['total_energy'].max():,.0f}")

print("\n### 40 機器人能源數據（對比）###")
robot_40_df = df[df['robot_count'] == 40]
print(f"40 機器人平均總能源: {robot_40_df['total_energy'].mean():,.0f}")
print(f"40 機器人總能源範圍: {robot_40_df['total_energy'].min():,.0f} - {robot_40_df['total_energy'].max():,.0f}")

# 分析是否有數據清洗影響
print("\n### 檢查是否受數據清洗影響 ###")
# 標記訂單生成異常
df['order_anomaly'] = df['total_orders'] < df['total_orders'].max() * 0.9

for robot_count in [30, 35, 40]:
    robot_df = df[df['robot_count'] == robot_count]
    normal_df = robot_df[~robot_df['order_anomaly']]
    
    print(f"\n{robot_count} 機器人：")
    print(f"  原始數據平均能源: {robot_df['total_energy'].mean():,.0f}")
    print(f"  排除異常後平均能源: {normal_df['total_energy'].mean():,.0f} (剩餘 {len(normal_df)} 筆)")
    
# 檢查能源與完成訂單的關係
print("\n### 能源消耗與完成訂單的相關性 ###")
for robot_count in [30, 35, 40]:
    robot_df = df[df['robot_count'] == robot_count]
    if len(robot_df) > 1:
        correlation = robot_df['total_energy'].corr(robot_df['completed_orders'])
        print(f"{robot_count} 機器人: 相關係數 = {correlation:.3f}")
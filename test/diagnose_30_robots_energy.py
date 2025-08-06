import json
import glob
import pandas as pd
import numpy as np

# 查找所有評估結果
test_dir = r"C:\Users\h2388\Desktop\RMFS\rmfs-kris-gpu-1\test\results\capacity_test_20250806_001849_e96aeaff"

# 收集 25, 30, 35 機器人的數據進行比較
data_by_robot = {25: [], 30: [], 35: []}

for robot_count in [25, 30, 35]:
    pattern = f"{test_dir}\\workspaces\\robots_{robot_count}_*\\results\\*\\evaluation_results.json"
    files = glob.glob(pattern)
    
    for file in files:
        try:
            with open(file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if 'results' in data and data['results']:
                result = data['results'][0]
                run_name = file.split('\\')[-3]
                
                data_by_robot[robot_count].append({
                    'run': run_name,
                    'completed_orders': result.get('completed_orders', 0),
                    'total_orders': result.get('total_orders', 0),
                    'completion_rate': result.get('completion_rate', 0),
                    'total_energy': result.get('total_energy', 0),
                    'energy_per_order': result.get('energy_per_order', 0)
                })
        except Exception as e:
            continue

# 分析每個機器人配置
print("=" * 100)
print("25, 30, 35 機器人能源消耗詳細分析")
print("=" * 100)

for robot_count in [25, 30, 35]:
    df = pd.DataFrame(data_by_robot[robot_count])
    df = df.sort_values('total_energy')
    
    print(f"\n{robot_count} 機器人配置（按總能源排序）：")
    print("-" * 100)
    
    for _, row in df.iterrows():
        print(f"{row['run']}:")
        print(f"  完成: {row['completed_orders']}/{row['total_orders']} ({row['completion_rate']:.1%})")
        print(f"  總能源: {row['total_energy']:,.0f}")
        print(f"  每訂單能源: {row['energy_per_order']:.1f}")
    
    # 統計
    print(f"\n統計：")
    print(f"  平均總能源: {df['total_energy'].mean():,.0f}")
    print(f"  能源範圍: {df['total_energy'].min():,.0f} - {df['total_energy'].max():,.0f}")
    print(f"  標準差: {df['total_energy'].std():,.0f}")

# 特別分析 30 機器人的異常低能源數據
print("\n" + "=" * 100)
print("30 機器人異常低能源數據分析：")
print("=" * 100)

df_30 = pd.DataFrame(data_by_robot[30])

# 找出能源特別低的數據
low_energy = df_30[df_30['total_energy'] < 10000]
if not low_energy.empty:
    print("\n能源 < 10,000 的運行：")
    for _, row in low_energy.iterrows():
        print(f"- {row['run']}: {row['total_energy']:,.0f} (完成 {row['completed_orders']}/{row['total_orders']})")

# 檢查訂單數和能源的關係
print("\n訂單數與能源消耗的關係：")
print("完成訂單 | 總訂單 | 總能源")
print("-" * 40)
for _, row in df_30.sort_values('completed_orders').iterrows():
    print(f"{row['completed_orders']:8d} | {row['total_orders']:6d} | {row['total_energy']:10,.0f}")

# 應用清洗規則看看會保留哪些
max_orders = max([d['total_orders'] for robot in data_by_robot.values() for d in robot])
order_threshold = max_orders * 0.9

print(f"\n清洗規則檢查（訂單閾值: {order_threshold:.0f}）：")
normal_30 = df_30[(df_30['total_orders'] >= order_threshold) & 
                  (df_30['completion_rate'] >= 0.5) & 
                  (df_30['completed_orders'] >= 100)]

print(f"30 機器人正常數據（{len(normal_30)}筆）：")
if len(normal_30) > 0:
    print(f"  平均總能源: {normal_30['total_energy'].mean():,.0f}")
    print(f"  能源範圍: {normal_30['total_energy'].min():,.0f} - {normal_30['total_energy'].max():,.0f}")

# 和其他機器人比較
print("\n\n與其他機器人配置比較（只看正常數據）：")
for robot_count in [25, 30, 35]:
    df = pd.DataFrame(data_by_robot[robot_count])
    normal = df[(df['total_orders'] >= order_threshold) & 
                (df['completion_rate'] >= 0.5) & 
                (df['completed_orders'] >= 100)]
    if len(normal) > 0:
        print(f"{robot_count} 機器人: 平均能源 {normal['total_energy'].mean():,.0f} (n={len(normal)})")
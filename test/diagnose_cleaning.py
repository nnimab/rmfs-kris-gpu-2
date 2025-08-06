import json
import glob
import pandas as pd
import numpy as np

# 查找所有評估結果
test_dir = r"C:\Users\h2388\Desktop\RMFS\rmfs-kris-gpu-1\test\results\capacity_test_20250806_001849_e96aeaff"
pattern = f"{test_dir}\\workspaces\\robots_*\\results\\*\\evaluation_results.json"
files = glob.glob(pattern)

# 收集所有數據
all_data = []
for file in files:
    try:
        with open(file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if 'results' in data and data['results']:
            result = data['results'][0]
            workspace_name = file.split('\\')[-4]
            parts = workspace_name.split('_')
            robot_count = int(parts[1])
            
            all_data.append({
                'robot_count': robot_count,
                'run': workspace_name,
                'completed_orders': result.get('completed_orders', 0),
                'total_orders': result.get('total_orders', 0),
                'completion_rate': result.get('completion_rate', 0),
                'total_energy': result.get('total_energy', 0),
                'energy_per_order': result.get('energy_per_order', 0)
            })
    except Exception as e:
        continue

df = pd.DataFrame(all_data)

# 應用清洗規則
max_total_orders = df['total_orders'].max()
order_threshold = max_total_orders * 0.9

print(f"訂單生成異常閾值: {order_threshold:.0f} (最大訂單數 {max_total_orders} 的 90%)")
print("=" * 80)

# 標記異常
df['order_anomaly'] = df['total_orders'] < order_threshold
df['performance_anomaly'] = df['completion_rate'] < 0.5
df['any_anomaly'] = df['order_anomaly'] | df['performance_anomaly']

# 按機器人數量分析
for robot_count in sorted(df['robot_count'].unique()):
    robot_df = df[df['robot_count'] == robot_count]
    clean_df = robot_df[~robot_df['any_anomaly']]
    
    print(f"\n{robot_count} 機器人配置：")
    print(f"  總數據: {len(robot_df)}")
    print(f"  訂單生成異常: {robot_df['order_anomaly'].sum()}")
    print(f"  性能異常: {robot_df['performance_anomaly'].sum()}")
    print(f"  清洗後剩餘: {len(clean_df)}")
    
    if len(robot_df) > 0:
        print(f"\n  原始數據:")
        print(f"    平均完成訂單: {robot_df['completed_orders'].mean():.1f}")
        print(f"    平均總能源: {robot_df['total_energy'].mean():,.0f}")
        print(f"    平均每訂單能源: {robot_df['energy_per_order'].mean():.1f}")
    
    if len(clean_df) > 0:
        print(f"\n  清洗後數據:")
        print(f"    平均完成訂單: {clean_df['completed_orders'].mean():.1f}")
        print(f"    平均總能源: {clean_df['total_energy'].mean():,.0f}")
        print(f"    平均每訂單能源: {clean_df['energy_per_order'].mean():.1f}")
    
    # 顯示被移除的數據
    removed_df = robot_df[robot_df['any_anomaly']]
    if len(removed_df) > 0:
        print(f"\n  被移除的數據:")
        for _, row in removed_df.iterrows():
            reason = []
            if row['order_anomaly']:
                reason.append(f"訂單生成異常({row['total_orders']})")
            if row['performance_anomaly']:
                reason.append(f"性能異常({row['completion_rate']:.1%})")
            print(f"    {row['run']}: {', '.join(reason)}")

# 總體能源趨勢
print("\n" + "=" * 80)
print("清洗後的總能源消耗趨勢：")
clean_df = df[~df['any_anomaly']]
energy_trend = clean_df.groupby('robot_count')['total_energy'].mean().sort_index()
for rc, energy in energy_trend.items():
    print(f"  {rc} 機器人: {energy:,.0f}")
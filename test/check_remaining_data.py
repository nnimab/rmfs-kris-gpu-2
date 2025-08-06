import json
import glob
import pandas as pd

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
                'total_energy': result.get('total_energy', 0)
            })
    except Exception as e:
        continue

df = pd.DataFrame(all_data)

# 應用新的清洗規則
max_total_orders = df['total_orders'].max()
order_threshold = max_total_orders * 0.9

df['order_anomaly'] = df['total_orders'] < order_threshold
df['performance_anomaly'] = (
    (df['completion_rate'] < 0.5) | 
    ((df['completion_rate'] < 0.8) & (df['completed_orders'] < 350))
)
df['any_anomaly'] = df['order_anomaly'] | df['performance_anomaly']

# 檢查 30 和 40 機器人的具體情況
for robot_count in [30, 40]:
    print(f"\n{robot_count} 機器人配置詳情：")
    print("=" * 80)
    
    robot_df = df[df['robot_count'] == robot_count].sort_values('completed_orders')
    
    for _, row in robot_df.iterrows():
        status = "保留" if not row['any_anomaly'] else "移除"
        reasons = []
        if row['order_anomaly']:
            reasons.append("訂單生成異常")
        if row['performance_anomaly']:
            reasons.append("性能異常")
        
        print(f"{status} - {row['run']}: {row['completed_orders']}/{row['total_orders']} "
              f"({row['completion_rate']:.1%}) 能源: {row['total_energy']:,.0f}")
        if reasons:
            print(f"    原因: {', '.join(reasons)}")
    
    # 計算保留數據的統計
    clean_df = robot_df[~robot_df['any_anomaly']]
    if len(clean_df) > 0:
        print(f"\n保留的數據統計：")
        print(f"  數量: {len(clean_df)}")
        print(f"  平均總能源: {clean_df['total_energy'].mean():,.0f}")
        print(f"  能源範圍: {clean_df['total_energy'].min():,.0f} - {clean_df['total_energy'].max():,.0f}")

# 建議
print("\n" + "=" * 80)
print("問題分析：")
print("1. 40 機器人移除了 3 筆 60%+ 完成率的數據，這些可能是正常數據")
print("2. 規則 '完成率 < 80% 且 完成訂單 < 350' 太嚴格")
print("\n建議調整為：")
print("- 性能異常：完成率 < 50% 或 完成訂單 < 100")
print("- 這樣可以保留大部分正常數據，只移除真正的異常")
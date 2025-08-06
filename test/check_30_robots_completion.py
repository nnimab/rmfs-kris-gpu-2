import json
import glob
import pandas as pd

# 查找所有 30 機器人的評估結果
test_dir = r"C:\Users\h2388\Desktop\RMFS\rmfs-kris-gpu-1\test\results\capacity_test_20250806_001849_e96aeaff"
pattern = f"{test_dir}\\workspaces\\robots_30*\\results\\*\\evaluation_results.json"
files = glob.glob(pattern)

print(f"找到 {len(files)} 個 30 機器人的評估結果")
print("=" * 80)

# 收集數據
data_30 = []
for file in sorted(files):
    try:
        with open(file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if 'results' in data and data['results']:
            result = data['results'][0]
            run_name = file.split('\\')[-3]
            
            data_30.append({
                'run': run_name,
                'completed_orders': result.get('completed_orders', 0),
                'total_orders': result.get('total_orders', 0),
                'completion_rate': result.get('completion_rate', 0),
                'total_energy': result.get('total_energy', 0)
            })
    except Exception as e:
        continue

# 轉換為 DataFrame
df = pd.DataFrame(data_30)
df = df.sort_values('completed_orders')

print("30 機器人所有運行數據（按完成訂單排序）：")
print("-" * 80)
for _, row in df.iterrows():
    print(f"{row['run']}: {row['completed_orders']}/{row['total_orders']} "
          f"(完成率: {row['completion_rate']:.1%})")

# 標記異常
max_orders = df['total_orders'].max()
order_threshold = max_orders * 0.9
df['order_anomaly'] = df['total_orders'] < order_threshold
df['performance_anomaly'] = df['completion_rate'] < 0.5
df['any_anomaly'] = df['order_anomaly'] | df['performance_anomaly']

print(f"\n異常檢測規則：")
print(f"- 訂單生成異常：總訂單 < {order_threshold:.0f} (最大訂單 {max_orders} 的 90%)")
print(f"- 性能異常：完成率 < 50%")

# 分析清洗前後
print(f"\n清洗前統計（所有 {len(df)} 筆）：")
print(f"- 平均完成訂單: {df['completed_orders'].mean():.1f}")
print(f"- 平均完成率: {df['completion_rate'].mean():.1%}")
print(f"- 完成率範圍: {df['completion_rate'].min():.1%} - {df['completion_rate'].max():.1%}")

# 清洗後
df_clean = df[~df['any_anomaly']]
print(f"\n清洗後統計（剩餘 {len(df_clean)} 筆）：")
if len(df_clean) > 0:
    print(f"- 平均完成訂單: {df_clean['completed_orders'].mean():.1f}")
    print(f"- 平均完成率: {df_clean['completion_rate'].mean():.1%}")
    print(f"- 完成率範圍: {df_clean['completion_rate'].min():.1%} - {df_clean['completion_rate'].max():.1%}")

# 被移除的數據
removed = df[df['any_anomaly']]
if len(removed) > 0:
    print(f"\n被移除的 {len(removed)} 筆數據：")
    for _, row in removed.iterrows():
        reasons = []
        if row['order_anomaly']:
            reasons.append(f"訂單生成異常({row['total_orders']})")
        if row['performance_anomaly']:
            reasons.append(f"性能異常({row['completion_rate']:.1%})")
        print(f"- {row['run']}: {', '.join(reasons)}")

# 特別檢查 320 訂單的那筆
run6_data = df[df['completed_orders'] == 320]
if not run6_data.empty:
    print(f"\n特別注意 run6 (320 訂單)：")
    row = run6_data.iloc[0]
    print(f"- 完成: {row['completed_orders']}/{row['total_orders']}")
    print(f"- 完成率: {row['completion_rate']:.1%}")
    print(f"- 是否被標記為異常: {'是' if row['any_anomaly'] else '否'}")
    if not row['any_anomaly']:
        print("- 結論：這筆數據沒有被移除，會拉低平均完成率！")
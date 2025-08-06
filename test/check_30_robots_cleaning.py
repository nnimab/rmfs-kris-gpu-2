import json
import glob
import numpy as np
import pandas as pd

# 查找所有 30 機器人的評估結果
pattern = r"C:\Users\h2388\Desktop\RMFS\rmfs-kris-gpu-1\test\results\capacity_test_20250806_001849_e96aeaff\workspaces\robots_30*\results\*\evaluation_results.json"
files = glob.glob(pattern)

print(f"找到 {len(files)} 個 30 機器人的評估結果")
print("=" * 60)

# 收集所有數據
orders_data = []
for file in sorted(files):
    try:
        with open(file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if 'results' in data and data['results']:
            result = data['results'][0]
            completed = result.get('completed_orders', 0)
            total = result.get('total_orders', 0)
            
            # 從路徑提取 run 編號
            run_match = file.split('\\')[-3]  # e.g., robots_30_run0_b1500c8a
            
            orders_data.append({
                'run': run_match,
                'completed_orders': completed,
                'total_orders': total
            })
    except Exception as e:
        print(f"處理 {file} 時發生錯誤: {e}")

# 轉換為 DataFrame
df = pd.DataFrame(orders_data)
df['completion_rate'] = df['completed_orders'] / df['total_orders']

print("\n原始數據：")
for _, row in df.iterrows():
    print(f"{row['run']}: {row['completed_orders']}/{row['total_orders']} (完成率: {row['completion_rate']:.1%})")

# 計算 IQR
completed_values = df['completed_orders'].values
Q1 = np.percentile(completed_values, 25)
Q3 = np.percentile(completed_values, 75)
IQR = Q3 - Q1

# 使用 1.5 * IQR 規則
lower_bound = Q1 - 1.5 * IQR
upper_bound = Q3 + 1.5 * IQR

print(f"\nIQR 分析：")
print(f"Q1: {Q1}")
print(f"Q3: {Q3}")
print(f"IQR: {IQR}")
print(f"異常值邊界: [{lower_bound:.1f}, {upper_bound:.1f}]")

# 標記異常值
df['is_outlier_1.5'] = (df['completed_orders'] < lower_bound) | (df['completed_orders'] > upper_bound)

# 使用 2.0 * IQR（更寬鬆）
lower_bound_2 = Q1 - 2.0 * IQR
upper_bound_2 = Q3 + 2.0 * IQR
df['is_outlier_2.0'] = (df['completed_orders'] < lower_bound_2) | (df['completed_orders'] > upper_bound_2)

print(f"\n使用 1.5*IQR 規則的異常值：")
outliers_1_5 = df[df['is_outlier_1.5']]
if len(outliers_1_5) > 0:
    for _, row in outliers_1_5.iterrows():
        print(f"  {row['run']}: {row['completed_orders']} 訂單")
else:
    print("  無異常值被檢測到")

print(f"\n使用 2.0*IQR 規則的異常值：")
outliers_2_0 = df[df['is_outlier_2.0']]
if len(outliers_2_0) > 0:
    for _, row in outliers_2_0.iterrows():
        print(f"  {row['run']}: {row['completed_orders']} 訂單")
else:
    print("  無異常值被檢測到")

# 如果剔除異常值會怎樣？
print("\n=== 剔除分析 ===")

# 計算原始統計
print(f"\n原始數據統計（包含所有 {len(df)} 筆）：")
print(f"平均完成訂單: {df['completed_orders'].mean():.1f}")
print(f"平均完成率: {df['completion_rate'].mean():.1%}")
print(f"標準差: {df['completed_orders'].std():.1f}")

# 如果使用固定閾值（例如完成訂單 < 100）
df['is_poor_performance'] = df['completed_orders'] < 100
poor_performance = df[df['is_poor_performance']]

print(f"\n表現不佳的運行（完成 < 100 訂單）：")
for _, row in poor_performance.iterrows():
    print(f"  {row['run']}: {row['completed_orders']} 訂單")

# 剔除表現不佳後的統計
df_cleaned = df[~df['is_poor_performance']]
print(f"\n剔除表現不佳後的統計（剩餘 {len(df_cleaned)} 筆）：")
if len(df_cleaned) > 0:
    print(f"平均完成訂單: {df_cleaned['completed_orders'].mean():.1f}")
    print(f"平均完成率: {df_cleaned['completion_rate'].mean():.1%}")
    print(f"標準差: {df_cleaned['completed_orders'].std():.1f}")
else:
    print("所有數據都被剔除了！")

# 如果只剔除極端異常值（< 50 訂單）
df['is_extreme_outlier'] = df['completed_orders'] < 50
extreme_outliers = df[df['is_extreme_outlier']]

print(f"\n極端異常值（完成 < 50 訂單）：")
for _, row in extreme_outliers.iterrows():
    print(f"  {row['run']}: {row['completed_orders']} 訂單")

df_cleaned_extreme = df[~df['is_extreme_outlier']]
print(f"\n剔除極端異常值後的統計（剩餘 {len(df_cleaned_extreme)} 筆）：")
print(f"平均完成訂單: {df_cleaned_extreme['completed_orders'].mean():.1f}")
print(f"平均完成率: {df_cleaned_extreme['completion_rate'].mean():.1%}")
print(f"標準差: {df_cleaned_extreme['completed_orders'].std():.1f}")

# 總結
print("\n=== 總結 ===")
print(f"1. IQR 方法無法檢測到異常值（因為異常值恰好在 Q1 位置）")
print(f"2. 如果使用業務規則（< 100 訂單為異常）：")
print(f"   - 剔除 {len(poor_performance)} 筆異常數據")
print(f"   - 平均完成率從 {df['completion_rate'].mean():.1%} 提升到 {df_cleaned['completion_rate'].mean():.1%}")
print(f"3. 建議：使用基於領域知識的固定閾值而非純統計方法")
import json
import glob
import numpy as np

# 查找所有 30 機器人的評估結果
pattern = r"C:\Users\h2388\Desktop\RMFS\rmfs-kris-gpu-1\test\results\capacity_test_20250806_001849_e96aeaff\workspaces\robots_30*\results\*\evaluation_results.json"
files = glob.glob(pattern)

print(f"找到 {len(files)} 個 30 機器人的評估結果")
print("=" * 60)

orders_data = []
for file in sorted(files):
    try:
        with open(file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if 'results' in data and data['results']:
            result = data['results'][0]
            completed = result.get('completed_orders', 0)
            total = result.get('total_orders', 0)
            orders_data.append(completed)
            
            # 從路徑提取 run 編號
            run_match = file.split('\\')[-3]  # e.g., robots_30_run0_b1500c8a
            print(f"{run_match}: 完成 {completed}/{total} 訂單")
    except Exception as e:
        print(f"處理 {file} 時發生錯誤: {e}")

if orders_data:
    print("\n統計摘要:")
    print(f"數據點數量: {len(orders_data)}")
    print(f"完成訂單數: {orders_data}")
    print(f"平均: {np.mean(orders_data):.1f}")
    print(f"標準差: {np.std(orders_data):.1f}")
    print(f"最小值: {min(orders_data)}")
    print(f"最大值: {max(orders_data)}")
    
    # 計算 IQR
    sorted_data = sorted(orders_data)
    n = len(sorted_data)
    q1 = sorted_data[int(n * 0.25)]
    q3 = sorted_data[int(n * 0.75)]
    iqr = q3 - q1
    
    print(f"\nIQR 分析:")
    print(f"Q1: {q1}")
    print(f"Q3: {q3}")
    print(f"IQR: {iqr}")
    
    # 使用 1.5 * IQR 規則
    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr
    print(f"異常值邊界: [{lower_bound:.1f}, {upper_bound:.1f}]")
    
    # 檢查異常值
    outliers = [x for x in orders_data if x < lower_bound or x > upper_bound]
    print(f"\n使用 1.5*IQR 規則找到的異常值: {outliers}")
    
    # 嘗試 2.0 * IQR（更寬鬆的標準）
    lower_bound_2 = q1 - 2.0 * iqr
    upper_bound_2 = q3 + 2.0 * iqr
    outliers_2 = [x for x in orders_data if x < lower_bound_2 or x > upper_bound_2]
    print(f"\n使用 2.0*IQR 規則找到的異常值: {outliers_2}")
    print(f"2.0*IQR 邊界: [{lower_bound_2:.1f}, {upper_bound_2:.1f}]")
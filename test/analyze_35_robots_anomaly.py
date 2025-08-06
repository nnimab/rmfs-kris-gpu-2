import json
import glob
import pandas as pd

# 查找所有評估結果
test_dir = r"C:\Users\h2388\Desktop\RMFS\rmfs-kris-gpu-1\test\results\capacity_test_20250806_001849_e96aeaff"

# 分析 35 機器人的 run5 為什麼能源特別低
print("### 分析 35 機器人 run5 的異常低能源消耗 ###\n")

# 讀取 run5 的數據
run5_file = f"{test_dir}\\workspaces\\robots_35_run5_16967f5d_robots_35\\results\\robots_35_run5_16967f5d\\evaluation_results.json"
with open(run5_file, 'r', encoding='utf-8') as f:
    run5_data = json.load(f)

print("robots_35_run5 詳細數據：")
result = run5_data['results'][0]
print(f"  完成訂單: {result['completed_orders']}/{result['total_orders']}")
print(f"  完成率: {result['completion_rate']:.1%}")
print(f"  總能源: {result['total_energy']:,.0f}")
print(f"  每訂單能源: {result['energy_per_order']:.1f}")
print(f"  平均等待時間: {result['avg_wait_time']}")
print(f"  機器人利用率: {result['robot_utilization']}")
print(f"  倉庫最終 tick: {result['warehouse_final_tick']}")
print(f"  評估 ticks: {result['evaluation_ticks']}")

# 比較其他正常的 35 機器人運行
print("\n\n### 比較其他正常的 35 機器人運行 ###\n")

normal_runs = ['run0', 'run1', 'run2']
for run in normal_runs:
    file_pattern = f"{test_dir}\\workspaces\\robots_35_{run}_*\\results\\*\\evaluation_results.json"
    files = glob.glob(file_pattern)
    if files:
        with open(files[0], 'r', encoding='utf-8') as f:
            data = json.load(f)
        result = data['results'][0]
        print(f"\nrobots_35_{run}:")
        print(f"  完成訂單: {result['completed_orders']}/{result['total_orders']}")
        print(f"  總能源: {result['total_energy']:,.0f}")
        print(f"  每訂單能源: {result['energy_per_order']:.1f}")

# 檢查是否有訂單生成問題
print("\n\n### 檢查訂單文件 ###\n")

# 檢查 run5 的訂單文件
orders_file = f"{test_dir}\\workspaces\\robots_35_run5_16967f5d_robots_35\\output_orders.csv"
try:
    orders_df = pd.read_csv(orders_file)
    print(f"robots_35_run5 訂單文件：")
    print(f"  訂單數量: {len(orders_df)}")
    print(f"  第一個訂單時間: {orders_df['Order Time'].min() if 'Order Time' in orders_df.columns else 'N/A'}")
    print(f"  最後一個訂單時間: {orders_df['Order Time'].max() if 'Order Time' in orders_df.columns else 'N/A'}")
except Exception as e:
    print(f"  讀取訂單文件失敗: {e}")

# 檢查日誌文件
print("\n\n### 檢查運行日誌 ###\n")
log_file = f"{test_dir}\\workspaces\\robots_35_run5_16967f5d_robots_35\\results\\robots_35_run5_16967f5d\\evaluation.log"
try:
    with open(log_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # 查找關鍵信息
    print("日誌關鍵信息：")
    for line in lines[-50:]:  # 最後 50 行
        if 'error' in line.lower() or 'exception' in line.lower():
            print(f"  錯誤: {line.strip()}")
        elif 'completed' in line.lower() and 'orders' in line.lower():
            print(f"  訂單完成: {line.strip()}")
        elif 'final' in line.lower():
            print(f"  最終狀態: {line.strip()}")
except Exception as e:
    print(f"  讀取日誌文件失敗: {e}")

# 統計分析
print("\n\n### 統計分析 ###\n")
print("問題總結：")
print("1. robots_35_run5 只完成了 49 個訂單（11.4%），而其他運行完成了 400+ 訂單")
print("2. 能源消耗與完成訂單數成正比，所以 run5 的能源消耗異常低")
print("3. 這是一個性能問題，不是能源效率提升")
print("\n建議：")
print("1. 在數據清洗時，應該同時考慮完成率過低的情況（例如 < 50%）")
print("2. 或者基於完成訂單數的異常值檢測（例如 < 100 訂單）")
print("3. 這樣可以避免將性能問題誤認為是能源效率的改善")
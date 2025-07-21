#!/usr/bin/env python3
"""
修復現有 assign_order.csv 中未分配的訂單
"""

import os
import pandas as pd
import glob

def fix_assign_orders():
    """檢查並修復所有 assign_order*.csv 檔案中的未分配訂單"""
    
    # 尋找所有 assign_order 檔案
    assign_files = glob.glob('data/input/assign_order*.csv')
    
    if not assign_files:
        print("沒有找到 assign_order*.csv 檔案")
        return
    
    for file_path in assign_files:
        print(f"\n處理檔案：{file_path}")
        
        # 讀取檔案
        df = pd.read_csv(file_path)
        
        # 檢查未分配的訂單
        unassigned = df[(df['assigned_station'].isna()) & (df['order_id'] < 0)]
        
        if len(unassigned) == 0:
            print(f"  所有訂單都已分配")
            continue
        
        print(f"  找到 {len(unassigned['order_id'].unique())} 個未分配的積壓訂單")
        
        # 獲取已分配的站點統計
        station_counts = df[df['assigned_station'].notna()]['assigned_station'].value_counts()
        print(f"  現有站點分配情況：")
        for station, count in station_counts.items():
            print(f"    {station}: {count} 個訂單")
        
        # 獲取所有可用的站點
        all_stations = [f'picker{i}' for i in range(6)]  # 假設有 6 個揀貨站
        
        # 循環分配未分配的訂單
        unassigned_order_ids = unassigned['order_id'].unique()
        station_index = 0
        
        for order_id in unassigned_order_ids:
            # 找到負載最少的站點
            min_count = float('inf')
            best_station = all_stations[0]
            
            for station in all_stations:
                current_count = len(df[(df['assigned_station'] == station) & (df['order_id'] < 0)])
                if current_count < min_count:
                    min_count = current_count
                    best_station = station
            
            # 分配訂單
            df.loc[df['order_id'] == order_id, 'assigned_station'] = best_station
            df.loc[df['order_id'] == order_id, 'status'] = -1
            
            print(f"  訂單 {order_id} 分配到 {best_station}")
        
        # 儲存修復後的檔案
        backup_path = file_path.replace('.csv', '_backup.csv')
        df.to_csv(backup_path, index=False)
        df.to_csv(file_path, index=False)
        
        print(f"  已儲存修復後的檔案，備份在：{backup_path}")
        
        # 顯示修復後的統計
        print(f"\n  修復後的站點分配情況：")
        station_counts_after = df[df['assigned_station'].notna()]['assigned_station'].value_counts()
        for station, count in station_counts_after.items():
            print(f"    {station}: {count} 個訂單")


def check_order_assignment():
    """檢查訂單分配狀態"""
    
    print("=== 訂單分配狀態檢查 ===\n")
    
    # 檢查 generated_order.csv
    order_file = 'data/output/generated_order.csv'
    if os.path.exists(order_file):
        df_order = pd.read_csv(order_file)
        backlog_orders = df_order[df_order['order_id'] < 0]
        print(f"generated_order.csv:")
        print(f"  總訂單數：{len(df_order['order_id'].unique())}")
        print(f"  積壓訂單數：{len(backlog_orders['order_id'].unique())}")
    
    # 檢查所有 assign_order 檔案
    assign_files = glob.glob('data/input/assign_order*.csv')
    
    for file_path in assign_files:
        if 'backup' in file_path:
            continue
            
        print(f"\n{file_path}:")
        df = pd.read_csv(file_path)
        
        # 統計
        total_orders = len(df['order_id'].unique())
        backlog_orders = df[df['order_id'] < 0]
        assigned_orders = backlog_orders[backlog_orders['assigned_station'].notna()]
        unassigned_orders = backlog_orders[backlog_orders['assigned_station'].isna()]
        
        print(f"  總訂單數：{total_orders}")
        print(f"  積壓訂單數：{len(backlog_orders['order_id'].unique())}")
        print(f"  已分配：{len(assigned_orders['order_id'].unique())}")
        print(f"  未分配：{len(unassigned_orders['order_id'].unique())}")
        
        if len(assigned_orders) > 0:
            print(f"  站點分配情況：")
            station_counts = assigned_orders['assigned_station'].value_counts()
            for station, count in station_counts.items():
                unique_orders = len(assigned_orders[assigned_orders['assigned_station'] == station]['order_id'].unique())
                print(f"    {station}: {unique_orders} 個訂單")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--check':
        # 只檢查狀態
        check_order_assignment()
    else:
        # 檢查狀態
        check_order_assignment()
        
        # 詢問是否修復
        print("\n是否要修復未分配的訂單？(y/n): ", end='')
        response = input().strip().lower()
        
        if response == 'y':
            fix_assign_orders()
            print("\n=== 修復後的狀態 ===")
            check_order_assignment()
        else:
            print("已取消修復")
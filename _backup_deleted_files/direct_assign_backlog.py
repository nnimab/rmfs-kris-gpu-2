#!/usr/bin/env python3
"""
直接平均分配積壓訂單的獨立腳本
不考慮 max_orders 限制，使用簡單的循環分配策略
"""

import os
import pandas as pd
import numpy as np
from collections import defaultdict

def direct_assign_backlog_orders(input_file='data/output/generated_order.csv', 
                                output_file='data/input/assign_order.csv',
                                num_stations=3):
    """
    直接平均分配積壓訂單到所有揀貨站
    
    Args:
        input_file: 輸入的訂單檔案路徑
        output_file: 輸出的分配檔案路徑
        num_stations: 揀貨站數量
    """
    
    # 讀取訂單資料
    print(f"讀取訂單檔案：{input_file}")
    if not os.path.exists(input_file):
        print(f"錯誤：找不到檔案 {input_file}")
        return
    
    orders_df = pd.read_csv(input_file)
    print(f"總訂單數：{len(orders_df)}")
    
    # 篩選積壓訂單（order_id < 0）
    backlog_orders = orders_df[orders_df['order_id'] < 0].copy()
    normal_orders = orders_df[orders_df['order_id'] >= 0].copy()
    
    # 獲取唯一的積壓訂單ID
    unique_backlog_ids = backlog_orders['order_id'].unique()
    print(f"\n找到 {len(unique_backlog_ids)} 個積壓訂單")
    
    if len(unique_backlog_ids) == 0:
        print("沒有積壓訂單需要分配")
        return
    
    # 創建站點列表
    stations = [f'picker{i}' for i in range(num_stations)]
    print(f"可用揀貨站：{stations}")
    
    # 建立訂單ID到站點的映射（循環分配）
    order_to_station = {}
    for idx, order_id in enumerate(sorted(unique_backlog_ids)):
        station_idx = idx % num_stations
        order_to_station[order_id] = stations[station_idx]
    
    # 創建 assign_order DataFrame
    assign_df = orders_df.copy()
    
    # 添加必要的欄位
    if 'assigned_station' not in assign_df.columns:
        assign_df['assigned_station'] = None
    if 'assigned_pod' not in assign_df.columns:
        assign_df['assigned_pod'] = None
    if 'status' not in assign_df.columns:
        assign_df['status'] = -3
    
    # 分配積壓訂單
    for order_id, station in order_to_station.items():
        mask = assign_df['order_id'] == order_id
        assign_df.loc[mask, 'assigned_station'] = station
        assign_df.loc[mask, 'status'] = -1  # 已分配但未處理
    
    # 保持正常訂單的狀態不變（未分配）
    normal_mask = assign_df['order_id'] >= 0
    assign_df.loc[normal_mask, 'status'] = -3
    
    # 儲存結果
    assign_df.to_csv(output_file, index=False)
    print(f"\n分配結果已儲存到：{output_file}")
    
    # 顯示分配統計
    print("\n=== 分配統計 ===")
    station_counts = defaultdict(int)
    station_items = defaultdict(int)
    
    for order_id, station in order_to_station.items():
        station_counts[station] += 1
        # 計算該訂單的項目數
        items_count = len(backlog_orders[backlog_orders['order_id'] == order_id])
        station_items[station] += items_count
    
    print("\n各站點分配情況：")
    print(f"{'站點':<10} {'訂單數':<8} {'項目數':<8} {'平均項目/訂單':<15}")
    print("-" * 45)
    
    total_orders = 0
    total_items = 0
    
    for station in stations:
        orders = station_counts[station]
        items = station_items[station]
        avg_items = items / orders if orders > 0 else 0
        
        print(f"{station:<10} {orders:<8} {items:<8} {avg_items:<15.2f}")
        
        total_orders += orders
        total_items += items
    
    print("-" * 45)
    print(f"{'總計':<10} {total_orders:<8} {total_items:<8} {total_items/total_orders if total_orders > 0 else 0:<15.2f}")
    
    # 檢查分配是否平均
    counts = [station_counts[s] for s in stations]
    if counts:
        max_diff = max(counts) - min(counts)
        print(f"\n負載平衡檢查：")
        print(f"  最多訂單數：{max(counts)}")
        print(f"  最少訂單數：{min(counts)}")
        print(f"  差異：{max_diff} {'✓ 平衡' if max_diff <= 1 else '✗ 不平衡'}")
    
    # 驗證分配完整性
    assigned_backlog = assign_df[(assign_df['order_id'] < 0) & (assign_df['assigned_station'].notna())]
    assigned_count = len(assigned_backlog['order_id'].unique())
    
    print(f"\n分配完整性檢查：")
    print(f"  應分配：{len(unique_backlog_ids)} 個訂單")
    print(f"  已分配：{assigned_count} 個訂單")
    print(f"  {'✓ 完整' if assigned_count == len(unique_backlog_ids) else '✗ 不完整'}")
    
    return assign_df


def check_existing_assignment(file_path='data/input/assign_order.csv'):
    """檢查現有的分配狀況"""
    if not os.path.exists(file_path):
        print(f"檔案 {file_path} 不存在")
        return
    
    df = pd.read_csv(file_path)
    
    print("\n=== 現有分配狀況 ===")
    
    # 積壓訂單統計
    backlog = df[df['order_id'] < 0]
    assigned = backlog[backlog['assigned_station'].notna()]
    unassigned = backlog[backlog['assigned_station'].isna()]
    
    print(f"\n積壓訂單：")
    print(f"  總數：{len(backlog['order_id'].unique())} 個")
    print(f"  已分配：{len(assigned['order_id'].unique())} 個")
    print(f"  未分配：{len(unassigned['order_id'].unique())} 個")
    
    if len(assigned) > 0:
        print(f"\n站點分配情況：")
        station_counts = assigned.groupby('assigned_station')['order_id'].nunique()
        for station, count in station_counts.items():
            print(f"  {station}: {count} 個訂單")


def main():
    """主程式"""
    import argparse
    
    parser = argparse.ArgumentParser(description='直接平均分配積壓訂單')
    parser.add_argument('--check', action='store_true', 
                       help='只檢查現有分配狀況')
    parser.add_argument('--input', type=str, 
                       default='data/output/generated_order.csv',
                       help='輸入訂單檔案')
    parser.add_argument('--output', type=str,
                       default='data/input/assign_order.csv',
                       help='輸出分配檔案')
    parser.add_argument('--stations', type=int, default=3,
                       help='揀貨站數量')
    parser.add_argument('--force', action='store_true',
                       help='強制覆寫現有檔案')
    
    args = parser.parse_args()
    
    if args.check:
        # 只檢查現有狀況
        check_existing_assignment(args.output)
    else:
        # 檢查輸出檔案是否存在
        if os.path.exists(args.output) and not args.force:
            print(f"警告：檔案 {args.output} 已存在")
            print("使用 --force 參數強制覆寫，或先備份現有檔案")
            
            # 顯示現有分配狀況
            check_existing_assignment(args.output)
            
            response = input("\n是否要繼續並覆寫檔案？(y/n): ")
            if response.lower() != 'y':
                print("已取消操作")
                return
        
        # 執行分配
        direct_assign_backlog_orders(args.input, args.output, args.stations)


if __name__ == "__main__":
    main()
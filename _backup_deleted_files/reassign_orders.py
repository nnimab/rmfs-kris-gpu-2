#!/usr/bin/env python3
"""
重新分配訂單的獨立腳本
可以對現有的 CSV 檔案進行訂單重新分配
"""

import os
import sys
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans

# 添加專案根目錄到 Python 路徑
PARENT_DIRECTORY = os.path.dirname(os.path.abspath(__file__))
sys.path.append(PARENT_DIRECTORY)

from lib.generator.order_generator import compute_jaccard_similarity


def get_station_capacity(num_stations=6, max_orders_per_station=10):
    """生成站點容量資訊"""
    columns = ['id_station', 'capacity_left']
    station_id_cap_df = pd.DataFrame(columns=columns)
    
    for i in range(num_stations):
        station_id = f'picker{i}'
        new_row = pd.DataFrame({'id_station': [station_id], 'capacity_left': [max_orders_per_station]})
        station_id_cap_df = pd.concat([station_id_cap_df, new_row], ignore_index=True)
    
    return station_id_cap_df


def cluster_backlog_orders_improved(jaccard_similarities, total_station, station_capacity_df):
    """改進的訂單分配算法，確保所有訂單都被分配"""
    jaccard_similarities_list = [similarities for similarities in jaccard_similarities.values()]
    cluster_labels = [-1] * len(jaccard_similarities_list)
    station_remaining_capacity = station_capacity_df['capacity_left'].tolist()
    
    # K-Means clustering
    kmeans = KMeans(n_clusters=total_station, random_state=42)
    kmeans.fit(jaccard_similarities_list)
    
    cluster_labels1 = kmeans.labels_
    cluster_distances = []
    
    # 計算每個訂單到其聚類中心的距離
    for i, label in enumerate(cluster_labels1):
        centroid = kmeans.cluster_centers_[label]
        distance = np.linalg.norm(jaccard_similarities_list[i] - centroid)
        cluster_distances.append((i, label, distance))
    
    cluster_distances.sort(key=lambda x: x[2])
    
    # 第一輪：優先分配到最佳匹配的站點
    unassigned_orders = []
    for order_idx, label, distance in cluster_distances:
        station_id = station_capacity_df.iloc[label]['id_station']
        if station_remaining_capacity[label] > 0:
            cluster_labels[order_idx] = station_id
            station_remaining_capacity[label] -= 1
        else:
            unassigned_orders.append((order_idx, label, distance))
    
    # 第二輪：將未分配的訂單分配到還有容量的站點
    if unassigned_orders:
        print(f"\n第一輪分配後，還有 {len(unassigned_orders)} 個訂單未分配")
        
        for order_idx, original_label, distance in unassigned_orders:
            # 尋找還有容量的站點
            for station_idx, capacity in enumerate(station_remaining_capacity):
                if capacity > 0:
                    station_id = station_capacity_df.iloc[station_idx]['id_station']
                    cluster_labels[order_idx] = station_id
                    station_remaining_capacity[station_idx] -= 1
                    print(f"訂單 {order_idx} 被重新分配到站點 {station_id}")
                    break
            else:
                # 如果所有站點都滿了，循環分配到負載最少的站點
                min_load_idx = np.argmax(station_remaining_capacity)
                station_id = station_capacity_df.iloc[min_load_idx]['id_station']
                cluster_labels[order_idx] = station_id
                print(f"警告：訂單 {order_idx} 被強制分配到站點 {station_id}（超出容量）")
    
    # 統計分配結果
    print("\n分配結果統計：")
    assigned_count = sum(1 for label in cluster_labels if label != -1 and label is not None)
    print(f"總訂單數：{len(cluster_labels)}")
    print(f"已分配訂單數：{assigned_count}")
    print(f"未分配訂單數：{len(cluster_labels) - assigned_count}")
    
    # 顯示每個站點的分配情況
    station_counts = {}
    for label in cluster_labels:
        if label is not None and label != -1:
            station_counts[label] = station_counts.get(label, 0) + 1
    
    print("\n各站點分配情況：")
    for station_id, count in sorted(station_counts.items()):
        print(f"{station_id}: {count} 個訂單")
    
    return cluster_labels


def reassign_orders(order_csv_path, output_path=None, num_stations=6, max_orders_per_station=10):
    """重新分配訂單的主函數"""
    
    # 讀取訂單數據
    print(f"讀取訂單檔案：{order_csv_path}")
    data_order_df = pd.read_csv(order_csv_path)
    
    # 篩選積壓訂單（order_id < 0）
    unassigned_backlog_order = data_order_df.loc[(data_order_df['order_id'] < 0)].sort_values(by=['order_id']).reset_index(drop=True)
    
    if len(unassigned_backlog_order) == 0:
        print("沒有找到積壓訂單（order_id < 0）")
        return
    
    print(f"找到 {len(unassigned_backlog_order)} 筆積壓訂單")
    
    # 獲取站點容量資訊
    station_capacity_df = get_station_capacity(num_stations, max_orders_per_station)
    
    # 計算 Jaccard 相似度
    print("\n計算訂單相似度...")
    full_order, jaccard_similarities = compute_jaccard_similarity(unassigned_backlog_order)
    
    # 執行改進的聚類分配
    print("\n執行訂單分配...")
    cluster_labels = cluster_backlog_orders_improved(jaccard_similarities, num_stations, station_capacity_df)
    
    # 創建分配結果
    order_dum_to_cluster = dict(zip(full_order.index, cluster_labels))
    
    # 準備輸出檔案
    if output_path is None:
        output_path = os.path.join(PARENT_DIRECTORY, f'data/input/assign_order_reassigned.csv')
    
    # 創建 assign_order 格式的 DataFrame
    assign_order_df = data_order_df.copy()
    if 'assigned_station' not in assign_order_df.columns:
        assign_order_df['assigned_station'] = None
    if 'assigned_pod' not in assign_order_df.columns:
        assign_order_df['assigned_pod'] = None
    if 'status' not in assign_order_df.columns:
        assign_order_df['status'] = -3
    
    # 更新分配資訊
    unique_orders = set()
    for index, row in unassigned_backlog_order.iterrows():
        order_dum = row['order_id']
        station_id = order_dum_to_cluster.get(order_dum)
        
        if station_id is not None and order_dum not in unique_orders:
            unique_orders.add(order_dum)
            assign_order_df.loc[assign_order_df['order_id'] == order_dum, 'assigned_station'] = station_id
            assign_order_df.loc[assign_order_df['order_id'] == order_dum, 'status'] = -1
    
    # 儲存結果
    assign_order_df.to_csv(output_path, index=False)
    print(f"\n分配結果已儲存到：{output_path}")
    
    # 顯示分配統計
    assigned_orders = assign_order_df[assign_order_df['status'] == -1]
    print(f"\n總共分配了 {len(assigned_orders['order_id'].unique())} 個訂單")
    
    return assign_order_df


def main():
    """主程式"""
    import argparse
    
    parser = argparse.ArgumentParser(description='重新分配積壓訂單到揀貨站')
    parser.add_argument('--input', type=str, 
                       default='data/output/generated_order.csv',
                       help='輸入的訂單檔案路徑')
    parser.add_argument('--output', type=str,
                       default=None,
                       help='輸出的分配檔案路徑（預設：data/input/assign_order_reassigned.csv）')
    parser.add_argument('--stations', type=int, default=6,
                       help='揀貨站數量（預設：6）')
    parser.add_argument('--capacity', type=int, default=10,
                       help='每個站點的最大訂單容量（預設：10）')
    parser.add_argument('--force-redistribute', action='store_true',
                       help='強制重新分配所有訂單，忽略容量限制')
    
    args = parser.parse_args()
    
    # 構建完整路徑
    input_path = os.path.join(PARENT_DIRECTORY, args.input)
    
    if not os.path.exists(input_path):
        print(f"錯誤：找不到輸入檔案 {input_path}")
        sys.exit(1)
    
    # 執行重新分配
    if args.force_redistribute:
        print("啟用強制分配模式：所有訂單都會被分配，可能超出站點容量")
        # 設置一個很大的容量值
        reassign_orders(input_path, args.output, args.stations, 9999)
    else:
        reassign_orders(input_path, args.output, args.stations, args.capacity)


if __name__ == "__main__":
    main()
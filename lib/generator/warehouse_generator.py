import time

from typing import List

from sklearn.cluster import KMeans
from lib.types.netlogo_coordinate import NetLogoCoordinate
from world.warehouse import Warehouse
from world.entities.intersection import Intersection
from world.entities.order import Order
from lib.generator.order_generator import *
from lib.enum.area_path_type import AreaPathType
from world.entities.pod import Pod
from world.managers.pod_manager import PodManager
from lib.generator.pod_generator import *
from pandas import DataFrame
from lib.math import *
from lib.constant import *

pods_path = os.path.join(PARENT_DIRECTORY, 'data/output/pods.csv')

def init_robots(warehouse: Warehouse):
    num_robot = 30 # Number of robots
    
    robots = []
    x_range = (5,43)
    y_range=(0,30)

    # Initialize a set to keep track of used coordinates
    used_coordinates = set()

    # Generate the robots with random unique x and y coordinates
    while len(robots) < num_robot:
        x = random.randint(x_range[0], x_range[1])
        y = random.randint(y_range[0], y_range[1])
        if (x, y) not in used_coordinates:
            robot = {
                'velocity': 0,
                'heading': 0,
                'x': x,
                'y': y
            }
            robots.append(robot)
            used_coordinates.add((x, y))

    # Iterate through each robot in the list to initialize and add to the warehouse
    for r in robots:
        # Create a new Robot instance
        obj = warehouse.robot_manager.createRobot(r['x'], r['y'])

        # Set the robot's attributes based on the dictionary values
        obj.velocity = r['velocity']
        obj.heading = r['heading']

        # Add the robot to the warehouse, which likely involves adding it to some internal list or map

def draw_layout(warehouse: Warehouse, process_id=None):
    """
    兩階段策略解決並行訓練文件競爭問題：
    第一階段：集中生成母版文件
    第二階段：分別複製個人副本
    """
    lock_file_path = os.path.join(PARENT_DIRECTORY, 'data/output/generator.lock')
    
    # 第一階段：集中生成母版文件
    _ensure_master_files_exist(warehouse, lock_file_path)
    
    # 第二階段：分別複製個人副本
    if process_id:
        _create_process_specific_files(process_id)
    
    # 執行後續處理
    draw_layout_from_generated_file(warehouse, process_id)


def _ensure_master_files_exist(warehouse: Warehouse, lock_file_path: str):
    """
    第一階段：確保母版文件存在
    """
    # 母版文件路徑列表
    master_files = [
        os.path.join(PARENT_DIRECTORY, 'data/output/generated_pod.csv'),
        os.path.join(PARENT_DIRECTORY, 'data/output/generated_order.csv'),
        os.path.join(PARENT_DIRECTORY, 'data/output/pods.csv')
    ]
    
    # 檢查是否所有母版文件都存在
    all_files_exist = all(os.path.exists(file_path) for file_path in master_files)
    
    if all_files_exist:
        # 所有文件都存在，無需重新生成
        return
    
    # 等待其他進程釋放鎖
    while os.path.exists(lock_file_path):
        time.sleep(1)
    
    # 雙重檢查：再次檢查文件是否存在
    all_files_exist = all(os.path.exists(file_path) for file_path in master_files)
    if all_files_exist:
        return
    
    # 獲取鎖並生成母版文件
    try:
        with open(lock_file_path, 'w') as f:
            f.write(str(os.getpid()))
        
        print(f"Process {os.getpid()} generating master files...")
        
        # 生成母版文件
        warehouse.layout.generate()
        
        print(f"Process {os.getpid()} master files generation complete.")
        
    finally:
        # 釋放鎖
        if os.path.exists(lock_file_path):
            os.remove(lock_file_path)


def _create_process_specific_files(process_id: int):
    """
    第二階段：為每個進程複製個人副本
    """
    import shutil
    
    # 需要複製的母版文件到個人副本的映射
    file_mappings = {
        'data/output/generated_pod.csv': f'data/output/generated_pod_{process_id}.csv',
        'data/output/generated_order.csv': f'data/output/generated_order_{process_id}.csv',
        'data/output/pods.csv': f'data/output/pods_{process_id}.csv'
    }
    
    for master_file, process_file in file_mappings.items():
        master_path = os.path.join(PARENT_DIRECTORY, master_file)
        process_path = os.path.join(PARENT_DIRECTORY, process_file)
        
        # 如果個人副本已經存在，跳過
        if os.path.exists(process_path):
            continue
        
        # 複製母版文件到個人副本
        if os.path.exists(master_path):
            try:
                shutil.copy2(master_path, process_path)
                print(f"Process {process_id}: Copied {master_file} -> {process_file}")
            except Exception as e:
                print(f"Process {process_id}: Failed to copy {master_file}: {e}")
        else:
            print(f"Process {process_id}: Warning - Master file {master_file} not found")


def draw_layout_from_generated_file(warehouse: Warehouse, process_id=None):
    draw_storage_from_generated_file(warehouse, process_id)

    # Config Orders
    assign_skus_to_pods(warehouse.pod_manager, process_id)
    
    # 只有第一個進程才需要生成訂單文件，其他進程直接使用複製的文件
    if not process_id or not _order_files_exist(process_id):
        config_orders(
            initial_order=20, #原本是20
            total_requested_item=500, # Number of SKU in warehouse #原本是500
            items_orders_class_configuration={"A": 0.6, "B": 0.3, "C": 0.1}, # Item class configuration in warehouse
            quantity_range=[1, 12], # Quantity range of number of SKU in each order
            order_cycle_time=100,  # 保持高密度以生成大量訂單
            order_period_time=150, # 保持長時程
            order_start_arrival_time=1, # 從 tick=1 開始，避開與積壓訂單的衝突
            date=1,
            sim_ver=1,        
            dev_mode=False)
        
        # Config Backlog Orders
        config_orders(
            initial_order=50, # Initial order in backlog
            total_requested_item=500, # Number of SKU in warehouse
            items_orders_class_configuration={"A": 0.6, "B": 0.3, "C": 0.1}, # Item class configuration in warehouse
            quantity_range=[1, 12], # Quantity range of number of SKU in each order
            order_cycle_time=5, # 恢復舊的、有效的設定
            order_period_time=3, # 恢復舊的、有效的設定
            order_start_arrival_time=0, # 確保積壓訂單在 t=0 生成
            date=1,  
            sim_ver=2, 
            dev_mode=True)
        
        # 如果有 process_id，將新生成的訂單文件複製為個人副本
        if process_id:
            _copy_order_files_to_process(process_id)
    
    init_robots(warehouse)
    # Assign backlog clustering
    assign_backlog_orders(warehouse, process_id)


def _order_files_exist(process_id: int) -> bool:
    """檢查訂單文件是否存在"""
    order_files = [
        f'data/output/generated_order_{process_id}.csv',
        f'data/input/generated_backlog_{process_id}.csv'
    ]
    
    return all(os.path.exists(os.path.join(PARENT_DIRECTORY, file_path)) for file_path in order_files)


def _copy_order_files_to_process(process_id: int):
    """將訂單文件複製為個人副本"""
    import shutil
    
    # 訂單文件映射
    order_file_mappings = {
        'data/output/generated_order.csv': f'data/output/generated_order_{process_id}.csv',
        'data/input/generated_backlog.csv': f'data/input/generated_backlog_{process_id}.csv'
    }
    
    for master_file, process_file in order_file_mappings.items():
        master_path = os.path.join(PARENT_DIRECTORY, master_file)
        process_path = os.path.join(PARENT_DIRECTORY, process_file)
        
        if os.path.exists(master_path) and not os.path.exists(process_path):
            try:
                shutil.copy2(master_path, process_path)
                print(f"Process {process_id}: Copied order file {master_file} -> {process_file}")
            except Exception as e:
                print(f"Process {process_id}: Failed to copy order file {master_file}: {e}")

def cluster_backlog_orders(jaccard_similarities, total_station, station_capacity_df):
    jaccard_similarities_list = [similarities for similarities in jaccard_similarities.values()]
    # print(jaccard_similarities_list)
    cluster_labels = [-1] * len(jaccard_similarities_list)
    station_remaining_capacity = station_capacity_df['capacity_left'].tolist()

    # K-Means clustering
    kmeans = KMeans(n_clusters=total_station)
    kmeans.fit(jaccard_similarities_list)

    cluster_labels1 = kmeans.labels_

    cluster_distances = []

    # calculate distances for each order
    for i, label in enumerate(cluster_labels1):
        centroid = kmeans.cluster_centers_[label]
        distance = np.linalg.norm(jaccard_similarities_list[i] - centroid)
        cluster_distances.append((i, label, distance))
        
    cluster_distances.sort(key=lambda x: x[2])

    # assign each backlog order to a cluster
    for order_idx, label, distance in cluster_distances:
        station_id = station_capacity_df.iloc[label]['id_station']
        if station_remaining_capacity[label] > 0:
            cluster_labels[order_idx] = station_id
            station_remaining_capacity[label] -= 1
        else:
            cluster_labels[order_idx] = None

    print("cluster label:")
    print(cluster_labels)

    return cluster_labels

def assign_cluster_labels(warehouse: Warehouse, data_backlog_order_df, full_order, cluster_labels, station_capacity_df, process_id=None):
    order_dum_to_cluster = dict(zip(full_order.index, cluster_labels))
    temp = float('inf')
    new_order = None
 
    if process_id:
        order_path = os.path.join(PARENT_DIRECTORY, f'data/output/generated_order_{process_id}.csv')
    else:
        order_path = os.path.join(PARENT_DIRECTORY, 'data/output/generated_order.csv')
    orders_df = pd.read_csv(order_path)
    
    if process_id:
        file_path = PARENT_DIRECTORY + f"/data/input/assign_order_{process_id}.csv"
    else:
        file_path = PARENT_DIRECTORY + f"/data/input/assign_order_{os.getpid()}.csv"
    if os.path.exists(file_path):
        assign_order_df = pd.read_csv(file_path)
        # pass
    else:
        assign_order_df = orders_df.copy()
        assign_order_df['assigned_station'] = None
        assign_order_df['assigned_pod'] = None
        assign_order_df['status'] = -3
        assign_order_df.to_csv(file_path, index=False)      
    
    unique_orders = set()
    order_sku_map = {}
    new_order = None
    for index, row in data_backlog_order_df.iterrows():
        order_dum = row['order_id']
        station_id = order_dum_to_cluster[order_dum]
       
        if station_id is not None and order_dum not in unique_orders:
            unique_orders.add(order_dum)
            new_order = warehouse.order_manager.createOrder(order_dum, 0)
            # print("order: ", new_order.id)
            # print("station: ", station_id)
            
            assign_order_df.loc[assign_order_df['order_id'] == new_order.id, 'assigned_station'] = station_id
            assign_order_df.loc[assign_order_df['order_id'] == new_order.id, 'status'] = -1
            
            assign_order_df.to_csv(file_path, index=False)
            new_order.assignStation(station_id)
            station = warehouse.station_manager.getStationById(station_id)
            
            order_sku_map[order_dum] = 0

        if order_dum in unique_orders:
            order = warehouse.order_manager.getOrderById(order_dum)
            order.addSKU(row['item_id'], row['item_quantity'])
            order_sku_map[order_dum] += 1
        if order_dum in order_sku_map:
            order = warehouse.order_manager.getOrderById(order_dum)
            expected_sku_count = data_backlog_order_df[data_backlog_order_df['order_id'] == order_dum].shape[0]
            if order_sku_map[order_dum] == expected_sku_count:
                station.addOrder(order_dum, order)
    
    return station_capacity_df

def assign_backlog_orders(warehouse: Warehouse, process_id=None):
    # open file order
    if process_id:
        order_path = os.path.join(PARENT_DIRECTORY, f'data/output/generated_order_{process_id}.csv')
    else:
        order_path = os.path.join(PARENT_DIRECTORY, 'data/output/generated_order.csv')
    data_order_df = pd.read_csv(order_path)

    # filter order_id < 0
    unassigned_backlog_order = data_order_df.loc[(data_order_df['order_id'] < 0)].sort_values(by=['order_id']).reset_index(drop=True)

    columns = ['id_station', 'capacity_left']
    station_id_cap_df = pd.DataFrame(columns=columns)

    for station in warehouse.station_manager.getAllStations():
        id = station.id
        cap = station.max_orders - len(station.order_ids)
        
        new_row = pd.DataFrame({'id_station': [id], 'capacity_left': [cap]})
        # station_id_cap_df = station_id_cap_df.append({'id_station': id, 'capacity_left': cap}, ignore_index=True)
        station_id_cap_df = pd.concat([station_id_cap_df, new_row], ignore_index=True)
    is_picker = station_id_cap_df['id_station'].str.startswith('picker')

    station_id_cap_df = station_id_cap_df[is_picker]
    station_id_cap_df.reset_index(drop=True, inplace=True)

    if len(unassigned_backlog_order) > 0:
        total_station = len(station_id_cap_df)
        full_order, jaccard_similarities = compute_jaccard_similarity(unassigned_backlog_order)
        cluster_labels = cluster_backlog_orders(jaccard_similarities, total_station, station_id_cap_df)
        station_id_cap_df = assign_cluster_labels(warehouse, unassigned_backlog_order, full_order, cluster_labels, station_id_cap_df, process_id)

def draw_storage_from_generated_file(warehouse: Warehouse, process_id=None):
    if process_id:
        pod_path = os.path.join(PARENT_DIRECTORY, f'data/output/generated_pod_{process_id}.csv')
    else:
        pod_path = os.path.join(PARENT_DIRECTORY, 'data/output/generated_pod.csv')
    warehouse.graph_pod.key = 'pod'
    data = pd.read_csv(pod_path, header=None)
    totalRows = len(data)
    totalCols = 0
    for y, row in data.iterrows():
        totalCols += len(list(row.items()))
        # Invert Y only to draw
        for x, value in row.items():
            # how to get the length of row.items() when the type is iterable
            create_storage_object(warehouse, x, y, row, totalRows, value, data)
    
    warehouse.setWarehouseSize([totalRows, totalCols])

def create_storage_object(warehouse: Warehouse, x, y, row, totalRows, value, data: DataFrame):
    def add_edges(graph, obj_key, coordinates, weight):
        for coord in coordinates:
            graph.addEdge(obj_key, coord, weight=weight)

    def handle_intersection(warehouse: Warehouse, x, y, data, obj_key, obj, obj_left_value, obj_right_value, obj_above_value, obj_below_value):
        intersection = warehouse.intersection_manager.createIntersection(x, y)
        approaching_path_coordinates = []

        def add_approaching_path(value, direction, increment):
            coord = increment
            while data.iloc[coord[1], coord[0]] in value:
                approaching_path_coordinates.append(coord)
                coord = (coord[0] + direction[0], coord[1] + direction[1])
            if data.iloc[coord[1], coord[0]] == 3:
                intersection.addConnectedIntersectionId(coord[0], coord[1])

        if obj_right_value in [4, 6, 7]:
            add_approaching_path([4, 6, 7], (1, 0), (x + 1, y))
        if obj_left_value in [5, 6, 7]:
            add_approaching_path([5, 6, 7], (-1, 0), (x - 1, y))
        if obj_below_value == 6:
            add_approaching_path([6], (0, 1), (x, y + 1))
        if obj_above_value == 7:
            add_approaching_path([7], (0, -1), (x, y - 1))

        for each_approaching_coordinate in approaching_path_coordinates:
            intersection.approaching_path_coordinates.append(each_approaching_coordinate)

        if obj.pos_x == 15:
            intersection.use_reinforcement_learning = True
            if obj.pos_y == 0:
                intersection.setRLModelName("BOTTOM")
            elif obj.pos_y == 30:
                intersection.setRLModelName("TOP")
            else:
                intersection.setRLModelName("MIDDLE")

        intersection_edges = [
            (obj_left_value, obj_left_coordinate),
            (obj_right_value, obj_right_coordinate),
            (obj_above_value, obj_above_coordinate),
            (obj_below_value, obj_below_coordinate)
        ]

        for value, coord in intersection_edges:
            if value in [4, 5, 6, 7]:
                add_edges(warehouse.graph, obj_key, [coord], intersection_weight)
                add_edges(warehouse.graph_pod, obj_key, [coord], intersection_weight)

    object_type = AreaPathType(value)
    obj = warehouse.area_path_manager.createAreaPath(x, y, object_type)

    obj_key = f"{x},{y}"
    obj_left_coordinate = f"{x - 1},{y}"
    obj_right_coordinate = f"{x + 1},{y}"
    obj_above_coordinate = f"{x},{y - 1}"
    obj_below_coordinate = f"{x},{y + 1}"

    obj_left_value = data.iloc[y, x - 1] if x > 0 else None
    obj_right_value = data.iloc[y, x + 1] if x < len(row) - 1 else None
    obj_above_value = data.iloc[y - 1, x] if y > 0 else None
    obj_below_value = data.iloc[y + 1, x] if y < totalRows - 1 else None

    weight = 3 if x <= 7 else 1
    turning_weight = 5
    intersection_weight = 4

    if value in [0, 1, 2]:
        add_all_direction_paths(warehouse.graph, obj_key, weight)
        if value == 1:
            obj = warehouse.pod_manager.createPod(x, y)
            warehouse.graph_pod.addNode(obj_key)
        for coord, val in [(obj_left_coordinate, obj_left_value), (obj_right_coordinate, obj_right_value), (obj_above_coordinate, obj_above_value), (obj_below_coordinate, obj_below_value)]:
            if val != 1:
                warehouse.graph_pod.addEdge(obj_key, coord, weight=100)
    elif value == 3:
        handle_intersection(warehouse, x, y, data, obj_key, obj, obj_left_value, obj_right_value, obj_above_value, obj_below_value)
    elif value in [4, 5, 6, 7]:
        direction_edges = {
            4: (obj_left_coordinate, obj_above_coordinate, obj_below_coordinate),
            5: (obj_right_coordinate, obj_above_coordinate, obj_below_coordinate),
            6: (obj_above_coordinate, obj_left_coordinate, obj_right_coordinate),
            7: (obj_below_coordinate, obj_left_coordinate, obj_right_coordinate)
        }
        coords = direction_edges[value]
        add_edges(warehouse.graph, obj_key, [coords[0]], weight)
        add_edges(warehouse.graph_pod, obj_key, [coords[0]], weight)
        add_edges(warehouse.graph, obj_key, [coords[1], coords[2]], turning_weight)
        add_edges(warehouse.graph_pod, obj_key, [coords[1], coords[2]], 100)
    elif value in [12, 23]:
        warehouse.graph_pod.addEdge(obj_key, obj_right_coordinate, weight=weight)
    elif value in [13, 22]:
        warehouse.graph_pod.addEdge(obj_key, obj_left_coordinate, weight=weight)
    elif value in [14, 24]:
        if obj_left_value == 11:
            warehouse.station_manager.createPickerStation(x, y, data)
        elif obj_right_value == 21:
            warehouse.station_manager.createReplenishmentStation(x, y, data, max_robots=3)
        warehouse.graph_pod.addEdge(obj_key, obj_above_coordinate, weight=weight)
        if value == 14:
            obj.heading = 270
        elif value == 24:
            obj.heading = 90
    elif value in [16, 17, 18, 19, 26, 27, 28, 29]:
        headings = {
            16: 270, 17: None, 18: 180, 19: 90,
            26: 180, 27: 90, 28: 270, 29: 0
        }
        if headings[value] is not None:
            obj.heading = headings[value]
        coord = {
            16: obj_right_coordinate, 17: obj_above_coordinate, 18: obj_left_coordinate, 19: obj_above_coordinate,
            26: obj_left_coordinate, 27: obj_below_coordinate, 28: obj_right_coordinate, 29: obj_above_coordinate
        }[value]
        warehouse.graph_pod.addEdge(obj_key, coord, weight=weight)
    if obj_left_coordinate == 13:
        warehouse.graph_pod.addEdge(obj_key, obj_left_coordinate, weight=weight)

def add_all_direction_paths(graph, obj_key, weight):
    x, y = map(int, obj_key.split(','))
    directions = {
        'left': (x - 1, y),
        'right': (x + 1, y),
        'up': (x, y + 1),
        'down': (x, y - 1)
    }

    for dir_key, (nx, ny) in directions.items():
        neighbor_key = f"{nx},{ny}"
        graph.addEdge(obj_key, neighbor_key, weight=weight)

def assign_skus_to_pods(pod_manager, process_id=None):
    # Check if pods.csv exists in the current directory
    if process_id:
        pods_path_dynamic = os.path.join(PARENT_DIRECTORY, f'data/output/pods_{process_id}.csv')
    else:
        pods_path_dynamic = os.path.join(PARENT_DIRECTORY, 'data/output/pods.csv')
        
    if os.path.exists(pods_path_dynamic):
        assign_skus_to_pods_from_file(pod_manager, process_id, pods_path_dynamic)
    else:
        # Fungsi generate pods.csv
        # PodGenerator(pod_manager).generate()
        generate_pod(pod_types=[0], pod_num=[300], total_sku=500, 
                      items_class_conf={"A": 0.1, "B": 0.3, "C": 0.6},
                      items_pods_inventory_levels={"A": 0.4, "B": 0.5, "C": 0.6},
                      items_warehouse_inventory_levels={"A": 0.4, "B": 0.5, "C": 0.6},
                      items_pods_class_conf={"A": 0.6, "B": 0.3, "C": 0.1},
                      dev_mode=False)
        assign_skus_to_pods_from_file(pod_manager, process_id, pods_path_dynamic)

def assign_skus_to_pods_from_file(pod_manager: PodManager, process_id=None, pods_path_dynamic=None):
    # 使用傳入的動態路徑或預設路徑
    if pods_path_dynamic is None:
        pods_path_dynamic = os.path.join(PARENT_DIRECTORY, 'data/output/pods.csv')
    
    with open(pods_path_dynamic, mode='r', newline='') as file:
        reader = csv.DictReader(file)
        for row in reader:
            pod_id = int(row['pod_id'])
            sku = int(row['item'])
            limit_qty = int(row['max_qty'])
            current_qty = int(row['qty'])
            threshold = row['item_pod_inventory_level']
            global_threshold_inv_level = row['item_warehouse_inventory_level']

            # Find the pod by id
            pod: Pod = pod_manager.getPodByNumber(pod_id)
            pod.addSKU(sku, limit_qty=limit_qty, current_qty=current_qty, threshold=threshold)
            pod_manager.addSKUToPod(sku, pod)
             
            # Add SKU Data of level
            pod_manager.addSKUData(sku,current_qty,limit_qty, global_threshold_inv_level)

    # 構建唯一的檔名
    if process_id:
        # 如果在並行環境中，使用帶有進程ID的唯一檔名
        csv_file = PARENT_DIRECTORY + f'/data/output/skus_data_{process_id}.csv'
    else:
        # 在非並行環境中，使用原始檔名
        csv_file = PARENT_DIRECTORY + '/data/output/skus_data.csv'
    
    if os.path.exists(csv_file):
        try:
            os.remove(csv_file)
        except OSError as e:
            # 在並行環境下，即使加了唯一ID，也可能因為其他原因刪除失敗
            # 在這裡我們可以只打印警告而不是讓程式崩潰
            print(f"Warning: Could not remove temporary SKU file {csv_file}. Reason: {e}")
    skus_data = pod_manager.getAllSKUData()
    
    with open(csv_file, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['item_id', 'current_global_qty', 'max_global_qty', 'global_inv_level'])
        for key, value in skus_data.items():
            writer.writerow([key, value['current_global_qty'], value['max_global_qty'], value['global_inv_level']])

    print(f"Data has been saved to {csv_file}")
    df = pd.read_csv(csv_file)
    df_sorted = df.sort_values(by='item_id')
    
    if process_id:
        sorted_csv_file = PARENT_DIRECTORY + f'/data/output/sorted_skus_data_{process_id}.csv'
    else:
        sorted_csv_file = PARENT_DIRECTORY + '/data/output/sorted_skus_data.csv'
    
    df_sorted.to_csv(sorted_csv_file, index=False)

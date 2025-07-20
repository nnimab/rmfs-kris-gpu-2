import os
import numpy as np
import pandas as pd
import time # Added for file locking

from lib.file import *
from lib.constant import *

def get_random_quantity(quantity_range=[1, 12]):
    ## Generate a random quantity based on a normal distribution
    ## Even quantities are favored

    # Define the quantities from min to max
    min_qty = quantity_range[0]
    max_qty = quantity_range[1]
    numbers = np.arange(min_qty, max_qty + 1)

    # Generate a normal distribution centered around the mean of the range
    mean = np.mean(numbers)
    std_dev = np.std(numbers)
    normal_dist = np.exp(-((numbers - mean) ** 2) / (2 * std_dev ** 2))

    # Adjust the probabilities to favor even numbers
    adjusted_prob = np.array([prob * 2 if num % 2 == 0 else prob for num, prob in zip(numbers, normal_dist)])

    # Normalize the adjusted probabilities to sum to 1
    probabilities = adjusted_prob / adjusted_prob.sum()

    # Make a random choice using the defined probabilities
    random_qty = np.random.choice(numbers, p=probabilities)

    return random_qty

def gen_backlog(initial_order, total_requested_item, items_orders_class_configuration,quantity_range,dev_mode):

    items_path = os.path.join(PARENT_DIRECTORY, 'data/output/items.csv')
    orders_path = os.path.join(PARENT_DIRECTORY, 'data/output/generated_order.csv')
    items = pd.read_csv(items_path, index_col=False)
    order = pd.read_csv(orders_path, index_col=False)

    total_available_item = items.shape[0]
    if total_available_item >= total_requested_item:

        if total_available_item > total_requested_item:
            print("Total SKU is less than total items in the items.csv")
            print("Total SKU will be set to the total items in the items.csv")
            total_requested_item = total_available_item

        temp = 0
        # calculate cummulative the class_pod_conf value, to get the threshold to assign the item to the pod.
        for key, value in items_orders_class_configuration.items():
            if temp == 0:
                temp = value
            else:
                temp += value
                items_orders_class_configuration[key] = np.round(temp, 1)

        # sort the class_pod_conf based on the value
        items_orders_class_configuration = dict(sorted(items_orders_class_configuration.items(), key=lambda x: x[1]))

        # get class_pod_conf values into list as thresholds. The keys will be used to get the item based on the class
        thresholds = list(items_orders_class_configuration.values())
        keys = list(items_orders_class_configuration.keys())
        # print(keys, thresholds)

        orders_in_backlog = list(i * -1 for i in range(1, initial_order+1))
        items_in_order = np.random.geometric(p=0.3, size=initial_order)
        # print(orders_in_backlog, items_in_order)

        orders_backlog = pd.DataFrame(columns=[ 'order_id', 
                                               'order_type',
                                               'item_id', 
                                               'item_quantity', 
                                               'order_arrival'])
        
        for i, order in enumerate(orders_in_backlog):
            order_id = order
            order_type = 1
            order_duedate = 99999
            
            items_num = items_in_order[i]
            # print(f"Order {order_id} has {items_num} items")

            rand = np.random.rand(items_num)
            item_exist = list()
            # class_item = "A"
            for r in rand:
                if r <= thresholds[0]:
                    # print(f"  below {thresholds[0]}, then the class is {keys[0]}")
                    item_available = items.loc[(items["item_class"] == keys[0]) & (
                        ~items.index.isin(item_exist)), "item_order_frequency"]
                    # class_item = keys[0]

                for l in range(len(thresholds) - 1):
                    if thresholds[l] < r <= thresholds[l + 1]:
                        # print(f"  between {thresholds[l]} and {thresholds[l + 1]}, then the class is {keys[l+1]}")
                        item_available = items.loc[(items["item_class"] == keys[l+1]) & (
                            ~items.index.isin(item_exist)), "item_order_frequency"]
                        # class_item = keys[l+1]
                
                item_probability = (item_available / item_available.sum()).to_list()
                item_available = item_available.index.to_list()
                if len(item_available) > 0:
                    item_id = np.random.choice(item_available, p=item_probability)
                    qty = get_random_quantity(quantity_range=quantity_range)
                    order_arrival = 0
                    item_exist.append(item_id)
                    # print("    ", item_id, qty, class_item)

                    orders_backlog = pd.concat([orders_backlog, 
                                                pd.DataFrame({"order_id": [order_id],
                                                              "order_type": [order_type],
                                                              "item_id": [item_id],
                                                              "item_quantity": [qty],
                                                              "order_arrival" : [order_arrival]})
                                                ], axis=0)

        orders_backlog.sort_values(by="order_id", ascending=True, inplace=True)                    
        orders_backlog.reset_index(drop=True, inplace=True)
        orders_backlog.insert(loc=0, column="sequence_id", value=orders_backlog.index.to_list())
        orders_backlog_path = os.path.join(PARENT_DIRECTORY, 'data/input/generated_backlog.csv')
        orders_backlog.to_csv(orders_backlog_path, index=False)

        return orders_backlog

    else:
        print("Total SKU ("+str(total_requested_item)+") is more than total items in the items.csv ("+str(total_available_item)+")")
        print("Please provide a total SKU that is equal to or less than the total items in the items.csv")
        return None
    
# ["order_id", 'order_dum', 'order_type', "item", "qty", "facing", "due_date", 'station', 'pod_id', 'status', 'finish_time', 'date', 'time_gen']

def gen_order_arrival_time(order_cycle_time):
    
    # Define the total number of orders and the time period in minutes
    total_orders = order_cycle_time     # number of orders in a cycle (hour)
    time_period = 60                    # 60 minutes in an hour

    # Calculate the average rate (lambda)
    lambda_rate = total_orders / time_period

    # Generate the number of orders per minute using a Poisson distribution
    orders_per_minute = np.random.poisson(lambda_rate, size=time_period)

    # Generate arrival times as integers
    arrival_times = []
    for minute, num_orders in enumerate(orders_per_minute):
        arrival_times.extend([minute] * num_orders)

    # If there are more than total_orders (due to Poisson randomness), truncate the list
    if len(arrival_times) >= total_orders:
        arrival_times = arrival_times[:total_orders]

    # Sort the arrival times
    arrival_times.sort()

    # # Print the arrival times
    # print(f"Order arrival times (in minutes): {arrival_times}")
    
    return arrival_times

def gen_order(order_cycle_time,
              order_period_time,  
              order_start_arrival_time,
              total_requested_item, 
              items_orders_class_configuration,
              quantity_range,
              date, 
              dev_mode):

    items_path = os.path.join(PARENT_DIRECTORY, 'data/output/items.csv')
    items = pd.read_csv(items_path, index_col=False)    

    total_available_item = items.shape[0]

    if (total_available_item > total_requested_item) or (total_available_item == total_requested_item):
        print("Total SKU is less than total items in the items.csv")
        print("Total SKU will be set to the total items in the items.csv")
        total_requested_item = total_available_item

    if total_available_item >= total_requested_item:
        temp = 0
        # calculate cummulative the class_pod_conf value, to get the threshold to assign the item to the pod.
        for key, value in items_orders_class_configuration.items():
            if temp == 0:
                temp = value
            else:
                temp += value
                items_orders_class_configuration[key] = np.round(temp, 1)

        # sort the class_pod_conf based on the value
        items_orders_class_configuration = dict(sorted(items_orders_class_configuration.items(), key=lambda x: x[1]))

        # get class_pod_conf values into list as thresholds. The keys will be used to get the item based on the class
        thresholds = list(items_orders_class_configuration.values())
        keys = list(items_orders_class_configuration.keys())
        # print(keys, thresholds)

        arrival_times_list = list()
        last_arrival_time  = 0
        for i in range(1, order_period_time+1):
            arrival_times = gen_order_arrival_time(order_cycle_time=order_cycle_time)
            if i==1:
                index_start_arrival_time = np.where(np.array(arrival_times) > order_start_arrival_time)[0][0]

                arrival_times_list = arrival_times[index_start_arrival_time:-1] + [arrival_times[-1] + 1 + x for x in arrival_times[:index_start_arrival_time]]
                last_arrival_time = arrival_times[-1] + 1
            else:
                arrival_times_list = arrival_times_list + [last_arrival_time + x for x in arrival_times]
                last_arrival_time = arrival_times_list[-1]

        arrival_times_list = [60 * x for x in arrival_times_list] # convert to seconds
        orders = range(0, len(arrival_times_list))
        items_in_order = np.random.geometric(p=0.3, size=len(orders))

        database_order = pd.DataFrame(columns=['order_dum', 
                                               'order_type', 
                                               "item", 
                                               "qty", 
                                               "facing", 
                                               "due_date", 
                                               'station', 
                                               'pod_id', 
                                               'status', 
                                               'finish_time', 
                                               'date', 
                                               'time_gen'])
        for i, order in enumerate(orders):
            order_id = order
            order_type = 1
            order_duedate = 99999
            
            items_num = items_in_order[i]
            # print(f"Order {order_id} has {items_num} items")

            rand = np.random.rand(items_num)
            item_exist = list()
            # class_item = "A"
            for r in rand:
                if r <= thresholds[0]:
                    # print(f"  below {thresholds[0]}, then the class is {keys[0]}")
                    item_available = items.loc[(items["item_class"] == keys[0]) & (
                        ~items.index.isin(item_exist)), "item_order_frequency"]
                    class_item = keys[0]

                for l in range(len(thresholds) - 1):
                    if thresholds[l] < r <= thresholds[l + 1]:
                        # print(f"  between {thresholds[l]} and {thresholds[l + 1]}, then the class is {keys[l+1]}")
                        item_available = items.loc[(items["item_class"] == keys[l+1]) & (
                            ~items.index.isin(item_exist)), "item_order_frequency"]
                        class_item = keys[l+1]
                
                item_probability = (item_available / item_available.sum()).to_list()
                item_available = item_available.index.to_list()
                if len(item_available) > 0:
                    item_id = np.random.choice(item_available, p=item_probability)
                    qty = get_random_quantity(quantity_range=quantity_range)      
                    item_exist.append(item_id)
                    # print("    ", item_id, qty, class_item)

                    database_order = pd.concat([database_order, 
                                                pd.DataFrame({"order_dum": [order_id],
                                                              "order_type": [order_type],
                                                              "item": [item_id],
                                                              "qty": [qty],
                                                              "facing": [-1],
                                                              "due_date": [order_duedate],
                                                              "station": [-1],
                                                              "pod_id": [-1],
                                                              "status": [-3],
                                                              "finish_time": [-1],
                                                              "date": [date],
                                                              "time_gen": [arrival_times_list[i]]})
                                                ], axis=0)


        database_order.reset_index(drop=True, inplace=True)
        database_order.insert(loc=0, column="order_id", value=database_order.index.to_list())
        database_order_path = os.path.join(PARENT_DIRECTORY, 'data/output/generated_database_order.csv')
        database_order.to_csv(database_order_path, index=False)

        generated_order = database_order[["order_id", 'order_dum', 'order_type', "item", "qty", 'time_gen']].copy()
        generated_order.columns = ["sequence_id", 'order_id', 'order_type', "item_id", "item_quantity", 'order_arrival']
        
        generated_order_path = os.path.join(PARENT_DIRECTORY, 'data/output/generated_order.csv')
        generated_order.to_csv(generated_order_path, index=False)

        return database_order

    else:
        print("Total SKU ("+str(total_requested_item)+") is more than total items in the items.csv ("+str(total_available_item)+")")
        print("Please provide a total SKU that is equal to or less than the total items in the items.csv")
        return None

def config_orders(initial_order, total_requested_item, items_orders_class_configuration,quantity_range,order_cycle_time,order_period_time,order_start_arrival_time,date,sim_ver,dev_mode):
    if sim_ver == 1:
        print("Generate database orders...")

        database_order_path = os.path.join(PARENT_DIRECTORY, 'data/output/generated_database_order.csv')
        if not os.path.exists(database_order_path):
            print("    Generated database orders is not found. We will generate database orders:")
            orders = gen_order(order_cycle_time=order_cycle_time,order_period_time=order_period_time,order_start_arrival_time=order_start_arrival_time,total_requested_item=total_requested_item, items_orders_class_configuration=items_orders_class_configuration,quantity_range=quantity_range,date=date,dev_mode=dev_mode)
            order_id_list = orders["order_dum"].unique().tolist()
            print("    "+str(len(order_id_list))+" orders are generated.")
        else:
            print("    Generated database orders file is found. We will use the existing orders file.")    
            print("    If you want to reconfigure the orders, please delete the generated_order.csv file.") 

    elif sim_ver == 2:
        
        print("Generate backlog orders...")
        backlogs_path = os.path.join(PARENT_DIRECTORY, 'data/input/generated_backlog.csv')
        backlog_generated = False
        if not os.path.exists(backlogs_path):
            
            print("    Generated backlog orders is not found. We will generate backlog orders.")
            backlogs = gen_backlog(initial_order=initial_order, total_requested_item=total_requested_item, 
                                   items_orders_class_configuration=items_orders_class_configuration,
                                   quantity_range=quantity_range,
                                   dev_mode=dev_mode)
            backlog_generated = True
        else:
            backlogs = pd.read_csv(backlogs_path, index_col=False)
            backlogs_id_list = backlogs["order_id"].unique().tolist()
            
            if initial_order == len(backlogs_id_list):
                print("    Initial order is the same as the number of orders in the backlog file.")
                print("    We will use the existing items file.")
            
            else:
                print("    Initial order is different from the number of orders in the backlog file.")
                print("    We will re-generate backlog orders using the new intial order.")
                backlogs = gen_backlog(initial_order=initial_order, total_requested_item=total_requested_item, 
                                       items_orders_class_configuration=items_orders_class_configuration,
                                       quantity_range=quantity_range,
                                       dev_mode=dev_mode)
                backlog_generated = True
        print("    Generate backlog orders is done. If you want to reconfigure the backlog orders, please delete the generated_backlog.csv file.")

        print("Generate orders...")
        generated_order_path = os.path.join(PARENT_DIRECTORY, 'data/output/generated_order.csv')
        if not os.path.exists(generated_order_path):
            print("    Generated orders is not found. We will generate database orders:")
            orders = gen_order(order_cycle_time=order_cycle_time,
                               order_period_time=order_period_time,  
                               order_start_arrival_time=order_start_arrival_time,  
                               total_requested_item=total_requested_item, 
                               items_orders_class_configuration=items_orders_class_configuration,
                               quantity_range=quantity_range,
                               date=date,
                               dev_mode=dev_mode)
            order_id_list = orders["order_dum"].unique().tolist()
            print("    "+str(len(order_id_list))+" orders are generated.")
            print("    Generate orders is done. If you want to reconfigure the orders, please delete the generated_order.csv file.")

        else:
            print("    Generated orders file is found. We will use the existing orders file.")
            print("    If you want to reconfigure the orders, please delete the generated_order.csv file.")  

        # --- 【並行安全終極修復：原子鎖】 ---
        # 使用 os.O_CREAT | os.O_EXCL 實現原子操作，確保在高併發下鎖的唯一性
        merge_lock_path = os.path.join(PARENT_DIRECTORY, 'data/output/merge.lock')
        
        while True:
            try:
                # 1. (關鍵修復) 嘗試以原子方式創建並打開鎖文件
                # 這是無法被中斷的操作，只有一個進程會成功
                lock_fd = os.open(merge_lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.close(lock_fd) # 我們只需要創建文件這個動作，所以立刻關閉它
                
                # 如果代碼執行到這裡，說明我們成功獲取了鎖
                # print(f"Process {os.getpid()} acquired lock.")
                
                # 在 try...finally 結構中執行敏感操作
                try:
                    # 【修復後邏輯】
                    # 1. 定義原始數據源和最終輸出文件的路徑
                    database_order_path = os.path.join(PARENT_DIRECTORY, 'data/output/generated_database_order.csv')
                    backlog_path = os.path.join(PARENT_DIRECTORY, 'data/input/generated_backlog.csv')
                    output_order_path = os.path.join(PARENT_DIRECTORY, 'data/output/generated_order.csv')

                    # 2. 檢查原始數據源是否存在
                    if not os.path.exists(database_order_path) or not os.path.exists(backlog_path):
                        print("    Pristine data files (database_order or backlog) are missing. Skipping merge.")
                    else:
                        # 3. 讀取積壓訂單和原始未來訂單
                        backlog_df = pd.read_csv(backlog_path)
                        database_df = pd.read_csv(database_order_path)

                        # 4. 從原始未來訂單中提取並重命名欄位，使其格式與積壓訂單一致
                        future_orders_df = database_df[['order_id', 'order_dum', 'order_type', 'item', 'qty', 'time_gen']].copy()
                        future_orders_df.columns = ['sequence_id', 'order_id', 'order_type', 'item_id', 'item_quantity', 'order_arrival']
                        
                        # 5. 合併積壓訂單和處理過的未來訂單
                        merged_df = pd.concat([backlog_df, future_orders_df], ignore_index=True)
                        
                        # 6. 重新計算 sequence_id 以確保其連續性
                        merged_df['sequence_id'] = range(len(merged_df))

                        # 7. 將最終的、正確的結果寫入 generated_order.csv，實現真正的覆蓋
                        merged_df.to_csv(output_order_path, index=False)
                        print(f"    Successfully created 'generated_order.csv' with {len(backlog_df)} backlog orders and {len(future_orders_df)} future orders.")
                finally:
                    # 無論成功或失敗，都必須釋放鎖
                    # print(f"Process {os.getpid()} releasing lock.")
                    os.remove(merge_lock_path)
                
                # 完成工作後，跳出主循環
                break

            except FileExistsError:
                # 如果創建失敗（因為文件已存在），說明鎖已被其他進程持有
                # print(f"Process {os.getpid()} waiting for lock.")
                time.sleep(0.5) # 等待一會再重試
            except Exception as e:
                # 捕獲其他潛在錯誤，確保鎖在異常情況下也能被考慮釋放
                print(f"An unexpected error occurred during file merging: {e}")
                # 檢查鎖文件是否存在並嘗試刪除，以防死鎖
                if os.path.exists(merge_lock_path):
                    try:
                        os.remove(merge_lock_path)
                    except OSError:
                        pass # 其他進程可能已經刪除了它
                break # 發生未知錯誤，跳出循環

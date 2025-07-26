"""
NetLogo 並行版本 - 支援多個獨立的狀態檔案
"""
import pickle
import os
import traceback
from typing import List

from lib.generator.warehouse_generator import *
import subprocess
import sys
from lib.file import *
from world.warehouse import Warehouse
from evaluation.performance_report_generator import generate_performance_report_from_warehouse, PerformanceReportGenerator

# 創建一個全局變量，用於存儲PerformanceReportGenerator實例
performance_reporter = None

def get_state_filename():
    """
    根據環境變數或進程ID生成唯一的狀態檔案名稱
    優先順序：
    1. 環境變數 NETLOGO_STATE_FILE
    2. 環境變數 SIMULATION_ID
    3. 預設使用進程ID
    """
    # 方法1：直接指定檔案名稱
    if 'NETLOGO_STATE_FILE' in os.environ:
        return os.environ['NETLOGO_STATE_FILE']
    
    # 方法2：使用模擬ID
    if 'SIMULATION_ID' in os.environ:
        sim_id = os.environ['SIMULATION_ID']
        return f'netlogo_sim_{sim_id}.state'
    
    # 方法3：使用進程ID（預設）
    return f'netlogo_pid_{os.getpid()}.state'

def setup():
    try:
        # Initialize the simulation warehouse
        assignment_path = PARENT_DIRECTORY + f"/data/input/assign_order_{os.getpid()}.csv"
        if os.path.exists(assignment_path):
            os.remove(assignment_path)
        warehouse = Warehouse()
        
        # Populate the warehouse with objects and connections
        draw_layout(warehouse, process_id=os.getpid())
        
        # 創建性能報告生成器
        global performance_reporter
        performance_reporter = PerformanceReportGenerator(warehouse=warehouse)

        # Generate initial results
        next_result = warehouse.generateResult()
        
        warehouse.initWarehouse();

        # Save the warehouse state with unique filename
        state_file = get_state_filename()
        with open(state_file, 'wb') as config_dictionary_file:
            pickle.dump(warehouse, config_dictionary_file)
        
        print(f"已創建狀態檔案: {state_file}")
        return next_result

    except Exception as e:
        traceback.print_exc()
        return "An error occurred. See the details above."

def tick():
    try:
        # Load the simulation state from unique file
        state_file = get_state_filename()
        with open(state_file, 'rb') as file:
            warehouse: Warehouse = pickle.load(file)

        # Update each object with the current warehouse context
        global performance_reporter
        if performance_reporter is None:
            performance_reporter = PerformanceReportGenerator(warehouse=warehouse)
        else:
            performance_reporter.warehouse = warehouse
            performance_reporter.controller_name = warehouse.current_controller
            
        # 收集時間序列數據
        performance_reporter.collect_time_series_data()

        # Perform a simulation tick
        warehouse.tick()

        # Generate results after the tick
        next_result = warehouse.generateResult()

        # Save state back to unique file
        with open(state_file, 'wb') as config_dictionary_file:
            pickle.dump(warehouse, config_dictionary_file)

        return [next_result, warehouse.total_energy, len(warehouse.job_queue), warehouse.stop_and_go,
                warehouse.total_turning, warehouse._tick]
    except Exception as e:
        print("ERROR: Exception in tick function!")
        traceback.print_exc()
        return "An error occurred. See the details above."

def cleanup_state_file():
    """清理狀態檔案"""
    state_file = get_state_filename()
    if os.path.exists(state_file):
        os.remove(state_file)
        print(f"已清理狀態檔案: {state_file}")

# 將原有的所有其他函數也複製過來，但都使用 get_state_filename()
# ... (省略其他函數，它們都需要修改以使用 get_state_filename())
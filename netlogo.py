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
    根據環境變數生成唯一的狀態檔案名稱
    優先順序：
    1. 環境變數 SIMULATION_ID (例如: SIMULATION_ID=exp1 -> states/netlogo_exp1.state)
    2. 預設使用 'states/netlogo.state'
    所有狀態檔案都存放在 states/ 資料夾中
    """
    # 確保 states 資料夾存在
    state_dir = 'states'
    if not os.path.exists(state_dir):
        os.makedirs(state_dir)
    
    sim_id = os.environ.get('SIMULATION_ID', '')
    if sim_id:
        return os.path.join(state_dir, f'netlogo_{sim_id}.state')
    return os.path.join(state_dir, 'netlogo.state')

def setup():
    try:
        # Initialize the simulation warehouse
        assignment_path = PARENT_DIRECTORY + f"/data/input/assign_order_{os.getpid()}.csv"
        if os.path.exists(assignment_path):
            os.remove(assignment_path)
        warehouse = Warehouse()
        
        # Populate the warehouse with objects and connections
        draw_layout(warehouse, process_id=os.getpid())
        # print(warehouse.intersection_manager.intersections[0].intersection_coordinate)

        # 創建性能報告生成器
        global performance_reporter
        performance_reporter = PerformanceReportGenerator(warehouse=warehouse)

        # Generate initial results
        next_result = warehouse.generateResult()
        
        warehouse.initWarehouse();

        # Save the warehouse state for future ticks
        state_file = get_state_filename()
        with open(state_file, 'wb') as config_dictionary_file:
            pickle.dump(warehouse, config_dictionary_file)

        return next_result

    except Exception as e:
        # Print complete stack trace
        traceback.print_exc()
        return "An error occurred. See the details above."


def tick():
    try:
        # print("DEBUG: Loading state...")
        # print("========tick========")

        # Load the simulation state
        state_file = get_state_filename()
        with open(state_file, 'rb') as file:
            warehouse: Warehouse = pickle.load(file)
        # print("DEBUG: State loaded.")

        # Check Robot debug level before printing
        from world.entities.robot import Robot
        if Robot.DEBUG_LEVEL > 1:
            print("before tick", warehouse._tick)

        # print("DEBUG: Collecting time series data...")
        # Update each object with the current warehouse context

        # 收集時間序列數據
        global performance_reporter
        if performance_reporter is None:
            # 如果reporter不存在，創建一個新的
            performance_reporter = PerformanceReportGenerator(warehouse=warehouse)
        else:
            # 保持warehouse引用的最新狀態
            performance_reporter.warehouse = warehouse
            # 確保controller_name與warehouse.current_controller保持一致
            performance_reporter.controller_name = warehouse.current_controller
            
        # 嘗試收集時間序列數據
        performance_reporter.collect_time_series_data()
        # print("DEBUG: Time series data collected.")

        # print("DEBUG: Starting warehouse tick...")

        # Perform a simulation tick
        warehouse.tick()
        # print("DEBUG: Warehouse tick finished.")

        # print("DEBUG: Generating results...")

        # Generate results after the tick
        next_result = warehouse.generateResult()
        # print("DEBUG: Results generated.")

        # print("DEBUG: Saving state...")

        with open(state_file, 'wb') as config_dictionary_file:
            pickle.dump(warehouse, config_dictionary_file)
        # print("DEBUG: State saved.")

        return [next_result, warehouse.total_energy, len(warehouse.job_queue), warehouse.stop_and_go,
                warehouse.total_turning, warehouse._tick]
    except Exception as e:
        # Print complete stack trace
        print("ERROR: Exception in tick function!")
        traceback.print_exc()
        return "An error occurred. See the details above."


def setup_py():
    def install_package(package_name):
        """Install a Python package using pip."""
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
            print(f"Successfully installed {package_name}")
        except subprocess.CalledProcessError as e:
            print(f"Failed to install {package_name}: {e}")

    # List of packages to install
    packages = ["networkx", "matplotlib"]

    # Install each package
    for package in packages:
        install_package(package)


# 新增設置交通控制器的函數
def set_traffic_controller(controller_type, **kwargs):
    """
    從NetLogo設置交通控制器類型
    
    Args:
        controller_type (str): 控制器類型，例如 "time_based", "queue_based", "dqn", "nerl"
        **kwargs: 控制器需要的額外參數
    
    Returns:
        bool: 成功返回True，失敗返回False
    """
    try:
        # 加載模擬狀態
        state_file = get_state_filename()
        with open(state_file, 'rb') as file:
            warehouse: Warehouse = pickle.load(file)
        
        # 設置交通控制器
        success = warehouse.set_traffic_controller(controller_type, **kwargs)
        
        # 保存控制器名稱到warehouse對象中
        warehouse.current_controller = controller_type
        
        # 更新全局的performance_reporter的controller_name
        global performance_reporter
        if performance_reporter is not None:
            performance_reporter.controller_name = controller_type
            print(f"Updated performance reporter controller name to: {controller_type}")
        
        # 保存模擬狀態
        with open(state_file, 'wb') as config_dictionary_file:
            pickle.dump(warehouse, config_dictionary_file)
            
        print(f"交通控制器已設置為: {controller_type}")
        return success
    except Exception as e:
        # 打印完整堆疊信息
        traceback.print_exc()
        return False


# 設置時間基控制器的快捷函數
def set_time_based_controller(horizontal_time=70, vertical_time=30):
    """
    設置時間基控制器
    
    Args:
        horizontal_time (int): 水平方向綠燈時間
        vertical_time (int): 垂直方向綠燈時間
    
    Returns:
        bool: 成功返回True，失敗返回False
    """
    return set_traffic_controller("time_based", 
                               horizontal_green_time=horizontal_time, 
                               vertical_green_time=vertical_time)


# 設置隊列基控制器的快捷函數
def set_queue_based_controller(min_green_time=1, bias_factor=1.5):
    """
    設置隊列基控制器
    
    Args:
        min_green_time (int): 最小綠燈時間
        bias_factor (float): 水平方向偏好因子
    
    Returns:
        bool: 成功返回True，失敗返回False
    """
    return set_traffic_controller("queue_based", 
                               min_green_time=min_green_time, 
                               bias_factor=bias_factor)


# 設置DQN控制器的快捷函數
def set_dqn_controller(exploration_rate=0.6, load_model_tick=None):
    """
    設置DQN控制器
    
    Args:
        exploration_rate (float): 探索率，控制隨機選擇動作的概率
        load_model_tick (int, optional): 加載特定時間點保存的模型（如5000,10000,20000）
    
    Returns:
        bool: 成功返回True，失敗返回False
    """
    result = set_traffic_controller("dqn", exploration_rate=exploration_rate)
    
    # 如果設置成功且指定了模型，嘗試加載模型
    if result and load_model_tick is not None:
        try:
            with open(state_file, 'rb') as file:
                warehouse: Warehouse = pickle.load(file)
                
            # 嘗試加載特定ticks的模型
            if hasattr(warehouse.intersection_manager, 'controller'):
                load_success = warehouse.intersection_manager.controller.load_model(tick=load_model_tick)
                
                # 保存更新後的狀態
                with open(state_file, 'wb') as file:
                    pickle.dump(warehouse, file)
                    
                print(f"DQN model loading {'successful' if load_success else 'failed'} for tick {load_model_tick}")
                return load_success
        except Exception as e:
            print(f"Error when loading model: {e}")
            traceback.print_exc()
            return False
    
    return result


# 設置NERL控制器的快捷函數
def set_nerl_controller(exploration_rate=0.6, load_model_tick=None):
    """
    設置NERL（神經進化強化學習）控制器
    
    Args:
        exploration_rate (float): 探索率，控制隨機選擇動作的概率
        load_model_tick (int, optional): 加載特定時間點保存的模型（如5000,10000,20000）
    
    Returns:
        bool: 成功返回True，失敗返回False
    """
    result = set_traffic_controller("nerl", exploration_rate=exploration_rate)
    
    # 如果設置成功且指定了模型，嘗試加載模型
    if result and load_model_tick is not None:
        try:
            with open(state_file, 'rb') as file:
                warehouse: Warehouse = pickle.load(file)
                
            # 嘗試加載特定ticks的模型
            if hasattr(warehouse.intersection_manager, 'controller'):
                load_success = warehouse.intersection_manager.controller.load_model(tick=load_model_tick)
                
                # 保存更新後的狀態
                with open(state_file, 'wb') as file:
                    pickle.dump(warehouse, file)
                    
                print(f"NERL model loading {'successful' if load_success else 'failed'} for tick {load_model_tick}")
                return load_success
        except Exception as e:
            print(f"Error when loading model: {e}")
            traceback.print_exc()
            return False
    
    return result


# 列出可用的模型函數
def list_available_models(controller_type="all"):
    """
    列出可用的模型及其時間點
    
    Args:
        controller_type (str): 控制器類型，可以是"dqn"、"nerl"或"all"（所有類型）
        
    Returns:
        dict: 包含不同控制器類型的可用模型時間點
    """
    try:
        models_info = {
            "dqn": [],
            "nerl": []
        }
        
        # 檢查models目錄是否存在
        models_dir = "models"
        if not os.path.exists(models_dir):
            return models_info if controller_type == "all" else models_info.get(controller_type, [])
        
        # 遍歷models目錄中的所有文件
        for filename in os.listdir(models_dir):
            # DQN模型
            if filename.startswith('dqn_traffic_') and filename.endswith('.pth'):
                try:
                    tick_str = filename.replace('dqn_traffic_', '').replace('.pth', '')
                    tick = int(tick_str)
                    models_info["dqn"].append(tick)
                except ValueError:
                    continue
            
            # NERL模型
            elif filename.startswith('nerl_traffic_') and filename.endswith('.pth'):
                try:
                    tick_str = filename.replace('nerl_traffic_', '').replace('.pth', '')
                    tick = int(tick_str)
                    models_info["nerl"].append(tick)
                except ValueError:
                    continue
        
        # 對時間點進行排序
        models_info["dqn"] = sorted(models_info["dqn"])
        models_info["nerl"] = sorted(models_info["nerl"])
        
        # 根據請求返回特定控制器類型的模型或所有模型
        if controller_type == "all":
            return models_info
        else:
            return models_info.get(controller_type, [])
    
    except Exception as e:
        # 打印完整堆疊信息
        traceback.print_exc()
        return {} if controller_type == "all" else []


# 設置NERL控制器的訓練/評估模式
def set_nerl_training_mode(is_training=True):
    """
    設置NERL控制器的訓練模式
    
    Args:
        is_training (bool): True為訓練模式，False為評估模式
        
    Returns:
        bool: 操作成功返回True，失敗返回False
    """
    try:
        # 加載模擬狀態
        state_file = get_state_filename()
        with open(state_file, 'rb') as file:
            warehouse: Warehouse = pickle.load(file)
        
        # 檢查當前控制器是否為NERL
        if warehouse.current_controller != "nerl":
            print("當前控制器不是NERL控制器，無法設置訓練模式")
            return False
        
        # 設置訓練模式
        controller = warehouse.intersection_manager.controllers.get("nerl")
        if controller and hasattr(controller, 'set_training_mode'):
            controller.set_training_mode(is_training)
            
            # 保存更新後的狀態
            with open(state_file, 'wb') as file:
                pickle.dump(warehouse, file)
                
            mode_str = "訓練" if is_training else "評估"
            print(f"NERL控制器已設置為{mode_str}模式")
            return True
        else:
            print("無法設置NERL控制器的訓練模式")
            return False
            
    except Exception as e:
        # 打印完整堆疊信息
        traceback.print_exc()
        return False


# 添加DQN控制器的訓練/評估模式切換功能
def set_dqn_training_mode(is_training=True):
    """
    設置DQN控制器的訓練模式
    
    Args:
        is_training (bool): True為訓練模式，False為評估模式
        
    Returns:
        bool: 操作成功返回True，失敗返回False
    """
    try:
        # 加載模擬狀態
        state_file = get_state_filename()
        with open(state_file, 'rb') as file:
            warehouse: Warehouse = pickle.load(file)
        
        # 檢查當前控制器是否為DQN
        if warehouse.current_controller != "dqn":
            print("Current controller is not DQN controller, cannot set training mode")
            return False
        
        # 設置訓練模式
        controller = warehouse.intersection_manager.controllers.get("dqn")
        if controller and hasattr(controller, 'set_training_mode'):
            controller.set_training_mode(is_training)
            
            # 保存更新後的狀態
            with open(state_file, 'wb') as file:
                pickle.dump(warehouse, file)
                
            mode_str = "training" if is_training else "evaluation"
            print(f"DQN controller set to {mode_str} mode")
            return True
        else:
            print("Cannot set DQN controller training mode")
            return False
            
    except Exception as e:
        # 打印完整堆疊信息
        traceback.print_exc()
        return False


def get_all_intersections():
    """獲取所有路口的位置信息"""
    try:
        # 加載模擬狀態
        state_file = get_state_filename()
        with open(state_file, 'rb') as file:
            warehouse: Warehouse = pickle.load(file)
        
        # 收集所有路口的坐標
        intersection_data = []
        for intersection in warehouse.intersection_manager.intersections:
            intersection_data.append([
                intersection.pos_x, 
                intersection.pos_y,
                intersection.id
            ])
        
        return intersection_data
    except Exception as e:
        # 打印完整的堆疊跟踪
        traceback.print_exc()
        return []


def generate_report():
    """
    為當前模擬生成綜合性能報告和圖表
    
    Returns:
        bool: 報告生成成功返回True，失敗返回False
    """
    try:
        # 加載模擬狀態
        state_file = get_state_filename()
        with open(state_file, 'rb') as file:
            warehouse: Warehouse = pickle.load(file)
        
        # 確保使用全局的performance_reporter
        global performance_reporter
        if performance_reporter is None:
            # 如果reporter不存在，創建一個新的
            performance_reporter = PerformanceReportGenerator(warehouse=warehouse)
        else:
            # 保持warehouse引用的最新狀態
            performance_reporter.warehouse = warehouse
            # 確保controller_name與warehouse.current_controller保持一致
            performance_reporter.controller_name = warehouse.current_controller
        
        # 直接使用performance_reporter生成報告（包括時間序列數據保存）
        kpis = performance_reporter.generate_report()
        
        # 生成圖表
        if len(performance_reporter.time_series_data["ticks"]) > 0:
            chart_files = performance_reporter.generate_charts()
            print(f"Generated {len(chart_files)} charts")
        
        print(f"Performance report generated for controller: {warehouse.current_controller}")
        print(f"Time series data was collected for {len(performance_reporter.time_series_data['ticks'])} time points")
        
        return True
    except Exception as e:
        # 打印完整堆疊信息
        traceback.print_exc()
        return False


if __name__ == "__main__":
    result = setup()
    for _ in range(10):
        result = tick()
    # with open('result.txt', 'w') as result_file:
    #     result_file.write(str(result))

# --- New Functions for Training Loop ---

# --- 【修改點 2：修改 training_setup 函式簽名以接收新參數】 ---
def training_setup(controller_type: str, controller_kwargs: dict):
    """
    一個通用的、輕量級的 setup 版本，專為訓練循環設計。
    它會根據傳入的參數設定指定的控制器。

    Args:
        controller_type (str): 要設定的控制器類型 (e.g., 'dqn', 'nerl')
        controller_kwargs (dict): 傳遞給控制器建構函式的參數字典
    """
    try:
        warehouse = Warehouse()
        
        # 從 controller_kwargs 中獲取 process_id，如果沒有則使用當前進程 ID
        process_id = controller_kwargs.get('process_id', os.getpid())
        
        # 步驟 1: 畫出佈局並生成必要的數據檔案
        draw_layout(warehouse, process_id=process_id)
        
        # 步驟 2: 初始化倉庫，這一步會載入初始訂單
        warehouse.initWarehouse()
        
        # 步驟 3: 根據傳入的參數，設定正確的控制器
        # 移除 process_id 以防止傳遞給控制器
        filtered_kwargs = {k: v for k, v in controller_kwargs.items() if k != 'process_id'}
        warehouse.set_traffic_controller(controller_type, **filtered_kwargs)
        
        return warehouse
    except Exception as e:
        traceback.print_exc()
        return None

def get_all_states(warehouse: Warehouse):
    """
    獲取所有交叉口的當前狀態。
    
    Args:
        warehouse (Warehouse): 當前的倉庫實例。
        
    Returns:
        dict: {intersection_id: state_vector}
    """
    if not warehouse:
        return {}
    
    controller = warehouse.intersection_manager.controllers.get(warehouse.current_controller)
    if not controller:
        return {}
        
    states = {}
    for intersection in warehouse.intersection_manager.intersections:
        state = controller.get_state(intersection, warehouse._tick, warehouse)
        # 使用 f"intersection-{id}" 格式，與NERL控制器期望的格式一致
        intersection_key = f"intersection-{intersection.id}"
        states[intersection_key] = state.tolist() # 將numpy array轉為list以便JSON序列化
    return states

def get_intersections_needing_action(warehouse: Warehouse):
    """
    獲取需要進行動作決策的交叉口的當前狀態。
    初始版本：返回所有交叉口的狀態（與 get_all_states 相同）。
    未來優化：只返回有機器人等待的交叉口狀態。
    
    Args:
        warehouse (Warehouse): 當前的倉庫實例。
        
    Returns:
        dict: {intersection_id: state_vector}
    """
    if not warehouse:
        return {}
    
    controller = warehouse.intersection_manager.controllers.get(warehouse.current_controller)
    if not controller:
        return {}
        
    states = {}
    for intersection in warehouse.intersection_manager.intersections:
        # 優化：只收集有機器人的路口狀態
        if len(intersection.horizontal_robots) > 0 or len(intersection.vertical_robots) > 0:
            state = controller.get_state(intersection, warehouse._tick, warehouse)
            # 使用 f"intersection-{id}" 格式，與NERL控制器期望的格式一致
            intersection_key = f"intersection-{intersection.id}"
            states[intersection_key] = state.tolist() # 將numpy array轉為list以便JSON序列化
    return states

def set_actions(warehouse: Warehouse, actions_json: str):
    """
    接收一個包含所有交叉口動作的JSON字符串，並更新它們的方向。
    
    Args:
        warehouse (Warehouse): 當前的倉庫實例。
        actions_json (str): 格式為 '{"intersection_id": action, ...}' 的JSON字符串。
    """
    import json
    try:
        actions = json.loads(actions_json)
        controller = warehouse.intersection_manager.controllers.get(warehouse.current_controller)
        if not controller:
            return False

        for intersection_id, action in actions.items():
            direction = controller.action_to_direction(action, intersection_id)
            if direction:
                try:
                    # 從 'intersection-12' 中提取出數字 12
                    id_num = int(intersection_id.split('-')[1])
                    # 檢查路口是否存在，如果不存在則跳過
                    intersection = warehouse.intersection_manager.findIntersectionById(id_num)
                    if intersection is not None:
                        warehouse.intersection_manager.updateAllowedDirection(id_num, direction, warehouse._tick)
                    # 移除警告訊息，因為某些路口可能在訓練過程中動態創建或不存在
                except (ValueError, IndexError) as e:
                    # 如果ID格式不正確，跳過處理
                    continue
        return True
    except Exception as e:
        traceback.print_exc()
        return False

def training_tick(warehouse: Warehouse):
    """
    一個輕量級的tick版本，專為訓練循環設計。
    它接收一個warehouse實例，執行一個tick，並返回更新後的實例和結果。
    """
    if not warehouse:
        return None, "Warehouse instance is None"
        
    try:
        warehouse.tick()
        # 在訓練tick中，我們不需要像主tick那樣返回所有全域變數
        # 我們只關心模擬是否能繼續
        return warehouse, "OK"
    except Exception as e:
        traceback.print_exc()
        return warehouse, str(e)

def calculate_fitness(warehouse: Warehouse):
    """
    在一次評估運行結束後，計算適應度分數。
    
    Args:
        warehouse (Warehouse): 評估結束後的倉庫實例。
        
    Returns:
        float: 適應度分數。
    """
    if not warehouse:
        return 0.0
        
    # 根據您的研究計畫，適應度 = 能源效率 - 懲罰項
    completed_orders = len([j for j in warehouse.job_manager.jobs if j.is_finished])
    total_energy = warehouse.total_energy
    stop_and_go = warehouse.stop_and_go
    
    # 避免除以零
    energy_efficiency = completed_orders / (total_energy + 1e-6)
    
    # 懲罰項可以根據需要調整權重
    stop_go_penalty = 0.01 * stop_and_go
    
    fitness = energy_efficiency - stop_go_penalty
    
    return fitness


def cleanup_temp_files(process_id: int):
    """
    清理由特定進程 ID 生成的臨時數據檔案。
    防止並行訓練中的文件競爭問題。
    
    Args:
        process_id (int): 進程 ID，用於識別該進程的臨時檔案
    """
    import glob
    
    # 要清理的檔案模式列表（以 process_id 結尾的檔案）
    temp_file_patterns = [
        f"data/input/generated_order_{process_id}.csv",
        f"data/input/generated_backlog_{process_id}.csv", 
        f"data/output/generated_order_{process_id}.csv",
        f"data/output/generated_database_order_{process_id}.csv",
        f"data/output/generated_pod_{process_id}.csv",
        f"data/output/items_{process_id}.csv",
        f"data/output/items_slots_configuration_{process_id}.csv",
        f"data/output/pods_{process_id}.csv",
        f"data/output/skus_data_{process_id}.csv",
        f"data/output/sorted_skus_data_{process_id}.csv",
        f"data/input/assign_order_{process_id}.csv"
    ]
    
    cleaned_files = []
    failed_files = []
    
    for file_pattern in temp_file_patterns:
        try:
            # 使用 glob 匹配檔案，支援通配符
            matching_files = glob.glob(file_pattern)
            
            for file_path in matching_files:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    cleaned_files.append(file_path)
                    
        except Exception as e:
            failed_files.append((file_pattern, str(e)))
    
    # 記錄清理結果（可選擇的日誌記錄）
    if cleaned_files:
        print(f"Worker {process_id}: Cleaned {len(cleaned_files)} temporary files")
        
    if failed_files:
        print(f"Worker {process_id}: Failed to clean {len(failed_files)} files: {failed_files}")
        
    return len(cleaned_files), len(failed_files)

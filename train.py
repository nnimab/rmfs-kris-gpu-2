import argparse
import os
import json
import sys
import subprocess
import time
import platform
from datetime import datetime
import multiprocessing
import torch

# Real imports
import netlogo
from ai.controllers.nerl_controller import NEController
from ai.controllers.dqn_controller import DQNController
from lib.logger import get_logger, set_current_tick
from lib.time_manager import TimeManager
# --- 延遲初始化：步驟 2 ---
from ai.utils import get_device
# --- 結束 ---

import logging

# 初始化為 None，等待命令行參數
logger = None


def evaluate_individual_parallel(args):
    """
    並行評估單個個體的工作函式。
    每個進程擁有獨立的環境。
    """
    # --- 【修改點 3：解包新的 log_file_path 參數並使用它】 ---
    # 1. 解包參數 (新增 log_file_path 和 nerl_params)
    individual_network, eval_ticks, reward_mode, individual_index, generation, log_level, log_file_path, nerl_params = args

    # 獲取當前進程的 PID來解決文件競爭問題
    process_id = os.getpid()
    
    # 2. 每個工作進程獨立設置日誌
    #    使用唯一的名稱確保日誌隔離，但使用共享的檔案路徑
    print(f"DEBUG: Worker {process_id} - log_level: {log_level}, log_file_path: {log_file_path}")
    worker_logger = get_logger(name=f"NERL-Worker-{process_id}", level=log_level, log_file_path=log_file_path)
    # --- 【修改結束】 ---
    
    # Print statement for terminal visibility
    print(f"=== NERL Worker {process_id} evaluating individual {individual_index + 1} (generation {generation + 1}) ===")
    sys.stdout.flush()  # Force stdout flush
    
    worker_logger.info(f"Evaluating individual {individual_index + 1} (generation {generation + 1})")
    print(f"DEBUG: Worker {process_id} - logger setup complete")

    try:
        # 3. 創建獨立、乾淨的 Warehouse 環境
        # --- 【關鍵修改點】 ---
        # 準備要傳遞給 training_setup 的參數
        controller_kwargs = {
            'reward_mode': reward_mode,
            'log_file_path': log_file_path,
            'process_id': process_id  # 新增進程 ID 來解決文件競爭問題
            # 注意：training_dir 是主進程的概念，子進程不需要
        }
        
        # V-Final: 如果有 nerl_params，將其合併到 controller_kwargs
        if nerl_params:
            controller_kwargs.update(nerl_params)
        # 呼叫新的 training_setup，並明確指定控制器類型
        warehouse = netlogo.training_setup(controller_type="nerl", controller_kwargs=controller_kwargs)
        # --- 【修改結束】 ---
        if not warehouse:
            worker_logger.error("Warehouse creation failed.")
            return -1e9, {}  # Return a very poor fitness score and empty summary

        # --- 延遲初始化：步驟 2 ---
        device = get_device()
        individual_network.to(device)
        # --- 結束 ---

        # 4. 載入當前要評估的個體模型
        # 移除舊的 set_traffic_controller 呼叫，因為 setup 已經處理了
        controller = warehouse.intersection_manager.controllers.get('nerl')
        if not controller:
            worker_logger.error("NERL controller not found in warehouse.")
            return -1e9, {}
        controller.set_active_individual(individual_network)
        controller.reset_episode_stats()

        # 5. 運行模擬
        # 記錄開始時間
        start_time = time.time()
        
        for python_tick in range(eval_ticks):
            warehouse_tick = warehouse._tick
            set_current_tick(f"Gen:{generation+1}|Ind:{individual_index+1}|Tick:{python_tick}|WTick:{warehouse_tick:.1f}")

            # 每隔一定時間輸出進度到終端
            if python_tick % 500 == 0:
                print(f"Worker {os.getpid()} - Gen:{generation+1} Ind:{individual_index+1} Tick:{python_tick}/{eval_ticks}")
                sys.stdout.flush()

            # --- 【NERL 速度優化：開始】 ---
            # 步驟 A：從 NetLogo 一次性收集所有需要決策的狀態
            states_dict = netlogo.get_intersections_needing_action(warehouse)
            
            # 檢查是否有需要決策的路口
            if states_dict:
                # 步驟 B：將狀態打包成批次並用 GPU 進行預測
                state_batch_list = list(states_dict.values())
                id_batch_list = list(states_dict.keys())
                
                # 將狀態列表轉換為 PyTorch 張量
                state_tensor = torch.FloatTensor(state_batch_list).to(device)
                
                # 使用神經網路進行批次預測
                individual_network.eval()  # 切換到評估模式，解決 BatchNorm1d 問題
                with torch.no_grad():
                    q_values_batch = individual_network(state_tensor)
                
                # 計算每個狀態的最佳動作
                actions_tensor = torch.argmax(q_values_batch, dim=1)
                actions_list = actions_tensor.cpu().tolist()
                
                # 步驟 C：將批次計算的動作分發回 NetLogo
                actions_to_set = {str(intersection_id): action for intersection_id, action in zip(id_batch_list, actions_list)}
                
                # 轉換為 JSON 格式並設定動作
                actions_json = json.dumps(actions_to_set)
                netlogo.set_actions(warehouse, actions_json)
            
            # 無論是否有動作，都執行一個模擬 tick
            warehouse, status = netlogo.training_tick(warehouse)
            
            # V5.0: 更新溢出懲罰累加器
            if controller.reward_system.reward_mode == "global":
                controller.reward_system.update_spillback_penalty(warehouse)
            # --- 【NERL 速度優化：結束】 ---

            if status != "OK":
                worker_logger.warning(f"模擬中斷: {status}")
                if "critical" in status.lower() or "fatal" in status.lower():
                    break
        
        # 6. 計算並回傳適應度分數和統計摘要
        # 計算執行時間並更新指標
        execution_time = time.time() - start_time
        
        # 安全地更新指標
        try:
            controller.reward_system.update_episode_metrics(warehouse, execution_time)
        except Exception as metrics_error:
            worker_logger.warning(f"更新指標時發生錯誤: {metrics_error}")
            # 繼續執行，但使用基本指標
        
        fitness = controller.calculate_individual_fitness(warehouse, eval_ticks)
        episode_summary = controller.reward_system.get_episode_summary()
        
        # 添加額外的 print 語句以確保 Windows 終端視窗顯示
        print(f"=== NERL Worker {os.getpid()} 個體 {individual_index + 1} (世代 {generation + 1}) 評估完成，適應度: {fitness:.4f} ===")
        sys.stdout.flush()  # 強制刷新 stdout
        
        worker_logger.info(f"個體 {individual_index + 1} (世代 {generation + 1}) 評估完成，適應度: {fitness:.4f}")
        return fitness, episode_summary

    except Exception as e:
        worker_logger.error(f"評估個體 {individual_index + 1} 時發生嚴重錯誤: {e}", exc_info=True)
        return -1e9, {}
    
    finally:
        # 無論成功或失敗，都在結束時清理該進程的臨時檔案
        try:
            netlogo.cleanup_temp_files(process_id)
        except Exception as cleanup_error:
            worker_logger.warning(f"清理臨時檔案時發生錯誤: {cleanup_error}")


def evaluate_final_best_nerl(args):
    """
    對最終找到的最佳個體進行一次詳細的評估，以收集詳細的績效指標。
    """
    # 1. 解包參數
    best_network, eval_ticks, reward_mode, log_level, log_file_path, nerl_params = args
    process_id = os.getpid()
    
    # 2. 獨立設置日誌
    worker_logger = get_logger(name=f"NERL-FinalEval-{process_id}", level=log_level, log_file_path=log_file_path)
    
    print("=== NERL Final Evaluation Started ===")
    sys.stdout.flush()
    worker_logger.info("Evaluating the final best individual...")

    try:
        # 3. 創建獨立的 Warehouse 環境
        controller_kwargs = {
            'reward_mode': reward_mode,
            'log_file_path': log_file_path,
            'process_id': process_id
        }
        if nerl_params:
            controller_kwargs.update(nerl_params)
        
        warehouse = netlogo.training_setup(controller_type="nerl", controller_kwargs=controller_kwargs)
        if not warehouse:
            worker_logger.error("Warehouse creation failed for final evaluation.")
            return {'best_fitness': -1e9, 'completed_orders': 0, 'total_energy': 0.0}

        device = get_device()
        best_network.to(device)

        # 4. 載入最佳個體模型
        controller = warehouse.intersection_manager.controllers.get('nerl')
        if not controller:
            worker_logger.error("NERL controller not found in warehouse for final evaluation.")
            return {'best_fitness': -1e9, 'completed_orders': 0, 'total_energy': 0.0}
        
        controller.set_active_individual(best_network)
        controller.reset_episode_stats()

        # 5. 運行模擬
        for python_tick in range(eval_ticks):
            if python_tick % 500 == 0:
                print(f"Final Eval - Tick:{python_tick}/{eval_ticks}")
                sys.stdout.flush()

            states_dict = netlogo.get_intersections_needing_action(warehouse)
            if states_dict:
                state_batch_list = list(states_dict.values())
                id_batch_list = list(states_dict.keys())
                state_tensor = torch.FloatTensor(state_batch_list).to(device)
                
                best_network.eval()
                with torch.no_grad():
                    q_values_batch = best_network(state_tensor)
                
                actions_tensor = torch.argmax(q_values_batch, dim=1)
                actions_list = actions_tensor.cpu().tolist()
                
                actions_to_set = {str(intersection_id): action for intersection_id, action in zip(id_batch_list, actions_list)}
                actions_json = json.dumps(actions_to_set)
                netlogo.set_actions(warehouse, actions_json)
            
            warehouse, status = netlogo.training_tick(warehouse)
            
            if controller.reward_system.reward_mode == "global":
                controller.reward_system.update_spillback_penalty(warehouse)

            if status != "OK":
                worker_logger.warning(f"模擬中斷於最終評估: {status}")
                if "critical" in status.lower() or "fatal" in status.lower():
                    break
        
        # 6. 計算並收集最終指標
        if reward_mode == "global":
            fitness = controller.reward_system.calculate_global_reward(warehouse, eval_ticks)
        else:
            fitness = controller.calculate_individual_fitness(warehouse, eval_ticks)

        completed_orders = len([j for j in warehouse.job_manager.jobs if j.is_finished])
        total_energy = getattr(warehouse, 'total_energy', 0.0)
        
        summary = {
            "best_fitness": fitness,
            "completed_orders": completed_orders,
            "total_energy": total_energy
        }

        print(f"=== NERL Final Evaluation Complete. Fitness: {fitness:.4f}, Orders: {completed_orders} ===")
        sys.stdout.flush()
        
        worker_logger.info(f"Final evaluation complete. Fitness: {fitness:.4f}, Completed Orders: {completed_orders}, Energy: {total_energy:.2f}")
        return summary

    except Exception as e:
        worker_logger.error(f"最終評估時發生嚴重錯誤: {e}", exc_info=True)
        return {'best_fitness': -1e9, 'completed_orders': 0, 'total_energy': 0.0}
    
    finally:
        try:
            netlogo.cleanup_temp_files(process_id)
        except Exception as cleanup_error:
            worker_logger.warning(f"清理最終評估的臨時檔案時發生錯誤: {cleanup_error}")


def launch_netlogo():
    """啟動 NetLogo GUI 來視覺化倉儲運作"""
    try:
        # 檢查作業系統
        system = platform.system()
        
        # NetLogo 檔案路徑
        nlogo_file = "rmfs.nlogo"
        
        if not os.path.exists(nlogo_file):
            logger.warning(f"找不到 {nlogo_file} 檔案")
            return False
            
        logger.info("正在啟動 NetLogo 視覺化界面...")
        
        # 根據不同系統使用不同的啟動指令
        if system == "Windows":
            # Windows 系統
            subprocess.Popen(["cmd", "/c", "start", nlogo_file], shell=False)
        elif system == "Darwin":
            # macOS 系統
            subprocess.Popen(["open", nlogo_file])
        else:
            # Linux 系統
            subprocess.Popen(["xdg-open", nlogo_file])
        
        # 給 NetLogo 一些時間來啟動
        logger.info("等待 NetLogo 啟動...")
        time.sleep(5)
        
        logger.info("NetLogo 視覺化界面已啟動")
        logger.info("請在 NetLogo 中按 'setup' 然後 'go' 來開始模擬")
        return True
        
    except Exception as e:
        logger.error(f"啟動 NetLogo 時發生錯誤: {e}")
        return False


def run_nerl_training(generations, population_size, evaluation_ticks, reward_mode="global", training_dir=None, parallel_workers=1, log_file_path=None, nerl_params=None):
    """
    Executes the NERL model training loop using the new lightweight functions.
    
    Args:
        generations: 進化代數
        population_size: 族群大小
        evaluation_ticks: 每個個體的評估時間
        reward_mode: 獎勵模式，"global"或"step"（V6.0已改進）
    """
    # 檢查日誌級別，只有在適當級別時才顯示訓練信息
    if logger and logger.isEnabledFor(logging.INFO):
        logger.info("--- Starting NERL Training ---")
        logger.info(f"Generations: {generations}, Population: {population_size}, Eval Ticks: {evaluation_ticks}")
        logger.info(f"Reward Mode: {reward_mode}")

    # 記錄訓練開始時間
    start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # --- 【修改點 3：將 log_file_path 和 nerl_params 傳遞給 NEController】 ---
    # 1. Initialize the actual NERL controller with specified reward mode
    # V-Final: 合併預設參數和變體參數
    controller_kwargs = {
        'population_size': population_size,
        'reward_mode': reward_mode,
        'training_dir': training_dir,
        'log_file_path': log_file_path
    }
    
    # 如果有提供 nerl_params，將其合併到 controller_kwargs
    if nerl_params:
        controller_kwargs.update(nerl_params)
        logger.info(f"Using NERL parameters: {nerl_params}")
    
    nerl_controller = NEController(**controller_kwargs)
    # --- 【修改結束】 ---

    # 獲取主日誌級別以傳遞給工作進程
    log_level = logger.level

    # 2. Main generation evolution loop
    for gen in range(generations):
        logger.info(f"\n--- Generation {gen + 1}/{generations} ---")
        
        # --- 【修改點 2：將 log_file_path 和 nerl_params 加入到任務參數中】 ---
        # 準備並行任務所需的參數列表
        tasks = [
            (individual_network, evaluation_ticks, reward_mode, i, gen, log_level, log_file_path, nerl_params)
            for i, individual_network in enumerate(nerl_controller.population)
        ]
        # --- 【修改結束】 ---

        evaluation_results = []
        if parallel_workers > 1:
            logger.info(f"Using {parallel_workers} parallel processes to evaluate population...")
            # 使用 'spawn' 啟動方法以獲得跨平台的最大兼容性
            ctx = multiprocessing.get_context('spawn')
            with ctx.Pool(processes=parallel_workers) as pool:
                # 分發任務並收集結果
                evaluation_results = pool.map(evaluate_individual_parallel, tasks)
        else:
            logger.info("使用序列模式評估族群...")
            # 序列執行作為後備和調試選項
            evaluation_results = [evaluate_individual_parallel(task) for task in tasks]

        # 分離適應度分數和統計摘要
        fitness_scores = []
        episode_summaries = []
        
        for i, result in enumerate(evaluation_results):
            if isinstance(result, tuple) and len(result) >= 2:
                fitness_scores.append(result[0])
                episode_summaries.append(result[1])
            else:
                # 如果結果不是預期的元組格式，記錄警告並使用默認值
                logger.warning(f"Individual {i} returned unexpected result format: {type(result)}")
                fitness_scores.append(float(result) if isinstance(result, (int, float)) else -1e9)
                episode_summaries.append({})

        # 4. Evolve the population using the collected fitness scores and episode summaries
        # This requires a new method in the controller: evolve_with_fitness
        try:
            best_fitness_of_gen = nerl_controller.evolve_with_fitness(fitness_scores, episode_summaries, generation=gen+1)
            logger.info(f"Generation {gen + 1} complete. Best fitness so far: {best_fitness_of_gen:.4f}")
            logger.info(f"  Fitness scores for this generation: {fitness_scores}")
        except Exception as e:
            logger.error(f"ERROR during evolution for generation {gen + 1}: {e}")
            break  # Stop training if evolution fails

    # 5. Save the final best model
    try:
        nerl_controller.save_model(is_final=True)
        logger.info("Final model saved successfully!")
    except Exception as e:
        logger.error(f"ERROR saving final model: {e}")
    
    # 6. 對最佳個體進行最終評估並顯示結果
    if nerl_controller.best_individual:
        logger.info("\n--- Running Final Evaluation on Best Individual ---")
        
        # 準備最終評估的參數
        final_eval_args = (
            nerl_controller.best_individual, evaluation_ticks, reward_mode, 
            logger.level, log_file_path, nerl_params
        )
        
        # 為最終評估創建一個單獨的進程，以確保環境隔離
        ctx = multiprocessing.get_context('spawn')
        with ctx.Pool(processes=1) as pool:
            final_summary_list = pool.map(evaluate_final_best_nerl, [final_eval_args])
            final_summary = final_summary_list[0] if final_summary_list else {}

        logger.info("--- NERL Final Performance Summary ---")
        logger.info(f"  Best Fitness Achieved: {final_summary.get('best_fitness', 'N/A')}")
        logger.info(f"  Completed Orders: {final_summary.get('completed_orders', 'N/A')}")
        logger.info(f"  Total Energy Consumed: {final_summary.get('total_energy', 0.0):.2f}")
    else:
        logger.warning("No best individual found, skipping final evaluation.")
        final_summary = {}

    # 記錄訓練結束時間和元資料
    end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if training_dir:
        config = {
            "generations": generations,
            "population_size": population_size,
            "evaluation_ticks": evaluation_ticks,
            "elite_size": nerl_controller.elite_size,
            "mutation_rate": nerl_controller.mutation_rate,
            "crossover_rate": nerl_controller.crossover_rate,
            "mutation_strength": nerl_controller.mutation_strength,
            "variant": args.variant if args.variant else "default"
        }
        # 合併最終評估結果
        final_results = {
            "best_fitness": getattr(nerl_controller, 'best_fitness', 0),
            "total_generations": gen + 1,
            "completed_orders_final_eval": final_summary.get('completed_orders'),
            "total_energy_final_eval": final_summary.get('total_energy')
        }
        nerl_controller.save_metadata(start_time, end_time, config, final_results)
    
    logger.info("--- NERL Training Finished ---")
    logger.info(f"Training completed {gen + 1} generations with population size {population_size}")
    if hasattr(nerl_controller, 'best_fitness'):
        logger.info(f"Best fitness achieved: {nerl_controller.best_fitness:.4f}")


def run_dqn_training(training_ticks, reward_mode="step", training_dir=None, log_file_path=None, batch_size=512):
    """
    執行DQN模型訓練循環
    
    Args:
        training_ticks: 訓練總時間步數
        reward_mode: 獎勵模式，"global"或"step"（V6.0已改進）
    """
    # 記錄訓練開始時間
    start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 檢查日誌級別，只有在適當級別時才顯示訓練信息
    if logger and logger.isEnabledFor(logging.INFO):
        logger.info("--- Starting DQN Training ---")
        logger.info(f"Training Ticks: {training_ticks}")
        logger.info(f"Reward Mode: {reward_mode}")

    # 初始化倉庫和DQN控制器
    # --- 【關鍵修改點】 ---
    # 準備要傳遞給 training_setup 的參數
    controller_kwargs = {
        'reward_mode': reward_mode, 
        'training_dir': training_dir, 
        'log_file_path': log_file_path,
        'batch_size': batch_size
    }
    # 呼叫新的 training_setup，並明確指定控制器類型
    warehouse = netlogo.training_setup(controller_type="dqn", controller_kwargs=controller_kwargs)
    # --- 【修改結束】 ---
    if warehouse is None:
        logger.error("Failed to set up warehouse for DQN training.")
        return

    # --- 延遲初始化：步驟 2 ---
    # 在 warehouse 創建成功後，再把模型移到 GPU
    dqn_controller = warehouse.intersection_manager.controllers.get('dqn')
    if dqn_controller:
        device = get_device()
        dqn_controller.dqn.policy_net.to(device)
        dqn_controller.dqn.target_net.to(device)
        dqn_controller.dqn.device = device # 確保 device 屬性也更新
        logger.info(f"DQN models have been moved to {device}.")
    else:
        logger.error("DQN controller not found after warehouse setup.")
        return
    # --- 結束 ---

    # 移除舊的 set_traffic_controller 呼叫，因為 setup 已經處理了
    # warehouse.set_traffic_controller("dqn", **controller_kwargs)
    dqn_controller = warehouse.intersection_manager.controllers.get('dqn')
    if not dqn_controller:
        logger.error("DQN controller not found in warehouse.")
        return

    # 設置訓練模式
    dqn_controller.set_training_mode(True)
    
    # 重置統計數據
    dqn_controller.reset_episode_stats()

    # 檢查日誌級別，只有在 INFO 或更低級別時才顯示訓練開始訊息
    if logger and logger.isEnabledFor(logging.INFO):
        logger.info("Starting DQN training loop...")
    
    # 死鎖檢測變數
    no_movement_ticks = 0
    last_completed_orders = 0
    last_robot_positions = {}
    deadlock_threshold = 100  # 連續 100 ticks 沒有進展就判定死鎖
    
    # 訓練循環
    for python_tick in range(training_ticks):
        # 設置當前 tick 給日誌系統（使用倉庫的實際時間）
        warehouse_tick = warehouse._tick if warehouse else python_tick * 0.15
        set_current_tick(f"Python:{python_tick}|倉庫:{warehouse_tick:.1f}")
        
        if python_tick % 1000 == 0:
            # 檢查日誌級別，只有在 INFO 或更低級別時才顯示進度
            if logger and logger.isEnabledFor(logging.INFO):
                logger.info(f"Training progress: {python_tick}/{training_ticks} ({python_tick/training_ticks*100:.1f}%) | 模擬時間: {warehouse_tick:.1f}")
            
        # 執行一個時間步
        warehouse, status = netlogo.training_tick(warehouse)
        
        # V5.0: 更新溢出懲罰累加器
        if warehouse and dqn_controller.reward_system.reward_mode == "global":
            dqn_controller.reward_system.update_spillback_penalty(warehouse)
        
        if status != "OK":
            logger.error(f"ERROR during training: {status}")
            # 只有在嚴重錯誤時才停止
            if "critical" in status.lower() or "fatal" in status.lower():
                break
            else:
                logger.warning(f"Non-critical error, continuing training...")

        # DQN控制器會在intersection_manager.update_traffic_using_controller中自動訓練
        
        # 死鎖檢測
        if python_tick % 10 == 0:  # 每 10 ticks 檢查一次
            # 檢查是否有訂單完成
            current_completed_orders = len([j for j in warehouse.job_manager.jobs if j.is_finished])
            
            # 檢查機器人是否有移動
            robots_moved = False
            current_positions = {}
            for robot in warehouse.robot_manager.robots:
                current_pos = (robot.pos_x, robot.pos_y)
                current_positions[robot.id] = current_pos
                
                if robot.id in last_robot_positions:
                    if last_robot_positions[robot.id] != current_pos:
                        robots_moved = True
                        break
            
            # 判斷是否有進展
            if current_completed_orders > last_completed_orders or robots_moved:
                no_movement_ticks = 0  # 重置計數器
            else:
                no_movement_ticks += 10
            
            # 更新記錄
            last_completed_orders = current_completed_orders
            last_robot_positions = current_positions.copy()
            
            # 檢查是否死鎖
            if no_movement_ticks >= deadlock_threshold:
                logger.warning(f"WARNING: System appears to be deadlocked!")
                logger.warning(f"  - No robot movement for {no_movement_ticks} ticks")
                logger.warning(f"  - Completed orders: {current_completed_orders}")
                logger.warning(f"  - Total orders: {len(warehouse.job_manager.jobs)}")
                
                # 顯示每個路口的等待情況
                total_waiting = 0
                max_wait = 0
                for intersection in warehouse.intersection_manager.intersections:
                    h_robots = len(intersection.horizontal_robots)
                    v_robots = len(intersection.vertical_robots)
                    if h_robots + v_robots > 0:
                        total_waiting += h_robots + v_robots
                        # 計算最大等待時間
                        for robot in list(intersection.horizontal_robots.values()) + list(intersection.vertical_robots.values()):
                            if hasattr(robot, 'current_intersection_start_time') and robot.current_intersection_start_time:
                                wait_time = warehouse._tick - robot.current_intersection_start_time
                                max_wait = max(max_wait, wait_time)
                
                logger.warning(f"  - Total robots waiting at intersections: {total_waiting}")
                logger.warning(f"  - Maximum wait time: {max_wait} ticks")
                
                # 對於 global 獎勵模式，不應該提前終止
                if args.reward_mode == 'global':
                    logger.warning(f"  - Continuing despite deadlock (global reward mode requires full episode)")
                    # 可選：重置死鎖計數器，給系統一個恢復的機會
                    if no_movement_ticks >= deadlock_threshold * 2:
                        logger.error(f"  - Severe deadlock detected, but continuing for global reward calculation")
                else:
                    logger.error(f"Ending training due to deadlock.")
                    break

    # 對於 global 模式，在訓練結束時處理最後的 episode
    if reward_mode == "global":
        logger.info("Processing final episode for global reward...")
        dqn_controller.process_episode_end(warehouse, python_tick + 1)
        
        # 執行最後一次訓練以學習全局獎勵
        if len(dqn_controller.dqn.memory) >= dqn_controller.batch_size:
            logger.info("Performing final replay training with global rewards...")
            for _ in range(10):  # 多次訓練以充分學習全局獎勵
                dqn_controller.dqn.replay()
    
    # 保存最終的訓練數據和模型
    try:
        # 保存最後的 episode 總結
        dqn_controller.save_episode_summary(python_tick + 1, warehouse)
        
        # 保存完整的訓練歷史
        dqn_controller.save_training_history()
        
        # 保存最終模型
        dqn_controller.save_model(tick=training_ticks, is_final=True)
        logger.info("Final DQN model and training data saved successfully!")
    except Exception as e:
        logger.error(f"ERROR saving final DQN model or training data: {e}")
    
    # 獲取並記錄訓練總結
    summary = dqn_controller.reward_system.get_episode_summary()
    completed_orders = len([j for j in warehouse.job_manager.jobs if j.is_finished])
    
    logger.info("--- DQN Training Summary ---")
    logger.info(f"  Total Ticks: {python_tick + 1}")
    logger.info(f"  Completed Orders: {completed_orders}")
    logger.info(f"  Final Epsilon: {getattr(dqn_controller.dqn, 'epsilon', 0.01):.4f}")
    if 'total_reward' in summary:
        logger.info(f"  Cumulative Reward (Step Mode): {summary.get('total_reward', 0.0):.4f}")

    # 記錄訓練結束時間和元資料
    end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if training_dir:
        config = {
            "training_ticks": training_ticks,
            "batch_size": dqn_controller.dqn.batch_size,
            "learning_rate": dqn_controller.dqn.learning_rate,
            "gamma": dqn_controller.dqn.gamma,
            "epsilon_start": 1.0,
            "epsilon_end": dqn_controller.dqn.epsilon_min,
            "memory_size": dqn_controller.dqn.memory.maxlen,
            "variant": args.variant if args.variant else "default"
        }
        final_results = {
            "total_ticks": python_tick + 1,
            "completed_orders": completed_orders,
            "final_epsilon": getattr(dqn_controller.dqn, 'epsilon', 0.01),
            "cumulative_step_reward": summary.get('total_reward', 0.0)
        }
        dqn_controller.save_metadata(start_time, end_time, config, final_results)

    logger.info("--- DQN Training Finished ---")
    logger.info(f"Training completed {training_ticks} ticks")


def main():
    """主函數，用於解析參數並啟動訓練。"""
    parser = argparse.ArgumentParser(description="RMFS Controller Training Script with Unified Reward System")
    parser.add_argument('--agent', type=str, required=True, choices=['nerl', 'dqn'], help="The agent to train.")
    parser.add_argument('--reward_mode', type=str, default='step', choices=['step', 'global'], 
                        help="Reward mode: 'step' for immediate rewards, 'global' for episode rewards")
    
    # NERL specific parameters
    parser.add_argument('--generations', type=int, default=50, help="Number of generations for NERL training.")
    parser.add_argument('--population', type=int, default=20, help="Population size for NERL training.")
    parser.add_argument('--eval_ticks', type=int, default=2000, help="Number of ticks to evaluate each individual in NERL.")
    
    # DQN specific parameters
    parser.add_argument('--training_ticks', type=int, default=10000, help="Number of training ticks for DQN.")
    parser.add_argument('--batch_size', type=int, default=8192, help="Batch size for DQN training (optimized for RTX 4090).")
    
    # 並行化參數 (新增)
    parser.add_argument('--parallel_workers', type=int, default=1, 
                        help="用於 NERL 個體評估的並行進程數。預設為1 (序列執行)。建議設為 CPU 核心數 - 1。")
                        
    # NetLogo visualization parameter
    parser.add_argument('--netlogo', action='store_true', help="Launch NetLogo GUI for visualization")
    
    # 日誌級別參數
    parser.add_argument('--log_level', type=str, default='INFO', 
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                        help="設置日誌輸出級別")
    
    # 變體參數（用於區分同類型的不同配置）
    parser.add_argument('--variant', type=str, default=None,
                        help="變體標識符（如 a, b），用於區分同類型的不同配置")
    
    # V6.0: Step 獎勵已自動改進，無需額外參數
    
    args = parser.parse_args()
    
    # 設置日誌級別
    log_level_map = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR
    }
    
    # --- 【修改點 1：在這裡建立訓練目錄與日誌】 ---
    # 1. 創建專屬的訓練目錄
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    # 包含 variant 參數在目錄名稱中
    if args.variant:
        training_dir = os.path.join("models", "training_runs", f"{timestamp}_{args.agent}_{args.reward_mode}_{args.variant}")
    else:
        training_dir = os.path.join("models", "training_runs", f"{timestamp}_{args.agent}_{args.reward_mode}")
    os.makedirs(training_dir, exist_ok=True)

    # 2. 定義日誌檔案的完整路徑
    log_file_path = os.path.join(training_dir, "training.log")

    # 3. 初始化全域 logger，同時指定日誌檔案路徑和終端機輸出級別
    #    這會讓 logger 同時輸出到檔案和終端機
    global logger
    logger = get_logger(log_file_path=log_file_path, level=log_level_map[args.log_level])
    # --- 【修改結束】 ---

    logger.info(f"日誌級別設置為: {args.log_level}")

    # 參數驗證
    if args.training_ticks <= 0:
        logger.error("訓練時長必須大於0")
        sys.exit(1)
    
    if args.generations <= 0:
        logger.error("進化代數必須大於0")
        sys.exit(1)
    
    if args.population <= 0:
        logger.error("族群大小必須大於0")
        sys.exit(1)
    
    if args.eval_ticks <= 0:
        logger.error("評估時長必須大於0")
        sys.exit(1)

    # 如果指定了 --netlogo 參數，啟動 NetLogo GUI
    if args.netlogo:
        netlogo_launched = launch_netlogo()
        if not netlogo_launched:
            choice = input("\nWARNING: NetLogo 啟動失敗。是否繼續訓練？[y/N]: ")
            if choice.lower() != 'y':
                logger.info("訓練已取消")
                sys.exit(0)
        else:
            input("\nINFO: 請確認 NetLogo 已正確設置，然後按 Enter 繼續訓練...")

    # 使用指定的獎勵模式
    reward_mode = args.reward_mode
    
    logger.info(f"Training {args.agent.upper()} controller with {reward_mode} reward mode")
    logger.info(f"Training directory: {training_dir}")

    if args.agent == 'nerl':
        # V-Final: 實現差異化的NERL超參數變體
        # 通用基礎參數
        base_nerl_params = {
            'elite_size': 2,
            'crossover_rate': 0.7
        }
        
        # 根據 variant 設置差異化參數
        variant_params = {}
        if args.variant == 'a':
            # 探索型 (Exploration)
            variant_params = {
                'mutation_rate': 0.3,
                'mutation_strength': 0.2
            }
            logger.info("Using Variant A (Exploration): higher mutation rate and strength")
        elif args.variant == 'b':
            # 利用型 (Exploitation)
            variant_params = {
                'mutation_rate': 0.1,
                'mutation_strength': 0.05
            }
            logger.info("Using Variant B (Exploitation): lower mutation rate and strength")
        else:
            # 預設值
            logger.info("No variant specified, using default NERL parameters")
        
        # 合併參數
        nerl_params = {**base_nerl_params, **variant_params}
        
        # 將 training_dir 和 log_file_path 傳遞給訓練函式
        run_nerl_training(args.generations, args.population, args.eval_ticks, reward_mode, 
                          training_dir, args.parallel_workers, log_file_path, nerl_params)
    elif args.agent == 'dqn':
        # 將 training_dir 和 log_file_path 傳遞給訓練函式
        run_dqn_training(args.training_ticks, reward_mode, training_dir, log_file_path, args.batch_size)
    else:
        logger.error("Invalid agent specified.")
    
    # 創建任務完成標記文件
    try:
        import tempfile
        
        # 生成任務名稱
        task_name = f"{args.agent}_{reward_mode}"
        if args.variant:
            task_name += f"_{args.variant}"
        
        # 創建完成標記文件
        temp_dir = tempfile.gettempdir()
        completion_dir = os.path.join(temp_dir, "rmfs_completion_flags")
        os.makedirs(completion_dir, exist_ok=True)
        completion_file = os.path.join(completion_dir, f"{task_name}.completed")
        
        with open(completion_file, 'w') as f:
            f.write(f"Training completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        logger.info(f"任務完成標記已創建: {completion_file}")
    except Exception as e:
        logger.warning(f"無法創建完成標記文件: {e}")

if __name__ == "__main__":
    main()

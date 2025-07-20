#!/usr/bin/env python3
"""
驗證能耗追蹤是否正常運作的快速測試腳本
"""

import sys
import os
import argparse
from datetime import datetime

# 添加專案根目錄到 Python 路徑
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

import netlogo
from lib.logger import get_logger
import logging

def verify_energy_consumption(eval_ticks=400):
    """
    運行短時評估並驗證能耗值
    
    Args:
        eval_ticks: 評估時間步數
    """
    logger = get_logger("EnergyVerification")
    logger.info(f"=== 開始能耗驗證測試 ===")
    logger.info(f"評估時間步數: {eval_ticks}")
    
    try:
        # 初始化 NetLogo 交互
        # netlogo 模組已經被導入，直接使用
        
        # 使用簡單的 time-based 控制器進行測試
        controller_kwargs = {}
        warehouse = netlogo.training_setup(controller_type="time_based", controller_kwargs=controller_kwargs)
        
        if not warehouse:
            logger.error("無法初始化倉庫")
            return
        
        logger.info("倉庫初始化成功，開始運行模擬...")
        
        # 記錄初始能耗（應該是 0）
        initial_energy = getattr(warehouse, 'total_energy', 0.0)
        logger.info(f"初始總能耗: {initial_energy:.6f}")
        
        # 運行模擬
        robot_energy_samples = []
        
        for tick in range(eval_ticks):
            if tick % 50 == 0:
                logger.info(f"進度: {tick}/{eval_ticks}")
                
                # 記錄當前總能耗
                current_total_energy = getattr(warehouse, 'total_energy', 0.0)
                logger.info(f"  當前總能耗: {current_total_energy:.6f}")
                
                # 取樣機器人個別能耗
                for robot in warehouse.robot_manager.robots[:3]:  # 只取前3個機器人
                    if hasattr(robot, 'energy_consumption'):
                        logger.info(f"  機器人 {robot.id} 能耗: {robot.energy_consumption:.6f}")
                        if robot.energy_consumption > 0 and tick > 0:
                            robot_energy_samples.append(robot.energy_consumption)
            
            # 執行一個時間步
            warehouse, status = netlogo.training_tick(warehouse)
            
            if status != "OK":
                logger.warning(f"模擬狀態異常: {status}")
                if "critical" in status.lower():
                    break
        
        # 最終結果
        final_total_energy = getattr(warehouse, 'total_energy', 0.0)
        logger.info(f"\n=== 能耗驗證結果 ===")
        logger.info(f"模擬運行 ticks: {tick + 1}")
        logger.info(f"最終總能耗: {final_total_energy:.6f}")
        logger.info(f"平均每 tick 能耗: {final_total_energy / (tick + 1) if tick > 0 else 0:.6f}")
        
        # 驗證個別機器人能耗
        logger.info(f"\n機器人能耗詳情:")
        moving_robots = 0
        for i, robot in enumerate(warehouse.robot_manager.robots):
            if hasattr(robot, 'energy_consumption') and robot.energy_consumption > 0:
                moving_robots += 1
                if i < 5:  # 只顯示前5個有移動的機器人
                    logger.info(f"  機器人 {robot.id}:")
                    logger.info(f"    累積能耗: {robot.energy_consumption:.6f}")
                    logger.info(f"    當前狀態: {robot.current_state}")
                    logger.info(f"    總活動時間: {getattr(robot, 'total_active_time', 0)} ticks")
        
        logger.info(f"\n有移動的機器人數量: {moving_robots}/{len(warehouse.robot_manager.robots)}")
        
        # 驗證結論
        if final_total_energy > 0:
            logger.info(f"\n✅ 能耗追蹤正常運作！總能耗為正值: {final_total_energy:.6f}")
        else:
            logger.error(f"\n❌ 能耗追蹤異常！總能耗為零或負值: {final_total_energy:.6f}")
        
        # 顯示一些統計
        if robot_energy_samples:
            avg_robot_energy = sum(robot_energy_samples) / len(robot_energy_samples)
            logger.info(f"\n機器人平均能耗（基於取樣）: {avg_robot_energy:.6f}")
        
    except Exception as e:
        logger.error(f"驗證過程中發生錯誤: {e}", exc_info=True)
    finally:
        # 清理
        try:
            netlogo.cleanup_temp_files(0)
        except:
            pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="驗證能耗追蹤系統")
    parser.add_argument('--ticks', type=int, default=400, help='評估時間步數')
    parser.add_argument('--log_level', type=str, default='INFO', 
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                        help='日誌級別')
    
    args = parser.parse_args()
    
    # 設置日誌級別
    log_level = getattr(logging, args.log_level)
    logging.getLogger().setLevel(log_level)
    
    # 運行驗證
    verify_energy_consumption(eval_ticks=args.ticks)
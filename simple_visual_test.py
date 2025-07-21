#!/usr/bin/env python
"""
簡化的視覺化測試腳本
直接在 NetLogo 中運行並觀察行為
"""

import netlogo
import time
from ai.controllers.dqn_controller import DQNController

def main():
    print("初始化倉儲系統...")
    
    # 設置 DQN 控制器
    controller_kwargs = {
        'reward_mode': 'step',
        'model_name': 'dqn_step',
        'state_size': 17,
        'action_size': 6,
        'training_dir': 'test_visual'
    }
    
    # 初始化倉儲
    warehouse = netlogo.training_setup(controller_type="dqn", controller_kwargs=controller_kwargs)
    
    if not warehouse:
        print("倉儲初始化失敗！")
        return
    
    print("倉儲初始化成功！")
    print("請在 NetLogo 中：")
    print("1. 點擊 'setup'")
    print("2. 點擊 'go' (勾選 forever)")
    print("3. 觀察機器人行為")
    
    # 簡單的訓練循環
    for i in range(100):
        warehouse.tick()
        time.sleep(0.1)  # 慢一點以便觀察
        
        if i % 10 == 0:
            print(f"Tick {i}: 完成訂單 {len(warehouse.job_shop.finished_jobs)}")

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
並行評估啟動器 - 每個評估使用獨立的狀態檔案
"""
import os
import sys
import time
import subprocess
from datetime import datetime
from pathlib import Path

def run_parallel_evaluations():
    """
    並行執行多個評估，每個使用不同的狀態檔案
    """
    # 定義要評估的控制器
    controllers = [
        ('time_based', 'time_based'),
        ('queue_based', 'queue_based'),
        ('dqn_step', 'dqn:models/dqn_step_55000.pth'),
        ('dqn_global', 'dqn:models/dqn_global_55000.pth'),
        ('nerl_step', 'nerl:models/nerl_step_a8000.pth'),
        ('nerl_global', 'nerl:models/nerl_global_a8000.pth'),
        ('no_control_1', 'none'),
        ('no_control_2', 'none')
    ]
    
    # 創建結果目錄
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_output_dir = Path(f"parallel_results_{timestamp}")
    base_output_dir.mkdir(exist_ok=True)
    
    # 啟動所有評估
    processes = []
    for i, (name, controller_spec) in enumerate(controllers):
        # 設定環境變數
        env = os.environ.copy()
        env['SIMULATION_ID'] = f"{name}_{timestamp}"
        env['NETLOGO_STATE_FILE'] = f"states/netlogo_{name}_{timestamp}.state"
        
        # 確保狀態目錄存在
        Path("states").mkdir(exist_ok=True)
        
        # 準備命令
        output_dir = base_output_dir / name
        cmd = [
            sys.executable, 'evaluate.py',
            '--controllers', controller_spec,
            '--output_dir', str(output_dir),
            '--eval_ticks', '50000',
            '--num_runs', '1'
        ]
        
        print(f"啟動評估 {i+1}/8: {name}")
        print(f"  狀態檔案: {env['NETLOGO_STATE_FILE']}")
        print(f"  輸出目錄: {output_dir}")
        
        # 啟動進程
        process = subprocess.Popen(cmd, env=env)
        processes.append((name, process))
        
        # 等待 5 秒再啟動下一個
        if i < len(controllers) - 1:
            print(f"  等待 5 秒再啟動下一個...")
            time.sleep(5)
    
    print("\n所有評估已啟動，等待完成...")
    
    # 監控進程
    while True:
        all_done = True
        for name, process in processes:
            if process.poll() is None:
                all_done = False
            else:
                if process.returncode == 0:
                    print(f"✅ {name} 已完成")
                else:
                    print(f"❌ {name} 失敗 (返回碼: {process.returncode})")
        
        if all_done:
            break
        
        time.sleep(30)  # 每 30 秒檢查一次
    
    print(f"\n所有評估完成！結果保存在: {base_output_dir}")
    
    # 清理狀態檔案
    print("\n清理狀態檔案...")
    for state_file in Path("states").glob("netlogo_*.state"):
        try:
            state_file.unlink()
            print(f"  已刪除: {state_file}")
        except:
            pass

if __name__ == "__main__":
    run_parallel_evaluations()
#!/usr/bin/env python3
"""簡單的測試狀態檢查腳本"""
import json
from pathlib import Path
from datetime import datetime

def check_test_status():
    results_dir = Path(__file__).parent / "results"
    
    # 找到最新的測試目錄
    test_dirs = sorted([d for d in results_dir.iterdir() if d.is_dir() and d.name.startswith("capacity_test_")], 
                      key=lambda x: x.stat().st_mtime, reverse=True)
    
    if not test_dirs:
        print("沒有找到測試結果")
        return
    
    latest_dir = test_dirs[0]
    print(f"最新測試目錄: {latest_dir.name}")
    print("="*60)
    
    # 檢查工作空間
    workspaces_dir = latest_dir / "workspaces"
    if workspaces_dir.exists():
        workspaces = list(workspaces_dir.iterdir())
        print(f"工作空間數量: {len(workspaces)}")
        
        # 檢查每個工作空間的狀態
        for ws in sorted(workspaces):
            # 解析機器人數量和運行次數
            parts = ws.name.split("_")
            if len(parts) >= 4:
                robot_count = parts[1]
                run_num = parts[2].replace("run", "")
                
                # 檢查是否有結果檔案
                result_file = ws / "results" / ws.name / "evaluation_results.json"
                log_file = ws / "logs" / f"{ws.name}_evaluation.log"
                
                status = "❓ 未知"
                if result_file.exists():
                    # 讀取結果
                    try:
                        with open(result_file, 'r') as f:
                            result = json.load(f)
                        completed_orders = result.get('completed_orders', 0)
                        total_orders = result.get('total_orders', 0)
                        final_tick = result.get('warehouse_final_tick', 0)
                        status = f"✅ 完成 - 訂單: {completed_orders}/{total_orders}, Tick: {final_tick}"
                    except:
                        status = "✅ 完成（無法讀取結果）"
                elif log_file.exists():
                    # 檢查日誌最後修改時間
                    mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
                    time_diff = (datetime.now() - mtime).total_seconds()
                    if time_diff < 60:  # 1分鐘內有更新
                        status = "🔄 執行中"
                    else:
                        status = f"⚠️  可能卡住（{int(time_diff/60)}分鐘無更新）"
                else:
                    status = "🔄 準備中"
                
                print(f"機器人 {robot_count} - 第 {int(run_num)+1} 次: {status}")
    
    # 檢查總結檔案
    summary_file = latest_dir / "capacity_test_summary.json"
    if summary_file.exists():
        print("\n" + "="*60)
        print("測試總結:")
        try:
            with open(summary_file, 'r') as f:
                summary = json.load(f)
            print(f"完成測試: {summary['completed_tests']}/{summary['total_tests']}")
            print(f"執行時間: {summary['total_execution_time']:.1f} 秒")
        except:
            print("無法讀取總結檔案")

if __name__ == "__main__":
    check_test_status()
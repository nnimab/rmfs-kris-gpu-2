#!/usr/bin/env python3
"""
清理狀態檔案的工具腳本
"""
import os
import shutil
from datetime import datetime, timedelta
from pathlib import Path

def clean_state_files(keep_recent_hours=24):
    """
    清理 states 資料夾中的狀態檔案
    
    Args:
        keep_recent_hours: 保留最近幾小時的檔案（預設24小時）
    """
    state_dir = Path('states')
    
    if not state_dir.exists():
        print("states 資料夾不存在")
        return
    
    # 計算時間閾值
    cutoff_time = datetime.now() - timedelta(hours=keep_recent_hours)
    
    removed_count = 0
    kept_count = 0
    total_size = 0
    
    print(f"清理 {state_dir} 中超過 {keep_recent_hours} 小時的檔案...")
    
    for state_file in state_dir.glob('*.state'):
        # 獲取檔案修改時間
        mtime = datetime.fromtimestamp(os.path.getmtime(state_file))
        file_size = state_file.stat().st_size
        
        if mtime < cutoff_time:
            # 刪除舊檔案
            print(f"  刪除: {state_file.name} (修改時間: {mtime.strftime('%Y-%m-%d %H:%M:%S')})")
            state_file.unlink()
            removed_count += 1
            total_size += file_size
        else:
            kept_count += 1
    
    print(f"\n清理完成:")
    print(f"  刪除檔案: {removed_count}")
    print(f"  保留檔案: {kept_count}")
    print(f"  釋放空間: {total_size / 1024 / 1024:.2f} MB")

def clean_all_states():
    """清理所有狀態檔案"""
    state_dir = Path('states')
    
    if not state_dir.exists():
        print("states 資料夾不存在")
        return
    
    # 詢問確認
    response = input(f"確定要刪除 {state_dir} 中的所有狀態檔案嗎? (y/N): ")
    if response.lower() != 'y':
        print("取消操作")
        return
    
    # 刪除整個資料夾
    shutil.rmtree(state_dir)
    print(f"已刪除 {state_dir} 資料夾")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="清理狀態檔案")
    parser.add_argument('--all', action='store_true', help='刪除所有狀態檔案')
    parser.add_argument('--hours', type=int, default=24, 
                       help='保留最近幾小時的檔案（預設24小時）')
    
    args = parser.parse_args()
    
    if args.all:
        clean_all_states()
    else:
        clean_state_files(args.hours)